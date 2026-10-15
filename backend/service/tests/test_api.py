import csv,io
from datetime import date
from decimal import Decimal
import pytest

def test_health_actual_scope(client):
 r=client.get('/health');assert r.status_code==200
 body=r.json();assert body['data']['read_only'] is True
 assert body['meta']['stock_count']==20 and body['meta']['data_final_date']=='2026-06-30'
 assert body['meta']['analysis_status']=='PENDING_C_DELIVERY'

def test_codes_and_numeric_strings(client):
 rows=client.get('/stocks').json()['data'];assert len(rows)==20
 r=next(r for r in rows if r['stock_cd']=='005930')
 assert isinstance(r['outstd_shr_qty'],str) and len(r['stock_cd'])==6
 assert client.get('/stocks',params={'q':'삼성전자'}).json()['data'][0]['stock_cd']=='005930'

def test_market_and_pagination(client):
 rows=client.get('/stocks',params={'market':'KOSDAQ','limit':2,'offset':1}).json()
 assert len(rows['data'])==2 and all(r['mkt_cd']=='KOSDAQ' for r in rows['data'])

def test_weekend_uses_observed_day(client):
 body=client.get('/stocks/compare',params={'as_of':'2026-06-27'}).json()
 assert len(body['data'])==20
 assert body['meta']['requested_as_of']=='2026-06-27'
 assert {r['trd_dt'] for r in body['data']}=={'2026-06-26'}

def test_pending_investor_preserves_price_and_null(client):
 r=client.get('/stocks/247540/daily',params={'start':'2026-04-16','end':'2026-04-16'}).json()['data'][0]
 assert r['close_prc'] is not None
 assert r['invstr_exist_yn']=='N' and r['frgn_net_buy_qty'] is None and r['inst_net_buy_qty'] is None
 assert r['connection']['miss_rsn_cd']=='INVESTOR_PENDING_REVIEW'

def test_unavailable_financials_are_not_zero(client):
 r=client.get('/stocks/000660/daily',params={'start':'2022-12-01','end':'2022-12-01'}).json()['data'][0]
 assert r['fin_avail_yn']=='N' and r['op_prft_ytd_amt'] is None and r['fin_rpt_id'] is None
 assert r['analysis'] is None

def test_all_financial_periods_retained(client):
 rows=client.get('/stocks/005930/financials').json()['data'];assert len(rows)==16
 assert any(r['pit_join_elig_yn']=='N' for r in rows)
 metrics=rows[0]['metrics'];assert len(metrics)==94
 assert {'YTD','PRIOR_YTD','ASOF'}<={r['prd_type_cd'] for r in metrics}
 revenue=next(r for r in metrics if r['mtrc_cd']=='REVENUE' and r['prd_type_cd']=='YTD')
 assert isinstance(revenue['mtrc_amt'],str) and Decimal(revenue['mtrc_amt'])>10**12

def test_financial_filter_is_strict_before_disclosure(client,csv_repo):
 reports=client.get('/stocks/005930/financials').json()['data']
 candidate=next(r for r in reports if r['pit_join_elig_yn']=='Y' and r['dscl_dt'] and csv_repo.min_date<r['dscl_dt']<csv_repo.max_date)
 result=client.get('/stocks/005930/financials',params={'as_of':candidate['dscl_dt']}).json()['data']
 assert candidate['fin_rpt_id'] not in {r['fin_rpt_id'] for r in result}
 assert all(r['dscl_dt']<candidate['dscl_dt'] for r in result)

def test_evidence_trace_and_pit(client):
 r=client.get('/analysis/005930/evidence',params={'as_of':'2026-06-30'}).json()['data']
 assert r['price_source']['src_file_path'] and r['price_source']['src_row_no']
 assert r['financial_report']['dscl_dt']<r['observation']['trd_dt']
 assert r['financial_report']['fin_rpt_id']==r['observation']['fin_rpt_id']

def test_quality_retains_open_case(client):
 body=client.get('/stocks/247540/quality',params={'start':'2026-04-16','end':'2026-04-16','limit':500}).json()
 assert body['data']['availability'][0]['invstr_exist_yn']=='N'
 assert any(r['resolve_stts_cd'] in ('OPEN','QUARANTINED') and '247540' in (r['rcrd_key_txt'] or '') for r in body['data']['issues'])

