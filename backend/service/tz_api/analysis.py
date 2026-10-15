"""Proposed C artifact adapter: validate delivered outputs without inventing calculations."""
from __future__ import annotations
import csv,json,re
from pathlib import Path
from decimal import Decimal
from datetime import date
from .repository import file_hash,wire

CONTRACT='tz-analysis-artifact/1.0'
TABLES={'g_fin_rpt_analysis':['fin_rpt_id'],'g_stock_daily_analysis':['stock_cd','trd_dt']}

def load_bundle(folder,repo):
 root=Path(folder).resolve();mf=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
 if mf.get('contract_version')!=CONTRACT:raise ValueError('Unsupported C artifact contract')
 if not mf.get('calculation_version') or not mf.get('input_version'):raise ValueError('C artifact versions required')
 if mf['input_version']!=repo.handoff_version:raise ValueError('C input version differs from verified handoff')
 if set(mf.get('tables',{}))!=set(TABLES):raise ValueError('Both proposed C Gold tables are required')
 result=dict(calculation_version=mf['calculation_version'],input_version=mf['input_version'],entries={},root=root)
 for name,pk in TABLES.items():
  item=mf['tables'][name];path=(root/item['file']).resolve()
  if not path.is_relative_to(root):raise ValueError('C artifact path escapes bundle')
  if file_hash(path)!=item['sha256']:raise ValueError('C artifact hash mismatch')
  if item['primary_key']!=pk:raise ValueError('C primary key mismatch')
  columns=item['columns']
  names=[c['name'] for c in columns]
  if len(set(names))!=len(names) or not set(pk)<=set(names):raise ValueError('Invalid C column definitions')
  if any(c['nullable'] for c in columns if c['name'] in pk):raise ValueError('C primary key columns must be nonnullable')
  for c in columns:
   if not re.fullmatch('[a-z][a-z0-9_]{0,39}',c['name']):raise ValueError('Invalid C column name')
   if not isinstance(c['nullable'],bool):raise ValueError('C nullability must be boolean')
   if not re.fullmatch(r'(?:CHAR\([1-9]\d{0,2}\)|VARCHAR\([1-9]\d{0,3}\)|DECIMAL\((?:[1-9]|[12]\d|3[0-8]),(?:\d|[12]\d|3[0-8])\)|DATE|BIGINT|INT|TEXT)',c['sql']):raise ValueError('C SQL type not supported')
  with path.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f)
   if reader.fieldnames!=names:raise ValueError('C CSV columns/order mismatch')
   rows=list(reader)
  if len(rows)!=item['rows']:raise ValueError('C row count mismatch')
  keyed={}
  for row in rows:
   if None in row or any(v is None for v in row.values()):raise ValueError('Malformed C CSV row')
   parsed={}
   for c in columns:
    v=row[c['name']]
    if v=='':
     if not c['nullable']:raise ValueError('Required C value missing')
     parsed[c['name']]=None;continue
    typ=c['sql']
    if typ.startswith('DECIMAL'):
     precision,scale=map(int,re.findall(r'\d+',typ));x=Decimal(v)
     if not x.is_finite() or scale>precision or x!=x.quantize(Decimal(1).scaleb(-scale)) or abs(x)>=Decimal(10)**(precision-scale):raise ValueError('C decimal precision invalid')
     parsed[c['name']]=format(x,f'.{scale}f')
    elif typ=='DATE':parsed[c['name']]=date.fromisoformat(v).isoformat()
    elif typ in ('INT','BIGINT'):
     value=int(v);bits=32 if typ=='INT' else 64
     if not -(2**(bits-1))<=value<2**(bits-1):raise ValueError('C integer overflow')
     parsed[c['name']]=str(value)
    else:
     limit=re.search(r'\((\d+)\)',typ)
     if limit and len(v)>int(limit[1]):raise ValueError('C text too long')
     parsed[c['name']]=v
   key=tuple(parsed[c] for c in pk)
   if None in key or key in keyed:raise ValueError('Null/duplicate C key')
   keyed[key]=parsed
  if name=='g_fin_rpt_analysis':
   expected={(k,) for k in repo.reports}
   result['financial']={k[0]:r for k,r in keyed.items()}
  else:
   expected={(code,r['trd_dt']) for code,rows in repo.daily.items() for r in rows}
   for key,row in keyed.items():
    base=next((r for r in repo.daily.get(key[0],[]) if r['trd_dt']==key[1]),None)
    if base and 'fin_rpt_id' in row and row['fin_rpt_id']!=base['fin_rpt_id']:raise ValueError('C PIT selection differs from baseline')
   result['daily']=keyed
  if set(keyed)!=expected:raise ValueError('C key coverage differs from verified baseline')
  result['entries'][name]=dict(item,path=path)
 return result
