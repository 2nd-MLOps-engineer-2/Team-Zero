"""One verified Silver price table: CSV -> Delta -> MySQL -> full value reconciliation.

This is a backend connection exercise, not a completed Bronze/Silver/Gold pipeline.
No DROP, TRUNCATE, REPLACE, or writes to the input data are performed.
"""
from __future__ import annotations
from pathlib import Path
from datetime import date,datetime,timedelta,timezone
from decimal import Decimal
import argparse,csv,getpass,hashlib,json,re,sys
import pyarrow as pa
from deltalake import DeltaTable,write_deltalake

HERE=Path(__file__).resolve().parent
KST=timezone(timedelta(hours=9))
TABLE='s_stock_daily_prc'
EXPECTED_SHA='1979277510c6b839f0831b5b79e5c249b841e31aa1994ced1f56c84ce60bd97c'
SPEC=[
 ('stock_cd',pa.string(),'CHAR(6)',False),
 ('trd_dt',pa.date32(),'DATE',False),
 ('candle_dttm',pa.timestamp('us'),'DATETIME',False),
 ('open_prc',pa.decimal128(18,4),'DECIMAL(18,4)',False),
 ('high_prc',pa.decimal128(18,4),'DECIMAL(18,4)',False),
 ('low_prc',pa.decimal128(18,4),'DECIMAL(18,4)',False),
 ('close_prc',pa.decimal128(18,4),'DECIMAL(18,4)',False),
 ('trd_qty',pa.int64(),'BIGINT',False),
 ('crncy_cd',pa.string(),'VARCHAR(50)',False),
 ('src_team_cd',pa.string(),'VARCHAR(50)',False),
 ('src_kind_cd',pa.string(),'VARCHAR(50)',False),
 ('src_file_path',pa.string(),'VARCHAR(500)',False),
 ('src_row_no',pa.int32(),'INT',False),
 ('bronze_row_no',pa.int32(),'INT',True),
 ('src_ver',pa.string(),'VARCHAR(80)',False),
 ('fetch_dttm',pa.timestamp('us'),'DATETIME',True),
 ('api_raw_file_path',pa.string(),'VARCHAR(500)',True),
 ('api_rcrd_path',pa.string(),'VARCHAR(500)',True),
 ('pipln_ver',pa.string(),'VARCHAR(80)',False),
]
SCHEMA=pa.schema([pa.field(n,t,nullable=nullable) for n,t,_,nullable in SPEC])
COLS=SCHEMA.names
class DemoError(Exception):pass

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def canonical(row):
    values=[]
    for n,t,_,_ in SPEC:
        v=row[n]
        if v is None:values.append(None)
        elif pa.types.is_decimal(t):values.append(format(Decimal(v),'.4f'))
        elif isinstance(v,(datetime,date)):values.append(v.isoformat())
        else:values.append(v)
    return values
def sorted_rows(rows):return sorted(rows,key=lambda r:(r['stock_cd'],r['trd_dt']))
def digest(rows):
    h=hashlib.sha256()
    for row in sorted_rows(rows):h.update((json.dumps(canonical(row),ensure_ascii=False,separators=(',',':'))+'\n').encode())
    return h.hexdigest()
def parse_value(v,t,nullable,name):
    if v=='':
        if nullable:return None
        raise DemoError('Required input empty: '+name)
    if pa.types.is_date32(t):return date.fromisoformat(v)
    if pa.types.is_timestamp(t):
        result=datetime.fromisoformat(v)
        if result.tzinfo is not None:raise DemoError('C table requires KST local timestamp without offset: '+name)
        return result
    if pa.types.is_integer(t):return int(v)
    if pa.types.is_decimal(t):
        result=Decimal(v)
        if not result.is_finite() or result!=result.quantize(Decimal('.0001')):raise DemoError('Unsupported precision: '+name)
        return result
    return v

def validate(rows):
    keys=set()
    for r in rows:
        if not re.fullmatch(r'\d{6}',r['stock_cd']):raise DemoError('stock_cd must be six digits')
        k=(r['stock_cd'],r['trd_dt'])
        if k in keys:raise DemoError('Duplicate price key: '+str(k))
        keys.add(k)
        if r['trd_qty']<0:raise DemoError('Negative volume')
        if not (r['low_prc']<=r['open_prc']<=r['high_prc'] and r['low_prc']<=r['close_prc']<=r['high_prc']):raise DemoError('Invalid OHLC')
        if r['candle_dttm'].date()!=r['trd_dt']:raise DemoError('KST candle date mismatch')
        if r['crncy_cd']!='KRW':raise DemoError('This demo requires KRW')
    if not rows:raise DemoError('Input is empty')
    return dict(rows=len(rows),companies=len({r['stock_cd'] for r in rows}),
                min_date=min(r['trd_dt'] for r in rows).isoformat(),max_date=max(r['trd_dt'] for r in rows).isoformat(),
                duplicate_keys=0,ohlc_check='PASS',business_and_provenance_digest=digest(rows))

