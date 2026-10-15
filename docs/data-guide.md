# 실제 데이터 사용 및 Bronze·Silver 상세 안내

## 1. 이번에 저장소에 들어온 것

`data/03_C_integration_20261014/`는 사용자가 제공한 C 통합·품질 패키지의 원본 스냅샷이다. **75파일, 104,528,932 bytes**, CSV 33개가 포함된다. CSV는 프로파일·사전·검증·메타 파일까지 포함한 개수이며 Silver는 17개, Gold는 2개다.

`data/handoff_manifest.json`에 75파일의 상대경로·크기·SHA-256과 CSV별 행수·전체 헤더를 기록했다. `.gitattributes`로 스냅샷의 줄바꿈 자동 변환을 막는다. 코드·PDF·DOCX·Excel·ERD·기존 검증 기록까지 함께 보존했다.

| 포함 | 미포함 |
|---|---|
| Silver 17개 CSV, Gold 초안 2개, Meta 2개 CSV | Bronze 입력 원본 CSV 18개와 Bronze 데이터 덤프 |
| Bronze 18테이블 DDL, Silver·Gold·Meta DDL | 별도 MySQL 덤프 ZIP·`tz_medallion_mysql8.sql.gz` |
| 표준 사전·AS-IS 진단 결과·검증 203개 기록 | 공시 원문 ZIP 752개에 해당하는 파일 실물 |
| 변환·모델 생성·MySQL 적재·검증 Python 코드 | 실제 Delta 테이블·`_delta_log`·실행 중인 DB/API |

기존 원본 `SHA256SUMS`는 덤프까지 참조하지만 덤프는 제공 폴더에 없었다. 존재하는 73개 참조 파일은 해시가 일치하며 미포함 덤프 1개는 별도로 기록한다. 새 manifest는 **실제로 받은 75파일**만 대상으로 한다.

## 2. '원본'과 AS-IS를 구분한다

이 자료는 A/B가 전달한 데이터를 C가 통합·표준화한 결과물이다. 인계 당시 `code/common.py`는 다음 두 입력 폴더를 기대한다.

- A: `02_C_handoff_20261014` — 기업·공시·재무·지표 정의·검토 이슈.
- B: `Team_B_Silver_Handoff` — 종목·가격·지수·수급·보유·CFD·가용성·복구 상태.

두 폴더는 이번 제공 범위에 없다. **C 관점의 AS-IS는 C 통합 전 A/B 인계 데이터**다. B 입력의 경로에도 `silver/`가 들어 있다. C Bronze는 이러한 인계본을 수정 없이 받아 둔 랜딩 계층이므로, 그 이름만으로 최초 교환한 오염 데이터가 모두 포함되어 있다고 해석하지 않는다.

체크북 F01의 최초 오염 원본·명세서·결함 진단 증빙은 기존 기록과 출처를 연결해 검토해야 한다. 추가 원본이 필요하면 해당 항목만 요청한다. 현재 저장된 Silver·Gold 분석은 원본 수령을 기다리지 않고 진행할 수 있다.

## 3. Bronze — 무엇을 어떤 형태로 보존했는가

### 물리 모델과 저장 정책

DB는 `tz_bronze`, DDL은 [01_bronze.sql](../data/03_C_integration_20261014/03_model/ddl/01_bronze.sql)이다. 총 18테이블이다. 원천 컬럼은 `TEXT NULL`로 보존하며 원래 식별자·빈값·JSON·날짜 표현을 유지한다. 저장용 컬럼은 별도로 붙는다.

| 추가 컬럼 | 타입·의미 |
|---|---|
| `ldng_row_no` | INT NOT NULL, 해당 입력 파일의 데이터 행 번호(1부터), 테이블 PK |
| `ldng_file_path` | VARCHAR(500) NOT NULL, 입력 패키지 기준 파일 경로 |
| `ldng_file_hash` | VARCHAR(80) NOT NULL, 입력 파일 SHA-256 |
| `ldng_run_id` | VARCHAR(64) NOT NULL, 적재 실행 ID |

`ldng_row_no`는 원천 업무 키가 아니라 행 보존용 키다. 업무 키의 중복 여부는 별도 진단한다. 모델은 정제 전에 원본을 보존하기 위한 것이며 존재하지 않는 원본 값·행을 Silver에서 복원한 것으로 대체하지 않는다.

### Bronze 18개 테이블과 Silver 연결

건수 열은 **이번 직접 읽기 값이 아니라 기존 프로파일·검증 기록**이다. `기록 미확인`은 0행을 뜻하지 않는다. 상세 원천 헤더는 [전체 사전](data-catalog.md)에 DDL에서 추출해 기재했다.

