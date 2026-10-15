"""Read-only source inputs -> immutable full Bronze/Silver/Gold Delta run.

Raw corruption is retained. Existing educational cleanup and A/B handoffs are
explicit evidence stages; C standardization is re-executed, never just relabeled.
"""
from __future__ import annotations
import argparse,collections,datetime as dt,importlib,io,json,re,shutil,subprocess,sys,uuid,zipfile
from pathlib import Path
import pandas as pd
import pyarrow as pa
pd.options.mode.string_storage='python'  # C regexes exceed Arrow/RE2 repetition limits.
from engine import HERE,sha,save,read,delta_snapshot,raw_spec,raw_arrow,from_csv

sys.path.insert(0,str(HERE/'vendor'))
import common,std_dictionary as sd,run_pipeline as transform,build_model as model
import clean_bronze,merge_recovery
DEFAULT_PROJECT=Path('C:/Users/Playdata/workspace/Team-Zero')
DEFAULT_RAW=Path('C:/Users/Playdata/Desktop/프로젝트/2차/데이터')
EXPECTED_RAW={'OpenDART_오염데이터.zip':'01b199d050ca43357a7bdc15d30e7c5f6503aebf21d06d353b023611ef7f1166',
              '토스증권_오염데이터.zip':'ae3cba6a0a304228561e056162118baa83afcba25c56592db935bff2500fb1e8'}

def say(s):print(s,flush=True)
def write(df,p):common.write_csv(df,p)

