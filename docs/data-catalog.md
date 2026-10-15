# 전체 데이터·컬럼·관계 사전

기준: 저장소 `data/03_C_integration_20261014`의 고정 스냅샷. Bronze는 DDL 정의만 제공되며 데이터 실물이 없다. Silver·Gold·Meta의 실제 CSV 정보와 표준 사전 정의를 구분한다. 금액은 원·수급은 주·비율은 소수 비율이다. **NULL 허용은 DDL/사전 정책이고 실제 빈값은 CSV 전체 집계**다.

[데이터 안내](data-guide.md) · [프로젝트 목표](project-plan.md) · [표준 용어 CSV](../data/03_C_integration_20261014/02_standard_dictionary/std_term.csv)

## 1. Bronze 18개 테이블 — DDL 기준

원천 업무 컬럼은 TEXT NULL, 적재 메타는 별도 타입이다. 아래 목록에 데이터 건수가 없다는 것은 0행이 아니라 원본 미제공을 뜻한다. 전체 입력 경로·변환 관계는 데이터 안내를 참조한다.

### b_a_company_master

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `corp_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_eng_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `stock_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `modify_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_a_disclosures

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `corp_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_cls` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `stock_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `report_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `rcept_no` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `flr_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `rcept_dt` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `rm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `document_status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `document_zip_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `document_sha256` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_a_disclosure_documents

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `rcept_no` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `stock_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `report_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `rcept_dt` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `zip_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sha256` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `error` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_a_financial_items

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `corp_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `stock_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `rcept_no` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `reprt_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bsns_year` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fs_div` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sj_div` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sj_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `account_id` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `account_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `account_detail` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `thstrm_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `thstrm_amount` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `thstrm_add_amount` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `frmtrm_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `frmtrm_amount` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `frmtrm_q_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `frmtrm_q_amount` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `frmtrm_add_amount` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bfefrmtrm_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bfefrmtrm_amount` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ord` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `currency` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `_source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `financial_report_id` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `financial_item_id` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_a_financial_summary

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `financial_report_id` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `stock_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bsns_year` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `reprt_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `report_label` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `report_quarter` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fs_div` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `rcept_no` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `report_nm` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `disclosure_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `disclosure_join_status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `document_status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `document_zip_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `currency` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `flow_period_months` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `period_start_nominal` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `period_end_nominal` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `calendar_period_status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cf_period_status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `point_in_time_join_eligible` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `same_period_comparison_eligible` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `revenue_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `revenue_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `revenue_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `revenue_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cost_of_sales_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cost_of_sales_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cost_of_sales_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cost_of_sales_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `gross_profit_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `gross_profit_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `gross_profit_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `gross_profit_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sga_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sga_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sga_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sga_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `operating_profit_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `operating_profit_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `operating_profit_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `operating_profit_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_income_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_income_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_income_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_income_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_cost_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_cost_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_cost_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `finance_cost_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pretax_profit_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pretax_profit_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pretax_profit_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pretax_profit_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `income_tax_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `income_tax_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `income_tax_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `income_tax_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_parent_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_parent_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_parent_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_income_parent_prior_3m` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `total_assets_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `total_assets_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `total_liabilities_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `total_liabilities_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `total_equity_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `total_equity_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_assets_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_assets_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `noncurrent_assets_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `noncurrent_assets_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_liabilities_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_liabilities_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `noncurrent_liabilities_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `noncurrent_liabilities_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cash_and_equivalents_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cash_and_equivalents_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_receivables_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_receivables_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_and_other_receivables_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_and_other_receivables_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `inventories_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `inventories_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_payables_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_payables_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_and_other_payables_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_and_other_payables_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `short_term_borrowings_reported_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `short_term_borrowings_reported_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `long_term_borrowings_reported_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `long_term_borrowings_reported_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_portion_long_term_debt_reported_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_portion_long_term_debt_reported_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_lease_liabilities_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_lease_liabilities_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `noncurrent_lease_liabilities_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `noncurrent_lease_liabilities_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `property_plant_equipment_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `property_plant_equipment_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `intangible_assets_asof` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `intangible_assets_prior_year_end` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `operating_cash_flow_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `operating_cash_flow_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `investing_cash_flow_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `investing_cash_flow_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `financing_cash_flow_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `financing_cash_flow_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ppe_purchase_reported_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ppe_purchase_reported_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `intangible_purchase_reported_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `intangible_purchase_reported_prior_ytd` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `metric_review_count` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `custom_mapped_count` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `metric_conflict_count` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `missing_core_metrics` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_a_metric_definitions

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `metric` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `label_ko` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `statement` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `account_ids` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `reason_ko` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `custom_names` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `name_guard` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_a_review_issues

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `financial_report_id` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `corp_name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `metric` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `severity` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `issue` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `detail` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_security_master

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `name` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `englishName` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `isinCode` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `market` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `securityType` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `isCommonShare` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `currency` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `listDate` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `delistDate` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sharesOutstanding` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `leverageFactor` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `koreanMarketDetail` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_stock_daily_price

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `timestamp` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `open_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `high_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `low_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `close_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `volume` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `currency` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_market_index_daily

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `index_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `timestamp` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `open_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `high_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `low_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `close_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `volume` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_investor_trading_daily

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `investor_type` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `parent_type` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `aggregation_level` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `buy_volume` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sell_volume` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `net_buy_volume` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_column` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `json_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_foreign_holding_daily

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `holding_quantity` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `limit_quantity` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `holding_rate` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_column` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `json_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_cfd_daily

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `buy_balance_quantity` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `buy_balance_rate` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sell_balance_quantity` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `sell_balance_rate` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_column` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `json_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_price_investor_availability

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `has_price` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `has_investor_data` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `missing_reason` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `missing_issue_codes` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_investor_source_daily

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `updated_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `individual` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `foreigner` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `institution` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `otherCorporation` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `foreignerHolding` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `cfd` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `bronze_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `pipeline_version` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_kind` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_path` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_data_quality_issues

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `table` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `column` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `issue_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `reason` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_bronze_unresolved_issues

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `dataset` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_data_row_1based` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `column_or_group` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `issue_code` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `original_value` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `current_value` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `reason` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `required_evidence` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `resolution` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

### b_b_pending_recovery_review

상태: **데이터 미포함 / DDL 포함**. PK: `ldng_row_no`.

| 컬럼 | 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `ldng_row_no` | INT | N | 적재 행 번호(원천 CSV 데이터 행, 1부터) |
| `source_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `source_row` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `symbol` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `trade_date` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `issue_codes` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `affected_columns` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `raw_file` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `fetched_at` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `api_record_json` | MEDIUMTEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `overlap_rows` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `overlap_matched` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `overlap_mismatched` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `error` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `review_status` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `review_notes` | TEXT | Y | AS-IS 원본 컬럼(문자열 그대로) |
| `ldng_file_path` | VARCHAR(500) | N | 적재 원천 파일(인계 폴더 기준) |
| `ldng_file_hash` | VARCHAR(80) | N | 적재 원천 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) | N | 적재 실행 식별자 |

