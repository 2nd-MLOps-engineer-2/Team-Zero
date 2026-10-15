import json,shutil
from pathlib import Path
import pytest
from tz_api.repository import Repository
from tz_api.settings import Settings

def test_source_hash_failure_refuses_changed_csv(project,tmp_path):
 target=tmp_path/'04_output/silver';target.mkdir(parents=True)
 shutil.copyfile(project/'data/03_C_integration_20261014/04_output/silver/s_stock.csv',target/'s_stock.csv')
 with (target/'s_stock.csv').open('ab') as f:f.write(b'changed')
 repo=Repository(Settings(project=project,backend='csv',data_dir=tmp_path))
 with pytest.raises(ValueError,match='hash mismatch'):repo.rows('s_stock')

def test_delta_and_csv_wire_values_match(project,csv_repo):
 if not (project/'backend/medallion_pipeline/LATEST_RUN.txt').exists():pytest.skip('Local Delta run not present in clone')
 repo=Repository(Settings(project=project,backend='delta'))
 for name,key in [('s_stock',['stock_cd']),('s_fin_rpt',['fin_rpt_id']),('s_fin_mtrc',['fin_rpt_id','mtrc_cd','prd_type_cd']),('g_ai_stock_daily',['stock_cd','trd_dt'])]:
  def keyed(rows):return {tuple(r[k] for k in key):r for r in rows}
  assert keyed(repo.rows(name))==keyed(csv_repo.rows(name))

def test_mysql_adapter_is_read_only_and_detects_mismatch(project,monkeypatch):
 if not (project/'backend/medallion_pipeline/LATEST_RUN.txt').exists():pytest.skip('Local MySQL run catalog not present')
 import pymysql
 repo=Repository(Settings(project=project,backend='mysql',mysql_password='not-a-real-password'))
 entry=repo.entries['s_stock'];rows=repo.engine.load_delta(repo.settings.delta_run,entry).to_pylist();queries=[]
 class Cursor:
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def execute(self,q):queries.append(q)
  def fetchall(self):return rows
 class Con:
  def cursor(self):return Cursor()
  def rollback(self):pass
  def close(self):pass
 monkeypatch.setattr(pymysql,'connect',lambda **kw:Con())
 assert len(repo._mysql('s_stock',entry))==20
 assert queries[0]=='SET SESSION TRANSACTION READ ONLY'
 assert all(q.startswith(('SET SESSION TRANSACTION READ ONLY','SELECT ')) for q in queries)
 rows[0]['stock_nm']='modified'
 with pytest.raises(ValueError,match='values changed'):repo._mysql('s_stock',entry)
 assert 'not-a-real-password' not in repr(repo.settings)
