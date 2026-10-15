"""UI-only synthetic values. Only stock identity fields come from the fixed snapshot."""
import csv
import json
from pathlib import Path

web = Path(__file__).resolve().parents[1]
root = web.parents[1]
with (root / 'data/03_C_integration_20261014/04_output/silver/s_stock.csv').open(encoding='utf-8-sig') as f:
    stocks = [{k: r[k] for k in ('stock_cd', 'stock_nm', 'mkt_cd')} for r in csv.DictReader(f)]
meta = dict(schema_version='a-proposal-1', synthetic=True, data_end='2026-06-30',
            input_version='03_C_integration_20261014 (종목 식별자만 참조)', calc_version='synthetic-ui-v1',
            scope='보유 20종목 · 합성 수치 · 비교 기준일 2026-06-30', price_base_date='2026-06-01', units='금액 원 / 수급 주 / 비율 소수')
result = dict(meta=meta, stocks=stocks, compare=[], daily={}, financials={}, evidence={})
for i, stock in enumerate(stocks):
    code = stock['stock_cd']
    unavailable = i % 7 == 3
    growth = [0.12, -0.08, 0, None][i % 4]
    excess = [0.054, 0.023, 0, None][i % 4]
    classification = ['개선·강세 동행', '둔화·강세 괴리', '중립', '판단 불가'][i % 4]
    result['compare'].append(dict(**stock, as_of='2026-06-30', revenue_growth_rt=growth,
        excess_return_rt=excess, classification=classification, dscl_dt='2026-03-20',
        dscl_elps_day_cnt=102, observation_start='2026-03-19', observation_end='2026-06-30',
        reason='기간 미검증' if growth is None else '합성 예시 · 임계값 0'))
    result['daily'][code] = [dict(stock_cd=code, trd_dt=f'2026-06-{day:02}',
        stock_base100=val, market_base100=market,
        frgn_net_buy_qty=None if j == 2 else str((j-2)*12300),
        inst_net_buy_qty=str((3-j)*7600), frgn_hold_rt=None if j == 2 else 0.42+j/1000,
        status='미연결' if j == 2 else '가용', reason='합성 수급 누락 예시' if j == 2 else None)
        for j, (day, val, market) in enumerate([(1,100,100),(5,101,100.4),(10,99,101),(15,104,102),(22,106,102.5),(30,108,103)])]
    result['financials'][code] = [dict(stock_cd=code, fin_rpt_id=f'SAMPLE-{code}-{year}',
        bsns_yr=str(year), rpt_cd='11011', fs_div_cd='CFS', period_type='YTD',
        prd_start_dt=f'{year}-01-01', prd_end_dt=f'{year}-12-31', dscl_dt=f'{year+1}-03-20',
        period_status='검토 중' if unavailable else '검증됨 (합성)',
        rev_ytd_amt=str(10000000000000 if year == 2024 else {0:11200000000000,1:9200000000000,2:10000000000000,3:10000000000000}[i % 4]),
        op_prft_ytd_amt='0' if i == 2 else str(1800000000000+offset),
        net_incm_ytd_amt=str(1300000000000+offset),
        op_cf_ytd_amt=None if unavailable else str(2200000000000+offset),
        reason='현금흐름 기간 미검증' if unavailable else None)
        for year, offset in [(2024,0),(2025,200000000000)]]
    result['evidence'][code] = dict(stock_cd=code, as_of='2026-06-30', classification=classification,
        revenue_growth_rt=growth, excess_return_rt=excess, fin_rpt_id=f'SAMPLE-{code}-2025',
        dscl_dt='2026-03-20', observation_start='2026-03-19', observation_end='2026-06-30',
        numerator=str({0:1200000000000,1:-800000000000,2:0}[i % 4]) if growth is not None else None,
        denominator='10000000000000' if growth is not None else None,
        formula='(당기 YTD 매출 − 전년동기 YTD 매출) / 전년동기 YTD 매출. 공시 후 시장 대비 성과는 별도 제공값.',
        threshold='0 (제안)', calc_status='계산 불가' if growth is None else '합성 계산값',
        review='공시 이후 구간의 길이, 기간 적격, 기업행동 및 수급 누락을 함께 검토하세요.',
        lineage=[dict(layer='Bronze',status='미확보',file=None,row=None,key=None,version=None,reason='원천 CSV·공시 ZIP 실물 미포함'),
                 dict(layer='Silver',status='검토 중',file=None,row=None,key=f'{code} / SAMPLE',version=None,reason='합성 검토 예시 · 원천 행 미제공'),
                 dict(layer='Silver',status='격리',file=None,row=None,key=None,version=None,reason='합성 격리 예시 · 해당 값 사용 제외'),
                 dict(layer='Gold',status='계산 불가' if growth is None else '합성',file=None,row=None,key=f'SAMPLE-{code}-2025',version='synthetic-ui-v1',reason='실제 Gold 계산 결과 아님')])
target = web / 'src/fixtures/sample.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'Wrote synthetic fixture for {len(stocks)} stock identities: {target}')
