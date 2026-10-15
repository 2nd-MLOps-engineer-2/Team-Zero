import unittest
from pathlib import Path

import pandas as pd

from analysis.gold import load_silver
from analysis.rules import institution_detail_identity, period_continuity, prior_ytd_restatement


def silver(reports, metrics, investors=None):
    rpt = pd.DataFrame([dict(fin_rpt_id=i, corp_cd="C1", bsns_yr=y, rpt_cd=c, fs_div_cd="CFS",
                             cal_prd_stts_cd="VERIFIED_XML") for i, y, c in reports])
    mtrc = pd.DataFrame([dict(fin_rpt_id=i, mtrc_cd=m, prd_type_cd=p, mtrc_amt=a) for i, m, p, a in metrics])
    return {"s_fin_rpt": rpt, "s_fin_mtrc": mtrc, "s_invstr_trd_daily": investors}


class SyntheticRuleTests(unittest.TestCase):
    def test_continuity_match_rounding_review(self):
        s = silver([("Q1", "2024", "11013"), ("H1", "2024", "11012"), ("Q3", "2024", "11014")], [
            ("Q1", "REVENUE", "YTD", "100"), ("Q1", "REVENUE", "Q3M", "100"),
            ("H1", "REVENUE", "YTD", "250"), ("H1", "REVENUE", "Q3M", "150"),            # match
            ("Q3", "REVENUE", "YTD", "400"), ("Q3", "REVENUE", "Q3M", "149"),            # gap 1 -> rounding
            ("Q1", "NET_INCOME", "YTD", "10"), ("Q1", "NET_INCOME", "Q3M", "10"),
            ("H1", "NET_INCOME", "YTD", "5000010"), ("H1", "NET_INCOME", "Q3M", "10"),  # gap 4,999,990 -> review
        ])
        summary, detail = period_continuity(s)
        self.assertEqual(summary["compared"], 3)
        self.assertEqual(summary["by_class"], {"MATCH": 1, "UNIT_ROUNDING": 1, "REVIEW": 1})
        self.assertEqual(summary["review_reports"], ["H1"])
        self.assertEqual(detail.set_index("mtrc_cd").loc["NET_INCOME", "gap_amt"], 4999990)

    def test_blank_q3m_is_not_compared_as_zero(self):
        s = silver([("Q1", "2024", "11013"), ("H1", "2024", "11012")], [
            ("Q1", "REVENUE", "YTD", "100"), ("H1", "REVENUE", "YTD", "250"), ("H1", "REVENUE", "Q3M", "")])
        self.assertEqual(period_continuity(s)[0]["compared"], 0)

    def test_restatement_uses_exact_integers(self):
        big = "12345678901234567"
        s = silver([("A23", "2023", "11011"), ("A24", "2024", "11011")], [
            ("A23", "REVENUE", "YTD", big), ("A24", "REVENUE", "PRIOR_YTD", str(int(big) + 1)),
            ("A23", "NET_INCOME", "YTD", "7"), ("A24", "NET_INCOME", "PRIOR_YTD", "7")])
        summary, diff = prior_ytd_restatement(s)
        self.assertEqual(summary["differs"], {"REVENUE": 1})
        self.assertEqual(diff.diff_amt.tolist(), [1])

    def test_institution_identity_detects_double_count_risk(self):
        rows = [("INSTITUTION", "TOP_LEVEL", "10"), ("PENSION", "INST_DETAIL", "6"), ("BANK", "INST_DETAIL", "4"),
                ("FOREIGNER", "TOP_LEVEL", "-3")]
        inv = pd.DataFrame([dict(stock_cd="000001", trd_dt="2024-01-02", invstr_type_cd=t, aggr_lvl_cd=a, net_buy_qty=n)
                            for t, a, n in rows])
        self.assertTrue(institution_detail_identity({"s_invstr_trd_daily": inv})["pass"])
        inv.loc[inv.invstr_type_cd == "BANK", "net_buy_qty"] = "5"
        self.assertFalse(institution_detail_identity({"s_invstr_trd_daily": inv})["pass"])


class RealSilverRuleTests(unittest.TestCase):
    """Regression on the supplied package (counts recorded in docs/roles/C.md)."""

    @classmethod
    def setUpClass(cls):
        cls.s = load_silver(Path(__file__).resolve().parents[2] / "data/03_C_integration_20261014")

    def test_institution_identity_holds_for_all_keys(self):
        r = institution_detail_identity(self.s)
        self.assertEqual((r["actual"], r["expected"], r["pass"]), (17439, 17439, True))

    def test_continuity_and_restatement_counts(self):
        cont, _ = period_continuity(self.s)
        self.assertEqual(cont["compared"], 480)
        self.assertEqual(sum(v for k, v in cont["by_class"].items() if k != "MATCH"), 27)
        rest, _ = prior_ytd_restatement(self.s)
        self.assertEqual(rest["differs"]["REVENUE"], 32)


if __name__ == "__main__":
    unittest.main()
