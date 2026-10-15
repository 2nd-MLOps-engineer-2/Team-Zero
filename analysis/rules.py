"""Silver business-rule checks for C05/C06/M07 (read only; no flag or value changes).

SS02 is a pass/fail rule. SF04 and SF06 are findings: they list review targets
for the source documents and never rewrite Silver flags or Gold values.
Amounts are compared as exact integers (KRW).
"""
from __future__ import annotations

import pandas as pd

ORDER = {"11013": 1, "11012": 2, "11014": 3, "11011": 4}
FLOW = ("REVENUE", "OPERATING_PROFIT", "NET_INCOME")
ROUNDING_KRW = 1_000_000  # source amounts published in KRW million can differ by one unit


def _int(v):
    return int(v) if v != "" else None


def institution_detail_identity(s):
    """SS02: INSTITUTION (TOP_LEVEL) net buying = sum of the 7 INST_DETAIL types per key.

    If it holds, adding detail rows to the institution total double-counts, so
    cross-investor sums must use TOP_LEVEL only."""
    inv = s["s_invstr_trd_daily"]
    net = inv.net_buy_qty.astype("int64")
    top = net[inv.invstr_type_cd == "INSTITUTION"].groupby([inv.stock_cd, inv.trd_dt]).sum()
    detail = net[inv.aggr_lvl_cd == "INST_DETAIL"].groupby([inv.stock_cd, inv.trd_dt]).sum()
    equal = int((top == detail.reindex(top.index)).sum())
    return {"name": "SS02.institution_equals_detail_sum", "actual": equal, "expected": len(top),
            "pass": equal == len(top)}


def _flow_amounts(s):
    m = s["s_fin_mtrc"]
    m = m[m.mtrc_cd.isin(FLOW)].pivot(index=["fin_rpt_id", "mtrc_cd"], columns="prd_type_cd", values="mtrc_amt")
    m = m.reset_index().fillna("")
    keys = ["fin_rpt_id", "corp_cd", "bsns_yr", "rpt_cd", "fs_div_cd", "cal_prd_stts_cd"]
    return m.merge(s["s_fin_rpt"][keys], on="fin_rpt_id", how="left", validate="many_to_one")


def period_continuity(s):
    """SF04: YTD(n) - YTD(n-1) = Q3M(n) for half-year/Q3 reports (same corp, year, CFS/OFS)."""
    f = _flow_amounts(s)
    f["order"] = f.rpt_cd.map(ORDER)
    prev = f[["corp_cd", "bsns_yr", "fs_div_cd", "mtrc_cd", "order", "YTD"]].assign(order=lambda d: d.order + 1)
    c = f[f.order.isin([2, 3])].merge(prev.rename(columns={"YTD": "prev_ytd_amt"}),
                                      on=["corp_cd", "bsns_yr", "fs_div_cd", "mtrc_cd", "order"], validate="one_to_one")
    c = c[(c.YTD != "") & (c.prev_ytd_amt != "") & (c.Q3M != "")].copy()
    c["gap_amt"] = [_int(a) - _int(b) - _int(q) for a, b, q in zip(c.YTD, c.prev_ytd_amt, c.Q3M)]
    c["gap_cls_cd"] = ["MATCH" if g == 0 else "UNIT_ROUNDING" if abs(g) <= ROUNDING_KRW else "REVIEW" for g in c.gap_amt]
    detail = c[c.gap_cls_cd != "MATCH"].rename(columns={"YTD": "ytd_amt", "Q3M": "q3m_amt"})[
        ["fin_rpt_id", "corp_cd", "bsns_yr", "rpt_cd", "fs_div_cd", "cal_prd_stts_cd", "mtrc_cd",
         "ytd_amt", "prev_ytd_amt", "q3m_amt", "gap_amt", "gap_cls_cd"]].sort_values(["corp_cd", "bsns_yr", "rpt_cd", "mtrc_cd"])
    by = c.groupby(["cal_prd_stts_cd", "gap_cls_cd"]).size()
    summary = {"name": "SF04.ytd_q3m_continuity", "compared": len(c),
               "by_class": c.gap_cls_cd.value_counts().to_dict(),
               "by_period_status": {f"{a}/{b}": int(n) for (a, b), n in by.items()},
               "review_reports": sorted(detail.loc[detail.gap_cls_cd == "REVIEW", "fin_rpt_id"].unique().tolist()),
               "policy": "finding only; flags and Gold values unchanged; REVIEW goes to the M07 source-document list"}
    return summary, detail


