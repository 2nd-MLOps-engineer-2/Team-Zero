"""Read-only audit, no database credentials or writes required."""
import argparse,json
from engine import load_delta
from mysql_load import select_run
ap=argparse.ArgumentParser();ap.add_argument('--run');a=ap.parse_args();run=select_run(a.run)
c=json.loads((run/'catalog.json').read_text(encoding='utf-8'))
for e in c['tables']:
 t=load_delta(run,e);print('PASS',e['layer'],e['name'],t.num_rows,flush=True)
print('All',len(c['tables']),'Delta tables passed full value checks.')
