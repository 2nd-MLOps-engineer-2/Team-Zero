import { escape as e } from './format.js';

// Chart coordinates are presentation only; business metrics arrive in the response.
export function chart(rows, series, labelKey, unit, title) {
  if (!rows.length) return '<p class="empty">조회 결과가 없습니다.</p>';
  const values = rows.flatMap(r => series.map(s => r[s.key] == null ? null : Number(r[s.key]) / (s.scale || 1))).filter(v => v !== null && Number.isFinite(v));
  if (!values.length) return '<p class="empty">표시할 값이 없습니다. 결측 사유를 확인하세요.</p>';
  const includeZero = ['주','조 원'].includes(unit);
  const min=Math.min(...values), max=Math.max(...values), padding=(max-min || Math.abs(max) || 1)*.12;
  const low = includeZero ? Math.min(min,0) : min-padding, high = includeZero ? Math.max(max,1) : max+padding, span = high-low;
  const dates=rows.map(r=>/^\d{4}-\d{2}-\d{2}$/.test(r[labelKey])?Date.parse(r[labelKey]):null);
  const byDate=dates.every(d=>d!==null)&&dates.at(-1)>dates[0];
  const x = i => 65 + (byDate ? (dates[i]-dates[0])/(dates.at(-1)-dates[0]) : i/Math.max(rows.length-1,1))*620;
  const y = n => 195 - (n-low)/span*155;
  const colors = ['#087f73','#dc814c','#6374b7','#ba658e'];
  let body = [0,0.5,1].map(f => {const n=low+span*f; return `<line x1="65" x2="685" y1="${y(n)}" y2="${y(n)}" stroke="#e2e9e6"/><text x="55" y="${y(n)+4}" text-anchor="end">${e(n.toLocaleString('ko-KR',{maximumFractionDigits:2}))}</text>`;}).join('');
  series.forEach((s,si) => {
    let segment=[];
    const flush=()=>{if(segment.length) body+=`<polyline points="${segment.join(' ')}" fill="none" stroke="${colors[si]}" stroke-width="3" ${si%2?'stroke-dasharray="6 4"':''}/>`; segment=[];};
    rows.forEach((r,i)=>{
      if(r[s.key]==null) {flush();return;}
      const n=Number(r[s.key])/(s.scale||1);
      segment.push(`${x(i)},${y(n)}`);
      body+=`<circle cx="${x(i)}" cy="${y(n)}" r="4" fill="${colors[si]}"><title>${e(r[labelKey])} · ${e(s.label)} ${e(r[s.key])} (${e(s.rawUnit||unit)})</title></circle>`;
    });flush();
  });
  [0,rows.length-1].forEach(i=>{body+=`<text x="${x(i)}" y="220" text-anchor="${i===0?'start':'end'}">${e(rows[i][labelKey])}</text>`;});
  return `<div class="legend">${series.map((s,i)=>`<span><i style="background:${colors[i]}"></i>${e(s.label)}</span>`).join('')}<span>세로축: ${e(unit)}</span></div><svg viewBox="0 0 740 240" role="img" aria-label="${e(title)}"><title>${e(title)}</title>${body}</svg>`;
}

export function scatter(rows) {
 const valid=rows.filter(r=>r.revenue_growth_rt!=null&&r.excess_return_rt!=null);
 const limitX=Math.max(.01,...valid.map(r=>Math.abs(Number(r.revenue_growth_rt))))*1.15;
 const limitY=Math.max(.01,...valid.map(r=>Math.abs(Number(r.excess_return_rt))))*1.15;
 const x=v=>370+Number(v)/limitX*290,y=v=>170-Number(v)/limitY*115;
 const point=r=>`<circle cx="${x(r.revenue_growth_rt)}" cy="${y(r.excess_return_rt)}" r="6" fill="#087f73" stroke="white" tabindex="0" role="button" data-stock="${e(r.stock_cd)}" aria-label="${e(r.stock_nm||r.stock_cd)} 상세 보기"><title>${e(r.stock_nm||r.stock_cd)} ${e(r.stock_cd)} | 기준일 ${e(r.as_of)} | 성장률 ${Number(r.revenue_growth_rt)*100}% | 공시 후 초과성과 ${Number(r.excess_return_rt)*100}%p | 공시 ${e(r.dscl_dt)} | 기준 관측 ${e(r.observation_start)} | ${e(r.classification)}</title></circle>`;
 return `<div class="scatter"><svg viewBox="0 0 740 340" role="group" aria-label="실적과 시장 대비 성과 사분면"><title>매출 성장률과 공시 후 시장 대비 성과</title><rect x="80" y="55" width="580" height="230" fill="#f5f8f3"/><line x1="80" y1="170" x2="660" y2="170" stroke="#7e9386"/><line x1="370" y1="55" x2="370" y2="285" stroke="#7e9386"/><text x="90" y="40">둔화 · 강세 괴리</text><text x="520" y="40">개선 · 강세 동행</text><text x="90" y="306">둔화 · 약세 동행</text><text x="520" y="306">개선 · 약세 괴리</text><text x="370" y="330" text-anchor="middle">매출 YoY (%) · 0축</text><text x="12" y="18">공시 후 초과성과 (%p)</text>${[-1,0,1].map(v=>`<text x="${x(limitX*v)}" y="187" text-anchor="middle">${(limitX*v*100).toFixed(1)}</text><text x="360" y="${y(limitY*v)}" text-anchor="end">${(limitY*v*100).toFixed(1)}</text>`).join('')}${valid.map(point).join('')}</svg><p class="muted">유효 ${valid.length}개 · 판단 불가 ${rows.length-valid.length}개는 점에서 제외하고 아래 표에 유지합니다. 겹치는 종목은 표에서 선택할 수 있습니다.</p></div>`;
}
