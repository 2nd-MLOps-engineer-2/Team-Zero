import unittest
from decimal import Decimal

import pandas as pd

from analysis.audit import aggregate_repairs
from analysis.gold import build_daily, choose_report, co_move, difference, ratio, transition


def report(**changes):
    r = dict(stock_cd="005930", fin_rpt_id="R1", pit_join_elig_yn="Y", dscl_dt="2025-01-02",
             bsns_yr="2024", rpt_cd="11014", fs_div_cd="CFS", rcept_no="001", rev_yoy_rt="0.10000000",
             rev_yoy_rt_stts_cd="OK", op_margin_rt="0.1", op_cf_delta_amt="5", op_cf_sales_rt="0.2",
             op_prft_transition_cd="PROFIT_CONTINUES", review_required_yn="N", cal_prd_stts_cd="VERIFIED_XML",
             cf_prd_stts_cd="VERIFIED_XML_YTD", same_prd_cmpr_elig_yn="Y")
    return r | changes


def days(n=25):
    rows = []
    for i, day in enumerate(pd.date_range("2025-01-01", periods=n)):
        rows.append(dict(stock_cd="005930", trd_dt=day.date().isoformat(), close_prc=str(100+i),
                         idx_close_prc="100", trd_qty="100", frgn_net_buy_qty="1", inst_net_buy_qty="2",
                         indv_net_buy_qty="-3", frgn_hold_rt="0.2", fin_rpt_id="R1" if i >= 2 else "",
                         dscl_dt="2025-01-02" if i >= 2 else ""))
    return pd.DataFrame(rows)


class GoldContractTests(unittest.TestCase):
    def test_precision_and_exception_states(self):
        self.assertEqual(difference("9007199254740993", "9007199254740992"), "1")
        self.assertEqual(ratio("10", "0"), ("", "DENOM_ZERO"))
        self.assertEqual(ratio("1", "-2", True), ("", "NEG_BASE"))
        self.assertEqual(ratio("", "2"), ("", "NO_DATA"))
        self.assertEqual(ratio("0", "2"), ("0.00000000", "OK"))
        self.assertEqual(transition("1", "-1"), "LOSS_TO_PROFIT")
        self.assertEqual(transition("-1", "1"), "PROFIT_TO_LOSS")

    def test_pit_day_and_correction_preference(self):
        r = report()
        self.assertIsNone(choose_report([r], "2025-01-02"))
        self.assertEqual(choose_report([r], "2025-01-03")["fin_rpt_id"], "R1")
        older_correction = report(fin_rpt_id="OLD", bsns_yr="2023", dscl_dt="2025-01-04")
        self.assertEqual(choose_report([r, older_correction], "2025-01-05")["fin_rpt_id"], "R1")
        self.assertIsNone(choose_report([report(pit_join_elig_yn="N")], "2025-01-05"))

    def test_classification(self):
        self.assertEqual(co_move("0.1", "-0.1"), "IMPROVE_WEAK")
        self.assertEqual(co_move("-0.1", "0.1"), "SLOW_STRONG")
        self.assertEqual(co_move("0", "0.1"), "NEUTRAL")
        self.assertEqual(co_move("", "0.1"), "UNAVAILABLE")

    def test_windows_missing_values_and_no_lookahead(self):
        baseline = days()
        f = pd.DataFrame([report()])
        result = build_daily({}, baseline, f)
        self.assertEqual(result.iloc[19].rtn_20d_stts_cd, "WINDOW_SHORT")
        self.assertEqual(result.iloc[20].rtn_20d_rt, "0.20000000")
        self.assertEqual(result.iloc[20].frgn_flow_20d_rt, "0.01000000")
        self.assertEqual(result.iloc[2].event_base_dt, "2025-01-01")
        self.assertEqual(result.iloc[20].event_excess_rt, "0.20000000")
        prefix = build_daily({}, baseline.iloc[:21], f)
        pd.testing.assert_frame_equal(prefix, result.iloc[:21].reset_index(drop=True))
        broken = baseline.copy()
        broken.loc[10, "frgn_net_buy_qty"] = ""
        result = build_daily({}, broken, f)
        self.assertEqual(result.iloc[20].frgn_flow_20d_stts_cd, "NO_DATA")
        self.assertEqual(result.iloc[20].joint_improve_yn, "")

    def test_zero_volume_and_stock_boundary(self):
        a = days()
        a["trd_qty"] = "0"
        b = days(2)
        b["stock_cd"] = "000660"
        f = pd.DataFrame([report(), report(stock_cd="000660", fin_rpt_id="R2")])
        result = build_daily({}, pd.concat([a, b], ignore_index=True), f)
        self.assertEqual(result.query("stock_cd == '005930'").iloc[-1].frgn_flow_20d_stts_cd, "DENOM_ZERO")
        self.assertTrue((result.query("stock_cd == '000660'").rtn_20d_stts_cd == "WINDOW_SHORT").all())

    def test_audit_counts_do_not_sum_overlapping_rules(self):
        rows = [dict(source_file="x.csv", source_data_row_1based="1", column="id", rules="TRIM|SYMBOL", resolution="EVIDENCE_BASED_REPAIR"),
                dict(source_file="x.csv", source_data_row_1based="1", column="value", rules="NULL", resolution="NULL_NORMALIZED_STILL_UNRESOLVED")]
        result = aggregate_repairs(rows)
        self.assertEqual(result["changed_cells"], 2)
        self.assertEqual(result["changed_rows"], 1)
        self.assertEqual(sum(result["by_rule_overlapping"].values()), 3)
        self.assertNotIn("before", str(result))


if __name__ == "__main__":
    unittest.main()
