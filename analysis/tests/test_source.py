"""Real supplied data checks, independent of the published baseline formula."""
import unittest
from decimal import Decimal
from pathlib import Path

from analysis.gold import build_financial, load_silver


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = load_silver(Path(__file__).resolve().parents[2]/"data/03_C_integration_20261014")
        cls.fin = build_financial(cls.s)

    def test_exact_money_and_unverified_period(self):
        self.assertEqual(len(self.fin), 320)
        self.assertEqual(sum(Decimal(v) for v in self.fin.rev_ytd_amt), Decimal("8496305502116058"))
        unverified = self.fin.query("same_prd_cmpr_elig_yn == 'N'")
        self.assertEqual(len(unverified), 61)
        self.assertTrue((unverified.rev_yoy_rt == "").all())
        self.assertTrue((unverified.rev_yoy_rt_stts_cd == "PRD_UNVERIFIED").all())

    def test_source_revenue_growth(self):
        # Compare every eligible result to a direct source amount computation,
        # without calling the implementation's ratio helper.
        source = self.s["s_fin_mtrc"].set_index(["fin_rpt_id", "mtrc_cd", "prd_type_cd"]).mtrc_amt
        eligible = self.fin.query("rev_yoy_rt_stts_cd == 'OK'")
        self.assertGreater(len(eligible), 200)
        for row in eligible.itertuples():
            current = Decimal(source.loc[row.fin_rpt_id, "REVENUE", "YTD"])
            prior = Decimal(source.loc[row.fin_rpt_id, "REVENUE", "PRIOR_YTD"])
            self.assertLessEqual(abs(Decimal(row.rev_yoy_rt) - (current-prior)/prior), Decimal("0.000000005"))


if __name__ == "__main__":
    unittest.main()
