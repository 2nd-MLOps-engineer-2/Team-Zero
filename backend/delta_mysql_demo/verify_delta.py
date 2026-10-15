"""Read-only verification of the prepared Delta table and source hash."""
from pathlib import Path
import argparse,json,hashlib
from deltalake import DeltaTable
from price_demo import validate,SCHEMA

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path);a=p.parse_args()
    candidates=sorted((Path(__file__).resolve().parent/'runs').glob('*/delta_validation.json'))
    if not a.run and len(candidates)!=1:raise ValueError('Specify --run')
    run=a.run or candidates[0].parent
    report=json.loads((run/'delta_validation.json').read_text(encoding='utf-8'))
    source=Path(report['input_path'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=report['input_sha256']:raise ValueError('Input source changed')
    dt=DeltaTable(str(run/report['delta_relative_path']),version=report['delta_version'])
    table=dt.to_pyarrow_table()
    if table.schema.names!=SCHEMA.names:raise ValueError('Delta columns differ')
    actual=validate(table.to_pylist())
    if actual!=report['delta_validation']:raise ValueError('Delta values differ')
    print(json.dumps(dict(status='PASS',rows=actual['rows'],columns=len(SCHEMA),companies=actual['companies'],
                         delta_version=dt.version(),parquet_files=len(dt.file_uris()),input_unchanged=True,
                         full_value_digest=actual['business_and_provenance_digest']),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
