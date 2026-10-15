"""Package C's native CSV/schema/validation output without altering calculated values."""
import argparse
import json
import shutil
from pathlib import Path
from tz_api.analysis import CONTRACT, TABLES, load_bundle
from tz_api.repository import BASE_TABLES, Repository, file_hash
from tz_api.settings import Settings


def package(source, output, project):
    source, output = Path(source).resolve(), Path(output).resolve()
    project = Path(project).resolve()
    if output.exists():
        raise ValueError('Refusing existing C artifact target')
    if output == source or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError('C source and artifact target must be separate')
    repo = Repository(Settings(project=project, backend='csv')).warm()
    validation = json.loads((source/'validation.json').read_text(encoding='utf-8'))
    schemas = json.loads((source/'schema.json').read_text(encoding='utf-8'))
    checks = validation.get('gold_checks', {})
    required = {'financial_rows','daily_rows','financial_duplicate_keys','daily_duplicate_keys',
                'pit_date_violations','source_close_mismatches','top_level_flow_mismatches','missing_financial_rows'}
    if not required <= set(checks) or not all(checks[k].get('pass') is True for k in required):
        raise ValueError('C Gold checks are missing or failed')
    if any(item['violations'] for item in validation['silver_integrity']):
        raise ValueError('C Silver integrity failed')
    expected = {f'04_output/silver/{name}.csv' for name in BASE_TABLES if name.startswith('s_')}
    expected |= {'04_output/gold/g_ai_stock_daily.csv','02_standard_dictionary/std_term.csv'}
    if set(validation.get('input_sha256', {})) != expected:
        raise ValueError('C input inventory differs from baseline')
    for relative, expected_hash in validation['input_sha256'].items():
        if relative not in repo.manifest or repo.manifest[relative]['sha256'] != expected_hash:
            raise ValueError('C input version differs from verified baseline: '+relative)
        if file_hash(repo.settings.data_dir/relative) != expected_hash:
            raise ValueError('C input values changed: '+relative)
    if set(schemas) != set(TABLES) or not validation.get('calc_ver'):
        raise ValueError('C schema or calculation version is missing')
    manifest = dict(contract_version=CONTRACT, calculation_version=validation['calc_ver'],
                    input_version=repo.handoff_version, tables={},
                    c_validation_sha256=file_hash(source/'validation.json'),
                    c_schema_sha256=file_hash(source/'schema.json'))
    for name, pk in TABLES.items():
        path=source/(name+'.csv');spec=schemas[name]
        if spec['primary_key'] != pk or file_hash(path) != validation['output_sha256'][path.name]:
            raise ValueError('C output hash or primary key mismatch: '+name)
        columns=[dict(name=c['name'],sql=c['type'],nullable=c['nullable']) for c in spec['columns']]
        manifest['tables'][name]=dict(file=path.name,sha256=file_hash(path),rows=spec['rows'],
                                      primary_key=pk,columns=columns)
    output.mkdir(parents=True, exist_ok=False)
    for name in TABLES:
        shutil.copyfile(source/(name+'.csv'),output/(name+'.csv'))
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    load_bundle(output,repo)
    return output,manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--project-root',type=Path,default=Settings().project)
    args=parser.parse_args()
    output,_=package(args.source,args.output,args.project_root)
    print('PASS: unchanged C outputs validated and packaged:',output)
