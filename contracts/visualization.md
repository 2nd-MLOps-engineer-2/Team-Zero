# G03 시각화 계약 — C 제안 / c-gold-0.1.0

상태: **실제 데이터 시안 제공 / A 사용성·브라우저 검증 대기**.

차트 시안: `analysis/evidence/analysis-preview.png`. 재생성: `python -m analysis.run`, `build/analysis/analysis-preview.png`. 공개 데이터의 실제 계산 시안이며 웹 구현이나 실시간 시세가 아니다.

| 화면·그래프 | 입력 | 축·단위·표현 | 주의 |
|---|---|---|---|
| 가격·시장 비교 | 일별 종가·지수 | x 거래일, y 조회 구간 첫 유효 관측=100. 두 계열 같은 기준일 | 제공 종가 기준·수정주가 미확인 |
| 실적·현금 | 보고서별 `rev_ytd_amt`, `op_cf_ytd_amt` | x `prd_end_dt`, y 원(차트 표시만 조 원), YTD 표시 | 기간별 누적 실적을 더하거나 분기 단독이라 부르지 않음 |
| 외국인·기관 수급 | 일별 `frgn_flow_20d_rt`, `inst_flow_20d_rt` | x 거래일, y 소수 비율×100 %, 범례 투자자 유형 | 순매수 수량/거래량. 금액·보유율과 구분 |
| 동행/괴리 사분면 | 기준일별 `rev_yoy_rt`, `event_excess_rt` | x 매출 YoY %, y 공시 후 초과성과 %p. 0축, 점은 보유 종목 | 공시 후 경과 기간이 종목마다 다름. 성장률·공시일·기준일·event_base_dt를 툴팁으로 노출 |

툴팁: 종목 코드/명, 기준일, 보고서 ID·연도·유형·CFS/OFS, 공시일·경과일, 실제 계산 시작/종료일, 원천·계산 버전, 값·상태·검토 이유. 원천 metadata가 없는 필드는 미제공으로 표시한다.

| 코드 | 표시 문구 |
|---|---|
| IMPROVE_STRONG | 실적 개선·시장 대비 강세 동행 |
| IMPROVE_WEAK | 실적 개선·시장 대비 약세 괴리 |
| SLOW_STRONG | 실적 둔화·시장 대비 강세 괴리 |
| SLOW_WEAK | 실적 둔화·시장 대비 약세 동행 |
| NEUTRAL | 기준값 0, 방향 중립 |
| NO_DATA / UNAVAILABLE | 자료 부족으로 판단 불가 |
| PRD_UNVERIFIED | 재무 기간 검증 필요 |
| DENOM_ZERO / NEG_BASE | 기준값 0/음수로 비율 계산 불가 |
| WINDOW_SHORT / NO_PRE_EVENT_PRICE | 과거 관측 부족/공시 전 기준가격 없음 |

빈값은 0으로 그림에 찍지 않고 선을 끊거나 분석 불가 표로 별도 표시한다. Y/N/판단 불가를 구분하고 joint_improve의 조건을 설명한다. 시안은 영어 폰트로 렌더링했으며 위 표의 한글 문구가 A 화면 계약이다. A가 언어·색·범례·접근성·반응형을 실제 화면에서 검사한다.
