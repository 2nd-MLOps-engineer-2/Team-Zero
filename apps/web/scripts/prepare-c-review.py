"""Read C generated outputs for browser response tests. No database/API or business calculations.
Run from repository root with --output under build; output is local-only evidence.
"""
import argparse
import csv
import json
from pathlib import Path

root=Path(__file__).resolve().parents[3]
ap=argparse.ArgumentParser()
ap.add_argument('--c-output',type=Path,required=True)
ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args()
target=args.output.resolve()
if root/'build' not in target.parents:
    ap.error('Review output must be inside repository build/')
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return [{k:v if v!='' else None for k,v in r.items()} for r in csv.DictReader(f)]
stocks=read(root/'data/03_C_integration_20261014/04_output/silver/s_stock.csv')
stocks.sort(key=lambda r:r['stock_cd']!='005930')
daily=read(args.c_output/'g_stock_daily_analysis.csv')
financial=read(args.c_output/'g_fin_rpt_analysis.csv')
compare=[dict(r,stock_nm=next(s['stock_nm'] for s in stocks if s['stock_cd']==r['stock_cd'])) for r in daily if r['trd_dt']=='2026-06-30']
selected=[dict(r,stock_base100=None,market_base100=None) for r in daily if r['stock_cd']=='005930' and r['trd_dt']>='2026-06-26']
reports=[r for r in financial if r['stock_cd']=='005930' and r['bsns_yr'] in ['2024','2025'] and r['rpt_cd']=='11011' and r['fs_div_cd']=='CFS' and r['dscl_dt'] and r['dscl_dt']<'2026-06-30']
latest=selected[-1];report=next(r for r in financial if r['fin_rpt_id']==latest['fin_rpt_id'])
evidence=dict(latest,lineage=[dict(layer='Silver',status='제공',file=report['src_file_path'],row=report['src_row_no'],key=report['fin_rpt_id'],version=report['src_ver'],reason='C 제공 원천 메타')],
              numerator=None,denominator=report['rev_prior_ytd_amt'],formula='C 제공 rev_yoy_rt / event_excess_rt · 분자 미제공, 화면에서 재계산하지 않음',threshold='0',review='실제 C 계산/공개 인계본. B API 대신 브라우저 테스트 응답으로 주입')
bundle=dict(meta=dict(schema_version='a-proposal-1',synthetic=False,data_end='2026-06-30',input_version='03_C_integration_20261014',calc_version='c-gold-0.1.0',price_base_date=None),stocks=stocks,compare=compare,daily=selected,financials=reports,evidence=[evidence])
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(target),'compare_rows':len(compare),'daily_rows':len(selected),'financial_rows':len(reports)}))