def ddl(db):
    definitions=[f'  `{n}` {sql}'+(' NULL' if nullable else ' NOT NULL') for n,_,sql,nullable in SPEC]
    definitions += ['  PRIMARY KEY (`stock_cd`,`trd_dt`)',
                    '  CHECK (`trd_qty` >= 0)',
                    '  CHECK (`high_prc` >= `open_prc` AND `high_prc` >= `close_prc` AND `low_prc` <= `open_prc` AND `low_prc` <= `close_prc` AND `high_prc` >= `low_prc`)']
    return f'CREATE TABLE `{db}`.`{TABLE}` (\n'+',\n'.join(definitions)+'\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin'

def build_delta(source,output,allow_different_source=False):
    source=source.resolve();output=output.resolve()
    before=sha(source)
    if not allow_different_source and before!=EXPECTED_SHA:raise DemoError('Input differs from the verified C package. Check the original before using --allow-different-source.')
    if output.exists():raise DemoError('Output exists. Choose a new run directory; no overwrite is performed.')
    with source.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f,strict=True)
        if reader.fieldnames!=COLS:raise DemoError('Column names/order differ from verified C price table')
        raw=list(reader)
    rows=[{n:parse_value(r[n],t,nullable,n) for n,t,_,nullable in SPEC} for r in raw]
    validation=validate(rows)
    if before==EXPECTED_SHA and (len(rows)!=17440 or validation['companies']!=20):raise DemoError('Verified input count mismatch')
    table=pa.Table.from_pylist(rows,schema=SCHEMA)
    output.mkdir(parents=True)
    path=output/'delta/silver'/TABLE
    write_deltalake(str(path),table,mode='error')
    dt=DeltaTable(str(path));version=dt.version()
    back=dt.to_pyarrow_table().to_pylist()
    result=validate(back)
    if result!=validation:raise DemoError('Delta roundtrip mismatch')
    if not any((path/'_delta_log').glob('*.json')) or not any(path.glob('*.parquet')):raise DemoError('Delta table/log missing')
    if before!=sha(source):raise DemoError('Input changed while reading')
    roundtrip=DeltaTable(str(path),version=version).to_pyarrow_table().to_pylist()
    if digest(roundtrip)!=validation['business_and_provenance_digest']:raise DemoError('Pinned Delta version mismatch')
    if re.fullmatch(r'run_\d{8}_\d{6}_[0-9a-f]{6}',output.name):database='tz_demo_'+output.name.removeprefix('run_')
    else:
        import uuid
        database=datetime.now(KST).strftime('tz_demo_%Y%m%d_%H%M%S_')+uuid.uuid4().hex[:6]
    report=dict(status='DELTA_PASS_MYSQL_PENDING',scope='Silver price connection exercise only; full Medallion not completed',
                input_file=source.name,input_path=str(source),input_sha256=before,input_unchanged=True,
                delta_relative_path=path.relative_to(output).as_posix(),delta_version=version,delta_history=dt.history(),
                mysql_database=database,delta_validation=result,versions=package_versions())
    save(output/'delta_validation.json',report)
    (output/'01_create_mysql.sql').write_text('-- Reference DDL; the loader refuses an existing database.\n'+f'CREATE DATABASE `{database}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;\n'+ddl(database)+';\n',encoding='utf-8')
    (output/'02_check_mysql.sql').write_text(f'''SELECT COUNT(*) AS row_count, COUNT(DISTINCT stock_cd) AS companies,
       MIN(trd_dt) AS first_date, MAX(trd_dt) AS last_date FROM `{database}`.`{TABLE}`;
SELECT stock_cd,trd_dt,COUNT(*) AS n FROM `{database}`.`{TABLE}`
GROUP BY stock_cd,trd_dt HAVING COUNT(*)>1;
SELECT stock_cd,trd_dt,close_prc,trd_qty FROM `{database}`.`{TABLE}`
WHERE stock_cd='005930' ORDER BY trd_dt LIMIT 10;
''',encoding='utf-8')
    return output,report

