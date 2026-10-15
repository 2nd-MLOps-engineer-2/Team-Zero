# S4 API 전달 보완 — B → A (2026-10-15 / API 1.1.0 로컬 검증본)


```powershell
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\pack_c_analysis.py --source .\build\analysis --output .\build\c_api_artifact
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\run.py --backend csv --analysis-dir .\build\c_api_artifact
```

현재 B PC에는 검증한 묶음이 `build/s4_api_20261015/c_api_artifact`에 있다. 해당 PC에서는 위 analysis-dir만 이 경로로 바꾼다. 한 번에 서버 하나를 시작하고 종료는 실행 창 Ctrl+C. C CSV의 빈칸만 JSON null로 바꾸며 계산값·상태코드는 바꾸지 않는다. C 묶음을 생략하면 기존 Gold는 조회 가능하고 analysis=null/PENDING_C_DELIVERY로 명확히 남는다.


환경 예시(비밀값 없음):

```powershell
$env:TZ_CORS_ORIGINS='http://localhost:5173,http://127.0.0.1:5173'
$env:TZ_MYSQL_HOST='127.0.0.1'
$env:TZ_MYSQL_PORT='3306'
$env:TZ_MYSQL_USER='root'
# .env 자동 로드는 없음. C 묶음은 CLI --analysis-dir 또는 TZ_ANALYSIS_DIR 사용.
```

MySQL 기준 기존 Gold를 읽으려면 run.py --backend mysql(PC에서 암호 입력). C 묶음도 함께 연결할 수 있으나 **이번 신규 C 계산2테이블 MySQL 적재/조회 검증은 미실행**이다. 이번 C API 증빙은 CSV/Delta 기준자료 + 검증된 C CSV 연결이다. 기존58테이블의 MySQL 검증과 섞지 않는다. 팀원 PC의 localhost는 B PC가 아니므로 각자 CSV 서버부터 실행한다. 운영 배포·외부 접속·인증 서버는 미구성이다.

A 설정 예: VITE_DATA_MODE=api / VITE_API_BASE_URL=http://127.0.0.1:8000. 단, 아래 계약 어댑터를 A가 적용한 후 사용해야 한다. 모드만 바꿔 즉시 호환된다고 표시하지 않는다.

## 3. 실제 지원 API·필터

| GET | 쿼리 | 데이터 |
|---|---|---|
| /health | 없음 | 원본/버전/분석 가용 상태 |
| /stocks | market=KOSPI 또는 KOSDAQ,q,limit(1~100),offset | 20종목 목록,기본100 |
| /stocks/compare | as_of,market | 각 종목 기준일 이하 마지막 거래일 Gold, C 계산은 각 행 analysis |
| /stocks/{code}/daily | start,end,limit(1~5000,기본1000),offset | 일별 Gold+analysis+기준100 값 |
| /stocks/{code}/financials | year 정수,report_code,fs_div,as_of | 보고서+metrics+period_market_summary+analysis |
| /stocks/{code}/quality | start,end,limit(1~500),offset | availability/직접issues/전역statement이슈 분리 |
| /analysis/{code}/evidence | as_of | observation,financial_report,price_source,pit_rule; **data는 객체** |
| /exports/stocks/{code}/daily.csv | start,end | 기존 Gold 원래 컬럼,기준100/C신규컬럼 미포함 |
| /exports/stocks/{code}/chart.csv | start,end | 원종가·지수·stock_base100·market_base100·price_base_date·상태 |
| /exports/stocks/{code}/financials.csv | 재무조회와 동일 | 보고서×지표×기간 유형,보고서당94행 |
| /exports/analysis/g_fin_rpt_analysis.csv | 없음 | C 보고서54컬럼/320행 전량 |
| /exports/analysis/g_stock_daily_analysis.csv | 없음 | C 일별91컬럼/17440행 전량 |

report_code=11011사업/11012반기/11013제1분기/11014제3분기, fs_div=CFS연결/OFS별도. 일별 범위는 포함 경계이고 구간 밖은 정상 빈 결과. compare/evidence/as_of는 보유 범위2022-12-01~2026-06-30 안에서 선택. 휴일은 직전 관측일이며 요청기준일과 실제 trd_dt를 구분한다. 재무는 as_of 지정 시 공시일<as_of 및PIT적격만 반환, 미지정이면 부적격 보고서도 플래그와 함께 보여준다. 일별 재무 반복 합산·기관합계+기관세부 중복 합산 금지.

## 4. 가격·시장 기준100 및 A 어댑터 차이

일별 JSON은 조회구간 전체(페이지 나누기 전)에서 종가와 지수가 **동시에 유효한 양수**인 첫 거래일을 기준으로 한다. 같은 날짜의 각 원값으로 현재값/기준값×100, Decimal HALF_UP 소수8자리 문자열. meta.price_base_date와 각 행 price_base_date로 날짜를 전달한다. 페이지 이동 시 기준은 유지하며 조회 시작일을 바꾸면 다시 계산한다. 주말 시작이면 첫 유효 거래일을 사용한다.