def safe_extract(z,dest):
 root=dest.resolve();already=dest.exists()
 for i in z.infolist():
  if not (root/i.filename).resolve().is_relative_to(root) or (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Unsafe ZIP entry')
 if already:
  import hashlib
  for i in z.infolist():
   if not i.is_dir() and sha(root/i.filename)!=hashlib.sha256(z.read(i)).hexdigest():raise ValueError('Changed extracted source '+i.filename)
 else:
  dest.mkdir(parents=True,exist_ok=False);z.extractall(root)

def attach(df,source,h,encoding):
 df=df.copy();df['ldng_file_path']=source;df['ldng_row_no']=range(1,len(df)+1)
 df['ldng_file_hash']=h;df['ldng_encoding']=encoding
 return df

def group_name(team,rel):
 name=Path(rel).name
 if team=='DART':
  return 'b_raw_dart_'+('disclosures' if '/disclosures/' in rel else 'financials' if '/financials/' in rel else 'documents' if name=='disclosure_documents.csv' else 'corp')
 return 'b_raw_toss_'+('stocks' if name=='stocks.csv' else 'investor' if 'investor_trading' in name else 'index' if '_index' in name else 'price')

def profile(df,team,rel,cols_out,files_out):
 # Observed blanks are distinct from confirmed required-field violations.
 candidate=[c for c in (['corp_code'] if 'corp_codes' in rel else ['rcept_no'] if 'disclosures/' in rel else
                       ['rcept_no','fs_div','sj_div','account_id','account_detail','ord'] if '/financials/' in rel else
                       ['symbol','date'] if 'date' in df else ['symbol','timestamp'] if 'timestamp' in df else ['symbol'] if 'symbol' in df else ['rcept_no']) if c in df]
 for c in df:
  s=df[c];null=s.str.strip().str.upper().isin(['','NULL','N/A','NONE','NAN','-'])
  row=dict(dataset=team,source_file=rel,column=c,rows=len(df),observed_blank_or_literal=int(null.sum()),
           distinct_including_blank=int(s.nunique(dropna=False)),non_ascii_header=bool(re.search('[^\x00-\x7f]',c)),
           snake_case_header=bool(re.fullmatch('[a-z][a-z0-9_]*',c)),format_rule='',format_violations=0,code_rule='',code_violations=0)
  non=s[~null]
  if c in ('corp_code','stock_code','rcept_no','symbol'):
   rx={'corp_code':r'\d{8}','stock_code':r'\d{6}','rcept_no':r'\d{14}','symbol':r'\d{6}|KOSPI|KOSDAQ'}[c]
   row.update(format_rule=rx,format_violations=int((~non.str.fullmatch(rx)).sum()))
  elif c in ('rcept_dt','modify_date'):
   parsed=pd.to_datetime(non,format='%Y%m%d',errors='coerce')
   row.update(format_rule='valid YYYYMMDD',format_violations=int(parsed.isna().sum()))
  elif c=='date':
   row.update(format_rule='YYYY-MM-DD',format_violations=int((~non.str.fullmatch(r'\d{4}-\d{2}-\d{2}')).sum()))
  elif c in ('thstrm_amount','thstrm_add_amount','frmtrm_amount','frmtrm_q_amount','frmtrm_add_amount','bfefrmtrm_amount'):
   row.update(format_rule='integer string; optional blank allowed',format_violations=int((~non.str.fullmatch(r'-?\d+')).sum()))
  if c in ('fs_div','sj_div','reprt_code','corp_cls','currency','isCommonShare'):
   vals={'fs_div':['CFS','OFS'],'sj_div':['BS','IS','CIS','CF','SCE'],'reprt_code':['11011','11012','11013','11014'],
         'corp_cls':['Y','K','N','E'],'currency':['KRW'],'isCommonShare':['true','false']}[c]
   row.update(code_rule='|'.join(vals),code_violations=int((~non.isin(vals)).sum()))
  cols_out.append(row)
 files_out.append(dict(dataset=team,source_file=rel,rows=len(df),columns=len(df.columns),
  candidate_key='|'.join(candidate),candidate_duplicate_excess=int(df.duplicated(candidate).sum()) if candidate else None,
  exact_duplicate_excess=int(df.duplicated().sum()),
  note='Candidate duplicates require source evidence; blank counts include permitted missing values.'))

def stage_a(archive,dest,expected):
 with zipfile.ZipFile(archive) as z:
  prefix=next(n for n in z.namelist() if n.endswith('/opendart_financial_summary_20_companies.csv')).rsplit('/',1)[0]+'/'
  dest.mkdir(parents=True,exist_ok=True)
  for team,logical,rel,h in expected:
   if team!='A':continue
   data=z.read(prefix+rel)
   import hashlib
   if hashlib.sha256(data).hexdigest()!=h:raise ValueError('A ZIP hash '+rel)
   p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True)
   if p.exists() and p.read_bytes()!=data:raise ValueError('Changed staged A input '+rel)
   if not p.exists():p.write_bytes(data)
  for name in z.namelist():
   if name.startswith(prefix+'scripts/') and not name.endswith('/'):
    rel=name[len(prefix):];p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);data=z.read(name)
    if p.exists() and p.read_bytes()!=data:raise ValueError('Changed A reference script')
    if not p.exists():p.write_bytes(data)

def replay_cleanup(run,roots,summary,manifest,original):
 out=run/'evidence'/'cleanup_replay'
 if (out/'replay_validation.json').exists():
  previous=json.loads((out/'replay_validation.json').read_text(encoding='utf-8'))
  if previous['status']!='PASS':raise ValueError('Prior cleanup not PASS')
  files=list((out/'01_bronze').rglob('*.csv'))
  if len(files)!=previous['files_compared']:raise ValueError('Cleanup replay file count changed')
  for p in files:
   if sha(p)!=sha(original/p.relative_to(out)):raise ValueError('Cleanup replay changed '+str(p))
  say('Reusing verified cleanup replay (91 CSV hashes checked)');return out
 out.mkdir(parents=True)
 dart=clean_bronze.restore_dart(roots['DART'],out,dict(summary=summary,manifest=manifest))
 toss=clean_bronze.clean_toss(roots['TOSS'],out,dart)
 fs=dart.pop('per_file')+toss.pop('per_file');dart.pop('stock_refs')
 mismatches=[]
 for row in fs:
  rel=Path('01_bronze')/row['dataset']/row['source_file']
  if sha(out/rel)!=sha(original/rel):mismatches.append(rel.as_posix())
 if mismatches:raise ValueError('Cleanup output changed '+str(mismatches))
 save(out/'replay_validation.json',dict(status='PASS',OpenDART=dart,Toss=toss,files_compared=len(fs),mismatches=mismatches))
 return out

