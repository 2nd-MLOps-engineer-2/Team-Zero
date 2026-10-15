# S4 — B API를 A 화면 작업에 전달

## S4 수신 검증 — 2026-10-15 최신

**판정: 전달 ZIP의 API 1.1.0 + C 산출물로 A 실제 화면 연결·수치 검증 완료. Git 고정 전달본 수신 완료 및 integration/main 반영은 미완료.** 아래 이전 기록의 API 미확인 상태는 이 범위에서 갱신한다.

- A 기준 HEAD: `2f215546aafb19ab1626109816bbaaae9b13d8eb`, 로컬 `review/s4-a-v1`. A 기존 변경 보존. 이번 연결 변경은 미커밋이며 PR #5에 아직 반영하지 않음.
- B 원격 API 1.0.0 기능 SHA: `ba2aaf1008d52dc96d983f61cae40d8a628366a2`, ZIP 기준 HEAD: `3bd7a2583305ee38a9755faa5660ab463b9896ca`. **ZIP의 1.1.0 추가 변경은 커밋 SHA가 없음**. 원격 PR #6의 코드와 동일하다고 간주하지 않음.
- 수신 파일 `S4-B-to-A.zip` SHA256: `8954983748c028af92ebfe037a39edaa4addbc7a02aebcb5a431b11c6f437309`. 내부 실제 이름은 `B_S4_API_local_bundle.zip`이며 안내문의 `B_S4_API_Handoff_v2.zip`과 다름.
- manifest 32파일의 크기·SHA256 전부 일치. 변경 전 해시는 26개 Git blob 기준, 문서 6개는 Windows CRLF 체크아웃 기준으로 일치. `build/s4-received-20261015/receipt-verification.json`, `bundle.diff`에 기록.
- 미커밋 B 코드를 A 저장소의 소유 경로에 덮어쓰거나 병합하지 않음. baseline의 backend/service 및 medallion 의존 코드를 `build/s4-received-20261015/runtime`에 추출하고 전달 서비스 변경만 겹쳐 실행. runtime/data는 기존 data의 읽기 참조 junction. Git merge 검증은 B의 1.1 고정 SHA 전달 후 별도 수행해야 함.
- Python **3.12.15** 격리 환경(전달자의 3.12.14와 패치 버전 차이), B lockfile 39패키지 사용. Node 24.21.0, npm 11.19.0, Vite 8.3.4, Playwright 1.64.1.
- C 고정 코드 `fb1f802c88e2d5b275c737200aa392deac0e628b`에서 앞서 재현한 출력을 그대로 패키징. 계산 `c-gold-0.1.0`, 입력 `handoff-sha256:4d0ed112f2cc1418`, C 산출물 `c-artifact-sha256:b55ee9b1d38c84977dd39a29c9c8e9066fe3cbc43cdadc7fe1286e9de05e4d25`.

### 실제 수행 결과

| 검사 | 결과 |
|---|---|
| 고정 인계본 무결성 | 75파일 PASS, 원본 변경 없음 |
| B pytest | 49 PASS / 2 SKIP (로컬 Delta·MySQL 실행 카탈로그 없음) |
| B 실HTTP 검사 | C 연결 16 PASS, C 미연결 16 PASS (409 포함) |
| C→API 전체 값 | 재무 320행·17,280값 + 일별 17,440행·1,587,040값 PASS |
| A 단위 검사 | 16 PASS |
| A 빌드 | PASS |
| A Chromium 브라우저 | 16 PASS: 기존 11 + 실제 C 응답 1 + 실제 B/C 2 + C 미연결 실제 서버 중계 1 + 실제 API 소페이지 조립 1 (마지막 1개 별도 실행) |

처음 실행 중 baseline 문서 해시의 CRLF 차이로 준비 스크립트가 중단되어 runtime 의존 파일이 빠졌고 B 검사가 실패했다. 문서 해시를 CRLF 기준으로 확인하고 고정 baseline 의존 파일을 확보한 뒤 위 결과로 재검사했다. 또 비JSON HTTP 500 응답에서 상태코드가 보이지 않던 A 오류 처리를 수정해 기존 오류·재시도 검사를 통과했다. 성공 결과만 남기기 위해 실패를 생략하지 않는다.

