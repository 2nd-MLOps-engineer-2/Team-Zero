// G01/G03 c-gold-0.1.0: representation mapping only, no business calculations.
export const statusLabels = {
 OK:'사용 가능', NO_DATA:'자료 부족으로 판단 불가', UNAVAILABLE:'자료 부족으로 판단 불가',
 PRD_UNVERIFIED:'재무 기간 검증 필요', DENOM_ZERO:'기준값 0으로 비율 계산 불가',
 NEG_BASE:'기준값 음수로 비율 계산 불가', WINDOW_SHORT:'과거 관측 부족',
 NO_PRE_EVENT_PRICE:'공시 전 기준가격 없음',
 IMPROVE_STRONG:'실적 개선·시장 대비 강세 동행', IMPROVE_WEAK:'실적 개선·시장 대비 약세 괴리',
 SLOW_STRONG:'실적 둔화·시장 대비 강세 괴리', SLOW_WEAK:'실적 둔화·시장 대비 약세 동행',
 NEUTRAL:'기준값 0, 방향 중립'
};
export const stateLabel = value => statusLabels[value] || value || '미제공';
export const jointLabel = value => value==='Y'?'동반 개선':value==='N'?'조건 미충족':'판단 불가';
export function normalizeCRow(input, kind) {
 const r=Object.fromEntries(Object.entries(input).map(([k,v])=>[k,v===''?null:v]));
 const alias=(to,from)=>{if(!(to in r)&&from in r)r[to]=r[from];};
 alias('revenue_growth_rt','rev_yoy_rt'); alias('excess_return_rt','event_excess_rt');
 alias('observation_start','event_base_dt'); alias('observation_end','trd_dt');
 if(['compare','evidence'].includes(kind)){
  alias('as_of','trd_dt');
  if(!('classification' in r)&&'co_move_cd' in r)r.classification=stateLabel(r.co_move_cd);
  if(!('calc_status' in r)&&'co_move_stts_cd' in r)r.calc_status=stateLabel(r.co_move_stts_cd);
 }
 if(kind==='financials'&&r.calc_ver==='c-gold-0.1.0'){
  r.period_type ??= 'YTD'; r.period_status ??= stateLabel(r.cal_prd_stts_cd);
 }
 return r;
}
