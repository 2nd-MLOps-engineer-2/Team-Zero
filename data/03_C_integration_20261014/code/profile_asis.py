"""AS-IS 프로파일링 (Pandas).

A·B 가 넘겨준 실버 후보 데이터를 '제공받은 레거시'로 보고, 통합 전 품질 문제를 수치로 진단한다.
결측 · 중복 · 형식 불일치 · 코드값 혼용 · 명명 규칙 불일치 5개 축으로 측정한다.

실행: python code/profile_asis.py [--a-dir ...] [--b-dir ...]
출력: 01_profiling/
"""
from __future__ import annotations
import argparse, re
from collections import Counter

import pandas as pd

from common import ROOT, input_dirs, load_inputs, write_csv, dump_json
from std_dictionary import check_name

OUT = ROOT / "01_profiling"

# 프로파일 대상과 선언된 키(인계 문서 기준)
TARGETS = {
    ("A", "company_master"): ["corp_code"],
    ("A", "disclosures"): ["rcept_no"],
    ("A", "disclosure_documents"): ["rcept_no"],
    ("A", "financial_summary"): ["financial_report_id"],
    ("A", "financial_items"): ["financial_item_id"],
    ("A", "metric_definitions"): ["metric"],
    ("B", "security_master"): ["symbol"],
    ("B", "stock_daily_price"): ["symbol", "trade_date"],
    ("B", "market_index_daily"): ["index_code", "trade_date"],
    ("B", "investor_trading_daily"): ["symbol", "trade_date", "investor_type"],
    ("B", "foreign_holding_daily"): ["symbol", "trade_date"],
    ("B", "cfd_daily"): ["symbol", "trade_date"],
    ("B", "price_investor_availability"): ["symbol", "trade_date"],
    ("B", "investor_source_daily"): ["symbol", "trade_date"],
}