| Bronze 테이블 | 입력 상대경로 | 기록상 행수 | Silver에서의 사용 |
|---|---|---:|---|
| `b_a_company_master` | A `support/company_master.csv` | 20 | `s_corp` |
| `b_a_disclosures` | A `support/disclosures_with_documents.csv` | 11,748 | `s_dscl`, 문서 속성 분리 |
| `b_a_disclosure_documents` | A `support/disclosure_documents.csv` | 753 | `s_dscl_doc` |
| `b_a_financial_items` | A `support/financial_items_all.csv` | 66,729 | `s_fin_item` |
| `b_a_financial_summary` | A `opendart_financial_summary_20_companies.csv` | 320 | `s_fin_rpt` + `s_fin_mtrc` |
| `b_a_metric_definitions` | A `support/metric_definitions.csv` | 36 | `s_fin_mtrc_def`、`s_cmn_cd`의 지표 코드 |
| `b_a_review_issues` | A `support/review_issues.csv` | 1,855 | `s_dq_issue`의 A_SELF |
| `b_b_security_master` | B `silver/security_master.csv` | 20 | `s_stock` |
| `b_b_stock_daily_price` | B `silver/stock_daily_price.csv` | 17,440 | `s_stock_daily_prc` |
| `b_b_market_index_daily` | B `silver/market_index_daily.csv` | 1,744 | `s_idx_daily_prc` |
| `b_b_investor_trading_daily` | B `silver/investor_trading_daily.csv` | 191,829 | `s_invstr_trd_daily` |
| `b_b_foreign_holding_daily` | B `silver/foreign_holding_daily.csv` | 17,439 | `s_frgn_hold_daily` |
| `b_b_cfd_daily` | B `silver/cfd_daily.csv` | 13,719 | `s_cfd_bal_daily` |
| `b_b_price_investor_availability` | B `silver/price_investor_availability.csv` | 17,440 | `s_conn_stts` 재계산 결과와 대조 |
| `b_b_investor_source_daily` | B `silver/investor_source_daily.csv` | 17,439 | 원천 JSON 보존용, Silver 대응 테이블 없음 |
| `b_b_data_quality_issues` | B `silver/data_quality_issues.csv` | 개별 기록 미확인 | B 이슈 통합 |
| `b_b_bronze_unresolved_issues` | B `silver/bronze_unresolved_issues.csv` | 개별 기록 미확인 | B 이슈 통합 |
| `b_b_pending_recovery_review` | B `silver/pending_recovery_review.csv` | 개별 기록 미확인 | B 이슈 통합 |

B 이슈 3종에서 통합된 이슈는 기존 V1-19 기록상 2건이다. 이것을 세 입력 각각의 행수로 해석하지 않는다. 입력 파일 해시·크기는 [input_manifest.csv](../data/03_C_integration_20261014/04_output/meta/input_manifest.csv)에 있다. 이 명세에 파일명이 있다고 해당 입력 실물이 저장소에 있다는 뜻은 아니다.

## 4. Silver — 무엇을 표준화하고 유지했는가

### 공통 표준

- 기업코드 CHAR(8), 종목코드 CHAR(6), 공시 접수번호 CHAR(14): 문자열로 읽어 선행 0 보존.
- 일자는 DATE, 시각은 KST DATETIME. CSV에서 읽을 때 먼저 문자열로 보존하고 필요한 컬럼만 변환.
- 금액은 DECIMAL(20,0) 원 단위. 큰 정수를 float로 바꾸지 않음.
- 가격은 DECIMAL(18,4), 수량 BIGINT, 비율 DECIMAL(12,8)의 소수 비율(1=100%).
- 여부는 Y/N, 투자자·시장·문서 상태는 공통코드로 관리.
- NULL을 0으로 채우지 않으며 미해결·격리·보존·시점 제외 상태를 분리.
- 원천 추적은 테이블별 `src_team_cd`, `src_file_path`, `src_row_no`, `src_ver`, `pipln_ver` 등으로 유지. 파생·정의 테이블은 제공되는 컬럼만 사용.

사전 CSV에서 실제 Silver 용어는 260행이다. 전체 용어 사전 345행(23개 테이블)은 Silver·Gold·Meta를 합친 범위다. AS-IS 프로파일의 337열 기준과 전체 표준준수 검사 377열 기준도 분모가 다르므로 혼합하지 않는다.

### 주요 변환·분리·파생

