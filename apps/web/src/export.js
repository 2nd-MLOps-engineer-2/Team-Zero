import { csv } from './format.js';

export function exportRows(data, query) {
  const rows=[];
  for (const kind of ['compare','daily','financials','evidence']) for (const record of data[kind]) {
    for (const [field,value] of Object.entries(record)) {
      rows.push({dataset:kind, stock_cd:record.stock_cd, record_key:record.trd_dt || record.fin_rpt_id || record.as_of,
        field, value:typeof value === 'object' && value !== null ? JSON.stringify(value) : value,
        unit:field.endsWith('_amt') || ['numerator','denominator'].includes(field) ? 'KRW' : field.endsWith('_qty') ? 'shares' : field.endsWith('_rt') ? 'decimal_ratio' : '',
        query_as_of:query.as_of, query_start:query.start, query_year:query.year, query_report:query.report, query_basis:query.basis,
        synthetic:data.meta.synthetic, data_end:data.meta.data_end, input_version:data.meta.input_version, calc_version:data.meta.calc_version});
    }
  }
  return rows;
}
export function download(data, query) {
  const blob = new Blob([csv(exportRows(data,query))], {type:'text/csv;charset=utf-8;'});
  const url=URL.createObjectURL(blob), link=document.createElement('a');
  link.href=url;link.download=`team-zero-${data.meta.synthetic?'SAMPLE-':''}${query.stock_cd}-${query.as_of}.csv`;link.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
