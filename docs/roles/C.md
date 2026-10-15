# C 진행 기록 — 김형준 / Pandas 분석·시각화

상태: **기준 반영·점검·분류 완료 / 신규 기능 구현 미착수.** [프롬프트](../../prompts/C_analysis.md) · [체크북](../workbook.md) · [보완 업무](../missing-work.md) · [진행표](../integration-status.md).

단계 책임: S0 분석/차트 계약, S1 진단 근거, S2 규칙 대사, **S3 검사한 Gold 계산을 handoff 브랜치·고정 SHA·실행법으로 B에 전달**, S4 API 수치 확인, S5 전체 대사.

## 1. 기준 반영 기록 (2026-10-15)

| 항목 | 실제 값 |
|---|---|
| 저장소 | `https://github.com/2nd-MLOps-engineer-2/Team-Zero.git` |
| 작업 브랜치 | `feature/c-gold-analysis` (깨끗한 clone의 `main`에서 생성, 기존 C 작업 브랜치 없음) |
| 기존 HEAD | `8af915fba1c40849b4cb80d7d8c2bd1768f674b7` |
| 기준 커밋 포함 여부 | `git fetch origin` 후 `origin/main`·`origin/integration` 모두 `8af915f…`를 포함(두 브랜치 HEAD가 동일) |
| 반영 | `git merge --ff-only origin/main` → Already up to date. `origin/integration`은 `main` 대비 추가 커밋 0개라 별도 반영 대상 없음 |
| 기존 작업 보존 | 기존 미커밋 변경 없음. 미추적 `.DS_Store`(macOS 생성) 1개는 삭제·커밋하지 않고 유지. 강제 reset·stash·삭제 없음 |
| 충돌 | 없음 |
| 로컬 환경 | `.venv/`(gitignore 대상): Python 3.13.15, pandas 3.0.6, numpy 2.5.4, matplotlib 3.11.2 — uv로 생성. 팀 공통 의존성 고정은 B01 범위이며 C 전용 고정 파일은 아직 없음 |

## 2. 실행한 검사

| 명령 | 결과 | 구분 |
|---|---|---|
| `python3 scripts/check_handoff.py` | PASS — 75파일 해시·크기, CSV 33개 헤더·행수. 덤프 1개 미포함 표시 | 파일 무결성(실제 데이터) |
| `python3 -m unittest discover -s scripts/tests -v` | 2 tests OK | 검사 도구 단위 테스트 |
| Pandas 읽기 전용 확인(스크래치, 저장소 출력 없음) | 기존 일별 Gold `dscl_dt >= trd_dt` 0건, 재무 가용 15,833행, 연결 보고서는 모두 `pit_join_elig_yn=Y` | 기존 Gold 재확인(신규 Gold 아님) |
| 〃 | `s_dq_issue` RETAINED 1,795 / EXCLUDED_FROM_PIT 122 / EXPLAINED 41 / OPEN 8 / QUARANTINED 1 | Silver 상태 확인 |
| 〃 | 기간 비교 부적격 61건 = 2022 Q1·반기·Q3 각 20건 + `066570` 2025 사업보고서 1건(`rcept_no 20260706000276`, 데이터 최종일 이후 접수) | M07 범위 특정 |
| 〃 | 지표 충돌 1건: `report_085596476a4ce774dab318fa`(`003490` 대한항공, 2023 사업보고서 CFS, `rcept_no 20240313001650`) | M07 범위 특정 |
| 〃 | 기존 기간 요약 `full_cvrg_yn`×`same_prd_cmpr_elig_yn`: Y·Y 239 / Y·N 1 / N·Y 20 / N·N 60 | Gold 기간 요약 사용 범위 |

미실행: MySQL 복원·203개 검증 재실행·Delta·API·브라우저 검사(환경·구현 없음). 기존 `code/*.py` 파이프라인은 A/B 입력·DB 전제와 출력 덮어쓰기 때문에 실행하지 않음. 신규 Gold 계산·차트는 이번 범위가 아니므로 미구현.

## 3. 담당 업무 분류

분류: **이미 포함** / **증빙 확인 필요** / **문서·계약 미작성** / **미구현** / **입력·합의 필요**. 체크북 체크는 하지 않았다.

