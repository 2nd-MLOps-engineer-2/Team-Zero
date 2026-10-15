# B 진행 기록 — 설호현 / 백엔드

상태: 시작 전. [프롬프트](../../prompts/B_backend.md) · [체크북](../workbook.md).

구현 예정 경로: `apps/api/`, `pipelines/`, `infra/`. 아직 환경 고정·Delta·DB·API 실행 구현은 없다.

데이터 준비: `data/03_C_integration_20261014/`에 실제 Silver·Gold·Meta와 DDL·기존 코드가 포함되어 있다. [데이터 안내](../data-guide.md) 참조. Bronze 입력 원본 18개·별도 덤프·원문 ZIP은 미포함이다.

| 작업 ID | 변경·증빙 경로 | 실행 명령·결과 | 기준 커밋/데이터 버전 | 남은 의존성 |
|---|---|---|---|---|
| B01~B12 | 미등록 | 미실행 | 미등록 | Bronze 원본·C 계산 계약·실행 환경 |

버전·설치·실행·종료·복원법과 G01·G02·G04·G05 handoff를 구현 후 기록한다.
