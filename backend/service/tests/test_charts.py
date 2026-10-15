import csv
import io
from decimal import Decimal, ROUND_HALF_UP
from tz_api.charts import normalize_prices


def test_same_base_date_and_no_backfill():
    rows=[dict(trd_dt='2026-01-02',close_prc='50',idx_close_prc=None),
          dict(trd_dt='2026-01-05',close_prc='100',idx_close_prc='200'),
          dict(trd_dt='2026-01-06',close_prc='125',idx_close_prc='210'),
          dict(trd_dt='2026-01-07',close_prc='0',idx_close_prc='220')]
    result,meta=normalize_prices(list(reversed(rows)))
    assert meta['price_base_date']=='2026-01-05'
    assert result[0]['stock_base100'] is None and result[0]['price_chart_stts_cd']=='BEFORE_BASE_DATE'
    assert result[1]['stock_base100']==result[1]['market_base100']=='100.00000000'
    assert result[2]['stock_base100']=='125.00000000' and result[2]['market_base100']=='105.00000000'
    assert result[3]['stock_base100'] is None and result[3]['market_base100']=='110.00000000'
    assert result[3]['price_chart_stts_cd']=='PARTIAL'
    assert 'stock_base100' not in rows[0]


def test_no_common_base_or_empty():
    for rows in ([],[dict(trd_dt='2026-01-02',close_prc='-1',idx_close_prc='2')],
                 [dict(trd_dt='2026-01-02',close_prc='NaN',idx_close_prc='Infinity')]):
        result,meta=normalize_prices(rows)
        assert meta['price_base_date'] is None
        assert all(r['stock_base100'] is None and r['market_base100'] is None
                   and r['price_chart_stts_cd']=='NO_COMMON_BASE' for r in result)


def test_daily_base_before_pagination_and_chart_csv_matches(client):
    url='/stocks/005930/daily?start=2026-06-01&end=2026-06-30'
    all_rows=client.get(url).json()
    page=client.get(url+'&limit=2&offset=2').json()
    assert page['meta']['price_base_date']==all_rows['meta']['price_base_date']=='2026-06-01'
    assert page['data']==all_rows['data'][2:4]
    assert all_rows['data'][0]['stock_base100']==all_rows['data'][0]['market_base100']=='100.00000000'
    response=client.get('/exports/stocks/005930/chart.csv?start=2026-06-01&end=2026-06-30')
    assert response.headers['x-price-base-date']=='2026-06-01'
    rows=list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert len(rows)==len(all_rows['data'])
    for actual,expected in zip(rows,all_rows['data']):
        assert all(v==('' if expected[k] is None else expected[k]) for k,v in actual.items())
    last=all_rows['data'][-1];base=all_rows['data'][0]
    assert Decimal(last['stock_base100'])==(Decimal(last['close_prc'])/Decimal(base['close_prc'])*100).quantize(Decimal('0.00000001'),rounding=ROUND_HALF_UP)


def test_weekend_window_and_empty_csv(client):
    body=client.get('/stocks/005930/daily?start=2026-06-06&end=2026-06-10').json()
    assert body['meta']['price_base_date']=='2026-06-08'
    assert body['data'][0]['stock_base100']==body['data'][0]['market_base100']=='100.00000000'
    body=client.get('/stocks/005930/daily?start=2021-01-01&end=2021-01-02').json()
    assert body['data']==[] and body['meta']['price_base_date'] is None
    response=client.get('/exports/stocks/005930/chart.csv?start=2021-01-01&end=2021-01-02')
    assert len(response.content.decode('utf-8-sig').splitlines())==1
