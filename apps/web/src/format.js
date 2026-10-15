export const missing = '미제공 (NULL)';
export function integer(value, unit = '원') {
  if (value === null || value === undefined) return missing;
  if (!/^-?\d+$/.test(String(value))) return '형식 오류';
  return `${BigInt(value).toLocaleString('ko-KR')} ${unit}`;
}
export function ratio(value, unit = '%') {
  return value == null ? missing : `${(value * 100).toLocaleString('ko-KR', {maximumFractionDigits: 2})} ${unit}`;
}
export function escape(value) {
  return String(value ?? '미제공').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
export function csv(rows) {
  if (!rows.length) return '\uFEFF';
  const keys = Object.keys(rows[0]);
  const cell = value => {
    let text = value === null || value === undefined ? 'NULL' : String(value);
    if (/^[=+@\t\r]/.test(text) || (/^-/.test(text) && !/^-\d+(\.\d+)?$/.test(text))) text = "'" + text;
    return '"' + text.replaceAll('"','""') + '"';
  };
  return '\uFEFF' + [keys, ...rows.map(row => keys.map(key => row[key]))].map(row => row.map(cell).join(',')).join('\r\n');
}