## 2. Silver·Gold·Meta — 표준 사전과 실제 CSV

현재 CSV가 없는 Meta 테이블은 DDL/정의만 표시한다. FK는 제공 사전에 선언된 관계이며 `논리 FK`는 DB 제약이 아니다.

### s_cmn_cd — 공통코드

- DB/계층: `tz_silver` / SILVER
- 행 단위: 코드그룹·코드값당 1행
- PK: `cd_grp_id+cd_val`
- FK: 없음
- 논리 FK: 없음
- 원천: C 표준 사전
- 실제 CSV: [s_cmn_cd.csv](../data/03_C_integration_20261014/04_output/silver/s_cmn_cd.csv) / 133행 × 6열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `cd_grp_id` | 코드그룹 식별자 | VARCHAR(64) | N | Y |  | 0 |  |
| `cd_val` | 코드값 | VARCHAR(200) | N | Y |  | 0 |  |
| `cd_nm` | 코드명 | VARCHAR(200) | N | N |  | 0 |  |
| `cd_desc_txt` | 코드 설명 | VARCHAR(2000) | Y | N |  | 0 |  |
| `sort_ord_no` | 정렬 순서 번호 | INT | N | N |  | 0 |  |
| `asis_val_txt` | 현행(AS-IS) 값 목록 | VARCHAR(2000) | Y | N |  | 38 |  |

### s_corp — 기업

- DB/계층: `tz_silver` / SILVER
- 행 단위: OpenDART 고유번호당 1행
- PK: `corp_cd`
- FK: 없음
- 논리 FK: 없음
- 원천: A support/company_master.csv
- 실제 CSV: [s_corp.csv](../data/03_C_integration_20261014/04_output/silver/s_corp.csv) / 20행 × 10열
- `chg_dt` 범위: 2022-12-06 ~ 2026-04-01

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `corp_cd` | 기업 코드 | CHAR(8) | N | Y |  | 0 | company_master.corp_code |
| `corp_nm` | 기업명 | VARCHAR(200) | N | N |  | 0 | company_master.corp_name |
| `corp_eng_nm` | 기업 영문명 | VARCHAR(200) | N | N |  | 0 | company_master.corp_eng_name |
| `stock_cd` | 종목 코드 | CHAR(6) | N | N |  | 0 | company_master.stock_code |
| `chg_dt` | 변경 일자 | DATE | N | N |  | 0 | company_master.modify_date (YYYYMMDD→DATE) |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) A |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | _source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | _source_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | _source_version |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_dscl — 공시

- DB/계층: `tz_silver` / SILVER
- 행 단위: 공시 접수번호당 1행
- PK: `rcept_no`
- FK: corp_cd→s_corp.corp_cd
- 논리 FK: 없음
- 원천: A support/disclosures_with_documents.csv (문서 컬럼 제외: s_dscl_doc 로 분리)
- 실제 CSV: [s_dscl.csv](../data/03_C_integration_20261014/04_output/silver/s_dscl.csv) / 11,748행 × 14열
- `rcept_dt` 범위: 2023-01-02 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `rcept_no` | 접수 번호 | CHAR(14) | N | Y |  | 0 | disclosures.rcept_no |
| `corp_cd` | 기업 코드 | CHAR(8) | N | N |  | 0 | disclosures.corp_code |
| `corp_nm` | 기업명(공시 당시) | VARCHAR(200) | N | N |  | 0 | disclosures.corp_name |
| `corp_cls_cd` | 법인구분 코드 | VARCHAR(50) | N | N | CORP_CLS | 0 | disclosures.corp_cls |
| `stock_cd` | 종목 코드 | CHAR(6) | N | N |  | 0 | disclosures.stock_code |
| `rpt_nm` | 보고서명 | VARCHAR(500) | N | N |  | 0 | disclosures.report_nm |
| `flr_nm` | 제출인명 | VARCHAR(200) | N | N |  | 0 | disclosures.flr_nm |
| `rcept_dt` | 접수 일자 | DATE | N | N |  | 0 | disclosures.rcept_dt (YYYYMMDD→DATE) |
| `rmk_txt` | 비고 내용 | VARCHAR(2000) | Y | N |  | 7,461 | disclosures.rm |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) A |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | _source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | _source_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | _source_version |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_dscl_doc — 공시 원문 문서

- DB/계층: `tz_silver` / SILVER
- 행 단위: 원문 수집 대상 접수번호당 1행
- PK: `rcept_no`
- FK: rcept_no→s_dscl.rcept_no; corp_cd→s_corp.corp_cd
- 논리 FK: 없음
- 원천: A support/disclosure_documents.csv
- 실제 CSV: [s_dscl_doc.csv](../data/03_C_integration_20261014/04_output/silver/s_dscl_doc.csv) / 753행 × 11열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `rcept_no` | 접수 번호 | CHAR(14) | N | Y |  | 0 | disclosure_documents.rcept_no |
| `corp_cd` | 기업 코드 | CHAR(8) | N | N |  | 0 | disclosure_documents.corp_code |
| `doc_stts_cd` | 문서 상태 코드 | VARCHAR(50) | N | N | DOC_STTS | 0 | disclosure_documents.status |
| `doc_zip_path` | 문서 압축파일 경로 | VARCHAR(500) | Y | N |  | 1 | disclosure_documents.zip_path |
| `doc_hash` | 문서 해시값 | VARCHAR(80) | Y | N |  | 1 | disclosure_documents.sha256 |
| `err_msg_txt` | 오류 메시지 내용 | VARCHAR(2000) | Y | N |  | 752 | disclosure_documents.error |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) A |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | _source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | _source_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | _source_version |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_fin_rpt — 재무 보고서