PATTERNS = [  # (이름, regex) 앞에서부터 첫 일치
    ("EMPTY", r""),
    ("DATE_ISO", r"\d{4}-\d{2}-\d{2}"),
    ("DATE_YYYYMMDD", r"(19|20)\d{6}"),
    ("DATETIME_OFFSET", r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?[+-]\d{2}:\d{2}"),
    ("BOOL_TF", r"True|False"),
    ("BOOL_tf", r"true|false"),
    ("SHA256", r"(sha256:)?[0-9a-f]{64}"),
    ("ZERO_PAD_DIGITS", r"0\d+"),
    ("INTEGER", r"-?\d+"),
    ("DECIMAL", r"-?\d+\.\d+"),
    ("JSON", r"[\[{].*[\]}]"),
    ("PLACEHOLDER", r"-|-표준계정코드 미사용-|N/A|NULL|null|None"),
    ("UPPER_CODE", r"[A-Z][A-Z0-9_]*"),
    ("LOWER_CODE", r"[a-z][a-z0-9_]*"),
    ("CAMEL_CODE", r"[a-z]+[A-Z][A-Za-z]*"),
]
_COMPILED = [(n, re.compile(p, re.S)) for n, p in PATTERNS]


def pattern_of(v: str) -> str:
    for n, rx in _COMPILED:
        if rx.fullmatch(v):
            return n
    return "TEXT"


def naming_style(c: str) -> str:
    if c.startswith("_"):
        return "leading_underscore"
    if re.fullmatch(r"[a-z]+([A-Z][a-z0-9]*)+", c):
        return "camelCase"
    if re.fullmatch(r"[a-z][a-z0-9]*(_[a-z0-9]+)*", c):
        return "snake_case"
    return "other"


def profile_column(team, tbl, df, col):
    s = df[col]
    n = len(s)
    empty = int((s == "").sum())
    vals = s[s != ""]
    # 큰 테이블은 패턴 판정에 고유값만 사용(속도)
    uniq = vals.drop_duplicates()
    pc = Counter()
    if len(uniq):
        pat_u = uniq.map(pattern_of)
        cnt = vals.value_counts()
        for v, p in zip(uniq, pat_u):
            pc[p] += int(cnt[v])
    pats = "|".join(f"{k}:{v}" for k, v in pc.most_common())
    placeholder = int(pc.get("PLACEHOLDER", 0))
    top = vals.value_counts().head(3)
    return dict(
        src_team=team, table=tbl, column=col, rows=n,
        null_cnt=empty, null_rate=round(empty / n, 6) if n else 0,
        placeholder_cnt=placeholder,
        distinct_cnt=int(vals.nunique()),
        max_len=int(vals.str.len().max()) if len(vals) else 0,
        pattern_mix_cnt=len([p for p in pc if p != "EMPTY"]),
        patterns=pats,
        top_values="; ".join(f"{str(k)[:40]}({v})" for k, v in top.items()),
        naming_style=naming_style(col),
        std_name_ok="Y" if not check_name(col) else "N",
        std_name_violation="; ".join(check_name(col)),
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a-dir"); ap.add_argument("--b-dir")
    a = ap.parse_args()
    adir, bdir = input_dirs(a.a_dir, a.b_dir)
    A, B = load_inputs(adir, bdir)
    data = {("A", k): v for k, v in A.items()} | {("B", k): v for k, v in B.items()}

    col_rows, tbl_rows = [], []
    for (team, tbl), key in TARGETS.items():
        df = data[(team, tbl)]
        for c in df.columns:
            col_rows.append(profile_column(team, tbl, df, c))
        dup_key = int(df.duplicated(key, keep=False).sum())
        dup_full = int(df.duplicated(keep=False).sum())
        null_cells = int((df == "").to_numpy().sum())
        tbl_rows.append(dict(src_team=team, table=tbl, rows=len(df), cols=df.shape[1], declared_key="+".join(key),
                             key_dup_rows=dup_key, full_row_dup_rows=dup_full,
                             null_cells=null_cells, null_cell_rate=round(null_cells / df.size, 6) if df.size else 0))
    colp = pd.DataFrame(col_rows)
    tblp = pd.DataFrame(tbl_rows)

    # ------------------------------------------------------------------
    # 통합 관점의 AS-IS 문제(수치)
    # ------------------------------------------------------------------
    cm, sm = A["company_master"], B["security_master"]
    d, it, s = A["disclosures"], A["financial_items"], A["financial_summary"]
    docs = A["disclosure_documents"]
    issues = []

    def add(axis, item, count, base, evidence):
        issues.append(dict(axis=axis, item=item, count=int(count), base=int(base),
                           rate=round(count / base, 6) if base else None, evidence=evidence))

    # 1) 결측
    add("결측", "재무 상세 당기금액(thstrm_amount) 빈값", (it.thstrm_amount == "").sum(), len(it),
        "A financial_items_all — 원천 허용 결측 여부 확인 대상, 0 대체 금지")
    add("결측", "재무 요약 공시일(disclosure_date) 빈값", (s.disclosure_date == "").sum(), len(s),
        "공시목록 수집 범위 밖 → 시점 조인 불가")
    add("결측", "수급 원천 없음(가격만 있는 종목·거래일)", (B["price_investor_availability"].has_investor_data == "false").sum(),
        len(B["price_investor_availability"]), "247540/2026-04-16 검토 대기")
    add("결측", "CFD 잔고 미제공 종목·거래일", len(B["stock_daily_price"]) - len(B["cfd_daily"]), len(B["stock_daily_price"]),
        f"CFD 는 {B['cfd_daily'].trade_date.min()} 부터만 존재")
    # 2) 중복
    add("중복", "선언 키 중복 행(전체 대상 테이블 합)", tblp.key_dup_rows.sum(), tblp.rows.sum(), "모든 인계 테이블 키 유일")
    k5 = ["rcept_no", "fs_div", "sj_div", "account_id", "account_detail"]
    add("중복", "재무 상세: 접수번호+연결구분+양식+계정ID+상세 키 충돌 행", it.duplicated(k5, keep="first").sum(), len(it),
        "PDF 경고 9,120건 유형 — 중복 아님(account_nm·ord 로 구분). 삭제 금지")
    # 3) 형식 불일치
    add("형식", "날짜 YYYYMMDD 문자열(rcept_dt·modify_date)",
        d.rcept_dt.str.fullmatch(r"\d{8}").sum() + cm.modify_date.str.fullmatch(r"\d{8}").sum() + docs.rcept_dt.str.fullmatch(r"\d{8}").sum(),
        len(d) + len(cm) + len(docs), "A 는 YYYYMMDD 와 YYYY-MM-DD(disclosure_date) 혼용, B 는 YYYY-MM-DD")
    add("형식", "시각 문자열에 +09:00 오프셋 포함(timestamp·fetched_at·updated_at)",
        B["stock_daily_price"].timestamp.str.contains(r"\+09:00").sum() + B["market_index_daily"].timestamp.str.contains(r"\+09:00").sum(),
        len(B["stock_daily_price"]) + len(B["market_index_daily"]), "DB DATETIME 적재 시 KST 로 변환 필요")
    add("형식", "출처 버전 표기 형식 2종(A 패키지명 vs B sha256)",
        (s.source_version == "Bronze_Cleanup_20261014").sum() + (it._source_version == "Bronze_Cleanup_20261014").sum(),
        len(s) + len(it), "A: 'Bronze_Cleanup_20261014', B: 'sha256:<64hex>'")
    js = colp[colp.patterns.str.contains("JSON:")]
    js_cnt = sum(int(re.search(r"JSON:(\d+)", p).group(1)) for p in js.patterns)
    add("형식", "JSON 문자열 셀(정형 컬럼과 별개로 보존된 원본 JSON)", js_cnt, int(js.rows.sum()),
        ", ".join(f"{r.table}.{r.column}" for r in js.itertuples()))
    # 4) 코드값 혼용
    bool_vals = Counter()
    for df, c in ((sm, "isCommonShare"), (B["price_investor_availability"], "has_price"),
                  (B["price_investor_availability"], "has_investor_data"),
                  (s, "point_in_time_join_eligible"), (s, "same_period_comparison_eligible")):
        for v, n in df[c].value_counts().items():
            bool_vals[v] += n
    add("코드값", "불리언 표기 혼용: " + ", ".join(f"'{k}'×{v}" for k, v in bool_vals.items()), sum(bool_vals.values()),
        sum(bool_vals.values()), "True/False, true/false, 1/0 세 방식 → 표준 Y/N")
    st = docs.status.value_counts().to_dict() | {"NOT_IN_INPUT(공시 측)": int((d.document_status == "NOT_IN_INPUT").sum())}
    add("코드값", "문서 상태 대소문자 혼용: " + ", ".join(f"{k}×{v}" for k, v in st.items()), sum(st.values()), sum(st.values()),
        "downloaded/unavailable(소문자) vs NOT_IN_INPUT(대문자)")
    itd = B["investor_trading_daily"]
    camel = itd.investor_type.str.fullmatch(r"[a-z]+[A-Z]\w*").sum()
    add("코드값", "투자자유형 camelCase 코드값(financialInvestment 등)", camel, len(itd),
        "같은 테이블의 aggregation_level 은 snake_case(top_level) — 코드 표기 규칙 혼재")
    add("코드값", "계정ID 자리표시값 '-표준계정코드 미사용-'", (it.account_id == "-표준계정코드 미사용-").sum(), len(it),
        "코드 컬럼에 설명 문구가 값으로 들어감 — 원값 보존 + 사전에 의미 등록")
    add("코드값", "계정상세 자리표시값 '-'(상세 없음)", (it.account_detail == "-").sum(), len(it), "빈값 대신 '-' 사용 — 원값 보존")
    add("코드값", "법인구분(corp_cls) Y/K 와 시장(market) KOSPI/KOSDAQ 이 같은 의미를 다른 코드로 표현",
        len(d), len(d), "Y↔KOSPI, K↔KOSDAQ — 표준 코드 MKT 로 대응표 관리")
    # 5) 명명 규칙
    st_cnt = colp.naming_style.value_counts().to_dict()
    add("명명", "컬럼 명명 스타일 분포: " + ", ".join(f"{k}×{v}" for k, v in st_cnt.items()),
        len(colp) - st_cnt.get("snake_case", 0), len(colp), "B security_master camelCase, A 추적 컬럼 '_' 접두사")
    syn = [("종목코드", "A.stock_code", "B.symbol"), ("종목/기업명", "A.corp_name", "B.name"),
           ("원천파일", "A._source_file", "B.source_file"), ("원천행", "A._source_row", "B.source_row"),
           ("원천버전", "A._source_version", "B.source_version"), ("공시일", "A.rcept_dt", "A.disclosure_date"),
           ("영문명", "A.corp_eng_name", "B.englishName"), ("거래량", "B.volume", "B.buy_volume(수량 의미 혼용)")]
    add("명명", "같은 개념 다른 컬럼명(이음동의) 쌍", len(syn), len(syn), " / ".join(f"{a}:{b}≠{c}" for a, b, c in syn))
    ok = (colp.std_name_ok == "Y").sum()
    add("명명", "표준 단어 조합 규칙 준수 컬럼(AS-IS)", ok, len(colp), "TO-BE 표준 사전 기준으로 측정한 현행 준수율")
    # 6) 참조·연결
    add("참조", "재무 요약 접수번호 중 공시목록에 없는 건", (~s.rcept_no.isin(d.rcept_no)).sum(), len(s), "공시목록 수집 범위 밖")
    m = cm.merge(sm, left_on="stock_code", right_on="symbol", how="outer", indicator=True)
    add("참조", "기업-종목 종목코드 기준 미연결", (m._merge != "both").sum(), len(m), "A 20 · B 20 모두 종목코드로 1:1 연결")
    nm = m[(m._merge == "both") & (m.corp_name != m["name"])]
    add("참조", "기업명≠종목명(동일 종목코드)", len(nm), len(m), "; ".join(f"{r.stock_code}:{r.corp_name}≠{r['name']}" for _, r in nm.iterrows()))
    dd = s[s.disclosure_date != ""].merge(d[["rcept_no", "rcept_dt"]], on="rcept_no", how="left")
    mism = (dd.disclosure_date.str.replace("-", "") != dd.rcept_dt).sum()
    add("참조", "요약 공시일 ≠ 공시목록 접수일(형식 통일 후)", mism, len(dd), "정규화(s_fin_rpt 에서 공시일 제거) 가능 여부 확인")

    iss = pd.DataFrame(issues)
    write_csv(colp, OUT / "asis_column_profile.csv")
    write_csv(tblp, OUT / "asis_table_profile.csv")
    write_csv(iss, OUT / "asis_issue_summary.csv")
    summary = dict(
        tables=len(tblp), columns=len(colp), rows_total=int(tblp.rows.sum()),
        null_cells=int(tblp.null_cells.sum()), cells=int((tblp.rows * tblp.cols).sum()),
        key_dup_rows=int(tblp.key_dup_rows.sum()),
        columns_with_pattern_mix=int((colp.pattern_mix_cnt > 1).sum()),
        naming_style=st_cnt,
        std_name_compliance_asis=round(ok / len(colp), 4),
    )
    dump_json(summary, OUT / "asis_summary.json")
    print(summary)
    print(iss[["axis", "item", "count", "base", "rate"]].to_string())


if __name__ == "__main__":
    main()
