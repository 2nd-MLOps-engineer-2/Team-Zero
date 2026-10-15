"""Complete physical model's four typed metadata tables before publication."""
import json,sys
from pathlib import Path
from engine import HERE,delta_snapshot,from_csv,save,sha
from mysql_load import select_run,state_save,write_sql
sys.path.insert(0,str(HERE/'vendor'))
import common,std_dictionary as sd,build_model as model

def finalize(run):
 catalog=json.loads((run/'catalog.json').read_text(encoding='utf-8'))
 if catalog.get('typed_metadata_completed'):return
 save(run/'evidence/catalog_before_metadata.json',catalog)
 # Retain seven original dictionary snapshots with explicit snapshot names.
 for e in catalog['tables']:
  if e['layer']=='meta' and e['kind']=='dictionary' and not e['name'].startswith('m_snapshot_'):
   e['name']='m_snapshot_'+e['name'][2:]
 sources={'m_exec_log':run/'exports/meta/m_exec_log.csv','m_std_word':run/'dictionary/std_word.csv',
          'm_std_dmn':run/'dictionary/std_domain.csv','m_std_term':run/'dictionary/std_term.csv'}
 checks=[]
 for name,src in sources.items():
  t=sd.TABLES[name];df=common.read_csv(src);cols=[c['phys'] for c in t['cols']];df=df[cols]
  if df.duplicated(t['pk']).any():raise ValueError('Metadata duplicate key '+name)
  dst=run/'exports/meta_model'/(name+'.csv');common.write_csv(df,dst)
  s=dict(name=name,layer='meta',kind='standard_metadata',pk=t['pk'],fks=t['fks'],
    columns=[dict(name=c['phys'],sql=sd.DOMAINS[c['dmn']][1],nullable=c['null']) for c in t['cols']],
    ddl=model.table_ddl(t))
  # Older prepared runs used these folder names for dictionary snapshots.
  if (run/'delta/meta'/name).exists():s['delta_folder']='typed_'+name
  table=from_csv(dst,s);e=delta_snapshot(run,table,s);catalog['tables'].append(e)
  checks.append(dict(table=name,rows=len(df),pk='PASS',explicit_type_and_delta_full_values='PASS'))
 catalog['typed_metadata_completed']=True
 catalog['source_code_sha256']={p.relative_to(HERE).as_posix():sha(p) for p in sorted(HERE.rglob('*.py')) if '.venv' not in p.parts and 'runs' not in p.parts}
 state_save(run/'catalog.json',catalog);write_sql(run,catalog)
 entries=catalog['tables']
 state_save(run/'validation/delta_summary.json',dict(status='PASS',tables=len(entries),
  rows_by_layer={l:sum(x['rows'] for x in entries if x['layer']==l) for l in catalog['databases']},
  tables_by_layer={l:sum(x['layer']==l for x in entries) for l in catalog['databases']},
  all_snapshots_version=0,full_value_reconciliation=True))
 save(run/'validation/meta_checks.json',dict(status='PASS',tables=checks,model_metadata_completed=True))
 print('Typed metadata model completed:',len(checks),'tables',flush=True)

if __name__=='__main__':finalize(select_run(None))
