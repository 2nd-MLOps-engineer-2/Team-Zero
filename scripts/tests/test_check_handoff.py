"""Detect loss or corruption instead of silently accepting a damaged snapshot."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("checker", Path(__file__).parents[1] / "check_handoff.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SnapshotCheck(unittest.TestCase):
    def test_copy_corruption_missing_and_extra(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "sample.csv"
            content = b"code,value\n005930,0\n"
            path.write_bytes(content)
            manifest = {"file_count": 1, "total_bytes": len(content), "files": [{
                "path": "sample.csv", "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "columns": ["code", "value"], "rows": 1,
            }]}
            self.assertEqual(checker.check(root, manifest), [])
            path.write_bytes(content.replace(b"0\n", b"1\n"))
            self.assertTrue(any("Changed bytes" in e for e in checker.check(root, manifest)))
            path.unlink()
            self.assertTrue(any("Missing file" in e for e in checker.check(root, manifest)))
            path.write_bytes(content + b"000660,2\n")
            self.assertTrue(any("CSV header/row" in e for e in checker.check(root, manifest)))
            path.write_bytes(content)
            (root / "extra.txt").write_text("extra")
            self.assertTrue(any("Unexpected file" in e for e in checker.check(root, manifest)))

    def test_unicode_filename_and_empty_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "가.csv").write_bytes(b"")
            manifest = {"file_count": 1, "total_bytes": 0, "files": [{
                "path": "가.csv", "bytes": 0, "sha256": hashlib.sha256(b"").hexdigest(),
                "columns": [], "rows": 0,
            }]}
            self.assertEqual(checker.check(root, manifest), [])


if __name__ == "__main__":
    unittest.main()
