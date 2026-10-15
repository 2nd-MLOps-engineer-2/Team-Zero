"""Local credential entry -> real MySQL API verification -> optional new dump/restore proof.

Source databases are read only. Restore creates four distinct new databases and
never drops or clears an existing database. Password is not saved in files/argv.
"""
from __future__ import annotations
import argparse,datetime,getpass,gzip,json,os,re,shutil,subprocess,sys,uuid
from pathlib import Path
from fastapi.testclient import TestClient
from tz_api.settings import Settings,identifier
from tz_api.repository import Repository
from tz_api.main import create_app

MYSQL_BIN=Path('C:/Program Files/MySQL/MySQL Server 8.4/bin')
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str),encoding='utf-8')

def verify_api(settings):
 sql_repo=Repository(settings).warm()
 csv_repo=Repository(Settings(project=settings.project,backend='csv')).warm()
 tests=['/health','/stocks','/stocks/compare?as_of=2026-06-30','/stocks/005930/daily?start=2026-06-01&end=2026-06-30',
  '/stocks/005930/financials','/stocks/247540/quality?start=2026-04-16&end=2026-04-16',
  '/analysis/005930/evidence?as_of=2026-06-30','/exports/stocks/005930/daily.csv?start=2026-06-01&end=2026-06-30',
  '/exports/stocks/005930/financials.csv?year=2025&report_code=11011']
 results=[];mismatches=[]
 with TestClient(create_app(repository=sql_repo)) as actual,TestClient(create_app(repository=csv_repo)) as reference:
  for url in tests:
   response=actual.get(url);expected=reference.get(url)
   equal=response.status_code==200 and (response.content==expected.content if '.csv' in url else response.json()['data']==expected.json()['data'])
   if not equal:mismatches.append(url)
   results.append(dict(request=url,status='PASS' if equal else 'FAIL',http_status=response.status_code))
 if mismatches:raise ValueError('MySQL API differs from verified CSV: '+'; '.join(mismatches))
 return sql_repo,results

def dump_database(binary,db,dest,settings,env):
 args=[str(binary),'--host='+settings.mysql_host,'--port='+str(settings.mysql_port),'--user='+settings.mysql_user,
  '--single-transaction','--skip-lock-tables','--skip-add-locks','--skip-add-drop-table','--skip-triggers',
  '--no-tablespaces','--set-gtid-purged=OFF','--column-statistics=0','--skip-dump-date','--default-character-set=utf8mb4',db]
 process=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=NO_WINDOW)
 try:
  with gzip.GzipFile(filename=str(dest),mode='wb',mtime=0) as stream:shutil.copyfileobj(process.stdout,stream,1<<20)
  stderr=process.stderr.read();rc=process.wait()
  if rc:raise RuntimeError('mysqldump failed: '+stderr.decode('utf-8',errors='replace')[:500])
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=10)
 # This dump has no database selection or destructive table creation commands.
 with gzip.open(dest,'rt',encoding='utf-8') as stream:
  for line in stream:
   if re.match(r'\s*(USE\s+|(?:CREATE|DROP)\s+DATABASE\b|DROP\s+TABLE\b)',line,re.I):raise ValueError('Unsafe database-scoped dump statement')

def restore_database(binary,db,source,settings,env):
 args=[str(binary),'--host='+settings.mysql_host,'--port='+str(settings.mysql_port),'--user='+settings.mysql_user,
  '--default-character-set=utf8mb4','--binary-mode=1','--database='+db]
 process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,creationflags=NO_WINDOW)
 try:
  with gzip.open(source,'rb') as stream:shutil.copyfileobj(stream,process.stdin,1<<20)
  process.stdin.close();process.stdin=None
  _,stderr=process.communicate(timeout=600)
  if process.returncode:raise RuntimeError('mysql restore failed: '+stderr.decode('utf-8',errors='replace')[:500])
 finally:
  if process.poll() is None:process.terminate();process.wait(timeout=10)

