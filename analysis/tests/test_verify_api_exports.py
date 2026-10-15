import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from analysis.verify_api import check_exports

class ExportContractTests(unittest.TestCase):
 def check(self,body):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)
   (p/'g_fin_rpt_analysis.csv').write_text('fin_rpt_id,stock_cd,rev_ytd_amt\nr1,005930,100\n',encoding='utf-8')
   (p/'g_stock_daily_analysis.csv').write_text('stock_cd,trd_dt,close_prc\n005930,2026-06-30,100\n',encoding='utf-8')
   def get(base,path):
    return body if 'g_stock_daily' in path else (p/'g_fin_rpt_analysis.csv').read_bytes()
   with patch('analysis.verify_api.get',side_effect=get):return check_exports('',p)[1]
 def test_numeric_format_only_preserves_hash_difference(self):
  r=self.check(b'stock_cd,trd_dt,close_prc\n005930,2026-06-30,100.0000\n')
  self.assertEqual(r['status'],'PASS');self.assertFalse(r['byte_identical']);self.assertEqual(r['format_only_diff'],1)
 def test_identifier_value_missing_duplicate_and_malformed_fail(self):
  for body in [b'stock_cd,trd_dt,close_prc\n5930,2026-06-30,100\n',b'stock_cd,trd_dt,close_prc\n005930,2026-06-30,101\n',b'stock_cd,trd_dt,close_prc\n',b'stock_cd,trd_dt,close_prc\n005930,2026-06-30,100\n005930,2026-06-30,100\n',b'stock_cd,trd_dt,close_prc\n005930,2026-06-30\n']:
   with self.subTest(body=body):self.assertEqual(self.check(body)['status'],'FAIL')
