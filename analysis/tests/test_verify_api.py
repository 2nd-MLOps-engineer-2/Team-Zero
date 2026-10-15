"""verify_api 대조 로직 테스트: 네트워크 없이 get/get_json을 합성 API로 바꿔 실행한다."""
import copy
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import pandas as pd

from analysis import verify_api

DAILY = "g_stock_daily_analysis.csv"
FIN = "g_fin_rpt_analysis.csv"


def gold_frames():
    daily = pd.DataFrame([
        dict(stock_cd="000001", trd_dt="2026-06-29", close_prc="100", rtn="0", rev_ytd_amt="333000"),
        dict(stock_cd="000001", trd_dt="2026-06-30", close_prc="101", rtn="", rev_ytd_amt="333000"),
        dict(stock_cd="000002", trd_dt="2026-06-29", close_prc="50", rtn="1", rev_ytd_amt=""),
        dict(stock_cd="000002", trd_dt="2026-06-30", close_prc="51", rtn="-0.5", rev_ytd_amt=""),
    ])
    fin = pd.DataFrame([
        dict(fin_rpt_id="R1", stock_cd="000001", rev_ytd_amt="333000", review_required_yn="N"),
        dict(fin_rpt_id="R2", stock_cd="000002", rev_ytd_amt="", review_required_yn="Y"),
    ])
    return daily, fin


class FakeApi:
    """Gold 원본으로 만든 API. 테스트가 daily/fin 행(analysis dict)을 직접 고쳐 차이를 만든다."""

    def __init__(self, daily: pd.DataFrame, fin: pd.DataFrame, gold_dir: Path, final_date="2026-06-30"):
        null = lambda rec: {k: (None if v == "" else v) for k, v in rec.items()}
        self.daily = {}
        for rec in daily.to_dict("records"):
            self.daily.setdefault(rec["stock_cd"], []).append({"trd_dt": rec["trd_dt"], "analysis": null(rec)})
        self.fin = {}
        for rec in fin.to_dict("records"):
            self.fin.setdefault(rec["stock_cd"], []).append({"fin_rpt_id": rec["fin_rpt_id"], "analysis": null(rec)})
        self.final_date = final_date
        self.exports = {n: (gold_dir / n).read_bytes() for n in (DAILY, FIN)}
        self.http_errors: dict[str, int] = {}  # 경로(쿼리 제외) -> 강제 HTTP 상태 코드

    def get_json(self, base, path):
        route, _, query = path.partition("?")
        if route in self.http_errors:
            raise urllib.error.HTTPError(base + path, self.http_errors[route], "forced", None, None)
        q = dict(p.split("=", 1) for p in query.split("&") if p)
        if route == "/health":
            return {"meta": {"data_final_date": self.final_date}}
        if route == "/stocks":
            codes = sorted(self.daily)
            lim, off = int(q["limit"]), int(q["offset"])
            return {"data": [{"stock_cd": c} for c in codes[off:off + lim]], "meta": {"total": len(codes)}}
        if route == "/stocks/compare":
            rows = []
            for code, items in sorted(self.daily.items()):
                upto = [r for r in items if r["trd_dt"] <= q["as_of"]]
                if upto:
                    rows.append({"stock_cd": code, "analysis": upto[-1]["analysis"]})
            return {"data": rows, "meta": {"requested_as_of": q["as_of"]}}
        _, _, code, kind = route.split("/")
        if code not in self.daily and code not in self.fin:  # B API: 제공 범위 밖 종목은 404
            raise urllib.error.HTTPError(base + path, 404, "STOCK_NOT_FOUND", None, None)
        if kind == "daily":
            rows = self.daily[code]
            lim, off = int(q["limit"]), int(q["offset"])
            return {"data": rows[off:off + lim], "meta": {"total": len(rows)}}
        if kind == "financials":
            return {"data": self.fin.get(code, [])}
        raise KeyError(path)

    def get(self, base, path):
        return self.exports[path.rsplit("/", 1)[1]]


class VerifyApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.daily, self.fin = gold_frames()
        self.write_gold()
        self.api = FakeApi(self.daily, self.fin, self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def write_gold(self):
        self.daily.to_csv(self.dir / DAILY, index=False)
        self.fin.to_csv(self.dir / FIN, index=False)

    def run_check(self, page_size=verify_api.DAILY_PAGE):
        with mock.patch.object(verify_api, "get_json", self.api.get_json), \
                mock.patch.object(verify_api, "get", self.api.get):
            report = verify_api.run("http://fake", self.dir, page_size)
        return report, {r["check"].split(" ")[0]: r for r in report["results"][:3]}

    def api_row(self, code="000001", i=0):
        return self.api.daily[code][i]["analysis"]

    def test_clean_pass(self):
        report, res = self.run_check()
        self.assertEqual(report["overall"], "PASS")
        self.assertEqual(res["daily"]["rows_compared"], 4)
        self.assertEqual(res["financial"]["rows_compared"], 2)
        self.assertEqual(res["compare"]["rows_compared"], 2)

    def test_one_value_changed_fails(self):
        self.api_row()["close_prc"] = "999"
        _, res = self.run_check()
        self.assertEqual(res["daily"]["status"], "FAIL")
        self.assertEqual(res["daily"]["value_diff_count"], 1)
        self.assertEqual(res["financial"]["status"], "PASS")

    def test_zero_and_blank_are_distinct(self):
        self.api_row()["rtn"] = None  # Gold "0"
        self.api_row(i=1)["rtn"] = "0"  # Gold ""
        _, res = self.run_check()
        self.assertEqual(res["daily"]["value_diff_count"], 2)
        self.assertEqual(res["daily"]["format_only_diff"], 0)

    def test_row_dropped_from_gold_is_extra_row(self):
        self.daily = self.daily.drop(index=0)
        self.write_gold()
        _, res = self.run_check()
        self.assertEqual(res["daily"]["status"], "FAIL")
        self.assertEqual(res["daily"]["extra_rows"], ["000001/2026-06-29"])
        self.assertEqual(res["daily"]["missing_row_count"], 0)

    def test_report_dropped_from_gold_is_extra_row(self):
        self.fin = self.fin.drop(index=1)
        self.write_gold()
        _, res = self.run_check()
        self.assertEqual(res["financial"]["status"], "FAIL")
        self.assertEqual(res["financial"]["extra_rows"], ["R2"])

    def test_column_dropped_from_gold_is_extra_column(self):
        self.daily = self.daily.drop(columns=["rtn"])
        self.fin = self.fin.drop(columns=["review_required_yn"])
        self.write_gold()
        _, res = self.run_check()
        self.assertEqual(res["daily"]["extra_columns"], {"rtn": 4})
        self.assertEqual(res["compare"]["extra_columns"], {"rtn": 2})
        self.assertEqual(res["financial"]["extra_columns"], {"review_required_yn": 2})
        for name in ("daily", "financial", "compare"):
            self.assertEqual(res[name]["status"], "FAIL", name)

    def test_duplicate_keys_fail(self):
        self.api.daily["000001"].append(copy.deepcopy(self.api.daily["000001"][0]))
        self.api.fin["000002"].append(copy.deepcopy(self.api.fin["000001"][0]))  # R1 두 번
        _, res = self.run_check()
        self.assertEqual(res["daily"]["duplicate_keys"], ["000001/2026-06-29"])
        self.assertEqual(res["financial"]["duplicate_keys"], ["R1"])
        self.assertEqual(res["daily"]["status"], "FAIL")
        self.assertEqual(res["financial"]["status"], "FAIL")

    def test_whitespace_is_value_diff(self):
        self.api_row("000002")["rtn"] = " 1"
        _, res = self.run_check()
        self.assertEqual(res["daily"]["value_diff_count"], 1)
        self.assertEqual(res["daily"]["format_only_diff"], 0)
        self.assertFalse(verify_api.same_number("1_000", "1000"))
        self.assertFalse(verify_api.same_number("1e3", "1000"))

    def test_trailing_zero_padding_is_format_diff(self):
        self.api_row()["rev_ytd_amt"] = "333000.0000"
        _, res = self.run_check()
        self.assertEqual(res["daily"]["status"], "PASS")
        self.assertEqual(res["daily"]["format_only_diff"], 1)
        self.assertEqual(res["daily"]["value_diff_count"], 0)

    def test_daily_paging_follows_offset(self):
        report, res = self.run_check(page_size=1)
        self.assertEqual(res["daily"]["status"], "PASS")
        self.assertEqual(res["daily"]["rows_api"], 4)

    def test_compare_date_mismatch_fails(self):
        self.api.final_date = "2026-07-01"
        _, res = self.run_check()
        self.assertEqual(res["compare"]["status"], "FAIL")
        self.assertEqual(res["compare"]["as_of_queried"], "2026-06-30")
        self.assertTrue(res["compare"]["notes"])

    def test_gold_only_stock_404_is_missing_rows(self):
        extra = dict(stock_cd="999999", trd_dt="2026-06-30", close_prc="1", rtn="", rev_ytd_amt="")
        self.daily = pd.concat([self.daily, pd.DataFrame([extra])], ignore_index=True)
        self.write_gold()  # API(FakeApi)는 원래 Gold로 만들어져 999999를 모른다 -> 404
        report, res = self.run_check()
        self.assertEqual(report["overall"], "FAIL")
        self.assertEqual(res["daily"]["status"], "FAIL")
        self.assertEqual(res["daily"]["missing_rows"], ["999999/2026-06-30"])
        self.assertEqual(res["daily"]["api_not_found_stocks"], ["999999"])
        self.assertEqual(res["daily"]["errors"], [])
        self.assertEqual(res["compare"]["missing_rows"], ["999999"])
        self.assertEqual(res["financial"]["status"], "PASS")  # 999999 보고서 Gold 행 없음 -> 404여도 누락 0

    def test_non_404_http_error_is_recorded_and_fails(self):
        self.api.http_errors["/stocks/000002/daily"] = 500
        self.api.http_errors["/stocks/000001/financials"] = 503
        report, res = self.run_check()
        self.assertEqual(report["overall"], "FAIL")
        self.assertEqual(res["daily"]["status"], "FAIL")
        self.assertEqual(res["daily"]["errors"], ["000002: daily offset=0: HTTP 500"])
        self.assertEqual(res["financial"]["status"], "FAIL")
        self.assertEqual(res["financial"]["errors"], ["000001: financials: HTTP 503"])
        self.assertEqual(res["compare"]["status"], "PASS")

    def test_connection_failure_still_returns_report(self):
        def refused(base, path):
            raise urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))
        self.api.get_json = refused
        self.api.get = refused
        report, res = self.run_check()
        self.assertEqual(report["overall"], "FAIL")
        self.assertTrue(report["errors"])
        for name in ("daily", "financial", "compare"):
            self.assertEqual(res[name]["status"], "FAIL", name)
            self.assertTrue(res[name]["errors"], name)
        self.assertTrue(all(r["status"] == "FAIL" for r in report["results"][3:]))

    def test_gold_daily_duplicate_fails(self):
        self.daily = pd.concat([self.daily, self.daily.iloc[[3]]], ignore_index=True)  # 000002/2026-06-30 두 번
        self.write_gold()
        _, res = self.run_check()
        self.assertEqual(res["daily"]["status"], "FAIL")
        self.assertEqual(res["daily"]["rows_gold"], 5)
        self.assertEqual(res["daily"]["gold_duplicate_key_count"], 1)
        self.assertEqual(res["daily"]["gold_duplicate_keys"], ["000002/2026-06-30"])
        self.assertEqual(res["daily"]["value_diff_count"], 0)
        self.assertEqual(res["compare"]["status"], "FAIL")  # 마지막 관측일 행이 두 개
        self.assertEqual(res["compare"]["gold_duplicate_keys"], ["000002"])

    def test_gold_report_duplicate_fails(self):
        self.fin = pd.concat([self.fin, self.fin.iloc[[0]]], ignore_index=True)  # R1 두 번
        self.write_gold()
        _, res = self.run_check()
        self.assertEqual(res["financial"]["status"], "FAIL")
        self.assertEqual(res["financial"]["rows_gold"], 3)
        self.assertEqual(res["financial"]["gold_duplicate_keys"], ["R1"])
        self.assertEqual(res["daily"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