def backup_restore(repo,output,binary_dir):
 import pymysql
 from mysql_load import table_digest
 settings=repo.settings;catalog=repo.catalog
 binaries={n:binary_dir/(n+('.exe' if os.name=='nt' else '')) for n in ['mysql','mysqldump']}
 if not all(p.is_file() for p in binaries.values()):raise ValueError('mysql/mysqldump binaries not found; pass --mysql-bin')
 suffix=output.name
 restore_db={layer:'tz_restore_'+layer+'_'+suffix for layer in catalog['databases']}
 env=os.environ.copy();env['MYSQL_PWD']=settings.mysql_password
 dumps=[]
 for layer,source_db in catalog['databases'].items():
  dest=output/(layer+'.sql.gz');print('Dumping source '+layer+' (read only)...',flush=True)
  dump_database(binaries['mysqldump'],source_db,dest,settings,env)
  dumps.append(dict(layer=layer,file=dest.name,sha256=repo.engine.sha(dest),bytes=dest.stat().st_size))
 con=pymysql.connect(host=settings.mysql_host,port=settings.mysql_port,user=settings.mysql_user,password=settings.mysql_password,
  charset='utf8mb4',autocommit=False,local_infile=False,read_timeout=600)
 results=[]
 try:
  with con.cursor() as cur:
   for db in restore_db.values():
    cur.execute('SELECT COUNT(*) FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s',(db,))
    if cur.fetchone()[0]:raise ValueError('Refusing existing restore target: '+db)
   for db in restore_db.values():cur.execute('CREATE DATABASE '+identifier(db)+' CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin')
  for layer,db in restore_db.items():
   print('Restoring into NEW database '+db+'...',flush=True)
   restore_database(binaries['mysql'],db,output/(layer+'.sql.gz'),settings,env)
  for entry in catalog['tables']:
   db=restore_db[entry['layer']];count,h=table_digest(con,identifier(db)+'.'+identifier(entry['name']),entry)
   if count!=entry['rows'] or h!=entry['canonical_digest']:raise ValueError('Restore value mismatch: '+entry['name'])
   results.append(dict(layer=entry['layer'],table=entry['name'],rows=count,status='PASS',canonical_digest=h))
   print('Restore PASS '+entry['name']+' '+str(count),flush=True)
 finally:con.close();env.pop('MYSQL_PWD',None)
 return dict(status='PASS',dumps=dumps,restore_databases=restore_db,restored_tables=results,
  original_databases_unchanged=True,password_saved=False,secret_transport='ephemeral child process environment only')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path);ap.add_argument('--delta-run',type=Path)
 ap.add_argument('--backup-restore',action='store_true');ap.add_argument('--mysql-bin',type=Path,default=MYSQL_BIN);a=ap.parse_args()
 settings=Settings.from_env();settings.backend='mysql'
 if a.project_root:settings.project=a.project_root
 if a.delta_run:settings.delta_run=a.delta_run
 settings.resolve();suffix=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4]
 output=settings.project/'build/mysql_operations'/suffix;output.mkdir(parents=True,exist_ok=False)
 settings.mysql_password=getpass.getpass('MySQL password (typing is hidden): ')
 try:
  repo,results=verify_api(settings);save(output/'api_mysql_validation.json',dict(status='PASS',requests=results,source_backend='mysql',run_id=repo.catalog['run_id'],password_saved=False))
  print('PASS: '+str(len(results))+' real MySQL API requests match the provided CSV.',flush=True)
  if a.backup_restore:save(output/'backup_restore_validation.json',backup_restore(repo,output,a.mysql_bin))
  print('SUCCESS. Evidence folder: '+str(output),flush=True)
 except BaseException as exc:
  save(output/'operation_failure.json',dict(status='FAIL',exception_type=type(exc).__name__))
  raise
 finally:settings.mysql_password=''

if __name__=='__main__':main()
