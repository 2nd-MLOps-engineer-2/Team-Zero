"""Pinned Delta -> new MySQL databases. Password is prompted locally only.

No DROP/TRUNCATE/REPLACE. Resume only databases owned by this run's state.
Every table is verified over all rows and all columns, not a row-count sample.
"""
from __future__ import annotations
import argparse,datetime as dt,getpass,json,re,sys
from pathlib import Path
import pymysql
from engine import HERE,load_delta,digest,iterrows,save,sha

def qi(s):
 if not re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',s):raise ValueError('Unsafe SQL identifier '+s)
 return '`'+s+'`'

def state_save(p,obj):
 tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8');tmp.replace(p)

def ddl(entry):
 if entry.get('ddl'):return entry['ddl']
 cols=[f"  {qi(c['name'])} {c['sql']}"+(' NULL' if c['nullable'] else ' NOT NULL') for c in entry['columns']]
 if entry['pk']:cols.append('  PRIMARY KEY ('+','.join(qi(c) for c in entry['pk'])+')')
 return 'CREATE TABLE '+qi(entry['name'])+' (\n'+',\n'.join(cols)+'\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin;'

def validation_queries(catalog):
 db=catalog['databases'];s=qi(db['silver']);g=qi(db['gold']);queries=[]
 def q(name,sql,expected=0):queries.append(dict(check=name,sql=sql,expected=expected))
 for e in catalog['tables']:
  fq=qi(db[e['layer']])+'.'+qi(e['name'])
  q(e['name']+'.row_count','SELECT COUNT(*) FROM '+fq,e['rows'])
  for col,parent,pcol in e.get('fks',[]):
   target_layer='silver' # All current Silver/Gold references point to Silver dimensions.
   q(e['name']+'.fk.'+col,f'SELECT COUNT(*) FROM {fq} a LEFT JOIN {qi(db[target_layer])}.{qi(parent)} p ON a.{qi(col)}=p.{qi(pcol)} WHERE a.{qi(col)} IS NOT NULL AND p.{qi(pcol)} IS NULL')
 q('pit_no_future_financials',f'SELECT COUNT(*) FROM {g}.g_ai_stock_daily WHERE dscl_dt>=trd_dt')
 q('investor_net_identity',f'SELECT COUNT(*) FROM {s}.s_invstr_trd_daily WHERE buy_qty-sell_qty<>net_buy_qty')
 q('unresolved_conversion_errors',f"SELECT COUNT(*) FROM {s}.s_dq_issue WHERE sev_cd='ERROR'")
 q('investor_missing_kept',f"SELECT COUNT(*) FROM {g}.g_ai_stock_daily WHERE invstr_exist_yn='N'",1)
 q('daily_finance_matched',f"SELECT COUNT(*) FROM {g}.g_ai_stock_daily WHERE fin_avail_yn='Y'",15833)
 q('daily_finance_unmatched',f"SELECT COUNT(*) FROM {g}.g_ai_stock_daily WHERE fin_avail_yn='N'",1607)
 q('gold_revenue_preservation',f"SELECT COUNT(*) FROM {g}.g_ai_stock_daily a JOIN {s}.s_fin_mtrc m ON a.fin_rpt_id=m.fin_rpt_id AND m.mtrc_cd='REVENUE' AND m.prd_type_cd='YTD' WHERE NOT(a.rev_ytd_amt <=> m.mtrc_amt)")
 q('gold_operating_profit_preservation',f"SELECT COUNT(*) FROM {g}.g_ai_stock_daily a JOIN {s}.s_fin_mtrc m ON a.fin_rpt_id=m.fin_rpt_id AND m.mtrc_cd='OPERATING_PROFIT' AND m.prd_type_cd='YTD' WHERE NOT(a.op_prft_ytd_amt <=> m.mtrc_amt)")
 q('gold_foreign_flow_preservation',f"SELECT COUNT(*) FROM {g}.g_ai_stock_daily a JOIN {s}.s_invstr_trd_daily i ON a.stock_cd=i.stock_cd AND a.trd_dt=i.trd_dt AND i.invstr_type_cd='FOREIGNER' WHERE NOT(a.frgn_net_buy_qty <=> i.net_buy_qty)")
 for name in ['s_stock_daily_prc','s_idx_daily_prc']:
  q(name+'.ohlc',f'SELECT COUNT(*) FROM {s}.{qi(name)} WHERE low_prc>high_prc OR open_prc<low_prc OR open_prc>high_prc OR close_prc<low_prc OR close_prc>high_prc OR trd_qty<0')
 return queries

def write_sql(run,catalog):
 folder=run/'sql';folder.mkdir(exist_ok=True)
 statements=['-- This run creates NEW databases only. Existing databases are never cleared.']
 for layer,db in catalog['databases'].items():
  statements.append(f'CREATE DATABASE {qi(db)} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;')
  statements.append('USE '+qi(db)+';')
  statements.extend(ddl(e) for e in catalog['tables'] if e['layer']==layer)
 (folder/'create_new_databases.sql').write_text('\n\n'.join(statements),encoding='utf-8')
 checks=validation_queries(catalog);state_save(folder/'validation_queries.json',checks)
 (folder/'validation_queries.sql').write_text('\n\n'.join('-- '+q['check']+' expected='+str(q['expected'])+'\n'+q['sql']+';' for q in checks),encoding='utf-8')

def select_run(value):
 if value:return Path(value).resolve()
 marker=HERE/'LATEST_RUN.txt'
 if not marker.exists():raise ValueError('No prepared run; run prepare.py first.')
 p=(HERE/marker.read_text(encoding='utf-8').strip()).resolve()
 if not p.is_relative_to((HERE/'runs').resolve()):raise ValueError('Invalid run marker')
 return p