- DB/계층: `tz_silver` / SILVER
- 행 단위: 기업·사업연도·보고서·연결구분·접수번호당 1행
- PK: `fin_rpt_id`
- FK: corp_cd→s_corp.corp_cd
- 논리 FK: rcept_no→s_dscl.rcept_no (61건 공시목록 수집 범위 밖 → 물리 FK 미적용, 검증으로 관리)
- 원천: A opendart_financial_summary_20_companies.csv (헤더 컬럼; report_label·report_quarter·report_nm·disclosure_date·document_* 는 정규화로 제거)
- 실제 CSV: [s_fin_rpt.csv](../data/03_C_integration_20261014/04_output/silver/s_fin_rpt.csv) / 320행 × 24열
- `prd_start_dt` 범위: 2022-01-01 ~ 2025-01-01
- `prd_end_dt` 범위: 2022-03-31 ~ 2025-12-31

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `fin_rpt_id` | 재무 보고서 식별자 | VARCHAR(64) | N | Y |  | 0 | summary.financial_report_id |
| `corp_cd` | 기업 코드 | CHAR(8) | N | N |  | 0 | summary.corp_code |
| `bsns_yr` | 사업 연도 | CHAR(4) | N | N |  | 0 | summary.bsns_year |
| `rpt_cd` | 보고서 코드 | VARCHAR(50) | N | N | RPT | 0 | summary.reprt_code |
| `fs_div_cd` | 재무제표 구분 코드 | VARCHAR(50) | N | N | FS_DIV | 0 | summary.fs_div |
| `rcept_no` | 접수 번호 | CHAR(14) | N | N |  | 0 | summary.rcept_no |
| `crncy_cd` | 통화 코드 | VARCHAR(50) | N | N | CRNCY | 0 | summary.currency |
| `flow_prd_mm_cnt` | 흐름 기간 개월 건수 | INT | N | N |  | 0 | summary.flow_period_months |
| `prd_start_dt` | 기간 시작 일자(명목) | DATE | N | N |  | 0 | summary.period_start_nominal |
| `prd_end_dt` | 기간 종료 일자(명목) | DATE | N | N |  | 0 | summary.period_end_nominal |
| `dscl_join_stts_cd` | 공시 연결 상태 코드 | VARCHAR(50) | N | N | DSCL_JOIN_STTS | 0 | summary.disclosure_join_status |
| `cal_prd_stts_cd` | 달력 기간 상태 코드 | VARCHAR(50) | N | N | CAL_PRD_STTS | 0 | summary.calendar_period_status |
| `cf_prd_stts_cd` | 현금흐름 기간 상태 코드 | VARCHAR(50) | N | N | CF_PRD_STTS | 0 | summary.cf_period_status |
| `pit_join_elig_yn` | 시점 조인 적격 여부 | CHAR(1) | N | N | YN | 0 | summary.point_in_time_join_eligible (1/0→Y/N) |
| `same_prd_cmpr_elig_yn` | 동일 기간 비교 적격 여부 | CHAR(1) | N | N | YN | 0 | summary.same_period_comparison_eligible (1/0→Y/N) |
| `mtrc_review_cnt` | 지표 검토 건수 | INT | N | N |  | 0 | summary.metric_review_count |
| `custom_map_cnt` | 사용자정의 매핑 건수 | INT | N | N |  | 0 | summary.custom_mapped_count |
| `mtrc_conflict_cnt` | 지표 충돌 건수 | INT | N | N |  | 0 | summary.metric_conflict_count |
| `core_mtrc_miss_txt` | 핵심 지표 누락 내용 | VARCHAR(2000) | Y | N |  | 320 | summary.missing_core_metrics |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) A |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | (C 부여) opendart_financial_summary_20_companies.csv |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | (C 부여) 요약 CSV 데이터 행 번호 |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | summary.source_version |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_fin_mtrc_def — 재무 지표 정의

- DB/계층: `tz_silver` / SILVER
- 행 단위: 지표당 1행
- PK: `mtrc_cd`
- FK: 없음
- 논리 FK: 없음
- 원천: A support/metric_definitions.csv
- 실제 CSV: [s_fin_mtrc_def.csv](../data/03_C_integration_20261014/04_output/silver/s_fin_mtrc_def.csv) / 36행 × 8열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `mtrc_cd` | 지표 코드 | VARCHAR(50) | N | Y | MTRC | 0 | metric_definitions.metric (대문자) |
| `mtrc_nm` | 지표명 | VARCHAR(200) | N | N |  | 0 | metric_definitions.label_ko |
| `stmt_div_txt` | 재무제표 양식 내용 | VARCHAR(2000) | N | N |  | 0 | metric_definitions.statement |
| `acnt_id_txt` | 계정 식별자 목록 내용 | VARCHAR(2000) | N | N |  | 0 | metric_definitions.account_ids |
| `select_rsn_txt` | 선정 사유 내용 | VARCHAR(2000) | N | N |  | 0 | metric_definitions.reason_ko |
| `custom_nm_txt` | 사용자정의 계정명 내용 | VARCHAR(2000) | Y | N |  | 14 | metric_definitions.custom_names |
| `guard_txt` | 제외조건 내용 | VARCHAR(2000) | Y | N |  | 32 | metric_definitions.name_guard |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_fin_mtrc — 재무 지표값

- DB/계층: `tz_silver` / SILVER
- 행 단위: 재무보고서·지표·기간유형당 1행(넓은 표 → 세로 표 정규화)
- PK: `fin_rpt_id+mtrc_cd+prd_type_cd`
- FK: fin_rpt_id→s_fin_rpt.fin_rpt_id; mtrc_cd→s_fin_mtrc_def.mtrc_cd
- 논리 FK: 없음
- 원천: A opendart_financial_summary_20_companies.csv (94개 지표 컬럼 UNPIVOT)
- 실제 CSV: [s_fin_mtrc.csv](../data/03_C_integration_20261014/04_output/silver/s_fin_mtrc.csv) / 30,080행 × 6열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `fin_rpt_id` | 재무 보고서 식별자 | VARCHAR(64) | N | Y |  | 0 | summary.financial_report_id |
| `mtrc_cd` | 지표 코드 | VARCHAR(50) | N | Y | MTRC | 0 | summary.<metric>_* 컬럼명의 지표부 |
| `prd_type_cd` | 기간 유형 코드 | VARCHAR(50) | N | Y | PRD_TYPE | 0 | summary.<metric>_* 컬럼명의 기간 접미사 |
| `mtrc_amt` | 지표 금액 | DECIMAL(20,0) | Y | N |  | 5,544 | summary.<metric>_<period> 값(빈값=NULL) |
| `src_col_nm` | 원천 컬럼명 | VARCHAR(200) | N | N |  | 0 | summary 컬럼명 |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_fin_item — 재무 계정 상세

