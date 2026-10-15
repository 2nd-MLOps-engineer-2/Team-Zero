from __future__ import annotations
import csv,io,logging
from datetime import date
from enum import Enum
from fastapi import FastAPI,HTTPException,Query,Path as ApiPath,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse,Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from .models import Envelope,Stock,Daily,Financial,Evidence,ErrorEnvelope
from .repository import Repository
from .settings import Settings

class Market(str,Enum):
 KOSPI='KOSPI'
 KOSDAQ='KOSDAQ'
class ReportCode(str,Enum):
 ANNUAL='11011'
 HALF='11012'
 Q1='11013'
 Q3='11014'
class FsDivision(str,Enum):
 CFS='CFS'
 OFS='OFS'
class AnalysisTable(str,Enum):
 FINANCIAL='g_fin_rpt_analysis'
 DAILY='g_stock_daily_analysis'

def create_app(settings=None,repository=None):
 settings=settings or Settings.from_env()
 repo=repository or Repository(settings).warm()
 api=FastAPI(title='TEAM ZERO API',version='1.0.0',description='기업 실적·현금흐름·수급·주가 조회. 금액·수량·비율은 정밀도 보존 문자열.',
  responses={code:{'model':ErrorEnvelope} for code in (404,409,422,503)})
 api.state.repo=repo
 api.add_middleware(CORSMiddleware,allow_origins=list(repo.settings.cors_origins),allow_credentials=False,
  allow_methods=['GET'],allow_headers=['Accept','Content-Type'],expose_headers=['Content-Disposition','X-Data-Version','X-API-Version','X-Analysis-Status'])

 @api.middleware('http')
 async def version_headers(request,call_next):
  response=await call_next(request)
  response.headers['X-API-Version']='1.0.0';response.headers['X-Data-Version']=repo.data_version
  response.headers['X-Analysis-Status']='AVAILABLE' if repo.analysis else 'PENDING_C_DELIVERY'
  response.headers['Cache-Control']='no-store'
  return response

 @api.exception_handler(HTTPException)
 @api.exception_handler(StarletteHTTPException)
 async def http_error(request,exc):
  detail=exc.detail if isinstance(exc.detail,dict) else dict(code='REQUEST_ERROR',message=str(exc.detail))
  return JSONResponse(status_code=exc.status_code,content=dict(error=detail,meta=repo.metadata()))

 @api.exception_handler(RequestValidationError)
 async def validation_error(request,exc):
  errors=[dict(field='.'.join(map(str,e['loc'])),message=e['msg'],type=e['type']) for e in exc.errors()]
  return JSONResponse(status_code=422,content=dict(error=dict(code='VALIDATION_ERROR',message='조회 조건을 확인하세요.',details=errors),meta=repo.metadata()))

 @api.exception_handler(ValueError)
 @api.exception_handler(OSError)
 async def source_error(request,exc):
  logging.getLogger('tz_api').error('Read-only data source failed',exc_info=exc)
  return JSONResponse(status_code=503,content=dict(error=dict(code='DATA_SOURCE_UNAVAILABLE',message='검증된 데이터 원본을 읽을 수 없습니다.'),meta=repo.metadata()))

 def fail(code,message,status=422):raise HTTPException(status,dict(code=code,message=message))
 def stock(code):
  if code not in repo.stocks:fail('STOCK_NOT_FOUND','제공 범위에 없는 종목입니다.',404)
  return repo.stocks[code]
 def asof(value):
  v=value.isoformat() if value else repo.max_date
  if not repo.min_date<=v<=repo.max_date:fail('AS_OF_OUT_OF_RANGE',f'기준일은 {repo.min_date}부터 {repo.max_date}까지 선택하세요.')
  return v
 def window(start,end):
  lo=start.isoformat() if start else repo.min_date;hi=end.isoformat() if end else repo.max_date
  if lo>hi:fail('INVALID_DATE_RANGE','시작일은 종료일보다 늦을 수 없습니다.')
  return lo,hi
 def envelope(data,**meta):return dict(data=data,meta=repo.metadata(**meta))
 def daily_rows(code,start,end):
  stock(code);lo,hi=window(start,end)
  return [r for r in repo.daily.get(code,[]) if lo<=r['trd_dt']<=hi],lo,hi
 def report_rows(code,year,rpt,fs,as_of):
  stock(code);corp=repo.mapping[code]['corp_cd'];rows=[]
  effective=asof(as_of) if as_of else None
  for report in repo.reports.values():
   if report['corp_cd']!=corp:continue
   if year is not None and report['bsns_yr']!=str(year):continue
   if rpt is not None and report['rpt_cd']!=rpt.value:continue
   if fs is not None and report['fs_div_cd']!=fs.value:continue
   dscl=repo.disclosures.get(report['rcept_no'])
   if effective and (report['pit_join_elig_yn']!='Y' or not dscl or dscl['rcept_dt']>=effective):continue
   rows.append(report)
  return sorted(rows,key=lambda r:(r['bsns_yr'],r['prd_end_dt'],r['fs_div_cd'],r['fin_rpt_id']),reverse=True)
 def csv_response(rows,filename,headers=None):
  out=io.StringIO(newline='');fields=headers or list(rows[0]) if rows else (headers or [])
  w=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
  return Response(content=out.getvalue().encode('utf-8-sig'),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="{filename}"'})

 @api.get('/health',tags=['status'])
 def health():return envelope(dict(status='ok',read_only=True,analysis_available=bool(repo.analysis)))

 @api.get('/stocks',tags=['stocks'],response_model=Envelope[list[Stock]])
 def stocks(market:Market|None=None,q:str|None=Query(None,max_length=100),limit:int=Query(100,ge=1,le=100),offset:int=Query(0,ge=0)):
  rows=[r for r in repo.stocks.values() if (not market or r['mkt_cd']==market.value) and (not q or q.casefold() in (r['stock_cd']+' '+r['stock_nm']).casefold())]
  rows.sort(key=lambda r:r['stock_cd'])
  return envelope(rows[offset:offset+limit],total=len(rows),limit=limit,offset=offset)

 @api.get('/stocks/compare',tags=['stocks'],response_model=Envelope[list[Daily]])
 def compare(as_of:date|None=None,market:Market|None=None):
  day=asof(as_of);rows=[]
  for code,s in sorted(repo.stocks.items()):
   if market and s['mkt_cd']!=market.value:continue
   row=repo.latest(code,day)
   if row:rows.append(repo.annotated_daily(row))
  return envelope(rows,requested_as_of=day,total=len(rows),selection_rule='last_observation_on_or_before_as_of')

 @api.get('/stocks/{code}',tags=['stocks'])
 def stock_detail(code:str=ApiPath(pattern=r'^\d{6}$')):
  return envelope(dict(stock=stock(code),corporation_mapping=repo.mapping.get(code)))

 @api.get('/stocks/{code}/daily',tags=['daily'],response_model=Envelope[list[Daily]])
 def daily(code:str=ApiPath(pattern=r'^\d{6}$'),start:date|None=None,end:date|None=None,
  limit:int=Query(1000,ge=1,le=5000),offset:int=Query(0,ge=0)):
  rows,lo,hi=daily_rows(code,start,end)
  return envelope([repo.annotated_daily(r) for r in rows[offset:offset+limit]],start=lo,end=hi,total=len(rows),limit=limit,offset=offset)

 @api.get('/stocks/{code}/financials',tags=['financials'],response_model=Envelope[list[Financial]])
 def financials(code:str=ApiPath(pattern=r'^\d{6}$'),year:int|None=Query(None,ge=1900,le=2100),
  report_code:ReportCode|None=None,fs_div:FsDivision|None=None,as_of:date|None=None):
  rows=report_rows(code,year,report_code,fs_div,as_of)
  return envelope([repo.financial(r) for r in rows],total=len(rows),pit_filter_applied=as_of is not None,
   period_summary_scope='descriptive_report_period; full_cvrg_yn is global_price_range_only')

 @api.get('/stocks/{code}/quality',tags=['quality'])
 def quality(code:str=ApiPath(pattern=r'^\d{6}$'),start:date|None=None,end:date|None=None,
  limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
  stock(code);lo,hi=window(start,end);corp=repo.mapping[code]['corp_cd']
  report_ids={r['fin_rpt_id'] for r in repo.reports.values() if r['corp_cd']==corp}
  direct=[];general=[]
  for issue in repo.rows('s_dq_issue'):
   key=issue.get('rcrd_key_txt') or ''
   if key in report_ids or key.startswith(code+'|') or key==repo.mapping[code]['map_id']:direct.append(issue)
   elif key.startswith('stmt='):general.append(issue)
  direct.sort(key=lambda r:r['issue_id']);general.sort(key=lambda r:r['issue_id'])
  availability=[r for (sc,day),r in sorted(repo.connection.items()) if sc==code and lo<=day<=hi]
  return envelope(dict(availability=availability,issues=direct[offset:offset+limit],global_statement_issues=general),
   total=len(direct),limit=limit,offset=offset,start=lo,end=hi,issue_time_scope='report_or_stock; detection_time_not_supplied')

 @api.get('/analysis/{code}/evidence',tags=['evidence'],response_model=Envelope[Evidence])
 def evidence(code:str=ApiPath(pattern=r'^\d{6}$'),as_of:date|None=None):
  stock(code);day=asof(as_of);row=repo.latest(code,day)
  if not row:fail('NO_OBSERVATION','해당 기준일까지 가격 관측이 없습니다.',404)
  report=repo.reports.get(row['fin_rpt_id']);price=next(r for r in repo.rows('s_stock_daily_prc') if r['stock_cd']==code and r['trd_dt']==row['trd_dt'])
  sources={k:v for k,v in price.items() if k.startswith(('src_','api_')) or k in ('bronze_row_no','fetch_dttm','pipln_ver')}
  return envelope(dict(observation=repo.annotated_daily(row),financial_report=repo.financial(report) if report else None,
   price_source=sources,pit_rule='disclosure_date < trade_date; latest eligible business period; same-day excluded',
   analysis_status='AVAILABLE' if repo.analysis else 'PENDING_C_DELIVERY'),requested_as_of=day,effective_as_of=row['trd_dt'])

 @api.get('/exports/stocks/{code}/daily.csv',tags=['exports'],response_class=Response,responses={200:{'content':{'text/csv':{'schema':{'type':'string'}}}}})
 def export_daily(code:str=ApiPath(pattern=r'^\d{6}$'),start:date|None=None,end:date|None=None):
  rows,_,_=daily_rows(code,start,end)
  fields=list(next(iter(repo.daily.values()))[0])
  return csv_response(rows,code+'_daily.csv',fields)

 @api.get('/exports/stocks/{code}/financials.csv',tags=['exports'],response_class=Response,responses={200:{'content':{'text/csv':{'schema':{'type':'string'}}}}})
 def export_financials(code:str=ApiPath(pattern=r'^\d{6}$'),year:int|None=Query(None,ge=1900,le=2100),
  report_code:ReportCode|None=None,fs_div:FsDivision|None=None,as_of:date|None=None):
  reports=report_rows(code,year,report_code,fs_div,as_of);rows=[]
  header=list(next(iter(repo.reports.values())))+['dscl_dt','mtrc_cd','prd_type_cd','mtrc_amt','src_col_nm']
  for r in reports:
   dscl=repo.disclosures.get(r['rcept_no'])
   for m in sorted(repo.metrics.get(r['fin_rpt_id'],[]),key=lambda m:(m['mtrc_cd'],m['prd_type_cd'])):
    rows.append(dict(r,dscl_dt=dscl['rcept_dt'] if dscl else None,**{k:m[k] for k in ['mtrc_cd','prd_type_cd','mtrc_amt','src_col_nm']}))
  return csv_response(rows,code+'_financial_metrics.csv',header)

 @api.get('/exports/analysis/{table}.csv',tags=['exports'],response_class=Response,responses={200:{'content':{'text/csv':{'schema':{'type':'string'}}}}})
 def export_analysis(table:AnalysisTable):
  if not repo.analysis:fail('ANALYSIS_NOT_AVAILABLE','신규 Gold 계산 결과가 아직 전달되지 않았습니다.',409)
  rows=list(repo.analysis['financial' if table==AnalysisTable.FINANCIAL else 'daily'].values())
  fields=[c['name'] for c in repo.analysis['entries'][table.value]['columns']]
  return csv_response(rows,table.value+'.csv',fields)

 return api
