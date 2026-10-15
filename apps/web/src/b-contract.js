import { normalizeCRow, stateLabel } from './c-contract.js';

// B 1.1 representation adapter. Monetary values and C calculations stay unchanged.
export function bParams(kind, q = {}) {
  const values = kind === 'stocks' ? {limit:100} : kind === 'compare' ? {as_of:q.as_of,market:q.market}
    : ['daily','quality','chart'].includes(kind) ? {start:q.start,end:q.as_of,...(kind==='daily'?{limit:5000}:kind==='quality'?{limit:500}:{})}
    : kind === 'financials' ? {year:q.year==='all'?undefined:q.year,report_code:q.report,fs_div:q.basis,as_of:q.as_of}
    : {as_of:q.as_of};
  return new URLSearchParams(Object.entries(values).filter(([,v])=>v!==undefined&&v!==''));
}
export const snapshot = m => JSON.stringify(['schema_version','api_version','synthetic','data_end','input_version','calc_version','data_version','analysis_data_version','analysis_status'].map(k=>m[k]));
const metric = (r,code,period='YTD') => r?.metrics?.find(m=>m.mtrc_cd===code&&m.prd_type_cd===period)?.mtrc_amt ?? null;
function observation(r, kind) {
  if (!r || !r.trd_dt) throw new Error('B 관측 응답이 누락되었습니다.');
  if(r.analysis && (r.analysis.stock_cd!==r.stock_cd || r.analysis.trd_dt!==r.trd_dt)) throw new Error('C 분석과 B 관측 키가 다릅니다.');
  return normalizeCRow({...r,...r.analysis,
    classification:r.analysis?stateLabel(r.analysis.co_move_cd):'C 분석 미연결',
    calc_status:r.analysis?stateLabel(r.analysis.co_move_stts_cd):'PENDING_C_DELIVERY',
    revenue_growth_rt:r.analysis?.rev_yoy_rt??null,excess_return_rt:r.analysis?.event_excess_rt??null,
    status:r.connection?.conn_stts_cd??null,reason:r.connection?.miss_rsn_txt??null},kind);
}
function financial(r,q) {
  const stock=r.analysis?.stock_cd??r.period_market_summary?.stock_cd??q.stock_cd;
  if(r.analysis && r.analysis.fin_rpt_id!==r.fin_rpt_id) throw new Error('재무 분석 보고서 키가 다릅니다.');
  return {...r,stock_cd:stock,period_type:'YTD',period_status:`재무 ${r.cal_prd_stts_cd??'미제공'} / CF ${r.cf_prd_stts_cd??'미제공'}`,
    rev_ytd_amt:metric(r,'REVENUE'),op_prft_ytd_amt:metric(r,'OPERATING_PROFIT'),net_incm_ytd_amt:metric(r,'NET_INCOME'),op_cf_ytd_amt:metric(r,'OPERATING_CASH_FLOW')};
}
export function adaptB(payload,kind,q={}) {
  const m=payload?.meta;
  if(m?.api_version!=='1.1.0'||m.synthetic!==false||!m.data_version||!m.input_version||!m.calculation_version||!['AVAILABLE','PENDING_C_DELIVERY'].includes(m.analysis_status)) throw new Error('지원하는 B API 1.1.0 메타데이터가 아닙니다.');
  if(m.analysis_status==='AVAILABLE'&&!m.analysis_data_version) throw new Error('C 산출물 버전이 없습니다.');
  const meta={...m,schema_version:'a-proposal-1',data_end:m.data_final_date,calc_version:m.calculation_version};
  let data=payload.data;
  if(kind==='quality') {
    if(!data || !['availability','issues','global_statement_issues'].every(k=>Array.isArray(data[k]))) throw new Error('품질 응답 형식이 잘못되었습니다.');
    return {meta,data};
  }
  if(kind==='evidence') {
    const r=observation(data.observation,'evidence'),f=data.financial_report,s=data.price_source??{};
    data=[{...r,formula:'C 제공 성장률 = (당기 YTD − 전년동기 YTD) / 전년동기 YTD. 화면에서 재계산하지 않습니다.',numerator:null,denominator:metric(f,'REVENUE','PRIOR_YTD'),threshold:'0 (C 분류 기준)',review:r.review_required_yn??'미제공',
      lineage:[{layer:'Bronze 출처 메타',status:'원본 파일 미확보',file:s.src_file_path,row:s.bronze_row_no,key:s.api_rcrd_path,version:s.src_ver,reason:'API의 출처 기록이며 원본 열람 검증은 미완료'},
        {layer:'Silver 가격',status:r.status,file:s.src_file_path,row:s.src_row_no,key:`${r.stock_cd}|${r.trd_dt}`,version:s.pipln_ver,reason:r.reason??'연결 상태 제공'},
        {layer:'Silver 재무',status:f?.cal_prd_stts_cd??'미연결',file:f?.src_file_path,row:f?.src_row_no,key:f?.fin_rpt_id,version:f?.src_ver,reason:`CF ${f?.cf_prd_stts_cd??'미제공'} / 동기간 ${f?.same_prd_cmpr_elig_yn??'미제공'}`},
        {layer:'Gold 분석',status:m.analysis_status,key:r.fin_rpt_id,version:m.analysis_data_version,reason:data.pit_rule}],
      raw_evidence:data}];
  } else {
    if(!Array.isArray(data)) throw new Error('B 목록 응답 형식이 잘못되었습니다.');
    data=data.map(r=>kind==='financials'?financial(r,q):['compare','daily'].includes(kind)?observation(r,kind):r);
  }
  return {meta,data};
}
