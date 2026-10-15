"""Immutable Delta snapshots and explicit MySQL-compatible, lossless types."""
from __future__ import annotations
import csv,hashlib,json,re
from datetime import date,datetime
from decimal import Decimal
from pathlib import Path
from functools import lru_cache
import pyarrow as pa
from deltalake import DeltaTable,write_deltalake

HERE=Path(__file__).resolve().parent

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def save(p,obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,default=str)

def read(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

@lru_cache(maxsize=64)
def arrow_type(sql):
 sql=sql.upper()
 if sql=='DATE':return pa.date32()
 if sql.startswith('DATETIME'):return pa.timestamp('us')
 if sql=='BIGINT':return pa.int64()
 if sql in ('INT','INTEGER'):return pa.int32()
 m=re.fullmatch(r'DECIMAL\((\d+),(\d+)\)',sql)
 if m:return pa.decimal128(int(m[1]),int(m[2]))
 if sql.startswith(('CHAR(','VARCHAR(')) or sql in ('TEXT','MEDIUMTEXT','LONGTEXT'):return pa.string()
 raise ValueError('Unsupported explicit SQL type '+sql)

def parse(v,sql,nullable):
 if v=='':
  if nullable:return None
  raise ValueError('Required value empty')
 t=arrow_type(sql)
 if pa.types.is_date32(t):return date.fromisoformat(v)
 if pa.types.is_timestamp(t):
  x=datetime.fromisoformat(v)
  if x.tzinfo is not None:raise ValueError('Expected local KST datetime')
  return x
 if pa.types.is_integer(t):return int(v)
 if pa.types.is_decimal(t):
  x=Decimal(v)
  if not x.is_finite() or x!=x.quantize(Decimal(1).scaleb(-t.scale)):raise ValueError('Decimal precision loss '+v)
  return x
 return v

def from_csv(path,spec):
 rows=read(path);cols=spec['columns']
 if rows and list(rows[0])!=[c['name'] for c in cols]:raise ValueError('Schema order mismatch '+str(path))
 arrays=[pa.array([parse(r[c['name']],c['sql'],c['nullable']) for r in rows],type=arrow_type(c['sql'])) for c in cols]
 schema=pa.schema([pa.field(c['name'],arrow_type(c['sql']),nullable=c['nullable']) for c in cols])
 return pa.Table.from_arrays(arrays,schema=schema)

def canon(v,c):
 if v is None:return None
 t=arrow_type(c['sql'])
 if pa.types.is_decimal(t):return format(Decimal(v),f'.{t.scale}f')
 if isinstance(v,(date,datetime)):return v.isoformat()
 return v

def digest(rows,spec):
 """Row order independent, multiplicity preserving; full row SHA then sort."""
 hs=[]
 for r in rows:
  vals=[canon(r[c['name']],c) for c in spec['columns']]
  hs.append(hashlib.sha256(json.dumps(vals,ensure_ascii=False,separators=(',',':')).encode()).digest())
 return hashlib.sha256(b''.join(sorted(hs))).hexdigest()

def iterrows(table):
 for batch in table.to_batches(max_chunksize=4096):yield from batch.to_pylist()

def delta_snapshot(run,table,spec,allow_existing=False):
 path=Path(run)/'delta'/spec['layer']/spec.get('delta_folder',spec['name'])
 before=digest(iterrows(table),spec)
 if path.exists() and not allow_existing:raise FileExistsError(path)
 if not path.exists():write_deltalake(str(path),table,mode='error')
 dt=DeltaTable(str(path),version=0);back=dt.to_pyarrow_table()
 if back.num_rows!=table.num_rows or digest(iterrows(back),spec)!=before:raise ValueError('Delta reconciliation '+spec['name'])
 return dict(**spec,delta_path=path.relative_to(run).as_posix(),delta_version=0,rows=table.num_rows,
             canonical_digest=before,
             delta_files={p.relative_to(path).as_posix():sha(p) for p in sorted(path.rglob('*')) if p.is_file()})

def load_delta(run,entry):
 path=Path(run)/entry['delta_path']
 for rel,h in entry['delta_files'].items():
  if sha(path/rel)!=h:raise ValueError('Changed Delta file '+rel)
 t=DeltaTable(str(path),version=entry['delta_version']).to_pyarrow_table()
 if t.num_rows!=entry['rows'] or digest(iterrows(t),entry)!=entry['canonical_digest']:raise ValueError('Changed Delta values '+entry['name'])
 return t

def raw_spec(name,headers):
 return dict(name=name,layer='bronze',kind='raw',pk=['ldng_file_path','ldng_row_no'],fks=[],
  columns=[dict(name=h,sql='LONGTEXT',nullable=False) for h in headers]+[
   dict(name='ldng_file_path',sql='VARCHAR(500)',nullable=False),dict(name='ldng_row_no',sql='INT',nullable=False),
   dict(name='ldng_file_hash',sql='CHAR(64)',nullable=False),dict(name='ldng_encoding',sql='VARCHAR(30)',nullable=False)])

def raw_arrow(frames,spec):
 schema=pa.schema([pa.field(c['name'],arrow_type(c['sql']),nullable=False) for c in spec['columns']])
 import pandas as pd
 df=pd.concat(frames,ignore_index=True)
 return pa.Table.from_pandas(df,schema=schema,preserve_index=False)
