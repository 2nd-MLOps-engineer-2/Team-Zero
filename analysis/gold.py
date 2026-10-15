"""Pandas orchestration; exact Decimal money/ratios; no DB/network writes.

PIT selection policy reused from the supplied c-integration-1.0.0
code/run_pipeline.py:pit_select, independently implemented without importing
the archived generator (which expects unavailable A/B inputs).
"""
from __future__ import annotations

from bisect import bisect_left
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd

VERSION = "c-gold-0.1.0"
Q8 = Decimal("0.00000001")
ORDER = {"11013": 1, "11012": 2, "11014": 3, "11011": 4}
CORE = {"REVENUE": "rev", "OPERATING_PROFIT": "op_prft", "NET_INCOME": "net_incm",
        "OPERATING_CASH_FLOW": "op_cf", "TOTAL_ASSETS": "tot_asst",
        "TOTAL_LIABILITIES": "tot_liab", "TOTAL_EQUITY": "tot_eqty"}


def dec(value):
    return Decimal(str(value)) if value is not None and str(value) != "" else None


def number(value):
    return "" if value is None else format(value, "f")


def ratio(numerator, denominator, change=False):
    n, d = dec(numerator), dec(denominator)
    if n is None or d is None:
        return "", "NO_DATA"
    if d == 0:
        return "", "DENOM_ZERO"
    if d < 0:
        return "", "NEG_BASE"
    return number((n / d - int(change)).quantize(Q8, rounding=ROUND_HALF_UP)), "OK"


def difference(current, previous):
    a, b = dec(current), dec(previous)
    return "" if a is None or b is None else number(a - b)


def transition(current, prior):
    a, b = dec(current), dec(prior)
    if a is None or b is None:
        return "NO_DATA"
    if b < 0 and a > 0:
        return "LOSS_TO_PROFIT"
    if b > 0 and a < 0:
        return "PROFIT_TO_LOSS"
    return "ZERO_BOUNDARY" if a == 0 or b == 0 else "PROFIT_CONTINUES" if a > 0 else "LOSS_CONTINUES"


def co_move(growth, excess):
    a, b = dec(growth), dec(excess)
    if a is None or b is None:
        return "UNAVAILABLE"
    if a == 0 or b == 0:
        return "NEUTRAL"
    return {(True, True): "IMPROVE_STRONG", (True, False): "IMPROVE_WEAK",
            (False, True): "SLOW_STRONG", (False, False): "SLOW_WEAK"}[a > 0, b > 0]


def read_csv(path):
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)


def load_silver(package):
    return {p.stem: read_csv(p) for p in sorted((package / "04_output/silver").glob("*.csv"))}


def choose_report(reports, day):
    eligible = [r for r in reports if r["pit_join_elig_yn"] == "Y" and r["dscl_dt"] and r["dscl_dt"] < day]
    return max(eligible, key=lambda r: (int(r["bsns_yr"]), ORDER[r["rpt_cd"]],
               r["fs_div_cd"] == "CFS", r["dscl_dt"], r["rcept_no"])) if eligible else None


