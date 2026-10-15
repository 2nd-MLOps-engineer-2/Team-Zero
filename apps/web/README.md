# TEAM ZERO A 프론트엔드

상태: 합성 샘플 화면 구현·검증 완료. 실제 B API 연동 및 C 지표/차트 의미 합의 대기.

## 실행

Node 22.12 이상(검증 24.21.0), npm 11.19.0. 이 폴더에서:

```powershell
npm ci
npm run dev -- --port 5173 --strictPort
```

http://127.0.0.1:5173 에서 확인. 터미널 Ctrl+C로 종료. 현재 기본은 fixture이며 DB·비밀값·Bronze 원본이 필요하지 않다. 원본은 읽기 전용으로 사용한다.

```powershell
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

E2E는 4173/4174 두 포트를 사용하고 서버를 자동 종료한다. trace와 desktop/mobile 캡처는 test-results/에 생성된다. npm run preview는 빌드된 dist의 미리보기다.

## 화면

시장/기업·기간·보고서 필터, 기준일 비교표, 재무 카드, 주가/시장·실적/현금·수급/보유율 차트, 원값 표, 근거·레이어 품질/출처, CSV 다운로드. 비교표 기업을 선택하면 상세로 이동한다. 로딩/오류/재시도/빈 결과/NULL/0/계산 불가 표시와 반응형 레이아웃을 포함한다.

시장은 목록/비교, 시작일은 주가/수급, 기준일은 시점 조회, 연도/보고서/연결구분은 재무 영역에 적용된다. 비교·근거는 기준일의 최근 보고서를 사용한다. 샘플은 기준일 2026-06-30, 6월 6개 관측점, 2024/2025 연간 연결 보고서만 제공한다. 다른 조건은 빈 결과가 될 수 있다.

## API 전환

.env.example을 참고해 .env.local에 VITE_DATA_MODE=api, VITE_API_BASE_URL을 설정하고 서버를 재시작한다. 주소는 공개 설정이므로 비밀키를 넣지 않는다. src/api.js 한 곳에서 endpoint/응답 검증/취소/timeout을 관리한다. API 오류 시 합성 fallback 없음.

[A 제안 계약](../../contracts/A-screen.md)의 a-proposal-1 스키마는 B와 아직 미합의다. B의 실제 endpoint가 같다고 즉시 호환된다고 가정하지 않는다. C가 계산한 지표를 전달받아 표시하며 A가 업무 계산을 대체하지 않는다.

## 재사용·검증 범위

입력 스냅샷 03_C_integration_20261014의 s_stock 식별자만 샘플 생성에 재사용. 고정 75파일은 수정하지 않음. 신규 기능 검사는 기존 203 PASS와 별개다. 실제 DB/Delta·B API·새 Gold·원본 대사는 이번 화면 검증 범위 밖이다.

금액은 정수 문자열/BigInt로 표시하고 CSV 원문을 유지한다. 차트 좌표만 Number로 스케일링하며 정확한 값은 표에서 확인한다. 출처가 없는 값은 미제공으로 표시. CSV를 Excel로 가져올 때 식별자와 value 열을 텍스트로 지정하면 자동 정밀도 손실을 피할 수 있다.