def prior_ytd_restatement(s):
    """SF06: PRIOR_YTD in year Y's report vs YTD in year Y-1's own report (same corp, report code, CFS/OFS)."""
    f = _flow_amounts(s)
    cur = f[["fin_rpt_id", "corp_cd", "bsns_yr", "rpt_cd", "fs_div_cd", "mtrc_cd", "PRIOR_YTD"]]
    prev = f[["fin_rpt_id", "corp_cd", "bsns_yr", "rpt_cd", "fs_div_cd", "mtrc_cd", "YTD"]].assign(
        bsns_yr=lambda d: (d.bsns_yr.astype(int) + 1).astype(str))
    c = cur.merge(prev, on=["corp_cd", "bsns_yr", "rpt_cd", "fs_div_cd", "mtrc_cd"], suffixes=("", "_prior_rpt"),
                  validate="one_to_one")
    c = c[(c.PRIOR_YTD != "") & (c.YTD != "")].copy()
    c["diff_amt"] = [_int(a) - _int(b) for a, b in zip(c.PRIOR_YTD, c.YTD)]
    diff = c[c.diff_amt != 0].rename(columns={"PRIOR_YTD": "prior_ytd_amt", "YTD": "prior_rpt_ytd_amt"})[
        ["fin_rpt_id", "fin_rpt_id_prior_rpt", "corp_cd", "bsns_yr", "rpt_cd", "fs_div_cd", "mtrc_cd",
         "prior_ytd_amt", "prior_rpt_ytd_amt", "diff_amt"]].sort_values(["mtrc_cd", "corp_cd", "bsns_yr", "rpt_cd"])
    summary = {"name": "SF06.prior_ytd_vs_prior_report", "compared": c.groupby("mtrc_cd").size().to_dict(),
               "differs": diff.groupby("mtrc_cd").size().to_dict(),
               "revenue_corps": int(diff.loc[diff.mtrc_cd == "REVENUE", "corp_cd"].nunique()),
               "policy": "finding only; growth rates keep the same-report PRIOR_YTD (restated comparative basis)"}
    return summary, diff


def run_rules(s, out=None):
    """Return the validation.json section; write detail CSVs when out is given. Raises on SS02 failure."""
    identity = institution_detail_identity(s)
    continuity, continuity_detail = period_continuity(s)
    restatement, restatement_detail = prior_ytd_restatement(s)
    if out is not None:
        for name, frame in (("rule_period_continuity.csv", continuity_detail),
                            ("rule_prior_ytd_restatement.csv", restatement_detail)):
            frame.to_csv(out / name, index=False, encoding="utf-8-sig", lineterminator="\n")
    if not identity["pass"]:
        raise ValueError(f"Silver rule failure: {identity}")
    return {"checks": [identity], "findings": [continuity, restatement]}


def report_period_join(financial, period_summary):
    """C08: same-period stock/index/flow comparison comes from the existing g_fin_rpt_mkt_smry.
    It must join 1:1 to g_fin_rpt_analysis on fin_rpt_id; partial coverage stays NULL (full_cvrg_yn=N)."""
    keys = set(financial.fin_rpt_id)
    one_to_one = period_summary.fin_rpt_id.is_unique and set(period_summary.fin_rpt_id) == keys
    partial = period_summary[period_summary.full_cvrg_yn == "N"]
    leaked = int(((partial.prd_rtn_rt != "") | (partial.frgn_net_buy_qty != "") | (partial.inst_net_buy_qty != "")).sum())
    return {"name": "C08.report_period_join", "pass": bool(one_to_one and leaked == 0),
            "rows": len(period_summary), "full_coverage": int((period_summary.full_cvrg_yn == "Y").sum()),
            "partial_coverage_values_present": leaked,
            "usage": "join g_fin_rpt_mkt_smry on fin_rpt_id for report-period return and TOP_LEVEL net buying"}