- DB/계층: `tz_silver` / SILVER
- 행 단위: 원천 재무 CSV 1행 = 1행
- PK: `fin_item_id`
- FK: fin_rpt_id→s_fin_rpt.fin_rpt_id; corp_cd→s_corp.corp_cd
- 논리 FK: 없음
- 원천: A support/financial_items_all.csv (corp_name·stock_code·sj_nm 은 정규화로 제거)
- 실제 CSV: [s_fin_item.csv](../data/03_C_integration_20261014/04_output/silver/s_fin_item.csv) / 66,729행 × 28열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `fin_item_id` | 재무 항목 식별자 | VARCHAR(64) | N | Y |  | 0 | financial_items_all.financial_item_id |
| `fin_rpt_id` | 재무 보고서 식별자 | VARCHAR(64) | N | N |  | 0 | financial_items_all.financial_report_id |
| `corp_cd` | 기업 코드 | CHAR(8) | N | N |  | 0 | financial_items_all.corp_code |
| `rcept_no` | 접수 번호 | CHAR(14) | N | N |  | 0 | financial_items_all.rcept_no |
| `bsns_yr` | 사업 연도 | CHAR(4) | N | N |  | 0 | financial_items_all.bsns_year |
| `rpt_cd` | 보고서 코드 | VARCHAR(50) | N | N | RPT | 0 | financial_items_all.reprt_code |
| `fs_div_cd` | 재무제표 구분 코드 | VARCHAR(50) | N | N | FS_DIV | 0 | financial_items_all.fs_div |
| `stmt_div_cd` | 재무제표 양식 코드 | VARCHAR(50) | N | N | STMT_DIV | 0 | financial_items_all.sj_div |
| `acnt_id` | 계정 식별자 | VARCHAR(200) | N | N |  | 0 | financial_items_all.account_id ('-표준계정코드 미사용-' 원값 보존) |
| `acnt_nm` | 계정명 | VARCHAR(200) | N | N |  | 0 | financial_items_all.account_nm |
| `acnt_dtl_nm` | 계정 상세명 | VARCHAR(500) | N | N |  | 0 | financial_items_all.account_detail ('-'=상세 없음, 원값 보존) |
| `cur_prd_nm` | 당기 기간명 | VARCHAR(200) | Y | N |  | 0 | thstrm_nm |
| `cur_amt` | 당기 금액 | DECIMAL(20,0) | Y | N |  | 2,202 | thstrm_amount |
| `cur_cum_amt` | 당기 누적 금액 | DECIMAL(20,0) | Y | N |  | 59,648 | thstrm_add_amount |
| `prev_prd_nm` | 전기 기간명 | VARCHAR(200) | Y | N |  | 36,256 | frmtrm_nm |
| `prev_amt` | 전기 금액 | DECIMAL(20,0) | Y | N |  | 37,011 | frmtrm_amount |
| `prev_qtr_prd_nm` | 전기 분기 기간명 | VARCHAR(200) | Y | N |  | 30,473 | frmtrm_q_nm |
| `prev_qtr_amt` | 전기 분기 금액 | DECIMAL(20,0) | Y | N |  | 31,866 | frmtrm_q_amount |
| `prev_cum_amt` | 전기 누적 금액 | DECIMAL(20,0) | Y | N |  | 59,616 | frmtrm_add_amount |
| `bfr_prev_prd_nm` | 전전기 기간명 | VARCHAR(200) | Y | N |  | 48,151 | bfefrmtrm_nm |
| `bfr_prev_amt` | 전전기 금액 | DECIMAL(20,0) | Y | N |  | 49,018 | bfefrmtrm_amount |
| `sort_ord_no` | 정렬 순서 번호 | INT | N | N |  | 0 | ord |
| `crncy_cd` | 통화 코드 | VARCHAR(50) | N | N | CRNCY | 0 | currency |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) A |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | _source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | _source_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | _source_version |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | (C 부여) |

### s_stock — 종목

- DB/계층: `tz_silver` / SILVER
- 행 단위: 종목코드당 1행
- PK: `stock_cd`
- FK: 없음
- 논리 FK: 없음
- 원천: B silver/security_master.csv
- 실제 CSV: [s_stock.csv](../data/03_C_integration_20261014/04_output/silver/s_stock.csv) / 20행 × 24열
- `list_dt` 범위: 1966-03-18 ~ 2020-08-06

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 | security_master.symbol |
| `stock_nm` | 종목명 | VARCHAR(200) | N | N |  | 0 | security_master.name |
| `stock_eng_nm` | 종목 영문명 | VARCHAR(200) | N | N |  | 0 | security_master.englishName |
| `isin_cd` | ISIN 코드 | CHAR(12) | N | N |  | 0 | security_master.isinCode |
| `mkt_cd` | 시장 코드 | VARCHAR(50) | N | N | MKT | 0 | security_master.market |
| `sec_type_cd` | 증권 유형 코드 | VARCHAR(50) | N | N | SEC_TYPE | 0 | security_master.securityType |
| `cmn_shr_yn` | 보통 주식 여부 | CHAR(1) | N | N | YN | 0 | security_master.isCommonShare (True/False→Y/N) |
| `stock_stts_cd` | 종목 상태 코드 | VARCHAR(50) | N | N | STOCK_STTS | 0 | security_master.status |
| `crncy_cd` | 통화 코드 | VARCHAR(50) | N | N | CRNCY | 0 | security_master.currency |
| `list_dt` | 상장 일자 | DATE | N | N |  | 0 | security_master.listDate |
| `delist_dt` | 상장폐지 일자 | DATE | Y | N |  | 20 | security_master.delistDate |
| `outstd_shr_qty` | 발행 주식 수량 | BIGINT | N | N |  | 0 | security_master.sharesOutstanding |
| `lvrg_val` | 레버리지 값 | DECIMAL(18,6) | Y | N |  | 20 | security_master.leverageFactor |
| `mkt_dtl_txt` | 시장 상세 내용(JSON) | TEXT | N | N |  | 0 | security_master.koreanMarketDetail |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) B |
| `src_kind_cd` | 원천 종류 코드 | VARCHAR(50) | N | N | SRC_KIND | 0 | source_kind |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | source_row |
| `bronze_row_no` | 브론즈 행 번호 | INT | Y | N |  | 0 | bronze_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | source_version |
| `fetch_dttm` | API 조회 일시 | DATETIME | Y | N |  | 20 | fetched_at |
| `api_raw_file_path` | API 원응답 파일 경로 | VARCHAR(500) | Y | N |  | 20 | api_raw_file |
| `api_rcrd_path` | API 레코드 경로 | VARCHAR(500) | Y | N |  | 20 | api_record_path |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적) |

### s_stock_daily_prc — 종목 일별 가격

- DB/계층: `tz_silver` / SILVER
- 행 단위: 종목·거래일당 1행
- PK: `stock_cd+trd_dt`
- FK: stock_cd→s_stock.stock_cd
- 논리 FK: 없음
- 원천: B silver/stock_daily_price.csv
- 실제 CSV: [s_stock_daily_prc.csv](../data/03_C_integration_20261014/04_output/silver/s_stock_daily_prc.csv) / 17,440행 × 19열
- `trd_dt` 범위: 2022-12-01 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 | stock_daily_price.symbol |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 | stock_daily_price.trade_date |
| `candle_dttm` | 봉 일시 | DATETIME | N | N |  | 0 | stock_daily_price.timestamp (+09:00 → KST DATETIME) |
| `open_prc` | 시가 가격 | DECIMAL(18,4) | N | N |  | 0 | open_price |
| `high_prc` | 고가 가격 | DECIMAL(18,4) | N | N |  | 0 | high_price |
| `low_prc` | 저가 가격 | DECIMAL(18,4) | N | N |  | 0 | low_price |
| `close_prc` | 종가 가격 | DECIMAL(18,4) | N | N |  | 0 | close_price |
| `trd_qty` | 거래 수량 | BIGINT | N | N |  | 0 | volume |
| `crncy_cd` | 통화 코드 | VARCHAR(50) | N | N | CRNCY | 0 | currency |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) B |
| `src_kind_cd` | 원천 종류 코드 | VARCHAR(50) | N | N | SRC_KIND | 0 | source_kind |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | source_row |
| `bronze_row_no` | 브론즈 행 번호 | INT | Y | N |  | 443 | bronze_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | source_version |
| `fetch_dttm` | API 조회 일시 | DATETIME | Y | N |  | 16,997 | fetched_at |
| `api_raw_file_path` | API 원응답 파일 경로 | VARCHAR(500) | Y | N |  | 16,997 | api_raw_file |
| `api_rcrd_path` | API 레코드 경로 | VARCHAR(500) | Y | N |  | 16,997 | api_record_path |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적) |

