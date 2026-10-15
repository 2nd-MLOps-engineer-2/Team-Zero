import { escape as e, integer, money, ratio } from './format.js';

let chartId=0;

// Only chart coordinates are calculated here. Financial metrics remain server values.
export function chart(rows, series, labelKey, unit, title, options={}) {
  if(!rows.length)return '<p class="empty">조회 결과가 없습니다.</p>';
  const numeric=(r,s)=>r[s.key]==null?null:Number(r[s.key])/(s.scale||1);
  const values=rows.flatMap(r=>series.map(s=>numeric(r,s))).filter(v=>v!==null&&Number.isFinite(v));
  if(!values.length)return '<p class="empty">표시할 값이 없습니다. 결측 사유를 확인하세요.</p>';
  const gradientId=`chart-fill-${++chartId}`;
  const bars=options.type==='bar',zero=bars||['주','조 원'].includes(unit);
  const min=Math.min(...values),max=Math.max(...values),padding=(max-min||Math.abs(max)||1)*.14;
  const low=zero?Math.min(0,min-padding):min-padding,high=zero?Math.max(0,max+padding):max+padding,span=high-low||1;
  const dates=rows.map(r=>Date.parse(r[labelKey]));
  const byDate=!bars&&dates.every(Number.isFinite)&&dates.at(-1)>dates[0];
  const x=i=>82+(bars?(i+.5)/rows.length:byDate?(dates[i]-dates[0])/(dates.at(-1)-dates[0]):rows.length===1?.5:i/(rows.length-1))*584;
  const y=v=>238-(v-low)/span*190;
  const colors=['#63d6bd','#e8b96d','#849ff0','#d795d1'];
  let body=[0,.25,.5,.75,1].map(f=>{const n=low+span*f;return `<line x1="70" x2="682" y1="${y(n)}" y2="${y(n)}" stroke="#2a3b42" stroke-dasharray="3 5"/><text x="60" y="${y(n)+4}" text-anchor="end">${e(n.toLocaleString('ko-KR',{notation:'compact',maximumFractionDigits:1}))}</text>`;}).join('');
  const baseline=unit==='기준값'?100:0;
  if(baseline>=low&&baseline<=high)body+=`<line x1="70" x2="682" y1="${y(baseline)}" y2="${y(baseline)}" stroke="#7c9299" stroke-dasharray="5 5"/><text x="690" y="${y(baseline)+4}">${baseline}</text>`;
  series.forEach((s,si)=>{
    body+=`<g data-series="${si}">`;let segment=[];
    const flush=()=>{if(segment.length>1&&si===0)body+=`<polygon class="chart-area" points="${segment[0].split(',')[0]},238 ${segment.join(' ')} ${segment.at(-1).split(',')[0]},238" fill="url(#${gradientId})"/>`;if(segment.length)body+=`<polyline points="${segment.join(' ')}" fill="none" stroke="${colors[si]}" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" ${si%2?'stroke-dasharray="7 4"':''}/>`;segment=[];};
    rows.forEach((r,i)=>{
      const n=numeric(r,s);if(n===null||!Number.isFinite(n)){flush();return;}
      const tip=`${e(r[labelKey])} · ${e(s.label)} ${e(r[s.key])} (${e(s.rawUnit||unit)})`;
      if(bars){const group=Math.min(100,584/rows.length*.68),width=group/series.length;
        body+=`<rect x="${x(i)-group/2+si*width}" y="${Math.min(y(n),y(0))}" width="${Math.max(.3,width-2)}" height="${Math.max(1,Math.abs(y(n)-y(0)))}" rx="2" fill="${colors[si]}"><title>${tip}</title></rect>`;
      }else{segment.push(`${x(i)},${y(n)}`);body+=`<circle class="data-dot ${i===rows.length-1?'last-dot':''}" cx="${x(i)}" cy="${y(n)}" r="${rows.length>40?1.5:3}" fill="${colors[si]}"><title>${tip}</title></circle>`;}
    });flush();body+='</g>';
  });
  const labels=[...new Set([0,Math.floor((rows.length-1)/2),rows.length-1])];
  body+=labels.map(i=>`<text x="${x(i)}" y="270" text-anchor="${i===0?'start':i===rows.length-1?'end':'middle'}">${e(rows[i][labelKey])}</text>`).join('');
  const points=rows.map((r,i)=>({x:x(i),date:r[labelKey],values:series.map(s=>({y:numeric(r,s)==null?null:y(numeric(r,s)),label:s.label,value:r[s.key]??null,unit:s.rawUnit||unit}))}));
  return `<div class="interactive-chart" data-points="${e(JSON.stringify(points))}"><div class="legend">${series.map((s,i)=>`<button type="button" data-series-toggle="${i}" aria-pressed="true"><i style="background:${colors[i]}"></i>${e(s.label)}</button>`).join('')}<span>단위: ${e(unit)}</span></div><svg viewBox="0 0 740 290" role="img" aria-label="${e(title)}"><title>${e(title)}</title><defs><linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#63d6bd" stop-opacity=".3"/><stop offset="100%" stop-color="#63d6bd" stop-opacity=".015"/></linearGradient></defs>${body}<g class="active-points"></g><line class="chart-cursor" x1="${x(rows.length-1)}" x2="${x(rows.length-1)}" y1="40" y2="240" stroke="#c4d4d8" stroke-dasharray="3 4"/></svg><div class="chart-tooltip" aria-hidden="true" hidden></div><div class="chart-readout" aria-live="polite"></div><label class="chart-scrubber">관측일 탐색 <input type="range" min="0" max="${rows.length-1}" value="${rows.length-1}" aria-label="${e(title)} 관측일 선택"></label></div>`;
}

