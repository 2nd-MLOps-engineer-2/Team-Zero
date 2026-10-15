"""Launch a real local HTTP process, inspect actual endpoints, stop only that child."""
import argparse,datetime,json,os,subprocess,sys,time,uuid
from pathlib import Path
import httpx
from tz_api.settings import Settings

def run(project,port=18000,backend='auto',fixtures=None):
 output=project/'build/api_http'/ (datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:4])
 output.mkdir(parents=True,exist_ok=False)
 checks=[('health','/health',200),('stocks','/stocks',200),('compare','/stocks/compare?as_of=2026-06-30',200),
  ('daily','/stocks/005930/daily?start=2026-06-30&end=2026-06-30',200),
  ('financials','/stocks/005930/financials?year=2025&report_code=11011',200),
  ('missing_investor','/stocks/247540/daily?start=2026-04-16&end=2026-04-16',200),
  ('evidence','/analysis/005930/evidence?as_of=2026-06-30',200),
  ('csv','/exports/stocks/005930/daily.csv?start=2026-06-30&end=2026-06-30',200),
  ('invalid_date','/stocks/005930/daily?start=2026-02-30',422),
  ('unknown_stock','/stocks/999999/daily',404),
  ('missing_analysis','/exports/analysis/g_stock_daily_analysis.csv',409),
  ('openapi','/openapi.json',200),('docs','/docs',200)]
 command=[sys.executable,'-X','utf8',str(Path(__file__).with_name('run.py')),'--project-root',str(project),'--backend',backend,'--port',str(port)]
 results=[];samples={}
 with (output/'server.log').open('w',encoding='utf-8') as log:
  process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  try:
   with httpx.Client(base_url=f'http://127.0.0.1:{port}',trust_env=False,timeout=30) as client:
    for _ in range(45):
     if process.poll() is not None:raise RuntimeError('API process exited; see server.log')
     try:
      if client.get('/health',timeout=1).status_code==200:break
     except httpx.HTTPError:pass
     time.sleep(.5)
    else:raise RuntimeError('API startup timed out')
    for name,url,status in checks:
     r=client.get(url)
     if r.status_code!=status:raise AssertionError(name+': unexpected HTTP status '+str(r.status_code))
     results.append(dict(name=name,request=url,http_status=r.status_code,status='PASS'))
     if r.headers.get('content-type','').startswith('application/json'):samples[name]=r.json()
   report=dict(status='PASS',transport='real HTTP over loopback',source_backend=samples['health']['meta']['source_backend'],checks=results,
    child_process_stopped=True,data_version=samples['health']['meta']['data_version'])
   (output/'http_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
   if fixtures:
    fixtures.mkdir(parents=True,exist_ok=True)
    for name in ['health','stocks','daily','financials','missing_investor','evidence','invalid_date','unknown_stock']:
     obj=dict(fixture_source='actual_provided_handoff_or_matching_Delta; not synthetic',request=next(url for n,url,_ in checks if n==name),response=samples[name])
     (fixtures/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    (fixtures/'openapi.json').write_text(json.dumps(samples['openapi'],ensure_ascii=False,indent=2),encoding='utf-8')
   print(json.dumps(report,ensure_ascii=False,indent=2));print('Evidence:',output)
   return report,output
  finally:
   if process.poll() is None:
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--project-root',type=Path,default=Settings().project);ap.add_argument('--port',type=int,default=18000)
 ap.add_argument('--backend',choices=['csv','delta','auto'],default='auto');ap.add_argument('--fixtures',type=Path);a=ap.parse_args()
 run(a.project_root.resolve(),a.port,a.backend,a.fixtures)
