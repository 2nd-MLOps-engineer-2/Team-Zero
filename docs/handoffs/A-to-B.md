# A → B: API·환경 인수인계 준비

2026-10-15 / A 이어진 → B 설호현 / **요청 정리, 합의·전달·수신 검증 전**.

G02 / A08~A10 / M08·M09·M12·M13·M14. 기준 feature/a-dashboard, HEAD 및 선행 integration `8af915fba1c40849b4cb80d7d8c2bd1768f674b7`. 미커밋 초안이며 기능 전달 SHA·PR 없음.

## 다음 B 전달에 필요한 항목

1. contracts/api.md: 종목 목록·비교·일별·보고서·품질·근거·CSV endpoint, 쿼리·응답·버전. A 코드의 /stocks, /stocks/compare, /stocks/{code}/daily, /stocks/{code}/financials, /analysis/{code}/evidence는 미합의 제안.
2. 기준일·시장·시작일·사업연도·보고서 코드·CFS/OFS 필터, 조회 기간 밖/주말/공시 당일 처리. 공시일 < 거래일, 보고기간 성과와 공시 후 성과 구분.
3. 6자리 종목코드 문자열, 금액/큰 수량 정수 문자열, 비율 소수, 날짜 ISO. NULL·0·미연결·검토·격리·계산 불가의 코드/사유.
4. 최종일 2026-06-30, 보유 20종목, 관측 수·구간·단위·입력/계산 버전·실제/합성 표시. API 간 snapshot 일관성 정책.
5. Bronze 파일/행/해시/실물 가용성, Silver 키·사유·처리 상태, Gold 보고서·계산 버전. 미제공은 NULL. 247540 / 2026-04-16 수급 부재·CFD 제공 전·재무 미연결 실제 예제.
6. 정상/빈 목록/오류/NULL/0/20자리 금액 예제, export 응답·파일명·단위·NULL 정책. 비밀값 없는 환경 예시·CORS/인증·설치/시작/종료법.
7. 실제 검사된 handoff 브랜치·전체 SHA·integration 대상 PR·실행 결과를 S4에 등록.

A 초안은 {meta, data: []}, schema_version a-proposal-1을 사용한다. endpoint별 관측 수 등을 meta에 넣으면 현재 전체 meta 일치 검사에서 거절될 수 있으므로 필드별 일관성 정책을 합의한 후 A가 수정한다. 실제 API 오류를 합성 샘플로 자동 대체하지 않는다.

## A 수신 검사 계획

B 전달본 확인 → A 작업 보존 → A HEAD에서 review/s4-a-v1 → 고정 SHA merge → 실제 서버 실행 → 필터/오류/취소/NULL/0/큰 금액·CSV/화면 대조 → S4 결과 기록. B 자체 검사만으로 A 수신 완료 처리하지 않는다.

최신 재개 결과: 화면/단위 검사 구현 후 빌드·단위 10개·브라우저 9개 PASS. [A 화면 계약 제안](../../contracts/A-screen.md)과 [로컬 실행법](../../apps/web/README.md)을 확인할 수 있다. meta 일치 검사는 schema/synthetic/data_end/input_version/calc_version으로 좁혔으며 endpoint별 추가 메타는 허용한다. B 실제 API는 여전히 미검증. 원격 main `1971dcbdfae2e2d29d1bc77ef712e40256014b34`, integration `b9b73a49bf169b17e3c324fcc9e51564d350b1ea` 반영, A 기능은 미커밋 로컬 상태. 외부 메시지 발송 없음.
