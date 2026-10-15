"""Source adapters; no SQL writes, silent fallback, or floating monetary conversion."""
from __future__ import annotations
import csv,hashlib,json,sys,threading,importlib.util
from pathlib import Path
from datetime import date,datetime
from decimal import Decimal
from .settings import Settings,identifier
from . import __version__

BASE_TABLES={'s_stock','s_corp','s_corp_stock_map','s_fin_rpt','s_fin_mtrc','s_fin_mtrc_def','s_fin_item','s_dscl','s_dscl_doc',
 's_stock_daily_prc','s_idx_daily_prc','s_invstr_trd_daily','s_frgn_hold_daily','s_cfd_bal_daily','s_conn_stts','s_dq_issue','s_cmn_cd',
 'g_ai_stock_daily','g_fin_rpt_mkt_smry'}

def file_hash(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

def wire(v):
 if v is None or v=='':return None
 if isinstance(v,Decimal):return format(v,'f')
 if isinstance(v,(date,datetime)):return v.isoformat()
 if isinstance(v,int):return str(v)
 return v

class Repository:
 def __init__(self,settings:Settings):
  self.settings=settings.resolve();self.backend=settings.backend;self._cache={};self.lock=threading.RLock()
  spec=importlib.util.spec_from_file_location('tz_service_standard',settings.project/'backend/medallion_pipeline/vendor/std_dictionary.py')
  registry=importlib.util.module_from_spec(spec);spec.loader.exec_module(registry)
  self.registry=registry
  self.catalog=None;self.entries={};self.manifest={};self.analysis=None
  self.handoff_version='handoff-sha256:'+file_hash(settings.project/'data/handoff_manifest.json')[:16]
  if self.backend=='csv':
   mf=settings.project/'data/handoff_manifest.json'
   if not mf.is_file():raise ValueError('The provided handoff manifest is required')
   m=json.loads(mf.read_text(encoding='utf-8'));self.manifest={e['path']:e for e in m['files']}
   self.data_version=self.handoff_version
  else:
   run=settings.delta_run.resolve();self.catalog=json.loads((run/'catalog.json').read_text(encoding='utf-8'))
   self.entries={e['name']:e for e in self.catalog['tables']};self.data_version='delta-run:'+self.catalog['run_id']
   sys.path.insert(0,str(settings.project/'backend/medallion_pipeline'))
   import engine
   self.engine=engine
   if self.backend=='mysql':
    evidence=json.loads((run/'validation/mysql_validation.json').read_text(encoding='utf-8'))
    if evidence['status']!='PASS' or evidence['run_id']!=self.catalog['run_id']:raise ValueError('Verified MySQL run is required')
    if evidence['databases']!=self.catalog['databases']:raise ValueError('MySQL database catalog mismatch')
  self.calculation_version='c-integration-1.0.0'

 def _csv(self,name):
  sub='gold' if name.startswith('g_') else 'silver';rel=f'04_output/{sub}/{name}.csv'
  expected=self.manifest.get(rel)
  if not expected:raise ValueError('Table not declared in handoff')
  path=self.settings.data_dir/rel
  if file_hash(path)!=expected['sha256']:raise ValueError('Handoff source hash mismatch: '+name)
  with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

 def _mysql(self,name,entry):
  import pymysql
  db=self.catalog['databases'][entry['layer']]
  con=pymysql.connect(host=self.settings.mysql_host,port=self.settings.mysql_port,user=self.settings.mysql_user,
   password=self.settings.mysql_password,charset='utf8mb4',autocommit=False,local_infile=False,connect_timeout=10,
   read_timeout=60,cursorclass=pymysql.cursors.DictCursor)
  try:
   with con.cursor() as cur:
    cur.execute('SET SESSION TRANSACTION READ ONLY')
    cols=','.join(identifier(c['name']) for c in entry['columns'])
    cur.execute('SELECT '+cols+' FROM '+identifier(db)+'.'+identifier(name));rows=cur.fetchall()
   if len(rows)!=entry['rows'] or self.engine.digest(rows,entry)!=entry['canonical_digest']:raise ValueError('MySQL snapshot values changed: '+name)
   return rows
  finally:con.rollback();con.close()

 def rows(self,name):
  if name not in BASE_TABLES:raise ValueError('Table not allowed')
  with self.lock:
   if name not in self._cache:
    if self.backend=='csv':rows=self._csv(name)
    else:
     entry=self.entries[name]
     if self.backend=='delta':
      path=(self.settings.delta_run/entry['delta_path']).resolve()
      if not path.is_relative_to(self.settings.delta_run.resolve()):raise ValueError('Delta path escapes run')
      rows=self.engine.load_delta(self.settings.delta_run,entry).to_pylist()
     else:rows=self._mysql(name,entry)
    types={c['phys']:self.registry.DOMAINS[c['dmn']][1] for c in self.registry.TABLES[name]['cols']}
    def normalized(key,value):
     if value is None or value=='':return None
     sql=types[key]
     if sql.startswith('DECIMAL'):
      scale=int(sql.rstrip(')').split(',')[1]);return format(Decimal(value),f'.{scale}f')
     if sql in ('INT','BIGINT'):return str(int(value))
     if sql=='DATETIME':return (value if isinstance(value,datetime) else datetime.fromisoformat(value)).isoformat()
     return wire(value)
    self._cache[name]=[{k:normalized(k,v) for k,v in row.items()} for row in rows]
   return self._cache[name]

 def warm(self):
  self.stocks={r['stock_cd']:r for r in self.rows('s_stock')}
  self.mapping={r['stock_cd']:r for r in self.rows('s_corp_stock_map')}
  self.reports={r['fin_rpt_id']:r for r in self.rows('s_fin_rpt')}
  self.disclosures={r['rcept_no']:r for r in self.rows('s_dscl')}
  self.daily={}
  for r in self.rows('g_ai_stock_daily'):self.daily.setdefault(r['stock_cd'],[]).append(r)
  for rows in self.daily.values():rows.sort(key=lambda r:r['trd_dt'])
  dates=[r['trd_dt'] for rows in self.daily.values() for r in rows]
  self.min_date=min(dates);self.max_date=max(dates)
  self.metrics={}
  for r in self.rows('s_fin_mtrc'):self.metrics.setdefault(r['fin_rpt_id'],[]).append(r)
  self.connection={(r['stock_cd'],r['trd_dt']):r for r in self.rows('s_conn_stts')}
  self.period_summary={r['fin_rpt_id']:r for r in self.rows('g_fin_rpt_mkt_smry')}
  if self.settings.analysis_dir:
   from .analysis import load_bundle
   self.analysis=load_bundle(self.settings.analysis_dir,self)
   self.calculation_version=self.analysis['calculation_version']
  return self

 def metadata(self,**extra):
  return dict(api_version=__version__,data_version=self.data_version,source_backend=self.backend,
   data_min_date=self.min_date,data_final_date=self.max_date,stock_count=len(self.stocks),
   calculation_version=self.calculation_version,analysis_status='AVAILABLE' if self.analysis else 'PENDING_C_DELIVERY',
   synthetic=False,input_version=self.handoff_version,
   analysis_data_version=self.analysis['artifact_version'] if self.analysis else None,
   units=dict(amount='KRW',quantity='shares',ratio='decimal_fraction'),
   numeric_encoding='decimal_string',**extra)

 def latest(self,code,as_of):
  return next((r for r in reversed(self.daily.get(code,[])) if r['trd_dt']<=as_of),None)

 def annotated_daily(self,row):
  out=dict(row);out['stock_nm']=self.stocks[row['stock_cd']]['stock_nm']
  out['connection']=self.connection.get((row['stock_cd'],row['trd_dt']))
  out['analysis']=self.analysis['daily'].get((row['stock_cd'],row['trd_dt'])) if self.analysis else None
  return out

 def financial(self,report):
  out=dict(report);dscl=self.disclosures.get(report['rcept_no'])
  out['dscl_dt']=dscl['rcept_dt'] if dscl else None
  out['metrics']=sorted(self.metrics.get(report['fin_rpt_id'],[]),key=lambda r:(r['mtrc_cd'],r['prd_type_cd']))
  out['period_market_summary']=self.period_summary.get(report['fin_rpt_id'])
  out['analysis']=self.analysis['financial'].get(report['fin_rpt_id']) if self.analysis else None
  return out
