import csv,hashlib,json
from types import SimpleNamespace
import pytest
from tz_api.analysis import load_bundle,CONTRACT
from tz_api.repository import wire
from decimal import Decimal

@pytest.fixture
def bundle(tmp_path):
 # Explicitly synthetic boundary data; no C calculations are implemented here.
 tables={
  'g_fin_rpt_analysis':dict(primary_key=['fin_rpt_id'],columns=[dict(name='fin_rpt_id',sql='VARCHAR(64)',nullable=False),dict(name='example_rt',sql='DECIMAL(12,8)',nullable=True)],rows=[['report_test','0.12345678']]),
  'g_stock_daily_analysis':dict(primary_key=['stock_cd','trd_dt'],columns=[dict(name='stock_cd',sql='CHAR(6)',nullable=False),dict(name='trd_dt',sql='DATE',nullable=False),dict(name='fin_rpt_id',sql='VARCHAR(64)',nullable=True)],rows=[['000001','2026-01-02','']])}
 manifest=dict(contract_version=CONTRACT,calculation_version='SYNTHETIC_TEST_ONLY',input_version='synthetic_test',tables={})
 for name,spec in tables.items():
  p=tmp_path/(name+'.csv')
  with p.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow([c['name'] for c in spec['columns']]);w.writerows(spec['rows'])
  manifest['tables'][name]=dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows=len(spec['rows']),primary_key=spec['primary_key'],columns=spec['columns'])
 (tmp_path/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
 repo=SimpleNamespace(reports={'report_test':{}},daily={'000001':[dict(trd_dt='2026-01-02',fin_rpt_id=None)]},handoff_version='synthetic_test')
 return tmp_path,repo,manifest

def test_lossless_large_number_wire():assert wire(Decimal('9007199254740993'))=='9007199254740993'

def test_valid_c_proposal_preserves_values_and_missing(bundle):
 root,repo,_=bundle;r=load_bundle(root,repo)
 assert r['financial']['report_test']['example_rt']=='0.12345678'
 assert r['daily'][('000001','2026-01-02')]['fin_rpt_id'] is None

def test_missing_contract_refused(bundle):
 root,repo,mf=bundle;mf['contract_version']='unknown'
 (root/'manifest.json').write_text(json.dumps(mf))
 with pytest.raises(ValueError,match='contract'):load_bundle(root,repo)

def test_traversal_refused(bundle):
 root,repo,mf=bundle;mf['tables']['g_fin_rpt_analysis']['file']='../private.csv'
 (root/'manifest.json').write_text(json.dumps(mf))
 with pytest.raises(ValueError,match='escapes'):load_bundle(root,repo)

def test_hash_mismatch_refused(bundle):
 root,repo,_=bundle;(root/'g_fin_rpt_analysis.csv').write_text('modified')
 with pytest.raises(ValueError,match='hash'):load_bundle(root,repo)

def test_key_coverage_refused(bundle):
 root,repo,_=bundle;repo.reports['additional_report']={}
 with pytest.raises(ValueError,match='key coverage'):load_bundle(root,repo)

def test_pit_selection_mismatch_refused(bundle):
 root,repo,_=bundle;repo.daily['000001'][0]['fin_rpt_id']='report_test'
 with pytest.raises(ValueError,match='PIT'):load_bundle(root,repo)

def test_input_version_mismatch_refused(bundle):
 root,repo,_=bundle;repo.handoff_version='different_input'
 with pytest.raises(ValueError,match='input version'):load_bundle(root,repo)

def test_c_artifact_delta_storage_preserves_source_values(bundle,project,tmp_path,monkeypatch):
 import import_analysis
 from deltalake import DeltaTable
 root,repo,_=bundle;repo.warm=lambda:repo;repo.data_version='synthetic_test'
 monkeypatch.setattr(import_analysis,'Repository',lambda settings:repo)
 before={p.name:p.read_bytes() for p in root.glob('*.csv')}
 run,catalog=import_analysis.prepare(root,project,tmp_path/'output')
 assert {e['name']:e['rows'] for e in catalog['tables']}=={'g_fin_rpt_analysis':1,'g_stock_daily_analysis':1}
 for entry in catalog['tables']:
  assert (run/entry['delta_path']/'_delta_log').is_dir()
  assert DeltaTable(str(run/entry['delta_path']),version=0).to_pyarrow_table().num_rows==1
 assert before=={p.name:p.read_bytes() for p in root.glob('*.csv')}

def test_new_analysis_loader_refuses_existing_database(bundle,project,tmp_path,monkeypatch):
 import import_analysis,pymysql
 root,repo,_=bundle;repo.warm=lambda:repo;repo.data_version='synthetic_test'
 monkeypatch.setattr(import_analysis,'Repository',lambda settings:repo)
 run,catalog=import_analysis.prepare(root,project,tmp_path/'output');queries=[]
 class Cursor:
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def execute(self,sql,args=None):queries.append(sql)
  def fetchone(self):return (1,)
 class Con:
  def cursor(self):return Cursor()
  def close(self):pass
 monkeypatch.setattr(pymysql,'connect',lambda **kw:Con())
 with pytest.raises(ValueError,match='Refusing existing'):import_analysis.mysql_load(run,catalog,'127.0.0.1',3306,'root','test')
 assert not any(q.startswith(('CREATE','DROP','DELETE','TRUNCATE','INSERT')) for q in queries)
