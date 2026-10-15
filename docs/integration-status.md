# 단계별 통합 진행표


2026-10-15 추가: B의 S4 1.1.0은 **미커밋 로컬 보완**이다. C계산해시 재현/2Delta/C값API대조·기준100차트PASS. 신규C MySQL/A실제API연결/새전달SHA·원격반영은대기. 최신요청별자료는 [S4](handoffs/S4-B-to-A.md) 상단을따른다. 아래기존SHA는v1코드로새확장미포함이다.

**다른 역할의 결과를 받으면 이 문서에서 단계 → 전달 기록 → 고정 SHA → 실행법 → 검사 결과 순으로 확인한다.** [절차·브랜치 규칙](integration-workflow.md) · [전달 양식](handoffs/TEMPLATE.md).

2026-10-15 B 실제 Delta·MySQL·기존 Gold API·덤프 복원 로컬 검증 완료. 고정 구현 전달은 `handoff/s4-b-to-a-v1` / `ba2aaf1008d52dc96d983f61cae40d8a628366a2`. 문서 후속 커밋은 feature/b-pipeline-api의 [Draft PR #6](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/6). A·C 수신 검증과 integration/main 병합은 별도다.

| 단계 | 합칠 내용 | 전달 → 확인 | 전달 브랜치·고정 SHA·PR | 수신 확인 브랜치·결과 | 상태·열린 의존성 |
|---|---|---|---|---|---|

| **S0 계약** | B API·환경 계약·샘플 | B → A·C | [API](../contracts/api.md)·[S4](handoffs/S4-B-to-A.md) | 미확인 | B 구현·검증 / C 분석·시각화 합의대기 |
| **S1 Bronze** | 실제오염91CSV/인계18입력/28Delta | B → C | [G04](handoffs/G04-validation.md)·S4고정SHA | C 독립확인대기 | B 저장·복구재현 / 최초원본과정제인계구분 |
| **S2 Silver** | 17Delta/MySQL·371437행 | B → C | [G04](handoffs/G04-validation.md)·S4고정SHA | C 독립확인대기 | B 전량대사PASS / 기간61·수급1검토유지 |
| **S3 Gold** | C 계산과 B 실행·저장, 기존Gold2저장·API / 신규분석 | C → B·A | [S3 전달 기록](handoffs/S3-C-to-B.md) / `handoff/s3-c-to-b-v1` / 검사 `fb1f802c88e2d5b275c737200aa392deac0e628b`(기록 커밋 `6a61b132f54bf6a2553ad323e57e73b1cda09e65`) / [PR #4](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/4) | B: 별도스냅샷계산/Delta/API대사PASS(정식 review/s3-b-v1 미등록) · A: review/s3-a-v1 재현 PASS | 수신 확인 대기 / 정식 review merge·신규C MySQL 대사(G04) 대기 |
| **S4 API→화면** | 실제조회·품질·근거·다운로드 | B → A·C | [S4](handoffs/S4-B-to-A.md) / `ba2aaf1008d52dc96d983f61cae40d8a628366a2` / [Draft PR #6](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/6) | A미확인 · C: `review/s4-c-v1` 값 일치(표기 2건 합의 필요) [S4-C-check](handoffs/S4-C-check.md) | B45자동·13HTTP·9MySQL API PASS / 수신확인대기 |
| **S5 전체** | 화면·계산·API·재현 공동검수 | A·B·C | 미등록 | 미확인 | 미완료 / C신규분석·A화면·G05필요 |