### s_idx_daily_prc — 지수 일별 가격

- DB/계층: `tz_silver` / SILVER
- 행 단위: 지수·거래일당 1행
- PK: `idx_cd+trd_dt`
- FK: 없음
- 논리 FK: 없음
- 원천: B silver/market_index_daily.csv
- 실제 CSV: [s_idx_daily_prc.csv](../data/03_C_integration_20261014/04_output/silver/s_idx_daily_prc.csv) / 1,744행 × 18열
- `trd_dt` 범위: 2022-12-01 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `idx_cd` | 지수 코드 | VARCHAR(50) | N | Y | IDX | 0 | market_index_daily.index_code |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 | trade_date |
| `candle_dttm` | 봉 일시 | DATETIME | N | N |  | 0 | timestamp |
| `open_prc` | 시가 가격 | DECIMAL(18,4) | N | N |  | 0 | open_price |
| `high_prc` | 고가 가격 | DECIMAL(18,4) | N | N |  | 0 | high_price |
| `low_prc` | 저가 가격 | DECIMAL(18,4) | N | N |  | 0 | low_price |
| `close_prc` | 종가 가격 | DECIMAL(18,4) | N | N |  | 0 | close_price |
| `trd_qty` | 거래 수량 | BIGINT | N | N |  | 0 | volume (업무 단위 미확정: B 인계 참고) |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) B |
| `src_kind_cd` | 원천 종류 코드 | VARCHAR(50) | N | N | SRC_KIND | 0 | source_kind |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | source_row |
| `bronze_row_no` | 브론즈 행 번호 | INT | Y | N |  | 55 | bronze_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | source_version |
| `fetch_dttm` | API 조회 일시 | DATETIME | Y | N |  | 1,689 | fetched_at |
| `api_raw_file_path` | API 원응답 파일 경로 | VARCHAR(500) | Y | N |  | 1,689 | api_raw_file |
| `api_rcrd_path` | API 레코드 경로 | VARCHAR(500) | Y | N |  | 1,689 | api_record_path |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적) |

### s_invstr_trd_daily — 투자자별 일별 매매

- DB/계층: `tz_silver` / SILVER
- 행 단위: 종목·거래일·투자자유형당 1행
- PK: `stock_cd+trd_dt+invstr_type_cd`
- FK: stock_cd→s_stock.stock_cd
- 논리 FK: 없음
- 원천: B silver/investor_trading_daily.csv
- 실제 CSV: [s_invstr_trd_daily.csv](../data/03_C_integration_20261014/04_output/silver/s_invstr_trd_daily.csv) / 191,829행 × 20열
- `trd_dt` 범위: 2022-12-01 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 | investor_trading_daily.symbol |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 | trade_date |
| `invstr_type_cd` | 투자자 유형 코드 | VARCHAR(50) | N | Y | INVSTR_TYPE | 0 | investor_type (camelCase→표준 코드) |
| `upper_invstr_type_cd` | 상위 투자자 유형 코드 | VARCHAR(50) | Y | N | INVSTR_TYPE | 69,756 | parent_type |
| `aggr_lvl_cd` | 집계 수준 코드 | VARCHAR(50) | N | N | AGGR_LVL | 0 | aggregation_level |
| `buy_qty` | 매수 수량 | BIGINT | N | N |  | 0 | buy_volume |
| `sell_qty` | 매도 수량 | BIGINT | N | N |  | 0 | sell_volume |
| `net_buy_qty` | 순매수 수량 | BIGINT | N | N |  | 0 | net_buy_volume |
| `src_col_nm` | 원천 컬럼명 | VARCHAR(200) | N | N |  | 0 | source_column |
| `src_json_path` | 원천 JSON 경로 | VARCHAR(500) | N | N |  | 0 | json_path |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) B |
| `src_kind_cd` | 원천 종류 코드 | VARCHAR(50) | N | N | SRC_KIND | 0 | source_kind |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | source_row |
| `bronze_row_no` | 브론즈 행 번호 | INT | Y | N |  | 2,662 | bronze_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | source_version |
| `fetch_dttm` | API 조회 일시 | DATETIME | Y | N |  | 189,167 | fetched_at |
| `api_raw_file_path` | API 원응답 파일 경로 | VARCHAR(500) | Y | N |  | 189,167 | api_raw_file |
| `api_rcrd_path` | API 레코드 경로 | VARCHAR(500) | Y | N |  | 189,167 | api_record_path |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적) |

### s_frgn_hold_daily — 외국인 보유 일별

- DB/계층: `tz_silver` / SILVER
- 행 단위: 종목·거래일당 1행
- PK: `stock_cd+trd_dt`
- FK: stock_cd→s_stock.stock_cd
- 논리 FK: 없음
- 원천: B silver/foreign_holding_daily.csv
- 실제 CSV: [s_frgn_hold_daily.csv](../data/03_C_integration_20261014/04_output/silver/s_frgn_hold_daily.csv) / 17,439행 × 17열
- `trd_dt` 범위: 2022-12-01 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 | foreign_holding_daily.symbol |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 | trade_date |
| `hold_qty` | 보유 수량 | BIGINT | N | N |  | 0 | holding_quantity |
| `limit_qty` | 한도 수량 | BIGINT | N | N |  | 0 | limit_quantity |
| `hold_rt` | 보유 율 | DECIMAL(12,8) | N | N |  | 0 | holding_rate (소수 비율) |
| `src_col_nm` | 원천 컬럼명 | VARCHAR(200) | N | N |  | 0 | source_column |
| `src_json_path` | 원천 JSON 경로 | VARCHAR(500) | N | N |  | 0 | json_path |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) B |
| `src_kind_cd` | 원천 종류 코드 | VARCHAR(50) | N | N | SRC_KIND | 0 | source_kind |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | source_row |
| `bronze_row_no` | 브론즈 행 번호 | INT | Y | N |  | 242 | bronze_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | source_version |
| `fetch_dttm` | API 조회 일시 | DATETIME | Y | N |  | 17,197 | fetched_at |
| `api_raw_file_path` | API 원응답 파일 경로 | VARCHAR(500) | Y | N |  | 17,197 | api_raw_file |
| `api_rcrd_path` | API 레코드 경로 | VARCHAR(500) | Y | N |  | 17,197 | api_record_path |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적) |

