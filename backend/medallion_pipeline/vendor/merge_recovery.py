"""Merge verified API rows into baseline silver; stdlib only, no API calls.
Run from 111: python3 code/merge_recovery.py --output silver
Baseline: inputs/silver_before_api_merge. Review exclusion is intentional.
"""
import argparse,csv,json,hashlib
from pathlib import Path
from decimal import Decimal
from datetime import date,datetime
from collections import Counter
BASE=Path(__file__).resolve().parents[1]
VERSION='toss-silver-1.1.0'
EXTRA=['source_kind','fetched_at','api_raw_file','api_record_path']
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,rows,fields):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def run(out):
 old=BASE/'inputs/silver_before_api_merge';api=BASE/'inputs/additional_data';out.mkdir(parents=True,exist_ok=True)
 for name,h in json.loads((old/'output_sha256.json').read_text()).items():assert sha(old/name)==h
 for entry in json.loads((api/'requests_manifest.json').read_text()):assert sha(api/entry['raw_file'])==entry['sha256']
 schema=json.loads((old/'schema.json').read_text());data={n:read(old/(n+'.csv')) for n in schema}
 before={n:len(rows) for n,rows in data.items()}
 for name,table in schema.items():
  for field in table['fields']:
   if field['name']=='bronze_row':field['nullable']=True;field['source']='브론즈 데이터 행 번호; API 재조회 행은 NULL'
   if field['name']=='pipeline_version':field['source']=VERSION
   if field['name']=='source_version':field['source']='브론즈는 패키지 SHA256SUMS 해시, API는 api_raw_file SHA-256'
   if name=='cfd_daily' and field['name'] in ['buy_balance_rate','sell_balance_rate']:field['unit']='상장주식수 대비 소수 비율(0.0002 = 0.02%)'
  table['fields'] += [dict(name=f,type='TIMESTAMPTZ' if f=='fetched_at' else 'TEXT',nullable=f!='source_kind',unit='해당 없음',source={'source_kind':'bronze / toss_api_requery','fetched_at':'requests_manifest.fetched_at','api_raw_file':'additional_data 기준 API 원응답 상대 경로','api_record_path':'API 원응답 내부 기록 경로'}[f]) for f in EXTRA]
 for rows in data.values():
  for r in rows:r.update(pipeline_version=VERSION,source_kind='bronze',fetched_at='',api_raw_file='',api_record_path='')
 candidates=read(api/'recovery_candidates_reviewed.csv');accepted=[r for r in candidates if r['review_status']=='MATCHED_RECOVERY_CANDIDATE'];pending=[r for r in candidates if r['review_status']!='MATCHED_RECOVERY_CANDIDATE']
 assert len(accepted)==740 and len(pending)==1
 audit=[];rawcache={}
 for c in accepted:
  r=json.loads(c['api_record_json']);file=c['source_file'];inv=file.endswith('investor_trading.csv');idx=file.endswith('index.csv')
  raw=rawcache.setdefault(c['raw_file'],json.loads((api/c['raw_file']).read_text()));arr=raw.get('result',raw)['records' if inv else 'candles']
  matches=[i for i,x in enumerate(arr) if x==r];assert len(matches)==1
  path='$.result.'+('records' if inv else 'candles')+'['+str(matches[0])+']' if 'result' in raw else '$.'+('records' if inv else 'candles')+'['+str(matches[0])+']'
  m={'source_file':file,'source_row':c['source_row'],'bronze_row':'','source_version':'sha256:'+sha(api/c['raw_file']),'pipeline_version':VERSION,'source_kind':'toss_api_requery','fetched_at':c['fetched_at'],'api_raw_file':c['raw_file'],'api_record_path':path}
  b={'symbol':c['symbol'],'trade_date':c['trade_date']}|m
  if not inv:
   row=b|{'timestamp':r['timestamp'],**{dest:r[src] for dest,src in [('open_price','openPrice'),('high_price','highPrice'),('low_price','lowPrice'),('close_price','closePrice'),('volume','volume')]}}
   if idx:row['index_code']=row.pop('symbol');name='market_index_daily'
   else:row['currency']=r['currency'];name='stock_daily_price'
   data[name].append(row)
  else:
   data['investor_source_daily'].append(b|{'updated_at':r['updatedAt'],**{f:json.dumps(r[f],ensure_ascii=False) if r[f] is not None else '' for f in ['individual','foreigner','institution','otherCorporation','foreignerHolding','cfd']}})
   for f in ['individual','foreigner','institution','otherCorporation']:
    nodes=[(f,'','top_level','$',r[f])]
    if f=='institution':nodes += [(t,'institution','institution_detail','$.breakdown.'+t,x) for t,x in r[f]['breakdown'].items()]
    for typ,parent,level,jpath,node in nodes:
     data['investor_trading_daily'].append(b|{'investor_type':typ,'parent_type':parent,'aggregation_level':level,'buy_volume':node['buyVolume'],'sell_volume':node['sellVolume'],'net_buy_volume':node['netBuyVolume'],'source_column':f,'json_path':jpath})
   obj=r['foreignerHolding'];data['foreign_holding_daily'].append(b|{'holding_quantity':obj['holdingQuantity'],'limit_quantity':obj['limitQuantity'],'holding_rate':obj['holdingRate'],'source_column':'foreignerHolding','json_path':'$'})
   if r['cfd'] is not None:
    obj=r['cfd'];data['cfd_daily'].append(b|{dest:obj[src] for dest,src in [('buy_balance_quantity','buyBalanceQuantity'),('buy_balance_rate','buyBalanceRate'),('sell_balance_quantity','sellBalanceQuantity'),('sell_balance_rate','sellBalanceRate')]}|{'source_column':'cfd','json_path':'$'})
  audit.append({f:c[f] for f in ['source_file','source_row','symbol','trade_date','affected_columns','review_status']}|m)
 prices={(r['symbol'],r['trade_date']):r for r in data['stock_daily_price']};investors={(r['symbol'],r['trade_date']):r for r in data['investor_source_daily']}
 pendingkeys={(r['symbol'],r['trade_date']) for r in pending};availability=[];state=Counter()
 for key in sorted(prices.keys()|investors.keys()):
  p,v=key in prices,key in investors;state['both' if p and v else 'price_only' if p else 'investor_only']+=1
  origin=prices.get(key) or investors[key]
  availability.append({'symbol':key[0],'trade_date':key[1],'has_price':str(p).lower(),'has_investor_data':str(v).lower(),'missing_reason':'' if p and v else 'investor_api_candidate_requires_review' if key in pendingkeys else 'missing_data','missing_issue_codes':'' if p and v else 'UPDATED_AT_MISMATCH_REVIEW'}|{f:origin[f] for f in ['source_file','source_row','bronze_row','source_version','pipeline_version']+EXTRA})
 data['price_investor_availability']=availability
 assert state=={'both':17439,'price_only':1}
 assert len(data['stock_daily_price'])==17440 and len(data['market_index_daily'])==1744
 assert len(data['investor_source_daily'])==17439 and len(data['investor_trading_daily'])==17439*11
 dictionary=[];sql=[]
 for name,rows in data.items():
  table=schema[name];fields=[f['name'] for f in table['fields']];keys=table['primary_key'];seen=set()
  rows.sort(key=lambda r:tuple(r[f] for f in keys))
  for r in rows:
   key=tuple(r[f] for f in keys);assert key not in seen;seen.add(key)
   for field in table['fields']:
    value=r[field['name']];assert value!='' or field['nullable'],(name,field['name'])
    if not value:continue
    typ=field['type']
    if typ in ['NUMERIC','BIGINT']:
     x=Decimal(value);assert x.is_finite()
     if typ=='BIGINT':assert x==x.to_integral_value()
    if typ=='DATE':date.fromisoformat(value)
    if typ=='TIMESTAMPTZ':assert datetime.fromisoformat(value).utcoffset() is not None
    if typ=='BOOLEAN':assert value.lower() in ['true','false']
  if name in ['stock_daily_price','market_index_daily']:
   for r in rows:
    o,h,l,c=[Decimal(r[f]) for f in ['open_price','high_price','low_price','close_price']];assert 0<=l<=min(o,c)<=max(o,c)<=h and Decimal(r['volume'])>=0
  if name=='investor_trading_daily':
   for r in rows:assert Decimal(r['buy_volume'])>=0 and Decimal(r['sell_volume'])>=0 and Decimal(r['buy_volume'])-Decimal(r['sell_volume'])==Decimal(r['net_buy_volume'])
  if name=='foreign_holding_daily':
   for r in rows:assert 0<=Decimal(r['holding_quantity'])<=Decimal(r['limit_quantity']) and 0<=Decimal(r['holding_rate'])<=1
  write(out/(name+'.csv'),rows,fields);assert read(out/(name+'.csv'))==rows
  table['rows']=len(rows);dictionary.extend({'table':name,**f} for f in table['fields'])
  cols=['  "'+f['name']+'" '+f['type']+('' if f['nullable'] else ' NOT NULL') for f in table['fields']]
  cols.append('  PRIMARY KEY ('+', '.join('"'+f+'"' for f in keys)+')');sql.append('CREATE TABLE "'+name+'" (\n'+',\n'.join(cols)+'\n);')
  # Independent source-preservation check: baseline business fields remain identical.
  if name!='price_investor_availability':
   merged={tuple(r[f] for f in keys):r for r in rows}
   for original in read(old/(name+'.csv')):
    actual=merged[tuple(original[f] for f in keys)]
    for f in original:
     if f!='pipeline_version':assert actual[f]==original[f],(name,f)
  # Verify new business fields directly against persisted original API JSON.
  for r in rows:
   if r['source_kind']!='toss_api_requery' or name=='price_investor_availability':continue
   raw=json.loads((api/r['api_raw_file']).read_text());collection='records' if name not in ['stock_daily_price','market_index_daily'] else 'candles'
   index=int(r['api_record_path'].split('[')[-1][:-1]);src=raw.get('result',raw)[collection][index]
   if collection=='candles':
    for f,s in [('open_price','openPrice'),('high_price','highPrice'),('low_price','lowPrice'),('close_price','closePrice'),('volume','volume')]:assert r[f]==src[s]
   elif name=='investor_source_daily':
    assert r['updated_at']==src['updatedAt']
    for f in ['individual','foreigner','institution','otherCorporation','foreignerHolding','cfd']:assert (json.loads(r[f]) if r[f] else None)==src[f]
   else:
    obj=src[r['source_column']]
    for part in r['json_path'].split('.')[1:]:obj=obj[part]
    pairs={'investor_trading_daily':[('buy_volume','buyVolume'),('sell_volume','sellVolume'),('net_buy_volume','netBuyVolume')],'foreign_holding_daily':[('holding_quantity','holdingQuantity'),('limit_quantity','limitQuantity'),('holding_rate','holdingRate')],'cfd_daily':[('buy_balance_quantity','buyBalanceQuantity'),('buy_balance_rate','buyBalanceRate'),('sell_balance_quantity','sellBalanceQuantity'),('sell_balance_rate','sellBalanceRate')]}[name]
    for f,s in pairs:assert r[f]==obj[s]
 # Group/reference and institution consistency checks on merged data.
 symbols={r['symbol'] for r in data['security_master']}
 sourcekeys=set(investors)
 grouped={}
 for r in data['investor_trading_daily']:
  k=(r['symbol'],r['trade_date']);assert k in sourcekeys
  grouped.setdefault(k,[]).append(r)
 for k,rows in grouped.items():
  assert len(rows)==11
  inst=next(r for r in rows if r['investor_type']=='institution')
  detail=[r for r in rows if r['aggregation_level']=='institution_detail'];assert len(detail)==7
  for f in ['buy_volume','sell_volume','net_buy_volume']:assert sum(Decimal(r[f]) for r in detail)==Decimal(inst[f])
 for name in ['stock_daily_price','investor_source_daily','foreign_holding_daily','cfd_daily']:
  for r in data[name]:
   assert r['symbol'] in symbols
   if name in ['foreign_holding_daily','cfd_daily']:assert (r['symbol'],r['trade_date']) in sourcekeys
 (out/'schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2))
 (out/'schema_postgresql.sql').write_text('-- Proposed schema; DB loading not performed.\n'+'\n\n'.join(sql))
 write(out/'data_dictionary.csv',dictionary,['table','name','type','nullable','unit','source'])
 originalissues=read(old/'bronze_unresolved_issues.csv');pendingids={(r['source_file'],r['source_row']) for r in pending}
 activeissues=[r for r in originalissues if (r['source_file'],r['source_data_row_1based']) in pendingids]
 write(out/'bronze_unresolved_issues.csv',activeissues,list(originalissues[0]))
 write(out/'recovery_merge_audit.csv',audit,list(audit[0]));write(out/'pending_recovery_review.csv',pending,list(pending[0]))
 write(out/'data_quality_issues.csv',[],['table','source_file','source_row','column','issue_code','reason'])
 summary={'pipeline_version':VERSION,'status':'PASS','baseline_counts':before,'output_counts':{n:len(r) for n,r in data.items()},'api_source_rows_merged':740,'merge_counts_by_source_type':dict(Counter('investor' if c['source_file'].endswith('investor_trading.csv') else 'index' if c['source_file'].endswith('index.csv') else 'stock_price' for c in accepted)),'remaining_review_rows':1,'active_bronze_issues':len(activeissues),'original_bronze_issues_archived':747,'availability':dict(state),'silver_errors':0,'checks':['原本 유지','가격 범위','수급 산술','자료형/키','API 원문 대조','저장 CSV 재파싱','출처 추적'],'baseline_snapshot':'silver_before_api_merge','api_origin':'additional_data'}
 summary['checks'][0]='기존 브론즈 기반 값 보존'
 (out/'validation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
 (out/'output_sha256.json').write_text(json.dumps({p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='output_sha256.json'},indent=2))
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output.resolve())
