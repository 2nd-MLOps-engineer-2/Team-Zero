# S4 — C 수치 확인 (B API ↔ C Gold)

2026-10-15 / 수신 확인 C 김형준 / **C 수치 확인: 값 일치, 표기 2건 합의 필요.** [S4 B 전달 기록](S4-B-to-A.md) · [진행표](../integration-status.md) · [절차](../integration-workflow.md).

## 확인 대상과 브랜치

| 항목 | 실제 값 |
|---|---|
| C 작업 브랜치·HEAD | `feature/c-gold-analysis` `81a5705` (미커밋 변경 없음, 미push 6커밋은 S3 작업·문서) |
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

`analysis/verify_api.py`는 B의 `verify_s4.py`와 별개인 C 쪽 독립 대조 도구다. 값을 문자열로 비교하고, 다르면 Decimal 동일 여부로 **표기 차이**와 **값 차이**를 나눈다. CSV 빈칸 = API null.

## 결과

| 검사 | 결과 |
|---|---|
| C 테스트 (B 변경 merge 후) | 18/18 OK |
| C Gold 재생성 해시 | `g_fin_rpt_analysis` `4514982c…`, `g_stock_daily_analysis` `a094a995…` — S3 전달본과 동일 |
| B 자동검사 (이 Mac) | 49 passed, 2 skipped |
| B `pack_c_analysis.py` | PASS, 묶음 CSV 2개 해시 = C Gold 해시 |
| 일별 analysis: 20종목 전체 구간 | 17,440/17,440행, 1,587,040셀, **값 차이 0**, 표기 차이 135,396셀 |
| 보고서 analysis: 종목별 재무 조회 | 320/320행, 17,280셀, 값·표기 차이 0 |
| 기준일 비교 `as_of=2026-06-30` | 20/20종목, 값 차이 0, 표기 차이 160셀 |
| 다운로드 `g_fin_rpt_analysis.csv` | 바이트 해시 일치 |
| 다운로드 `g_stock_daily_analysis.csv` | 값 일치, **바이트 해시 불일치** (아래 1번) |

증빙: [`analysis/evidence/s4_api_check.json`](../../analysis/evidence/s4_api_check.json).

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
- commit은 `review/s4-c-v1` 로컬에만, push·PR 코멘트·merge는 미실행.