### s_cfd_bal_daily — CFD 잔고 일별

- DB/계층: `tz_silver` / SILVER
- 행 단위: 종목·거래일당 1행
- PK: `stock_cd+trd_dt`
- FK: stock_cd→s_stock.stock_cd
- 논리 FK: 없음
- 원천: B silver/cfd_daily.csv
- 실제 CSV: [s_cfd_bal_daily.csv](../data/03_C_integration_20261014/04_output/silver/s_cfd_bal_daily.csv) / 13,719행 × 18열
- `trd_dt` 범위: 2023-08-31 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 | cfd_daily.symbol |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 | trade_date |
| `buy_bal_qty` | 매수 잔고 수량 | BIGINT | N | N |  | 0 | buy_balance_quantity |
| `buy_bal_rt` | 매수 잔고 율 | DECIMAL(12,8) | N | N |  | 0 | buy_balance_rate |
| `sell_bal_qty` | 매도 잔고 수량 | BIGINT | N | N |  | 0 | sell_balance_quantity |
| `sell_bal_rt` | 매도 잔고 율 | DECIMAL(12,8) | N | N |  | 0 | sell_balance_rate |
| `src_col_nm` | 원천 컬럼명 | VARCHAR(200) | N | N |  | 0 | source_column |
| `src_json_path` | 원천 JSON 경로 | VARCHAR(500) | N | N |  | 0 | json_path |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 | (C 부여) B |
| `src_kind_cd` | 원천 종류 코드 | VARCHAR(50) | N | N | SRC_KIND | 0 | source_kind |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | N | N |  | 0 | source_file |
| `src_row_no` | 원천 행 번호 | INT | N | N |  | 0 | source_row |
| `bronze_row_no` | 브론즈 행 번호 | INT | Y | N |  | 191 | bronze_row |
| `src_ver` | 원천 버전 | VARCHAR(80) | N | N |  | 0 | source_version |
| `fetch_dttm` | API 조회 일시 | DATETIME | Y | N |  | 13,528 | fetched_at |
| `api_raw_file_path` | API 원응답 파일 경로 | VARCHAR(500) | Y | N |  | 13,528 | api_raw_file |
| `api_rcrd_path` | API 레코드 경로 | VARCHAR(500) | Y | N |  | 13,528 | api_record_path |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 | pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적) |

### s_corp_stock_map — 기업-종목 매핑

- DB/계층: `tz_silver` / SILVER
- 행 단위: 기업·종목 대응 1건당 1행(미연결 포함)
- PK: `map_id`
- FK: corp_cd→s_corp.corp_cd; stock_cd→s_stock.stock_cd
- 논리 FK: 없음
- 원천: C 생성
- 실제 CSV: [s_corp_stock_map.csv](../data/03_C_integration_20261014/04_output/silver/s_corp_stock_map.csv) / 20행 × 11열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `map_id` | 매핑 식별자 | VARCHAR(64) | N | Y |  | 0 | (C 생성) corp_cd/stock_cd |
| `corp_cd` | 기업 코드 | CHAR(8) | Y | N |  | 0 | s_corp.corp_cd |
| `stock_cd` | 종목 코드 | CHAR(6) | Y | N |  | 0 | s_stock.stock_cd / s_corp.stock_cd |
| `map_stts_cd` | 매핑 상태 코드 | VARCHAR(50) | N | N | MAP_STTS | 0 |  |
| `map_mthd_cd` | 매핑 방법 코드 | VARCHAR(50) | N | N | MAP_MTHD | 0 |  |
| `cand_cnt` | 후보 건수 | INT | N | N |  | 0 |  |
| `corp_nm` | 기업명 | VARCHAR(200) | Y | N |  | 0 | s_corp.corp_nm (검증 근거) |
| `stock_nm` | 종목명 | VARCHAR(200) | Y | N |  | 0 | s_stock.stock_nm (검증 근거) |
| `nm_match_yn` | 명칭 일치 여부 | CHAR(1) | N | N | YN | 0 |  |
| `map_rsn_txt` | 매핑 사유 내용 | VARCHAR(2000) | Y | N |  | 0 |  |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 |  |

### s_conn_stts — 가격·수급 연결 상태

- DB/계층: `tz_silver` / SILVER
- 행 단위: 종목·거래일 키 합집합당 1행
- PK: `stock_cd+trd_dt`
- FK: stock_cd→s_stock.stock_cd
- 논리 FK: 없음
- 원천: C 생성 (가격 ∪ 수급 키, 내부조인 아님)
- 실제 CSV: [s_conn_stts.csv](../data/03_C_integration_20261014/04_output/silver/s_conn_stts.csv) / 17,440행 × 13열
- `trd_dt` 범위: 2022-12-01 ~ 2026-06-30

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 |  |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 |  |
| `corp_cd` | 기업 코드 | CHAR(8) | Y | N |  | 0 |  |
| `map_stts_cd` | 매핑 상태 코드 | VARCHAR(50) | N | N | MAP_STTS | 0 |  |
| `prc_exist_yn` | 가격 존재 여부 | CHAR(1) | N | N | YN | 0 | B price_investor_availability.has_price 대응 |
| `invstr_exist_yn` | 수급 존재 여부 | CHAR(1) | N | N | YN | 0 | B price_investor_availability.has_investor_data 대응 |
| `frgn_hold_exist_yn` | 외국인 보유 존재 여부 | CHAR(1) | N | N | YN | 0 |  |
| `cfd_exist_yn` | CFD 잔고 존재 여부 | CHAR(1) | N | N | YN | 0 |  |
| `fin_avail_yn` | 재무 가용 여부(시점 기준) | CHAR(1) | N | N | YN | 0 |  |
| `conn_stts_cd` | 연결 상태 코드 | VARCHAR(50) | N | N | CONN_STTS | 0 |  |
| `miss_rsn_cd` | 부재 사유 코드 | VARCHAR(50) | Y | N | MISS_RSN | 17,439 |  |
| `miss_rsn_txt` | 부재 사유 내용 | VARCHAR(2000) | Y | N |  | 17,439 |  |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 |  |

### s_dq_issue — 데이터 품질 이슈

