import { adaptB, bParams, snapshot } from './b-contract.js';
import fixture from './fixtures/sample.json' with { type: 'json' };
import { normalizeCRow } from './c-contract.js';

export const mode = import.meta.env?.VITE_DATA_MODE || 'fixture';
const base = (import.meta.env?.VITE_API_BASE_URL || '').replace(/\/$/, '');
const amountFields = ['rev_ytd_amt','op_prft_ytd_amt','net_incm_ytd_amt','op_cf_ytd_amt','frgn_net_buy_qty','inst_net_buy_qty','numerator','denominator'];
const isoDate = value => typeof value==='string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0,10)===value;
export function validate(payload, kind) {
  if (!payload || payload.meta?.schema_version !== 'a-proposal-1' || typeof payload.meta.synthetic !== 'boolean' || !payload.meta.data_end || !payload.meta.calc_version) throw new Error('API 계약/버전 또는 메타데이터가 일치하지 않습니다.');
  if (!Array.isArray(payload.data)) throw new Error('API data는 배열이어야 합니다.');
  payload={...payload,data:payload.data.map(r=>normalizeCRow(r,kind))};
  if (!isoDate(payload.meta.data_end)) throw new Error('데이터 최종일 형식 오류입니다.');
  for (const row of payload.data) {
    if (typeof row.stock_cd !== 'string' || !/^\d{6}$/.test(row.stock_cd)) throw new Error('종목코드는 6자리 문자열이어야 합니다.');
    for (const key of amountFields) if (key in row && row[key] !== null && (typeof row[key] !== 'string' || !/^-?\d+$/.test(row[key]))) throw new Error(`${key}: 정밀도를 보존하는 정수 문자열이 필요합니다.`);
    for (const key of ['revenue_growth_rt','excess_return_rt','frgn_hold_rt','frgn_flow_20d_rt','inst_flow_20d_rt','stock_base100','market_base100']) if (key in row && row[key] !== null && !((typeof row[key]==='number' && Number.isFinite(row[key])) || (typeof row[key]==='string' && /^-?\d+(\.\d+)?$/.test(row[key]) && Number.isFinite(Number(row[key]))))) throw new Error(`${key}: 소수 숫자/문자열 또는 NULL이 필요합니다.`);
    const required = {stocks:['stock_nm','mkt_cd'], compare:['as_of','classification','revenue_growth_rt','excess_return_rt'], daily:['trd_dt','stock_base100','market_base100','frgn_net_buy_qty','inst_net_buy_qty','frgn_hold_rt'], financials:['fin_rpt_id','bsns_yr','rpt_cd','fs_div_cd','period_type','prd_start_dt','prd_end_dt','dscl_dt',...amountFields.slice(0,4)], evidence:['as_of','classification','lineage','calc_status']}[kind] || [];
    if (required.some(key => !(key in row))) throw new Error(`${kind}: 필수 필드가 누락되었습니다.`);
    for(const key of ['as_of','trd_dt','dscl_dt','prd_start_dt','prd_end_dt','observation_start','observation_end']) if(key in row && row[key]!==null && !isoDate(row[key])) throw new Error(`${key}: 날짜 형식 오류입니다.`);
    if (kind === 'evidence' && !Array.isArray(row.lineage)) throw new Error('출처 목록 형식이 잘못되었습니다.');
  }
  return payload;
}
function sample(kind, query) {
  if (query.scenario === 'error') throw new Error('샘플 응답 오류입니다. 다시 시도해 주세요.');
  let data = kind === 'stocks' ? fixture.stocks : kind === 'compare' ? fixture.compare : kind === 'evidence' ? [fixture.evidence[query.stock_cd]].filter(Boolean) : fixture[kind][query.stock_cd] || [];
  if (kind === 'compare') data = data.filter(r => r.as_of === query.as_of && (!query.market || r.mkt_cd === query.market));
  if (kind === 'evidence') data = data.filter(r => r.as_of === query.as_of);
  let meta=fixture.meta;
  if (kind === 'daily') {
    data = data.filter(r => r.trd_dt >= query.start && r.trd_dt <= query.as_of);
    const baseDate=data[0]?.trd_dt;
    data=fixture.price_windows?.[query.stock_cd]?.[baseDate]?.filter(r=>r.trd_dt<=query.as_of) || data;
    meta={...meta,price_base_date:baseDate || null};
  }
  if (kind === 'financials') data = data.filter(r => (query.year === 'all' || r.bsns_yr === query.year) && r.rpt_cd === query.report && r.fs_div_cd === query.basis && r.dscl_dt < query.as_of);
  if (kind !== 'stocks' && query.scenario === 'empty') data = [];
  return {meta, data:structuredClone(data)};
}
export async function request(kind, query = {}, signal) {
  if (mode === 'fixture') {
    await new Promise((resolve, reject) => {
      const id = setTimeout(resolve, 220);
      signal?.addEventListener('abort', () => {clearTimeout(id); reject(new DOMException('Aborted', 'AbortError'));}, {once:true});
    });
    if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    return validate(sample(kind, query), kind);
  }
  if (mode !== 'api' || !base) throw new Error('API 모드와 주소 설정을 확인하세요.');
  const paths = {stocks:'/stocks',compare:'/stocks/compare',daily:`/stocks/${query.stock_cd}/daily`,financials:`/stocks/${query.stock_cd}/financials`,evidence:`/analysis/${query.stock_cd}/evidence`,quality:`/stocks/${query.stock_cd}/quality`};
  const params = bParams(kind,query);
  let result, offset=0;
  do {
    if(offset)params.set('offset',String(offset));
    const response = await fetch(`${base}${paths[kind]}?${params}`, {signal:AbortSignal.any([signal || new AbortController().signal, AbortSignal.timeout(15000)])});
    const body=await response.json().catch(()=>({}));
    if (!response.ok) throw new Error(`${body.error?.code || 'API 요청 실패'} (${response.status}): ${body.error?.message || '다시 시도해 주세요.'}`);
    const page=body.meta?.api_version ? adaptB(body,kind,query) : body;
    if(body.meta?.api_version && ['compare','evidence'].includes(kind) && body.meta.requested_as_of!==query.as_of)throw new Error('요청 기준일 메타데이터가 다릅니다.');
    if(body.meta?.api_version && kind==='financials' && (body.meta.pit_filter_applied!==true || page.data.some(r=>r.pit_join_elig_yn!=='Y')))throw new Error('공시 시점 검증이 적용되지 않았습니다.');
    const checked=kind==='quality'?page:validate(page,kind);
    if(result && snapshot(result.meta)!==snapshot(checked.meta))throw new Error('페이지 간 데이터 버전이 다릅니다.');
    const rows=kind==='quality'?checked.data.issues:checked.data;
    if(result) {if(kind==='quality')result.data.issues.push(...rows);else result.data.push(...rows);} else result=checked;
    offset+=rows.length;
    if(!['stocks','daily','quality'].includes(kind)||!body.meta?.api_version||offset>=body.meta.total)break;
    if(!rows.length||offset>100000)throw new Error('API 페이지가 불완전합니다.');
  }while(true);
  return result;
}
export async function dashboard(query, signal) {
  const kinds = ['compare','daily','financials','evidence'];
  const results = await Promise.all(kinds.map(kind => request(kind, query, signal)));
  let quality=null;
  if(results[0].meta.api_version){quality=await request('quality',query,signal);if(snapshot(quality.meta)!==snapshot(results[0].meta))throw new Error('품질 응답 버전이 다릅니다.');}
  if (new Set(results.map(r => snapshot(r.meta))).size !== 1) throw new Error('응답 간 데이터/계산 버전이 다릅니다.');
  const [, daily, financials, evidence]=results;
  if ([...daily.data,...financials.data,...evidence.data].some(r=>r.stock_cd!==query.stock_cd)) throw new Error('조회 기업과 응답 기업이 다릅니다.');
  if(daily.data.some(r=>r.trd_dt<query.start || r.trd_dt>query.as_of)) throw new Error('조회 기간 밖의 일별 응답입니다.');
  if(financials.data.some(r=>!r.dscl_dt || r.dscl_dt>=query.as_of || r.rpt_cd!==query.report || r.fs_div_cd!==query.basis || (query.year!=='all' && r.bsns_yr!==query.year))) throw new Error('공시 시점 또는 보고서 필터와 응답이 일치하지 않습니다.');
  if([...results[0].data,...evidence.data].some(r=>results[0].meta.api_version ? r.as_of>query.as_of : r.as_of!==query.as_of)) throw new Error('조회 기준일과 응답 기준일이 다릅니다.');
  return {quality:quality?.data,meta:{...results[0].meta,effective_as_of:evidence.meta.effective_as_of,price_base_date:daily.meta.price_base_date}, ...Object.fromEntries(kinds.map((kind,i) => [kind,results[i].data]))};
}