| ID | 분류 | 기존 자료·근거 | 부족한 것 → 다음 작업 |
|---|---|---|---|
| C01 원본 진단 | 증빙 확인 필요 + 입력 필요 | `01_profiling/` 14테이블·337열 진단, `asis_issue_summary.csv` 23항목(결측·중복·형식·코드값·명명) | 이 진단은 **C 통합 전 A/B 인계본** 기준. 최초 교환 오염 원본 진단은 원본 없이는 불가 → 입력 요청 R1 |
| C02 명세 대조 | 증빙 확인 필요 + 입력 필요 | 이슈 요약의 분모·근거 열, 정상 결측(CFD 범위·상세 `-`) 구분 기록 | 최초 명세서 미포함 → R1. 기존 기록을 파일·컬럼·결함 유형·분모 표로 재정리(`analysis/` 문서) |
| C03 표준 사전 | 이미 포함(검토 필요) | `02_standard_dictionary/` 단어 168·용어 345·도메인 26·코드 133·명명규칙 12, xlsx | 신규 Gold 컬럼(`g_fin_rpt_analysis`·`g_stock_daily_analysis`) 용어·도메인 미등록 → 별도 확장 사전 추가 |
| C04 변환·미해결 정책 | 증빙 확인 필요 | `s_dq_issue` 상태 5종, 원 코드 `run_pipeline.py` | B 실행 코드에 넘길 정책 문서 없음 → `contracts/analysis.md`에 격리·보존·재조회 상태 정의 |
| C05 재무 기간·계정 | 증빙 확인 필요 + 입력 필요 | `cal_prd_stts_cd`·`cf_prd_stts_cd` 259 VERIFIED / 61 미검증, 충돌 1건 | 61건·충돌 1건은 원문 필요 → R2. 나머지는 기간·연결구분 검사 코드 추가 |
| C06 주가·수급·시점 | 증빙 확인 필요 | 기존 Gold PIT 위반 0, `pit_select`(공시일 < 거래일), TOP_LEVEL/INST_DETAIL 구분 | 신규 Gold용 독립 PIT·이중합산 검사 미작성 → `analysis/tests` |
| C07 실적 변화 | 문서·계약 미작성 + 미구현 | 설계: `project-plan.md` §4 지표 정의 | 성장률·이익률·영업이익 증감·적자/흑자 전환·분모 0 상태 계산 |
| C08 현금·시장 비교 | 미구현 | 영업CF YTD 320건 존재, 기존 기간 요약의 가격·수급 합 | 영업CF/매출·CF 변화, 시장 대비 성과, TOP_LEVEL 순매수 비율 계산 |
| C09 동반 개선·괴리 | 문서·계약 미작성 + 미구현 | 설계 초안(매출 성장률 × 공시 후 시장 대비 성과 4분류) | 현금·수급 보조 근거, 분석 불가 사유 코드, 임계값·버전 문서화 |
| C10 시각화 | 문서·계약 미작성 + 미구현 | 인계 보고서 ERD·위반 차트(분석 차트 아님) | `contracts/visualization.md` + `analysis/` 샘플 그래프 |
| C11 AI 입력 규격 | 문서·계약 미작성 | 기존 `g_ai_stock_daily`(라벨 없음) | 특징·결측·시간순 분할·라벨 분리 규격. 모델은 후속 범위 |
| C12 Pandas 검증 | 미구현 + 합의 필요 | 기존 203 PASS(과거 기록, 신규 Gold 증거 아님) | B의 SQL 결과가 있어야 대조 가능 → G04 합의 |

| 보완 ID | 분류 | C 담당 범위·다음 작업 |
|---|---|---|
| M01 입력 18개 | 입력·합의 필요(B 주도) | B가 확보하면 `input_manifest.csv` 해시와 대조 확인 |
| M02 최초 오염 원본 증빙 | 입력 필요 + 문서 미작성 | 기존 AS-IS(인계본)와 최초 원본을 분리한 진단 문서·진단 코드 준비, 합성 검사로 먼저 검증 |
| M03 원문 ZIP·기간 근거 | 입력 필요 | 필요한 보고서 범위 지정 = R2 |
| M05 Bronze Delta | 미구현(B 주도) | B 저장 후 원본↔Delta 건수·값 대사 |
| M06 Silver 저장·대사 | 미구현(B 주도) | B 적재 후 17테이블 371,437행·키·값 Pandas 대사 |
| M07 기간·계정 잔여 | 증빙 확인 필요 + 입력 필요 | 61건·충돌 1건·상세 빈값 2,202행 사용 범위 규칙 작성(0 대체 금지) |
| M08 알려진 부재 | 증빙 확인 필요 | `247540/2026-04-16`(OPEN·QUARANTINED), CFD 2023-08-31 이전 3,721행, 재무 미가용 1,607행 → 영향 지표·상태 표 작성 |
| M09 계약 | 문서·계약 미작성 | `contracts/analysis.md`, `contracts/visualization.md` 작성(제안 상태) |
| M10 신규 Gold | 미구현 | `g_fin_rpt_analysis` 320행, `g_stock_daily_analysis` 17,440행 계산 모듈 |
| M14 AI 규격·대사 | 문서 미작성 | C11 규격 + G04 대사 기록 |

## 4. 필요한 입력 (한 번에 요청)

실제 Silver·Gold는 저장소에 있으므로 다시 요청하지 않는다. 아래는 해당 작업에만 필요하다.