- DB/계층: `tz_silver` / SILVER
- 행 단위: 이슈 1건당 1행
- PK: `issue_id`
- FK: 없음
- 논리 FK: 없음
- 원천: A review_issues + B data_quality_issues/bronze_unresolved/pending + C 통합 검증
- 실제 CSV: [s_dq_issue.csv](../data/03_C_integration_20261014/04_output/silver/s_dq_issue.csv) / 1,967행 × 13열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `issue_id` | 이슈 식별자 | VARCHAR(64) | N | Y |  | 0 |  |
| `detect_stage_cd` | 탐지 단계 코드 | VARCHAR(50) | N | N | DETECT_STAGE | 0 |  |
| `src_team_cd` | 원천 팀 코드 | VARCHAR(50) | N | N | TEAM | 0 |  |
| `tbl_nm` | 테이블명 | VARCHAR(200) | N | N |  | 0 |  |
| `col_nm` | 컬럼명 | VARCHAR(200) | Y | N |  | 142 |  |
| `rcrd_key_txt` | 레코드 키 내용 | VARCHAR(2000) | Y | N |  | 0 |  |
| `src_file_path` | 원천 파일 경로 | VARCHAR(500) | Y | N |  | 49 |  |
| `src_row_no` | 원천 행 번호 | INT | Y | N |  | 1,904 |  |
| `issue_type_cd` | 이슈 유형 코드 | VARCHAR(50) | N | N | ISSUE_TYPE | 0 |  |
| `sev_cd` | 심각도 코드 | VARCHAR(50) | N | N | SEV | 0 |  |
| `issue_rsn_txt` | 이슈 사유 내용 | VARCHAR(2000) | N | N |  | 0 |  |
| `resolve_stts_cd` | 조치 상태 코드 | VARCHAR(50) | N | N | RESOLVE_STTS | 0 |  |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 |  |

### g_ai_stock_daily — AI 학습용 종목 일별 데이터셋

- DB/계층: `tz_gold` / GOLD
- 행 단위: 종목·거래일당 1행(가격 기준)
- PK: `stock_cd+trd_dt`
- FK: stock_cd→s_stock.stock_cd; fin_rpt_id→s_fin_rpt.fin_rpt_id
- 논리 FK: 없음
- 원천: s_stock_daily_prc ⟕ s_invstr_trd_daily(TOP_LEVEL) ⟕ s_frgn_hold_daily ⟕ s_cfd_bal_daily ⟕ s_idx_daily_prc ⟕ 시점 기준 s_fin_rpt/s_fin_mtrc
- 실제 CSV: [g_ai_stock_daily.csv](../data/03_C_integration_20261014/04_output/gold/g_ai_stock_daily.csv) / 17,440행 × 34열
- `trd_dt` 범위: 2022-12-01 ~ 2026-06-30
- `dscl_dt` 범위: 2023-03-07 ~ 2026-03-23

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `stock_cd` | 종목 코드 | CHAR(6) | N | Y |  | 0 |  |
| `trd_dt` | 거래 일자 | DATE | N | Y |  | 0 |  |
| `corp_cd` | 기업 코드 | CHAR(8) | Y | N |  | 0 |  |
| `mkt_cd` | 시장 코드 | VARCHAR(50) | N | N | MKT | 0 |  |
| `open_prc` | 시가 가격 | DECIMAL(18,4) | N | N |  | 0 |  |
| `high_prc` | 고가 가격 | DECIMAL(18,4) | N | N |  | 0 |  |
| `low_prc` | 저가 가격 | DECIMAL(18,4) | N | N |  | 0 |  |
| `close_prc` | 종가 가격 | DECIMAL(18,4) | N | N |  | 0 |  |
| `trd_qty` | 거래 수량 | BIGINT | N | N |  | 0 |  |
| `close_rtn_rt` | 종가 수익률(전 관측일 대비) | DECIMAL(12,8) | Y | N |  | 20 |  |
| `idx_close_prc` | 지수 종가 가격 | DECIMAL(18,4) | Y | N |  | 0 |  |
| `idx_rtn_rt` | 지수 수익률(전 관측일 대비) | DECIMAL(12,8) | Y | N |  | 20 |  |
| `indv_net_buy_qty` | 개인 순매수 수량 | BIGINT | Y | N |  | 1 |  |
| `frgn_net_buy_qty` | 외국인 순매수 수량 | BIGINT | Y | N |  | 1 |  |
| `inst_net_buy_qty` | 기관 순매수 수량 | BIGINT | Y | N |  | 1 |  |
| `other_corp_net_buy_qty` | 기타법인 순매수 수량 | BIGINT | Y | N |  | 1 |  |
| `frgn_hold_rt` | 외국인 보유 율 | DECIMAL(12,8) | Y | N |  | 1 |  |
| `cfd_buy_bal_rt` | CFD 매수 잔고 율 | DECIMAL(12,8) | Y | N |  | 3,721 |  |
| `invstr_exist_yn` | 수급 존재 여부 | CHAR(1) | N | N | YN | 0 |  |
| `fin_avail_yn` | 재무 가용 여부 | CHAR(1) | N | N | YN | 0 |  |
| `fin_rpt_id` | 재무 보고서 식별자 | VARCHAR(64) | Y | N |  | 1,607 |  |
| `fin_bsns_yr` | 재무 사업 연도 | CHAR(4) | Y | N |  | 1,607 |  |
| `fin_rpt_cd` | 재무 보고서 코드 | VARCHAR(50) | Y | N | RPT | 1,607 |  |
| `fin_fs_div_cd` | 재무 재무제표 구분 코드 | VARCHAR(50) | Y | N | FS_DIV | 1,607 |  |
| `dscl_dt` | 공시 일자 | DATE | Y | N |  | 1,607 |  |
| `dscl_elps_day_cnt` | 공시 경과 일 건수 | INT | Y | N |  | 1,607 |  |
| `rev_ytd_amt` | 매출 누적 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `op_prft_ytd_amt` | 영업 이익 누적 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `net_incm_ytd_amt` | 순이익 누적 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `op_cf_ytd_amt` | 영업 현금흐름 누적 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `tot_asst_amt` | 총 자산 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `tot_liab_amt` | 총 부채 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `tot_eqty_amt` | 총 자본 금액 | DECIMAL(20,0) | Y | N |  | 1,607 |  |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 |  |

### g_fin_rpt_mkt_smry — 재무 보고기간 시장 요약

