from __future__ import annotations
import os,re
from dataclasses import dataclass,field
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[3]

@dataclass
class Settings:
 project:Path=PROJECT
 backend:str='auto'
 data_dir:Path|None=None
 delta_run:Path|None=None
 analysis_dir:Path|None=None
 mysql_host:str='127.0.0.1'
 mysql_port:int=3306
 mysql_user:str='root'
 mysql_password:str=field(default='',repr=False)
 cors_origins:tuple[str,...]=('http://localhost:3000','http://localhost:5173','http://127.0.0.1:5173')

 @classmethod
 def from_env(cls):
  def p(name):return Path(os.environ[name]).expanduser().resolve() if os.environ.get(name) else None
  return cls(project=p('TZ_PROJECT_ROOT') or PROJECT,backend=os.environ.get('TZ_DATA_BACKEND','auto'),
   data_dir=p('TZ_HANDOFF_DIR'),delta_run=p('TZ_DELTA_RUN'),analysis_dir=p('TZ_ANALYSIS_DIR'),
   mysql_host=os.environ.get('TZ_MYSQL_HOST','127.0.0.1'),mysql_port=int(os.environ.get('TZ_MYSQL_PORT','3306')),
   mysql_user=os.environ.get('TZ_MYSQL_USER','root'),mysql_password=os.environ.get('TZ_MYSQL_PASSWORD',''),
   cors_origins=tuple(filter(None,os.environ.get('TZ_CORS_ORIGINS',','.join(cls().cors_origins)).split(','))))

 def resolve(self):
  self.project=self.project.resolve()
  self.data_dir=(self.data_dir or self.project/'data/03_C_integration_20261014').resolve()
  if self.delta_run is None:
   base=self.project/'backend/medallion_pipeline';marker=base/'LATEST_RUN.txt'
   if marker.is_file():
    run=(base/marker.read_text(encoding='utf-8').strip()).resolve()
    if not run.is_relative_to((base/'runs').resolve()):raise ValueError('Invalid Delta run marker')
    self.delta_run=run
  if self.backend=='auto':self.backend='delta' if self.delta_run else 'csv'
  if self.backend not in ('csv','delta','mysql'):raise ValueError('Unsupported data backend')
  if self.backend in ('delta','mysql') and not self.delta_run:raise ValueError('Delta run catalog is required')
  return self

def identifier(value):
 if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',value):raise ValueError('Invalid SQL identifier')
 return '`'+value+'`'