- **R1 (C01·C02·M02, F01):** 최초 교환 오염 원본 파일 전체와 당시 데이터 명세서. 파일명·수집일·해시 포함. 없으면 C 통합 전 A 인계(`02_C_handoff_20261014`)·B 인계(`Team_B_Silver_Handoff`) 18개 파일이라도 — `04_output/meta/input_manifest.csv`의 경로·해시와 같은 버전.
- **R2 (C05·M03·M07):** OpenDART 원문 또는 최초 공시본 — ① 2022 사업연도 1분기(11013)·반기(11012)·3분기(11014) 보고서 20개 기업 × 3 = 60건(공시목록 수집 범위 밖, 기간·CF 누적 미검증), ② `066570` 2025 사업보고서 `rcept_no 20260706000276`, ③ `003490` 2023 사업보고서 CFS `rcept_no 20240313001650`(지표 충돌 1건). 우선순위는 ③ → ② → ①.
- **R3 (C12·G04·M05·M06):** B의 Silver/Gold 적재 결과와 대조용 SQL 결과(B 구현 후).

## 5. 단계별 전달 계획 (브랜치·PR은 아직 만들지 않음)

| 단계 | C가 넘기거나 받는 것 | 전달 브랜치 예정명 | 수신자·수신 검사 |
|---|---|---|---|
| S0 계약 | `contracts/analysis.md`(G01)·`contracts/visualization.md`(G03) 제안본 + 정상/NULL/분모0 예제 | `handoff/s0-c-to-ab-v1` | B: 컬럼·타입·단위가 DDL·API와 일치 / A: 축·단위·분석 불가 문구 표시 가능 여부 |
| S1 Bronze | 인계본 AS-IS와 최초 원본 진단 분리 문서·진단 코드(R1 확보 시 실측) | `handoff/s1-c-to-b-v1` | B: 원본 보존·Delta 행과 진단 분모 일치 |
| S2 Silver | 기간·계정·수급 규칙 검사 코드와 Pandas 집계 기대값 | `handoff/s2-c-to-b-v1` | B: 371,437행·키·기간 상태 SQL 결과와 대조(G04) |
| **S3 Gold (C 주 전달)** | `analysis/` 계산 모듈·실행법·320/17,440행 결과·검사(PIT·윈도·분모·이중합산)·차트 샘플 | `handoff/s3-c-to-b-v1` | **B**: `review/s3-b-v1`에서 B HEAD에 C SHA 병합 → 실행·저장·건수·값 일치. **A**: 차트 의미 확인 |
| S4 API→화면 | C는 API 수치·기간·단위 확인(수신 측) | — (B의 `handoff/s4-b-to-a-v1`) | C: 동일 종목·기준일 API 값과 Gold 대조 결과를 S4 기록에 남김 |
| S5 전체 | G05 사례 1건 원본→Gold→DB→API→화면·CSV 대조 | 공동 | A·B·C 공동 |

각 전달 시: 검사한 커밋에서 handoff 브랜치 생성·push → base `integration` PR → `docs/handoffs/S{n}-C-to-B.md`(TEMPLATE 복사)와 진행표에 전체 SHA·실행법·기대값·NULL/오류 검사·원천 버전 기록 → 수신 확인 전에는 `수신 확인 대기`로만 표시.

## 6. 다음 개발에서 바로 시작할 작업

1. `contracts/analysis.md` 초안: 두 신규 Gold의 PK·컬럼·타입·단위(소수 비율·원·주)·계산식·상태 코드(`OK`/`DENOM_ZERO`/`NEG_BASE`/`WINDOW_SHORT`/`PRD_UNVERIFIED`/`NOT_PIT_ELIGIBLE`/`NO_DATA` 등, 제안).
2. `analysis/` 모듈: Silver 읽기(문자열 보존·Decimal) → `g_fin_rpt_analysis` 320행 → `g_stock_daily_analysis` 17,440행(기존 `pit_select` 규칙 재사용, 출처 `code/run_pipeline.py` c-integration-1.0.0 명시) → 출력은 `build/analysis/`.
3. `analysis/tests`: 정상·분모 0·음수 기준·결측·공시 당일 경계·기관 이중합산·행 수 보존 검사(합성 + 실제).
4. `contracts/visualization.md`와 1종목 샘플 차트(가격·지수 기준 100, 실적·CF, 수급, 사분면).
5. C11 AI 입력 규격 문서, B와 G04 대조 방식 합의.

| 작업 ID | 변경·증빙 경로 | 실행 명령·결과 | 기준 커밋/데이터 버전 | 남은 의존성 |
|---|---|---|---|---|
| 기준 반영·분류 | `docs/roles/C.md` | 위 §2 | `8af915f` / `03_C_integration_20261014`, pipln `c-integration-1.0.0` | R1·R2·R3 |
| C01~C12 | 미구현(분류만 완료) | 미실행 | — | 위 §3·§4 |
