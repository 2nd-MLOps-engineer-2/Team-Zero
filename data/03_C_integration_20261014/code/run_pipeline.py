"""C 담당 실행 진입점 — 표준 사전 적용 → Silver 표준 테이블 → C 통합 테이블 → Gold → 품질 이슈 → 실행 기록.

실행:  python code/run_pipeline.py [--a-dir A인계폴더] [--b-dir B인계폴더]
출력:  04_output/silver/*.csv, 04_output/gold/*.csv, 04_output/meta/*.csv, 04_output/output_sha256.json

원칙(팀 공통 규칙)
- 입력(A·B 인계본)은 읽기 전용. 결과는 04_output 에 덮어쓰기(같은 입력 재실행 시 중복 행 없음).
- 식별자(corp_cd·stock_cd·rcept_no)는 문자열, 선행 0 보존.
- 금액은 정수 문자열 그대로(Decimal), 빈값은 NULL. 0 대체·보간 금지.
- 변환 실패·키 충돌은 s_dq_issue 에 사유 기록 후 실패 처리(fail-fast).
- 가격·수급은 내부조인하지 않고 키 합집합으로 연결 상태를 남긴다.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, re, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from common import ROOT, input_dirs, load_inputs, write_csv, input_manifest, input_version, dump_json, A_FILES
from std_dictionary import TABLES, CODES, DOMAINS, PIPELINE_VERSION

OUT = ROOT / "04_output"
KST = "Asia/Seoul"
EXEC_LOG: list[dict] = []
CONV_ERRORS: list[dict] = []


def now():
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")


# ----------------------------------------------------------------------------
# 변환 함수
# ----------------------------------------------------------------------------
def asis_map(group: str) -> dict[str, str]:
    """코드그룹의 AS-IS 값 → 표준 코드값 사전."""
    m = {}
    for val, _nm, _o, asis in CODES[group][1]:
        m[val] = val
        for a in filter(None, asis.split("|")):
            m[a] = val
    return m


def to_code(s: pd.Series, group: str, tbl: str, col: str, allow_null=False) -> pd.Series:
    m = asis_map(group)
    out = s.map(lambda v: m.get(v, None) if v != "" else "")
    bad = s[(out.isna()) | ((out == "") & (not allow_null))]
    for idx, v in bad.items():
        CONV_ERRORS.append(dict(tbl=tbl, col=col, idx=idx, val=v, rsn=f"코드그룹 {group} 미등록 값"))
    return out.fillna("")


def to_yn(s, tbl, col):
    return to_code(s, "YN", tbl, col)


def yyyymmdd(s: pd.Series, tbl, col, allow_null=False) -> pd.Series:
    def f(v):
        if v == "":
            return ""
        if re.fullmatch(r"\d{8}", v):
            try:
                return dt.date(int(v[:4]), int(v[4:6]), int(v[6:])).isoformat()
            except ValueError:
                pass
        return None
    out = s.map(f)
    for idx, v in s[out.isna() | ((out == "") & (not allow_null))].items():
        CONV_ERRORS.append(dict(tbl=tbl, col=col, idx=idx, val=v, rsn="YYYYMMDD 변환 실패"))
    return out.fillna("")


def iso_date(s, tbl, col, allow_null=False):
    def f(v):
        if v == "":
            return ""
        try:
            return dt.date.fromisoformat(v).isoformat()
        except ValueError:
            return None
    out = s.map(f)
    for idx, v in s[out.isna() | ((out == "") & (not allow_null))].items():
        CONV_ERRORS.append(dict(tbl=tbl, col=col, idx=idx, val=v, rsn="DATE 변환 실패"))
    return out.fillna("")


def kst_dttm(s, tbl, col, allow_null=True):
    """'2022-12-01T00:00:00.000+09:00' → '2022-12-01 00:00:00' (KST). 오프셋 없는 값은 실패 처리."""
    def f(v):
        if v == "":
            return ""
        try:
            t = dt.datetime.fromisoformat(v)
        except ValueError:
            return None
        if t.tzinfo is None:
            return None
        return t.astimezone(dt.timezone(dt.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
    out = s.map(f)
    for idx, v in s[out.isna() | ((out == "") & (not allow_null))].items():
        CONV_ERRORS.append(dict(tbl=tbl, col=col, idx=idx, val=v, rsn="시간대 포함 일시 변환 실패"))
    return out.fillna("")


def check_regex(s, rx, tbl, col, allow_null):
    bad = s[~s.str.fullmatch(rx) & ~((s == "") & allow_null)]
    for idx, v in bad.items():
        CONV_ERRORS.append(dict(tbl=tbl, col=col, idx=idx, val=v, rsn=f"형식 위반 {rx}"))
    return s


def ensure_cols(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """표준 정의 순서로 컬럼 정렬 + 정의되지 않은 컬럼 금지 + 도메인 형식 검사."""
    spec = TABLES[table]
    names = [c["phys"] for c in spec["cols"]]
    missing = set(names) - set(df.columns)
    if missing:
        raise RuntimeError(f"{table}: 누락 컬럼 {missing}")
    df = df[names].copy()
    for c in spec["cols"]:
        rx = DOMAINS[c["dmn"]][3]
        if rx == "CODE_GROUP":
            allowed = {v for v, *_ in CODES[c["code"]][1]}
            mx = int(DOMAINS[c["dmn"]][2])
            for idx, v in df[c["phys"]][df[c["phys"]].str.len() > mx].items():
                CONV_ERRORS.append(dict(tbl=table, col=c["phys"], idx=idx, val=v, rsn=f"도메인 길이 {mx} 초과"))
            bad = df[c["phys"]][~df[c["phys"]].isin(allowed) & ~((df[c["phys"]] == "") & c["null"])]
            for idx, v in bad.items():
                CONV_ERRORS.append(dict(tbl=table, col=c["phys"], idx=idx, val=v, rsn=f"코드 {c['code']} 허용값 아님"))
        else:
            check_regex(df[c["phys"]], rx, table, c["phys"], c["null"])
    dup = df.duplicated(spec["pk"], keep=False)
    for idx in df.index[dup][:50]:
        CONV_ERRORS.append(dict(tbl=table, col="+".join(spec["pk"]), idx=idx, val="", rsn="기본키 중복"))
    return df


def log(step, table, layer, n, start, input_ver, run_id):
    EXEC_LOG.append(dict(run_id=run_id, step_nm=step, tbl_nm=table, layer_cd=layer, input_ver=input_ver,
                         rcrd_cnt=n, start_dttm=start, end_dttm=now(), run_stts_cd="SUCCESS",
                         pipln_ver=PIPELINE_VERSION))


def lineage_a(src: pd.DataFrame) -> dict:
    return dict(src_team_cd="A", src_file_path=src["_source_file"], src_row_no=src["_source_row"],
                src_ver=src["_source_version"], pipln_ver=PIPELINE_VERSION)


def lineage_b(src: pd.DataFrame, tbl: str) -> dict:
    return dict(src_team_cd="B", src_kind_cd=to_code(src.source_kind, "SRC_KIND", tbl, "src_kind_cd"),
                src_file_path=src.source_file, src_row_no=src.source_row, bronze_row_no=src.bronze_row,
                src_ver=src.source_version, fetch_dttm=kst_dttm(src.fetched_at, tbl, "fetch_dttm"),
                api_raw_file_path=src.api_raw_file, api_rcrd_path=src.api_record_path, pipln_ver=PIPELINE_VERSION)


# ----------------------------------------------------------------------------
# 공통코드
# ----------------------------------------------------------------------------
def build_codes(metric_defs: pd.DataFrame) -> pd.DataFrame:
    CODES["MTRC"] = ("재무 지표", [(m.upper(), lbl, i + 1, m) for i, (m, lbl) in
                                 enumerate(zip(metric_defs.metric, metric_defs.label_ko))])
    rows = []
    for g, (gnm, items) in CODES.items():
        for val, nm, order, asis in items:
            rows.append(dict(cd_grp_id=g, cd_val=val, cd_nm=nm, cd_desc_txt=gnm, sort_ord_no=str(order),
                             asis_val_txt=asis))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# A → Silver
# ----------------------------------------------------------------------------
PRD_SUFFIX = [("_prior_year_end", "PRIOR_YE"), ("_prior_ytd", "PRIOR_YTD"), ("_prior_3m", "PRIOR_Q3M"),
              ("_ytd", "YTD"), ("_3m", "Q3M"), ("_asof", "ASOF")]


def silver_a(A):
    out = {}
    cm = A["company_master"]
    out["s_corp"] = pd.DataFrame(dict(
        corp_cd=cm.corp_code, corp_nm=cm.corp_name, corp_eng_nm=cm.corp_eng_name, stock_cd=cm.stock_code,
        chg_dt=yyyymmdd(cm.modify_date, "s_corp", "chg_dt"), **lineage_a(cm)))

    d = A["disclosures"]
    out["s_dscl"] = pd.DataFrame(dict(
        rcept_no=d.rcept_no, corp_cd=d.corp_code, corp_nm=d.corp_name,
        corp_cls_cd=to_code(d.corp_cls, "CORP_CLS", "s_dscl", "corp_cls_cd"), stock_cd=d.stock_code,
        rpt_nm=d.report_nm, flr_nm=d.flr_nm, rcept_dt=yyyymmdd(d.rcept_dt, "s_dscl", "rcept_dt"), rmk_txt=d.rm,
        **lineage_a(d)))

    doc = A["disclosure_documents"]
    out["s_dscl_doc"] = pd.DataFrame(dict(
        rcept_no=doc.rcept_no, corp_cd=doc.corp_code,
        doc_stts_cd=to_code(doc.status, "DOC_STTS", "s_dscl_doc", "doc_stts_cd"),
        doc_zip_path=doc.zip_path, doc_hash=doc.sha256, err_msg_txt=doc.error, **lineage_a(doc)))

    s = A["financial_summary"]
    out["s_fin_rpt"] = pd.DataFrame(dict(
        fin_rpt_id=s.financial_report_id, corp_cd=s.corp_code, bsns_yr=s.bsns_year,
        rpt_cd=to_code(s.reprt_code, "RPT", "s_fin_rpt", "rpt_cd"),
        fs_div_cd=to_code(s.fs_div, "FS_DIV", "s_fin_rpt", "fs_div_cd"), rcept_no=s.rcept_no,
        crncy_cd=to_code(s.currency, "CRNCY", "s_fin_rpt", "crncy_cd"), flow_prd_mm_cnt=s.flow_period_months,
        prd_start_dt=iso_date(s.period_start_nominal, "s_fin_rpt", "prd_start_dt"),
        prd_end_dt=iso_date(s.period_end_nominal, "s_fin_rpt", "prd_end_dt"),
        dscl_join_stts_cd=to_code(s.disclosure_join_status, "DSCL_JOIN_STTS", "s_fin_rpt", "dscl_join_stts_cd"),
        cal_prd_stts_cd=to_code(s.calendar_period_status, "CAL_PRD_STTS", "s_fin_rpt", "cal_prd_stts_cd"),
        cf_prd_stts_cd=to_code(s.cf_period_status, "CF_PRD_STTS", "s_fin_rpt", "cf_prd_stts_cd"),
        pit_join_elig_yn=to_yn(s.point_in_time_join_eligible, "s_fin_rpt", "pit_join_elig_yn"),
        same_prd_cmpr_elig_yn=to_yn(s.same_period_comparison_eligible, "s_fin_rpt", "same_prd_cmpr_elig_yn"),
        mtrc_review_cnt=s.metric_review_count, custom_map_cnt=s.custom_mapped_count,
        mtrc_conflict_cnt=s.metric_conflict_count, core_mtrc_miss_txt=s.missing_core_metrics,
        src_team_cd="A", src_file_path=A_FILES["financial_summary"],
        src_row_no=[str(i + 1) for i in range(len(s))], src_ver=s.source_version, pipln_ver=PIPELINE_VERSION))

    md = A["metric_definitions"]
    out["s_fin_mtrc_def"] = pd.DataFrame(dict(
        mtrc_cd=md.metric.str.upper(), mtrc_nm=md.label_ko, stmt_div_txt=md.statement, acnt_id_txt=md.account_ids,
        select_rsn_txt=md.reason_ko, custom_nm_txt=md.custom_names, guard_txt=md.name_guard,
        pipln_ver=PIPELINE_VERSION))

    # 넓은 표(지표 94열) → 세로 표
    metrics = set(md.metric)
    long_rows = []
    for col in s.columns:
        for suf, ptype in PRD_SUFFIX:
            if col.endswith(suf) and col[: -len(suf)] in metrics:
                long_rows.append(pd.DataFrame(dict(
                    fin_rpt_id=s.financial_report_id, mtrc_cd=col[: -len(suf)].upper(), prd_type_cd=ptype,
                    mtrc_amt=s[col], src_col_nm=col, pipln_ver=PIPELINE_VERSION)))
                break
    out["s_fin_mtrc"] = pd.concat(long_rows, ignore_index=True)
    out["_wide_metric_cols"] = len(long_rows)

    it = A["financial_items"]
    T_ = "s_fin_item"
    out["s_fin_item"] = pd.DataFrame(dict(
        fin_item_id=it.financial_item_id, fin_rpt_id=it.financial_report_id, corp_cd=it.corp_code,
        rcept_no=it.rcept_no, bsns_yr=it.bsns_year, rpt_cd=to_code(it.reprt_code, "RPT", T_, "rpt_cd"),
        fs_div_cd=to_code(it.fs_div, "FS_DIV", T_, "fs_div_cd"),
        stmt_div_cd=to_code(it.sj_div, "STMT_DIV", T_, "stmt_div_cd"),
        acnt_id=it.account_id, acnt_nm=it.account_nm, acnt_dtl_nm=it.account_detail,
        cur_prd_nm=it.thstrm_nm, cur_amt=it.thstrm_amount, cur_cum_amt=it.thstrm_add_amount,
        prev_prd_nm=it.frmtrm_nm, prev_amt=it.frmtrm_amount, prev_qtr_prd_nm=it.frmtrm_q_nm,
        prev_qtr_amt=it.frmtrm_q_amount, prev_cum_amt=it.frmtrm_add_amount, bfr_prev_prd_nm=it.bfefrmtrm_nm,
        bfr_prev_amt=it.bfefrmtrm_amount, sort_ord_no=it.ord, crncy_cd=to_code(it.currency, "CRNCY", T_, "crncy_cd"),
        **lineage_a(it)))
    return out


# ----------------------------------------------------------------------------
# B → Silver
# ----------------------------------------------------------------------------
def silver_b(B):
    out = {}
    sm = B["security_master"]
    out["s_stock"] = pd.DataFrame(dict(
        stock_cd=sm.symbol, stock_nm=sm["name"], stock_eng_nm=sm.englishName, isin_cd=sm.isinCode,
        mkt_cd=to_code(sm.market, "MKT", "s_stock", "mkt_cd"),
        sec_type_cd=to_code(sm.securityType, "SEC_TYPE", "s_stock", "sec_type_cd"),
        cmn_shr_yn=to_yn(sm.isCommonShare, "s_stock", "cmn_shr_yn"),
        stock_stts_cd=to_code(sm.status, "STOCK_STTS", "s_stock", "stock_stts_cd"),
        crncy_cd=to_code(sm.currency, "CRNCY", "s_stock", "crncy_cd"),
        list_dt=iso_date(sm.listDate, "s_stock", "list_dt"),
        delist_dt=iso_date(sm.delistDate, "s_stock", "delist_dt", allow_null=True),
        outstd_shr_qty=sm.sharesOutstanding, lvrg_val=sm.leverageFactor, mkt_dtl_txt=sm.koreanMarketDetail,
        **lineage_b(sm, "s_stock")))

    p = B["stock_daily_price"]
    out["s_stock_daily_prc"] = pd.DataFrame(dict(
        stock_cd=p.symbol, trd_dt=iso_date(p.trade_date, "s_stock_daily_prc", "trd_dt"),
        candle_dttm=kst_dttm(p.timestamp, "s_stock_daily_prc", "candle_dttm", allow_null=False),
        open_prc=p.open_price, high_prc=p.high_price, low_prc=p.low_price, close_prc=p.close_price,
        trd_qty=p.volume, crncy_cd=to_code(p.currency, "CRNCY", "s_stock_daily_prc", "crncy_cd"),
        **lineage_b(p, "s_stock_daily_prc")))

    ix = B["market_index_daily"]
    out["s_idx_daily_prc"] = pd.DataFrame(dict(
        idx_cd=to_code(ix.index_code, "IDX", "s_idx_daily_prc", "idx_cd"),
        trd_dt=iso_date(ix.trade_date, "s_idx_daily_prc", "trd_dt"),
        candle_dttm=kst_dttm(ix.timestamp, "s_idx_daily_prc", "candle_dttm", allow_null=False),
        open_prc=ix.open_price, high_prc=ix.high_price, low_prc=ix.low_price, close_prc=ix.close_price,
        trd_qty=ix.volume, **lineage_b(ix, "s_idx_daily_prc")))

    iv = B["investor_trading_daily"]
    T_ = "s_invstr_trd_daily"
    out[T_] = pd.DataFrame(dict(
        stock_cd=iv.symbol, trd_dt=iso_date(iv.trade_date, T_, "trd_dt"),
        invstr_type_cd=to_code(iv.investor_type, "INVSTR_TYPE", T_, "invstr_type_cd"),
        upper_invstr_type_cd=to_code(iv.parent_type, "INVSTR_TYPE", T_, "upper_invstr_type_cd", allow_null=True),
        aggr_lvl_cd=to_code(iv.aggregation_level, "AGGR_LVL", T_, "aggr_lvl_cd"),
        buy_qty=iv.buy_volume, sell_qty=iv.sell_volume, net_buy_qty=iv.net_buy_volume,
        src_col_nm=iv.source_column, src_json_path=iv.json_path, **lineage_b(iv, T_)))

    fh = B["foreign_holding_daily"]
    out["s_frgn_hold_daily"] = pd.DataFrame(dict(
        stock_cd=fh.symbol, trd_dt=iso_date(fh.trade_date, "s_frgn_hold_daily", "trd_dt"),
        hold_qty=fh.holding_quantity, limit_qty=fh.limit_quantity, hold_rt=fh.holding_rate,
        src_col_nm=fh.source_column, src_json_path=fh.json_path, **lineage_b(fh, "s_frgn_hold_daily")))

    cf = B["cfd_daily"]
    out["s_cfd_bal_daily"] = pd.DataFrame(dict(
        stock_cd=cf.symbol, trd_dt=iso_date(cf.trade_date, "s_cfd_bal_daily", "trd_dt"),
        buy_bal_qty=cf.buy_balance_quantity, buy_bal_rt=cf.buy_balance_rate,
        sell_bal_qty=cf.sell_balance_quantity, sell_bal_rt=cf.sell_balance_rate,
        src_col_nm=cf.source_column, src_json_path=cf.json_path, **lineage_b(cf, "s_cfd_bal_daily")))
    return out


# ----------------------------------------------------------------------------
# C: 매핑 · 시점(PIT) 재무 선택 · 연결 상태
# ----------------------------------------------------------------------------
def build_mapping(corp: pd.DataFrame, stock: pd.DataFrame) -> pd.DataFrame:
    rows = []
    by_stock = corp.groupby("stock_cd").corp_cd.apply(list).to_dict()
    stock_nm = dict(zip(stock.stock_cd, stock.stock_nm))
    corp_nm = dict(zip(corp.corp_cd, corp.corp_nm))
    for sc in sorted(set(stock.stock_cd) | set(corp.stock_cd)):
        corps = by_stock.get(sc, [])
        in_b = sc in stock_nm
        if in_b and len(corps) == 1:
            st, mth = "MATCHED", "STOCK_CD_EXACT"
        elif in_b and len(corps) > 1:
            st, mth = "MULTIPLE_CANDIDATES", "STOCK_CD_EXACT"
        else:
            st, mth = "UNMAPPED", "NONE"
        for cc in (corps or [""]):
            cn, sn = corp_nm.get(cc, ""), stock_nm.get(sc, "")
            nm_ok = "Y" if cn and sn and cn == sn else "N"
            if st == "MATCHED" and nm_ok == "N":
                rsn = f"종목코드 완전일치. 명칭 상이(기업 '{cn}' / 종목 '{sn}') — 약칭 차이로 판단, 종목코드 기준 확정"
            elif st == "MATCHED":
                rsn = "종목코드 완전일치, 명칭 일치"
            elif not in_b:
                rsn = "A 기업 마스터에만 존재(B 종목 마스터에 종목코드 없음)"
            elif not corps:
                rsn = "B 종목 마스터에만 존재(A 기업 마스터에 종목코드 없음)"
            else:
                rsn = f"동일 종목코드 후보 {len(corps)}개"
            rows.append(dict(map_id=f"{cc or '-'}|{sc}", corp_cd=cc, stock_cd=sc if in_b else sc,
                             map_stts_cd=st, map_mthd_cd=mth, cand_cnt=str(len(corps)), corp_nm=cn, stock_nm=sn,
                             nm_match_yn=nm_ok, map_rsn_txt=rsn, pipln_ver=PIPELINE_VERSION))
    return pd.DataFrame(rows)


def pit_select(fin_rpt: pd.DataFrame, dscl: pd.DataFrame, corp_map: pd.DataFrame, days: pd.DataFrame) -> pd.DataFrame:
    """A 인계 규칙: disclosure_date < trade_date 인 보고서 중
    (사업연도, 분기순서, CFS 우선, 공시일, 접수번호) 최댓값 1개. 공시일 없는 보고서 제외."""
    qorder = {v: o for v, _n, o, _a in CODES["RPT"][1]}
    r = fin_rpt.merge(dscl[["rcept_no", "rcept_dt"]], on="rcept_no", how="left")
    r = r[r.rcept_dt.notna() & (r.rcept_dt != "")]
    m = corp_map[corp_map.map_stts_cd == "MATCHED"][["corp_cd", "stock_cd"]]
    r = r.merge(m, on="corp_cd", how="inner")
    r["sort_key"] = list(zip(r.bsns_yr.astype(int), r.rpt_cd.map(qorder), r.fs_div_cd == "CFS", r.rcept_dt, r.rcept_no))
    res = []
    for sc, g in days.groupby("stock_cd", sort=True):
        reps = r[r.stock_cd == sc].sort_values("rcept_dt")
        rep_list = list(zip(reps.rcept_dt, reps.sort_key, reps.fin_rpt_id))
        i, best = 0, None
        for d in sorted(g.trd_dt):
            while i < len(rep_list) and rep_list[i][0] < d:      # 공시 당일 제외(<)
                if best is None or rep_list[i][1] > best[1]:
                    best = rep_list[i]
                i += 1
            res.append((sc, d, best[2] if best else "", best[0] if best else ""))
    return pd.DataFrame(res, columns=["stock_cd", "trd_dt", "fin_rpt_id", "dscl_dt"])


def build_conn(S, corp_map, pit):
    price = S["s_stock_daily_prc"][["stock_cd", "trd_dt"]].assign(p=1)
    inv = S["s_invstr_trd_daily"][["stock_cd", "trd_dt"]].drop_duplicates().assign(i=1)
    fh = S["s_frgn_hold_daily"][["stock_cd", "trd_dt"]].assign(f=1)
    cfd = S["s_cfd_bal_daily"][["stock_cd", "trd_dt"]].assign(c=1)
    k = price.merge(inv, on=["stock_cd", "trd_dt"], how="outer")
    k = k.merge(fh, on=["stock_cd", "trd_dt"], how="left").merge(cfd, on=["stock_cd", "trd_dt"], how="left")
    k = k.merge(pit[["stock_cd", "trd_dt", "fin_rpt_id"]], on=["stock_cd", "trd_dt"], how="left")
    mm = corp_map[corp_map.stock_cd != ""].drop_duplicates("stock_cd")[["stock_cd", "corp_cd", "map_stts_cd"]]
    k = k.merge(mm, on="stock_cd", how="left")
    yn = lambda s: s.notna().map({True: "Y", False: "N"})
    k["prc_exist_yn"], k["invstr_exist_yn"] = yn(k.p), yn(k.i)
    k["frgn_hold_exist_yn"], k["cfd_exist_yn"] = yn(k.f), yn(k.c)
    k["fin_avail_yn"] = (k.fin_rpt_id.fillna("") != "").map({True: "Y", False: "N"})
    k["conn_stts_cd"] = [("BOTH" if a == "Y" and b == "Y" else "PRICE_ONLY" if a == "Y" else "INVESTOR_ONLY")
                         for a, b in zip(k.prc_exist_yn, k.invstr_exist_yn)]
    return k


# ----------------------------------------------------------------------------
# Gold
# ----------------------------------------------------------------------------
Q8 = Decimal("0.00000001")


def ret(cur: str, prev: str) -> str:
    if not cur or not prev or Decimal(prev) == 0:
        return ""
    return format((Decimal(cur) / Decimal(prev) - 1).quantize(Q8, rounding=ROUND_HALF_UP), "f")


def build_gold(S, corp_map, pit, conn):
    price = S["s_stock_daily_prc"].sort_values(["stock_cd", "trd_dt"]).reset_index(drop=True)
    price["prev_close"] = price.groupby("stock_cd").close_prc.shift(1).fillna("")
    price["close_rtn_rt"] = [ret(c, p) for c, p in zip(price.close_prc, price.prev_close)]
    stock = S["s_stock"][["stock_cd", "mkt_cd"]]
    idx = S["s_idx_daily_prc"].sort_values(["idx_cd", "trd_dt"]).reset_index(drop=True)
    idx["prev"] = idx.groupby("idx_cd").close_prc.shift(1).fillna("")
    idx["idx_rtn_rt"] = [ret(c, p) for c, p in zip(idx.close_prc, idx.prev)]
    idx = idx.rename(columns={"idx_cd": "mkt_cd", "close_prc": "idx_close_prc"})[["mkt_cd", "trd_dt", "idx_close_prc", "idx_rtn_rt"]]

    inv = S["s_invstr_trd_daily"]
    top = inv[inv.aggr_lvl_cd == "TOP_LEVEL"].pivot(index=["stock_cd", "trd_dt"], columns="invstr_type_cd", values="net_buy_qty")
    top = top.rename(columns={"INDIVIDUAL": "indv_net_buy_qty", "FOREIGNER": "frgn_net_buy_qty",
                              "INSTITUTION": "inst_net_buy_qty", "OTHER_CORP": "other_corp_net_buy_qty"}).reset_index()
    top.columns.name = None
    fh = S["s_frgn_hold_daily"][["stock_cd", "trd_dt", "hold_rt"]].rename(columns={"hold_rt": "frgn_hold_rt"})
    cfd = S["s_cfd_bal_daily"][["stock_cd", "trd_dt", "buy_bal_rt"]].rename(columns={"buy_bal_rt": "cfd_buy_bal_rt"})

    mt = S["s_fin_mtrc"]
    want = {("REVENUE", "YTD"): "rev_ytd_amt", ("OPERATING_PROFIT", "YTD"): "op_prft_ytd_amt",
            ("NET_INCOME", "YTD"): "net_incm_ytd_amt", ("OPERATING_CASH_FLOW", "YTD"): "op_cf_ytd_amt",
            ("TOTAL_ASSETS", "ASOF"): "tot_asst_amt", ("TOTAL_LIABILITIES", "ASOF"): "tot_liab_amt",
            ("TOTAL_EQUITY", "ASOF"): "tot_eqty_amt"}
    sel = mt[[(a, b) in want for a, b in zip(mt.mtrc_cd, mt.prd_type_cd)]].copy()
    sel["col"] = [want[(a, b)] for a, b in zip(sel.mtrc_cd, sel.prd_type_cd)]
    fin_wide = sel.pivot(index="fin_rpt_id", columns="col", values="mtrc_amt").reset_index()
    fin_wide.columns.name = None
    fr = S["s_fin_rpt"][["fin_rpt_id", "bsns_yr", "rpt_cd", "fs_div_cd"]].rename(
        columns={"bsns_yr": "fin_bsns_yr", "rpt_cd": "fin_rpt_cd", "fs_div_cd": "fin_fs_div_cd"})

    g = price[["stock_cd", "trd_dt", "open_prc", "high_prc", "low_prc", "close_prc", "trd_qty", "close_rtn_rt"]]
    g = g.merge(stock, on="stock_cd", how="left").merge(idx, on=["mkt_cd", "trd_dt"], how="left")
    g = g.merge(top, on=["stock_cd", "trd_dt"], how="left").merge(fh, on=["stock_cd", "trd_dt"], how="left")
    g = g.merge(cfd, on=["stock_cd", "trd_dt"], how="left")
    g = g.merge(conn[["stock_cd", "trd_dt", "corp_cd", "invstr_exist_yn", "fin_avail_yn"]], on=["stock_cd", "trd_dt"], how="left")
    g = g.merge(pit[["stock_cd", "trd_dt", "fin_rpt_id", "dscl_dt"]], on=["stock_cd", "trd_dt"], how="left")
    g = g.merge(fr, on="fin_rpt_id", how="left").merge(fin_wide, on="fin_rpt_id", how="left")
    g = g.fillna("")
    g["dscl_elps_day_cnt"] = [str((dt.date.fromisoformat(t) - dt.date.fromisoformat(d)).days) if d else ""
                              for t, d in zip(g.trd_dt, g.dscl_dt)]
    g["pipln_ver"] = PIPELINE_VERSION
    assert len(g) == len(price), "Gold 행 수가 가격 행 수와 다름(조인 팽창)"

    # 보고기간 요약(A 인계 '방법 B')
    fr_all = S["s_fin_rpt"].merge(corp_map[corp_map.map_stts_cd == "MATCHED"][["corp_cd", "stock_cd"]], on="corp_cd", how="left")
    topq = inv[(inv.aggr_lvl_cd == "TOP_LEVEL")][["stock_cd", "trd_dt", "invstr_type_cd", "net_buy_qty"]]
    rng = price.groupby("stock_cd").trd_dt.agg(["min", "max"])
    rows = []
    for r in fr_all.itertuples():
        pp = price[(price.stock_cd == r.stock_cd) & (price.trd_dt >= r.prd_start_dt) & (price.trd_dt <= r.prd_end_dt)]
        qq = topq[(topq.stock_cd == r.stock_cd) & (topq.trd_dt >= r.prd_start_dt) & (topq.trd_dt <= r.prd_end_dt)]
        sums = {}
        for code, col in (("FOREIGNER", "frgn_net_buy_qty"), ("INSTITUTION", "inst_net_buy_qty"), ("INDIVIDUAL", "indv_net_buy_qty")):
            v = qq[qq.invstr_type_cd == code].net_buy_qty
            sums[col] = str(sum(int(x) for x in v)) if len(v) else ""
        mn, mx = rng.loc[r.stock_cd] if r.stock_cd in rng.index else ("9999", "0000")
        full = mn <= r.prd_start_dt and mx >= r.prd_end_dt
        first = pp.close_prc.iloc[0] if len(pp) else ""
        last = pp.close_prc.iloc[-1] if len(pp) else ""
        if not full:   # 기간 일부만 관측되면 기간 수익률·순매수 합은 만들지 않는다(부분 기간 값의 오해 방지)
            sums = {k: "" for k in sums}
        rows.append(dict(fin_rpt_id=r.fin_rpt_id, corp_cd=r.corp_cd, stock_cd=r.stock_cd, bsns_yr=r.bsns_yr,
                         rpt_cd=r.rpt_cd, fs_div_cd=r.fs_div_cd, prd_start_dt=r.prd_start_dt, prd_end_dt=r.prd_end_dt,
                         same_prd_cmpr_elig_yn=r.same_prd_cmpr_elig_yn, trd_day_cnt=str(len(pp)),
                         full_cvrg_yn="Y" if full else "N",
                         first_close_prc=first, last_close_prc=last, prd_rtn_rt=ret(last, first) if (full and len(pp) > 1) else "",
                         **sums, pipln_ver=PIPELINE_VERSION))
    smry = pd.DataFrame(rows).merge(fin_wide[["fin_rpt_id", "rev_ytd_amt", "op_prft_ytd_amt", "op_cf_ytd_amt"]],
                                    on="fin_rpt_id", how="left").fillna("")
    return g, smry


# ----------------------------------------------------------------------------
# 품질 이슈 통합
# ----------------------------------------------------------------------------
def build_issues(A, B, S, corp_map, conn):
    rows = []

    def add(stage, team, tbl, col, key, file, row, itype, sev, rsn, resolve):
        rows.append(dict(detect_stage_cd=stage, src_team_cd=team, tbl_nm=tbl, col_nm=col, rcrd_key_txt=key,
                         src_file_path=file, src_row_no=row, issue_type_cd=itype, sev_cd=sev, issue_rsn_txt=rsn[:2000],
                         resolve_stts_cd=resolve))

    # A 자체 검증 결과
    tmap = {"UNVERIFIED_NO_DOCUMENT": ("PERIOD", "RETAINED"), "DISCLOSURE_DATE_MISSING": ("COVERAGE", "EXCLUDED_FROM_PIT"),
            "NO_UNAMBIGUOUS_ACCOUNT": ("MAPPING", "RETAINED"), "CONFLICT": ("MAPPING", "RETAINED"),
            "SOURCE_CURRENT_VALUE_EMPTY": ("MISSING_VALUE", "RETAINED")}
    smap = {"REVIEW": "WARN", "INFO": "INFO"}
    for r in A["review_issues"].itertuples():
        it, rs = tmap.get(r.issue, ("REVIEW", "OPEN"))
        add("A_SELF", "A", "s_fin_mtrc" if r.metric else "s_fin_rpt", r.metric.upper() or None, r.financial_report_id,
            A_FILES["review_issues"], None, it, smap.get(r.severity, "WARN"), f"{r.issue}: {r.detail}", rs)
    # B 자체 검증 결과
    for r in B["data_quality_issues"].itertuples():
        add("B_SELF", "B", r.table, r.column, None, r.source_file, r.source_row, "REVIEW", "WARN",
            f"{r.issue_code}: {r.reason}", "OPEN")
    for r in B["bronze_unresolved_issues"].itertuples():
        add("B_SELF", "B", "s_frgn_hold_daily", r.column_or_group, f"{r.symbol}|{r.date}", r.source_file,
            r.source_data_row_1based, "MISSING_VALUE", "WARN", f"{r.issue_code}: {r.reason}", "QUARANTINED")
    for r in B["pending_recovery_review"].itertuples():
        add("B_SELF", "B", "s_invstr_trd_daily", r.affected_columns, f"{r.symbol}|{r.trade_date}", r.source_file,
            r.source_row, "REVIEW", "WARN",
            f"{r.review_status}: {r.review_notes} — API 재조회값의 updatedAt 이 기존 스냅샷과 달라 자동 병합 제외", "OPEN")

    # C 통합 검증
    for r in corp_map.itertuples():
        if r.map_stts_cd != "MATCHED":
            add("C_INTEGRATION", "C", "s_corp_stock_map", "map_stts_cd", r.map_id, None, None, "MAPPING", "WARN", r.map_rsn_txt, "OPEN")
        elif r.nm_match_yn == "N":
            add("C_INTEGRATION", "C", "s_corp_stock_map", "corp_nm", r.map_id, None, None, "NAME_MISMATCH", "INFO",
                r.map_rsn_txt, "EXPLAINED")
    fr, ds = S["s_fin_rpt"], S["s_dscl"]
    for r in fr[~fr.rcept_no.isin(ds.rcept_no)].itertuples():
        add("C_INTEGRATION", "C", "s_fin_rpt", "rcept_no", r.fin_rpt_id, r.src_file_path, r.src_row_no, "REFERENCE", "INFO",
            f"접수번호 {r.rcept_no} 가 공시목록(s_dscl)에 없음 — 공시목록 수집 범위 밖. 재무행 보존, 시점 조인 제외", "EXCLUDED_FROM_PIT")
    for r in conn[conn.conn_stts_cd != "BOTH"].itertuples():
        add("C_INTEGRATION", "C", "s_conn_stts", "conn_stts_cd", f"{r.stock_cd}|{r.trd_dt}", None, None, "COVERAGE", "WARN",
            f"{r.conn_stts_cd}: {r.miss_rsn_txt}", "RETAINED")
    c0 = S["s_cfd_bal_daily"].trd_dt.min()
    nocfd = conn[(conn.prc_exist_yn == "Y") & (conn.cfd_exist_yn == "N")]
    for sc, g in nocfd.groupby("stock_cd"):
        add("C_INTEGRATION", "C", "s_cfd_bal_daily", None, f"{sc}|{g.trd_dt.min()}~{g.trd_dt.max()}", None, None, "COVERAGE",
            "INFO", f"CFD 잔고 미제공 {len(g)}거래일 (원천 CFD 제공 시작 {c0}). NULL 유지, 0 대체 금지", "EXPLAINED")
    nofin = conn[(conn.prc_exist_yn == "Y") & (conn.fin_avail_yn == "N")]
    for sc, g in nofin.groupby("stock_cd"):
        add("C_INTEGRATION", "C", "g_ai_stock_daily", "fin_rpt_id", f"{sc}|{g.trd_dt.min()}~{g.trd_dt.max()}", None, None,
            "COVERAGE", "INFO", f"해당 거래일 이전에 공개된(공시일<거래일) 재무 보고서 없음: {len(g)}거래일", "EXPLAINED")
    it = S["s_fin_item"]
    emp = it[it.cur_amt == ""]
    for (sj, fs), g in emp.groupby(["stmt_div_cd", "fs_div_cd"]):
        add("C_INTEGRATION", "C", "s_fin_item", "cur_amt", f"stmt={sj}|fs={fs}", None, None, "MISSING_VALUE", "WARN",
            f"당기금액 빈값 {len(g)}행 — 원천 허용 결측 여부 A 확인 대상(PDF A 주의사항). NULL 유지", "OPEN")
    # 변환 오류(있으면 ERROR)
    for e in CONV_ERRORS:
        add("C_INTEGRATION", "C", e["tbl"], e["col"], str(e["idx"]), None, None, "FORMAT", "ERROR", f"{e['rsn']}: '{e['val']}'", "OPEN")

    df = pd.DataFrame(rows).fillna("")
    df["src_row_no"] = df.src_row_no.astype(str).replace({"None": ""})
    key = (df.detect_stage_cd + "|" + df.tbl_nm + "|" + df.col_nm.astype(str) + "|" + df.rcrd_key_txt.astype(str) + "|"
           + df.issue_type_cd + "|" + df.issue_rsn_txt)
    seq = key.groupby(key).cumcount().astype(str)
    df.insert(0, "issue_id", ["DQ-" + hashlib.sha1((k + "#" + s).encode()).hexdigest()[:16] for k, s in zip(key, seq)])
    df["pipln_ver"] = PIPELINE_VERSION
    return df


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a-dir"); ap.add_argument("--b-dir")
    args = ap.parse_args()
    t0 = now()
    adir, bdir = input_dirs(args.a_dir, args.b_dir)
    man = input_manifest(adir, bdir)
    iver = input_version(man)
    run_id = "RUN-" + dt.datetime.now().strftime("%Y%m%d%H%M%S") + "-" + iver[-8:]
    A, B = load_inputs(adir, bdir)
    log("load_inputs", "(A·B 인계본 " + str(len(man)) + "개 파일)", "BRONZE", int(sum(len(v) for v in A.values()) + sum(len(v) for v in B.values())), t0, iver, run_id)

    S: dict[str, pd.DataFrame] = {}
    t = now(); S["s_cmn_cd"] = build_codes(A["metric_definitions"]); log("build_codes", "s_cmn_cd", "SILVER", len(S["s_cmn_cd"]), t, iver, run_id)
    t = now(); sa = silver_a(A); wide_cols = sa.pop("_wide_metric_cols"); S |= sa
    t2 = now(); S |= silver_b(B)
    corp_map = build_mapping(S["s_corp"], S["s_stock"])
    S["s_corp_stock_map"] = corp_map
    days = pd.concat([S["s_stock_daily_prc"][["stock_cd", "trd_dt"]],
                      S["s_invstr_trd_daily"][["stock_cd", "trd_dt"]]]).drop_duplicates()
    pit = pit_select(S["s_fin_rpt"], S["s_dscl"], corp_map, days)
    conn = build_conn(S, corp_map, pit)
    # 부재 사유: B 검토 대기 키는 사유 코드 지정
    pend = set(zip(B["pending_recovery_review"].symbol, B["pending_recovery_review"].trade_date))
    def reason(r):
        if r.conn_stts_cd == "BOTH":
            return "", ""
        if r.conn_stts_cd == "PRICE_ONLY":
            if (r.stock_cd, r.trd_dt) in pend:
                return "INVESTOR_PENDING_REVIEW", "수급 API 재조회값 updatedAt 불일치로 B 검토 대기(pending_recovery_review.csv). 가격 행 유지"
            return "INVESTOR_NOT_SUPPLIED", "수급 원천 행 없음. 가격 행 유지"
        return "PRICE_NOT_SUPPLIED", "가격 원천 행 없음. 수급 행 유지"
    rr = [reason(r) for r in conn.itertuples()]
    conn["miss_rsn_cd"] = [a for a, _ in rr]; conn["miss_rsn_txt"] = [b for _, b in rr]
    conn["pipln_ver"] = PIPELINE_VERSION
    conn["map_stts_cd"] = conn.map_stts_cd.fillna("UNMAPPED")
    S["s_conn_stts"] = conn.fillna("")
    g_daily, g_smry = build_gold(S, corp_map, pit, S["s_conn_stts"])
    S["s_dq_issue"] = build_issues(A, B, S, corp_map, S["s_conn_stts"])
    G = {"g_ai_stock_daily": g_daily, "g_fin_rpt_mkt_smry": g_smry}

    # 표준 컬럼 정렬 + 도메인/코드/PK 검사
    final = {}
    for name, df in list(S.items()) + list(G.items()):
        final[name] = ensure_cols(df.reset_index(drop=True), name)
    if CONV_ERRORS:   # 검사 중 새로 생긴 오류도 이슈에 반영 후 실패
        final["s_dq_issue"] = ensure_cols(build_issues(A, B, S, corp_map, S["s_conn_stts"]), "s_dq_issue")
        write_csv(final["s_dq_issue"], OUT / "silver" / "s_dq_issue.csv")
        print("변환/도메인 오류", len(CONV_ERRORS), "건 — s_dq_issue.csv 확인", file=sys.stderr)
        for e in CONV_ERRORS[:20]:
            print(e, file=sys.stderr)
        sys.exit(2)

    hashes = {}
    for name, df in final.items():
        layer = TABLES[name]["layer"]
        sub = {"SILVER": "silver", "GOLD": "gold"}[layer]
        t = now()
        p = OUT / sub / f"{name}.csv"
        write_csv(df, p)
        hashes[f"{sub}/{name}.csv"] = __import__("common").sha256_file(p)
        log("write_" + sub, name, layer, len(df), t, iver, run_id)
    write_csv(man, OUT / "meta" / "input_manifest.csv")
    # 실행 기록은 누적(append) — 결과 테이블은 덮어쓰기라 재실행해도 중복 행 없음
    lp = OUT / "meta" / "m_exec_log.csv"
    prev = pd.read_csv(lp, dtype=str, keep_default_na=False, encoding="utf-8-sig") if lp.exists() else None
    cur = pd.DataFrame(EXEC_LOG)
    write_csv(pd.concat([prev, cur]) if prev is not None else cur, lp)
    dump_json(dict(pipeline_version=PIPELINE_VERSION, input_version=iver, files=hashes,
                   counts={k: len(v) for k, v in final.items()}, wide_metric_columns=wide_cols), OUT / "output_sha256.json")
    print(run_id, iver)
    for k, v in final.items():
        print(f"  {k:22s} {len(v):>8,}")


if __name__ == "__main__":
    main()
