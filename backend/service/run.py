"""Local/API launcher. MySQL credentials stay only in this process memory."""
import argparse,getpass,sys
from pathlib import Path
from tz_api.settings import Settings
from tz_api.main import create_app

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=['auto','csv','delta','mysql']);ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=8000)
 ap.add_argument('--project-root',type=Path);ap.add_argument('--delta-run',type=Path);ap.add_argument('--analysis-dir',type=Path)
 a=ap.parse_args();s=Settings.from_env()
 if a.backend:s.backend=a.backend
 if a.project_root:s.project=a.project_root
 if a.delta_run:s.delta_run=a.delta_run
 if a.analysis_dir:s.analysis_dir=a.analysis_dir
 s.resolve()
 if s.backend=='mysql' and not s.mysql_password:s.mysql_password=getpass.getpass('MySQL password (typing is hidden): ')
 import uvicorn
 print('Starting read-only '+s.backend+' API; OpenAPI: http://'+a.host+':'+str(a.port)+'/docs',flush=True)
 uvicorn.run(create_app(s),host=a.host,port=a.port,log_level='info')

if __name__=='__main__':main()