export async function serverExport(kind,q,meta,signal) {
  const names={chart:'chart',daily:'daily',financials:'financials'};
  const path=names[kind]?`/exports/stocks/${q.stock_cd}/${names[kind]}.csv`:`/exports/analysis/${kind}.csv`;
  if(!names[kind]&&!['g_fin_rpt_analysis','g_stock_daily_analysis'].includes(kind))throw new Error('잘못된 내보내기 유형입니다.');
  const checkSnapshot=async()=>{
    const r=await fetch(`${base}/health`,{signal:AbortSignal.any([signal||new AbortController().signal,AbortSignal.timeout(15000)])});
    if(!r.ok)throw new Error(`CSV 버전 확인 실패 (${r.status})`);
    const body=await r.json(),current=adaptB({meta:body.meta,data:[]},'stocks').meta;
    if(snapshot(meta)!==snapshot(current))throw new Error('화면과 CSV 분석 버전이 다릅니다. 다시 조회하세요.');
  };
  await checkSnapshot();
  const params=names[kind]?bParams(kind,q):new URLSearchParams();params.delete('limit');
  const response=await fetch(`${base}${path}?${params}`,{signal:AbortSignal.any([signal||new AbortController().signal,AbortSignal.timeout(30000)])});
  if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(`${body.error?.code} (${response.status}): ${body.error?.message}`);}
  if(response.headers.get('X-Data-Version')!==meta.data_version||response.headers.get('X-API-Version')!==meta.api_version||response.headers.get('X-Analysis-Status')!==meta.analysis_status)throw new Error('화면과 CSV 버전이 다릅니다. 다시 조회하세요.');
  if(kind==='chart'&&(response.headers.get('X-Price-Base-Date')||null)!==meta.price_base_date)throw new Error('화면과 CSV 가격 기준일이 다릅니다.');
  const blob=await response.blob();
  await checkSnapshot();
  return {blob,filename:`${names[kind]?q.stock_cd:kind}-${kind}.csv`};
}
