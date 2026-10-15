// B API 1.0.0. Full schema: openapi.json. Monetary/quantity/ratio values are strings.
export type NumericString = string;
export interface ApiMeta {
  api_version: string; data_version: string; source_backend: 'csv'|'delta'|'mysql';
  data_min_date: string; data_final_date: string; stock_count: number;
  calculation_version: string; analysis_status: 'AVAILABLE'|'PENDING_C_DELIVERY';
  numeric_encoding: 'decimal_string'; units: {amount:'KRW';quantity:'shares';ratio:'decimal_fraction'};
  total?: number; limit?: number; offset?: number;
  [key: string]: unknown;
}
export interface ApiEnvelope<T> {data:T;meta:ApiMeta}
export interface ApiError {error:{code:string;message:string;details?:unknown[]};meta:ApiMeta}
export type BusinessRow = Record<string,string|null>;
export interface DailyRow {
  stock_cd:string;stock_nm:string;trd_dt:string;close_prc:NumericString;
  rev_ytd_amt:NumericString|null;op_prft_ytd_amt:NumericString|null;
  net_incm_ytd_amt:NumericString|null;op_cf_ytd_amt:NumericString|null;
  frgn_net_buy_qty:NumericString|null;inst_net_buy_qty:NumericString|null;
  fin_rpt_id:string|null;dscl_dt:string|null;fin_avail_yn:string;invstr_exist_yn:string;
  connection:BusinessRow|null;analysis:BusinessRow|null;
  [key:string]:unknown;
}
