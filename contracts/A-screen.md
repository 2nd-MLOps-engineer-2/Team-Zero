# A 화면·응답 계약 제안 v1

## B API 1.1.0 실제 연결 추가 계약

2026-10-15 수신 ZIP으로 검증. `a-proposal-1`은 내부 화면/샘플 표현이며 B wire version은 `1.1.0`이다. B 메타를 보존하며 `data_final_date → data_end`, `calculation_version → calc_version`만 내부 이름으로 매핑한다. 중첩 analysis를 펼치되 원본도 유지한다. 지원하지 않는 API 버전은 오류 처리한다.

- 일별 query: start/end, 재무: year(전체는 생략)/report_code/fs_div/as_of, 비교: market/as_of, 근거: as_of. 품질은 start/end. 페이지가 있는 목록은 끝까지 수신한다.
- 요청일과 실제 관측일을 구분한다. B의 직전 관측 선택을 허용하며 미래 관측은 거부한다. 재무는 PIT 필터 적용과 공시일 < 요청일을 검증한다.
- metrics에서 REVENUE/OPERATING_PROFIT/NET_INCOME/OPERATING_CASH_FLOW의 YTD 원값을 선택한다. 누락은 NULL. Q3M/ASOF를 YTD로 바꾸거나 연간화하지 않는다.
- API/데이터/입력/계산/C 산출물 버전을 응답 간 검사한다. 서버 CSV는 전후 health와 X-* 헤더도 비교한다. 스냅샷 변경 시 재조회 오류를 표시한다.
- 품질은 날짜별 availability, 기업·보고서 issues, global_statement_issues의 세 범위를 구분한다. C 미연결은 PENDING_C_DELIVERY, 원본 출처 메타는 원본 확보 증거로 사용하지 않는다.
- 화면 표시값 CSV와 B 서버 원값 CSV를 구분한다. C 전체 CSV는 필터 미적용이며 NULL은 B 계약대로 빈칸이다. 가격 기준일은 B 제공값을 그대로 쓴다.


작성: A 이어진 / 2026-10-15 / **제안·합성 구현 검증, B/C 합의 전**. G02·G03 / M08·M09·M12·M13.

## G03 수신 검토 후 추가 사항

C 고정 전달 SHA fb1f802c88e2d5b275c737200aa392deac0e628b(c-gold-0.1.0)의 실제 샘플·시안을 확인했다. 아래 기존 v1 내용보다 이 추가 사항이 우선한다.

- rev_yoy_rt → revenue_growth_rt, event_excess_rt → excess_return_rt, event_base_dt → observation_start, trd_dt → as_of/observation_end(비교/근거)의 표현 매핑 지원. 원문 C 필드·소수 문자열을 보존한다.
- 비율은 유한 숫자 또는 소수 문자열 허용. C CSV 샘플의 빈 문자열은 null로 정규화. 0과 빈값 구분. UI에서 C 지표를 재계산하지 않는다.
- C co_move_cd·*_stts_cd 한글 문구, joint_improve_yn Y/N/판단 불가 표시. 복합 조건은 2축 분류와 별도로 설명.
- frgn_flow_20d_rt, inst_flow_20d_rt를 %로 표시하는 별도 차트/표 추가. 일별 수량(주) 및 보유율과 혼동하지 않음. *_flow_20d_stts_cd 유지.
- 사분면 x=매출 YoY %, y=공시 후 초과성과 %p, 0축 표시, NULL 점 제외 후 표 유지. 마우스·키보드로 상세 이동. 공시일·기준일·event_base_dt tooltip 포함.
- 가격 차트는 조회 첫 유효 관측=100, 동일 기준일을 제공하는 B/C 응답 필요. 합성 예제는 미리 생성한 구간별 기준값을 선택. C Gold에 정규화 필드는 없어 B 응답 계약에서 추가해야 함. 없는 기준값을 A가 실제 값처럼 만들지 않음.
- 재무 x축=prd_end_dt, YTD/원(표)·조 원(차트). 분기 단독/연간이라는 잘못된 고정 라벨 제거.

실제 C 재생성 CSV로 만든 테스트 응답에서 삼성전자 2026-06-30 매출 333605938000000원, rev_yoy_rt 0.10880093, event_excess_rt 0.32769823, joint_improve_yn=N을 화면·CSV와 대조했다. B API 대신 브라우저 응답 주입이며 실제 서버/DB 연동 검증은 아니다. 상세 S3-C-to-A.md 참고.

실행 구현: apps/web/src/api.js, fixtures/sample.json. B의 공식 API·C 분석/시각화 계약을 대체하지 않는다. 기존 Gold 컬럼명(금액·수급·보고서 키 등)은 재사용하고 신규 분석 필드는 아래 제안으로 구분한다.

## 화면 동선·조회

시장/기업/시작일/기준일 → 기준일 종목 비교 → 기업 상세 재무·가격/시장·수급/보유율 → 계산 근거·레이어 출처 → CSV.

시장 필터는 목록/비교, 시작일은 일별 추이, 기준일은 일별 상한·비교/근거·공시 시점, 사업연도/보고서/CFS·OFS는 재무에 적용한다. 비교와 근거는 기준일의 최근 공시 기준이며 재무 필터로 임의 재계산하지 않는다. 연도 all은 비교 가능한 복수 연도의 보고서 배열을 요청한다.

| GET 경로 | data 행 단위·키 | 쿼리 |
|---|---|---|
| /stocks | stock_cd당 1행 | 없음 |
| /stocks/compare | stock_cd + as_of | as_of, market |
| /stocks/{stock_cd}/daily | stock_cd + trd_dt | start, as_of |
| /stocks/{stock_cd}/financials | fin_rpt_id | as_of, year, report, basis |
| /analysis/{stock_cd}/evidence | stock_cd + as_of | as_of |

