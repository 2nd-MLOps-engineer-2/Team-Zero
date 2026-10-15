import unittest

import pandas as pd

from analysis.asis import _amount_in_text, defect_axes, name_style, naming_profile
from analysis.rules import report_period_join


class DefectAxesTests(unittest.TestCase):
    def test_overlapping_rules_count_cells_once_per_axis(self):
        repairs = [
            dict(dataset="Toss", source_file="a.csv", source_data_row_1based="1", column="symbol",
                 rules="TRIM_OUTER_WHITESPACE|SYMBOL_FROM_FILENAME", resolution="EVIDENCE_BASED_REPAIR"),
            dict(dataset="Toss", source_file="a.csv", source_data_row_1based="1", column="openPrice",
                 rules="NULL_REPRESENTATION", resolution="NULL_NORMALIZED_STILL_UNRESOLVED"),
            dict(dataset="OpenDART", source_file="f.csv", source_data_row_1based="3", column="thstrm_amount",
                 rules="amount_x1000", resolution="EXACT_MANIFEST_RESTORE"),
        ]
        issues = [dict(source_file="a.csv", source_data_row_1based="1", column_or_group="openPrice",
                       issue_code="MISSING_REQUIRED_VALUE")]
        axes, unmapped = defect_axes(repairs, issues)
        self.assertEqual(unmapped, {})
        self.assertEqual(axes["Toss"]["FORMAT"]["cells"], 1)
        self.assertEqual(axes["Toss"]["CODE_MIX"]["cells"], 1)
        self.assertEqual(axes["Toss"]["MISSING"]["cells"], 1)          # null-normalized + quarantine = one cell
        self.assertEqual(axes["OpenDART"]["VALUE_CONSISTENCY"]["rules"], {"amount_x1000": 1})
        self.assertNotIn("before", str(axes))

    def test_naming_styles_and_synonyms(self):
        self.assertEqual([name_style(c) for c in ("stock_code", "volume", "openPrice", "_src")],
                         ["snake_case", "single_lower", "camelCase", "leading_underscore"])
        p = naming_profile({"OpenDART": {"x": ["stock_code", "corp_name"]}, "Toss": {"y": ["symbol", "name", "openPrice"]}})
        self.assertEqual(p["Toss"]["styles"], {"single_lower": 2, "camelCase": 1})
        self.assertIn("OpenDART.stock_code ≠ Toss.symbol", p["synonym_pairs"])

    def test_amount_units_without_partial_matches(self):
        text = "<TD>1,234</TD><TD>91,234,567</TD>"
        self.assertTrue(_amount_in_text(text, "1234000000"))            # KRW million
        self.assertFalse(_amount_in_text(text, "234567"))               # not a substring match
        self.assertTrue(_amount_in_text(text, "91234567"))


class ReportPeriodJoinTests(unittest.TestCase):
    def test_join_and_partial_coverage(self):
        fin = pd.DataFrame(dict(fin_rpt_id=["A", "B"]))
        smry = pd.DataFrame(dict(fin_rpt_id=["A", "B"], full_cvrg_yn=["Y", "N"], prd_rtn_rt=["0.1", ""],
                                 frgn_net_buy_qty=["5", ""], inst_net_buy_qty=["1", ""]))
        self.assertTrue(report_period_join(fin, smry)["pass"])
        smry.loc[1, "prd_rtn_rt"] = "0.2"
        self.assertFalse(report_period_join(fin, smry)["pass"])
        self.assertFalse(report_period_join(pd.DataFrame(dict(fin_rpt_id=["A", "B", "C"])), smry.iloc[:2])["pass"])


if __name__ == "__main__":
    unittest.main()
