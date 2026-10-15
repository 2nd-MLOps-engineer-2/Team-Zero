# A 진행 기록 — 이어진 / 프론트엔드

상태: **2026-10-15 A 합성 샘플 화면 구현·빌드·브라우저 검증 완료. 실제 B API 연결·C 의미 합의·G05 대사 대기.** [프롬프트](../../prompts/A_frontend.md) · [체크북](../workbook.md).

## 최신 구현 결과 — 사용자 “시작” 요청 이후

기존 준비 중단은 사용자의 재개 요청으로 해제되었다. 아래 역사 기록의 빌드/테스트 실패 및 미구현 상태는 이 최신 결과로 대체한다. A 기능의 합성 검증과 실제 서비스 전체 완료를 구분한다.

### 브랜치·최신 기준

- 작업: feature/a-dashboard. 최초 HEAD `8af915fba1c40849b4cb80d7d8c2bd1768f674b7`.
- 작업 중 원격 변경을 발견하여 fetch 후 origin/main을 fast-forward 반영. 현재 HEAD/main `1971dcbdfae2e2d29d1bc77ef712e40256014b34`, 선행 origin/integration `b9b73a49bf169b17e3c324fcc9e51564d350b1ea`(현재 HEAD에 포함).
- A의 미커밋 코드·문서 모두 보존, 충돌 없음. backend/ 및 C 문서는 원격 기준을 그대로 받았으며 변경/실행하지 않음. B S4 전달본·G03는 여전히 미등록.
- A 기능은 미커밋 로컬 변경. 위 HEAD를 기능 전달 SHA로 표시하지 않는다. commit·push·PR·remote merge 없음.

### 구현 및 체크북 증빙

| 범위 | 현재 결과 | 증빙 / 실제 연결 잔여 |
|---|---|---|
| A01·A02 | 비교→상세→근거 동선, 시장/기업/기간/보고서/연결 필터, 로딩/오류/재시도/빈 결과, 취소·마지막 요청 반영 | src/main.js, tests/browser; 샘플 검증 |
| A03~A07 | 4개 재무 카드, 가격/시장·실적/현금·수급/보유율 차트, 공시 구간/분자/분모/판단 불가 | src/charts.js, fixtures/sample.json; C 실제 차트/분류 확인 대기 |
| A08 | 단일 API 어댑터, 계약/필터/공시 시점/응답 버전 검사, 15초 timeout, 실제 모드에서 샘플 fallback 없음 | src/api.js; B API 모의 네트워크 검사 통과, 실제 서버는 대기 |
| A09 | NULL/0·미연결·검토·격리·계산 불가, Bronze 미확보·출처/버전 노출 | main.js/format.js; 실제 lineage B/C 제공 대기 |
| A10 | 정확한 금액/CSV 대조, 데스크톱 1440·모바일 390, 오류·요청 경합 검사 | 단위 10 + Chromium E2E 9 통과, 캡처 test-results/ |
| M08 | 부재 사유/상태와 차트 결측 단절 구현 | 실제 부재 키 대사는 B/C 대기 |
| M09 | A 화면 계약 제안 작성 | contracts/A-screen.md, B/C 승인 아님 |
| M12 | 실제/합성 모드 분리 및 모의 API 연결 검증 | B 실제 API/S4 SHA·PR 미등록 |
| M13 | 출처/품질/근거/CSV 구현 | 합성 상태 예시, 원본을 만들어 채우지 않음 |
| M14 | 같은 합성 사례 화면/응답/CSV 원값 확인·캡처 | 실제 원본→Gold→DB→API 대사 미완료 |

합성 fixture 성장률·분자/분모 및 모든 종목의 최초 기준값 100을 일관되게 수정했다. 금융 업무 계산은 A UI에서 수행하지 않는다. 합성 기준일/기간 한계는 화면/README/계약에 명시했다. 보고서 필터는 재무 영역, 비교·근거는 기준일 최근 공시 기준이다.

### 실제 검증과 실행

