"""C's pinned expected CSV hashes -> complete API/CSV values -> small A handoff examples."""
import argparse
import csv
from decimal import Decimal
import io
import json
from pathlib import Path
from fastapi.testclient import TestClient
from tz_api.main import create_app
from tz_api.repository import Repository,file_hash
from tz_api.settings import Settings


def verify(project,artifact,expected_evidence,output,backend='csv'):
    expected=json.loads(expected_evidence.read_text(encoding='utf-8'))
    repo=Repository(Settings(project=project,backend=backend,analysis_dir=artifact)).warm()
    checks=[]
    output.mkdir(parents=True,exist_ok=False)
    with TestClient(create_app(repository=repo)) as client:
        for name,item in repo.analysis['entries'].items():
            if file_hash(item['path'])!=expected['output_sha256'][name+'.csv']:
                raise AssertionError('Output differs from pinned C evidence: '+name)
            with item['path'].open(encoding='utf-8-sig',newline='') as f:
                source=list(csv.DictReader(f))
            response=client.get('/exports/analysis/'+name+'.csv')
            assert response.status_code==200
            exported=list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
            columns=item['columns'];pk=item['primary_key']
            keyed=lambda rows:{tuple(r[k] for k in pk):r for r in rows}
            left,right=keyed(source),keyed(exported)
            assert set(left)==set(right) and len(source)==len(exported)==len(left)
            assert all(list(row)==[c['name'] for c in columns] for row in exported)
            for key,row in left.items():
                for col in columns:
                    original,actual=row[col['name']],right[key][col['name']]
                    if original and col['sql'].startswith(('DECIMAL','INT','BIGINT')):
                        assert Decimal(original)==Decimal(actual),(name,key,col['name'])
                    else:assert original==actual,(name,key,col['name'])
            checks.append(dict(name=name+'.C_CSV_API_all_values',rows=len(source),values=len(source)*len(columns),status='PASS'))
        requests={
            'stocks':'/stocks',
            'compare':'/stocks/compare?as_of=2026-06-30',
            'daily':'/stocks/005930/daily?start=2026-06-01&end=2026-06-30',
            'financials':'/stocks/005930/financials?year=2025&report_code=11011&fs_div=CFS&as_of=2026-06-30',
            'evidence':'/analysis/005930/evidence?as_of=2026-06-30',
            'quality':'/stocks/247540/quality?start=2026-04-16&end=2026-04-16&limit=5',
            'missing_investor':'/stocks/247540/daily?start=2026-04-16&end=2026-04-16',
            'empty':'/stocks/005930/daily?start=2021-01-01&end=2021-01-02',
            'invalid_date':'/stocks/005930/daily?start=2026-02-30',
            'unknown_stock':'/stocks/999999/daily'}
        samples={}
        for name,url in requests.items():
            response=client.get(url)
            assert response.status_code==({'invalid_date':422,'unknown_stock':404}.get(name,200))
            body=response.json();samples[name]=body
            (output/(name+'.json')).write_text(json.dumps(dict(request=url,response=body,fixture_source='actual verified C calculation and immutable handoff'),ensure_ascii=False,indent=2),encoding='utf-8')
            checks.append(dict(name=name,http_status=response.status_code,status='PASS'))
        assert len(samples['stocks']['data'])==len(samples['compare']['data'])==20
        for row in samples['compare']['data']:
            assert row['analysis']==repo.analysis['daily'][(row['stock_cd'],row['trd_dt'])]
        daily=samples['daily'];assert daily['meta']['price_base_date']=='2026-06-01'
        assert daily['data'][0]['stock_base100']==daily['data'][0]['market_base100']=='100.00000000'
        chart=client.get('/exports/stocks/005930/chart.csv?start=2026-06-01&end=2026-06-30')
        chart_rows=list(csv.DictReader(io.StringIO(chart.content.decode('utf-8-sig'))))
        assert len(chart_rows)==len(daily['data'])
        for actual,row in zip(chart_rows,daily['data']):
            assert all(v==('' if row[k] is None else row[k]) for k,v in actual.items())
        (output/'price_chart.csv').write_bytes(chart.content)
        observation=samples['evidence']['data']['observation']
        selected=observation['analysis']
        assert selected==repo.analysis['daily'][('005930','2026-06-30')]
        report=samples['evidence']['data']['financial_report']
        assert report['analysis']==repo.analysis['financial'][report['fin_rpt_id']]
        assert report['dscl_dt']<'2026-06-30'
        assert samples['missing_investor']['data'][0]['frgn_net_buy_qty'] is None
        assert samples['empty']['data']==[] and samples['empty']['meta']['price_base_date'] is None
        (output/'openapi.json').write_text(json.dumps(client.get('/openapi.json').json(),ensure_ascii=False,indent=2),encoding='utf-8')
        expectations=dict(company='005930',as_of='2026-06-30',meta=samples['evidence']['meta'],
                          observation={k:observation[k] for k in ('stock_cd','trd_dt','close_prc','fin_rpt_id','dscl_dt','rev_ytd_amt','op_prft_ytd_amt','net_incm_ytd_amt','op_cf_ytd_amt','frgn_net_buy_qty','inst_net_buy_qty')},
                          analysis={k:selected[k] for k in ('rev_yoy_rt','op_margin_rt','event_excess_rt','event_base_dt','co_move_cd','co_move_stts_cd','joint_improve_yn','joint_improve_stts_cd','frgn_flow_20d_rt','inst_flow_20d_rt')},
                          chart_first=chart_rows[0],chart_last=chart_rows[-1])
        (output/'expected_values.json').write_text(json.dumps(expectations,ensure_ascii=False,indent=2),encoding='utf-8')
    report=dict(status='PASS',source_backend=backend,checks=checks,
                c_calculation_version=repo.calculation_version,input_version=repo.handoff_version,
                analysis_data_version=repo.analysis['artifact_version'],expected_c_output_sha256=expected['output_sha256'],
                chart_csv_matches_api=True,new_c_mysql_load_performed=False)
    (output/'s4_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2));print('Evidence:',output)
    return report


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project-root',type=Path,default=Settings().project)
    ap.add_argument('--analysis-dir',type=Path,required=True)
    ap.add_argument('--expected-evidence',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--backend',choices=['csv','delta'],default='csv')
    args=ap.parse_args()
    verify(args.project_root.resolve(),args.analysis_dir.resolve(),args.expected_evidence.resolve(),args.output.resolve(),args.backend)
