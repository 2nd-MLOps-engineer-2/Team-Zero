# A 진행 기록 — 이어진 / 프론트엔드

상태: 시작 전. [프롬프트](../../prompts/A_frontend.md) · [체크북](../workbook.md).

단계 책임: S0 계약 확인, S3 차트 의미 확인, **S4 B의 API를 A 작업의 review 브랜치에 합쳐 확인·보고**, S5 화면 전달·통합 검사. [진행표](../integration-status.md)와 [S4 기록](../handoffs/S4-B-to-A.md)에 전달 SHA·A review HEAD·실행 결과를 기록한다.

필수 보완: [M08·M09·M12·M13·M14 및 A 역할](../missing-work.md). Bronze 출처/미확보, Silver 검토/NULL, Gold 계산/근거 상태의 화면·계약·예제·검사를 추가한다. 항목별 상태·증빙·의존성을 아래 기록에 추가한다. 현재 모두 미완료다.

구현 예정 경로: `apps/web/`. 아직 실행 명령·화면 구현은 없다.

데이터 준비: `data/03_C_integration_20261014/`에 실제 `s_stock`·Gold·사전이 포함되어 있다. [데이터 안내](../data-guide.md)에서 단위·NULL·기간을 확인한다. 데이터 업로드와 A01~A10의 완료는 별개다.

| 작업 ID | 변경·증빙 경로 | 실행 명령·결과 | 기준 커밋/데이터 버전 | 남은 의존성 |
|---|---|---|---|---|
| A01~A10 | 미등록 | 미실행 | 미등록 | B API·C 차트 계약 |

실행 방법과 실제 API/합성 fixture 사용 여부, G02·G03·G05 handoff를 구현 후 기록한다.
