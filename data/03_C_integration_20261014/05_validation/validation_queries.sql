-- validate.py 가 실행한 SQL (MySQL 8.0)
SELECT COUNT(*) FROM tz_bronze.b_a_company_master;

SELECT COUNT(*) FROM tz_silver.s_corp;

SELECT COUNT(*) FROM tz_bronze.b_a_disclosures;

SELECT COUNT(*) FROM tz_silver.s_dscl;

SELECT COUNT(*) FROM tz_bronze.b_a_disclosure_documents;

SELECT COUNT(*) FROM tz_silver.s_dscl_doc;

SELECT COUNT(*) FROM tz_bronze.b_a_financial_summary;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt;

SELECT COUNT(*) FROM tz_bronze.b_a_metric_definitions;

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc_def;

SELECT COUNT(*) FROM tz_bronze.b_a_financial_items;

SELECT COUNT(*) FROM tz_silver.s_fin_item;

SELECT COUNT(*) FROM tz_bronze.b_b_security_master;

SELECT COUNT(*) FROM tz_silver.s_stock;

SELECT COUNT(*) FROM tz_bronze.b_b_stock_daily_price;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc;

SELECT COUNT(*) FROM tz_bronze.b_b_market_index_daily;

SELECT COUNT(*) FROM tz_silver.s_idx_daily_prc;

SELECT COUNT(*) FROM tz_bronze.b_b_investor_trading_daily;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily;

SELECT COUNT(*) FROM tz_bronze.b_b_foreign_holding_daily;

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily;

SELECT COUNT(*) FROM tz_bronze.b_b_cfd_daily;

SELECT COUNT(*) FROM tz_silver.s_cfd_bal_daily;

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc;

SELECT COUNT(*) FROM (SELECT symbol, trade_date FROM tz_bronze.b_b_stock_daily_price UNION SELECT symbol, trade_date FROM tz_bronze.b_b_investor_trading_daily) k;

SELECT COUNT(*) FROM tz_silver.s_conn_stts;

SELECT COUNT(*) FROM tz_bronze.b_b_price_investor_availability WHERE has_price='true' AND has_investor_data='true';

SELECT COUNT(*) FROM tz_silver.s_conn_stts WHERE conn_stts_cd='BOTH';

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily;

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry;

SELECT COUNT(*) FROM tz_bronze.b_a_review_issues;

SELECT COUNT(*) FROM tz_silver.s_dq_issue WHERE detect_stage_cd='A_SELF';

SELECT (SELECT COUNT(*) FROM tz_bronze.b_b_data_quality_issues)+(SELECT COUNT(*) FROM tz_bronze.b_b_bronze_unresolved_issues)+(SELECT COUNT(*) FROM tz_bronze.b_b_pending_recovery_review);

SELECT COUNT(*) FROM tz_silver.s_dq_issue WHERE detect_stage_cd='B_SELF';

SELECT SUM(CAST(net_buy_volume AS SIGNED)) FROM tz_bronze.b_b_investor_trading_daily;

SELECT SUM(net_buy_qty) FROM tz_silver.s_invstr_trd_daily;

SELECT SUM(CAST(close_price AS DECIMAL(18,4))) FROM tz_bronze.b_b_stock_daily_price;

SELECT SUM(close_prc) FROM tz_silver.s_stock_daily_prc;

SELECT SUM(CAST(NULLIF(thstrm_amount,'') AS DECIMAL(30,0))) FROM tz_bronze.b_a_financial_items;

SELECT SUM(cur_amt) FROM tz_silver.s_fin_item;

SELECT SUM(thstrm_amount='') FROM tz_bronze.b_a_financial_items;

SELECT SUM(cur_amt IS NULL) FROM tz_silver.s_fin_item;

SELECT SUM(CAST(NULLIF(revenue_ytd,'') AS DECIMAL(30,0))) FROM tz_bronze.b_a_financial_summary;

