-- Connect in MySQL Workbench: 127.0.0.1:3306 (use your local credentials).
SHOW DATABASES LIKE 'tz_%';

SELECT COUNT(*) AS daily_rows
FROM tz_gold_20261015_101647_d567.g_ai_stock_daily;
-- Expected: 17440

SELECT COUNT(*) AS financial_reports
FROM tz_silver_20261015_101647_d567.s_fin_rpt;
-- Expected: 320

SELECT COUNT(*) AS financial_items
FROM tz_silver_20261015_101647_d567.s_fin_item;
-- Expected: 66729

SELECT stock_cd, trd_dt, close_prc, rev_ytd_amt,
       op_prft_ytd_amt, net_incm_ytd_amt, op_cf_ytd_amt,
       frgn_net_buy_qty, inst_net_buy_qty, dscl_dt
FROM tz_gold_20261015_101647_d567.g_ai_stock_daily
WHERE stock_cd = '005930'
ORDER BY trd_dt DESC LIMIT 10;

SELECT fin_avail_yn, COUNT(*) AS rows_by_availability
FROM tz_gold_20261015_101647_d567.g_ai_stock_daily
GROUP BY fin_avail_yn;
-- Expected: Y=15833, N=1607. NULL is retained, not replaced with zero.

SELECT stock_cd,trd_dt,close_prc,invstr_exist_yn,frgn_net_buy_qty
FROM tz_gold_20261015_101647_d567.g_ai_stock_daily
WHERE stock_cd='247540' AND trd_dt='2026-04-16';
-- Price exists; investor flag N and foreign net-buy NULL are intentional.