| 구분 | 실제 처리 |
|---|---|
| 기업·종목 | A `stock_code`, B `symbol`을 `stock_cd`로 통일하고 기업은 `corp_cd`로 식별 |
| 공시·원문 | 공시 11,748행과 원문 수집 대상 753행을 분리. 문서 미수집과 원문 부재 상태 보존 |
| 재무 보고서 | 320행. 사업연도·보고서 코드·CFS/OFS·기간·공시 연결·비교 적격을 관리 |
| 재무 지표 | 보고서의 지표열 94개를 UNPIVOT해 320×94=30,080행. 36지표·기간 유형 조합이며 94개의 다른 지표가 아님 |
| 재무 상세 | 66,729행 보존. 좁은 계정 키 충돌 9,120행을 중복으로 삭제하지 않고 `fin_item_id`로 식별 |
| 투자자 매매 | 종목·일·투자자 유형당 1행. TOP_LEVEL 4유형과 기관 세부 7유형 분리 |
| 기업-종목 매핑 | 20건 모두 MATCHED. 현대자동차/현대차의 명칭 차이는 코드 일치 근거로 설명 |
| 연결 상태 | 가격·수급 키 합집합 17,440행. BOTH 17,439, PRICE_ONLY 1, INVESTOR_ONLY 0 |
| 품질 이슈 | A/B 이슈와 C 연결·기간·범위 이슈를 통합해 1,967행 유지 |
| 공통코드 | 표준 사전에서 코드그룹·코드값 133행 구성 |

### 핵심 조인

기업→공시·보고서는 `corp_cd`, 보고서→지표·상세는 `fin_rpt_id`, 종목→일별 데이터는 `stock_cd`다. 기업·종목 연결은 `s_corp_stock_map`을 사용한다. 가격·수급은 `(stock_cd,trd_dt)`로 연결하되 수급을 먼저 필요한 유형별로 피벗한다. 지수는 시장 코드와 거래일을 함께 사용한다.

물리 FK 15개는 [전체 컬럼·관계 사전](data-catalog.md)을 참조한다. 재무 보고서 `rcept_no`→공시의 관계는 61건이 수집 범위 밖이므로 논리 관계다. 이 61건에 공시일을 임의 생성하지 않는다.

### 빈값·상태의 실제 범위

| 항목 | 실제 제공 데이터에서 확인한 범위 | 사용 정책 |
|---|---|---|
| 주가 | 20종목 × 872일 = 17,440행 | 모든 분석의 일별 기준 |
| 외국인 보유·수급 | 가격 기준 1키 부재 | `247540 / 2026-04-16`, 0 대체 금지 |
| CFD | 2023-08-31부터 13,719행 | 가격 기준 3,721행 NULL, 전 기간 비교에 사용 불가 |
| 재무 상세 당기금액 | 2,202행 빈값 | 계정·양식별 허용 여부와 검토 상태 유지 |
| 시점/기간 비교 적격 | 보고서 각각 259 Y, 61 N | 분석 목적별 플래그 확인 |
| 핵심 실적 | 매출·영업이익·순이익·영업CF YTD 각 320개 금액 존재 | 금액 존재와 기간 검증은 별개 |
| Q3M | 매출·영업이익·순이익 각각 240/320 금액 존재 | YTD로 대체해 분기 실적이라 표시하지 않음 |
| 재무 충돌 | 보고서 1건의 `mtrc_conflict_cnt=1` | 관련 지표 근거 확인 |
| 이슈 상태 | RETAINED 1,795 / EXCLUDED_FROM_PIT 122 / EXPLAINED 41 / OPEN 8 / QUARANTINED 1 | 이슈 건수와 영향받는 원천 행수는 다름 |

보고서의 시점 선택은 공시일 < 거래일인 적격 보고서 중 사업연도·분기 순서·CFS 우선·공시일·접수번호를 기준으로 한다. 기존 `code/run_pipeline.py`의 `pit_select`를 재사용 검토한다.

## 5. Gold — 지금 바로 분석 가능한 범위

`g_ai_stock_daily`는 17,440행 × 34열이며 가격·지수·최상위 수급·보유·CFD·시점 재무가 합쳐져 있다. 재무 가용 15,833행, 미가용 1,607행. 첫 관측일의 수익률은 종목별로 비어 있고 예측 라벨은 없다.

`g_fin_rpt_mkt_smry`는 보고서별 320행 × 21열이다. 전체 가격 기간 커버리지 Y 240건에만 성과·수급 합을 계산하고 N 80건은 NULL로 둔다. **보고기간 시장 요약과 공시 후 반응은 다른 분석**이다.

