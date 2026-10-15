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

// BigInt keeps large won amounts exact until display-only rounding.
export function money(value) {
  if(value==null)return missing;
  const text=String(value);
  if(!/^-?\d+(?:\.0+)?$/.test(text))return '형식 오류';
  const n=BigInt(text.split('.')[0]),abs=n<0n?-n:n;
  if(abs<100000000n)return integer(n);
  let divisor=abs>=1000000000000n?1000000000000n:100000000n;
  let rounded=(abs*100n+divisor/2n)/divisor;
  if(divisor===100000000n&&rounded>=1000000n){divisor=1000000000000n;rounded=(abs*100n+divisor/2n)/divisor;}
  const fraction=String(rounded%100n).padStart(2,'0').replace(/0+$/,'');
  return `${n<0n?'-':''}${(rounded/100n).toLocaleString('ko-KR')}${fraction?'.'+fraction:''} ${divisor===1000000000000n?'조 원':'억 원'}`;
}