공통 기준 전 관측은 두 지수null/BEFORE_BASE_DATE, 기준없음은null/NO_COMMON_BASE, 이후 한 계열만 결측이면 해당 값null/PARTIAL, 정상은OK. 빈 구간은 data=[]·price_base_date=null. 보간·다른 날짜별 기준·0대체를 하지 않는다. chart.csv는 같은 값과 기준일을 포함하고 X-Price-Base-Date 헤더도 제공한다. 기존daily.csv는 원 Gold 다운로드로 보존했다.

**현재 A 코드와 B는 자동 호환 상태가 아니다. A 소유 코드 수정은 이번에 하지 않았다.**

| A 제안 | B 실제 / A가 적용할 대응 |
|---|---|
| meta.schema_version=a-proposal-1 | B는 meta.api_version=1.1.0; A validator를 실제 계약으로 조정 |
| data_end / calc_version | data_final_date / calculation_version |
| synthetic / input_version | 동일 이름 제공. analysis_data_version도 스냅샷 일관성 검사에 포함 권장 |
| 모든 endpoint에 start/as_of/report/basis/year=all 전송 | endpoint별 쿼리만 전송. daily는 end=as_of, financials는 report_code=report·fs_div=basis, year=all이면 year 생략, 빈 market 생략 |
| C 계산 평면 필드 | compare/daily 각 행.analysis, financials 각 보고서.analysis. 표준컬럼과 C 계산을 화면 어댑터에서 병합하되 상태·NULL 유지 |
| evidence data 배열·lineage | data 객체의 observation/financial_report/price_source/pit_rule를 화면 근거 구조로 매핑. 미제공 원천 값을 임의로 채우지 않음 |
| as_of=trd_dt | 요청 기준일은 meta.requested_as_of, 실제 관측일은 trd_dt(meta.effective_as_of는evidence). 휴일에는 다를 수 있음 |
| 재무 row.stock_cd·period_type | 보고서.analysis.stock_cd와 C YTD/ASOF 의미를 사용. 원 헤더·metrics·원본기간플래그도 보존 |

C 필드 별칭은 A의 normalizeCRow 규칙(rev_yoy_rt→revenue_growth_rt,event_excess_rt→excess_return_rt 등)을 사용하되 먼저 analysis 중첩을 풀어야 한다. 기준100은 C의 공시후 event_* 기준과 다른 조회차트 표현이므로 서로 대체하지 않는다.

## 5. 단위·큰 금액·NULL·오류·샘플

성공{data,meta},오류{error:{code,message,details?},meta}. 업무금액·주수량·비율은 문자열,메타페이지수는 정수,날짜ISO. 원금액KRW/수급shares/비율소수(0.01=1%). 큰 원금액을 JS Number로 일괄변환하지 않는다. NULL≠"0". C상태OK/PRD_UNVERIFIED/NO_DATA/DENOM_ZERO/NEG_BASE/WINDOW_SHORT/NO_PRE_EVENT_PRICE/UNAVAILABLE과분류·검토플래그를 보존한다.

404 STOCK_NOT_FOUND,422 VALIDATION_ERROR/INVALID_DATE_RANGE/AS_OF_OUT_OF_RANGE,409 ANALYSIS_NOT_AVAILABLE(C묶음없이 신규CSV요청), 원본읽기오류503 DATA_SOURCE_UNAVAILABLE. 서버시작 무결성/접속 실패는 기동실패로 별도 확인한다. 품질 날짜필터는availability에 적용하며 발견시각없는 보고서이슈를 해당 날짜신규발견으로 해석하지 않는다.

작은 실제 샘플과 정확한 요청은 `fixtures/api/s4/`의 stocks/compare/daily/financials/evidence/quality/missing_investor/empty/invalid_date/unknown_stock.json. 각각 request/response wrapper이고 response가 API원문이다. OpenAPI전체와price_chart.csv,expected_values.json도 함께 둔다. 일반 오류는 HTTP코드와error.code를 보고 합성fallback하지 않는다. 미제공 수급247540/2026-04-16은 가격유지·수급null/N, 초기재무미연결은 금액null이다.

## 6. C와 대조할 실제 기대값·버전

입력 `handoff-sha256:4d0ed112f2cc1418`, C계산 `c-gold-0.1.0`, API1.1.0. C묶음해시는 `c-artifact-sha256:b55ee9b1d38c84977dd39a29c9c8e9066fe3cbc43cdadc7fe1286e9de05e4d25`. CSV모드data_version은입력해시,Delta모드는delta-run:20261015_101647_d567. 입력/계산/분석묶음 버전을 응답간 함께 확인한다. 전량 C출력SHA는 expected_values 및 검증JSON에 있다.