def validate_handoff_lineage(a,b,clean):
 # A detail rows retain exact source_file/source_row links to replayed cleanup.
 A=common.load_inputs(a,b)[0];rows=A['financial_items']
 say('Validating A financial detail against replayed cleanup')
 # Inspect A lineage names rather than infer data from rounded monetary values.
 source_col='_source_file' if '_source_file' in rows else 'source_file'
 row_col='_source_row' if '_source_row' in rows else 'source_row'
 mismatches=0
 for rel,g in rows.groupby(source_col):
  src=common.read_csv(clean/'01_bronze/OpenDART/dataset'/rel)
  indices=g[row_col].astype(int).to_numpy()-1
  for c in src.columns:
   mismatches+=int((g[c].to_numpy()!=src.iloc[indices][c].to_numpy()).sum())
 if mismatches:raise ValueError('A cleaned detail preservation failed '+str(mismatches))
 return dict(A_detail_rows=len(rows),A_detail_mismatches=mismatches,
  limitation='A report mapping is supplied by the hash-verified A package; its original builder is not rerun here. B baseline is supplied, API merge is replayed.')

def quality(run,entries,a,b,croot):
 D={n:common.read_csv(run/'exports'/sd.TABLES[n]['layer'].lower()/f'{n}.csv') for n in sd.TABLES if sd.TABLES[n]['layer'] in ('SILVER','GOLD')}
 checks=[]
 def ck(name,ok,actual):
  checks.append(dict(check=name,status='PASS' if ok else 'FAIL',actual=actual))
 for n,df in D.items():
  t=sd.TABLES[n]
  ck(n+'.pk',not df.duplicated(t['pk']).any(),int(df.duplicated(t['pk']).sum()))
  for col,parent,pcol in t['fks']:
   if parent in D:
    bad=df[(df[col]!='')&~df[col].isin(D[parent][pcol])]
    ck(n+'.fk.'+col,len(bad)==0,len(bad))
  for col in t['cols']:
   if not col['null']:ck(n+'.required.'+col['phys'],not (df[col['phys']]=='').any(),int((df[col['phys']]=='').sum()))
   violations=sd.check_name(col['phys'],col['dmn'])
   ck(n+'.name.'+col['phys'],not violations,str(violations))
 g=D['g_ai_stock_daily'];ck('daily_price_count',len(g)==len(D['s_stock_daily_prc']),len(g))
 ck('daily_pit_no_lookahead',not ((g.dscl_dt!='')&(g.dscl_dt>=g.trd_dt)).any(),int(((g.dscl_dt!='')&(g.dscl_dt>=g.trd_dt)).sum()))
 ck('investor_missing_kept',int((g.invstr_exist_yn=='N').sum())==1,int((g.invstr_exist_yn=='N').sum()))
 # Independent reference PIT selection from A handoff code.
 import importlib.util
 refpath=a/'scripts/join_daily_for_c.py'
 spec=importlib.util.spec_from_file_location('a_reference_join',refpath);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 ref=mod.attach([dict(stock_code=r.stock_cd,trade_date=r.trd_dt) for r in g.itertuples()],read(a/common.A_FILES['financial_summary']))
 mismatch=sum(x['dart_financial_report_id']!=y for x,y in zip(ref,g.fin_rpt_id))
 ck('independent_A_PIT_reference',mismatch==0,mismatch)
 old=json.loads((croot/'04_output/output_sha256.json').read_text())['files']
 for rel,h in old.items():ck('C_reproduction.'+rel,sha(run/'exports'/rel)==h,sha(run/'exports'/rel))
 write(pd.DataFrame(checks),run/'validation/pandas_checks.csv')
 failed=[x for x in checks if x['status']=='FAIL']
 save(run/'validation/pandas_summary.json',dict(status='PASS' if not failed else 'FAIL',total=len(checks),passed=len(checks)-len(failed),failed=failed,
       daily_rows=len(g),financial_matched=int((g.fin_avail_yn=='Y').sum()),financial_unmatched=int((g.fin_avail_yn=='N').sum()),
       investor_unmatched=int((g.invstr_exist_yn=='N').sum()),standard_name_violations=0 if not any('.name.' in x['check'] for x in failed) else None))
 if failed:raise ValueError('Pandas verification failed '+str(failed[:5]))