def table_digest(con,fq,e):
 # SS cursor streams raw results; digest retains 32-byte row hashes, not all full rows.
 with con.cursor(pymysql.cursors.SSDictCursor) as cur:
  cur.execute('SELECT '+','.join(qi(c['name']) for c in e['columns'])+' FROM '+fq)
  n=0
  def rows():
   nonlocal n
   for row in cur:n+=1;yield row
  h=digest(rows(),e)
 return n,h

def load(run,host,user,port):
 catalog=json.loads((run/'catalog.json').read_text(encoding='utf-8'))
 # Verify all immutable Delta files and values before asking for credentials.
 print('Checking '+str(len(catalog['tables']))+' Delta snapshots before MySQL login...',flush=True)
 for e in catalog['tables']:
  for rel,h in e['delta_files'].items():
   if sha(run/e['delta_path']/rel)!=h:raise ValueError('Changed Delta file '+rel)
  print('  verified '+e['layer']+'.'+e['name'],flush=True)
 print(f'MySQL {user}@{host}:{port}. Four NEW databases for run {catalog["run_id"]}.',flush=True)
 password=getpass.getpass('MySQL password (typing is hidden): ')
 con=pymysql.connect(host=host,user=user,port=port,password=password,charset='utf8mb4',autocommit=False,
                     local_infile=False,connect_timeout=15,read_timeout=600,write_timeout=600)
 password=None
 p=run/'mysql_state.json';state=json.loads(p.read_text()) if p.exists() else dict(run_id=catalog['run_id'],databases=[],completed_tables=[])
 try:
  with con.cursor() as cur:
   cur.execute('SELECT VERSION()');version=cur.fetchone()[0]
   cur.execute('SELECT @@SESSION.sql_mode');modes=cur.fetchone()[0].split(',')
   if not set(modes)&{'STRICT_TRANS_TABLES','STRICT_ALL_TABLES'}:raise ValueError('MySQL strict mode required')
   for db in catalog['databases'].values():
    cur.execute('SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s',(db,));exists=cur.fetchone()[0]
    if exists and db not in state['databases']:raise ValueError('Refusing existing database without this run ownership: '+db)
    if not exists and db in state['databases']:raise ValueError('Previously created database is missing: '+db)
   for db in catalog['databases'].values():
    if db in state['databases']:continue
    cur.execute(f'CREATE DATABASE {qi(db)} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin')
    state['databases'].append(db);state_save(p,state)
  results=[]
  for e in catalog['tables']:
   db=catalog['databases'][e['layer']];fq=qi(db)+'.'+qi(e['name']);key=e['layer']+'.'+e['name']
   table=load_delta(run,e)
   with con.cursor() as cur:
    cur.execute('USE '+qi(db))
    cur.execute('SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s',(db,e['name']))
    exists=cur.fetchone()[0]
    if not exists:cur.execute(ddl(e));con.commit()
    cur.execute('SELECT COUNT(*) FROM '+fq);count=cur.fetchone()[0]
    if key not in state['completed_tables'] and count:
     # A prior commit may have succeeded before the state file update.
     n,h=table_digest(con,fq,e)
     if n!=e['rows'] or h!=e['canonical_digest']:raise ValueError('Nonempty partial/different table; preserving it: '+fq)
     state['completed_tables'].append(key);state_save(p,state)
    if key not in state['completed_tables']:
     names=[c['name'] for c in e['columns']]
     sql='INSERT INTO '+fq+' ('+','.join(qi(n) for n in names)+') VALUES ('+','.join(['%s']*len(names))+')'
     inserted=0
     try:
      for batch in table.to_batches(max_chunksize=1000):
       cur.executemany(sql,[tuple(row[n] for n in names) for row in batch.to_pylist()]);inserted+=batch.num_rows
       if inserted%100000==0:print('  loading '+key+' '+str(inserted),flush=True)
      con.commit()
     except BaseException:con.rollback();raise
     state['completed_tables'].append(key);state_save(p,state)
   n,h=table_digest(con,fq,e)
   if n!=e['rows'] or h!=e['canonical_digest']:raise ValueError('Full MySQL value reconciliation failed '+fq)
   results.append(dict(table=key,rows=n,values_checked=n*len(e['columns']),status='PASS',canonical_digest=h))
   print('PASS '+key+' '+str(n)+' rows, all columns matched',flush=True)
  checks=[]
  with con.cursor() as cur:
   for q in validation_queries(catalog):
    cur.execute(q['sql']);actual=cur.fetchone()[0]
    checks.append(dict(check=q['check'],expected=q['expected'],actual=actual,status='PASS' if actual==q['expected'] else 'FAIL'))
  failed=[q for q in checks if q['status']=='FAIL']
  report=dict(status='PASS' if not failed else 'FAIL',server_version=version,completed_at=dt.datetime.now().astimezone().isoformat(),
   run_id=catalog['run_id'],databases=catalog['databases'],tables=results,sql_checks=checks,
   all_rows_all_columns_match=True,existing_databases_unchanged=True,password_saved=False)
  state_save(run/'validation/mysql_validation.json',report)
  if failed:raise ValueError('SQL checks failed '+str(failed))
  print('SUCCESS: '+str(len(results))+' tables loaded; '+str(len(checks))+' SQL checks passed.',flush=True)
  print('Report: '+str(run/'validation/mysql_validation.json'),flush=True)
 finally:con.close()

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run');ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--user',default='root');ap.add_argument('--port',default=3306,type=int)
 a=ap.parse_args()
 try:load(select_run(a.run),a.host,a.user,a.port)
 except KeyboardInterrupt:print('Interrupted. Current transaction rolled back; rerun to verify and resume.',file=sys.stderr);sys.exit(1)
 except Exception as exc:print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(1)