005930 삼성전자 / 기준일2026-06-30 / 선택보고서report_76a18cf53ffa7baf9975a0d8 / 공시일2026-03-10. 아래는 이 저장소의 실제 검증 자료 값이며 실시간 시장값이 아니다.

| 필드 | 기대값 |
|---|---|
| close_prc | 333000.0000 |
| rev_ytd_amt | 333605938000000 |
| op_prft_ytd_amt | 43601051000000 |
| net_incm_ytd_amt | 45206805000000 |
| op_cf_ytd_amt | 85315148000000 |
| analysis.rev_yoy_rt / op_margin_rt | 0.10880093 / 0.13069627 |
| analysis.event_excess_rt / event_base_dt | 0.32769823 / 2026-03-09 |
| analysis.co_move_cd / joint_improve_yn | IMPROVE_STRONG / N |
| analysis.frgn_flow_20d_rt / inst_flow_20d_rt | -0.06459243 / 0.00119083 |

조회구간2026-06-01~2026-06-30: price_base_date=2026-06-01,첫날두계열100.00000000. 마지막날stock_base100=93.80281690,market_base100=96.45099552. 기준 원종가355000.0000/지수8788.3800. 기대값전체는 fixtures/api/s4/expected_values.json.

## 7. 이번 실제 검사·남은 범위

- B자동검사51PASS(기존45+차트4+C묶음2), C원본테스트18OK. C계산 환경과 B제공 환경은 분리했다.
- C결과320/17440행 CSV해시가 C의고정증빙과 정확히일치. 출력금액/비율/상태를 바꾸지 않고 묶음생성·키/타입/기준입력 검증.
- CSV기준 API와 Delta기준 API에서 각각 C전체출력값1,604,320개(보고서17,280+일별1,587,040)와 신규C다운로드CSV를 대조PASS. 기준100JSON/CSV일치,휴일/페이지/빈결과/오류/결측 검사PASS.
- 신규 C두테이블 실제 Delta쓰기·버전0·전량왕복검증PASS. 신규C MySQL 적재·SQL대조는 미실행. 기존58MySQL테이블/9API/복원증빙은 기존 v1의 검사이며 G04-validation.md에서 별도 확인한다.
- 최신 실행증빙은 build/s4_api_20261015/{verified_csv,verified_delta,c_replay,c_delta,source_manifest,pytest.xml}. 실제 Delta+C묶음 HTTP16검사PASS, 증빙 build/api_http/20261015_115955_d807/http_validation.json 및 같은폴더 http_evidence.json에 등록했다.
- A별도검토브랜치·화면실제API연동·화면/CSV수치대조·새전달SHA/PR반영·공동G05는 미확인. 사용자보고A/C검사와 B실행검사를 구분한다.

## C 수치 확인 기록 (C가 실제 실행 후 작성)

상세: [S4-C-check.md](S4-C-check.md). 확인 브랜치 `review/s4-c-v1`(C HEAD `81a5705` + B `9f78ccc` merge), macOS·B Python 3.12.14·`--backend csv`.

- 판정: **값 일치** — 일별 17,440행·보고서 320행·기준일 비교 20종목, 값 차이 0. G05 005930/2026-06-30 기대값 일치.
- 합의 필요(값 오류 아님): ① 원천 통과 8개 컬럼 소수 자릿수 정규화로 `/exports/analysis/g_stock_daily_analysis.csv` 바이트 해시가 C 원본과 다름 ② `input_version` 표기가 PC마다 다름(Windows 줄바꿈 추정).
- 미실행: MySQL·Delta 경로, 신규 C MySQL SQL 대조(C12/G04), A 화면.

## A 수신 검증 기록 (A가 실제 실행 후 작성)

- A의 원래 브랜치·HEAD / 미커밋 작업 보존 방법:
- 검토 브랜치 또는 별도 검토 위치:
- B 기준 SHA / ZIP 해시 / 실제 API 버전·입력·계산·분석묶음 버전:
- 설치·시작·종료 명령 / Python·Node·OS / C 결과 위치:
- 실행한 자동검사·브라우저·실제 API·CSV 대조와 증빙:
- 정상·빈 결과·오류·NULL·큰 금액·공시당일·휴일·가격기준일 결과:
- 계약 차이·충돌·미지원·수정 요청 / 실제 수정 파일:
- 판정: 미확인 / 수정 필요 / A 수신 확인 완료 (실제 증빙에 따라 선택):
- 신규 C MySQL 검증: 미실행 유지(별도 증빙이 있을 때만 변경):
- commit·push·PR·merge: 이번 수신 요청 범위 밖:

이전 v1 상세 기록은 B 로컬 증빙에 별도 보존한다. 현재 지원 판단은 위 API1.1.0 본문을 사용한다.
