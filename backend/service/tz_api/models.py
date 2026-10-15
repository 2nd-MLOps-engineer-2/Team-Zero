"""Wire contracts: financial numbers stay strings; optional source values stay null."""
from typing import Generic,TypeVar
from pydantic import BaseModel,ConfigDict,StrictStr

class Record(BaseModel):
 model_config=ConfigDict(extra='allow')

class Meta(Record):
 api_version:StrictStr
 data_version:StrictStr
 source_backend:StrictStr
 data_min_date:StrictStr
 data_final_date:StrictStr
 stock_count:int
 calculation_version:StrictStr
 analysis_status:StrictStr
 units:dict[str,str]
 numeric_encoding:StrictStr

T=TypeVar('T')
class Envelope(BaseModel,Generic[T]):
 data:T
 meta:Meta

class Error(Record):
 code:StrictStr
 message:StrictStr
class ErrorEnvelope(BaseModel):
 error:Error
 meta:Meta

class Stock(Record):
 stock_cd:StrictStr
 stock_nm:StrictStr
 mkt_cd:StrictStr
 outstd_shr_qty:StrictStr|None

class Metric(Record):
 fin_rpt_id:StrictStr
 mtrc_cd:StrictStr
 prd_type_cd:StrictStr
 mtrc_amt:StrictStr|None
 src_col_nm:StrictStr
 pipln_ver:StrictStr

class Daily(Record):
 stock_cd:StrictStr
 stock_nm:StrictStr
 trd_dt:StrictStr
 corp_cd:StrictStr|None
 mkt_cd:StrictStr
 open_prc:StrictStr
 high_prc:StrictStr
 low_prc:StrictStr
 close_prc:StrictStr
 trd_qty:StrictStr
 close_rtn_rt:StrictStr|None
 idx_close_prc:StrictStr|None
 idx_rtn_rt:StrictStr|None
 indv_net_buy_qty:StrictStr|None
 frgn_net_buy_qty:StrictStr|None
 inst_net_buy_qty:StrictStr|None
 other_corp_net_buy_qty:StrictStr|None
 frgn_hold_rt:StrictStr|None
 cfd_buy_bal_rt:StrictStr|None
 invstr_exist_yn:StrictStr
 fin_avail_yn:StrictStr
 fin_rpt_id:StrictStr|None
 fin_bsns_yr:StrictStr|None
 fin_rpt_cd:StrictStr|None
 fin_fs_div_cd:StrictStr|None
 dscl_dt:StrictStr|None
 dscl_elps_day_cnt:StrictStr|None
 rev_ytd_amt:StrictStr|None
 op_prft_ytd_amt:StrictStr|None
 net_incm_ytd_amt:StrictStr|None
 op_cf_ytd_amt:StrictStr|None
 tot_asst_amt:StrictStr|None
 tot_liab_amt:StrictStr|None
 tot_eqty_amt:StrictStr|None
 pipln_ver:StrictStr
 connection:dict[str,str|None]|None
 analysis:dict[str,str|None]|None

class Financial(Record):
 fin_rpt_id:StrictStr
 corp_cd:StrictStr
 bsns_yr:StrictStr
 rpt_cd:StrictStr
 fs_div_cd:StrictStr
 dscl_dt:StrictStr|None
 pit_join_elig_yn:StrictStr
 same_prd_cmpr_elig_yn:StrictStr
 metrics:list[Metric]
 period_market_summary:dict[str,str|None]|None
 analysis:dict[str,str|None]|None

class Evidence(Record):
 observation:Daily
 financial_report:Financial|None
 price_source:dict[str,str|None]
 pit_rule:StrictStr
 analysis_status:StrictStr