환경 Node 24.21.0 / npm 11.19.0 / Python 3.13.15 / Vite 8.3.4 / Playwright 1.64.1 / Chromium 156.0.8078.4.

apps/web에서 `npm test`: **10/10 PASS**, `npm run build`: **PASS**, `npm run test:e2e`: **9/9 PASS**. 최신 기능 변경 후 전체 재검사 통과. 브라우저 JS 오류 0(정상 desktop case), 모바일 문서 가로 넘침 없음. 금액·NULL/0·필터·공시 당일 제외·CSV·취소·오류 복구·API 모드 500 및 markup escape 포함.

`npm run dev -- --port 5173 --strictPort` → http://127.0.0.1:5173. 종료 Ctrl+C. 신규 설치는 npm ci, E2E 브라우저 설치는 npx playwright install chromium. [실행 README](../../apps/web/README.md).

원본 75파일 무결성 및 루트 도구 테스트를 최종 재확인한다. 실제 B API·MySQL·Delta·신규 Gold 실행과 C 지표 검증은 하지 않음. 기존 203 PASS와 이번 A 검사 결과는 별개다.

### 인수인계

[S5 A 로컬 전달 준비](../handoffs/S5-A-to-team.md), [A 화면 계약](../../contracts/A-screen.md), [A→B](../handoffs/A-to-B.md), [A→C](../handoffs/A-to-C.md). B/C 전달 SHA·실제 계약이 생기면 A 작업 보존 후 자기 HEAD에서 별도 S4 review를 만들어 확인한다. 현재 원격 전달·수신 확인·S5 전체 완료로 표시하지 않는다.

## 이전 준비 단계 기록 (역사 기록, 아래 실패는 위 재검증으로 해소)

단계 책임: S0 계약 확인, S3 차트 의미 확인, **S4 B의 API를 A 작업의 review 브랜치에 합쳐 확인·보고**, S5 화면 전달·통합 검사. [진행표](../integration-status.md)와 [S4 기록](../handoffs/S4-B-to-A.md)에 전달 SHA·A review HEAD·실행 결과를 기록한다.

필수 보완: [M08·M09·M12·M13·M14 및 A 역할](../missing-work.md). Bronze 출처/미확보, Silver 검토/NULL, Gold 계산/근거 상태의 화면·계약·예제·검사를 추가한다. 항목별 상태·증빙·의존성을 아래 기록에 추가한다. 현재 모두 미완료다.

구현 경로: `apps/web/`. 앞선 구현 요청으로 환경·합성 fixture·API 접근 초안을 만들던 중, 사용자의 후속 안내가 이번 범위를 기준 반영·점검·준비까지로 제한했다. 이후 기능 구현은 중단하고 초안을 보존했다. 아직 실행 가능한 화면은 없다.

데이터 준비: `data/03_C_integration_20261014/`에 실제 `s_stock`·Gold·사전이 포함되어 있다. [데이터 안내](../data-guide.md)에서 단위·NULL·기간을 확인한다. 데이터 업로드와 A01~A10의 완료는 별개다.

| 작업 ID | 변경·증빙 경로 | 실행 명령·결과 | 기준 커밋/데이터 버전 | 남은 의존성 |
|---|---|---|---|---|
| A01~A10 | 아래 항목별 기록 | 구문/자료 검사와 실패 구분 | 아래 기준 SHA | B API·C 차트 계약 |

실행 방법과 실제 API/합성 fixture 사용 여부, G02·G03·G05 handoff를 구현 후 기록한다.

## 이번 기준 반영과 보존