def package_versions():
    from importlib.metadata import version
    return {n:version(n) for n in ['deltalake','pyarrow','PyMySQL']}

def load_mysql(run,host,port,user):
    import pymysql
    run=run.resolve();report=json.loads((run/'delta_validation.json').read_text(encoding='utf-8'))
    if (run/'mysql_validation.json').exists():raise DemoError('This run already has a MySQL result. No repeated insertion is allowed.')
    db=report['mysql_database']
    if not re.fullmatch(r'tz_demo_\d{8}_\d{6}_[0-9a-f]{6}',db):raise DemoError('Invalid demo database name')
    path=run/report['delta_relative_path'];dt=DeltaTable(str(path),version=report['delta_version'])
    rows=sorted_rows(dt.to_pyarrow_table().to_pylist());verification=validate(rows)
    if verification!=report['delta_validation']:raise DemoError('Pinned Delta content differs from validation report')
    print(f'MySQL {user}@{host}:{port} | NEW database: {db}',flush=True)
    print('Password is entered locally and is never saved. Enter an empty value only if your account has no password.',flush=True)
    password=getpass.getpass('MySQL password: ')
    try:
        con=pymysql.connect(host=host,port=port,user=user,password=password,charset='utf8mb4',autocommit=False,connect_timeout=10,
                            read_timeout=60,write_timeout=60,cursorclass=pymysql.cursors.DictCursor)
    finally:password=None
    created=False
    try:
        with con.cursor() as cur:
            cur.execute('SELECT VERSION() AS version');server=cur.fetchone()['version']
            cur.execute('SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME=%s',(db,))
            if cur.fetchone():raise DemoError('Demo database exists. Refusing to change it. Build a new run.')
            cur.execute(f'CREATE DATABASE `{db}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin');created=True
            cur.execute(ddl(db))
            sql=f'INSERT INTO `{db}`.`{TABLE}` ('+','.join('`'+n+'`' for n in COLS)+') VALUES ('+','.join(['%s']*len(COLS))+')'
            for offset in range(0,len(rows),1000):cur.executemany(sql,[tuple(r[n] for n in COLS) for r in rows[offset:offset+1000]])
            cur.execute(f'SELECT '+','.join('`'+n+'`' for n in COLS)+f' FROM `{db}`.`{TABLE}` ORDER BY stock_cd,trd_dt')
            loaded=cur.fetchall();actual=validate(loaded)
            if actual!=verification:raise DemoError('MySQL full value reconciliation failed')
            cur.execute(f'SELECT COUNT(*) AS n,COUNT(DISTINCT stock_cd) AS companies,MIN(trd_dt) AS first_date,MAX(trd_dt) AS last_date FROM `{db}`.`{TABLE}`')
            stats={k:(v.isoformat() if isinstance(v,date) else v) for k,v in cur.fetchone().items()}
        con.commit()
        result=dict(status='PASS',database=db,host=host,port=port,user=user,server_version=server,
                    table=TABLE,delta_version=report['delta_version'],source_sha256=report['input_sha256'],sql_counts=stats,
                    all_rows_all_columns_match=True,checked_values=len(rows)*len(COLS),canonical_digest=actual['business_and_provenance_digest'],
                    existing_databases_unchanged=True,password_saved=False)
        save(run/'mysql_validation.json',result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception:
        con.rollback()
        if created:print('The new demo schema/table may remain, because DDL is not rolled back. Existing databases were not changed.',file=sys.stderr)
        raise
    finally:con.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--load-existing',type=Path);p.add_argument('--delta-only',action='store_true')
    p.add_argument('--allow-different-source',action='store_true')
    p.add_argument('--mysql-host',default='127.0.0.1');p.add_argument('--mysql-port',type=int,default=3306);p.add_argument('--mysql-user',default='root')
    a=p.parse_args()
    if a.load_existing:
        if a.source or a.output or a.delta_only:p.error('--load-existing cannot be combined with --source/--output/--delta-only')
        run=a.load_existing
    else:
        if not a.source:p.error('--source is required when building a Delta run')
        import uuid
        run_id=datetime.now(KST).strftime('run_%Y%m%d_%H%M%S_')+uuid.uuid4().hex[:6]
        run,report=build_delta(a.source,a.output or HERE/'runs'/run_id,a.allow_different_source)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    if not a.delta_only:load_mysql(run,a.mysql_host,a.mysql_port,a.mysql_user)

if __name__=='__main__':
    try:main()
    except (DemoError,ValueError,FileNotFoundError) as e:print('ERROR: '+str(e),file=sys.stderr);sys.exit(2)
