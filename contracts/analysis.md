# G01 분석·변환 계약 — C 제안 / c-gold-0.1.0

상태: **C 구현·로컬 검사 / B 실행·저장 및 A 사용 확인 대기**. 버전 변경은 계산 의미·컬럼·기간·NULL 정책을 함께 기록한다. 구현은 `analysis/gold.py`, 실행법은 [analysis README](../analysis/README.md)다.

## 입력·행 단위·출력

고정 패키지의 Silver 17개, 기존 `g_ai_stock_daily.csv`, 표준 사전을 사용한다. 입력 파일 SHA-256은 실행 결과 `validation.json`에 기록한다. 원천은 읽기만 한다.

- `g_fin_rpt_analysis`: PK `fin_rpt_id`, 보고서당 1행, 기준 데이터 320행. 보고서 메타·공시일·종목 매핑·핵심 재무 금액·비율·상태·원천 버전을 보존한다.
- `g_stock_daily_analysis`: PK `(stock_cd,trd_dt)`, 가격 기준 1행, 기준 데이터 17,440행. 기존 일별 34컬럼에 계산 결과를 추가한다. 보고서 금액을 일별에서 합산하지 않는다.
- 전체 필드별 타입·순서·빈값은 `analysis/evidence/schema.json` 및 재생성된 `build/analysis/schema.json`에 정의한다. B는 이 정의를 검토해 DDL·API를 만든다. 미래 확장 입력에는 고정 320/17,440 하드코딩 대신 원천 행 보존을 적용한다.

## 타입·단위·결측

CSV UTF-8 BOM, 줄바꿈 LF, 식별자는 문자열, 빈 필드는 NULL. Y/N과 코드형 필드를 명시한다. 원 금액·주 수량을 float로 재저장하지 않는다. 원천 금액 DECIMAL(20,0), 차분/기간합 제안 DECIMAL(21,0), 비율 DECIMAL(18,8). 비율은 소수(1=100%)이고 HALF_UP 8자리다. 변동성만 NumPy 표본 표준편차로 계산한다.

JSON 샘플은 정밀도·명시적 CSV 대응을 위해 금액·비율을 문자열, 빈값을 빈 문자열로 보존한다. **B의 실제 API에서는 빈값을 JSON null로 매핑하고 상태 코드를 유지**하는 계약을 제안한다. 프론트엔드는 원·주·%·%p를 표시한다. 사례 데이터가 실제 공개 입력에서 계산됐음을 표시하고 합성 예외 검사는 별도로 둔다.

## 보고서 지표

핵심 7지표는 REVENUE, OPERATING_PROFIT, NET_INCOME, OPERATING_CASH_FLOW, TOTAL_ASSETS/LIABILITIES/EQUITY다. 손익·현금은 YTD/PRIOR_YTD, 잔액은 ASOF를 사용한다. 분기 단독 추정은 하지 않는다.

| 필드 | 계산·예외 |
|---|---|
| `rev_yoy_rt` | 당기 매출/전년동기 매출−1. 동일기간 비교 적격·VERIFIED_XML 필요 |
| `op_margin_rt` | YTD 영업이익/매출. VERIFIED_XML 필요 |
| `debt_equity_rt` | ASOF 부채/자본. VERIFIED_XML 필요. 자본≤0은 계산 불가 |
| `op_cf_sales_rt` | YTD 영업CF/매출. VERIFIED_XML·VERIFIED_XML_YTD 필요 |
| `op_cf_yoy_rt` | 당기 영업CF/전년동기 영업CF−1. 기간 검증·비교 적격 필요. 전년 음수 기준률은 산출하지 않음 |
| `op_prft_delta_amt`, `op_cf_delta_amt` | 당기−전년동기 원 단위 차이. 검증된 동일기간만 계산하고 상태도 저장 |
| `op_prft_transition_cd` | LOSS_TO_PROFIT / PROFIT_TO_LOSS / PROFIT_CONTINUES / LOSS_CONTINUES / ZERO_BOUNDARY. 부적격·결측은 별도 코드 |
| `review_required_yn` | 기존 충돌·핵심 누락 메타가 있으면 Y. 보조 장기차입금 충돌을 핵심 지표 해결·격리로 바꾸지 않음 |

## 종목·일별 지표

- `rtn_{1,5,20}d_rt`: 종가[t]/종가[t−n]−1. n은 거래소 캘린더가 아닌 **종목 관측 간격**이다.
- `idx_rtn_{1,5,20}d_rt`: 동일 시작·종료 관측일에 연결된 지수 성과.
- `excess_{1,5,20}d_rt`: 종목 성과−지수 성과. 화면에서는 %p. 복리 초과성과가 아니다.
- `{frgn,inst,indv}_net_{5,20}d_qty`: 현재 포함 최근 n개 관측의 TOP_LEVEL 순매수 수량 합.
- `{frgn,inst,indv}_flow_{5,20}d_rt`: 위 합/동일 기간 거래량 합. n개 모두 있어야 계산, 누락 1개라도 NO_DATA. 기관 세부를 더하지 않는다.
- `frgn_hold_change_20d_rt`: t와 t−20 보유율 차이. 두 끝점 필요. 화면에서는 %p.
- `volatility_20d_rt`: 최근 20개 유효 일별 수익률의 표본 표준편차(ddof=1), 연율화하지 않음.