검증 사례: 삼성전자 2026-06-30 매출 `333605938000000`, 영업이익 `43601051000000`, 순이익 `45206805000000`, 영업CF `85315148000000` 원. 매출 YoY `0.10880093`, 공시 후 초과성과 `0.32769823`, 동반 개선 `N`. 6월 가격 기준일 6/1, 마지막 종목/시장 기준값 `93.80281690`/`96.45099552`. API·화면·차트 CSV 일치. 6/6 요청은 실제 관측 6/5, 6/6 시작 차트는 6/8 기준. 공시 당일 제외, 247540의 4/16 수급 NULL·가격 유지, OFS 빈 결과, 404/422/409, 로딩/취소/재시도/500, 모바일 가로 넘침 없음 확인.

### A 변경과 남은 범위

- `apps/web/src/b-contract.js`: B 1.1 응답 및 중첩 C 분석을 표현용으로 매핑. 금액 문자열 보존, YTD만 선택, 업무 계산 없음. C 미연결은 판단 불가.
- `api.js`: 실제 query 이름·페이지 전체 수신·데이터/계산/산출물 버전 일치·시점 검증·오류 처리. `main.js`: 실제 관측일, 2022~2025, 품질 범위 구분, 서버 CSV 선택.
- 화면 CSV와 서버 CSV를 구분. 기존 Gold 일별/정규화 차트/재무 metric/C 전체 산출물 다운로드. 서버 CSV 전후 health로 C 산출물까지 버전 대조. 전체 C CSV는 종목·기간 필터 미적용을 명시.
- Bronze 원본 확보 완료로 표시하지 않음. 가격 출처 메타의 파일/행/버전만 표시하고 미확보 상태 유지. 성장률 분자는 API가 제공하지 않아 NULL, 분모는 제공된 PRIOR_YTD 원값.
- 품질 availability는 선택 날짜, 직접 이슈는 기업·보고서 전체, 전역 이슈는 별도 표시. 발견 시각이 없어 이슈를 날짜 필터된 것으로 설명하지 않음.
- A01~A10 중 실제 API 연결 및 M08/M09/M12/M13 표시·대사 보완. G05는 제공 CSV→C→B API→A 화면/CSV 구간 검증. M14/S5 전체의 Bronze·실제 DB/Delta 저장 대사나 팀 통합 완료를 주장하지 않음.
- 남은 B 요청: **이번 API 1.1.0 변경을 담은 브랜치·전체 SHA·PR**. 전달 후 A review에 실제 merge하여 재검사하고 A PR #5에 연결 변경을 반영할 수 있음. 새로운 Silver/Gold 파일은 요청할 필요 없음.

실행 방법은 `apps/web/README.md`의 S4 절을 따른다. 상세 증빙은 `build/s4-a-value-verification/s4_validation.json`, runtime/build/api_http의 두 검사 결과, `apps/web/test-results/s4-actual-desktop.png`·`s4-actual-mobile.png`에 있다.


**현재 상태: ZIP 기반 실제 API 연결 검증 완료 / API 1.1.0 고정 SHA 및 Git 통합 대기.** 상세 최신 결과를 먼저 확인한다. [전체 절차](../integration-workflow.md) · [진행표](../integration-status.md).

| 항목 | 현재 값 |
|---|---|
| 전달자 / 수신자 / 수치 확인 | B 설호현 / A 이어진 / C 김형준 |
| 관련 업무 | B09·A08~A10·G02·G05·M12·M13 |
| 전달 브랜치 예정명 | `handoff/s4-b-to-a-v1` — 준비 시 생성 |
| 전달 전체 SHA·PR·선행 integration SHA | 미등록 |
| A 수신 확인 브랜치 예정명 | `review/s4-a-v1` — A의 작업 HEAD에서 준비 시 생성 |
| 설치·시작·종료·검사 명령 / API 주소 | 미구현 |
| API·데이터·계산 버전 | 미등록 |

## B가 넘길 묶음

