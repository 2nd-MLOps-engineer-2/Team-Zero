#!/usr/bin/env python3
"""Restore the supplied educational OpenDART/Toss dataset without guessing lost values.

Usage:
    python clean_bronze.py --input drive-download-20261014T012748Z-1-001.zip --output restored

Python 3.10+; standard library only. Input files are never modified.
OpenDART uses the supplied before/after manifest (not a blind cleansing heuristic).
Toss uses reversible text fixes, filename/ISIN/master evidence, verified date
alignment, and net-buy identities. Unrecoverable records are quarantined.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
import re
import shutil
import sys
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

KST = timezone(timedelta(hours=9))
NULLS = {'', 'NULL', 'N/A', 'NONE', 'NAN', '-'}
JSON_COLUMNS = {'individual', 'foreigner', 'institution', 'otherCorporation', 'foreignerHolding', 'cfd', 'koreanMarketDetail'}
PRICE_COLUMNS = ['openPrice', 'highPrice', 'lowPrice', 'closePrice', 'volume']
AUDIT_COLUMNS = ['dataset', 'source_file', 'source_data_row_1based', 'column', 'before', 'after', 'rules', 'evidence', 'resolution']


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read_csv(path: Path, encoding: str = 'utf-8-sig') -> tuple[list[str], list[dict[str, str]]]:
    with path.open('r', encoding=encoding, errors='strict', newline='') as f:
        rd = csv.reader(f, strict=True)
        header = next(rd)
        if len(set(header)) != len(header):
            raise ValueError(f'Duplicate header: {path}')
        rows = []
        for i, row in enumerate(rd, 1):
            if len(row) != len(header):
                raise ValueError(f'CSV width mismatch: {path}, data row {i}')
            rows.append(dict(zip(header, row)))
    return header, rows


def write_csv(path: Path, header: list[str], rows: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=header, extrasaction='raise', lineterminator='\n')
        wr.writeheader()
        wr.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')


def safe_extract(z: zipfile.ZipFile, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    for info in z.infolist():
        if not (root / info.filename).resolve().is_relative_to(root):
            raise ValueError(f'Unsafe archive member: {info.filename}')
        if (info.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError(f'Symlink archive member: {info.filename}')
    bad = z.testzip()
    if bad:
        raise ValueError(f'ZIP CRC failed: {bad}')
    z.extractall(target)


def prepare_sources(outer_path: Path, work: Path, out: Path) -> dict[str, Any]:
    outer = work / 'source'
    with zipfile.ZipFile(outer_path) as z:
        safe_extract(z, outer)
    nested = list(outer.rglob('*.zip'))
    dart_zip = next(p for p in nested if p.name.startswith('OpenDART'))
    toss_zip = next(p for p in nested if not p.name.startswith('OpenDART'))
    summary_path = next(outer.rglob('*.json'))
    manifest_path = next(outer.rglob('*.csv'))
    source_summary = json.loads(summary_path.read_text(encoding='utf-8-sig'))
    if sha256(dart_zip) != source_summary['output_sha256']:
        raise ValueError('OpenDART archive SHA-256 differs from the supplied manifest.')
    roots = {}
    for name, p in [('OpenDART', dart_zip), ('Toss', toss_zip)]:
        root = work / name
        with zipfile.ZipFile(p) as z:
            safe_extract(z, root)
        roots[name] = root
    source_out = out / '06_sources'
    source_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(summary_path, source_out / 'OpenDART_corruption_summary.json')
    shutil.copy2(manifest_path, source_out / 'OpenDART_corruption_manifest.csv')
    for p in outer.rglob('*.pdf'):
        shutil.copy2(p, source_out / ('OpenDART_specification.pdf' if p.name.startswith('OpenDART') else 'Toss_specification.pdf'))
    hashes = {'outer_archive': {'filename': outer_path.name, 'sha256': sha256(outer_path)},
              'OpenDART_corrupted_archive': {'filename': dart_zip.name, 'sha256': sha256(dart_zip)},
              'Toss_corrupted_archive': {'filename': toss_zip.name, 'sha256': sha256(toss_zip)},
              'OpenDART_original_archive_hash_declared_not_verified': source_summary['source_sha256']}
    write_json(out / '04_audit' / 'input_hashes.json', hashes)
    return {'roots': roots, 'summary': source_summary, 'manifest': manifest_path, 'hashes': hashes}


def restore_dart(root: Path, out: Path, source: dict[str, Any]) -> dict[str, Any]:
    print('Restoring OpenDART from exact before/after values...', flush=True)
    _, manifest = read_csv(source['manifest'])
    grouped = collections.defaultdict(list)
    for m in manifest:
        grouped[m['file']].append(m)
    if len(manifest) != sum(source['summary']['rules_overall'].values()):
        raise ValueError('Manifest total does not match rule counts.')
    records = []; per_file = []; document_checks = []; baseline_findings = []
    all_codes = set(); stock_refs = collections.defaultdict(list)
    rules = collections.Counter(); logged_rows = set(); logged_cells = set()
    dest = out / '01_bronze' / 'OpenDART'
    dest.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in root.rglob('*') if p.is_file())
    csv_files = [p for p in files if p.suffix.lower() == '.csv']
    for p in files:
        if p.suffix.lower() != '.csv':
            t = dest / p.relative_to(root)
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, t)
            if sha256(p) != sha256(t):
                raise ValueError(f'Non-CSV byte preservation failed: {p}')
    for p in csv_files:
        rel = p.relative_to(root).as_posix()
        enc = source['summary']['encodings'][rel]
        header, rows = read_csv(p, enc)
        if len(rows) != source['summary']['rows_by_file'][rel]:
            raise ValueError(f'Source row-count mismatch: {rel}')
        file_logs = grouped.get(rel, [])
        for m in reversed(file_logs):
            i = int(m['data_row_1based']) - 1
            c = m['column']
            key = (rel, i + 1, c)
            if key in logged_cells:
                raise ValueError(f'Unexpected repeated manifest cell: {key}')
            logged_cells.add(key); logged_rows.add((rel, i + 1))
            if rows[i][c] != m['after']:
                raise ValueError(f'Manifest precondition failed: {rel}, row {i+1}, {c}')
            rows[i][c] = m['before']
            rules[m['rule']] += 1
            records.append(dict(zip(AUDIT_COLUMNS, ['OpenDART', rel, i+1, c, m['after'], m['before'], m['rule'], 'Supplied corruption manifest: exact after match and exact before restore', 'EXACT_MANIFEST_RESTORE'])))
        output = dest / rel
        write_csv(output, header, rows)
        h2, r2 = read_csv(output)
        if h2 != header or r2 != rows:
            raise ValueError(f'Output reparse differs: {rel}')
        for m in file_logs:
            if r2[int(m['data_row_1based'])-1][m['column']] != m['before']:
                raise ValueError(f'Postcondition failed: {rel}')
        q = collections.Counter()
        for i, r in enumerate(rows, 1):
            if 'corp_code' in r and not re.fullmatch(r'\d{8}', r['corp_code']):
                q['corp_code_format'] += 1
            if 'rcept_no' in r and not re.fullmatch(r'\d{14}', r['rcept_no']):
                q['receipt_format'] += 1
            if 'rcept_dt' in r:
                try:
                    dt = datetime.strptime(r['rcept_dt'], '%Y%m%d')
                    if p.name.startswith('disclosures_') and dt.strftime('%Y%m') != p.stem[-6:]:
                        q['date_partition_mismatch'] += 1
                except ValueError:
                    q['date_parse'] += 1
            if 'bsns_year' in r and r['bsns_year'] != p.stem[-4:]:
                q['business_year_mismatch'] += 1
            if p.name == 'corp_codes.csv':
                all_codes.add(r['corp_code'])
                if r['stock_code'].strip():
                    stock_refs[r['stock_code'].strip()].append({'corp_code': r['corp_code'], 'corp_name': r['corp_name']})
            if p.name == 'disclosure_documents.csv':
                if r['status'] == 'downloaded':
                    doc = dest / 'dataset' / r['zip_path']
                    ok_path = doc.is_file()
                    actual = sha256(doc) if ok_path else ''
                    ok_hash = actual == r['sha256']
                    ok_receipt = Path(r['zip_path']).stem == r['rcept_no']
                    if not all([ok_path, ok_hash, ok_receipt]):
                        raise ValueError(f'Document integrity failed: row {i}')
                    with zipfile.ZipFile(doc) as z:
                        crc_ok = z.testzip() is None
                    if not crc_ok:
                        raise ValueError(f'Embedded document ZIP CRC failed: {doc}')
                    document_checks.append({'source_data_row_1based': i, 'rcept_no': r['rcept_no'], 'zip_path': r['zip_path'], 'expected_sha256': r['sha256'], 'actual_sha256': actual, 'sha256_match': True, 'receipt_path_match': True, 'zip_crc_ok': True, 'status': r['status']})
                else:
                    baseline_findings.append({'source_file': rel, 'source_data_row_1based': i, 'finding': 'ORIGINAL_DOCUMENT_NON_DOWNLOADED', 'detail': json.dumps(r, ensure_ascii=False), 'handling': 'Original collection status preserved; not introduced by this cleaning.'})
        per_file.append({'dataset': 'OpenDART', 'source_file': rel, 'input_encoding': enc, 'output_encoding': 'utf-8-sig', 'input_rows': len(rows), 'preserved_rows': len(rows), 'bronze_rows': len(rows), 'quarantine_rows': 0, 'changed_rows': len({m['data_row_1based'] for m in file_logs}), 'changed_cells': len(file_logs), 'unresolved_issues': 0, 'schema_preserved': True, 'reparse_ok': True, 'input_sha256': sha256(p), 'bronze_sha256': sha256(output), 'baseline_format_findings': json.dumps(q, ensure_ascii=False)})
    if dict(rules) != source['summary']['rules_overall']:
        raise ValueError('Restored per-rule counts do not match source.')
    if len(logged_rows) != source['summary']['total_modified_rows']:
        raise ValueError('Restored distinct row count does not match source.')
    write_csv(out / '04_audit' / 'OpenDART_repair_log.csv', AUDIT_COLUMNS, records)
    write_csv(out / '04_audit' / 'OpenDART_document_checks.csv', ['source_data_row_1based','rcept_no','zip_path','expected_sha256','actual_sha256','sha256_match','receipt_path_match','zip_crc_ok','status'], document_checks)
    write_csv(out / '04_audit' / 'OpenDART_original_collection_status.csv', ['source_file','source_data_row_1based','finding','detail','handling'], baseline_findings)
    return {'csv_files':len(csv_files), 'input_rows':sum(x['input_rows'] for x in per_file), 'bronze_rows':sum(x['bronze_rows'] for x in per_file), 'exactly_restored_cells':len(records), 'exactly_restored_rows':len(logged_rows), 'restored_by_rule':dict(rules), 'preserved_document_zip_count':len([p for p in files if p.suffix.lower()=='.zip']), 'verified_document_index_rows':len(document_checks), 'original_collection_status_findings':len(baseline_findings), 'original_archive_full_byte_equivalence_verified':False, 'all_manifest_preconditions_and_postconditions_passed':True, 'per_file':per_file, 'stock_refs':dict(stock_refs)}


def fix_mojibake(value: str) -> str:
    def fix(m: re.Match) -> str:
        s = m.group()
        try:
            return s.encode('latin-1').decode('utf-8')
        except UnicodeError:
            return s
    return re.sub(r'[\x00-\xff]+', fix, value)


def parse_date(s: str) -> str:
    if re.fullmatch(r'\d{8}', s):
        return datetime.strptime(s, '%Y%m%d').date().isoformat()
    m = re.fullmatch(r'(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D*', s)
    if not m:
        raise ValueError(f'Unrecognized date: {s!r}')
    return datetime(int(m[1]), int(m[2]), int(m[3])).date().isoformat()


def parse_time(s: str) -> str:
    if re.fullmatch(r'\d{14}', s):
        dt = datetime.strptime(s, '%Y%m%d%H%M%S')
    elif re.fullmatch(r'\d{8}', s):
        dt = datetime.strptime(s, '%Y%m%d')
    elif re.fullmatch(r'\d{4}/\d{2}/\d{2}', s):
        dt = datetime.strptime(s, '%Y/%m/%d')
    else:
        dt = datetime.fromisoformat(s.replace('/', '-').replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)
    return dt.astimezone(KST).isoformat(timespec='milliseconds')


def decimal_value(s: Any) -> Decimal | None:
    try:
        d = Decimal(str(s))
        return d if d.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def isin_ok(s: str) -> bool:
    if not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}\d', s):
        return False
    digits = ''.join(str(ord(c)-ord('A')+10) if c.isalpha() else c for c in s)
    result = 0
    for i, c in enumerate(reversed(digits)):
        n = int(c) * (2 if i % 2 else 1)
        result += n // 10 + n % 10
    return result % 10 == 0


def clean_toss(root: Path, out: Path, dart: dict[str, Any]) -> dict[str, Any]:
    print('Cleaning Toss; verifying independent evidence and isolating lost values...', flush=True)
    original = {}; data = {}; headers = {}; paths = {}
    for p in sorted(root.rglob('*.csv')):
        h, r = read_csv(p)
        original[p.name] = r
        data[p.name] = [dict(x) for x in r]
        headers[p.name] = h; paths[p.name] = p
    if len(data) != 43 or sum(map(len, data.values())) != 36644:
        raise ValueError('Unexpected Toss file count or row count.')
    reasons = collections.defaultdict(list); evidence = collections.defaultdict(list)
    issues = []; rule_events = collections.Counter(); semantic_fixes = collections.Counter()
    def assign(fn: str, i: int, c: str, value: str, rule: str, why: str) -> None:
        if data[fn][i][c] != value:
            data[fn][i][c] = value
            if rule not in reasons[fn,i,c]:
                reasons[fn,i,c].append(rule)
            if why not in evidence[fn,i,c]:
                evidence[fn,i,c].append(why)
            rule_events[rule] += 1
    def issue(fn: str, i: int, c: str, code: str, why: str) -> None:
        issues.append({'dataset':'Toss','source_file':fn,'source_data_row_1based':i+1,'symbol':data[fn][i].get('symbol',''),'date':data[fn][i].get('date', data[fn][i].get('timestamp','')),'column_or_group':c,'issue_code':code,'original_value':original[fn][i].get(c,''),'current_value':data[fn][i].get(c,''),'reason':why,'required_evidence':'Uncorrupted source snapshot or exact before/after history','resolution':'QUARANTINED_NOT_IMPUTED'})
    # Reverse byte-decoding damage before trimming: some mojibake bytes are spaces.
    for fn, rows in data.items():
        for i, row in enumerate(rows):
            for c in headers[fn]:
                s = row[c]
                fixed = fix_mojibake(s)
                assign(fn,i,c,fixed,'MOJIBAKE_REVERSE','Latin-1 code points re-encoded then decoded as UTF-8; reversible mapping')
                nfc = unicodedata.normalize('NFC', row[c])
                assign(fn,i,c,nfc,'UNICODE_NFC','Unicode canonical composition')
                assign(fn,i,c,row[c].strip(),'TRIM_OUTER_WHITESPACE','Only leading/trailing whitespace removed; internal text preserved')
                if row[c].upper() in NULLS and row[c] != '':
                    assign(fn,i,c,'','NULL_REPRESENTATION','Missing-value marker standardized; not a restoration of lost information')
                if c in {'isinCode','market','securityType','status','currency'}:
                    assign(fn,i,c,row[c].upper(),'ENUM_UPPERCASE','Declared identifier/category field; original uppercase vocabulary')
                if c in {'date','listDate','delistDate'} and row[c]:
                    try:
                        assign(fn,i,c,parse_date(row[c]),'DATE_CANONICAL','Valid calendar date rendered as YYYY-MM-DD')
                    except ValueError:
                        issue(fn,i,c,'UNPARSEABLE_DATE','Date cannot be parsed without guessing.')
                if c in {'timestamp','updatedAt'} and row[c]:
                    try:
                        assign(fn,i,c,parse_time(row[c]),'TIME_CANONICAL_KST','UTC instants converted to +09:00; naive forms use the +09:00 convention in unchanged rows')
                    except ValueError:
                        issue(fn,i,c,'UNPARSEABLE_TIMESTAMP','Timestamp cannot be parsed without guessing.')
    symbols = {fn.split('_')[0] for fn in data if fn.endswith('_candles.csv')}
    stock_evidence = []
    for i, row in enumerate(data['stocks.csv']):
        isin = row['isinCode']; sym = isin[3:9]
        if not isin_ok(isin) or sym not in symbols:
            raise ValueError(f'Master symbol cannot be verified: row {i+1}')
        if row['symbol'] != sym.replace('0',''):
            raise ValueError(f'Master zero-deletion evidence differs: row {i+1}')
        assign('stocks.csv',i,'symbol',sym,'SYMBOL_FROM_ISIN','ISIN check digit valid; ISIN[3:9] agrees with unchanged stock filenames and zero-deleted identifier')
        refs = dart['stock_refs'].get(sym, [])
        if not refs:
            raise ValueError(f'Restored DART master does not contain Toss symbol: {sym}')
        stock_evidence.append({'source_data_row_1based':i+1,'symbol_before':original['stocks.csv'][i]['symbol'],'symbol_restored':sym,'isinCode':isin,'isin_checksum_valid':True,'name_restored':row['name'],'englishName':row['englishName'],'matching_candle_file':sym+'_candles.csv','matching_investor_file':sym+'_investor_trading.csv','dart_corporation_candidates':json.dumps(refs, ensure_ascii=False),'evidence':'ISIN + filenames + zero-deletion round trip + restored DART master'})
    master = {r['symbol']:r for r in data['stocks.csv']}
    if set(master) != symbols or len(master) != 20:
        raise ValueError('Master/filename symbol mapping is not one-to-one.')
    for fn, rows in data.items():
        if fn == 'stocks.csv':
            continue
        expected = fn.split('_')[0]
        for i,row in enumerate(rows):
            assign(fn,i,'symbol',expected,'SYMBOL_FROM_FILENAME','Unmodified file name identifies the single stock/index in this file; master mapping verified')
            if 'currency' in row:
                assign(fn,i,'currency',master[expected]['currency'],'CURRENCY_FROM_MASTER','Same-symbol master currency; correcting a label, not converting prices')
    # All 42 daily files retain exactly the same 872-row ordering.
    series = {fn:rows for fn,rows in data.items() if fn!='stocks.csv'}
    if {len(v) for v in series.values()} != {872}:
        raise ValueError('Date consensus requires the declared equal source-row structure.')
    date_evidence = []; last_date = None
    for i in range(872):
        votes = collections.defaultdict(list)
        for fn, rows in series.items():
            c = 'date' if 'date' in rows[i] else 'timestamp'
            s = rows[i][c]
            if s:
                date_s = s[:10]
                datetime.strptime(date_s, '%Y-%m-%d')
                votes[date_s].append(fn)
        if len(votes) != 1:
            raise ValueError(f'Date alignment is not unanimous at source row {i+1}: {dict(votes)}')
        date_s, witnesses = next(iter(votes.items()))
        if len(witnesses)<2 or (last_date and date_s <= last_date):
            raise ValueError('Insufficient or non-monotonic date consensus.')
        last_date = date_s
        restored_files = []
        for fn,rows in series.items():
            c = 'date' if 'date' in rows[i] else 'timestamp'
            if not rows[i][c]:
                paired = fn.replace('_candles.csv','_investor_trading.csv') if fn.endswith('_candles.csv') else fn.replace('_investor_trading.csv','_candles.csv')
                why = f'Unanimous date in {len(witnesses)} other unchanged-order daily files at data row {i+1}; same-symbol pair {paired}'
                value = date_s if c=='date' else date_s+'T00:00:00.000+09:00'
                assign(fn,i,c,value,'MISSING_DATE_FROM_ALIGNED_FILES',why)
                restored_files.append(fn)
        date_evidence.append({'source_data_row_1based':i+1,'date':date_s,'independent_nonmissing_file_count':len(witnesses),'agreement':'UNANIMOUS','restored_file_count':len(restored_files),'restored_files':'|'.join(restored_files),'witness_files':'|'.join(witnesses)})
    # Parse nested JSON and repair only a derived net field, never the inputs.
    for fn, rows in data.items():
        for i,row in enumerate(rows):
            for c in JSON_COLUMNS.intersection(headers[fn]):
                if not row[c]:
                    continue
                try:
                    obj = json.loads(row[c])
                    if not isinstance(obj,dict):
                        raise ValueError('Not a JSON object')
                except (json.JSONDecodeError, ValueError):
                    issue(fn,i,c,'INVALID_JSON','JSON object missing or malformed.')
                    continue
                changed_paths = []
                def walk(d: dict[str,Any], path: str='') -> None:
                    keys = ('buyVolume','sellVolume','netBuyVolume')
                    if all(k in d for k in keys):
                        b,s,n = [decimal_value(d[k]) for k in keys]
                        if b is not None and s is not None and n is not None:
                            if b-s != n:
                                if not (b == b.to_integral_value() and s == s.to_integral_value()):
                                    issue(fn,i,c,'NONINTEGER_VOLUME','Cannot derive a share count from noninteger inputs.')
                                else:
                                    new = b-s
                                    d['netBuyVolume'] = str(int(new)) if isinstance(d['netBuyVolume'],str) else int(new)
                                    changed_paths.append(path+'netBuyVolume')
                                    semantic_fixes['net_buy_values_recomputed'] += 1
                                    if n == -new:
                                        semantic_fixes['net_buy_exact_sign_flip_pattern'] += 1
                    for key,value in d.items():
                        if isinstance(value,dict):
                            walk(value,path+key+'.')
                walk(obj)
                if changed_paths:
                    assign(fn,i,c,json.dumps(obj,ensure_ascii=False),'NET_BUY_FROM_BUY_MINUS_SELL','Derived only '+','.join(changed_paths)+'; buyVolume, sellVolume and other JSON leaves unchanged')
    # Required values and price consistency. Do NOT fabricate missing measurements.
    preserved_optional_blanks=collections.Counter(); zero_volume_rows=0
    for fn, rows in data.items():
        for i,row in enumerate(rows):
            if fn=='stocks.csv':
                required = ['symbol','name','englishName','isinCode','market','securityType','isCommonShare','status','currency','listDate','sharesOutstanding','koreanMarketDetail']
                for c in ['delistDate','leverageFactor']:
                    if row[c]=='':preserved_optional_blanks[c]+=1
            elif fn.endswith('_investor_trading.csv'):
                required = ['symbol','date','updatedAt','individual','foreigner','institution','otherCorporation','foreignerHolding']
                if row['cfd']=='':preserved_optional_blanks['cfd']+=1
            else:
                required = ['symbol','timestamp']+PRICE_COLUMNS+(['currency'] if 'currency' in row else [])
            for c in required:
                if row[c]=='':
                    issue(fn,i,c,'MISSING_REQUIRED_VALUE','Original value has been deleted; no exact duplicate/source value was supplied. Zero filling and interpolation were not used.')
            if 'openPrice' in row:
                values = {c:decimal_value(row[c]) for c in PRICE_COLUMNS}
                for c,n in values.items():
                    if row[c] and n is None:
                        issue(fn,i,c,'INVALID_NUMBER','Expected a finite numeric measurement.')
                    elif n is not None and (n < 0 or (c=='volume' and n!=n.to_integral_value())):
                        issue(fn,i,c,'INVALID_NUMERIC_DOMAIN','Prices/volume must be nonnegative and volume integral; zero is valid.')
                if values['volume']==0:zero_volume_rows+=1
                o,h,l,close = [values[k] for k in PRICE_COLUMNS[:4]]
                relations = [('low<=open',l,o),('open<=high',o,h),('low<=close',l,close),('close<=high',close,h),('low<=high',l,h)]
                broken = [name for name,a,b in relations if a is not None and b is not None and a>b]
                if broken:
                    issue(fn,i,'OHLC','OHLC_INCONSISTENT','Contradictory observed prices: '+', '.join(broken)+'. True intraday extrema cannot be recovered from open/close or by sorting values.')
                    issues[-1]['original_value']=json.dumps({c:original[fn][i][c] for c in PRICE_COLUMNS[:4]},ensure_ascii=False)
                    issues[-1]['current_value']=json.dumps({c:row[c] for c in PRICE_COLUMNS[:4]},ensure_ascii=False)
    # Validate JSON domains/identities after correction, including nested breakdowns.
    json_identity_checks=0
    for fn, rows in data.items():
        for i,row in enumerate(rows):
            for c in JSON_COLUMNS.intersection(headers[fn]):
                if not row[c]:continue
                try:obj=json.loads(row[c])
                except (ValueError,TypeError):continue
                def check_obj(d: Any, path: str='') -> None:
                    nonlocal json_identity_checks
                    if not isinstance(d,dict):return
                    if all(k in d for k in ['buyVolume','sellVolume','netBuyVolume']):
                        b,s,n=[decimal_value(d[k]) for k in ['buyVolume','sellVolume','netBuyVolume']]
                        json_identity_checks+=1
                        if None in (b,s,n) or b-s!=n or b<0 or s<0 or any(x!=x.to_integral_value() for x in (b,s,n)):
                            issue(fn,i,c,'INVALID_TRADING_IDENTITY','Nested trading identity or numeric domain failed at '+path)
                    for k,v in d.items():
                        if isinstance(v,dict):check_obj(v,path+k+'.')
                check_obj(obj)
    # No row deletion in the row-preserved edition. Release only issue-free rows.
    by_row=collections.defaultdict(list)
    for x in issues:by_row[x['source_file'],x['source_data_row_1based']-1].append(x)
    repair_log=[];lineage=[];quarantine=[];per_file=[]
    for fn,rows in data.items():
        clean_rows=[];changed_rows=set();changed_cells=0
        for i,row in enumerate(rows):
            row_issues=by_row.get((fn,i),[])
            if not row_issues:clean_rows.append(row)
            else:
                quarantine.append({'source_file':fn,'source_data_row_1based':i+1,'symbol':row['symbol'],'date':row.get('date',row.get('timestamp','')),'issue_codes':'|'.join(sorted({x['issue_code'] for x in row_issues})),'affected_columns':'|'.join(sorted({x['column_or_group'] for x in row_issues})),'original_row_json':json.dumps(original[fn][i],ensure_ascii=False),'partially_cleaned_row_json':json.dumps(row,ensure_ascii=False)})
            lineage.append({'source_file':fn,'source_data_row_1based':i+1,'preserved_data_row_1based':i+1,'bronze_data_row_1based':len(clean_rows) if not row_issues else '', 'status':'RELEASED' if not row_issues else 'QUARANTINED','issue_count':len(row_issues)})
            for c in headers[fn]:
                if original[fn][i][c] != row[c]:
                    changed_rows.add(i);changed_cells+=1
                    unresolved_c=any(x['column_or_group']==c for x in row_issues)
                    resolution='NULL_NORMALIZED_STILL_UNRESOLVED' if unresolved_c and row[c]=='' else ('DERIVED_IDENTITY_REPAIR' if 'NET_BUY_FROM_BUY_MINUS_SELL' in reasons[fn,i,c] else 'EVIDENCE_BASED_REPAIR')
                    repair_log.append(dict(zip(AUDIT_COLUMNS,['Toss',fn,i+1,c,original[fn][i][c],row[c],'|'.join(reasons[fn,i,c]),' | '.join(evidence[fn,i,c]),resolution])))
        full_path=out/'02_preserved_rows'/'Toss'/fn
        bronze_path=out/'01_bronze'/'Toss'/fn
        write_csv(full_path,headers[fn],rows);write_csv(bronze_path,headers[fn],clean_rows)
        for p,expected in [(full_path,rows),(bronze_path,clean_rows)]:
            h2,r2=read_csv(p)
            if h2!=headers[fn] or r2!=expected:raise ValueError(f'Reparse mismatch: {p}')
        date_key='date' if fn.endswith('_investor_trading.csv') else 'timestamp'
        keys=[(r['symbol'],r.get(date_key,'')) for r in clean_rows] if fn!='stocks.csv' else [r['symbol'] for r in clean_rows]
        if len(keys)!=len(set(keys)):raise ValueError(f'Duplicate released primary key: {fn}')
        per_file.append({'dataset':'Toss','source_file':fn,'input_encoding':'utf-8-sig','output_encoding':'utf-8-sig','input_rows':len(rows),'preserved_rows':len(rows),'bronze_rows':len(clean_rows),'quarantine_rows':len(rows)-len(clean_rows),'changed_rows':len(changed_rows),'changed_cells':changed_cells,'unresolved_issues':sum(len(by_row.get((fn,i),[])) for i in range(len(rows))),'schema_preserved':True,'reparse_ok':True,'input_sha256':sha256(paths[fn]),'bronze_sha256':sha256(bronze_path),'baseline_format_findings':'{}'})
    if rule_events['MOJIBAKE_REVERSE']!=96:raise ValueError('Mojibake restored count differs from supplied specification.')
    write_csv(out/'04_audit'/'Toss_repair_log.csv',AUDIT_COLUMNS,repair_log)
    write_csv(out/'04_audit'/'Toss_row_lineage.csv',['source_file','source_data_row_1based','preserved_data_row_1based','bronze_data_row_1based','status','issue_count'],lineage)
    write_csv(out/'04_audit'/'Toss_symbol_evidence.csv',list(stock_evidence[0]),stock_evidence)
    write_csv(out/'04_audit'/'Toss_date_alignment_evidence.csv',list(date_evidence[0]),date_evidence)
    issue_header=['dataset','source_file','source_data_row_1based','symbol','date','column_or_group','issue_code','original_value','current_value','reason','required_evidence','resolution']
    write_csv(out/'03_quarantine'/'Toss'/'unresolved_issues.csv',issue_header,issues)
    write_csv(out/'03_quarantine'/'Toss'/'quarantined_rows.csv',['source_file','source_data_row_1based','symbol','date','issue_codes','affected_columns','original_row_json','partially_cleaned_row_json'],quarantine)
    affected_rows = {(x['source_file'], int(x['source_data_row_1based'])) for x in repair_log} | {(x['source_file'], int(x['source_data_row_1based'])) for x in issues}
    repaired_cells = sum(x['resolution'] != 'NULL_NORMALIZED_STILL_UNRESOLVED' for x in repair_log)
    reconciliation = {'declared_affected_rows':35074, 'detected_affected_rows':len(affected_rows), 'declared_changed_cells':38050, 'repaired_cells_excluding_unresolved_null_markers':repaired_cells, 'unresolved_required_cells':sum(x['issue_code']=='MISSING_REQUIRED_VALUE' for x in issues), 'unresolved_ohlc_issue_groups':sum(x['issue_code']=='OHLC_INCONSISTENT' for x in issues), 'aggregate_total_matches':repaired_cells+len(issues)==38050, 'limitation':'Aggregate reconciliation is not a cell-by-cell comparison with a pristine Toss source; an OHLC group does not identify a unique original value.'}
    if len(affected_rows)!=35074 or repaired_cells+len(issues)!=38050:
        raise ValueError('Toss observed actions do not reconcile with supplied specification totals.')
    return {'specification_reconciliation':reconciliation,'csv_files':len(data),'input_rows':sum(map(len,data.values())),'preserved_rows':sum(map(len,data.values())),'bronze_rows':sum(p['bronze_rows'] for p in per_file),'quarantined_rows':len(quarantine),'unresolved_issues':len(issues),'issues_by_code':dict(collections.Counter(x['issue_code'] for x in issues)),'missing_required_by_column':dict(collections.Counter(x['column_or_group'] for x in issues if x['issue_code']=='MISSING_REQUIRED_VALUE')),'changed_rows':sum(p['changed_rows'] for p in per_file),'changed_cells':len(repair_log),'changes_by_resolution':dict(collections.Counter(x['resolution'] for x in repair_log)),'rule_events_overlapping_not_additive':dict(rule_events),'semantic_fixes':dict(semantic_fixes),'preserved_optional_blank_counts':dict(preserved_optional_blanks),'preserved_zero_volume_rows':zero_volume_rows,'date_alignment_rows_verified':len(date_evidence),'date_alignment_min_witnesses':min(x['independent_nonmissing_file_count'] for x in date_evidence),'json_trading_identity_checks':json_identity_checks,'all_original_values_fully_recovered':False,'release_definition':'Only records with no detected unresolved issue; this is not proof against undetectable corruption without a pristine reference.','per_file':per_file}


def make_manifest(out: Path) -> None:
    entries=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name!='SHA256SUMS':
            entries.append(f'{sha256(p)}  {p.relative_to(out).as_posix()}')
    (out/'SHA256SUMS').write_text('\n'.join(entries)+'\n',encoding='utf-8')


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if not args.input.is_file():parser.error('Input ZIP not found.')
    if (args.output/'01_bronze').exists():parser.error('Output data folder already exists. Choose an empty output path.')
    args.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='bronze_cleanup_') as tmp:
        sources=prepare_sources(args.input,Path(tmp),args.output)
        dart=restore_dart(sources['roots']['OpenDART'],args.output,sources)
        toss=clean_toss(sources['roots']['Toss'],args.output,dart)
    per_file=dart.pop('per_file')+toss.pop('per_file');dart.pop('stock_refs')
    write_csv(args.output/'04_audit'/'file_validation.csv',list(per_file[0]),per_file)
    summary={'dataset_version':'2026-10-14','definition':'User-requested cleaned-source Bronze. Raw-source copies were not modified.','OpenDART':dart,'Toss':toss,'totals':{'csv_files':dart['csv_files']+toss['csv_files'],'input_rows':dart['input_rows']+toss['input_rows'],'bronze_rows':dart['bronze_rows']+toss['bronze_rows'],'quarantined_rows':toss['quarantined_rows']},'scope_limits':['OpenDART exact restoration is verified against every supplied before/after entry; the pristine original ZIP was not supplied, so full original ZIP byte equality is not claimed.','Toss lost prices, volumes, JSON blocks, update times and inconsistent price extrema are not invented; unresolved rows remain in both the row-preserved edition and explicit quarantine.','Source-native optional blanks, zero trading volume and existing OpenDART download failures are preserved.','CSV encoding is standardized to UTF-8 BOM; header order, source row order and textual precision are preserved in the full editions.']}
    write_json(args.output/'04_audit'/'validation_summary.json',summary)
    make_manifest(args.output)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print(f'FAILED: {exc}',file=sys.stderr)
        raise