성과의 n간격은 n+1개 관측, 수급 n기간은 n개 관측이 필요하다. 최초 윈도는 WINDOW_SHORT, 이후 누락은 NO_DATA다. 결측을 전방채움·0 대체·보간하지 않는다.

## 시점·공시 이후 반응과 분류

공시일<거래일, `pit_join_elig_yn=Y`인 보고서 중 `(사업연도, 분기순서, CFS 우선, 공시일, 접수번호)` 최댓값을 고른다. 공시 당일 제외, 뒤늦은 과거 사업연도 정정공시가 최근 기간을 덮지 않는다. 선택 결과가 기존 일별 Gold와 다르면 실행을 실패시킨다.

`event_base_dt`는 선택 보고서 공시일 **전 마지막 관측일**이다. 그 종가·지수부터 현재까지의 종목/지수 성과·차이를 `event_rtn_rt`, `event_idx_rtn_rt`, `event_excess_rt`로 둔다. 기준 가격이 없으면 NO_PRE_EVENT_PRICE. 원문·공시 부재를 보고기간 종료일로 대체하지 않는다.

`co_move_cd`: 매출 성장률과 공시 후 초과성과 부호로 IMPROVE_STRONG / IMPROVE_WEAK / SLOW_STRONG / SLOW_WEAK. 어느 축이 0이면 NEUTRAL, 계산 불가면 UNAVAILABLE. `co_move_stts_cd`에 이유를 보존한다.

`joint_improve_yn`: 성장률>0·공시 후 초과성과>0·검증된 영업CF 차분>0·20관측 외국인 순매수>0·기관 순매수>0 모두 만족 시 Y. 모두 판단 가능하되 하나라도 불만족이면 N, 필요 정보가 없으면 NULL/UNAVAILABLE. 매출/가격 2축 분류를 수급·현금의 복합 점수로 바꾸지 않는다. 관측 패턴이며 인과·매매 신호가 아니다.

## 상태와 잔여 검증

OK / NO_DATA / DENOM_ZERO / NEG_BASE / PRD_UNVERIFIED / WINDOW_SHORT / NO_PRE_EVENT_PRICE / UNAVAILABLE. 각 비율·기간 계산에 상태 필드를 둔다. 기간 미검증은 분모 검사보다 우선해 표시한다. 금액은 원천대로 보존한다.

### Silver 업무 규칙 검사 (`analysis/rules.py`, `validation.json`의 `silver_rules`)

| ID | 종류 | 규칙 | 실제 결과(c-gold-0.1.0) |
|---|---|---|---|
| SS02 | 통과/실패, 실패 시 실행 중단 | 종목·일별 `INSTITUTION`(TOP_LEVEL) 순매수 = `INST_DETAIL` 7유형 합. 투자자 간 합계에 기관 세부를 더하면 이중 계산이므로 TOP_LEVEL만 사용한다 | 17,439/17,439 일치 |
| SF04 | 발견 사항 | 반기·3분기 보고서 YTD(n)−YTD(n−1)=Q3M(n) (매출·영업이익·순이익, 같은 기업·연도·연결구분). 차이 0=MATCH, \|차이\|≤1,000,000원=UNIT_ROUNDING(백만원 단위 공시 반올림 추정), 그 외 REVIEW | 480건 중 MATCH 453, UNIT_ROUNDING 7, REVIEW 20(보고서 11건) |
| SF06 | 발견 사항 | Y년 보고서 PRIOR_YTD ≠ Y−1년 같은 보고서의 YTD (재작성·정정 가능성) | 각 240건 중 매출 32(8개 기업)·영업이익 38·순이익 13 |

SF04 REVIEW 중 로컬 원문이 있는 11행(보고서 6건)은 Silver YTD·Q3M이 모두 원문에 존재해 보고서 간 재작성 차이로 판정했다(`sf04_review_documents`). 원문 없는 2022년 5건은 미판정.

### C08 같은 기간 비교

보고기간 동안의 종목·지수 성과와 TOP_LEVEL 순매수 합은 기존 `g_fin_rpt_mkt_smry`(320행, 전체 커버리지 240)를 `fin_rpt_id`로 1:1 연결해 쓴다. 공시 후 반응(`event_*`)과는 다른 관측 구간이다. 부분 커버리지 80건은 값이 NULL이며 이를 검사한다(`c08_report_period_join`, 실패 시 실행 중단).

발견 사항은 Silver 플래그·Gold 값을 바꾸지 않는다. REVIEW 보고서는 원문 대조 목록(M07)에 올린다. 성장률은 같은 보고서의 PRIOR_YTD(재작성된 비교 기준)를 사용하며 전년 보고서의 당시 값으로 바꾸지 않는다. Q3M은 MVP 지표에 쓰지 않는다. 상세 행은 `build/analysis/rule_period_continuity.csv`, `rule_prior_ytd_restatement.csv`.

B는 실행 후 원천·결과 SHA, 행수·PK, Decimal 금액, PIT·TOP_LEVEL 대사와 SQL 결과를 G04에 남긴다. 수신자 검증 없이 상태를 합의·통합 완료로 올리지 않는다. 기존 203 PASS와 이번 검사 결과는 별개다.
