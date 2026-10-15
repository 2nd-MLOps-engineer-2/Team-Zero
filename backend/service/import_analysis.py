"""Validate C's proposed artifact contract, then snapshot new Gold without altering C values."""
import argparse,datetime,getpass,json,sys,uuid
from pathlib import Path
from tz_api.settings import Settings,identifier
from tz_api.repository import Repository
from tz_api.analysis import load_bundle

def prepare(source,project,output):
 repo=Repository(Settings(project=project,backend='csv')).warm();bundle=load_bundle(source,repo)
 sys.path.insert(0,str(project/'backend/medallion_pipeline'));import engine
 run=output/(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4]);run.mkdir(parents=True,exist_ok=False)
 entries=[]
 for name,item in bundle['entries'].items():
  spec=dict(name=name,layer='gold',pk=item['primary_key'],fks=[],columns=item['columns'])
  table=engine.from_csv(item['path'],spec);entries.append(engine.delta_snapshot(run,table,spec))
 catalog=dict(status='DELTA_PASS_MYSQL_PENDING',contract_version='tz-analysis-artifact/1.0',calculation_version=bundle['calculation_version'],
  input_version=bundle['input_version'],base_data_version=repo.data_version,tables=entries,
  database='tz_gold_analysis_'+run.name,source_manifest_sha256=engine.sha(source/'manifest.json'))
 engine.save(run/'catalog.json',catalog)
 return run,catalog

def mysql_load(run,catalog,host,port,user,password):
 import pymysql
 import engine
 from mysql_load import ddl,table_digest
 db=catalog['database'];con=pymysql.connect(host=host,port=port,user=user,password=password,charset='utf8mb4',autocommit=False,local_infile=False)
 results=[]
 try:
  with con.cursor() as cur:
   cur.execute('SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s',(db,))
   if cur.fetchone()[0]:raise ValueError('Refusing existing analysis database')
   cur.execute('CREATE DATABASE '+identifier(db)+' CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin');cur.execute('USE '+identifier(db))
   for entry in catalog['tables']:
    cur.execute(ddl(entry));names=[c['name'] for c in entry['columns']]
    sql='INSERT INTO '+identifier(entry['name'])+' ('+','.join(map(identifier,names))+') VALUES ('+','.join(['%s']*len(names))+')'
    table=engine.load_delta(run,entry)
    try:
     for batch in table.to_batches(max_chunksize=1000):cur.executemany(sql,[tuple(r[n] for n in names) for r in batch.to_pylist()])
     con.commit()
    except BaseException:con.rollback();raise
    count,h=table_digest(con,identifier(db)+'.'+identifier(entry['name']),entry)
    if count!=entry['rows'] or h!=entry['canonical_digest']:raise ValueError('Analysis Delta/MySQL mismatch')
    results.append(dict(table=entry['name'],rows=count,status='PASS',canonical_digest=h))
  engine.save(run/'mysql_validation.json',dict(status='PASS',database=db,tables=results,password_saved=False))
 finally:con.close()

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--project-root',type=Path,default=Settings().project)
 ap.add_argument('--output',type=Path);ap.add_argument('--mysql',action='store_true');ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=3306);ap.add_argument('--user',default='root');a=ap.parse_args()
 run,catalog=prepare(a.source.resolve(),a.project_root.resolve(),a.output or a.project_root/'build/analysis_import')
 print('PASS: C artifact validated and stored as Delta:',run)
 if a.mysql:mysql_load(run,catalog,a.host,a.port,a.user,getpass.getpass('MySQL password (typing is hidden): '))