def test_quality_order_and_pagination_do_not_depend_on_source_row_order(client,csv_repo):
 from copy import copy
 from fastapi.testclient import TestClient
 from tz_api.main import create_app
 other=copy(csv_repo);other._cache=dict(csv_repo._cache)
 other._cache['s_dq_issue']=list(reversed(csv_repo.rows('s_dq_issue')))
 url='/stocks/247540/quality?start=2026-04-16&end=2026-04-16&limit=5&offset=1'
 with TestClient(create_app(repository=other)) as reordered:
  assert reordered.get(url).json()['data']==client.get(url).json()['data']

def test_all_mysql_verification_routes_are_source_order_independent(client,csv_repo,project):
 from fastapi.testclient import TestClient
 from tz_api.main import create_app
 from tz_api.repository import Repository
 from tz_api.settings import Settings
 other=Repository(Settings(project=project,backend='csv'))
 other.rows=lambda name:list(reversed(csv_repo.rows(name)))
 other.warm()
 urls=['/health','/stocks','/stocks/compare?as_of=2026-06-30','/stocks/005930/daily?start=2026-06-01&end=2026-06-30',
  '/stocks/005930/financials','/stocks/247540/quality?start=2026-04-16&end=2026-04-16',
  '/analysis/005930/evidence?as_of=2026-06-30','/exports/stocks/005930/daily.csv?start=2026-06-01&end=2026-06-30',
  '/exports/stocks/005930/financials.csv?year=2025&report_code=11011']
 with TestClient(create_app(repository=other)) as shuffled:
  for url in urls:
   actual=shuffled.get(url);expected=client.get(url)
   assert actual.status_code==expected.status_code==200,url
   assert (actual.content==expected.content if '.csv' in url else actual.json()['data']==expected.json()['data']),url

def test_daily_csv_matches_json_and_bom(client):
 params={'start':'2026-06-01','end':'2026-06-30'}
 j=client.get('/stocks/005930/daily',params=params).json()['data']
 response=client.get('/exports/stocks/005930/daily.csv',params=params)
 assert response.content.startswith(b'\xef\xbb\xbf')
 rows=list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
 assert len(rows)==len(j)
 for source,target in zip(j,rows):
  for k,v in target.items():assert v==('' if source[k] is None else source[k])

def test_financial_csv_grain_and_amount(client):
 params={'year':2025,'report_code':'11011'}
 report=client.get('/stocks/005930/financials',params=params).json()['data'][0]
 response=client.get('/exports/stocks/005930/financials.csv',params=params)
 rows=list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
 assert len(rows)==len(report['metrics'])==94
 lookup={(r['mtrc_cd'],r['prd_type_cd']):r for r in rows}
 assert all(lookup[(m['mtrc_cd'],m['prd_type_cd'])]['mtrc_amt']==(m['mtrc_amt'] or '') for m in report['metrics'])

@pytest.mark.parametrize('url,params,status',[
 ('/stocks/999999/daily',{},404),('/stocks/abc/daily',{},422),
 ('/stocks/005930/daily',{'start':'2026-02-30'},422),
 ('/stocks/005930/daily',{'start':'2026-06-30','end':'2026-06-01'},422),
 ('/stocks',{'market':'HACK'},422),('/stocks',{'limit':0},422),('/stocks',{'offset':-1},422),
 ('/stocks/compare',{'as_of':'2026-07-01'},422),('/exports/analysis/g_stock_daily_analysis.csv',{},409),
 ('/exports/analysis/unknown.csv',{},422)])
def test_errors_are_structured(client,url,params,status):
 response=client.get(url,params=params);assert response.status_code==status
 assert response.json()['error']['code']
 assert 'C:\\Users' not in response.text

def test_empty_range_is_valid_not_imputed(client):
 r=client.get('/stocks/005930/daily',params={'start':'2021-01-01','end':'2021-01-31'})
 assert r.status_code==200 and r.json()['data']==[] and r.json()['meta']['total']==0

def test_cors_allowlist_and_no_write_route(client):
 r=client.get('/stocks',headers={'Origin':'http://localhost:5173'})
 assert r.headers['access-control-allow-origin']=='http://localhost:5173'
 assert 'access-control-allow-origin' not in client.get('/stocks',headers={'Origin':'http://unknown.invalid'}).headers
 assert client.post('/stocks',json={}).status_code==405

def test_openapi_declares_supported_routes(client):
 schema=client.get('/openapi.json').json()
 assert '/stocks/{code}/daily' in schema['paths'] and '/analysis/{code}/evidence' in schema['paths']
 assert not any(method in operations for operations in schema['paths'].values() for method in ('post','put','patch','delete'))
