import './style.css';
import { mode, request, dashboard } from './api.js';
import { integer, ratio, escape as e } from './format.js';
import { chart } from './charts.js';
import { download } from './export.js';

const app=document.querySelector('#app');
let stocks=[], data=null, activeQuery=null, controller=null;
const options=(pairs)=>pairs.map(([value,label])=>`<option value="${e(value)}">${e(label)}</option>`).join('');
app.innerHTML=`<header><a class="brand" href="#"><b>ZERO<span>↗</span></b><small>기업의 흐름을 읽다</small></a><nav aria-label="주요 영역"><a href="#comparison">종목 비교</a><a href="#detail">기업 상세</a><a href="#evidence">분석 근거</a></nav><span class="badge">${mode==='fixture'?'합성 샘플 모드':'API 연결 모드'}</span></header>
<main><div class="intro"><div><p class="eyebrow">TEAM ZERO / MARKET EXPLORER</p><h1>실적과 시장, 같은 방향일까요?</h1><p>기업 실적·현금흐름·투자자 수급을 함께 살펴보고, 움직임의 근거를 확인하세요.</p></div><div class="scope">보유 <b>20</b> 종목<br><small>기준 데이터 최종일 2026.06.30</small></div></div>
<aside class="notice">${mode==='fixture'?'샘플 안내 · 종목명과 코드는 제공 자료를 사용하며, 모든 분석 수치는 합성 예시입니다. 비교·근거는 2026-06-30, 추이는 6월의 6개 샘플 관측점, 재무는 2024·2025 연간 연결 YTD를 제공합니다.':'실제 API 응답의 출처·버전을 확인해 주세요. 연결 실패 시 샘플로 대체하지 않습니다.'}</aside>
<form id="filters" class="panel filters">
<label>시장<select name="market">${options([['','전체 시장'],['KOSPI','KOSPI'],['KOSDAQ','KOSDAQ']])}</select></label>
<label>기업<select name="stock_cd" required aria-label="기업"><option value="">불러오는 중</option></select></label>
<label>주가 조회 시작<input name="start" type="date" value="2026-06-01" min="2022-12-01" max="2026-06-30" required></label>
<label>기준일<input name="as_of" type="date" value="2026-06-30" min="2022-12-01" max="2026-06-30" required></label>
<label>사업연도<select name="year">${options([['all','2024·2025 비교'],['2025','2025'],['2024','2024']])}</select></label>
<label>보고서<select name="report">${options([['11011','사업보고서'],['11012','반기보고서'],['11013','1분기보고서'],['11014','3분기보고서']])}</select></label>
<label>재무제표<select name="basis">${options([['CFS','연결'],['OFS','별도']])}</select></label>
${mode==='fixture'?`<label>샘플 응답<select name="scenario">${options([['normal','정상'],['empty','빈 결과'],['error','오류']])}</select></label>`:''}
<button type="submit" id="submit">조회하기 <span>↗</span></button></form>
<div class="resultbar"><p id="status" role="status" aria-live="polite">종목 목록을 불러오는 중입니다.</p><button id="export" class="secondary" disabled>CSV 다운로드 ↓</button></div>
<div id="results" aria-busy="true"></div><footer>2026-06-30까지의 보유 20종목 범위 · 제공 종가 기준 · 동행·괴리는 인과관계나 매매 추천이 아닙니다.</footer></main>`;
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
function render(d,q){
  const financials=[...d.financials].sort((a,b)=>a.prd_end_dt.localeCompare(b.prd_end_dt));
  const latest=financials.at(-1), stock=stocks.find(s=>s.stock_cd===q.stock_cd), ev=d.evidence[0];
  const metrics=[['rev_ytd_amt','매출'],['op_prft_ytd_amt','영업이익'],['net_incm_ytd_amt','순이익'],['op_cf_ytd_amt','영업현금흐름']];
  results.innerHTML=`<section id="comparison" class="panel"><div class="section-head"><div><p class="eyebrow">01 / COMPARE</p><h2>실적과 시장의 동행·괴리</h2></div><span>${e(q.as_of)} · ${d.compare.length}개 종목</span></div><p class="muted">매출 전년동기 성장률(%)과 공시 후 시장 대비 성과(%p). 서로 다른 공시 경과 기간에 유의하세요.</p>
${d.compare.length?table(['기업 / 상세 보기','매출 성장률','시장 대비 성과','분류','공시일 · 경과일','관측 구간'],d.compare.map(r=>`<tr><td><button class="text-button" data-stock="${e(r.stock_cd)}">${e(r.stock_nm)} <small>${e(r.stock_cd)}</small></button></td>${cell(ratio(r.revenue_growth_rt))}${cell(ratio(r.excess_return_rt,'%p'))}${cell(r.classification)}${cell(`${r.dscl_dt || '미제공'} · ${r.dscl_elps_day_cnt ?? '미제공'}일`)}${cell(`${r.observation_start || '미제공'} ~ ${r.observation_end || '미제공'}`)}</tr>`)):empty}</section>
<section id="detail"><div class="section-head"><div><p class="eyebrow">02 / COMPANY</p><h2>${e(stock?.stock_nm)} <small>${e(q.stock_cd)}</small></h2></div><span>${e(q.basis==='CFS'?'연결':'별도')} · ${e(q.year==='all'?'연도 비교':q.year)}</span></div>
<div class="cards">${metrics.map(([key,label])=>`<article class="panel metric"><p>${label}</p><strong>${integer(latest?.[key])}</strong><small>${latest?`${e(latest.prd_start_dt)} ~ ${e(latest.prd_end_dt)} · ${e(latest.period_type)}`:'보고서 없음'}</small><span class="muted">${e(latest?.period_status || '미연결')}${latest?.[key]===null?` · ${e(latest.reason)}`:''}</span></article>`).join('')}</div>
<div class="grid"><article class="panel"><h3>주가와 시장 추이</h3><p class="muted">${e(d.meta.price_base_date || '기준일 미제공')} = 100 · 제공된 기준값 · 가로축: 관측일<br>조회 시작일을 바꾸어도 기준값을 재계산하지 않습니다.</p>${chart(d.daily,[{key:'stock_base100',label:'종목'},{key:'market_base100',label:'시장'}],'trd_dt','기준값','종목과 시장 기준값 추이')}</article>
<article class="panel"><h3>실적과 현금흐름</h3><p class="muted">가로축: 사업연도 · 같은 연간 YTD / ${q.basis==='CFS'?'연결':'별도'}<br>재무 수치를 일별로 반복 합산하지 않습니다.</p>${chart(financials,metrics.map(([key,label])=>({key,label,scale:1e12,rawUnit:'원'})),'bsns_yr','조 원','연간 실적과 현금흐름 비교')}</article>
<article class="panel"><h3>외국인·기관 순매수</h3><p class="muted">가로축: 관측일 · 일별 수량(주), 기관 합계만 표시<br>NULL 구간은 연결하거나 0으로 채우지 않습니다.</p>${chart(d.daily,[{key:'frgn_net_buy_qty',label:'외국인'},{key:'inst_net_buy_qty',label:'기관 합계'}],'trd_dt','주','일별 외국인 기관 순매수')}</article>
<article class="panel"><h3>외국인 보유율</h3><p class="muted">가로축: 관측일 · 소수 비율을 %로 표시<br>순매수 수량과 보유 비율을 구분합니다.</p>${chart(d.daily,[{key:'frgn_hold_rt',label:'외국인 보유율',scale:.01,rawUnit:'소수 비율'}],'trd_dt','%','외국인 보유율 추이')}</article></div>
<details class="panel"><summary>차트 원값 · 재무 보고서 확인</summary><h3>일별 값</h3>${d.daily.length?table(['거래일','종목 기준값','시장 기준값','외국인 순매수(주)','기관 순매수(주)','외국인 보유율','상태 / 사유'],d.daily.map(r=>`<tr>${cell(r.trd_dt)}${cell(r.stock_base100??'미제공 (NULL)')}${cell(r.market_base100??'미제공 (NULL)')}${cell(integer(r.frgn_net_buy_qty,'주'))}${cell(integer(r.inst_net_buy_qty,'주'))}${cell(ratio(r.frgn_hold_rt))}${cell(`${r.status || '미제공'} ${r.reason || ''}`)}</tr>`)):empty}<h3>보고서별 원 단위 값</h3>${financials.length?table(['보고서 / 공시일','기간 유형 / 검증','매출','영업이익','순이익','영업CF'],financials.map(r=>`<tr>${cell(`${r.fin_rpt_id} / ${r.dscl_dt}`)}${cell(`${r.prd_start_dt} ~ ${r.prd_end_dt} / ${r.period_type} / ${r.period_status || '미제공'}`)}${metrics.map(([key])=>cell(integer(r[key]))).join('')}</tr>`)):empty}</details></section>
<section id="evidence" class="panel"><div class="section-head"><div><p class="eyebrow">03 / EVIDENCE</p><h2>판단의 근거를 확인하세요</h2></div><span class="badge">${e(ev?.calc_status || '미연결')}</span></div>${ev?`<h3>${e(ev.classification)}</h3><p>매출 성장률 <b>${ratio(ev.revenue_growth_rt)}</b> · 공시 후 시장 대비 성과 <b>${ratio(ev.excess_return_rt,'%p')}</b></p><p>${e(ev.formula)}</p><dl><dt>보고서 / 공시일</dt><dd>${e(ev.fin_rpt_id)} / ${e(ev.dscl_dt)}</dd><dt>공시 후 성과 관측 구간</dt><dd>${e(ev.observation_start)} ~ ${e(ev.observation_end)}</dd><dt>성장률 분자 / 분모</dt><dd>${integer(ev.numerator)} / ${integer(ev.denominator)}</dd><dt>임계값 / 추가 검토</dt><dd>${e(ev.threshold)} / ${e(ev.review)}</dd></dl><h3>레이어별 품질·출처</h3>${table(['레이어','상태','파일 / 행','키','버전','사유'],ev.lineage.map(r=>`<tr>${cell(r.layer)}${cell(r.status)}${cell(`${r.file ?? '미제공'} / ${r.row ?? '미제공'}`)}${cell(r.key??'미제공')}${cell(r.version??'미제공')}${cell(r.reason)}</tr>`))}`:empty}<p class="metadata">${e(d.meta.synthetic?'합성 데이터':'API 데이터')} · 입력 ${e(d.meta.input_version)} · 계산 ${e(d.meta.calc_version)} · 최종일 ${e(d.meta.data_end)}</p></section>`;
  results.querySelectorAll('[data-stock]').forEach(b=>b.addEventListener('click',()=>{fields.stock_cd.value=b.dataset.stock;load().then(()=>document.querySelector('#detail')?.scrollIntoView({behavior:'smooth'}));}));
}
async function load(){
  if(!form.reportValidity())return;
  const q=Object.fromEntries(new FormData(form));
  controller?.abort();controller=new AbortController();const local=controller;
  data=null;activeQuery=null;exportButton.disabled=true;
  if(q.start>q.as_of){results.innerHTML='';results.setAttribute('aria-busy','false');status.textContent='시작일은 기준일보다 늦을 수 없습니다.';return;}
  status.textContent='데이터를 불러오는 중입니다…';results.setAttribute('aria-busy','true');results.innerHTML='<div class="panel skeleton">선택한 기업의 흐름을 확인하고 있습니다.</div>';
  try{
    const response=await dashboard(q,local.signal);
    if(local!==controller)return;
    data=response;activeQuery=q;render(data,q);
    const count=['compare','daily','financials','evidence'].reduce((n,k)=>n+data[k].length,0);
    status.textContent=`${data.meta.synthetic?'합성 샘플':'API 응답'} · 조회 완료 · ${q.as_of} · 일별 ${data.daily.length}개 관측`;
    exportButton.disabled=!count;
  }catch(error){if(local!==controller || error.name==='AbortError')return; status.textContent='조회에 실패했습니다.';results.innerHTML=`<div class="panel error" role="alert"><h2>데이터를 불러오지 못했습니다</h2><p>${e(error.message)}</p><button id="retry">다시 시도</button></div>`;document.querySelector('#retry').onclick=load;
  }finally{if(local===controller)results.setAttribute('aria-busy','false');}
}
form.addEventListener('submit',event=>{event.preventDefault();load();});
form.addEventListener('change',event=>{if(event.target.name==='market')populateStocks();load();});
exportButton.onclick=()=>{if(data&&activeQuery)download(data,activeQuery);};
async function initialize(){
  try{const response=await request('stocks');stocks=response.data;populateStocks();if(!stocks.length){status.textContent='사용 가능한 종목이 없습니다.';results.innerHTML=empty;results.setAttribute('aria-busy','false');return;}await load();}
  catch(error){status.textContent='종목 목록을 불러오지 못했습니다.';results.setAttribute('aria-busy','false');results.innerHTML=`<div class="panel error" role="alert">${e(error.message)} <button id="retry-init">다시 시도</button></div>`;document.querySelector('#retry-init').onclick=initialize;}
}
initialize();
