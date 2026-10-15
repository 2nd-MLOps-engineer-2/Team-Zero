"""S4 C 수치 확인: 실행 중인 B API의 C 분석 값을 C Gold CSV와 독립적으로 대조한다.

B의 verify_s4.py와 별개로 C 쪽에서 직접 요청·비교한다. 값은 문자열 그대로 비교하고,
문자열이 다르면 Decimal 동일 여부로 '표기 차이'와 '값 차이'를 나눈다. CSV 빈칸은 API null과 같다고 본다.

Run: python -m analysis.verify_api --gold build/analysis [--base http://127.0.0.1:8000] [--out build/s4-c-review/api_check.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd


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
    try:
        return Decimal(a) == Decimal(b)
    except InvalidOperation:
        return False


class Tally:
    def __init__(self, name: str):
        self.name = name
        self.rows = 0
        self.cells = 0
        self.format_diff = 0
        self.value_diff: list[dict] = []
        self.missing_rows: list[str] = []
        self.missing_cols: Counter = Counter()

    def compare_row(self, key: str, gold: dict, api: dict | None, columns: list[str]) -> None:
        if api is None:
            self.missing_rows.append(key)
            return
        self.rows += 1
        for col in columns:
            if col not in api:
                self.missing_cols[col] += 1
                continue
            g, a = norm(gold[col]), norm(api[col])
            self.cells += 1
            if g == a:
                continue
            if g is not None and a is not None and same_number(g, a):
                self.format_diff += 1
            elif len(self.value_diff) < 50:
                self.value_diff.append({"key": key, "column": col, "gold": g, "api": a})
            else:
                self.value_diff.append({"key": key, "column": col})

    def result(self, expected_rows: int) -> dict:
        ok = (self.rows == expected_rows and not self.missing_rows and not self.value_diff
              and not self.missing_cols)
        return {
            "check": self.name, "status": "PASS" if ok else "FAIL",
            "rows_compared": self.rows, "rows_expected": expected_rows, "cells_compared": self.cells,
            "format_only_diff": self.format_diff, "value_diff_count": len(self.value_diff),
            "value_diff_sample": self.value_diff[:20], "missing_rows": self.missing_rows[:20],
            "missing_columns": dict(self.missing_cols),
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", type=Path, default=Path("build/analysis"))
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    read = lambda name: pd.read_csv(args.gold / name, dtype=str, keep_default_na=False)
    fin, daily = read("g_fin_rpt_analysis.csv"), read("g_stock_daily_analysis.csv")
    meta = get_json(args.base, "/health")["meta"]
    stocks = sorted(daily["stock_cd"].unique())
    results = []

    # 1) 일별: 종목별 전체 구간 조회 → 각 행 analysis 대 C 일별 Gold
    t = Tally("daily analysis (all stocks, all dates)")
    d_cols = list(daily.columns)
    for code in stocks:
        rows = get_json(args.base, f"/stocks/{code}/daily?limit=5000")["data"]
        by_dt = {r["trd_dt"]: r.get("analysis") for r in rows}
        for g in daily[daily["stock_cd"] == code].to_dict("records"):
            t.compare_row(f"{code}/{g['trd_dt']}", g, by_dt.get(g["trd_dt"]), d_cols)
    results.append(t.result(len(daily)))

    # 2) 보고서: 종목별 재무 조회(as_of 없음 = 부적격 보고서 포함) → analysis 대 C 보고서 Gold
    t = Tally("financial report analysis (all reports)")
    f_cols = list(fin.columns)
    api_fin: dict[str, dict] = {}
    for code in stocks:
        for r in get_json(args.base, f"/stocks/{code}/financials")["data"]:
            if r.get("analysis"):
                api_fin[r["fin_rpt_id"]] = r["analysis"]
    for g in fin.to_dict("records"):
        t.compare_row(g["fin_rpt_id"], g, api_fin.get(g["fin_rpt_id"]), f_cols)
    results.append(t.result(len(fin)))

    # 3) 기준일 비교: 마지막 거래일 기준 종목 비교 → 같은 날짜의 일별 Gold
    as_of = meta["data_final_date"]
    t = Tally(f"compare as_of={as_of}")
    last = daily[daily["trd_dt"] == daily["trd_dt"].max()]
    cmp_rows = {r["stock_cd"]: r.get("analysis") for r in get_json(args.base, f"/stocks/compare?as_of={as_of}")["data"]}
    for g in last.to_dict("records"):
        t.compare_row(g["stock_cd"], g, cmp_rows.get(g["stock_cd"]), d_cols)
    results.append(t.result(len(last)))

    # 4) 전량 다운로드 CSV: 바이트 해시가 C Gold와 같은지
    for name in ("g_fin_rpt_analysis.csv", "g_stock_daily_analysis.csv"):
        api_hash = hashlib.sha256(get(args.base, f"/exports/analysis/{name}")).hexdigest()
        gold_hash = hashlib.sha256((args.gold / name).read_bytes()).hexdigest()
        results.append({"check": f"export {name}", "status": "PASS" if api_hash == gold_hash else "FAIL",
                        "api_sha256": api_hash, "gold_sha256": gold_hash})

    report = {
        "api_meta": {k: meta.get(k) for k in ("api_version", "source_backend", "calculation_version",
                                              "analysis_status", "data_version", "analysis_data_version")},
        "gold_dir": str(args.gold), "results": results,
        "overall": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