- 역할: A 이어진. 저장소 `https://github.com/2nd-MLOps-engineer-2/Team-Zero`.
- 경로 `C:\Users\Playdata\Desktop\Team-Zero`. ZIP은 백업으로 유지하고 기존 저장소 위에 풀지 않음.
- 시작은 변경 없는 `main`. `feature/a-dashboard`를 생성하여 작업.
- 시작/현재 HEAD 및 origin/main·origin/integration: `8af915fba1c40849b4cb80d7d8c2bd1768f674b7`.
- `git fetch origin` 성공. 위 기준 SHA의 양쪽 원격 브랜치 포함 검사(`git merge-base --is-ancestor`) 각각 exit 0.
- 실제 feature 브랜치에서 `git merge --ff-only origin/main`, `git merge --ff-only origin/integration`: 모두 `Already up to date.`. 추가 커밋·충돌 없음.
- 선행 integration은 위 전체 SHA. 초안과 문서는 미커밋 로컬 파일로 보존. reset·stash·삭제·공유 이력 변경 없음.
- 공통 문서·A 프롬프트·사전·S4 기록 확인. 별도 하위 AGENTS 없음.
- commit·push·PR 생성/병합·main 수정·빈 handoff/review 생성 없음. 현재 HEAD는 기능 전달 SHA가 아님.

## 환경과 보존한 초안

Windows PowerShell / Node 24.21.0 / npm 11.19.0 / Python 3.13.15 / Vite 8.3.4 / Playwright test 1.64.1.

`apps/web`에서 `npm install --save-dev --save-exact vite @playwright/test` 실행: 18패키지 설치, 설치 당시 npm audit 0 vulnerabilities. package-lock.json 보존. 다른 환경의 재현용 명령은 `npm ci`이며 이번에는 별도로 재실행하지 않았다. B 공통 실행 환경과는 별도 로컬 초안이다.

| 파일 | 내용·현재 한계 |
|---|---|
| apps/web/package.json, package-lock.json, .gitignore, .env.example | 의존성·환경 초안. 실행 스크립트 정의와 기능 완료는 다름 |
| apps/web/index.html | src/main.js를 참조하지만 해당 파일은 아직 없음 |
| apps/web/src/api.js | 합성/실제 모드 및 제안 응답 검사. 실제 B API 미연결 |
| apps/web/src/format.js | 큰 정수·비율 표시·CSV 직렬화 초안, 단위 검증 전 |
| apps/web/scripts/generate-fixture.py, src/fixtures/sample.json | s_stock 식별자 20개만 재사용, 분석값은 합성 |

`npm run dev`·`npm run preview`는 정상 화면 시작 명령으로 검증되지 않았다. 화면 진입 파일과 빌드 산출물이 없어 현재 시연 불가. 서비스 프로세스는 시작하지 않았다.

## A 업무별 분류

| ID | 분류 | 확인한 증빙·다음 개발 |
|---|---|---|
| A01 | 미구현 | HTML 틀만 존재. 비교→상세→근거 화면/동선 구현 |
| A02 | 미구현 / 증빙 확인 필요 | 합성 조회 필터 함수 초안. 기업·기간·보고서 UI, 로딩/오류/빈 결과·요청 경합 검사 필요 |
| A03 | 미구현 | 정수 문자열 fixture/표시 함수. 4개 카드·기간·NULL/0 UI 및 검사 필요 |
| A04 | 미구현 / 입력·합의 필요 | 기준값 100 합성 필드. C 시계열·기준일·축·범례 합의 필요 |
| A05 | 미구현 / 입력·합의 필요 | 연간 CFS YTD 샘플. 같은 기간 실적/현금 비교 및 검토 표시 필요 |
| A06 | 미구현 | 수급·보유율 샘플만 존재. 주·원·% 구분과 TOP_LEVEL UI 필요 |
| A07 | 미구현 / 입력·합의 필요 | 분류/근거 독립 UI 값. C의 일관된 근거·공시 구간 필요 |
| A08 | 증빙 확인 필요 / 문서·계약 미작성 | api.js 제안 초안. B 실제 계약/연결·오류/취소/날짜 검사 필요 |
| A09 | 미구현 | Bronze 미확보·Silver 검토/격리·Gold 계산 불가 샘플. 출처/사유/버전 UI 필요 |
| A10 | 미구현 | 테스트·브라우저 화면 없음. 큰 금액·좁은 화면·필터·다운로드 대조 필요 |
| M08 | 이미 포함 / 입력·합의 필요 | 데이터 안내의 부재 정책 재사용. C/B 키·기간별 상태 연결 필요 |
| M09 | 문서·계약 미작성 / 입력·합의 필요 | contracts/README만 있음. B API·C 분석/시각화 명세 필요 |
| M12 | 입력·합의 필요 / 증빙 확인 필요 | 접근 초안만 존재. B 실제 전달본을 A review에서 연결 검사 필요 |
| M13 | 미구현 | 출처 fixture만 존재. 레이어별 상태/다운로드 화면 필요 |
| M14 | 미구현 / 입력·합의 필요 | 공통 실제 사례·캡처 없음. B/C 기대값과 화면/API/CSV 대조 필요 |