앞으로 `g_fin_rpt_analysis`와 `g_stock_daily_analysis`를 [프로젝트 설계](project-plan.md)에 따라 추가한다. 현금흐름·실적 지표는 보고서 단위에서, 가격·수급 윈도는 종목·일별에서 계산한다. 기존 결과를 보존하고 별도 개발 경로에서 확장한다.

## 6. 역할별 실제 데이터 출발점

| 역할 | 먼저 읽을 실제 자료 | 즉시 가능한 작업 | 추가 입력이 필요한 작업 |
|---|---|---|---|
| A 이어진 | `s_stock`, 기존 Gold 2개, 본 문서·사전 | 실제 컬럼·기간·NULL을 반영한 화면·표시·API 요구 정리 | 실제 API 연동은 B 구현 필요 |
| B 설호현 | DDL 5개, 기존 적재 코드, Silver·Gold·Meta CSV | 제공 CSV의 신규 저장·조회·API 연결, 실제 Delta Silver/Gold 확장 | 원래 Bronze 재현·전체 원본 대사는 A/B 입력·덤프 필요 |
| C 김형준 | Silver 17개, Gold 2개, 사전·프로파일·검증·처리 코드 | 실제 전량 지표 계산·기간 검증·차트 설계·Gold 확장 | 최초 오염 원본 재진단은 해당 원본·명세 필요 |

Silver 파일이 이미 저장소에 있으므로 B/C 시작 시 같은 파일을 다시 업로드해 달라고 요청하지 않는다. A는 제공 CSV가 API 서버인 것처럼 취급하지 않고 B와 응답 계약을 맞춘다.

## 7. 안전한 읽기와 확인 명령

저장소 루트에서 실행:

```bash
python3 scripts/check_handoff.py
python3 -m unittest discover -s scripts/tests -v
```

Pandas 환경이 준비되었다면 다음처럼 읽는다. 설치 버전 고정은 B01에서 관리한다.

```python
from pathlib import Path
import pandas as pd

package = Path("data/03_C_integration_20261014")
price = pd.read_csv(
    package / "04_output/silver/s_stock_daily_prc.csv",
    dtype=str, encoding="utf-8-sig", keep_default_na=False,
)
assert len(price) == 17_440
assert price["stock_cd"].str.fullmatch(r"[0-9]{6}").all()
```

빈 문자열 정책을 명시적으로 변환하고, 금액은 정수·Decimal 등 정밀도를 보존하는 타입으로 계산한다. 원본 스냅샷의 `code/common.py`도 문자열 보존 읽기를 사용한다.

## 8. 원래 코드의 실행 전제

| 코드 | 필요한 전제·주의 |
|---|---|
| `common.py` | `--a-dir`, `--b-dir` 또는 `TZ_A_DIR`, `TZ_B_DIR`. 없으면 패키지 옆 두 입력 폴더를 기대 |
| `profile_asis.py` | A/B 입력 원본과 Pandas 필요. 진단 결과 디렉터리에 쓰기 |
| `run_pipeline.py` | A/B 입력·기존 정책 필요. `04_output` 결과를 덮어씀 |
| `build_model.py` | A/B 입력을 읽어 사전·DDL·ERD를 재생성. Graphviz 사용 가능 여부 확인 |
| `load_mysql.py` | A/B 입력·Pandas·pymysql·MySQL 필요. DDL 실행·DB 테이블 재적재 |
| `validate.py` | 원본·DB 등 필요. `--rerun`은 파이프라인·적재를 다시 실행 |

**저장소에 코드가 들어왔다고 전체 파이프라인이 즉시 실행 가능한 것은 아니다.** 스냅샷 내부에서 재실행해 Git 기준 데이터를 바꾸지 않는다. 재사용할 코드는 출처·버전을 기록해 활성 경로로 옮기거나 별도 작업 사본에서 실행한다. DB 적재 전 대상 DB와 DROP/덮어쓰기 범위를 확인한다. 이번 업로드에서는 DB·Delta 변환·203개 교차검증 재실행을 하지 않았다.

## 9. 이번 검증과 남은 제출 증빙

이번에 직접 확인한 것은 75파일 복사 일치, 파일 크기·해시, CSV 헤더·행수, Silver 기본키·FK, Gold 공시일 경계와 명세 일관성이다. 이전 SQL/Pandas 검증 203 PASS는 **보존된 과거 실행 기록**이다.

추가 확보·구현: 최초 오염 원본·명세서와 C 입력 A/B 패키지, 필요한 원문·덤프, 실제 Delta 3레이어·버전, 신규 Gold 지표·AI 입력 규격, DB/API·화면 통합·재실행 증빙. [체크북](workbook.md)은 자료 업로드만으로 완료 처리하지 않는다.
