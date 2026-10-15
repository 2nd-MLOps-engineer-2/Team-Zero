# S5 A·B·C 통합 회귀검사 — 2026-10-15

## 현재 판정

고정 제공 데이터 기반 C 계산 → B API 1.1 → A 화면/CSV 통합 검증 PASS. **통합 PR #10을 원격 integration에 병합 완료했다.** 기능 병합 SHA `81731cd1fafcc9c8604a95e401538295aa3ce449`, 검증 소스 `fb74c253407fb124e3f4e6f04ba83880995374f3`. GitHub frontend 및 A B C integration checks 모두 PASS. PR #4/#5/#6도 포함 커밋이 integration에 도달해 병합 완료 상태가 됐다. C #7/#8/#9는 원래 review/s4-c-v1에도 각각 병합 완료. main 반영 및 Bronze/MySQL 전체 재현 완료는 별도이며 이번 결과로 대신하지 않는다.

## 포함 이력

- A 기존 HEAD `2f215546aafb19ab1626109816bbaaae9b13d8eb`와 S4 연결 커밋 `00b8fba` 보존. PR #5 전달 브랜치에 A 변경을 별도로 올린다.
- B PR #6 `9f78cccd208d750cf2726ab11e85a0a6218b3bba` (API 1.1.0).
- C PR #4 `6a61b132f54bf6a2553ad323e57e73b1cda09e65`, 독립 API 검증 `37e54515b340f6000ef523a788ca3a05a4a5a1e8`.
- C 검증 수정: #7 `4877ff3d7aa2286f9b0287dc8196beb13e5b268b`, #8 `beb1f2c76ed5f550c7947dc37dc5fce6a0a9846a`, #9 `35d85f406999d4bcaf2ec52473a56b3c4dff6428`.
- 모두 A의 `review/s4-a-v1` 위에서 정상 merge. 실행 코드 충돌 없음. 인수인계/진행 문서 충돌은 양쪽 이력을 보존하고 최신 상태를 이 문서에서 명시했다. 강제 push·원본 변경 없음.

## 회귀검사 결과

| 범위 | 결과 |
|---|---|
| 고정 인계본 | 75파일 무결성 PASS |
| B API pytest | 49 PASS, 2 SKIP (기존 Delta/MySQL 실행 카탈로그 미보유) |
| B 저장 안전성 | 6 PASS (격리된 테스트/모의 DB, 실제 MySQL 검사 아님) |
| C unittest | 49 PASS |
| C 실제 재계산 | 320 재무 + 17,440 일별행, Silver/Gold 규칙 PASS |
| C 독립 API 전량 비교 | daily/financial/compare/export 두 종류 PASS, 실제 값 차이 0 |
| C 신규 Delta 저장 | 2 Gold, version 0, 17,760행, 실제 _delta_log/Parquet 및 재조회 해시 검증 |
| A unit / build / Chromium | 16 PASS / PASS / 16 PASS (모두 통합 서버로 실행) |

C 결과는 `build/s5-analysis`, API 패키지는 `build/s5-c-api-artifact`, 독립 대조 결과는 `build/s5-validation/c-api-check.json`이다. 기존 ZIP 임시 runtime 대신 병합된 `backend/service/run.py`를 실제로 실행했다. 데이터 최종일 2026-06-30, 20종목, 계산 c-gold-0.1.0, C 산출물 b55ee9b1… 유지.

## 통합 중 발견·수정한 문제

1. Windows cp949 환경에서 C CLI 테스트가 UTF-8 결과 JSON을 읽지 못함: 읽기 인코딩을 UTF-8로 명시. CLI 실패 종료코드 검증은 그대로 유지.
2. C CSV 수출 검사가 전체 파일 해시만 비교해, B의 계약된 소수 자릿수 표준화를 값 오류로 판정함. 예: 100 → 100.0000. API JSON 전량 값 비교는 이미 PASS였음. 수출 CSV도 기존 C 스키마와 Tally로 양방향 행/키/컬럼/중복/값을 검사한다. 숫자형 선언 컬럼만 Decimal 동등성을 인정하고 식별자 선행 0은 정확히 비교한다. 파일 SHA 및 byte_identical=false를 결과에 남긴다. 실제 값 차이·코드 변경·행 누락/중복·잘못된 CSV는 실패하는 회귀검사 추가.

B/C의 업무 계산·원본·값을 바꾸지 않았으며, 대조 계약을 JSON과 CSV에서 일관되게 적용한 통합 수정이다. 상세 원본 byte hash를 보존해 바이트 일치로 오해하지 않도록 했다.

## 현재 로컬 실행

저장소 루트, API와 화면은 별도 터미널에서 실행한다.

```powershell
$env:TZ_CORS_ORIGINS='http://127.0.0.1:5173,http://127.0.0.1:4175'
& build/s4-api-venv/Scripts/python.exe -X utf8 backend/service/run.py --backend csv --project-root . --analysis-dir build/s5-c-api-artifact --port 8000
```

```powershell
$env:VITE_DATA_MODE='api'
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
npm --prefix apps/web run dev -- --port 5173 --strictPort
```

각 터미널 Ctrl+C로 해당 서버만 종료. 8001은 C 미연결 검사용으로 같은 API를 analysis-dir 없이 실행했다. 브라우저 검사에 S4_API_BASE_URL, S4_NO_C_API_URL, C_REVIEW_BUNDLE을 설정한다. 새 통합 CI `.github/workflows/integration.yml`은 별도 Python B/C 환경 설치부터 C 재계산·Delta 저장·실API·브라우저까지 자동 수행한다. 실제 MySQL 접속은 수행하지 않는다.

## 남은 전체 프로젝트 범위

B의 G04 문서에는 원본/Delta/MySQL·복원 검증 결과가 기록되어 있으나 해당 외부 원본·실행 카탈로그·DB 자격정보는 A 환경에 없다. 이번에는 C 신규 Delta만 실제 재검증했다. 기존 58테이블 MySQL·덤프 복원·전체 Bronze 재현을 A에서 검증했다고 주장하지 않는다. 검토 가능한 B 실행 증빙을 확인한 뒤 최종 main 승격 판단에 포함한다. integration 병합은 기능 통합이며 main의 전체 완료 표시는 아니다.


## 원격 최종 상태

- 통합 PR: https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/10 (merged)
- A·B·C 기능 PR #4/#5/#6: merged. C 검증 수정 PR #7/#8/#9: merged.
- GitHub 검증: frontend run 38691439071, A B C integration run 38691439244 모두 success.
- integration 기능 병합 SHA: `81731cd1fafcc9c8604a95e401538295aa3ce449`.
- main: 아직 변경하지 않음. integration→main 초안 PR을 준비해 남은 외부 증빙/전체 수용 범위를 검토한다.
- 작업 트리에 원본/비밀값/덤프 추가 없음. 추가 커밋은 이 최종 상태 기록이며 기능은 검증 소스와 동일하다.
