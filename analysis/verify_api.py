"""S4 C 수치 확인: 실행 중인 B API의 C 분석 값을 C Gold CSV와 독립적으로 대조한다.

B의 verify_s4.py와 별개로 C 쪽에서 직접 요청·비교한다. 값은 문자열 그대로 비교하고, 문자열이 다를 때
두 값이 모두 순수 숫자 형식(-?\\d+(\\.\\d+)?)이고 Decimal이 같으면 '표기 차이', 나머지는 '값 차이'로 본다.
CSV 빈칸은 API null과 같다고 본다. 행 단위 검사는 Gold와 API 양쪽의 키·컬럼 집합을 대조해
누락·추가·중복(API·Gold 양쪽)이 모두 0이고 값 차이가 없을 때만 PASS다.
종목 조회 404는 '그 종목 API 행 없음'으로 보고 Gold 행을 누락으로 센다. 그 밖의 HTTP 오류·연결 실패·응답 형식
오류는 errors에 기록하고 FAIL이다. 어느 경우든 결과 JSON은 남긴다.

Run: python -m analysis.verify_api --gold build/analysis [--base http://127.0.0.1:8000] [--out build/s4-c-review/api_check.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pandas as pd

DAILY_PAGE = 5000  # B API /stocks/{code}/daily 의 limit 상한
SAMPLE = 20
PLAIN_NUMBER = re.compile(r"-?\d+(\.\d+)?")
# 요청·응답 처리 실패로 기록할 예외 (HTTPError는 URLError 하위, 시간 초과는 OSError, JSON 해석 실패는 ValueError,
# 응답에 data 등 키가 없으면 KeyError/TypeError)
API_ERRORS = (urllib.error.URLError, OSError, ValueError, KeyError, TypeError)


def describe(exc: BaseException) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP {exc.code}"
    return f"{type(exc).__name__}: {exc}"


def is_not_found(exc: BaseException) -> bool:
    return isinstance(exc, urllib.error.HTTPError) and exc.code == 404


def get(base: str, path: str) -> bytes:
    with urllib.request.urlopen(base + path, timeout=60) as resp:
        return resp.read()


def get_json(base: str, path: str) -> dict:
    return json.loads(get(base, path))


def norm(value) -> str | None:
    if value is None:
        return None
    text = str(value)
    return None if text == "" else text


def same_number(a: str, b: str) -> bool:
    """두 문자열이 모두 순수 숫자 형식이고 Decimal 값이 같을 때만 True (공백·밑줄·지수 표기 등은 값 차이)."""
    if not (PLAIN_NUMBER.fullmatch(a) and PLAIN_NUMBER.fullmatch(b)):
        return False
    return Decimal(a) == Decimal(b)


class Tally:
    """Gold 행과 API 행을 키 단위로 모아 양방향으로 대조한다."""

    def __init__(self, name: str):
        self.name = name
        self.api: dict[str, dict] = {}
        self.duplicate_keys: list[str] = []
        self.notes: list[str] = []  # 잘림·날짜 불일치 등 행 대조 밖의 FAIL 사유
        self.errors: list[str] = []  # 404가 아닌 HTTP 오류·연결 실패 등 (FAIL)
        self.not_found: list[str] = []  # 404로 API 행이 없다고 본 종목 (Gold에 행이 있으면 누락으로 FAIL)

    def add_api(self, key: str, row: dict | None) -> None:
        if not row:  # analysis가 없는 API 행은 분석 행으로 세지 않는다 (Gold에 있으면 누락으로 잡힘)
            return
        if key in self.api:
            self.duplicate_keys.append(key)
            return
        self.api[key] = row

    def result(self, gold_rows: list[tuple[str, dict]], columns: list[str]) -> dict:
        gold: dict[str, dict] = {}
        gold_dups: list[str] = []
        for key, row in gold_rows:
            if key in gold:
                gold_dups.append(key)
                continue
            gold[key] = row
        cells = fmt = 0
        value_diff: list[dict] = []
        missing_cols: Counter = Counter()
        extra_cols: Counter = Counter()
        missing_rows = sorted(set(gold) - set(self.api))
        extra_rows = sorted(set(self.api) - set(gold))
        gold_cols = set(columns)
        for key, a_row in self.api.items():
            for col in a_row:
                if col not in gold_cols:
                    extra_cols[col] += 1
        compared = sorted(set(gold) & set(self.api))
        for key in compared:
            g_row, a_row = gold[key], self.api[key]
            for col in columns:
                if col not in a_row:
                    missing_cols[col] += 1
                    continue
                g, a = norm(g_row[col]), norm(a_row[col])
                cells += 1
                if g == a:
                    continue
                if g is not None and a is not None and same_number(g, a):
                    fmt += 1
                else:
                    value_diff.append({"key": key, "column": col, "gold": g, "api": a})
        ok = not (missing_rows or extra_rows or self.duplicate_keys or gold_dups or missing_cols or extra_cols
                  or value_diff or self.notes or self.errors)
        return {
            "check": self.name, "status": "PASS" if ok else "FAIL",
            "rows_gold": len(gold_rows), "rows_api": len(self.api), "rows_compared": len(compared),
            "cells_compared": cells, "format_only_diff": fmt,
            "value_diff_count": len(value_diff), "value_diff_sample": value_diff[:SAMPLE],
            "missing_row_count": len(missing_rows), "missing_rows": missing_rows[:SAMPLE],
            "extra_row_count": len(extra_rows), "extra_rows": extra_rows[:SAMPLE],
            "duplicate_key_count": len(self.duplicate_keys), "duplicate_keys": self.duplicate_keys[:SAMPLE],
            "gold_duplicate_key_count": len(gold_dups), "gold_duplicate_keys": gold_dups[:SAMPLE],
            "missing_columns": dict(missing_cols), "extra_columns": dict(extra_cols),
            "notes": self.notes, "errors": self.errors, "api_not_found_stocks": self.not_found,
        }


def api_stock_codes(base: str) -> set[str]:
    codes: set[str] = set()
    offset = 0
    while True:
        body = get_json(base, f"/stocks?limit=100&offset={offset}")
        page = body["data"]
        codes.update(r["stock_cd"] for r in page)
        offset += len(page)
        if not page or offset >= body.get("meta", {}).get("total", offset):
            return codes


def fetch_daily(base: str, code: str, t: Tally, page_size: int = DAILY_PAGE) -> list[dict]:
    """limit/offset로 끝까지 이어 받는다. meta.total과 받은 행 수가 다르면 잘림으로 FAIL 사유를 남긴다.

    첫 페이지 404는 그 종목 API 행 없음([] 반환). 그 밖의 실패는 t.errors에 남기고 받은 데까지만 반환한다.
    """
    rows: list[dict] = []
    total = None
    while True:
        try:
            body = get_json(base, f"/stocks/{code}/daily?limit={page_size}&offset={len(rows)}")
            page = body["data"]
        except API_ERRORS as exc:
            if is_not_found(exc) and not rows:
                t.not_found.append(code)
            else:
                t.errors.append(f"{code}: daily offset={len(rows)}: {describe(exc)}")
            return rows
        total = body.get("meta", {}).get("total", total)
        rows.extend(page)
        if len(page) < page_size or (total is not None and len(rows) >= total):
            break
    if total is not None and len(rows) != total:
        t.notes.append(f"{code}: daily received {len(rows)} rows but meta.total={total}")
    return rows


def check_daily(base: str, daily: pd.DataFrame, codes: list[str], page_size: int = DAILY_PAGE,
                listed: set[str] | None = None) -> dict:
    t = Tally("daily analysis (all stocks, all dates)")
    for code in codes:
        for r in fetch_daily(base, code, t, page_size):
            t.add_api(f"{code}/{r['trd_dt']}", r.get("analysis"))
    for code in sorted(set(t.not_found) & (listed or set())):
        t.errors.append(f"{code}: listed by /stocks but daily returned HTTP 404")
    gold = [(f"{g['stock_cd']}/{g['trd_dt']}", g) for g in daily.to_dict("records")]
    return t.result(gold, list(daily.columns))


def check_financials(base: str, fin: pd.DataFrame, codes: list[str], listed: set[str] | None = None) -> dict:
    # as_of 없음 = 부적격 보고서 포함 전체
    t = Tally("financial report analysis (all reports)")
    for code in codes:
        try:
            data = get_json(base, f"/stocks/{code}/financials")["data"]
        except API_ERRORS as exc:
            if is_not_found(exc):
                t.not_found.append(code)
                if code in (listed or set()):
                    t.errors.append(f"{code}: listed by /stocks but financials returned HTTP 404")
            else:
                t.errors.append(f"{code}: financials: {describe(exc)}")
            continue
        for r in data:
            t.add_api(r["fin_rpt_id"], r.get("analysis"))
    gold = [(g["fin_rpt_id"], g) for g in fin.to_dict("records")]
    return t.result(gold, list(fin.columns))


def check_compare(base: str, daily: pd.DataFrame, api_final_date: str | None) -> dict:
    """Gold 마지막 거래일로 API를 조회하고, 같은 날짜 기준 종목별 마지막 관측 행과 대조한다."""
    as_of = daily["trd_dt"].max()
    t = Tally(f"compare as_of={as_of}")
    if api_final_date != as_of:
        t.notes.append(f"date mismatch: API meta.data_final_date={api_final_date}, Gold max trd_dt={as_of}")
    try:
        body = get_json(base, f"/stocks/compare?as_of={as_of}")
        requested = body.get("meta", {}).get("requested_as_of")
        if requested is not None and str(requested) != as_of:
            t.notes.append(f"date mismatch: API meta.requested_as_of={requested}, queried as_of={as_of}")
        for r in body["data"]:
            t.add_api(r["stock_cd"], r.get("analysis"))
    except API_ERRORS as exc:  # 비교 조회는 404도 오류 (종목 단위 조회가 아님)
        t.errors.append(f"compare as_of={as_of}: {describe(exc)}")
    # 종목별 마지막 관측일의 Gold 행 전부 (같은 날짜가 두 번이면 Gold 중복으로 잡힌다)
    upto = daily[daily["trd_dt"] <= as_of]
    last = upto[upto["trd_dt"] == upto.groupby("stock_cd")["trd_dt"].transform("max")]
    gold = [(g["stock_cd"], g) for g in last.sort_values(["stock_cd", "trd_dt"]).to_dict("records")]
    res = t.result(gold, list(daily.columns))
    res["as_of_queried"] = as_of
    res["api_data_final_date"] = api_final_date
    return res


def check_exports(base: str, gold_dir: Path) -> list[dict]:
    out = []
    for name in ("g_fin_rpt_analysis.csv", "g_stock_daily_analysis.csv"):
        gold_hash = hashlib.sha256((gold_dir / name).read_bytes()).hexdigest()
        try:
            api_hash = hashlib.sha256(get(base, f"/exports/analysis/{name}")).hexdigest()
        except API_ERRORS as exc:
            out.append({"check": f"export {name}", "status": "FAIL", "api_sha256": None,
                        "gold_sha256": gold_hash, "errors": [describe(exc)]})
            continue
        out.append({"check": f"export {name}", "status": "PASS" if api_hash == gold_hash else "FAIL",
                    "api_sha256": api_hash, "gold_sha256": gold_hash})
    return out


def run(base: str, gold_dir: Path, page_size: int = DAILY_PAGE) -> dict:
    read = lambda name: pd.read_csv(gold_dir / name, dtype=str, keep_default_na=False)
    fin, daily = read("g_fin_rpt_analysis.csv"), read("g_stock_daily_analysis.csv")
    errors: list[str] = []
    try:
        meta = get_json(base, "/health")["meta"]
    except API_ERRORS as exc:
        meta = {}
        errors.append(f"/health: {describe(exc)}")
    # Gold에서 종목 전체가 빠져도 API 쪽 추가 행을 잡도록 API 종목 목록과 합친다
    try:
        listed = api_stock_codes(base)
    except API_ERRORS as exc:
        listed = set()
        errors.append(f"/stocks: {describe(exc)}")
    codes = sorted((set(daily["stock_cd"]) | set(fin["stock_cd"]) | listed) - {""})
    results = [check_daily(base, daily, codes, page_size, listed), check_financials(base, fin, codes, listed),
               check_compare(base, daily, meta.get("data_final_date"))]
    results += check_exports(base, gold_dir)
    return {
        "api_meta": {k: meta.get(k) for k in ("api_version", "source_backend", "calculation_version",
                                              "analysis_status", "data_version", "analysis_data_version")},
        "gold_dir": gold_dir.as_posix(), "errors": errors, "results": results,
        "overall": "PASS" if not errors and all(r["status"] == "PASS" for r in results) else "FAIL",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, default=Path("build/analysis"))
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        report = run(args.base, args.gold)
    except Exception as exc:  # Gold 파일 읽기 실패 등도 FAIL 결과로 남긴다
        report = {"gold_dir": args.gold.as_posix(), "errors": [f"run: {type(exc).__name__}: {exc}"],
                  "results": [], "overall": "FAIL"}
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