def prepare(project,raw,output,resume=None):
 global save,delta_snapshot
 if resume:
  from functools import partial
  import engine
  run=resume.resolve()
  if not run.is_relative_to(output.resolve()):raise ValueError('Resume must stay inside output root')
  config=json.loads((run/'run_config.json').read_text(encoding='utf-8'));runid=config['run_id']
  if config['project']!=str(project) or config['raw']!=str(raw):raise ValueError('Resume source paths changed')
  original_save=engine.save
  def save_equal(path,obj):
   path=Path(path)
   if path.exists():
    if json.loads(path.read_text(encoding='utf-8'))!=json.loads(json.dumps(obj,default=str)):raise ValueError('Changed immutable evidence '+str(path))
   else:original_save(path,obj)
  save=save_equal;delta_snapshot=partial(engine.delta_snapshot,allow_existing=True)
 else:
  runid=dt.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4]
  run=output/runid;run.mkdir(parents=True,exist_ok=False)
  save(run/'run_config.json',dict(run_id=runid,project=str(project),raw=str(raw),created_at=dt.datetime.now().astimezone().isoformat()))
 say('RUN '+str(run))
 data=project/'data';croot=data/'silver/03_C_integration_20261014/03_C_integration_20261014'
 b=data/'silver/Team_B_Silver_Handoff/Team_B_Silver_Handoff'
 origclean=data/'Bronze_Cleanup/Bronze_Cleanup_20261014'
 a=run/'inputs/A';expected=[(r['src_team_cd'],r['logical_nm'],r['rel_path'],r['sha256']) for r in read(croot/'04_output/meta/input_manifest.csv')]
 stage_a(data/'silver/OpenDART/02_C_handoff_20261014.zip',a,expected)
 for team,logical,rel,h in expected:
  if team=='B' and sha(b/rel)!=h:raise ValueError('B input changed '+rel)
 save(run/'evidence/input_manifest.json',[dict(team=t,logical=n,file=r,sha256=h) for t,n,r,h in expected])
 summary=json.loads((raw/'OpenDART_오염데이터_요약.json').read_text(encoding='utf-8-sig'))
 roots={};groups=collections.defaultdict(list);specs={};cols_profile=[];files_profile=[];entries=[]
 for team,name in zip(('DART','TOSS'),EXPECTED_RAW):
  archive=raw/name
  if sha(archive)!=EXPECTED_RAW[name]:raise ValueError('Raw source archive changed '+name)
  # Preserve archive bytes too; Delta contains decoded CSV values, not original encoding bytes.
  copy=run/'raw_archives'/name;copy.parent.mkdir(parents=True,exist_ok=True)
  if not copy.exists():shutil.copy2(archive,copy)
  if sha(copy)!=EXPECTED_RAW[name]:raise ValueError('Archive copy mismatch')
  root=run/'inputs'/('raw_'+team)
  with zipfile.ZipFile(copy) as z:safe_extract(z,root)
  roots[team]=root
  for p in sorted(root.rglob('*.csv')):
   rel=p.relative_to(root).as_posix();enc=summary['encodings'][rel] if team=='DART' else 'utf-8-sig'
   df=pd.read_csv(p,dtype=str,encoding=enc,keep_default_na=False,na_filter=False)
   profile(df,team,rel,cols_profile,files_profile)
   n=group_name(team,rel);s=raw_spec(n,list(df.columns))
   if n in specs and specs[n]!=s:raise ValueError('Raw schema drift '+n)
   specs[n]=s;groups[n].append(attach(df,team+':'+rel,sha(p),enc))
  say('Pandas raw profile '+team+' completed')
 for n,frames in groups.items():
  table=raw_arrow(frames,specs[n]);entries.append(delta_snapshot(run,table,specs[n]));say('Bronze Delta '+n+' '+str(table.num_rows))
 groups.clear()
 write(pd.DataFrame(cols_profile),run/'profiling/raw_column_profile.csv');write(pd.DataFrame(files_profile),run/'profiling/raw_file_profile.csv')
 save(run/'profiling/raw_summary.json',dict(files=len(files_profile),rows=sum(x['rows'] for x in files_profile),
  observed_blank_or_literal_cells=sum(x['observed_blank_or_literal'] for x in cols_profile),
  confirmed_format_rule_violations=sum(x['format_violations'] for x in cols_profile),
  code_standard_rule_violations=sum(x['code_violations'] for x in cols_profile),
  headers_non_snake_case=sum(not x['snake_case_header'] for x in cols_profile),
  note='Counts use stated rules; optional blanks and candidate duplicates are not asserted to be corruption. Amount sign/x1000 changes may be syntactically valid; manifest restoration detects them.'))
 manifest=raw/'OpenDART_오염데이터_변경사항.csv'
 mf=common.read_csv(manifest);counts=mf.groupby('rule').size().to_dict()
 if counts!=summary['rules_overall']:raise ValueError('Corruption manifest rule counts differ')
 save(run/'profiling/declared_corruption_rules.json',counts)
 cleaned=replay_cleanup(run,roots,summary,manifest,origclean)
 # B API merge must reproduce all 11 current input CSVs exactly.
 breplay=run/'evidence/B_api_merge_replay'
 if not (resume and (breplay/'validation_summary.json').exists()):
  subprocess.run([sys.executable,'-X','utf8',str(HERE/'replay_b.py'),'--b',str(b),'--output',str(breplay)],check=True)
 for team,logical,rel,h in expected:
  if team=='B' and sha(breplay/Path(rel).name)!=h:raise ValueError('B API replay differs '+rel)
 save(run/'evidence/handoff_lineage.json',validate_handoff_lineage(a,b,cleaned))
 from check_b_lineage import verify as verify_b
 save(run/'validation/B_clean_source_lineage.json',verify_b(b,cleaned))
 # Snapshot the supplied A/B contracts, including B nested JSON, before standardizing.
 for team,base,files in [('A',a,common.A_FILES),('B',b,common.B_FILES)]:
  for logical,rel in files.items():
   p=base/rel;df=common.read_csv(p);s=raw_spec('b_'+team.lower()+'_'+logical,list(df.columns))
   s['kind']='handoff';t=raw_arrow([attach(df,team+':'+rel,sha(p),'utf-8-sig')],s)
   entries.append(delta_snapshot(run,t,s));say('Bronze handoff '+s['name']+' '+str(t.num_rows))
 # Captured API JSON provenance: no live API requests during this run.
 api=b/'inputs/additional_data';apirows=[]
 for p in sorted(api.rglob('*.json')):
  text=p.read_text(encoding='utf-8-sig');json.loads(text)
  apirows.append(dict(api_file_path=p.relative_to(api).as_posix(),api_file_hash=sha(p),api_raw_txt=text))
 if apirows:
  df=pd.DataFrame(apirows);s=raw_spec('b_api_captured_response',list(df));entries.append(delta_snapshot(run,raw_arrow([attach(df,'B:captured_API',sha(api/'requests_manifest.json'),'utf-8-sig')],s),s))
 s=raw_spec('b_corruption_manifest',list(mf));entries.append(delta_snapshot(run,raw_arrow([attach(mf,'DART:corruption_manifest',sha(manifest),'utf-8-sig')],s),s))
 # Re-execute C transformations in a new output folder. Never execute C's DROP loader.
 common.ROOT=run;transform.OUT=run/'exports';transform.EXEC_LOG.clear();transform.CONV_ERRORS.clear()
 previous=sys.argv[:];sys.argv=['run_pipeline.py','--a-dir',str(a),'--b-dir',str(b)]
 try:transform.main()
 finally:sys.argv=previous
 model.DICT=run/'dictionary';model.build_dictionary(common.read_csv(a/common.A_FILES['metric_definitions']))
 for n in model.SILVER_ORDER+[n for n,t in sd.TABLES.items() if t['layer']=='GOLD']:
  t=sd.TABLES[n];s=dict(name=n,layer=t['layer'].lower(),kind='standard',pk=t['pk'],fks=t['fks'],
   columns=[dict(name=c['phys'],sql=sd.DOMAINS[c['dmn']][1],nullable=c['null']) for c in t['cols']],
   ddl=model.table_ddl(t,physical_fk=True))
  table=from_csv(run/'exports'/s['layer']/(n+'.csv'),s)
  entries.append(delta_snapshot(run,table,s));say(s['layer']+' Delta '+n+' '+str(table.num_rows))
 quality(run,entries,a,b,croot)
 # Standard dictionary is queryable in MySQL meta as well as delivered in CSV/XLSX.
 for p in sorted((run/'dictionary').glob('*.csv')):
  df=common.read_csv(p);s=raw_spec('m_snapshot_'+p.stem,list(df));s.update(layer='meta',kind='dictionary')
  entries.append(delta_snapshot(run,raw_arrow([attach(df,'dictionary:'+p.name,sha(p),'utf-8-sig')],s),s))
 catalog=dict(run_id=runid,status='DELTA_PASS_MYSQL_PENDING',tables=entries,databases={l:'tz_'+l+'_'+runid for l in ['bronze','silver','gold','meta']},
  source_archives=EXPECTED_RAW,transform_version=sd.PIPELINE_VERSION,standard_version=sd.STD_VERSION,
  source_code_sha256={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*.py')) if '.venv' not in p.parts and 'runs' not in p.parts},
  limits=['A report metric mapping and B pre-recovery baseline are supplied handoffs, not rebuilt from their original builders.',
          'Raw cleanup and B stored-API recovery replayed; A financial details compared against replayed cleaned raw sources.',
          'Gold is the C integration baseline: topic divergence flags and AI target labels require a later analytical definition.',
          'No MySQL load has been performed by prepare.py. Local password entry is required.'])
 save(run/'catalog.json',catalog)
 from mysql_load import write_sql
 write_sql(run,catalog)
 save(run/'validation/delta_summary.json',dict(status='PASS',tables=len(entries),rows_by_layer={l:sum(x['rows'] for x in entries if x['layer']==l) for l in catalog['databases']},
   tables_by_layer={l:sum(x['layer']==l for x in entries) for l in catalog['databases']},all_snapshots_version=0,full_value_reconciliation=True))
 from finalize_metadata import finalize
 finalize(run)
 (HERE/'LATEST_RUN.txt').write_text(run.relative_to(HERE).as_posix(),encoding='utf-8')
 say('PREPARED '+str(run));return run

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,default=DEFAULT_PROJECT);ap.add_argument('--raw',type=Path,default=DEFAULT_RAW)
 ap.add_argument('--output',type=Path,default=HERE/'runs');ap.add_argument('--resume',type=Path);args=ap.parse_args()
 prepare(args.project.resolve(),args.raw.resolve(),args.output.resolve(),args.resume)
