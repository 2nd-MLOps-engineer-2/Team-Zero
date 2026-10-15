import './style.css';
import { mode, request, dashboard, serverExport } from './api.js';
import { integer, ratio, escape as e } from './format.js';
import { chart, scatter, bindCharts } from './charts.js';
import { stateLabel, jointLabel } from './c-contract.js';
import { download } from './export.js';

const app=document.querySelector('#app');
let stocks=[], data=null, activeQuery=null, controller=null;
const options=(pairs)=>pairs.map(([value,label])=>`<option value="${e(value)}">${e(label)}</option>`).join('');
app.innerHTML=`<header><a class="brand" href="#"><b>ZERO<span>↗</span></b><small>기업의 흐름을 읽다</small></a><nav aria-label="주요 영역"><a href="#comparison">종목 비교</a><a href="#detail">기업 상세</a><a href="#evidence">분석 근거</a></nav><span class="badge">${mode==='fixture'?'합성 샘플 모드':'API 연결 모드'}</span></header>
<aside class="report-sidebar" aria-label="리포트 탐색"><div class="sidebar-company"><span class="company-monogram">Z</span><strong id="sidebar-name">기업 리포트</strong><small id="sidebar-code">TEAM ZERO · KOREA</small></div><p class="eyebrow">COMPANY REPORT</p><nav aria-label="리포트 목차"><a href="#company-summary">기업 개요 <span>↗</span></a><a href="#price-report"><em>01</em> 주가와 시장</a><a href="#financial-report"><em>02</em> 실적과 현금흐름</a><a href="#flow-report"><em>03</em> 투자자 수급</a><a href="#comparison"><em>04</em> 종목 비교</a><a href="#evidence"><em>05</em> 판단 근거</a></nav><div class="sidebar-foot"><span class="live-dot"></span> 검증된 스냅샷<br><small>20개 기업 · 2026.06.30까지</small><p>실적과 시장의 관계를<br>데이터로 탐색합니다.</p></div></aside>
<main><div class="intro"><div><p class="eyebrow">TEAM ZERO / MARKET EXPLORER</p><h1>기업 분석 리포트</h1><p>실적에서 시장 반응까지, 기업의 흐름을 한눈에 살펴보세요.</p></div><div class="scope">보유 <b>20</b> 종목<br><small>기준 데이터 최종일 2026.06.30</small></div></div>
<aside class="notice">${mode==='fixture'?'샘플 안내 · 종목명과 코드는 제공 자료를 사용하며, 모든 분석 수치는 합성 예시입니다. 비교·근거는 2026-06-30, 추이는 6월의 6개 샘플 관측점, 재무는 2024·2025 연간 연결 YTD를 제공합니다.':'실제 API 응답의 출처·버전을 확인해 주세요. 연결 실패 시 샘플로 대체하지 않습니다.'}</aside>
<form id="filters" class="panel filters">
<label>시장<select name="market">${options([['','전체 시장'],['KOSPI','KOSPI'],['KOSDAQ','KOSDAQ']])}</select></label>
<label>기업<select name="stock_cd" required aria-label="기업"><option value="">불러오는 중</option></select></label>
<label>주가 조회 시작<input name="start" type="date" value="2026-06-01" min="2022-12-01" max="2026-06-30" required></label>
<label>기준일<input name="as_of" type="date" value="2026-06-30" min="2022-12-01" max="2026-06-30" required></label>
<label>사업연도<select name="year">${options([['all','전체 연도'],['2025','2025'],['2024','2024'],['2023','2023'],['2022','2022']])}</select></label>
<label>보고서<select name="report">${options([['11011','사업보고서'],['11012','반기보고서'],['11013','1분기보고서'],['11014','3분기보고서']])}</select></label>
<label>재무제표<select name="basis">${options([['CFS','연결'],['OFS','별도']])}</select></label>
${mode==='fixture'?`<label>샘플 응답<select name="scenario">${options([['normal','정상'],['empty','빈 결과'],['error','오류']])}</select></label>`:''}
<button type="submit" id="submit">조회하기 <span>↗</span></button></form>
<div class="resultbar"><p id="status" role="status" aria-live="polite">종목 목록을 불러오는 중입니다.</p><button id="export" class="secondary" disabled>CSV 다운로드 ↓</button></div>
<div id="results" aria-busy="true"></div><details id="server-exports" class="panel export-panel" hidden><summary>데이터 내보내기 · 서버 CSV</summary><label>서버 CSV 종류 <select id="csv-kind">${options([['chart','화면 주가 차트 · 선택 기간'],['daily','기존 Gold 일별 · 선택 기간'],['financials','재무 지표 · 선택 보고서 조건'],['g_fin_rpt_analysis','C 재무 분석 · 전체 20종목'],['g_stock_daily_analysis','C 일별 분석 · 전체 20종목']])}</select></label> <button id="server-export" class="secondary">서버 CSV 다운로드</button><p class="muted">상단 CSV는 화면 표시값입니다. C 분석 CSV는 전체 자료이며 기업·기간 필터가 적용되지 않습니다.</p><p id="export-status" role="status"></p></details><footer>2026-06-30까지의 보유 20종목 범위 · 제공 종가 기준 · 동행·괴리는 인과관계나 매매 추천이 아닙니다.</footer></main>`;
const form=document.querySelector('#filters'), results=document.querySelector('#results'), status=document.querySelector('#status'), exportButton=document.querySelector('#export');
const fields=form.elements;
function populateStocks(){
  const selected=fields.stock_cd.value;
  fields.stock_cd.innerHTML=options(stocks.filter(s=>!fields.market.value || s.mkt_cd===fields.market.value).map(s=>[s.stock_cd,`${s.stock_nm} · ${s.stock_cd}`]));
  if([...fields.stock_cd.options].some(o=>o.value===selected))fields.stock_cd.value=selected;
}
const empty='<p class="empty">조회 결과가 없습니다. 기간·보고서·재무제표 조건을 확인하세요.</p>';
function table(headers, rows){return `<div class="table-scroll" tabindex="0"><table><thead><tr>${headers.map(h=>`<th scope="col">${e(h)}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;}
function cell(value){return `<td>${e(value)}</td>`;}
function rangeStart(end,days){
 if(days==='all')return '2022-12-01';
 const date=new Date(end+'T00:00:00Z');date.setUTCDate(date.getUTCDate()-Number(days)+1);
 return [date.toISOString().slice(0,10),'2022-12-01'].sort().at(-1);
}
function render(d,q){
  const financials=[...d.financials].sort((a,b)=>(a.prd_end_dt||'').localeCompare(b.prd_end_dt||''));
  const latest=financials.at(-1), stock=stocks.find(s=>s.stock_cd===q.stock_cd), ev=d.evidence[0];
  const metrics=[['rev_ytd_amt','매출'],['op_prft_ytd_amt','영업이익'],['net_incm_ytd_amt','순이익'],['op_cf_ytd_amt','영업현금흐름']];
  results.innerHTML=`<section id="comparison" class="panel"><div class="section-head"><div><p class="eyebrow">04 / PEER COMPARISON</p><h2>실적과 시장의 동행·괴리</h2></div><span>요청 ${e(q.as_of)} · 실제 관측 ${e(d.meta.effective_as_of||q.as_of)} · ${d.compare.length}개 종목</span></div><p class="muted">매출 전년동기 성장률(%)과 공시 후 시장 대비 성과(%p). 서로 다른 공시 경과 기간에 유의하세요.</p>
${d.compare.length?scatter(d.compare,q.stock_cd):''}${d.compare.length?table(['기업 / 상세 보기','매출 성장률','시장 대비 성과','분류','공시일 · 경과일','관측 구간'],d.compare.map(r=>`<tr><td><button class="text-button" data-stock="${e(r.stock_cd)}">${e(r.stock_nm)} <small>${e(r.stock_cd)}</small></button></td>${cell(ratio(r.revenue_growth_rt))}${cell(ratio(r.excess_return_rt,'%p'))}${cell(r.classification)}${cell(`${r.dscl_dt || '미제공'} · ${r.dscl_elps_day_cnt ?? '미제공'}일`)}${cell(`${r.observation_start || '미제공'} ~ ${r.observation_end || '미제공'}`)}</tr>`)):empty}</section>
<section id="detail"><div class="section-head"><div><p class="eyebrow">FINANCIAL SNAPSHOT</p><h2>${e(stock?.stock_nm)} <small>${e(q.stock_cd)}</small></h2></div><span>${e(q.basis==='CFS'?'연결':'별도')} · ${e(q.year==='all'?'연도 비교':q.year)}</span></div>
<div class="cards">${metrics.map(([key,label])=>`<article class="panel metric"><p>${label}</p><strong>${integer(latest?.[key])}</strong><small>${latest?`${e(latest.prd_start_dt)} ~ ${e(latest.prd_end_dt)} · ${e(latest.period_type)}`:'보고서 없음'}</small><span class="muted">${e(latest?.period_status || '미연결')}${latest?.[key]===null?` · ${e(latest.reason||'원천 NULL 유지')}`:''}</span></article>`).join('')}</div>
<div class="grid"><article class="panel chart-panel wide" id="price-report"><div class="chart-heading"><div><p class="eyebrow">01 / PRICE PERFORMANCE</p><h3>주가와 시장 추이</h3></div><div class="range-buttons" aria-label="주가 조회 기간">${[[30,"1M"],[90,"3M"],[365,"1Y"],["all","전체"]].map(([days,label])=>`<button type="button" data-range="${days}" aria-pressed="${q.start===rangeStart(q.as_of,days)}" title="${days==='all'?'보유 전체 기간':'최근 '+days+'일'}">${label}</button>`).join('')}</div></div><p class="muted">${e(d.meta.price_base_date || '기준일 미제공')} = 100 · 제공된 기준값 · 가로축: 관측일<br>조회 구간 첫 유효 관측 기준 · B/C가 제공한 기준값을 표시합니다.</p>${chart(d.daily,[{key:'stock_base100',label:'종목'},{key:'market_base100',label:'시장'}],'trd_dt','기준값','종목과 시장 기준값 추이')}</article>
<article class="panel chart-panel wide" id="financial-report"><p class="eyebrow">02 / FINANCIAL PERFORMANCE</p><h3>실적과 현금흐름</h3><p class="muted">가로축: 보고기간 종료일 · 같은 보고서 유형의 YTD / ${q.basis==='CFS'?'연결':'별도'}<br>재무 수치를 일별로 반복 합산하지 않습니다.</p>${chart(financials,metrics.map(([key,label])=>({key,label,scale:1e12,rawUnit:'원'})),'prd_end_dt','조 원','연간 실적과 현금흐름 비교',{type:'bar'})}</article>
<article class="panel chart-panel wide" id="flow-report"><p class="eyebrow">03 / INVESTOR FLOWS</p><h3>외국인·기관 순매수</h3><p class="muted">가로축: 관측일 · 일별 수량(주), 기관 합계만 표시<br>NULL 구간은 연결하거나 0으로 채우지 않습니다.</p>${chart(d.daily,[{key:'frgn_net_buy_qty',label:'외국인'},{key:'inst_net_buy_qty',label:'기관 합계'}],'trd_dt','주','일별 외국인 기관 순매수',{type:'bar'})}</article>
<article class="panel chart-panel"><h3>20관측 수급 비율</h3><p class="muted">외국인·기관의 최근 20관측 순매수 수량 / 같은 기간 거래량 · 단위 %<br>수량·금액·보유율과 별개이며 C 제공 비율을 표시합니다.</p>${chart(d.daily,[{key:'frgn_flow_20d_rt',label:'외국인 20관측',scale:.01,rawUnit:'소수 비율'},{key:'inst_flow_20d_rt',label:'기관 20관측',scale:.01,rawUnit:'소수 비율'}],'trd_dt','%','외국인 기관 20관측 순매수 비율')}</article><article class="panel chart-panel"><h3>외국인 보유율</h3><p class="muted">가로축: 관측일 · 소수 비율을 %로 표시<br>순매수 수량과 보유 비율을 구분합니다.</p>${chart(d.daily,[{key:'frgn_hold_rt',label:'외국인 보유율',scale:.01,rawUnit:'소수 비율'}],'trd_dt','%','외국인 보유율 추이')}</article></div>
<details id="raw-values" class="panel"><summary>차트 원값 · 재무 보고서 확인</summary><h3>일별 값</h3>${d.daily.length?table(['거래일','종목 기준값','시장 기준값','외국인 순매수(주)','기관 순매수(주)','외국인 보유율','외국인 20관측 비율','기관 20관측 비율','수급 비율 상태','상태 / 사유'],d.daily.map(r=>`<tr>${cell(r.trd_dt)}${cell(r.stock_base100??'미제공 (NULL)')}${cell(r.market_base100??'미제공 (NULL)')}${cell(integer(r.frgn_net_buy_qty,'주'))}${cell(integer(r.inst_net_buy_qty,'주'))}${cell(ratio(r.frgn_hold_rt))}${cell(ratio(r.frgn_flow_20d_rt))}${cell(ratio(r.inst_flow_20d_rt))}${cell(`${stateLabel(r.frgn_flow_20d_stts_cd)} / ${stateLabel(r.inst_flow_20d_stts_cd)}`)}${cell(`${r.status || '미제공'} ${r.reason || ''}`)}</tr>`)):empty}<h3>보고서별 원 단위 값</h3>${financials.length?table(['보고서 / 공시일','기간 유형 / 검증','매출','영업이익','순이익','영업CF'],financials.map(r=>`<tr>${cell(`${r.fin_rpt_id} / ${r.dscl_dt}`)}${cell(`${r.prd_start_dt} ~ ${r.prd_end_dt} / ${r.period_type} / ${r.period_status || '미제공'}`)}${metrics.map(([key])=>cell(integer(r[key]))).join('')}</tr>`)):empty}</details></section>
<section id="evidence" class="panel"><div class="section-head"><div><p class="eyebrow">05 / EVIDENCE</p><h2>판단의 근거를 확인하세요</h2></div><span class="badge">${e(ev?.calc_status || '미연결')}</span></div>${ev?`<h3>${e(ev.classification)}</h3><p>복합 동반 개선: <b>${e(jointLabel(ev.joint_improve_yn))}</b> · ${e(stateLabel(ev.joint_improve_stts_cd))}</p><p class="muted">매출 성장·공시 후 초과성과·영업CF 차분·외국인/기관 20관측 순매수가 모두 양수일 때 Y, 판단 가능한 조건 중 미충족이 있으면 N, 필요한 값이 없으면 판단 불가입니다. 2축 분류와 별개입니다.</p><p>매출 성장률 <b>${ratio(ev.revenue_growth_rt)}</b> · 공시 후 시장 대비 성과 <b>${ratio(ev.excess_return_rt,'%p')}</b></p><p>${e(ev.formula)}</p><dl><dt>보고서 / 공시일</dt><dd>${e(ev.fin_rpt_id)} / ${e(ev.dscl_dt)}</dd><dt>공시 후 성과 관측 구간</dt><dd>${e(ev.observation_start)} ~ ${e(ev.observation_end)}</dd><dt>성장률 분자 / 분모</dt><dd>${integer(ev.numerator)} / ${integer(ev.denominator)}</dd><dt>임계값 / 추가 검토</dt><dd>${e(ev.threshold)} / ${e(ev.review)}</dd></dl><h3>레이어별 품질·출처</h3>${table(['레이어','상태','파일 / 행','키','버전','사유'],ev.lineage.map(r=>`<tr>${cell(r.layer)}${cell(r.status)}${cell(`${r.file ?? '미제공'} / ${r.row ?? '미제공'}`)}${cell(r.key??'미제공')}${cell(r.version??'미제공')}${cell(r.reason)}</tr>`))}`:empty}<p class="metadata">${e(d.meta.synthetic?'합성 데이터':'API 데이터')} · API ${e(d.meta.api_version||'샘플 계약')} · 분석 ${e(d.meta.analysis_status||'합성 예시')} · 입력 ${e(d.meta.input_version)} · 계산 ${e(d.meta.calc_version)} · 최종일 ${e(d.meta.data_end)}</p></section>`;
  results.prepend(results.querySelector('#detail'));
  const observation=ev||d.daily.at(-1),close=observation?.close_prc;
  const price=close==null?'미제공':e(String(close).replace(/\.0+$/,'').replace(/\B(?=(\d{3})+(?!\d))/g,','))+' 원';
  results.insertAdjacentHTML('afterbegin',`<section id="company-summary" class="company-overview panel"><div class="company-heading"><div><p class="eyebrow">${e(stock?.mkt_cd)} : ${e(q.stock_cd)} / COMPANY OVERVIEW</p><h2>${e(stock?.stock_nm)}<span class="report-pill">${e(d.meta.synthetic?'합성 샘플':'기업 리포트')}</span></h2><p>${e(ev?.classification||'분석 결과 미제공')}</p></div><div class="closing-price"><small>기준일 종가 · ${e(d.meta.effective_as_of||q.as_of)}</small><strong>${price}</strong><span>제공 데이터 기준 · 실시간 시세 아님</span></div></div><div class="overview-signals"><div><small>매출 전년동기 성장률</small><strong>${ratio(ev?.revenue_growth_rt)}</strong><span>공시 재무 YTD 기준</span></div><div><small>공시 후 시장 대비 성과</small><strong>${ratio(ev?.excess_return_rt,'%p')}</strong><span>${e(ev?.observation_start||'미제공')} ~ ${e(ev?.observation_end||'미제공')}</span></div><div><small>복합 동반 개선</small><strong class="signal-label">${e(jointLabel(ev?.joint_improve_yn))}</strong><span>${e(stateLabel(ev?.joint_improve_stts_cd))}</span></div></div></section>`);
  document.querySelector('#sidebar-name').textContent=stock?.stock_nm||'기업 리포트';
  document.querySelector('#sidebar-code').textContent=`${stock?.mkt_cd||''} · ${q.stock_cd}`;
  bindCharts(results);
  results.querySelectorAll('[data-range]').forEach(button=>button.addEventListener('click',()=>{fields.start.value=rangeStart(fields.as_of.value,button.dataset.range);load();}));
  document.querySelector('#server-exports').hidden=!d.meta.api_version;
  document.querySelector('#server-export').disabled=false;document.querySelector('#server-exports').open=true;
  if(d.quality){
    const issues=rows=>rows.length?table(['상태 / 중요도','테이블 / 키','사유'],rows.map(r=>`<tr>${cell(`${r.resolve_stts_cd} / ${r.sev_cd}`)}${cell(`${r.tbl_nm} / ${r.rcrd_key_txt}`)}${cell(r.issue_rsn_txt)}</tr>`)):'<p>등록된 이슈 없음</p>';
    results.insertAdjacentHTML('beforeend',`<section class="panel" id="quality"><h2>품질·연결 상태</h2><p>연결 상태는 선택한 날짜 범위입니다. 이슈는 발견 시각이 제공되지 않아 기업·보고서 전체 범위이며, 전역 이슈는 해당 기업에만 귀속되지 않습니다.</p><details><summary>날짜별 연결 상태 (${d.quality.availability.length})</summary>${table(['거래일','가격 / 수급 / 재무','연결 / 사유'],d.quality.availability.map(r=>`<tr>${cell(r.trd_dt)}${cell(`${r.prc_exist_yn} / ${r.invstr_exist_yn} / ${r.fin_avail_yn}`)}${cell(`${r.conn_stts_cd} / ${r.miss_rsn_txt??'없음'}`)}</tr>`))}</details><details><summary>기업·보고서 이슈 (${d.quality.issues.length})</summary>${issues(d.quality.issues)}</details><details><summary>전역 재무제표 이슈 (${d.quality.global_statement_issues.length})</summary>${issues(d.quality.global_statement_issues)}</details></section>`);
  }
  results.querySelectorAll('[data-stock]').forEach(b=>{const select=()=>{fields.stock_cd.value=b.dataset.stock;load().then(()=>document.querySelector('#detail')?.scrollIntoView({behavior:'smooth'}));};b.addEventListener('click',select);if(b.tagName.toLowerCase()==='circle')b.addEventListener('keydown',event=>{if(['Enter',' '].includes(event.key)){event.preventDefault();select();}});});
}
async function load(){
  if(!form.reportValidity())return;
  const q=Object.fromEntries(new FormData(form));
  controller?.abort();controller=new AbortController();const local=controller;
  data=null;activeQuery=null;exportButton.disabled=true;document.querySelector('#server-exports').hidden=true;document.querySelector('#export-status').textContent='';
  if(q.start>q.as_of){results.innerHTML='';results.setAttribute('aria-busy','false');status.textContent='시작일은 기준일보다 늦을 수 없습니다.';return;}
  status.textContent='데이터를 불러오는 중입니다…';results.setAttribute('aria-busy','true');results.innerHTML='<div class="panel skeleton">선택한 기업의 흐름을 확인하고 있습니다.</div>';
  try{
    const response=await dashboard(q,local.signal);
    if(local!==controller)return;
    data=response;activeQuery=q;render(data,q);
    const count=['compare','daily','financials','evidence'].reduce((n,k)=>n+data[k].length,0);
    status.textContent=`${data.meta.synthetic?'합성 샘플':'API 응답'} · 조회 완료 · 요청 ${q.as_of} · 실제 관측 ${data.meta.effective_as_of||q.as_of} · 일별 ${data.daily.length}개 관측`;
    exportButton.disabled=!count;
  }catch(error){if(local!==controller || error.name==='AbortError')return; status.textContent='조회에 실패했습니다.';results.innerHTML=`<div class="panel error" role="alert"><h2>데이터를 불러오지 못했습니다</h2><p>${e(error.message)}</p><button id="retry">다시 시도</button></div>`;document.querySelector('#retry').onclick=load;
  }finally{if(local===controller)results.setAttribute('aria-busy','false');}
}
form.addEventListener('submit',event=>{event.preventDefault();load();});
form.addEventListener('change',event=>{if(event.target.name==='market')populateStocks();load();});
exportButton.onclick=()=>{if(data&&activeQuery)download(data,activeQuery);};
document.querySelector('#server-export').onclick=async()=>{
  if(!data||!activeQuery)return;
  const current=data,q=activeQuery,button=document.querySelector('#server-export'),message=document.querySelector('#export-status');
  button.disabled=true;message.textContent='CSV를 준비하고 있습니다…';
  try{
    const file=await serverExport(document.querySelector('#csv-kind').value,q,current.meta,controller.signal);
    if(current!==data)return;
    const url=URL.createObjectURL(file.blob),link=document.createElement('a');link.href=url;link.download=file.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    message.textContent='다운로드 완료';
  }catch(error){if(current===data)message.textContent=error.message;}
  finally{if(current===data)button.disabled=false;}
};
async function initialize(){
  try{const response=await request('stocks');stocks=response.data;populateStocks();if(!stocks.length){status.textContent='사용 가능한 종목이 없습니다.';results.innerHTML=empty;results.setAttribute('aria-busy','false');return;}await load();}
  catch(error){status.textContent='종목 목록을 불러오지 못했습니다.';results.setAttribute('aria-busy','false');results.innerHTML=`<div class="panel error" role="alert">${e(error.message)} <button id="retry-init">다시 시도</button></div>`;document.querySelector('#retry-init').onclick=initialize;}
}
initialize();