체크북은 완료 체크하지 않았다. A→B/C 요청은 [A-to-B](../handoffs/A-to-B.md), [A-to-C](../handoffs/A-to-C.md)에 구체화했다.

## 실제 검사 결과와 데이터

| 명령·위치 | 결과 |
|---|---|
| 루트: python scripts/check_handoff.py | PASS: 75파일 해시/크기 및 33 CSV 헤더/건수 |
| 루트: python -m unittest discover -s scripts/tests -v | 2/2 PASS |
| apps/web: python scripts/generate-fixture.py | 식별자 20개 합성 fixture 생성 성공 |
| apps/web: node --check src/api.js 및 node --check src/format.js | 구문 검사 PASS, 기능 검사 아님 |
| apps/web: npm run build | **실패**: /src/main.js 없음 |
| apps/web: npm test | **실패**: tests/unit.test.js 없음 |
| 루트: git diff -- data/03_C_integration_20261014 | 출력 없음, 원본 변경 없음 |

Silver 17개 371,437행·Gold 2개·사전/DDL/ERD·기존 코드/검증 기록 포함. s_stock/Gold 2개의 실제 헤더·첫 행과 사전 헤더를 확인했다. Bronze 입력 18개·공시 ZIP·덤프·Delta는 미포함. 기존 203 PASS는 과거 기록이며 재실행하지 않았다. Silver/Gold 재업로드 요청 없음. 기존 파이프라인 실행 없음.

실제 API·MySQL·Delta·신규 Gold 대사·브라우저/E2E는 미실행: 구현/전달본이 없고 이번 범위는 준비까지. 빌드·테스트 실패를 준비 완료 화면으로 표현하지 않는다.

## 다음 개발에서 먼저 해결할 초안 한계

- 샘플 비교/근거는 2026-06-30, 일별은 6개 관측점, 보고서는 2024/2025 연간 CFS YTD만 포함. 전체 날짜/분기/별도 지원 아님.
- 일부 합성 성장률과 근거 분자/분모가 독립 값으로 일치하지 않음. 첫 기준값 100도 종목별 오프셋이 있음. 시각화·대사 전에 fixture 의미 일관성과 검사를 보완해야 함.
- a-proposal-1은 B와 미합의. 응답 검사는 기본 자료형 중심이며 날짜·기간·출처 의미 검증 필요. endpoint별 meta가 다르면 현재 일치 검사에서 거절될 수 있으므로 snapshot 필드 합의 필요.
- CSV는 직렬화 초안. 다운로드 UI·B export 계약·스프레드시트 해석/정밀도/문자열 보안 검사 필요.
- 화면 src/main.js/스타일·단위/E2E 검사 추가가 첫 구현 작업. C 지표를 A에서 다시 계산하지 않음.

## 단계·다음 전달

현재 S0 계약 요청 준비, S3 의미 검토 대기, S4 미수신, S5 미착수. 사용자도 B API/C 가이드가 아직 없다고 확인했다.

B가 검사된 handoff 브랜치·전체 SHA·PR·환경/실행/종료법을 S4에 등록하면, A의 작업을 보존한 HEAD에서 review/s4-a-v1을 생성하여 고정 SHA를 merge한다. 정상/NULL/0/빈 결과/오류/공시 당일/큰 금액/다운로드 검사 후 S4에 결과를 기록한다. B 검사만으로 A 확인 완료 처리하지 않는다. 이번에는 상대 메시지·수신 확인·통합 완료를 수행하지 않았다.
