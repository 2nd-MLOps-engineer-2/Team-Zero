import gzip,io
from pathlib import Path
from types import SimpleNamespace
import pytest
import verify_mysql as operations

def test_dump_omits_destructive_flags_and_password_argv(tmp_path,monkeypatch):
 captured={};payload=b'CREATE TABLE `example` (`v` TEXT);\nINSERT INTO `example` VALUES ("ok");\n'
 class Process:
  stdout=io.BytesIO(payload);stderr=io.BytesIO(b'')
  def wait(self):return 0
  def poll(self):return 0
 def popen(args,**kwargs):captured.update(args=args,kwargs=kwargs);return Process()
 monkeypatch.setattr(operations.subprocess,'Popen',popen)
 settings=SimpleNamespace(mysql_host='127.0.0.1',mysql_port=3306,mysql_user='root')
 dest=tmp_path/'gold.sql.gz'
 operations.dump_database(Path('mysqldump.exe'),'original',dest,settings,{'MYSQL_PWD':'synthetic-secret'})
 assert '--skip-add-drop-table' in captured['args'] and '--skip-triggers' in captured['args']
 assert '--databases' not in captured['args']
 assert not any('synthetic-secret' in arg for arg in captured['args'])
 assert gzip.decompress(dest.read_bytes())==payload

@pytest.mark.parametrize('payload',[b'USE `original`;\n',b'DROP TABLE `example`;\n',b'CREATE DATABASE `original`;\n'])
def test_database_scoped_or_destructive_dump_refused(tmp_path,monkeypatch,payload):
 class Process:
  stdout=io.BytesIO(payload);stderr=io.BytesIO(b'')
  def wait(self):return 0
  def poll(self):return 0
 monkeypatch.setattr(operations.subprocess,'Popen',lambda *args,**kw:Process())
 settings=SimpleNamespace(mysql_host='127.0.0.1',mysql_port=3306,mysql_user='root')
 with pytest.raises(ValueError,match='Unsafe'):operations.dump_database(Path('mysqldump.exe'),'original',tmp_path/'bad.gz',settings,{})

def test_restore_existing_database_is_preserved(tmp_path,monkeypatch,project):
 import pymysql
 monkeypatch.syspath_prepend(str(project/'backend/medallion_pipeline'))
 for name in ('mysql','mysqldump'):(tmp_path/(name+('.exe' if operations.os.name=='nt' else ''))).write_bytes(b'')
 output=tmp_path/'proof';output.mkdir();queries=[]
 class Cursor:
  def __enter__(self):return self
  def __exit__(self,*args):pass
  def execute(self,sql,args=None):queries.append(sql)
  def fetchone(self):return (1,)
 class Con:
  def cursor(self):return Cursor()
  def close(self):pass
 monkeypatch.setattr(pymysql,'connect',lambda **kw:Con())
 monkeypatch.setattr(operations,'dump_database',lambda binary,db,dest,*args:dest.write_bytes(b'synthetic dump'))
 settings=SimpleNamespace(mysql_host='127.0.0.1',mysql_port=3306,mysql_user='root',mysql_password='test')
 repo=SimpleNamespace(settings=settings,catalog={'databases':{'gold':'original'},'tables':[]},engine=SimpleNamespace(sha=lambda p:'test'))
 with pytest.raises(ValueError,match='Refusing existing restore target'):operations.backup_restore(repo,output,tmp_path)
 assert not any(q.startswith(('CREATE','DROP','DELETE','TRUNCATE','ALTER')) for q in queries)
