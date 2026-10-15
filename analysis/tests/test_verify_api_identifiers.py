"""Identifiers are not numeric values even when they contain only digits."""
import unittest

from analysis import verify_api


def compare(gold, api):
    tally = verify_api.Tally("schema types")
    tally.add_api("row", api)
    return tally.result([("row", gold)], list(gold))


class IdentifierComparisonTests(unittest.TestCase):
    def test_leading_zero_loss_in_stock_and_corp_fails(self):
        result = compare({"stock_cd": "005930", "corp_cd": "00126380"},
                         {"stock_cd": "5930", "corp_cd": "126380"})
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["value_diff_count"], 2)
        self.assertEqual(result["format_only_diff"], 0)

    def test_receipt_year_version_date_and_unknown_are_exact(self):
        gold = dict(rcept_no="00000000000001", bsns_yr="2025", calc_ver="01", trd_dt="2026-06-30", unknown="01")
        api = dict(rcept_no="1", bsns_yr="2025.0", calc_ver="1", trd_dt="20260630", unknown="1")
        result = compare(gold, api)
        self.assertEqual(result["value_diff_count"], 5)
        self.assertEqual(result["format_only_diff"], 0)

    def test_declared_money_quantity_and_rate_allow_equal_padding(self):
        gold = dict(rev_ytd_amt="9007199254740993", close_prc="100", frgn_net_buy_qty="2", frgn_hold_rt="0.5")
        api = dict(rev_ytd_amt="9007199254740993.0", close_prc="100.0000", frgn_net_buy_qty="2.0", frgn_hold_rt="0.50000000")
        result = compare(gold, api)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["format_only_diff"], 4)

    def test_null_zero_whitespace_exponent_and_changed_precision_fail(self):
        pairs = [("rev_ytd_amt", "0", None), ("close_prc", "100", " 100"),
                 ("close_prc", "1000", "1e3"), ("rev_ytd_amt", "9007199254740993", "9007199254740992")]
        for field, gold, api in pairs:
            with self.subTest(field=field, gold=gold, api=api):
                result = compare({field: gold}, {field: api})
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["value_diff_count"], 1)

    def test_ambiguous_schema_field_is_not_numeric(self):
        from unittest import mock
        schema = {"a": {"columns": [{"name": "value", "type": "DECIMAL(20,0)"}]},
                  "b": {"columns": [{"name": "value", "type": "CHAR(8)"}]}}
        import json
        with mock.patch.object(verify_api.Path, "read_text", return_value=json.dumps(schema)):
            self.assertNotIn("value", verify_api.numeric_columns())


if __name__ == "__main__":
    unittest.main()
