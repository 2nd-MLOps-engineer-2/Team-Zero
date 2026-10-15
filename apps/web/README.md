> 최신 통합 실행은 [S5 통합 기록](../../docs/handoffs/S5-integration.md)을 따른다. 아래 S4 ZIP runtime은 과거 수신 환경이며 현재는 병합된 backend/service를 실행한다.

# TEAM ZERO A 프론트엔드

상태: 합성 샘플 화면 구현·검증 완료. 실제 B API 연동 및 C 지표/차트 의미 합의 대기.

## C 전달본 검토 후 갱신

C 고정 SHA fb1f802c88e2d5b275c737200aa392deac0e628b의 G01/G03를 검토했다. 사분면(매출 YoY % / 공시 후 초과성과 %p), 20관측 순매수 수량/거래량 비율, 복합 동반 개선 Y/N/판단 불가, C 상태 문구를 표시한다. 기존 일별 수량·외국인 보유율과 별도 차트다. 재무 가로축은 보고기간 종료일, 같은 보고서 유형의 YTD로 표시한다.

src/c-contract.js는 C decimal 문자열·빈 문자열·필드 별칭을 표현용으로 매핑한다. 금융 계산은 하지 않고 원문 C 필드를 CSV에도 보존한다. 샘플 가격은 생성 시 미리 준비한 구간별 기준값을 조회하며, 실제 API는 B/C가 동일 시작일의 기준값을 제공해야 한다.

C 결과를 재현한 환경에서만 실행하는 추가 검증:

```powershell
# 저장소 루트에서 실행. C 모듈은 별도 review 브랜치에서 받은 상태여야 함.
python apps/web/scripts/prepare-c-review.py --c-output build/a-c-review-output --output build/a-c-review-bundle.json
cd apps/web
$env:C_REVIEW_BUNDLE = (Resolve-Path ../../build/a-c-review-bundle.json).Path
npm run test:e2e
```

기본 E2E는 11개 실행 + C 실제 입력 1개 명시적 skip, C_REVIEW_BUNDLE 제공 시 12개 모두 실행한다. 실제 C 입력은 build/에서만 보존하며 저장소/CI에 자동 업로드하지 않는다. CI는 샘플·모의 API 검사이고 실제 B 서버 검증 아님.

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

[A 화면 계약](../../contracts/A-screen.md)의 a-proposal-1은 내부/샘플 표현이다. 실제 B API 1.1.0은 별도 어댑터로 연결 검증했다. API 1.0.0 등 다른 버전을 동일하게 취급하지 않는다. C가 계산한 지표를 전달받아 표시하며 A가 업무 계산을 대체하지 않는다.

## 재사용·검증 범위

입력 스냅샷 03_C_integration_20261014의 s_stock 식별자만 샘플 생성에 재사용. 고정 75파일은 수정하지 않음. 신규 기능 검사는 기존 203 PASS와 별개다. S4에서 제공 CSV·C Gold·B 실제 API·화면/CSV 대사를 수행했다. 실제 DB/Delta 저장·Bronze 원본 대사는 별도 범위다.

금액은 정수 문자열/BigInt로 표시하고 CSV 원문을 유지한다. 차트 좌표만 Number로 스케일링하며 정확한 값은 표에서 확인한다. 출처가 없는 값은 미제공으로 표시. CSV를 Excel로 가져올 때 식별자와 value 열을 텍스트로 지정하면 자동 정밀도 손실을 피할 수 있다.

## S4 실제 API 재실행 (현재 로컬 수신 환경)

작업 디렉터리는 저장소 루트 `C:\Users\Playdata\Desktop\Team-Zero`다. ZIP은 `build/s4-received-20261015`에 분리했고, B baseline과 ZIP 서비스 수정본을 runtime에 준비했다. runtime/data는 고정 data를 참조하는 junction이며 수정 대상이 아니다. 기존 A/B/C 소유 경로에 ZIP을 덮어쓰지 않는다. `build/s4-c-api-artifact`는 기존 C 출력 두 CSV를 변경하지 않고 B 패키징 도구로 검증한 결과다. 이 경로들은 로컬 준비물로 Git에 포함되지 않는다. 새 PC에서는 S4 기록의 ZIP·baseline·C 출력부터 확보하고 별도 runtime을 준비해야 한다.

API 터미널:

```powershell
$env:TZ_CORS_ORIGINS='http://127.0.0.1:5173,http://127.0.0.1:4175'
& build/s4-api-venv/Scripts/python.exe -X utf8 build/s4-received-20261015/runtime/backend/service/run.py --backend csv --project-root build/s4-received-20261015/runtime --analysis-dir build/s4-c-api-artifact --port 8000
```

프론트엔드 별도 터미널:

```powershell
$env:VITE_DATA_MODE='api'
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
npm --prefix apps/web run dev -- --port 5173 --strictPort
```

각 실행 터미널에서 Ctrl+C로 해당 서버만 종료한다. 화면 http://127.0.0.1:5173, API 문서 http://127.0.0.1:8000/docs. 설정 파일을 강제로 바꾸지 않았으므로 위 환경 설정 없이 실행하면 기본 합성 샘플 모드다.

검사 터미널:

```powershell
python scripts/check_handoff.py
$env:TZ_TEST_PROJECT_ROOT=(Resolve-Path build/s4-received-20261015/runtime).Path
& build/s4-api-venv/Scripts/python.exe -m pytest build/s4-received-20261015/runtime/backend/service/tests -q
npm --prefix apps/web test
npm --prefix apps/web run build
$env:S4_API_BASE_URL='http://127.0.0.1:8000'
$env:C_REVIEW_BUNDLE=(Resolve-Path build/a-c-review-bundle.json).Path
npm --prefix apps/web run test:e2e
```

실제 API 브라우저 검사는 4175를 추가 사용한다. C 미연결 검사도 실행하려면 별도 터미널에서 위 API 명령의 `--analysis-dir` 인자만 제외하고 `--port 8001`로 시작한 후 검사 터미널에 `$env:S4_NO_C_API_URL='http://127.0.0.1:8001'`을 설정한다. 이 검사는 브라우저 요청을 실제 미연결 서버로 중계해 카드 유지·분류 미연결·CSV 409를 확인한다. 세 입력 환경변수가 모두 있으면 16개 검사, 기본 환경은 11개 실행·5개 명시적 skip이다. 실제 API 8000/8001은 검사 도구가 종료하지 않으며 시작한 터미널에서 정리한다.

서버 CSV는 B가 제공한 원값 그대로 다운로드한다. C 전체 산출물은 선택 기업·기간과 관계없이 전체 범위다. Excel에서 종목코드·큰 금액을 가져올 때 텍스트로 지정한다. 브라우저 CSV 전후 버전 확인은 서버의 읽기 전용 스냅샷을 전제로 하며 배포 중 버전이 바뀌면 재조회한다.