def build_financial(s):
    reports = s["s_fin_rpt"].copy()
    mapping = s["s_corp_stock_map"].query("map_stts_cd == 'MATCHED'")[["corp_cd", "stock_cd"]]
    reports = reports.merge(mapping, on="corp_cd", how="left", validate="many_to_one")
    reports = reports.merge(s["s_dscl"][["rcept_no", "rcept_dt"]].rename(columns={"rcept_dt": "dscl_dt"}),
                            on="rcept_no", how="left", validate="many_to_one").fillna("")
    metrics = s["s_fin_mtrc"].pivot(index="fin_rpt_id", columns=["mtrc_cd", "prd_type_cd"], values="mtrc_amt").fillna("")
    result = []
    for r in reports.to_dict("records"):
        m = metrics.loc[r["fin_rpt_id"]]
        for code, prefix in CORE.items():
            periods = ("ASOF",) if code.startswith("TOTAL_") else ("YTD", "PRIOR_YTD")
            for period in periods:
                r[f"{prefix}_{period.lower()}_amt"] = m.get((code, period), "")
        for name, num, den, change, comparable in [
            ("rev_yoy_rt", "rev_ytd_amt", "rev_prior_ytd_amt", True, True),
            ("op_margin_rt", "op_prft_ytd_amt", "rev_ytd_amt", False, False),
            ("debt_equity_rt", "tot_liab_asof_amt", "tot_eqty_asof_amt", False, False),
            ("op_cf_sales_rt", "op_cf_ytd_amt", "rev_ytd_amt", False, False),
            ("op_cf_yoy_rt", "op_cf_ytd_amt", "op_cf_prior_ytd_amt", True, True),
        ]:
            value, status = ratio(r[num], r[den], change)
            if r["cal_prd_stts_cd"] != "VERIFIED_XML" or (comparable and r["same_prd_cmpr_elig_yn"] != "Y"):
                value, status = "", "PRD_UNVERIFIED"
            if name.startswith("op_cf") and r["cf_prd_stts_cd"] != "VERIFIED_XML_YTD":
                value, status = "", "PRD_UNVERIFIED"
            r[name], r[name + "_stts_cd"] = value, status
        comparable = r["same_prd_cmpr_elig_yn"] == "Y"
        r["op_prft_delta_amt"] = difference(r["op_prft_ytd_amt"], r["op_prft_prior_ytd_amt"]) if comparable else ""
        r["op_prft_delta_stts_cd"] = "OK" if r["op_prft_delta_amt"] != "" else "PRD_UNVERIFIED" if not comparable else "NO_DATA"
        r["op_prft_transition_cd"] = transition(r["op_prft_ytd_amt"], r["op_prft_prior_ytd_amt"]) if comparable else "PRD_UNVERIFIED"
        r["op_cf_delta_amt"] = difference(r["op_cf_ytd_amt"], r["op_cf_prior_ytd_amt"]) if comparable and r["cf_prd_stts_cd"] == "VERIFIED_XML_YTD" else ""
        r["op_cf_delta_stts_cd"] = "OK" if r["op_cf_delta_amt"] != "" else "PRD_UNVERIFIED" if not comparable or r["cf_prd_stts_cd"] != "VERIFIED_XML_YTD" else "NO_DATA"
        # The known conflict concerns LONG_TERM_BORROWINGS_REPORTED, not CORE.
        r["review_required_yn"] = "Y" if int(r["mtrc_conflict_cnt"]) or r["core_mtrc_miss_txt"] else "N"
        r["calc_ver"] = VERSION
        result.append(r)
    return pd.DataFrame(result).sort_values("fin_rpt_id").reset_index(drop=True)


def build_daily(s, baseline, financial):
    g = baseline.sort_values(["stock_cd", "trd_dt"]).copy()
    reports = {k: v.to_dict("records") for k, v in financial.groupby("stock_cd")}
    selected, dates = [], []
    # At this data size (~279k comparisons) the explicit PIT rule is auditable.
    for r in g.to_dict("records"):
        chosen = choose_report(reports.get(r["stock_cd"], []), r["trd_dt"])
        selected.append(chosen["fin_rpt_id"] if chosen else "")
        dates.append(chosen["dscl_dt"] if chosen else "")
    if selected != g.fin_rpt_id.tolist() or dates != g.dscl_dt.tolist():
        raise ValueError("Independent PIT selection disagrees with supplied daily Gold")
    fincols = ["fin_rpt_id", "rev_yoy_rt", "rev_yoy_rt_stts_cd", "op_margin_rt", "op_cf_delta_amt",
               "op_cf_sales_rt", "op_prft_transition_cd", "review_required_yn", "cal_prd_stts_cd",
               "cf_prd_stts_cd", "same_prd_cmpr_elig_yn"]
    g = g.merge(financial[fincols], on="fin_rpt_id", how="left", validate="many_to_one").fillna("")
    output = []
    for stock, group in g.groupby("stock_cd", sort=True):
        rows = group.to_dict("records")
        trading_dates = [r["trd_dt"] for r in rows]
        for i, r in enumerate(rows):
            for n in (1, 5, 20):
                previous = rows[i-n] if i >= n else None
                value, status = ratio(r["close_prc"], previous["close_prc"], True) if previous else ("", "WINDOW_SHORT")
                idx, istatus = ratio(r["idx_close_prc"], previous["idx_close_prc"], True) if previous else ("", "WINDOW_SHORT")
                r[f"rtn_{n}d_rt"], r[f"rtn_{n}d_stts_cd"] = value, status
                r[f"idx_rtn_{n}d_rt"] = idx
                r[f"excess_{n}d_rt"] = difference(value, idx) if status == istatus == "OK" else ""
                r[f"excess_{n}d_stts_cd"] = status if status != "OK" else istatus
            for n in (5, 20):
                window = rows[max(0, i-n+1):i+1]
                for prefix in ("frgn", "inst", "indv"):
                    present = len(window) == n and all(x[prefix+"_net_buy_qty"] != "" and x["trd_qty"] != "" for x in window)
                    total = sum(Decimal(x[prefix+"_net_buy_qty"]) for x in window) if present else None
                    volume = sum(Decimal(x["trd_qty"]) for x in window) if present else None
                    value, status = ratio(total, volume) if present else ("", "WINDOW_SHORT" if len(window) < n else "NO_DATA")
                    r[f"{prefix}_net_{n}d_qty"] = number(total)
                    r[f"{prefix}_flow_{n}d_rt"], r[f"{prefix}_flow_{n}d_stts_cd"] = value, status
            previous = rows[i-20] if i >= 20 else None
            r["frgn_hold_change_20d_rt"] = difference(r["frgn_hold_rt"], previous["frgn_hold_rt"]) if previous else ""
            r["frgn_hold_change_20d_stts_cd"] = "OK" if r["frgn_hold_change_20d_rt"] != "" else "WINDOW_SHORT" if not previous else "NO_DATA"
            returns = [x["rtn_1d_rt"] for x in rows[max(0, i-19):i+1]]
            good = len(returns) == 20 and all(x != "" for x in returns)
            r["volatility_20d_rt"] = f"{np.std([float(x) for x in returns], ddof=1):.8f}" if good else ""
            r["volatility_20d_stts_cd"] = "OK" if good else "WINDOW_SHORT" if i < 20 else "NO_DATA"
            j = bisect_left(trading_dates, r["dscl_dt"]) - 1 if r["dscl_dt"] else -1
            base = rows[j] if j >= 0 else None
            price, ps = ratio(r["close_prc"], base["close_prc"], True) if base else ("", "NO_PRE_EVENT_PRICE")
            idx, ins = ratio(r["idx_close_prc"], base["idx_close_prc"], True) if base else ("", "NO_PRE_EVENT_PRICE")
            r["event_base_dt"] = base["trd_dt"] if base else ""
            r["event_rtn_rt"], r["event_idx_rtn_rt"] = price, idx
            r["event_excess_rt"] = difference(price, idx) if ps == ins == "OK" else ""
            r["event_stts_cd"] = "NO_DATA" if not r["fin_rpt_id"] else ps if ps != "OK" else ins
            r["co_move_cd"] = co_move(r["rev_yoy_rt"], r["event_excess_rt"])
            r["co_move_stts_cd"] = r["rev_yoy_rt_stts_cd"] or "NO_DATA"
            if r["co_move_stts_cd"] == "OK":
                r["co_move_stts_cd"] = r["event_stts_cd"]
            ready = r["co_move_cd"] != "UNAVAILABLE" and r["op_cf_delta_amt"] != "" and all(r[f"{p}_flow_20d_stts_cd"] == "OK" for p in ("frgn", "inst"))
            r["joint_improve_yn"] = ("Y" if all(Decimal(r[c]) > 0 for c in ["rev_yoy_rt", "event_excess_rt", "op_cf_delta_amt", "frgn_net_20d_qty", "inst_net_20d_qty"]) else "N") if ready else ""
            r["joint_improve_stts_cd"] = "OK" if ready else "UNAVAILABLE"
            r["calc_ver"] = VERSION
            output.append(r)
    return pd.DataFrame(output)


