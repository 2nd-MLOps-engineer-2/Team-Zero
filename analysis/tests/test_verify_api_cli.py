"""Run the actual CLI against a local synthetic HTTP API; no external services."""
import json
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from analysis.tests.test_verify_api import DAILY, FIN, FakeApi, gold_frames


class CliExitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        daily, fin = gold_frames()
        daily.to_csv(self.directory/DAILY, index=False)
        fin.to_csv(self.directory/FIN, index=False)
        self.api = FakeApi(daily, fin, self.directory)
        api = self.api

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                try:
                    if self.path.startswith("/exports/"):
                        data = api.get("", self.path)
                    else:
                        data = json.dumps(api.get_json("", self.path)).encode()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(data)
                except urllib.error.HTTPError as exc:
                    self.send_error(exc.code)

            def log_message(self, *_):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": .05}, daemon=True)
        self.thread.start()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(self.close_server)

    def close_server(self):
        if self.thread.is_alive():
            self.server.shutdown()
            self.thread.join(timeout=5)
        self.server.server_close()

    def cli(self, gold=None):
        output = self.directory/"result.json"
        proc = subprocess.run([
            sys.executable, "-m", "analysis.verify_api", "--gold", str(gold or self.directory),
            "--base", f"http://127.0.0.1:{self.server.server_port}", "--out", str(output),
        ], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, timeout=30)
        self.assertTrue(output.exists(), proc.stderr)
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report, json.loads(proc.stdout))
        return proc.returncode, report

    def test_pass_returns_zero(self):
        code, report = self.cli()
        self.assertEqual(report["overall"], "PASS")
        self.assertEqual(code, 0)

    def test_value_mismatch_returns_one_and_keeps_json(self):
        self.api.daily["000001"][0]["analysis"]["close_prc"] = "999"
        code, report = self.cli()
        self.assertEqual(report["overall"], "FAIL")
        self.assertEqual(code, 1)
        self.assertEqual(report["results"][0]["value_diff_count"], 1)

    def test_missing_gold_returns_one_and_keeps_json(self):
        code, report = self.cli(self.directory/"missing")
        self.assertEqual(code, 1)
        self.assertEqual(report["overall"], "FAIL")
        self.assertIn("FileNotFoundError", report["errors"][0])

    def test_connection_failure_returns_one_and_keeps_json(self):
        self.close_server()
        code, report = self.cli()
        self.assertEqual(code, 1)
        self.assertEqual(report["overall"], "FAIL")
        self.assertTrue(report["errors"])


if __name__ == "__main__":
    unittest.main()