export function bindCharts(root){
 root.querySelectorAll('.interactive-chart').forEach(wrap=>{
  const points=JSON.parse(wrap.dataset.points),svg=wrap.querySelector('svg'),range=wrap.querySelector('input'),readout=wrap.querySelector('.chart-readout');
  const show=i=>{const p=points[i];range.value=i;range.setAttribute('aria-valuetext',p.date);const cursor=wrap.querySelector('.chart-cursor');cursor.setAttribute('x1',p.x);cursor.setAttribute('x2',p.x);
   readout.innerHTML=`<b>${e(p.date)}</b>${p.values.map((v,si)=>`<span data-readout-series="${si}">${e(v.label)} <strong title="${e(v.value==null?'미제공 (NULL)':String(v.value)+' '+v.unit)}">${v.value===null?'미제공 (NULL)':v.unit==='원'?money(v.value):v.unit==='주'?integer(v.value,v.unit):v.unit==='소수 비율'?ratio(v.value):e(Number(v.value).toLocaleString('ko-KR',{maximumFractionDigits:2}))+' '+e(v.unit)}</strong></span>`).join('')}`;
   svg.querySelector('.active-points').innerHTML=p.values.map((v,si)=>v.y==null?'':`<circle data-active-series="${si}" cx="${p.x}" cy="${v.y}" r="5" fill="${['#63d6bd','#e8b96d','#849ff0','#d795d1'][si]}" stroke="#142329" stroke-width="2"/>`).join('');
   wrap.querySelectorAll('[data-series-toggle]').forEach(b=>{const marker=svg.querySelector(`[data-active-series="${b.dataset.seriesToggle}"]`);if(marker)marker.style.display=b.getAttribute('aria-pressed')==='false'?'none':'';readout.querySelector(`[data-readout-series="${b.dataset.seriesToggle}"]`).hidden=b.getAttribute('aria-pressed')==='false';});
  };
  range.addEventListener('input',()=>show(Number(range.value)));
  svg.addEventListener('pointermove',event=>{const box=svg.getBoundingClientRect(),px=(event.clientX-box.left)/box.width*740;let nearest=0;points.forEach((p,i)=>{if(Math.abs(p.x-px)<Math.abs(points[nearest].x-px))nearest=i;});show(nearest);const tip=wrap.querySelector('.chart-tooltip'),outer=wrap.getBoundingClientRect();tip.innerHTML=readout.innerHTML;tip.hidden=false;tip.style.left=Math.max(0,Math.min(event.clientX-outer.left+16,outer.width-tip.offsetWidth))+'px';tip.style.top=Math.max(30,event.clientY-outer.top-tip.offsetHeight-18)+'px';});
  svg.addEventListener('pointerleave',()=>{wrap.querySelector('.chart-tooltip').hidden=true;});
  wrap.querySelectorAll('[data-series-toggle]').forEach(b=>b.addEventListener('click',()=>{const pressed=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',String(pressed));wrap.querySelector(`[data-series="${b.dataset.seriesToggle}"]`).style.display=pressed?'':'none';show(Number(range.value));}));
  show(points.length-1);
 });
}

export function scatter(rows, selected) {
 const valid=rows.filter(r=>r.revenue_growth_rt!=null&&r.excess_return_rt!=null);
 const limitX=Math.max(.01,...valid.map(r=>Math.abs(Number(r.revenue_growth_rt))))*1.15;
 const limitY=Math.max(.01,...valid.map(r=>Math.abs(Number(r.excess_return_rt))))*1.15;
 const x=v=>370+Number(v)/limitX*290,y=v=>170-Number(v)/limitY*115;
 const point=r=>`<circle cx="${x(r.revenue_growth_rt)}" cy="${y(r.excess_return_rt)}" r="${r.stock_cd===selected?10:6}" fill="${r.stock_cd===selected?'#d8ef86':'#58c9b4'}" stroke="#162328" tabindex="0" role="button" data-stock="${e(r.stock_cd)}" aria-label="${e(r.stock_nm||r.stock_cd)} 상세 보기"><title>${e(r.stock_nm||r.stock_cd)} ${e(r.stock_cd)} | 기준일 ${e(r.as_of)} | 성장률 ${Number(r.revenue_growth_rt)*100}% | 공시 후 초과성과 ${Number(r.excess_return_rt)*100}%p | 공시 ${e(r.dscl_dt)} | 기준 관측 ${e(r.observation_start)} | ${e(r.classification)}</title></circle>`;
 return `<div class="scatter"><svg viewBox="0 0 740 340" role="group" aria-label="실적과 시장 대비 성과 사분면"><title>매출 성장률과 공시 후 시장 대비 성과</title><rect x="80" y="55" width="580" height="230" fill="#152329"/><line x1="80" y1="170" x2="660" y2="170" stroke="#536c73"/><line x1="370" y1="55" x2="370" y2="285" stroke="#536c73"/><text x="90" y="40">둔화 · 강세 괴리</text><text x="520" y="40">개선 · 강세 동행</text><text x="90" y="306">둔화 · 약세 동행</text><text x="520" y="306">개선 · 약세 괴리</text><text x="370" y="330" text-anchor="middle">매출 YoY (%) · 0축</text><text x="12" y="18">공시 후 초과성과 (%p)</text>${[-1,0,1].map(v=>`<text x="${x(limitX*v)}" y="187" text-anchor="middle">${(limitX*v*100).toFixed(1)}</text><text x="360" y="${y(limitY*v)}" text-anchor="end">${(limitY*v*100).toFixed(1)}</text>`).join('')}${valid.map(point).join('')}</svg><p class="muted">유효 ${valid.length}개 · 판단 불가 ${rows.length-valid.length}개는 점에서 제외하고 아래 표에 유지합니다. 겹치는 종목은 표에서 선택할 수 있습니다.</p></div>`;
}
