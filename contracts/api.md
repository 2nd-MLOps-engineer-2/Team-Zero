# G02 — B 조회 API 1.0.0

작성 B / 구현·로컬 검증 완료 / A·C 수신 합의 대기. 기존 C 통합본 1.0.0을 제공한다. C 신규 분석 계약의 대체물이 아니다. 정확한 전체 컬럼·필수값은 실행 서버 `/openapi.json`과 `fixtures/api/openapi.json`을 따른다.

기본 주소 `http://127.0.0.1:8000`. 인증 없는 로컬 GET 서비스다. 20종목, 거래일 2022-12-01~2026-06-30(872일), 재무 사업연도 2022~2025. 새로운 주가·공시를 실시간 수집하지 않는다.

## 요청

| GET | 조건 | 결과·행 단위 |
|---|---|---|
| `/health` | 없음 | 원본·버전·신규 분석 가용 상태 |
| `/stocks` | market=KOSPI/KOSDAQ, q, limit=1~100(기본100), offset | 종목, 코드순 |
| `/stocks/compare` | as_of(기본 최종일), market | 종목별 기준일 이하 마지막 관측값 |
| `/stocks/{code}` | 6자리 코드 | 종목·기업 매핑 |
| `/stocks/{code}/daily` | start,end,limit=1~5000(기본1000),offset | 종목×거래일, 날짜순 |
| `/stocks/{code}/financials` | year,report_code,fs_div,as_of | 보고서 헤더 + metrics + 기존 기간 요약 |
| `/stocks/{code}/quality` | start,end,limit=1~500(기본100),offset | availability·직접 issue·전체 statement 이슈 분리 |
| `/analysis/{code}/evidence` | as_of | Gold 관측값·연결 보고서·94개 기간별 지표·가격 원천 |
| `/exports/stocks/{code}/daily.csv` | start,end | 기존 Gold 전체 컬럼, 종목×거래일 |
| `/exports/stocks/{code}/financials.csv` | financials와 동일 | 보고서×지표×기간 유형, 보고서당94행 |
| `/exports/analysis/{table}.csv` | g_fin_rpt_analysis 또는 g_stock_daily_analysis | C 신규 전달 전409 |

`report_code`: 11011 사업보고서, 11012 반기, 11013 1분기, 11014 3분기. `fs_div`: CFS 연결, OFS 별도. 목록 total/limit/offset은 JSON 정수다. daily/quality 시작·종료는 포함 경계이며 범위 밖 조회는 빈 결과가 될 수 있다. compare/evidence/financials.as_of는 보유 거래일 범위 안에서만 허용한다. 휴일 as_of는 직전 관측값을 반환하고 요청 기준일과 실제 거래일을 함께 확인한다.

financials는 기본적으로 PIT 부적격 보고서도 품질 플래그와 함께 보여 준다. as_of를 지정하면 `pit_join_elig_yn=Y`이고 공시일 < as_of인 보고서만 선택한다. 근거 없는 공시일을 채우지 않는다. 일별 보고서 선택은 C의 기존 Gold를 그대로 사용한다.

quality의 날짜 필터는 availability에 적용한다. 직접 이슈는 종목·보고서 범위이고 발견 시각 자료가 없어 날짜별 신규 결함으로 해석할 수 없다. 전역 statement 이슈는 종목 직접 이슈 건수에 합치지 않는다. issue_id 순으로 정렬 후 페이지를 나눈다.

## 타입·단위·결측

성공 `{data, meta}`, 오류 `{error:{code,message,details?},meta}`. 헤더에 X-API-Version, X-Data-Version, X-Analysis-Status를 제공한다. `meta`에 원본 종류, 데이터 버전·최종일·계산 버전·단위·분석 상태가 있다. HTTP 캐시는 no-store다.

업무 행의 금액·가격·수량·비율·연도·일수는 **문자열**이다. MySQL DECIMAL과 큰 정수의 유효숫자를 보존한다. 금액 KRW, 수급 shares, 비율 decimal_fraction. 비율 0.01은 표시 시1%. 브라우저에서 큰 금액을 무조건 Number로 변환하지 말고 정밀도 라이브러리 또는 표시용 문자열을 사용한다. 코드의 앞자리0도 보존한다. 날짜 YYYY-MM-DD, 시각 ISO 문자열. NULL은 JSON null, 실제0은 문자열 "0" 또는 타입별 소수 자릿수의0이다. CSV는 BOM UTF-8, NULL은 빈칸, 모든 페이지가 아닌 해당 조건 전체 행을 내보낸다.

일별 주요 필드: close_prc, close_rtn_rt, idx_rtn_rt, rev_ytd_amt(당기 누적매출), op_prft_ytd_amt(누적영업이익), net_incm_ytd_amt(누적순이익), op_cf_ytd_amt(누적영업현금), tot_asst_amt/tot_liab_amt/tot_eqty_amt(기말자산/부채/자본), frgn_net_buy_qty/inst_net_buy_qty(일별순매수 주), fin_rpt_id/dscl_dt(당시 선택 보고서/공시일). 누적 재무를 일별로 다시 합산하지 않는다. 기관 합계에 기관 세부7종을 더하지 않는다.

재무 metrics는 mtrc_cd + prd_type_cd로 식별한다. 지표 정의는 `s_fin_mtrc_def`, 원본 계정 상세는 `s_fin_item`에 있다. YTD·PRIOR_YTD·Q3M·ASOF 및 CFS/OFS를 섞어 비교하지 않는다. 기존 period_market_summary는 사후 보고기간 설명 자료다. `full_cvrg_yn`은 전역 가격 범위로 개별종목 수급 완전성을 보증하지 않는다.

## 상태·예외·예제

현재 `analysis_status=PENDING_C_DELIVERY`, 각 `analysis=null`. 기존 Gold 값은 조회 가능하다. 동반 개선·괴리 분류·전년동기 증감 등 C 신규 계산은 만들어 제공하지 않는다.

404 STOCK_NOT_FOUND(보유 외 코드), 422 VALIDATION_ERROR(형식·enum·상한), INVALID_DATE_RANGE(역순), AS_OF_OUT_OF_RANGE(기준일), 409 ANALYSIS_NOT_AVAILABLE(C 미전달), 읽기 오류503 DATA_SOURCE_UNAVAILABLE. 시작 단계 원본 무결성·DB 접속 오류는 서버 시작을 중단한다.

실제 저장소 자료 기반 샘플은 `fixtures/api/`에 request/response wrapper로 저장했다. `missing_investor.json`: 247540/2026-04-16 가격은 있고 수급은 null, invstr_exist_yn=N. `invalid_date.json`: 존재하지 않는 날짜422. `unknown_stock.json`: 미제공 종목404. 합성 C 어댑터 검사 자료는 테스트 안에만 있고 실제 분석 성과가 아니다.

A는 `/stocks`, `/stocks/compare?as_of=2026-06-30`, `/stocks/005930/financials?year=2025&report_code=11011`, `/analysis/005930/evidence?as_of=2026-06-30`부터 연결한다. API/화면/CSV 수치는 G05에서 별도 대조한다.
