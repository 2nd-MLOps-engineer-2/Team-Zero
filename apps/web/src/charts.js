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