- DB/계층: `tz_gold` / GOLD
- 행 단위: 재무 보고서당 1행
- PK: `fin_rpt_id`
- FK: fin_rpt_id→s_fin_rpt.fin_rpt_id
- 논리 FK: 없음
- 원천: s_fin_rpt + s_fin_mtrc + s_stock_daily_prc + s_invstr_trd_daily (A 인계 '방법 B')
- 실제 CSV: [g_fin_rpt_mkt_smry.csv](../data/03_C_integration_20261014/04_output/gold/g_fin_rpt_mkt_smry.csv) / 320행 × 21열
- `prd_start_dt` 범위: 2022-01-01 ~ 2025-01-01
- `prd_end_dt` 범위: 2022-03-31 ~ 2025-12-31

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `fin_rpt_id` | 재무 보고서 식별자 | VARCHAR(64) | N | Y |  | 0 |  |
| `corp_cd` | 기업 코드 | CHAR(8) | N | N |  | 0 |  |
| `stock_cd` | 종목 코드 | CHAR(6) | N | N |  | 0 |  |
| `bsns_yr` | 사업 연도 | CHAR(4) | N | N |  | 0 |  |
| `rpt_cd` | 보고서 코드 | VARCHAR(50) | N | N | RPT | 0 |  |
| `fs_div_cd` | 재무제표 구분 코드 | VARCHAR(50) | N | N | FS_DIV | 0 |  |
| `prd_start_dt` | 기간 시작 일자 | DATE | N | N |  | 0 |  |
| `prd_end_dt` | 기간 종료 일자 | DATE | N | N |  | 0 |  |
| `same_prd_cmpr_elig_yn` | 동일 기간 비교 적격 여부 | CHAR(1) | N | N | YN | 0 |  |
| `trd_day_cnt` | 거래 일 건수 | INT | N | N |  | 0 |  |
| `full_cvrg_yn` | 기간 전체 커버리지 여부 | CHAR(1) | N | N | YN | 0 |  |
| `first_close_prc` | 첫 종가 가격 | DECIMAL(18,4) | Y | N |  | 60 |  |
| `last_close_prc` | 마지막 종가 가격 | DECIMAL(18,4) | Y | N |  | 60 |  |
| `prd_rtn_rt` | 기간 수익률 | DECIMAL(12,8) | Y | N |  | 80 |  |
| `frgn_net_buy_qty` | 외국인 순매수 수량(기간 합) | BIGINT | Y | N |  | 80 |  |
| `inst_net_buy_qty` | 기관 순매수 수량(기간 합) | BIGINT | Y | N |  | 80 |  |
| `indv_net_buy_qty` | 개인 순매수 수량(기간 합) | BIGINT | Y | N |  | 80 |  |
| `rev_ytd_amt` | 매출 누적 금액 | DECIMAL(20,0) | Y | N |  | 0 |  |
| `op_prft_ytd_amt` | 영업 이익 누적 금액 | DECIMAL(20,0) | Y | N |  | 0 |  |
| `op_cf_ytd_amt` | 영업 현금흐름 누적 금액 | DECIMAL(20,0) | Y | N |  | 0 |  |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 |  |

### m_exec_log — 실행 기록

- DB/계층: `tz_meta` / META
- 행 단위: 실행·절차·테이블당 1행
- PK: `run_id+step_nm+tbl_nm`
- FK: 없음
- 논리 FK: 없음
- 원천: C run_pipeline.py / load_mysql.py
- 실제 CSV: [m_exec_log.csv](../data/03_C_integration_20261014/04_output/meta/m_exec_log.csv) / 42행 × 10열

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `run_id` | 실행 식별자 | VARCHAR(64) | N | Y |  | 0 |  |
| `step_nm` | 절차명 | VARCHAR(200) | N | Y |  | 0 |  |
| `tbl_nm` | 테이블명 | VARCHAR(200) | N | Y |  | 0 |  |
| `layer_cd` | 계층 코드 | VARCHAR(50) | N | N | LAYER | 0 |  |
| `input_ver` | 입력 버전 | VARCHAR(80) | N | N |  | 0 |  |
| `rcrd_cnt` | 레코드 건수 | INT | N | N |  | 0 |  |
| `start_dttm` | 시작 일시 | DATETIME | N | N |  | 0 |  |
| `end_dttm` | 종료 일시 | DATETIME | N | N |  | 0 |  |
| `run_stts_cd` | 실행 상태 코드 | VARCHAR(50) | N | N | RUN_STTS | 0 |  |
| `pipln_ver` | 파이프라인 버전 | VARCHAR(80) | N | N |  | 0 |  |

### m_std_word — 표준 단어

- DB/계층: `tz_meta` / META
- 행 단위: 단어당 1행
- PK: `word_nm`
- FK: 없음
- 논리 FK: 없음
- 원천:
- 실제 CSV: 미포함. DDL·표준 정의만 제공.

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `word_nm` | 단어 물리명 | VARCHAR(200) | N | Y |  | 미확인 |  |
| `word_kor_nm` | 단어 한글명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `word_eng_nm` | 단어 영문명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `word_cls_cd` | 단어 분류 코드 | VARCHAR(50) | N | N |  | 미확인 |  |

### m_std_dmn — 표준 도메인

- DB/계층: `tz_meta` / META
- 행 단위: 도메인당 1행
- PK: `dmn_nm`
- FK: 없음
- 논리 FK: 없음
- 원천:
- 실제 CSV: 미포함. DDL·표준 정의만 제공.

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `dmn_nm` | 도메인명 | VARCHAR(200) | N | Y |  | 미확인 |  |
| `cls_word_nm` | 분류어명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `data_type_nm` | 데이터 유형명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `data_len_txt` | 데이터 길이 내용 | VARCHAR(2000) | N | N |  | 미확인 |  |
| `allow_ptrn_txt` | 허용 패턴 내용 | VARCHAR(2000) | N | N |  | 미확인 |  |
| `dmn_desc_txt` | 도메인 설명 내용 | VARCHAR(2000) | N | N |  | 미확인 |  |

### m_std_term — 표준 용어(컬럼)

- DB/계층: `tz_meta` / META
- 행 단위: 테이블·컬럼당 1행
- PK: `tbl_nm+col_nm`
- FK: 없음
- 논리 FK: 없음
- 원천:
- 실제 CSV: 미포함. DDL·표준 정의만 제공.

| 컬럼 | 의미 | 타입 | NULL 허용 | PK | 코드그룹 | 실제 빈값 | 원천/대응 |
|---|---|---|---|---|---|---:|---|
| `tbl_nm` | 테이블명 | VARCHAR(200) | N | Y |  | 미확인 |  |
| `col_nm` | 컬럼명 | VARCHAR(200) | N | Y |  | 미확인 |  |
| `term_kor_nm` | 용어 한글명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `dmn_nm` | 도메인명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `data_type_nm` | 데이터 유형명 | VARCHAR(200) | N | N |  | 미확인 |  |
| `null_allow_yn` | 널 허용 여부 | CHAR(1) | N | N |  | 미확인 |  |
| `pk_yn` | 기본키 여부 | CHAR(1) | N | N |  | 미확인 |  |
| `cd_grp_id` | 코드그룹 식별자 | VARCHAR(64) | Y | N |  | 미확인 |  |
| `layer_cd` | 계층 코드 | VARCHAR(50) | N | N |  | 미확인 |  |
| `asis_src_txt` | 현행 원천 내용 | VARCHAR(2000) | Y | N |  | 미확인 |  |

## 3. CSV 전용 메타

`04_output/meta/input_manifest.csv`는 입력 18개의 경로·해시·크기 명세이며 자체 DB 테이블 정의는 없다. `04_output/meta/m_exec_log.csv`는 실제 42행 × 10열이고, 원래 실행 로그를 보존한다. 실행 로그 행수는 테이블 데이터의 최신 버전 건수와 구분한다.
