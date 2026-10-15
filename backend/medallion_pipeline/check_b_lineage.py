"""Verify all pre-API B business values against replayed cleaned source rows."""
import json,csv
from pathlib import Path
from functools import lru_cache
from engine import read,save

def verify(b,clean):
 paths={p.name:p for p in (clean/'01_bronze/Toss').rglob('*.csv')}
 source={name:read(p) for name,p in paths.items()}
 @lru_cache(maxsize=20000)
 def obj(file,row,col):
  s=source[file][row-1][col]
  return json.loads(s) if s else None
 counts={};values=0
 def eq(a,b,where):
  nonlocal values
  values+=1
  if a!=b:raise ValueError('B clean-source mismatch '+where+': '+str(a)+' != '+str(b))
 for name in ['security_master','stock_daily_price','market_index_daily','investor_source_daily','investor_trading_daily','foreign_holding_daily','cfd_daily']:
  n=0
  for r in read(b/'silver'/(name+'.csv')):
   if r['source_kind']!='bronze':continue
   n+=1;file=r['source_file'];row=int(r['bronze_row']);raw=source[file][row-1]
   if name=='security_master':
    for col in raw:
     if col not in r:continue
     if col=='koreanMarketDetail':eq(json.loads(r[col]) if r[col] else None,obj(file,row,col),name+'.'+col)
     elif col=='isCommonShare':eq(r[col].lower(),raw[col].lower(),name+'.'+col)
     else:eq(r[col],raw[col],name+'.'+col)
   elif name in ('stock_daily_price','market_index_daily'):
    mapping={'symbol' if name=='stock_daily_price' else 'index_code':'symbol','timestamp':'timestamp','open_price':'openPrice','high_price':'highPrice','low_price':'lowPrice','close_price':'closePrice','volume':'volume'}
    for dst,src in mapping.items():eq(r[dst],raw[src],name+'.'+dst)
   elif name=='investor_source_daily':
    eq(r['symbol'],raw['symbol'],name+'.symbol');eq(r['trade_date'],raw['date'],name+'.date');eq(r['updated_at'],raw['updatedAt'],name+'.updated_at')
    for col in ['individual','foreigner','institution','otherCorporation','foreignerHolding','cfd']:eq(json.loads(r[col]) if r[col] else None,obj(file,row,col),name+'.'+col)
   else:
    node=obj(file,row,r['source_column'])
    for part in r['json_path'].split('.')[1:]:node=node[part]
    pairs={'investor_trading_daily':{'buy_volume':'buyVolume','sell_volume':'sellVolume','net_buy_volume':'netBuyVolume'},
     'foreign_holding_daily':{'holding_quantity':'holdingQuantity','limit_quantity':'limitQuantity','holding_rate':'holdingRate'},
     'cfd_daily':{'buy_balance_quantity':'buyBalanceQuantity','buy_balance_rate':'buyBalanceRate','sell_balance_quantity':'sellBalanceQuantity','sell_balance_rate':'sellBalanceRate'}}[name]
    for dst,src in pairs.items():eq(r[dst],node[src],name+'.'+dst)
  counts[name]=n
 return dict(status='PASS',pre_api_rows_by_table=counts,business_values_compared=values,mismatches=0,
             definition='Compares cleaned-source business values, not serialized JSON whitespace; API additions verified in B replay.')

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True);ap.add_argument('--b',type=Path,required=True);a=ap.parse_args()
 result=verify(a.b,a.run/'evidence/cleanup_replay');save(a.run/'validation/B_clean_source_lineage.json',result);print(json.dumps(result,indent=2))