def validate(s, baseline, financial, daily):
    """Independent source checks; known absences are reported, not repaired."""
    checks = {}
    def verify(name, actual, expected):
        checks[name] = {"actual": int(actual), "expected": int(expected), "pass": bool(actual == expected)}
    verify("financial_rows", len(financial), len(s["s_fin_rpt"]))
    verify("daily_rows", len(daily), len(s["s_stock_daily_prc"]))
    verify("financial_duplicate_keys", financial.fin_rpt_id.duplicated().sum(), 0)
    verify("daily_duplicate_keys", daily.duplicated(["stock_cd", "trd_dt"]).sum(), 0)
    verify("pit_date_violations", sum(bool(r.dscl_dt) and r.dscl_dt >= r.trd_dt for r in daily.itertuples()), 0)
    source = s["s_stock_daily_prc"].set_index(["stock_cd", "trd_dt"]).close_prc.to_dict()
    verify("source_close_mismatches", sum(source[(r.stock_cd, r.trd_dt)] != r.close_prc for r in daily.itertuples()), 0)
    top = s["s_invstr_trd_daily"].query("aggr_lvl_cd == 'TOP_LEVEL'").set_index(["stock_cd", "trd_dt", "invstr_type_cd"]).net_buy_qty.to_dict()
    mismatches = 0
    for r in daily.itertuples():
        for code, col in [("FOREIGNER", "frgn_net_buy_qty"), ("INSTITUTION", "inst_net_buy_qty"), ("INDIVIDUAL", "indv_net_buy_qty")]:
            key = (r.stock_cd, r.trd_dt, code)
            expected = top.get(key, "")
            mismatches += expected != getattr(r, col)
    verify("top_level_flow_mismatches", mismatches, 0)
    verify("missing_financial_rows", (daily.fin_rpt_id == "").sum(), (baseline.fin_rpt_id == "").sum())
    if not all(c["pass"] for c in checks.values()):
        raise ValueError(f"Gold validation failed: {checks}")
    return checks
