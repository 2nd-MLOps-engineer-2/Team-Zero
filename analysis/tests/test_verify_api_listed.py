"""A listed stock must remain addressable even if no analysis rows exist."""
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from analysis import verify_api
from analysis.tests.test_verify_api import DAILY, FIN, FakeApi, gold_frames


class ListedStockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.daily, self.fin = gold_frames()

    def check(self, api, page_size=5000):
        with mock.patch.object(verify_api, "get_json", api.get_json), mock.patch.object(verify_api, "get", api.get):
            return verify_api.run("http://fake", self.directory, page_size)

    def prepare(self):
        self.daily.to_csv(self.directory/DAILY, index=False)
        self.fin.to_csv(self.directory/FIN, index=False)
        return FakeApi(self.daily, self.fin, self.directory)

    def test_listed_only_stock_404_fails_both_queries(self):
        api = self.prepare()
        original = api.get_json
        def listed(base, path):
            if path.startswith("/stocks?"):
                return {"data": [{"stock_cd": c} for c in ["000001", "000002", "999999"]], "meta": {"total": 3}}
            return original(base, path)
        api.get_json = listed
        report = self.check(api)
        self.assertEqual(report["overall"], "FAIL")
        for result in report["results"][:2]:
            self.assertEqual(result["missing_row_count"], 0)
            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["api_not_found_stocks"], ["999999"])
            self.assertIn("listed by /stocks", result["errors"][0])

    def test_known_stock_with_no_reports_returns_empty_success(self):
        self.fin = self.fin.query("stock_cd != '000002'")
        report = self.check(self.prepare())
        self.assertEqual(report["overall"], "PASS")
        self.assertEqual(report["results"][1]["rows_compared"], 1)

    def test_listed_stock_financials_404_fails_even_without_gold_report(self):
        self.fin = self.fin.query("stock_cd != '000002'")
        api = self.prepare()
        api.http_errors["/stocks/000002/financials"] = 404
        report = self.check(api)
        self.assertEqual(report["results"][1]["missing_row_count"], 0)
        self.assertEqual(report["results"][1]["status"], "FAIL")
        self.assertTrue(report["results"][1]["errors"])

    def test_later_page_404_remains_an_error(self):
        api = self.prepare()
        original = api.get_json
        def second_page(base, path):
            if path == "/stocks/000001/daily?limit=1&offset=1":
                raise urllib.error.HTTPError(base+path, 404, "forced", None, None)
            return original(base, path)
        api.get_json = second_page
        result = self.check(api, page_size=1)["results"][0]
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["api_not_found_stocks"], [])
        self.assertIn("offset=1: HTTP 404", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
