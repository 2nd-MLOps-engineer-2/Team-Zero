"""통합 검증 — SQL(MySQL) 과 Pandas(CSV) 로 같은 규칙을 이중 검사.

  V1 레이어 간 건수·값 대사      V2 키 무결성(PK·FK·출처 추적)
  V3 표준 준수율(AS-IS vs TO-BE)  V4 도메인·코드·업무 규칙 위반 건수
  V5 재실행 일관성(--rerun)       V6 A 인계 스크립트와 시점 조인 교차검증

실행: python code/validate.py --socket /var/run/mysqld/mysqld.sock [--rerun]
출력: 05_validation/
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from decimal import Decimal

import pandas as pd

from common import ROOT, input_dirs, read_csv, write_csv, dump_json, A_FILES
from std_dictionary import TABLES, DOMAINS, CODES, check_name
from load_mysql import connect

OUT = ROOT / "05_validation"
O = ROOT / "04_output"
RES: list[dict] = []
SQLS: list[str] = []


def q(cur, sql):
    cur.execute(sql)
    return cur.fetchall()


def scalar(cur, sql):
    SQLS.append(sql.strip().rstrip(";") + ";")
    return q(cur, sql)[0][0]


def rec(cid, cat, item, expected, sql_v=None, pd_v=None, note="", ok=None):
    vals = [v for v in (sql_v, pd_v) if v is not None]
    if ok is None:
        ok = all(str(v) == str(expected) for v in vals) if expected is not None else True
    if sql_v is not None and pd_v is not None and str(sql_v) != str(pd_v):
        ok = False
    RES.append(dict(check_id=cid, category=cat, item=item, expected=expected, sql_result=sql_v, pandas_result=pd_v,
                    status="PASS" if ok else "FAIL", note=note))


def load_csvs():
    D = {}
    for sub in ("silver", "gold"):
        for p in (O / sub).glob("*.csv"):
            D[p.stem] = read_csv(p)
    return D


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1"); ap.add_argument("--port", type=int, default=3306)
    ap.add_argument("--user", default="root"); ap.add_argument("--password"); ap.add_argument("--socket")
    ap.add_argument("--a-dir"); ap.add_argument("--b-dir"); ap.add_argument("--rerun", action="store_true")
    a = ap.parse_args()
    adir, bdir = input_dirs(a.a_dir, a.b_dir)
    con = connect(a); cur = con.cursor()
    D = load_csvs()
    n = lambda t: len(D[t])

    # ------------------------------------------------------------------ V1 건수·값 대사
    pairs = [("b_a_company_master", "s_corp"), ("b_a_disclosures", "s_dscl"), ("b_a_disclosure_documents", "s_dscl_doc"),
             ("b_a_financial_summary", "s_fin_rpt"), ("b_a_metric_definitions", "s_fin_mtrc_def"),
             ("b_a_financial_items", "s_fin_item"), ("b_b_security_master", "s_stock"),
             ("b_b_stock_daily_price", "s_stock_daily_prc"), ("b_b_market_index_daily", "s_idx_daily_prc"),
             ("b_b_investor_trading_daily", "s_invstr_trd_daily"), ("b_b_foreign_holding_daily", "s_frgn_hold_daily"),
             ("b_b_cfd_daily", "s_cfd_bal_daily")]
    for i, (b, s) in enumerate(pairs, 1):
        bc = scalar(cur, f"SELECT COUNT(*) FROM tz_bronze.{b}")
        sc = scalar(cur, f"SELECT COUNT(*) FROM tz_silver.{s}")
        rec(f"V1-{i:02d}", "V1 건수 대사", f"Bronze {b} → Silver {s}", bc, sc, n(s), "행 보존(삭제·증식 없음)")
    wide = json.loads((O / "output_sha256.json").read_text())["wide_metric_columns"]
    bc = scalar(cur, "SELECT COUNT(*) FROM tz_bronze.b_a_financial_summary")
    rec("V1-13", "V1 건수 대사", f"Bronze 재무요약 {bc}행 × 지표열 {wide} → s_fin_mtrc", bc * wide,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_fin_mtrc"), n("s_fin_mtrc"), "넓은 표 UNPIVOT(정규화) 건수")
    u = scalar(cur, "SELECT COUNT(*) FROM (SELECT symbol, trade_date FROM tz_bronze.b_b_stock_daily_price UNION "
                    "SELECT symbol, trade_date FROM tz_bronze.b_b_investor_trading_daily) k")
    rec("V1-14", "V1 건수 대사", "가격∪수급 키(Bronze) → s_conn_stts", u, scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_conn_stts"),
        n("s_conn_stts"), "내부조인이 아닌 합집합")
    both_b = scalar(cur, "SELECT COUNT(*) FROM tz_bronze.b_b_price_investor_availability WHERE has_price='true' AND has_investor_data='true'")
    rec("V1-15", "V1 건수 대사", "B 가용성표 '모두 있음' ↔ C 연결상태 BOTH", both_b,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_conn_stts WHERE conn_stts_cd='BOTH'"),
        int((D["s_conn_stts"].conn_stts_cd == "BOTH").sum()), "B 자체 판정과 C 재계산 일치")
    rec("V1-16", "V1 건수 대사", "Silver s_stock_daily_prc → Gold g_ai_stock_daily", n("s_stock_daily_prc"),
        scalar(cur, "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily"), n("g_ai_stock_daily"), "조인 팽창·손실 없음")
    rec("V1-17", "V1 건수 대사", "Silver s_fin_rpt → Gold g_fin_rpt_mkt_smry", n("s_fin_rpt"),
        scalar(cur, "SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry"), n("g_fin_rpt_mkt_smry"))
    a_self = scalar(cur, "SELECT COUNT(*) FROM tz_bronze.b_a_review_issues")
    rec("V1-18", "V1 건수 대사", "A review_issues → s_dq_issue(A_SELF)", a_self,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_dq_issue WHERE detect_stage_cd='A_SELF'"),
        int((D["s_dq_issue"].detect_stage_cd == "A_SELF").sum()))
    b_self = scalar(cur, "SELECT (SELECT COUNT(*) FROM tz_bronze.b_b_data_quality_issues)+(SELECT COUNT(*) FROM tz_bronze.b_b_bronze_unresolved_issues)+(SELECT COUNT(*) FROM tz_bronze.b_b_pending_recovery_review)")
    rec("V1-19", "V1 건수 대사", "B 이슈 3종 → s_dq_issue(B_SELF)", b_self,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_dq_issue WHERE detect_stage_cd='B_SELF'"),
        int((D["s_dq_issue"].detect_stage_cd == "B_SELF").sum()))
    # 값 보존(합계 대사) — 정수 정밀도 유지 여부
    sums = [("V1-20", "순매수 합계", "SELECT SUM(CAST(net_buy_volume AS SIGNED)) FROM tz_bronze.b_b_investor_trading_daily",
             "SELECT SUM(net_buy_qty) FROM tz_silver.s_invstr_trd_daily", lambda: sum(int(x) for x in D["s_invstr_trd_daily"].net_buy_qty)),
            ("V1-21", "종가 합계", "SELECT SUM(CAST(close_price AS DECIMAL(18,4))) FROM tz_bronze.b_b_stock_daily_price",
             "SELECT SUM(close_prc) FROM tz_silver.s_stock_daily_prc", lambda: sum(Decimal(x) for x in D["s_stock_daily_prc"].close_prc)),
            ("V1-22", "재무 당기금액 합계", "SELECT SUM(CAST(NULLIF(thstrm_amount,'') AS DECIMAL(30,0))) FROM tz_bronze.b_a_financial_items",
             "SELECT SUM(cur_amt) FROM tz_silver.s_fin_item", lambda: sum(int(x) for x in D["s_fin_item"].cur_amt if x)),
            ("V1-23", "재무 당기금액 빈값(NULL) 건수", "SELECT SUM(thstrm_amount='') FROM tz_bronze.b_a_financial_items",
             "SELECT SUM(cur_amt IS NULL) FROM tz_silver.s_fin_item", lambda: int((D["s_fin_item"].cur_amt == "").sum())),
            ("V1-24", "재무요약 매출 YTD 합계", "SELECT SUM(CAST(NULLIF(revenue_ytd,'') AS DECIMAL(30,0))) FROM tz_bronze.b_a_financial_summary",
             "SELECT SUM(mtrc_amt) FROM tz_silver.s_fin_mtrc WHERE mtrc_cd='REVENUE' AND prd_type_cd='YTD'",
             lambda: sum(int(x) for x, m, p in zip(D["s_fin_mtrc"].mtrc_amt, D["s_fin_mtrc"].mtrc_cd, D["s_fin_mtrc"].prd_type_cd) if x and m == "REVENUE" and p == "YTD"))]
    for cid, item, bs, ss, pdf in sums:
        bv, sv = scalar(cur, bs), scalar(cur, ss)
        rec(cid, "V1 값 대사", f"{item}: Bronze ↔ Silver", str(Decimal(bv).normalize()), str(Decimal(sv).normalize()),
            str(Decimal(pdf()).normalize()), "0 대체·반올림 없음")

    # ------------------------------------------------------------------ V2 키 무결성
    k = 0
    for t in TABLES.values():
        if t["layer"] not in ("SILVER", "GOLD"):
            continue
        db = "tz_silver" if t["layer"] == "SILVER" else "tz_gold"
        pk = ",".join(t["pk"])
        k += 1
        sv = scalar(cur, f"SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT {pk} FROM {db}.{t['name']}) d) FROM {db}.{t['name']}")
        pv = int(D[t["name"]].duplicated(t["pk"]).sum())
        rec(f"V2-PK{k:02d}", "V2 키 무결성", f"PK 중복 {t['name']}({pk})", 0, sv, pv)
    k = 0
    for t in TABLES.values():
        if t["layer"] not in ("SILVER", "GOLD"):
            continue
        db = "tz_silver" if t["layer"] == "SILVER" else "tz_gold"
        for col, rt, rc in t["fks"]:
            k += 1
            sv = scalar(cur, f"SELECT COUNT(*) FROM {db}.{t['name']} x LEFT JOIN tz_silver.{rt} r ON r.{rc}=x.{col} "
                             f"WHERE x.{col} IS NOT NULL AND r.{rc} IS NULL")
            ch = D[t["name"]][col]
            pv = int(((ch != "") & ~ch.isin(D[rt][rc])).sum())
            rec(f"V2-FK{k:02d}", "V2 키 무결성", f"FK 고아 {t['name']}.{col} → {rt}.{rc}" + (" (Gold 논리FK)" if t["layer"] == "GOLD" else ""), 0, sv, pv)
        for col, rt, rc, note in t["logical_fks"]:
            k += 1
            sv = scalar(cur, f"SELECT COUNT(*) FROM {db}.{t['name']} x LEFT JOIN tz_silver.{rt} r ON r.{rc}=x.{col} WHERE r.{rc} IS NULL")
            pv = int((~D[t["name"]][col].isin(D[rt][rc])).sum())
            expl = scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_fin_rpt WHERE dscl_join_stts_cd='NOT_IN_INPUT_COVERAGE'")
            rec(f"V2-FK{k:02d}", "V2 키 무결성", f"논리FK 미일치 {t['name']}.{col} → {rt}.{rc}", expl, sv, pv,
                "기대값 = A 가 NOT_IN_INPUT_COVERAGE 로 표시한 건수(설명된 미일치). s_dq_issue REFERENCE 로 기록")
    # 매핑
    rec("V2-MAP1", "V2 키 무결성", "기업-종목 매핑 MATCHED 건수(A 20 · B 20)", 20,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_corp_stock_map WHERE map_stts_cd='MATCHED'"),
        int((D["s_corp_stock_map"].map_stts_cd == "MATCHED").sum()))
    rec("V2-MAP2", "V2 키 무결성", "매핑 미연결·다중후보 건수", 0,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_corp_stock_map WHERE map_stts_cd<>'MATCHED'"),
        int((D["s_corp_stock_map"].map_stts_cd != "MATCHED").sum()))
    rec("V2-MAP3", "V2 키 무결성", "종목코드 기준 매핑 결과와 기업마스터 stock_cd 불일치", 0,
        scalar(cur, "SELECT COUNT(*) FROM tz_silver.s_corp_stock_map m JOIN tz_silver.s_corp c ON c.corp_cd=m.corp_cd WHERE c.stock_cd<>m.stock_cd"), None)
    # 출처 추적: Silver 행 → Bronze 원본 행
    lin = [("s_stock_daily_prc", "b_b_stock_daily_price", "x.stock_cd=b.symbol AND x.trd_dt=b.trade_date AND x.src_file_path=b.source_file AND x.src_row_no=CAST(b.source_row AS UNSIGNED)"),
           ("s_invstr_trd_daily", "b_b_investor_trading_daily", "x.stock_cd=b.symbol AND x.trd_dt=b.trade_date AND x.src_json_path=b.json_path AND x.src_row_no=CAST(b.source_row AS UNSIGNED) AND x.src_file_path=b.source_file"),
           ("s_fin_item", "b_a_financial_items", "x.fin_item_id=b.financial_item_id AND x.src_file_path=b._source_file AND x.src_row_no=CAST(b._source_row AS UNSIGNED)"),
           ("s_dscl", "b_a_disclosures", "x.rcept_no=b.rcept_no AND x.src_file_path=b._source_file AND x.src_row_no=CAST(b._source_row AS UNSIGNED)"),
           ("s_fin_rpt", "b_a_financial_summary", "x.fin_rpt_id=b.financial_report_id AND x.src_row_no=b.ldng_row_no")]
    for i, (s, b, on) in enumerate(lin, 1):
        sv = scalar(cur, f"SELECT COUNT(*) FROM tz_silver.{s} x LEFT JOIN tz_bronze.{b} b ON {on} WHERE b.ldng_row_no IS NULL")
        rec(f"V2-LIN{i}", "V2 출처 추적", f"{s} 행 중 Bronze 원본 행(파일·행번호)으로 역추적 불가", 0, sv, None)
    nolin = 0
    for t in TABLES.values():
        if t["layer"] == "SILVER" and "src_row_no" in [c["phys"] for c in t["cols"]] and t["name"] != "s_dq_issue":
            nolin += int(((D[t["name"]].src_file_path == "") | (D[t["name"]].src_row_no == "")).sum())
    rec("V2-LIN6", "V2 출처 추적", "A·B 유래 Silver 행 중 src_file_path/src_row_no 누락", 0, None, nolin)

    # ------------------------------------------------------------------ V3 표준 준수율
    cols = q(cur, "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE FROM information_schema.COLUMNS "
                  "WHERE TABLE_SCHEMA IN ('tz_bronze','tz_silver','tz_gold','tz_meta') ORDER BY 1,2,ORDINAL_POSITION")
    SQLS.append("SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA LIKE 'tz\\_%';")
    term = {(t["name"], c["phys"]): c for t in TABLES.values() for c in t["cols"]}
    detail = []
    for sch, tb, col, ctype, nul in cols:
        if sch == "tz_bronze" and col.startswith("ldng_"):
            continue  # 적재 메타 컬럼은 C 가 부여(표준 준수) — AS-IS 측정에서 제외
        spec = term.get((tb, col))
        name_err = check_name(col, spec["dmn"] if spec else None)
        type_ok = None
        if spec:
            want = DOMAINS[spec["dmn"]][1].lower().replace(" ", "")
            got = ctype.lower().replace(" ", "")
            type_ok = (got == want) or (want == "int" and got.startswith("int")) or (want == "bigint" and got.startswith("bigint"))
            null_ok = (nul == "YES") == spec["null"]
        else:
            null_ok = None
        detail.append(dict(schema=sch, table=tb, column=col, column_type=ctype, in_dictionary="Y" if spec else "N",
                           name_ok="Y" if not name_err else "N", type_ok={None: "", True: "Y", False: "N"}[type_ok],
                           null_ok={None: "", True: "Y", False: "N"}[null_ok], violation="; ".join(name_err)))
    det = pd.DataFrame(detail)
    write_csv(det, OUT / "std_compliance_detail.csv")
    asis = det[det.schema == "tz_bronze"]
    tobe = det[det.schema != "tz_bronze"]
    asis_rate = round((asis.name_ok == "Y").mean() * 100, 2)
    tobe_ok = (tobe.name_ok == "Y") & (tobe.in_dictionary == "Y") & (tobe.type_ok == "Y") & (tobe.null_ok == "Y")
    tobe_rate = round(tobe_ok.mean() * 100, 2)
    rec("V3-01", "V3 표준 준수율", f"AS-IS(Bronze 원본 {len(asis)}개 컬럼) 명명 규칙 준수율 %", None, asis_rate, None,
        "측정값(목표 아님). 인계본 컬럼명 기준", ok=True)
    rec("V3-02", "V3 표준 준수율", f"TO-BE(Silver·Gold·Meta {len(tobe)}개 컬럼) 명명+사전등록+타입+NULL 준수율 %", 100.0, tobe_rate, None)
    rec("V3-03", "V3 표준 준수율", "TO-BE 실제 DB 타입 ≠ 표준 도메인 타입", 0, int((tobe.type_ok == "N").sum()), None)
    rec("V3-04", "V3 표준 준수율", "TO-BE 실제 NULL 허용 ≠ 표준 정의", 0, int((tobe.null_ok == "N").sum()), None)
    rec("V3-05", "V3 표준 준수율", "TO-BE 컬럼 중 표준 사전 미등록", 0, int((tobe.in_dictionary == "N").sum()), None)
    # SQL 만으로 하는 타입 대조(m_std_term ↔ information_schema)
    sv = scalar(cur, "SELECT COUNT(*) FROM tz_meta.m_std_term t LEFT JOIN information_schema.COLUMNS c "
                     "ON c.TABLE_SCHEMA IN ('tz_silver','tz_gold','tz_meta') AND c.TABLE_NAME=t.tbl_nm AND c.COLUMN_NAME=t.col_nm "
                     "WHERE c.COLUMN_NAME IS NULL OR REPLACE(LOWER(c.COLUMN_TYPE),' ','') <> REPLACE(LOWER(t.data_type_nm),' ','')")
    rec("V3-06", "V3 표준 준수율", "SQL: m_std_term(사전) ↔ information_schema 타입 불일치·미구현 컬럼", 0, sv, None)

    # ------------------------------------------------------------------ V4 도메인·코드 규칙
    k = 0
    tot_viol = 0
    for t in TABLES.values():
        if t["layer"] not in ("SILVER", "GOLD"):
            continue
        db = "tz_silver" if t["layer"] == "SILVER" else "tz_gold"
        for c in t["cols"]:
            if c["code"]:
                k += 1
                sv = scalar(cur, f"SELECT COUNT(*) FROM {db}.{t['name']} x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='{c['code']}' "
                                 f"AND c.cd_val=x.{c['phys']} WHERE x.{c['phys']} IS NOT NULL AND c.cd_val IS NULL")
                allowed = set(D["s_cmn_cd"][D["s_cmn_cd"].cd_grp_id == c["code"]].cd_val)
                s_ = D[t["name"]][c["phys"]]
                pv = int(((s_ != "") & ~s_.isin(allowed)).sum())
                tot_viol += sv
                rec(f"V4-CD{k:02d}", "V4 코드 규칙", f"{t['name']}.{c['phys']} ∉ 공통코드 {c['code']}", 0, sv, pv)
    rx = {"CORP_CD": "^[0-9]{8}$", "STOCK_CD": "^[0-9]{6}$", "RCEPT_NO": "^[0-9]{14}$", "YEAR": "^[0-9]{4}$",
          "ISIN_CD": "^[A-Z]{2}[A-Z0-9]{9}[0-9]$", "HASH": "^(sha256:)?[0-9a-f]{64}$"}
    k = 0
    for t in TABLES.values():
        if t["layer"] not in ("SILVER", "GOLD"):
            continue
        db = "tz_silver" if t["layer"] == "SILVER" else "tz_gold"
        for c in t["cols"]:
            if c["dmn"] in rx:
                k += 1
                sv = scalar(cur, f"SELECT COUNT(*) FROM {db}.{t['name']} WHERE {c['phys']} IS NOT NULL AND NOT REGEXP_LIKE({c['phys']}, '{rx[c['dmn']]}', 'c')")
                s_ = D[t["name"]][c["phys"]]
                pv = int(((s_ != "") & ~s_.str.fullmatch(rx[c["dmn"]].strip("^$"))).sum())
                tot_viol += sv
                rec(f"V4-DM{k:02d}", "V4 도메인 규칙", f"{t['name']}.{c['phys']} 형식({c['dmn']}) 위반", 0, sv, pv)
    P, IV = D["s_stock_daily_prc"], D["s_invstr_trd_daily"]
    f = lambda s: s.astype(float)
    biz = [
        ("V4-BZ01", "주가 OHLC 범위(high≥max(open,close,low), low≤min(open,close))",
         "SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE high_prc < GREATEST(open_prc,close_prc,low_prc) OR low_prc > LEAST(open_prc,close_prc)",
         int(((f(P.high_prc) < pd.concat([f(P.open_prc), f(P.close_prc), f(P.low_prc)], axis=1).max(axis=1)) |
              (f(P.low_prc) > pd.concat([f(P.open_prc), f(P.close_prc)], axis=1).min(axis=1))).sum())),
        ("V4-BZ02", "지수 OHLC 범위", "SELECT COUNT(*) FROM tz_silver.s_idx_daily_prc WHERE high_prc < GREATEST(open_prc,close_prc,low_prc) OR low_prc > LEAST(open_prc,close_prc)", None),
        ("V4-BZ03", "가격 ≤ 0", "SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE LEAST(open_prc,high_prc,low_prc,close_prc) <= 0",
         int((pd.concat([f(P.open_prc), f(P.high_prc), f(P.low_prc), f(P.close_prc)], axis=1).min(axis=1) <= 0).sum())),
        ("V4-BZ04", "거래량 < 0", "SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE trd_qty < 0", int((P.trd_qty.astype("int64") < 0).sum())),
        ("V4-BZ05", "매수-매도 ≠ 순매수", "SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily WHERE buy_qty - sell_qty <> net_buy_qty",
         int((IV.buy_qty.astype("int64") - IV.sell_qty.astype("int64") != IV.net_buy_qty.astype("int64")).sum())),
        ("V4-BZ06", "기관 합계 ≠ 기관 세부 7유형 합(순매수)",
         "SELECT COUNT(*) FROM (SELECT t.stock_cd, t.trd_dt, t.net_buy_qty, SUM(d.net_buy_qty) s FROM tz_silver.s_invstr_trd_daily t "
         "JOIN tz_silver.s_invstr_trd_daily d ON d.stock_cd=t.stock_cd AND d.trd_dt=t.trd_dt AND d.upper_invstr_type_cd='INSTITUTION' "
         "WHERE t.invstr_type_cd='INSTITUTION' GROUP BY t.stock_cd, t.trd_dt, t.net_buy_qty HAVING s <> t.net_buy_qty) z", None),
        ("V4-BZ07", "외국인 보유율 ∉ [0,1]", "SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily WHERE hold_rt < 0 OR hold_rt > 1",
         int(((f(D['s_frgn_hold_daily'].hold_rt) < 0) | (f(D['s_frgn_hold_daily'].hold_rt) > 1)).sum())),
        ("V4-BZ08", "외국인 보유수량 > 한도수량", "SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily WHERE hold_qty > limit_qty",
         int((D['s_frgn_hold_daily'].hold_qty.astype('int64') > D['s_frgn_hold_daily'].limit_qty.astype('int64')).sum())),
        ("V4-BZ09", "[시점 누수] Gold 공시일 ≥ 거래일 (미래 재무가 과거 주가에 붙음)",
         "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE dscl_dt IS NOT NULL AND dscl_dt >= trd_dt",
         int(((D['g_ai_stock_daily'].dscl_dt != '') & (D['g_ai_stock_daily'].dscl_dt >= D['g_ai_stock_daily'].trd_dt)).sum())),
        ("V4-BZ10", "Gold 에 붙은 재무 보고서가 시점조인 부적격(pit_join_elig_yn='N')",
         "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily g JOIN tz_silver.s_fin_rpt r ON r.fin_rpt_id=g.fin_rpt_id WHERE r.pit_join_elig_yn<>'Y'", None),
        ("V4-BZ11", "Gold fin_avail_yn 과 fin_rpt_id 존재 불일치",
         "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE (fin_avail_yn='Y') <> (fin_rpt_id IS NOT NULL)",
         int(((D['g_ai_stock_daily'].fin_avail_yn == 'Y') != (D['g_ai_stock_daily'].fin_rpt_id != '')).sum())),
        ("V4-BZ12", "Gold 공시 경과일 ≠ 거래일-공시일",
         "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE dscl_dt IS NOT NULL AND dscl_elps_day_cnt <> DATEDIFF(trd_dt, dscl_dt)", None),
        ("V4-BZ13", "Gold 종가수익률 재계산 불일치(전 관측일 종가 기준, 소수 8자리)",
         "SELECT COUNT(*) FROM (SELECT close_rtn_rt, ROUND(close_prc / LAG(close_prc) OVER (PARTITION BY stock_cd ORDER BY trd_dt) - 1, 8) r FROM tz_gold.g_ai_stock_daily) z "
         "WHERE NOT (close_rtn_rt <=> r)", None),
        ("V4-BZ14", "Gold 순매수가 Silver TOP_LEVEL 값과 불일치",
         "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily g JOIN tz_silver.s_invstr_trd_daily s ON s.stock_cd=g.stock_cd AND s.trd_dt=g.trd_dt "
         "AND s.invstr_type_cd='FOREIGNER' WHERE NOT (s.net_buy_qty <=> g.frgn_net_buy_qty)", None),
        ("V4-BZ15", "Gold 재무값이 Silver 지표값과 불일치(매출 YTD)",
         "SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily g JOIN tz_silver.s_fin_mtrc m ON m.fin_rpt_id=g.fin_rpt_id AND m.mtrc_cd='REVENUE' AND m.prd_type_cd='YTD' "
         "WHERE NOT (m.mtrc_amt <=> g.rev_ytd_amt)", None),
        ("V4-BZ16", "Silver 공시일(s_dscl.rcept_dt) ≠ A 요약 disclosure_date (정규화 근거)",
         "SELECT COUNT(*) FROM tz_bronze.b_a_financial_summary b JOIN tz_silver.s_dscl d ON d.rcept_no=b.rcept_no WHERE b.disclosure_date<>'' AND DATE(b.disclosure_date)<>d.rcept_dt", None),
    ]
    for cid, item, sql, pv in biz:
        sv = scalar(cur, sql)
        tot_viol += sv
        rec(cid, "V4 업무 규칙", item, 0, sv, pv)
    # AS-IS 대비(Bronze 원본 코드값 중 표준 코드값이 아닌 건수)
    asis_checks = [
        ("투자자유형 investor_type", "SELECT COUNT(*) FROM tz_bronze.b_b_investor_trading_daily b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='INVSTR_TYPE' AND c.cd_val=b.investor_type WHERE c.cd_val IS NULL",
         "SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='INVSTR_TYPE' AND c.cd_val=x.invstr_type_cd WHERE c.cd_val IS NULL"),
        ("집계수준 aggregation_level", "SELECT COUNT(*) FROM tz_bronze.b_b_investor_trading_daily b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='AGGR_LVL' AND c.cd_val=b.aggregation_level WHERE c.cd_val IS NULL",
         "SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='AGGR_LVL' AND c.cd_val=x.aggr_lvl_cd WHERE c.cd_val IS NULL"),
        ("원천종류 source_kind", "SELECT COUNT(*) FROM tz_bronze.b_b_stock_daily_price b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=b.source_kind WHERE c.cd_val IS NULL",
         "SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE c.cd_val IS NULL"),
        ("문서상태 status", "SELECT COUNT(*) FROM tz_bronze.b_a_disclosure_documents b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DOC_STTS' AND c.cd_val=b.status WHERE c.cd_val IS NULL",
         "SELECT COUNT(*) FROM tz_silver.s_dscl_doc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DOC_STTS' AND c.cd_val=x.doc_stts_cd WHERE c.cd_val IS NULL"),
        ("여부값(Y/N 아님) 5개 컬럼", "SELECT (SELECT SUM(isCommonShare NOT IN ('Y','N')) FROM tz_bronze.b_b_security_master)+(SELECT SUM(point_in_time_join_eligible NOT IN ('Y','N'))+SUM(same_period_comparison_eligible NOT IN ('Y','N')) FROM tz_bronze.b_a_financial_summary)+(SELECT SUM(has_price NOT IN ('Y','N'))+SUM(has_investor_data NOT IN ('Y','N')) FROM tz_bronze.b_b_price_investor_availability)",
         "SELECT (SELECT SUM(cmn_shr_yn NOT IN ('Y','N')) FROM tz_silver.s_stock)+(SELECT SUM(pit_join_elig_yn NOT IN ('Y','N'))+SUM(same_prd_cmpr_elig_yn NOT IN ('Y','N')) FROM tz_silver.s_fin_rpt)+(SELECT SUM(prc_exist_yn NOT IN ('Y','N'))+SUM(invstr_exist_yn NOT IN ('Y','N')) FROM tz_silver.s_conn_stts)"),
        ("일자 YYYY-MM-DD 아님(rcept_dt·modify_date)", "SELECT (SELECT SUM(NOT REGEXP_LIKE(rcept_dt,'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_bronze.b_a_disclosures)+(SELECT SUM(NOT REGEXP_LIKE(modify_date,'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_bronze.b_a_company_master)",
         "SELECT (SELECT SUM(NOT REGEXP_LIKE(CAST(rcept_dt AS CHAR),'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_silver.s_dscl)+(SELECT SUM(NOT REGEXP_LIKE(CAST(chg_dt AS CHAR),'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_silver.s_corp)"),
    ]
    for i, (item, bsql, ssql) in enumerate(asis_checks, 1):
        bv, sv = int(scalar(cur, bsql) or 0), int(scalar(cur, ssql) or 0)
        rec(f"V4-AB{i:02d}", "V4 AS-IS→TO-BE", f"{item}: 표준 위반 AS-IS {bv:,}건 → TO-BE", 0, sv, None, f"AS-IS(Bronze) {bv}건")

    # ------------------------------------------------------------------ V6 A 스크립트 교차검증
    a_script = adir / "scripts" / "join_daily_for_c.py"
    if a_script.exists():
        with tempfile.TemporaryDirectory() as td:
            g = D["g_ai_stock_daily"]
            g[["stock_cd", "trd_dt"]].rename(columns={"stock_cd": "stock_code", "trd_dt": "trade_date"}).to_csv(
                f"{td}/daily.csv", index=False, encoding="utf-8-sig")
            subprocess.run([sys.executable, "-I", str(a_script), "--daily", f"{td}/daily.csv", "--financial",
                            str(adir / A_FILES["financial_summary"]), "--output", f"{td}/out.csv"], check=True, capture_output=True)
            o = read_csv(__import__("pathlib").Path(f"{td}/out.csv"))
        same = int((o.dart_financial_report_id.values == g.fin_rpt_id.values).sum())
        rec("V6-01", "V6 교차검증", "Gold 시점(PIT) 재무 선택 = A 인계 스크립트(join_daily_for_c.py) 결과 일치 행", len(g), None, same)
        same2 = int(sum((x == y) for x, y in zip(o.dart_operating_profit_ytd, g.op_prft_ytd_amt)))
        rec("V6-02", "V6 교차검증", "Gold 영업이익 YTD = A 스크립트 결과 일치 행", len(g), None, same2)

    # ------------------------------------------------------------------ V5 재실행 일관성
    if a.rerun:
        before = json.loads((O / "output_sha256.json").read_text())
        cnt_before = {r[0]: r[1] for r in q(cur, "SELECT TABLE_NAME, TABLE_ROWS FROM information_schema.TABLES WHERE 0")}
        exact_before = {}
        for t in TABLES.values():
            if t["layer"] in ("SILVER", "GOLD"):
                db = "tz_silver" if t["layer"] == "SILVER" else "tz_gold"
                exact_before[t["name"]] = q(cur, f"SELECT COUNT(*) FROM {db}.{t['name']}")[0][0]
        con.close()
        args = [sys.executable, str(ROOT / "code" / "run_pipeline.py"), "--a-dir", str(adir), "--b-dir", str(bdir)]
        subprocess.run(args, check=True, capture_output=True)
        after = json.loads((O / "output_sha256.json").read_text())
        diff = [k for k in before["files"] if before["files"][k] != after["files"].get(k)]
        rec("V5-01", "V5 재실행 일관성", f"같은 입력 재실행 시 결과 CSV {len(before['files'])}개 SHA-256 변경 파일 수", 0, None, len(diff),
            "변경 파일: " + ", ".join(diff) if diff else "모든 결과 파일 해시 동일")
        la = [sys.executable, str(ROOT / "code" / "load_mysql.py"), "--a-dir", str(adir), "--b-dir", str(bdir), "--user", a.user]
        la += ["--socket", a.socket] if a.socket else ["--host", a.host, "--port", str(a.port)]
        if a.password:
            la += ["--password", a.password]
        subprocess.run(la, check=True, capture_output=True)
        con = connect(a); cur = con.cursor()
        changed = 0
        for t, c0 in exact_before.items():
            db = "tz_silver" if TABLES[t]["layer"] == "SILVER" else "tz_gold"
            if q(cur, f"SELECT COUNT(*) FROM {db}.{t}")[0][0] != c0:
                changed += 1
        rec("V5-02", "V5 재실행 일관성", "MySQL 재적재 후 Silver·Gold 테이블 건수가 달라진 테이블 수(중복 적재 여부)", 0, changed, None)
        runs = q(cur, "SELECT COUNT(DISTINCT run_id) FROM tz_meta.m_exec_log")[0][0]
        rec("V5-03", "V5 재실행 일관성", "실행 기록(m_exec_log) 누적 run 수 ≥ 2 (재실행 이력 보존)", ">=2", runs, None, ok=runs >= 2)

    # ------------------------------------------------------------------ 저장
    res = pd.DataFrame(RES)
    write_csv(res, OUT / "validation_results.csv")
    (OUT / "validation_queries.sql").write_text("-- validate.py 가 실행한 SQL (MySQL 8.0)\n" + "\n\n".join(dict.fromkeys(SQLS)), encoding="utf-8")
    summ = dict(total=len(res), passed=int((res.status == "PASS").sum()), failed=int((res.status == "FAIL").sum()),
                by_category=res.groupby("category").status.value_counts().unstack(fill_value=0).to_dict("index"),
                std_compliance_asis_pct=asis_rate, std_compliance_tobe_pct=tobe_rate,
                domain_code_rule_violations_tobe=int(tot_viol))
    dump_json(summ, OUT / "validation_summary.json")
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    if summ["failed"]:
        print(res[res.status == "FAIL"].to_string())
    con.close()


if __name__ == "__main__":
    main()
