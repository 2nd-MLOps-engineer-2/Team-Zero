"""Read-only source/run copy audit; optional new audit report in the run folder."""
import argparse,json,sys,importlib.metadata
from pathlib import Path
from engine import HERE,sha,save
from mysql_load import select_run
ap=argparse.ArgumentParser();ap.add_argument('--prepared-source',type=Path,required=True);ap.add_argument('--save-report',action='store_true');a=ap.parse_args()
run=select_run(None);catalog=json.loads((run/'catalog.json').read_text(encoding='utf-8'))
source=a.prepared_source/run.name
files=[p for p in source.rglob('*') if p.is_file()]
bad=[p.relative_to(source).as_posix() for p in files if not (run/p.relative_to(source)).is_file() or sha(p)!=sha(run/p.relative_to(source))]
codebad=[rel for rel,h in catalog['source_code_sha256'].items() if sha(HERE/rel)!=h]
deltabad=[]
for e in catalog['tables']:
 for rel,h in e['delta_files'].items():
  if sha(run/e['delta_path']/rel)!=h:deltabad.append(e['name']+':'+rel)
versions={n:importlib.metadata.version(n) for n in ['pandas','pyarrow','deltalake','PyMySQL','openpyxl']}
report=dict(status='PASS' if not bad and not codebad and not deltabad else 'FAIL',
 copied_run_files_checked=len(files),copied_run_mismatches=bad,source_code_files_checked=len(catalog['source_code_sha256']),source_code_mismatches=codebad,
 delta_tables_checked=len(catalog['tables']),delta_file_mismatches=deltabad,python=sys.version,runtime_versions=versions,
 mysql_status='PENDING' if not (run/'validation/mysql_validation.json').exists() else 'SEE_MYSQL_REPORT')
if a.save_report:save(run/'validation/published_copy_audit.json',report)
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS':raise SystemExit(1)
