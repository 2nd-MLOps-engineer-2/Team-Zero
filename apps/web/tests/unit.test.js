import test from 'node:test';
import assert from 'node:assert/strict';
import fixture from '../src/fixtures/sample.json' with {type:'json'};
import { integer, ratio, csv, escape } from '../src/format.js';
import { validate, dashboard } from '../src/api.js';
import { exportRows } from '../src/export.js';
import { chart } from '../src/charts.js';

const query={stock_cd:'000660',market:'',start:'2026-06-01',as_of:'2026-06-30',year:'all',report:'11011',basis:'CFS',scenario:'normal'};
test('large integer precision, NULL and zero stay distinct',()=>{
 assert.equal(integer('99999999999999999999'),'99,999,999,999,999,999,999 원');
 assert.equal(integer(null),'미제공 (NULL)');assert.equal(integer('0'),'0 원');
 assert.equal(ratio(0.054,'%p'),'5.4 %p');assert.equal(ratio(0),'0 %');
});
test('CSV quotes, explicit NULL, numeric zero and spreadsheet formulas',()=>{
 const output=csv([{a:null,b:'0',c:'=1+1',d:'a"b,가',e:'-123'}]);
 assert.ok(output.startsWith('\uFEFF'));assert.ok(output.includes('"NULL","0","\'=1+1","a""b,가","-123"'));
});
test('unsafe API strings are escaped',()=>assert.equal(escape('<img onerror="x">'),'&lt;img onerror=&quot;x&quot;&gt;'));
test('contract rejects numeric large amounts and wrong stock types',()=>{
 const payload={meta:fixture.meta,data:[{...fixture.financials['000660'][0],rev_ytd_amt:123}]};
 assert.throws(()=>validate(payload,'financials'),/정수 문자열/);
 assert.throws(()=>validate({meta:fixture.meta,data:[{stock_cd:123456}]},'stocks'),/문자열/);
});
test('fixture identities, baseline, growth evidence are consistent',()=>{
 assert.equal(fixture.stocks.length,20);assert.equal(new Set(fixture.stocks.map(r=>r.stock_cd)).size,20);
 for(const s of fixture.stocks){
  const reports=fixture.financials[s.stock_cd], ev=fixture.evidence[s.stock_cd];
  assert.equal(fixture.daily[s.stock_cd][0].stock_base100,100);
  if(ev.revenue_growth_rt!==null){
   assert.equal(BigInt(reports[1].rev_ytd_amt)-BigInt(reports[0].rev_ytd_amt),BigInt(ev.numerator));
   assert.equal(Number(ev.numerator)/Number(ev.denominator),ev.revenue_growth_rt);
  }
 }
});
test('market, date, report and year filters retain semantics',async()=>{
 const d=await dashboard({...query,market:'KOSDAQ',start:'2026-06-15',year:'2025'});
 assert.equal(d.compare.length,6);assert.equal(d.daily.length,3);assert.equal(d.financials.length,1);
 assert.equal((await dashboard({...query,report:'11012'})).financials.length,0);
 assert.equal((await dashboard({...query,as_of:'2026-03-20'})).financials.length,1); // same-day 2025 report excluded
});
test('empty and error cases do not become normal data',async()=>{
 assert.equal((await dashboard({...query,scenario:'empty'})).daily.length,0);
 await assert.rejects(dashboard({...query,scenario:'error'}),/샘플 응답 오류/);
});
test('export retains raw financial precision, query and sample metadata',async()=>{
 const d=await dashboard(query), rows=exportRows(d,query);
 const value=rows.find(r=>r.dataset==='financials'&&r.record_key==='SAMPLE-000660-2025'&&r.field==='rev_ytd_amt');
 assert.equal(value.value,'11200000000000');assert.equal(value.synthetic,true);assert.equal(value.unit,'KRW');
 assert.ok(rows.some(r=>r.field==='frgn_net_buy_qty'&&r.value===null));
});
test('NULL creates chart gaps rather than connecting across missing points',()=>{
 const svg=chart([{d:'1',v:1},{d:'2',v:null},{d:'3',v:2}],[{key:'v',label:'test'}],'d','주','test');
 assert.equal((svg.match(/<polyline/g)||[]).length,2);
 assert.equal((svg.match(/<circle/g)||[]).length,2);
});
test('aborted requests cannot return data',async()=>{
 const c=new AbortController(); const pending=dashboard(query,c.signal);c.abort();
 await assert.rejects(pending,{name:'AbortError'});
});
