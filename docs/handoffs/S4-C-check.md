# S4 — C 수치 확인 (B API ↔ C Gold)

2026-10-15 / 수신 확인 C 김형준 / **C 수치 확인: 값 일치, 표기 2건 합의 필요.** [S4 B 전달 기록](S4-B-to-A.md) · [진행표](../integration-status.md) · [절차](../integration-workflow.md).

## 확인 대상과 브랜치

| 항목 | 실제 값 |
|---|---|
| C 작업 브랜치·HEAD | `feature/c-gold-analysis` `81a5705` (review 브랜치 생성 직전 확인 기준 미커밋 변경 없음, 미push 6커밋은 S3 작업·문서) |
| 수신 확인 브랜치 | `review/s4-c-v1` = C HEAD + B [PR #6](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/6) head `9f78cccd208d750cf2726ab11e85a0a6218b3bba` merge (`origin/feature/b-pipeline-api`에 존재 확인) |
| merge 충돌 | `docs/integration-status.md` 1건: B의 S0~S2·S4 행 유지, S3 행에 C 검사 SHA `fb1f802…`·PR #4 복원 |
| API·버전 | API 1.1.0, `--backend csv`, `calculation_version c-gold-0.1.0`, `analysis_status AVAILABLE`, `input_version handoff-sha256:89e81d3d549f6ea0` |
| 환경 | macOS, C 계산 Python 3.13.15(`.venv`) / B API Python 3.12.14(`build/s4-c-review/b-venv`, `requirements.lock.txt` 설치·`uv pip check` 통과). `setup.ps1`(Windows) 대신 uv로 같은 lock 설치 |

## 실행 명령 (프로젝트 루트)

```bash
.venv/bin/python -m unittest discover -s analysis/tests
.venv/bin/python -m analysis.run --output build/s4-c-review/analysis
uv venv --python 3.12 build/s4-c-review/b-venv
uv pip install --python build/s4-c-review/b-venv/bin/python -r backend/service/requirements.lock.txt
build/s4-c-review/b-venv/bin/python -X utf8 -m pytest backend/service/tests -q
build/s4-c-review/b-venv/bin/python -X utf8 backend/service/pack_c_analysis.py --source build/s4-c-review/analysis --output build/s4-c-review/c_api_artifact
build/s4-c-review/b-venv/bin/python -X utf8 backend/service/run.py --backend csv --analysis-dir build/s4-c-review/c_api_artifact --port 8000
# 다른 창에서
.venv/bin/python -m analysis.verify_api --gold build/s4-c-review/analysis --out build/s4-c-review/api_check.json
```

`analysis/verify_api.py`는 B의 `verify_s4.py`와 별개인 C 쪽 독립 대조 도구다. 값을 문자열로 비교하고, 다르면 두 값이 모두 순수 숫자 형식이고 Decimal이 같을 때만 **표기 차이**, 나머지는 **값 차이**로 나눈다. CSV 빈칸 = API null.
행 단위 검사(일별·보고서·비교)는 Gold·API 양쪽 키·컬럼을 대조해 누락·추가·중복 키(API 쪽 `duplicate_keys`, Gold 쪽 `gold_duplicate_keys`)가 모두 0일 때만 PASS이며, 일별은 offset으로 끝까지 받고, 비교는 Gold 마지막 거래일로 조회해 API `data_final_date`와 다르면 FAIL이다. `rows_gold`는 Gold CSV 실제 행 수다.
종목 조회 404는 "그 종목 API 행 없음"으로 보고 Gold 행을 `missing_rows`로 센다(`api_not_found_stocks`에 종목 기록). 404가 아닌 HTTP 오류·연결 실패·응답 형식 오류는 `errors`에 기록하고 FAIL이며, 어느 경우든 결과 JSON을 남긴다.

## 결과

| 검사 | 결과 |
|---|---|
| C 테스트 (B 변경 merge 후, verify_api 수정 반영) | 34/34 OK (`test_verify_api` 16건 포함) |
| C Gold 재생성 해시 | `g_fin_rpt_analysis` `4514982c…`, `g_stock_daily_analysis` `a094a995…` — S3 전달본과 동일 |
| B 자동검사 (이 Mac) | 49 passed, 2 skipped |
| B `pack_c_analysis.py` | PASS, 묶음 CSV 2개 해시 = C Gold 해시 |
| 일별 analysis: 20종목 전체 구간 | 17,440/17,440행, 1,587,040셀, **값 차이 0**, 표기 차이 135,396셀 |
| 보고서 analysis: 종목별 재무 조회 | 320/320행, 17,280셀, 값·표기 차이 0 |
| 기준일 비교 `as_of=2026-06-30` | 20/20종목, 값 차이 0, 표기 차이 160셀 |
| 다운로드 `g_fin_rpt_analysis.csv` | 바이트 해시 일치 |
| 다운로드 `g_stock_daily_analysis.csv` | 값 일치, **바이트 해시 불일치** (아래 1번) |

증빙: [`analysis/evidence/s4_api_check.json`](../../analysis/evidence/s4_api_check.json) — 위 실행 명령과 같은 `--gold build/s4-c-review/analysis`로 생성. 기준은 `review/s4-c-v1` HEAD `9861f59` + `verify_api` 수정(생성 당시 작업 트리, 이후 같은 내용으로 커밋). API는 `--analysis-dir build/s4-qa/c_api_artifact`로 띄웠고, 이 묶음은 `build/s4-c-review/c_api_artifact`와 CSV 2개·manifest 해시가 같다(manifest `5e85c1ad…`).

검사 도구 음성 대조(같은 API, 결과 `build/s4-dev2/`, 저장소 안 `build/`(git 제외) 로컬 산출물):

| Gold 변형 | 기대 | 결과 |
|---|---|---|
| `build/s4-qa2/gold_only_stock` (일별에 999999 1행 추가) | JSON 생성, daily FAIL | daily FAIL `missing_rows` `999999/2022-12-01`, compare FAIL `missing_rows` `999999`, 보고서 PASS |
| `build/s4-qa2/gold_dup` (일별 17,441행, 1행 중복) | daily FAIL | daily FAIL `gold_duplicate_key_count` 1 (`000660/2022-12-08`), `rows_gold` 17441 |
| `build/s4-qa/tampered` (마지막 자리 1 변경) | FAIL | daily·비교 `excess_20d_rt`, 보고서 `rev_yoy_rt` 각 `value_diff` 1, FAIL |
| `build/s4-qa/tampered_null` (0 ↔ 빈칸 교체) | FAIL | daily `close_rtn_rt`·보고서 `custom_map_cnt` 각 `value_diff` 1, FAIL (비교 PASS) |
| `build/s4-qa/tampered_droprow` (행 삭제 + 일별 `calc_ver` 컬럼 삭제) | FAIL | daily `extra_row` 1·`extra_columns` `calc_ver` 17440, 보고서 `extra_row` 1, 비교 `extra_columns` `calc_ver` 20, FAIL |
| API 중지 상태 (연결 거부) | JSON 생성, FAIL | 전 검사 FAIL, `errors`에 연결 거부 기록 |

## G05 대표 사례 (C Gold = API = A 대조값)

005930 삼성전자 / 기준일 2026-06-30 / 보고서 `report_76a18cf53ffa7baf9975a0d8` (2025 사업보고서 `11011`, CFS, `rcept_no 20260310002820`, 공시일 2026-03-10, 경과 112일) / 입력 `03_C_integration_20261014` / 계산 `c-gold-0.1.0`.

| 필드 | 값 | 상태 |
|---|---|---|
| rev_ytd_amt / rev_prior_ytd_amt | 333605938000000 / 300870903000000 원 | |
| rev_yoy_rt | 0.10880093 | OK |
| op_prft_ytd_amt / op_prft_delta_amt | 43601051000000 / 10875090000000 원 | PROFIT_CONTINUES |
| op_cf_ytd_amt / op_cf_sales_rt / op_cf_yoy_rt | 85315148000000 원 / 0.25573630 / 0.16897895 | OK |
| event_excess_rt | 0.32769823 | OK |
| excess_20d_rt | -0.02648179 | OK |
| frgn_flow_20d_rt / inst_flow_20d_rt / indv_flow_20d_rt | -0.06459243 / 0.00119083 / 0.06096100 | OK |
| frgn_net_20d_qty | -76545220 주 | OK |
| joint_improve_yn | N | OK |

A의 PR #5 기록(매출 333605938000000원, YoY 0.10880093, 공시 후 초과성과 0.32769823, 외국인 20관측 비율 -0.06459243, joint_improve=N)과 B의 S4 §6 기대값과 모두 일치한다.

## 합의가 필요한 것 (값 오류 아님)

1. **원천 통과 컬럼의 소수 자릿수 표기.** API는 B가 묶음 manifest의 SQL 타입대로 소수 자릿수를 채운다(`tz_api/analysis.py` DECIMAL 처리). C CSV는 원천에서 그대로 옮긴 8개 컬럼을 자릿수 없이 쓴다. 예: `close_prc` `333000` ↔ `333000.0000`, `frgn_hold_rt` `0.5006` ↔ `0.50060000`. 대상: `open_prc`·`high_prc`·`low_prc`·`close_prc`·`idx_close_prc`(DECIMAL(18,4)), `frgn_hold_rt`·`cfd_buy_bal_rt`(DECIMAL(12,8)), `frgn_hold_change_20d_rt`(DECIMAL(18,8)). C가 직접 계산한 비율은 이미 8자리라 차이 없음.
   - 결과: `/exports/analysis/g_stock_daily_analysis.csv`가 C 원본·manifest 해시(`a094a995…`)와 바이트가 다르다(값은 전량 동일). B 기록 §7의 "신규 C 다운로드 CSV 대조 PASS"는 값 대조로 읽어야 한다.
   - 선택지: (가) C가 다음 계산 버전에서 통과 컬럼을 선언 자릿수로 출력(해시 변경·재전달) / (나) B가 다운로드는 원본 바이트 그대로 제공 / (다) 현행 유지하고 "값 동일·표기 정규화"를 계약에 명시.
2. **입력 버전 표기 차이.** 이 Mac의 `input_version`은 `handoff-sha256:89e81d3d549f6ea0`, B 기록은 `4d0ed112f2cc1418`. 이 값은 `data/handoff_manifest.json` 파일 해시이며, 이 저장소에서는 LF(`git ls-files --eol`: `i/lf w/lf`)이고 `check_handoff.py` 75파일 PASS. B PC가 Windows 체크아웃에서 CRLF로 바뀐 것으로 **추정**되며 확인 필요. 같은 데이터에 PC마다 다른 버전 문자열이 나오면 G05 대조 시 혼동되므로 줄바꿈 정규화 해시를 권장.

## 미실행·남은 일

- MySQL 경로(`--backend mysql`)와 신규 C 2테이블 MySQL 적재·SQL 대조(C12/G04): 이 Mac에 B DB 없음, B 실행 결과 필요.
- Delta 경로 API(`--backend delta`): 이 저장소에 Delta 실물 없음.
- A 화면 연결(PR #5)과 S5 공동 G05: A·B 실제 환경 필요.
- PR #4(S3) B 정식 `review/s3-b-v1` 수신 확인 대기.
- `verify_api`는 결과가 FAIL이어도 종료 코드 0으로 끝난다. 자동화에서 판정하려면 결과 JSON의 `overall`을 읽어야 한다.
- 404는 상태 코드만 보고 "그 종목 행 없음"으로 처리한다(B 오류 코드 `STOCK_NOT_FOUND` 여부는 확인하지 않음). 잘못된 경로의 404도 행 없음으로 읽히지만, 그 종목에 Gold 행이 있으면 누락으로 잡혀 FAIL이므로 거짓 PASS는 아니다. 단, `/stocks`에는 있는데 404이고 Gold 행도 0인 종목은 PASS로 끝난다(`api_not_found_stocks`에만 기록) — 한계, 다음 회차 과제.
- `verify_api` 수정·테스트·증빙·이 문서는 `9861f59` 다음 커밋으로 `review/s4-c-v1`에 반영하고 원격에 push, 결과 요약을 PR #6 코멘트로 남김. merge·main 반영은 미실행.