SELECT SUM(mtrc_amt) FROM tz_silver.s_fin_mtrc WHERE mtrc_cd='REVENUE' AND prd_type_cd='YTD';

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT cd_grp_id,cd_val FROM tz_silver.s_cmn_cd) d) FROM tz_silver.s_cmn_cd;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT corp_cd FROM tz_silver.s_corp) d) FROM tz_silver.s_corp;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT rcept_no FROM tz_silver.s_dscl) d) FROM tz_silver.s_dscl;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT rcept_no FROM tz_silver.s_dscl_doc) d) FROM tz_silver.s_dscl_doc;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT fin_rpt_id FROM tz_silver.s_fin_rpt) d) FROM tz_silver.s_fin_rpt;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT mtrc_cd FROM tz_silver.s_fin_mtrc_def) d) FROM tz_silver.s_fin_mtrc_def;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT fin_rpt_id,mtrc_cd,prd_type_cd FROM tz_silver.s_fin_mtrc) d) FROM tz_silver.s_fin_mtrc;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT fin_item_id FROM tz_silver.s_fin_item) d) FROM tz_silver.s_fin_item;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd FROM tz_silver.s_stock) d) FROM tz_silver.s_stock;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd,trd_dt FROM tz_silver.s_stock_daily_prc) d) FROM tz_silver.s_stock_daily_prc;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT idx_cd,trd_dt FROM tz_silver.s_idx_daily_prc) d) FROM tz_silver.s_idx_daily_prc;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd,trd_dt,invstr_type_cd FROM tz_silver.s_invstr_trd_daily) d) FROM tz_silver.s_invstr_trd_daily;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd,trd_dt FROM tz_silver.s_frgn_hold_daily) d) FROM tz_silver.s_frgn_hold_daily;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd,trd_dt FROM tz_silver.s_cfd_bal_daily) d) FROM tz_silver.s_cfd_bal_daily;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT map_id FROM tz_silver.s_corp_stock_map) d) FROM tz_silver.s_corp_stock_map;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd,trd_dt FROM tz_silver.s_conn_stts) d) FROM tz_silver.s_conn_stts;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT issue_id FROM tz_silver.s_dq_issue) d) FROM tz_silver.s_dq_issue;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT stock_cd,trd_dt FROM tz_gold.g_ai_stock_daily) d) FROM tz_gold.g_ai_stock_daily;

SELECT COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT fin_rpt_id FROM tz_gold.g_fin_rpt_mkt_smry) d) FROM tz_gold.g_fin_rpt_mkt_smry;

