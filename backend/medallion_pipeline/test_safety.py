"""Regression checks for data precision and refusal to touch pre-existing databases."""
import json,tempfile,unittest
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch
from engine import parse,digest,arrow_type,delta_snapshot,sha
import mysql_load

class SafetyTests(unittest.TestCase):
 def test_large_amount_exact(self):
  self.assertEqual(parse('9007199254740993','DECIMAL(20,0)',False),Decimal('9007199254740993'))
 def test_precision_loss_refused(self):
  with self.assertRaises(ValueError):parse('1.00001','DECIMAL(18,4)',False)
 def test_missing_and_zero_differ(self):
  self.assertIsNone(parse('','DECIMAL(20,0)',True))
  self.assertEqual(parse('0','DECIMAL(20,0)',True),Decimal(0))
  with self.assertRaises(ValueError):parse('','CHAR(6)',False)
 def test_digest_order_multiplicity_and_null(self):
  s=dict(columns=[dict(name='v',sql='DECIMAL(20,0)')])
  a=[dict(v=Decimal(0)),dict(v=None)]
  self.assertEqual(digest(a,s),digest(a[::-1],s))
  self.assertNotEqual(digest(a,s),digest([dict(v=Decimal(0))]*2,s))
 def test_existing_database_refused_before_any_ddl(self):
  class Cursor:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def execute(self,q,args=None):self.q=q;queries.append(q)
   def fetchone(self):
    if self.q=='SELECT VERSION()':return ('8.4.11',)
    if self.q=='SELECT @@SESSION.sql_mode':return ('STRICT_TRANS_TABLES',)
    return (1,)
  class Con:
   def cursor(self,*args):return Cursor()
   def close(self):pass
  queries=[]
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'catalog.json').write_text(json.dumps(dict(run_id='test',tables=[],databases={'silver':'already_existing'})))
   with patch.object(mysql_load.getpass,'getpass',return_value='test-only'),patch.object(mysql_load.pymysql,'connect',return_value=Con()):
    with self.assertRaisesRegex(ValueError,'Refusing existing database'):mysql_load.load(p,'127.0.0.1','root',3306)
   self.assertFalse(any(q.startswith(('CREATE','DROP','TRUNCATE','DELETE','INSERT','UPDATE')) for q in queries))
 def test_delta_resume_refuses_changed_source_without_overwrite(self):
  import pyarrow as pa
  spec=dict(name='sample',layer='bronze',columns=[dict(name='v',sql='TEXT',nullable=False)],pk=['v'],fks=[])
  with tempfile.TemporaryDirectory() as tmp:
   run=Path(tmp);table=pa.table({'v':['original']})
   entry=delta_snapshot(run,table,spec)
   with self.assertRaises(FileExistsError):delta_snapshot(run,table,spec)
   delta_snapshot(run,table,spec,allow_existing=True)
   with self.assertRaisesRegex(ValueError,'Delta reconciliation'):delta_snapshot(run,pa.table({'v':['changed']}),spec,allow_existing=True)
   for rel,h in entry['delta_files'].items():self.assertEqual(sha(run/entry['delta_path']/rel),h)

if __name__=='__main__':unittest.main()
