# S5 — A 화면 로컬 전달 준비 v1

## PR 준비 갱신

- A 원본 기능 커밋: `ab2264a29bc788214d611042e45ad923315b6978` (feature/a-dashboard).
- integration 기반 검사한 전달 기능 커밋: `8061fce53fc4cc4076e226f9419380c24e8ea9f9` (handoff/s5-a-to-team-v1). 해당 커밋에서 단위 10/10·build·브라우저 9/9 재검증 PASS.
- 팀 저장소 쓰기 권한이 없는 jobless-fish 계정의 origin push는 HTTP 403으로 실패. 공개 저장소의 개인 포크 `jobless-fish/Team-Zero`에 전달 브랜치를 게시하고 upstream integration 대상 초안 PR을 만든다. origin 권한·보호 설정 변경 없음.
- 이 갱신은 전달 메타데이터만 변경하며 최종 PR head는 위 기능 커밋을 포함한다. 실제 API/C 확인·수신 검증·병합은 대기.

사용자의 PR 요청에 따라 A 변경을 커밋하고 integration 대상 초안 PR로 전달한다. 기존 feature/a-dashboard는 main 기준 작업으로 보존하고, integration에서 handoff/s5-a-to-team-v1을 만들어 A 커밋만 적용한다. 따라서 main에만 있는 B 백엔드 커밋은 이 PR에 섞이지 않는다. 최종 전달 SHA와 PR URL은 실제 GitHub PR의 head를 기준으로 확인한다. 아래 미커밋/원격 미전달 설명은 PR 요청 전 검사 시점의 기록이며, 실제 API·수신 확인·통합 완료 대기 상태는 유지한다.

2026-10-15 / A 이어진 → B 설호현·C 김형준 / **합성 화면 검증 완료, 실제 통합·원격 전달 전**.

| 항목 | 값 |
|---|---|
| 체크북 | A01~A10 / M08·M09·M12·M13·M14 / G02·G03·G05 |
| 작업 브랜치 | feature/a-dashboard |
| 반영한 main/현재 HEAD | 1971dcbdfae2e2d29d1bc77ef712e40256014b34 |
| 선행 integration | b9b73a49bf169b17e3c324fcc9e51564d350b1ea |
| A 기능 전달 SHA·handoff·PR | 없음: 미커밋 로컬 변경. 위 HEAD는 기능 전달 SHA가 아님 |
| 데이터/계약/계산 버전 | 고정 03_C_integration_20261014의 식별자만 / a-proposal-1 제안 / synthetic-ui-v1 |
| 수신 확인·integration/main 기능 반영 | 미실행 |

## 실행 및 검사

apps/web에서 npm ci → npm run dev -- --port 5173 --strictPort. http://127.0.0.1:5173, Ctrl+C 종료. 기본 합성 모드는 DB·비밀값 없이 실행한다. Node 24.21.0/npm 11.19.0/Vite 8.3.4/Playwright 1.64.1에서 확인.

- npm test: 10/10 PASS. 정밀도·NULL/0·CSV·fixture 성장률/기준값·필터/공시일·오류/빈 결과·차트 결측·취소.
- npm run build: PASS.
- npx playwright install chromium 후 npm run test:e2e: Chromium 9/9 PASS. 정상/필터/NULL/0/오류 복구/빈 결과/다운로드/390px 화면/기간 오류/빠른 변경/모의 API 포함.
- 캡처: apps/web/test-results/desktop.png, mobile.png(재실행 생성, gitignore). 화면 JS 오류 0 및 모바일 전체 문서 가로 넘침 없음 확인.
- 같은 합성 사례 000660 / 2026-06-30 / SAMPLE-000660-2025: 화면 매출 11,200,000,000,000원, CSV value 11200000000000. NULL 수급과 합성·버전 메타 보존.

## 포함 변경

apps/web/ 실행·UI·차트·표시·API·CSV·fixture 생성·lockfile·단위/브라우저 검사·README, contracts/A-screen.md, docs/roles/A.md, A-to-B/A-to-C/S4/S5 문서 및 integration-status.md. 소유 외 B/C 구현 및 고정 데이터는 수정하지 않음.

## 수신 시 확인할 것

B 실제 API 계약·고정 SHA·PR·환경/실행법과 C 시각화/분류·기대값을 먼저 제공한다. A 작업을 보존한 HEAD에서 review/s4-a-v1을 만들고 B SHA를 merge한 뒤 실제 API 모드로 정상/빈/오류/NULL/0/큰 금액/공시 당일/필터/품질/CSV 대조를 한다. 계약 차이는 A-screen 제안을 기준으로 협의하고 A가 화면 어댑터를 수정한다.

현재 UI 차트와 비교·CSV는 합성 증거다. B 코드가 main에 있다는 이유만으로 API·Delta·MySQL 수신 검증을 완료 처리하지 않는다. 실제 출처·계산값 대사·C 의미 검토·G05 캡처 및 F07은 잔여다. commit/push/PR·상대 통보는 이번 실행에 포함하지 않았다.