SELECT COUNT(*) FROM tz_silver.s_dscl x LEFT JOIN tz_silver.s_corp r ON r.corp_cd=x.corp_cd WHERE x.corp_cd IS NOT NULL AND r.corp_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl_doc x LEFT JOIN tz_silver.s_dscl r ON r.rcept_no=x.rcept_no WHERE x.rcept_no IS NOT NULL AND r.rcept_no IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl_doc x LEFT JOIN tz_silver.s_corp r ON r.corp_cd=x.corp_cd WHERE x.corp_cd IS NOT NULL AND r.corp_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_corp r ON r.corp_cd=x.corp_cd WHERE x.corp_cd IS NOT NULL AND r.corp_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_dscl r ON r.rcept_no=x.rcept_no WHERE r.rcept_no IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt WHERE dscl_join_stts_cd='NOT_IN_INPUT_COVERAGE';

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc x LEFT JOIN tz_silver.s_fin_rpt r ON r.fin_rpt_id=x.fin_rpt_id WHERE x.fin_rpt_id IS NOT NULL AND r.fin_rpt_id IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc x LEFT JOIN tz_silver.s_fin_mtrc_def r ON r.mtrc_cd=x.mtrc_cd WHERE x.mtrc_cd IS NOT NULL AND r.mtrc_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_fin_rpt r ON r.fin_rpt_id=x.fin_rpt_id WHERE x.fin_rpt_id IS NOT NULL AND r.fin_rpt_id IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_corp r ON r.corp_cd=x.corp_cd WHERE x.corp_cd IS NOT NULL AND r.corp_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_cfd_bal_daily x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map x LEFT JOIN tz_silver.s_corp r ON r.corp_cd=x.corp_cd WHERE x.corp_cd IS NOT NULL AND r.corp_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_stock r ON r.stock_cd=x.stock_cd WHERE x.stock_cd IS NOT NULL AND r.stock_cd IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_fin_rpt r ON r.fin_rpt_id=x.fin_rpt_id WHERE x.fin_rpt_id IS NOT NULL AND r.fin_rpt_id IS NULL;

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry x LEFT JOIN tz_silver.s_fin_rpt r ON r.fin_rpt_id=x.fin_rpt_id WHERE x.fin_rpt_id IS NOT NULL AND r.fin_rpt_id IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map WHERE map_stts_cd='MATCHED';

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map WHERE map_stts_cd<>'MATCHED';

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map m JOIN tz_silver.s_corp c ON c.corp_cd=m.corp_cd WHERE c.stock_cd<>m.stock_cd;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_bronze.b_b_stock_daily_price b ON x.stock_cd=b.symbol AND x.trd_dt=b.trade_date AND x.src_file_path=b.source_file AND x.src_row_no=CAST(b.source_row AS UNSIGNED) WHERE b.ldng_row_no IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_bronze.b_b_investor_trading_daily b ON x.stock_cd=b.symbol AND x.trd_dt=b.trade_date AND x.src_json_path=b.json_path AND x.src_row_no=CAST(b.source_row AS UNSIGNED) AND x.src_file_path=b.source_file WHERE b.ldng_row_no IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_bronze.b_a_financial_items b ON x.fin_item_id=b.financial_item_id AND x.src_file_path=b._source_file AND x.src_row_no=CAST(b._source_row AS UNSIGNED) WHERE b.ldng_row_no IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl x LEFT JOIN tz_bronze.b_a_disclosures b ON x.rcept_no=b.rcept_no AND x.src_file_path=b._source_file AND x.src_row_no=CAST(b._source_row AS UNSIGNED) WHERE b.ldng_row_no IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_bronze.b_a_financial_summary b ON x.fin_rpt_id=b.financial_report_id AND x.src_row_no=b.ldng_row_no WHERE b.ldng_row_no IS NULL;

SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, COLUMN_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA LIKE 'tz\_%';

SELECT COUNT(*) FROM tz_meta.m_std_term t LEFT JOIN information_schema.COLUMNS c ON c.TABLE_SCHEMA IN ('tz_silver','tz_gold','tz_meta') AND c.TABLE_NAME=t.tbl_nm AND c.COLUMN_NAME=t.col_nm WHERE c.COLUMN_NAME IS NULL OR REPLACE(LOWER(c.COLUMN_TYPE),' ','') <> REPLACE(LOWER(t.data_type_nm),' ','');