현재 어댑터는 공통 쿼리의 추가 키도 endpoint에 보낸다. B가 엄격한 쿼리 스키마를 사용하면 필요한 키만 보내도록 A가 맞춘다. 인증·CORS·pagination·서버 export는 B와 합의 전이다. 현재 CSV는 조회 응답을 클라이언트에서 그대로 직렬화한다.

## 응답 형태와 예외

모든 성공 응답: `{ "meta": {...}, "data": [...] }`. 빈 결과도 성공 200 + 빈 data. 비정상 HTTP/JSON/필수 필드/정밀도/날짜/기업·기간/버전 불일치는 오류 화면을 표시한다. 15초 timeout, 이전 요청 취소 및 마지막 조회만 반영. 실제 API 모드에서 샘플로 fallback하지 않는다.

meta: schema_version=`a-proposal-1`, synthetic(boolean), data_end(ISO 날짜), input_version, calc_version, scope, units, price_base_date. schema/synthetic/data_end/input/calc 버전은 endpoint 간 동일해야 한다. 관측 수는 각 data 행수로 표시. price_base_date는 C가 산출한 기준값 100의 날짜이며 A가 조회 구간에 맞춰 재계산하지 않는다.

- stock_cd: 문자열 6자리. stock_nm, mkt_cd는 s_stock 식별자에서 참조.
- *_amt, *_qty, numerator, denominator: 정수 문자열 또는 null. Number 변환으로 금액을 표시하지 않음. 금액 원, 수량 주. 차트 좌표에서만 스케일 변환하며 표/CSV는 원문 문자열 유지.
- *_rt: 소수 비율 숫자 또는 null. 화면 % 또는 %p만 100배 표시. excess_return_rt는 종목성과−시장성과, %p.
- compare: revenue_growth_rt, excess_return_rt, classification, dscl_dt, dscl_elps_day_cnt, observation_start/end, reason.
- daily: trd_dt, stock_base100, market_base100, frgn_net_buy_qty, inst_net_buy_qty, frgn_hold_rt, status, reason. 기관 TOP_LEVEL 합계만 사용.
- financials: fin_rpt_id, bsns_yr, rpt_cd, fs_div_cd, period_type, prd_start/end_dt, dscl_dt, period_status, rev_ytd_amt, op_prft_ytd_amt, net_incm_ytd_amt, op_cf_ytd_amt, reason.
- evidence: 분류/성장률/시장대비성과, fin_rpt_id, dscl_dt, observation_start/end, numerator/denominator(매출 증감액/전년동기 매출), formula, threshold, calc_status, review, lineage 배열.
- lineage: layer, status, file, row, key, version, reason. 없는 출처를 창작하지 않고 null로 전송. Bronze 미확보, Silver 검토/격리, Gold 계산 불가를 분리.

공시일은 기준일보다 엄격히 이전이어야 한다. NULL은 `미제공 (NULL)`, 0은 `0 원/주/%`. 부재 관측점은 선을 끊고 0/보간 금지. 원문 ZIP 수집 기록과 실제 파일 확보를 구분한다. 근거 없는 기간/출처/원본 증빙을 만들지 않는다.

## 샘플·시각화

정상 예제 전체: apps/web/src/fixtures/sample.json. scripts/generate-fixture.py는 고정 s_stock에서 식별자만 읽고 UI 수치를 합성한다. 20개 종목, 비교/근거는 2026-06-30, 일별은 6월 6개 관측점, 보고서는 2024·2025 연간 CFS YTD. 실제 거래일 전량이나 업무 계산 결과가 아니다.

- 000660: 매출 2024년 10,000,000,000,000원 → 2025년 11,200,000,000,000원, 성장률 .12, 근거 분자 1,200,000,000,000원 / 분모 10,000,000,000,000원. CSV도 동일 원값.
- 005380: 영업이익 문자열 "0". 005490: 영업CF null/기간 미검증, 분류 판단 불가.
- 일별 2026-06-10: 외국인 수량/보유율 null, 미연결 사유. 이 날짜는 합성 사례이며 실제 부재 키로 주장하지 않는다.
- scenario=empty/error는 샘플 모드에서만 선택 가능. error는 의도된 오류, 빈 결과는 모든 분석 배열 비움.

차트: 주가/시장 기준값 100, 재무 연도별 YTD(조 원), 일별 외국인/기관 수량(주), 외국인 보유율(%). 날짜 축은 실제 날짜 간격, 값 축은 명시적으로 눈금 표시. 원값은 펼침 표와 SVG tooltip으로 확인. 재무는 일별 반복합산하지 않음. C의 실제 예제/의미 확인 전 최종 시각화 합의 아님.

## CSV

UTF-8 BOM, 인용 부호 escape, 수식 접두 문자열 방어, null은 NULL. dataset/stock_cd/record_key/field/value/unit/조회 필터/synthetic/data_end/input_version/calc_version의 long 형식. 값은 API/fixture의 원문 정밀도 유지. Excel 자동 숫자 변환을 피하려면 가져오기에서 stock_cd·value를 텍스트 열로 선택한다. CSV 자체는 원문 보존을 검증했으며 모든 Excel 버전의 자동열기 동작은 검증하지 않았다.

## 검증 및 남은 의존성

단위 10개, Chromium 브라우저 9개, 빌드 통과. API 모드는 네트워크 응답 모의 검사이며 B 실제 서버 검증 아님. 출처 상태·정밀도·필터·오류·모바일·CSV 검증은 A 기록 참조. B API 고정 SHA·C G03 가이드/실제 기대값을 받은 뒤 review 브랜치에서 S4/G05를 검증해야 한다.