- [ ] 기업 목록·비교·일별·보고서·품질·근거·다운로드의 실제 지원 API와 미지원 범위.
- [ ] 계약·필터·단위·큰 금액 표현·NULL·오류·샘플 응답.
- [ ] 실제 실행법·버전·환경 예시·DB/데이터 준비·안전한 종료법.
- [ ] 실제 데이터와 합성 데이터 구분, 기준일·기간·종목 범위·출처.
- [ ] 실행 검사·결과·미실행·열린 이슈·고정 SHA·PR·다음 실행 명령.

## A가 합친 뒤 확인할 것

- [ ] A 작업·미커밋 변경을 보존하고 review 브랜치에 B의 고정 SHA를 정상 merge.
- [ ] 실제 API 시작·접속·필터·로딩·오류·빈 결과·NULL/0 구분 확인.
- [ ] 금액 원·수급 주·비율 %/%p·공시일·기간·검토/출처 표시 확인.
- [ ] 동일 종목·기준일의 API·화면·CSV 값을 대조하고 C의 근거 확인 연결.
- [ ] A의 화면 연결 수정과 B 계약 수정 요청을 각자 소유 경로로 구분.
- [ ] 결과·브라우저 증빙·두 역할 SHA·잔여 문제를 아래와 진행표에 기록.

## A·C 확인 결과

### 최신 A 독립 검증 — 재개 후

A 화면은 샘플 기반 구현 완료. npm test 10개·build·Chromium E2E 9개 PASS. API 모드는 모의 네트워크 응답과 HTTP 500/markup escape로 검사했으며 실제 B 서버 검사 아님. 이전 main.js/test 파일 부재로 인한 실패는 해소했다.

A는 feature/a-dashboard에서 최신 main `1971dcbdfae2e2d29d1bc77ef712e40256014b34`를 반영했고 선행 integration `b9b73a49bf169b17e3c324fcc9e51564d350b1ea`를 포함한다. A 변경은 미커밋 보존 중이다. B S4 고정 SHA·실행법이 없어 review/실제 merge는 미실행. 판정은 **실제 API 미확인** 유지. [A 로컬 전달 준비](S5-A-to-team.md)·[A 화면 제안](../../contracts/A-screen.md).

아래는 준비 단계 당시 기록이며 실패/미구현 상태는 위 최신 결과로 갱신한다.

확인 브랜치·SHA / 실행 명령·환경 / 실제 결과·증빙 / C 수치 대조 / 충돌·수정 요청 / 확인자·일시: **미등록**.

### A 사전 점검 — 2026-10-15 (실제 수신 검증 아님)

- A 이어진의 작업 브랜치 feature/a-dashboard. A HEAD 및 선행 integration `8af915fba1c40849b4cb80d7d8c2bd1768f674b7`.
- B 전달 브랜치·전체 SHA·PR·실행법 미등록이며 사용자가 별도 API/C 가이드도 없다고 확인함.
- A의 기존 작업은 미커밋 로컬 초안으로 보존. 실제 전달본이 없어 review 브랜치 생성/merge는 미실행. 충돌 없음.
- 상태: **미확인 / B 입력 대기**. 합성 fixture 생성 및 JS 구문 확인은 실제 API 연결·수신 확인 증거가 아님.
- A 초안 빌드는 src/main.js 미작성, npm test는 tests/unit.test.js 미작성으로 실패. 실제 UI·브라우저 검증은 수행하지 않음.
- 다음 수신 시 필터·오류·빈 목록·NULL/0·큰 금액·공시일 경계·기간·출처·CSV를 확인하고 C 기대값과 대조. B 자체 검사를 A 확인으로 대신하지 않음.
- 요청/실행 환경/제한: [A→B](A-to-B.md), [A→C](A-to-C.md), [A 진행 기록](../roles/A.md).
- 이번에는 기준 점검·준비만 수행. 실제 전달 브랜치·기능 SHA·PR·수신 완료·integration 병합 기록은 생성하지 않음.

## integration 병합 결과

PR·병합 SHA·다음 역할이 반영할 기준 / 남은 일: **미등록**. 체크만으로 서비스 전체 완료를 주장하지 않는다.