SELECT COUNT(*) FROM tz_silver.s_corp x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CORP_CLS' AND c.cd_val=x.corp_cls_cd WHERE x.corp_cls_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl_doc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DOC_STTS' AND c.cd_val=x.doc_stts_cd WHERE x.doc_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl_doc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='RPT' AND c.cd_val=x.rpt_cd WHERE x.rpt_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='FS_DIV' AND c.cd_val=x.fs_div_cd WHERE x.fs_div_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CRNCY' AND c.cd_val=x.crncy_cd WHERE x.crncy_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DSCL_JOIN_STTS' AND c.cd_val=x.dscl_join_stts_cd WHERE x.dscl_join_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CAL_PRD_STTS' AND c.cd_val=x.cal_prd_stts_cd WHERE x.cal_prd_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CF_PRD_STTS' AND c.cd_val=x.cf_prd_stts_cd WHERE x.cf_prd_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.pit_join_elig_yn WHERE x.pit_join_elig_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.same_prd_cmpr_elig_yn WHERE x.same_prd_cmpr_elig_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_rpt x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc_def x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MTRC' AND c.cd_val=x.mtrc_cd WHERE x.mtrc_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MTRC' AND c.cd_val=x.mtrc_cd WHERE x.mtrc_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_mtrc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='PRD_TYPE' AND c.cd_val=x.prd_type_cd WHERE x.prd_type_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='RPT' AND c.cd_val=x.rpt_cd WHERE x.rpt_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='FS_DIV' AND c.cd_val=x.fs_div_cd WHERE x.fs_div_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='STMT_DIV' AND c.cd_val=x.stmt_div_cd WHERE x.stmt_div_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CRNCY' AND c.cd_val=x.crncy_cd WHERE x.crncy_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_fin_item x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MKT' AND c.cd_val=x.mkt_cd WHERE x.mkt_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SEC_TYPE' AND c.cd_val=x.sec_type_cd WHERE x.sec_type_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.cmn_shr_yn WHERE x.cmn_shr_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='STOCK_STTS' AND c.cd_val=x.stock_stts_cd WHERE x.stock_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CRNCY' AND c.cd_val=x.crncy_cd WHERE x.crncy_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE x.src_kind_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CRNCY' AND c.cd_val=x.crncy_cd WHERE x.crncy_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE x.src_kind_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_idx_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='IDX' AND c.cd_val=x.idx_cd WHERE x.idx_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_idx_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_idx_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE x.src_kind_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='INVSTR_TYPE' AND c.cd_val=x.invstr_type_cd WHERE x.invstr_type_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='INVSTR_TYPE' AND c.cd_val=x.upper_invstr_type_cd WHERE x.upper_invstr_type_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='AGGR_LVL' AND c.cd_val=x.aggr_lvl_cd WHERE x.aggr_lvl_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE x.src_kind_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE x.src_kind_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_cfd_bal_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_cfd_bal_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE x.src_kind_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MAP_STTS' AND c.cd_val=x.map_stts_cd WHERE x.map_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MAP_MTHD' AND c.cd_val=x.map_mthd_cd WHERE x.map_mthd_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.nm_match_yn WHERE x.nm_match_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MAP_STTS' AND c.cd_val=x.map_stts_cd WHERE x.map_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.prc_exist_yn WHERE x.prc_exist_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.invstr_exist_yn WHERE x.invstr_exist_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.frgn_hold_exist_yn WHERE x.frgn_hold_exist_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.cfd_exist_yn WHERE x.cfd_exist_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.fin_avail_yn WHERE x.fin_avail_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='CONN_STTS' AND c.cd_val=x.conn_stts_cd WHERE x.conn_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_conn_stts x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MISS_RSN' AND c.cd_val=x.miss_rsn_cd WHERE x.miss_rsn_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dq_issue x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DETECT_STAGE' AND c.cd_val=x.detect_stage_cd WHERE x.detect_stage_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dq_issue x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='TEAM' AND c.cd_val=x.src_team_cd WHERE x.src_team_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dq_issue x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='ISSUE_TYPE' AND c.cd_val=x.issue_type_cd WHERE x.issue_type_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dq_issue x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SEV' AND c.cd_val=x.sev_cd WHERE x.sev_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dq_issue x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='RESOLVE_STTS' AND c.cd_val=x.resolve_stts_cd WHERE x.resolve_stts_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='MKT' AND c.cd_val=x.mkt_cd WHERE x.mkt_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.invstr_exist_yn WHERE x.invstr_exist_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.fin_avail_yn WHERE x.fin_avail_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='RPT' AND c.cd_val=x.fin_rpt_cd WHERE x.fin_rpt_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='FS_DIV' AND c.cd_val=x.fin_fs_div_cd WHERE x.fin_fs_div_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='RPT' AND c.cd_val=x.rpt_cd WHERE x.rpt_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='FS_DIV' AND c.cd_val=x.fs_div_cd WHERE x.fs_div_cd IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.same_prd_cmpr_elig_yn WHERE x.same_prd_cmpr_elig_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='YN' AND c.cd_val=x.full_cvrg_yn WHERE x.full_cvrg_yn IS NOT NULL AND c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_corp WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_corp WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_dscl WHERE rcept_no IS NOT NULL AND NOT REGEXP_LIKE(rcept_no, '^[0-9]{14}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_dscl WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_dscl WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_dscl_doc WHERE rcept_no IS NOT NULL AND NOT REGEXP_LIKE(rcept_no, '^[0-9]{14}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_dscl_doc WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_dscl_doc WHERE doc_hash IS NOT NULL AND NOT REGEXP_LIKE(doc_hash, '^(sha256:)?[0-9a-f]{64}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_fin_rpt WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_fin_rpt WHERE bsns_yr IS NOT NULL AND NOT REGEXP_LIKE(bsns_yr, '^[0-9]{4}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_fin_rpt WHERE rcept_no IS NOT NULL AND NOT REGEXP_LIKE(rcept_no, '^[0-9]{14}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_fin_item WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_fin_item WHERE rcept_no IS NOT NULL AND NOT REGEXP_LIKE(rcept_no, '^[0-9]{14}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_fin_item WHERE bsns_yr IS NOT NULL AND NOT REGEXP_LIKE(bsns_yr, '^[0-9]{4}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_stock WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_stock WHERE isin_cd IS NOT NULL AND NOT REGEXP_LIKE(isin_cd, '^[A-Z]{2}[A-Z0-9]{9}[0-9]$', 'c');

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_cfd_bal_daily WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_corp_stock_map WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_conn_stts WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_conn_stts WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE fin_bsns_yr IS NOT NULL AND NOT REGEXP_LIKE(fin_bsns_yr, '^[0-9]{4}$', 'c');

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry WHERE corp_cd IS NOT NULL AND NOT REGEXP_LIKE(corp_cd, '^[0-9]{8}$', 'c');

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry WHERE stock_cd IS NOT NULL AND NOT REGEXP_LIKE(stock_cd, '^[0-9]{6}$', 'c');

SELECT COUNT(*) FROM tz_gold.g_fin_rpt_mkt_smry WHERE bsns_yr IS NOT NULL AND NOT REGEXP_LIKE(bsns_yr, '^[0-9]{4}$', 'c');

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE high_prc < GREATEST(open_prc,close_prc,low_prc) OR low_prc > LEAST(open_prc,close_prc);

SELECT COUNT(*) FROM tz_silver.s_idx_daily_prc WHERE high_prc < GREATEST(open_prc,close_prc,low_prc) OR low_prc > LEAST(open_prc,close_prc);

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE LEAST(open_prc,high_prc,low_prc,close_prc) <= 0;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc WHERE trd_qty < 0;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily WHERE buy_qty - sell_qty <> net_buy_qty;

SELECT COUNT(*) FROM (SELECT t.stock_cd, t.trd_dt, t.net_buy_qty, SUM(d.net_buy_qty) s FROM tz_silver.s_invstr_trd_daily t JOIN tz_silver.s_invstr_trd_daily d ON d.stock_cd=t.stock_cd AND d.trd_dt=t.trd_dt AND d.upper_invstr_type_cd='INSTITUTION' WHERE t.invstr_type_cd='INSTITUTION' GROUP BY t.stock_cd, t.trd_dt, t.net_buy_qty HAVING s <> t.net_buy_qty) z;

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily WHERE hold_rt < 0 OR hold_rt > 1;

SELECT COUNT(*) FROM tz_silver.s_frgn_hold_daily WHERE hold_qty > limit_qty;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE dscl_dt IS NOT NULL AND dscl_dt >= trd_dt;

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily g JOIN tz_silver.s_fin_rpt r ON r.fin_rpt_id=g.fin_rpt_id WHERE r.pit_join_elig_yn<>'Y';

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE (fin_avail_yn='Y') <> (fin_rpt_id IS NOT NULL);

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily WHERE dscl_dt IS NOT NULL AND dscl_elps_day_cnt <> DATEDIFF(trd_dt, dscl_dt);

SELECT COUNT(*) FROM (SELECT close_rtn_rt, ROUND(close_prc / LAG(close_prc) OVER (PARTITION BY stock_cd ORDER BY trd_dt) - 1, 8) r FROM tz_gold.g_ai_stock_daily) z WHERE NOT (close_rtn_rt <=> r);

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily g JOIN tz_silver.s_invstr_trd_daily s ON s.stock_cd=g.stock_cd AND s.trd_dt=g.trd_dt AND s.invstr_type_cd='FOREIGNER' WHERE NOT (s.net_buy_qty <=> g.frgn_net_buy_qty);

SELECT COUNT(*) FROM tz_gold.g_ai_stock_daily g JOIN tz_silver.s_fin_mtrc m ON m.fin_rpt_id=g.fin_rpt_id AND m.mtrc_cd='REVENUE' AND m.prd_type_cd='YTD' WHERE NOT (m.mtrc_amt <=> g.rev_ytd_amt);

SELECT COUNT(*) FROM tz_bronze.b_a_financial_summary b JOIN tz_silver.s_dscl d ON d.rcept_no=b.rcept_no WHERE b.disclosure_date<>'' AND DATE(b.disclosure_date)<>d.rcept_dt;

SELECT COUNT(*) FROM tz_bronze.b_b_investor_trading_daily b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='INVSTR_TYPE' AND c.cd_val=b.investor_type WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='INVSTR_TYPE' AND c.cd_val=x.invstr_type_cd WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_bronze.b_b_investor_trading_daily b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='AGGR_LVL' AND c.cd_val=b.aggregation_level WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_invstr_trd_daily x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='AGGR_LVL' AND c.cd_val=x.aggr_lvl_cd WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_bronze.b_b_stock_daily_price b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=b.source_kind WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_stock_daily_prc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='SRC_KIND' AND c.cd_val=x.src_kind_cd WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_bronze.b_a_disclosure_documents b LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DOC_STTS' AND c.cd_val=b.status WHERE c.cd_val IS NULL;

SELECT COUNT(*) FROM tz_silver.s_dscl_doc x LEFT JOIN tz_silver.s_cmn_cd c ON c.cd_grp_id='DOC_STTS' AND c.cd_val=x.doc_stts_cd WHERE c.cd_val IS NULL;

SELECT (SELECT SUM(isCommonShare NOT IN ('Y','N')) FROM tz_bronze.b_b_security_master)+(SELECT SUM(point_in_time_join_eligible NOT IN ('Y','N'))+SUM(same_period_comparison_eligible NOT IN ('Y','N')) FROM tz_bronze.b_a_financial_summary)+(SELECT SUM(has_price NOT IN ('Y','N'))+SUM(has_investor_data NOT IN ('Y','N')) FROM tz_bronze.b_b_price_investor_availability);

SELECT (SELECT SUM(cmn_shr_yn NOT IN ('Y','N')) FROM tz_silver.s_stock)+(SELECT SUM(pit_join_elig_yn NOT IN ('Y','N'))+SUM(same_prd_cmpr_elig_yn NOT IN ('Y','N')) FROM tz_silver.s_fin_rpt)+(SELECT SUM(prc_exist_yn NOT IN ('Y','N'))+SUM(invstr_exist_yn NOT IN ('Y','N')) FROM tz_silver.s_conn_stts);

SELECT (SELECT SUM(NOT REGEXP_LIKE(rcept_dt,'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_bronze.b_a_disclosures)+(SELECT SUM(NOT REGEXP_LIKE(modify_date,'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_bronze.b_a_company_master);

SELECT (SELECT SUM(NOT REGEXP_LIKE(CAST(rcept_dt AS CHAR),'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_silver.s_dscl)+(SELECT SUM(NOT REGEXP_LIKE(CAST(chg_dt AS CHAR),'^[0-9]{4}-[0-9]{2}-[0-9]{2}$')) FROM tz_silver.s_corp);