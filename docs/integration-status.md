# 단계별 통합 진행표

**다른 역할의 결과를 받으면 이 문서에서 단계 → 전달 기록 → 고정 SHA → 실행법 → 검사 결과 순으로 확인한다.** [절차·브랜치 규칙](integration-workflow.md) · [전달 양식](handoffs/TEMPLATE.md).

2026-10-15 B 실제 Delta·MySQL·기존 Gold API·덤프 복원 로컬 검증 완료. 고정 구현 전달은 `handoff/s4-b-to-a-v1` / `ba2aaf1008d52dc96d983f61cae40d8a628366a2`. 문서 후속 커밋은 feature/b-pipeline-api의 [Draft PR #6](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/6). A·C 수신 검증과 integration/main 병합은 별도다.

| 단계 | 합칠 내용 | 전달 → 확인 | 전달 브랜치·고정 SHA·PR | 수신 확인 브랜치·결과 | 상태·열린 의존성 |
|---|---|---|---|---|---|
| **S0 계약** | B API·환경 계약·샘플 | B → A·C | [API](../contracts/api.md)·[S4](handoffs/S4-B-to-A.md) | 미확인 | B 구현·검증 / C 분석·시각화 합의대기 |
| **S1 Bronze** | 실제오염91CSV/인계18입력/28Delta | B → C | [G04](handoffs/G04-validation.md)·S4고정SHA | C 독립확인대기 | B 저장·복구재현 / 최초원본과정제인계구분 |
| **S2 Silver** | 17Delta/MySQL·371437행 | B → C | [G04](handoffs/G04-validation.md)·S4고정SHA | C 독립확인대기 | B 전량대사PASS / 기간61·수급1검토유지 |
| **S3 Gold** | 기존Gold2저장·API / 신규분석대기 | C → B·A | C 신규전달SHA미등록 | 신규계산미검증 | 사용자지시기존Gold제공 / 신규어댑터합성검사만 |
| **S4 API→화면** | 실제조회·품질·근거·다운로드 | B → A·C | [S4](handoffs/S4-B-to-A.md) / `ba2aaf1008d52dc96d983f61cae40d8a628366a2` / [Draft PR #6](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/6) | A미확인 | B45자동·13HTTP·9MySQL API PASS / 수신확인대기 |
| **S5 전체** | 화면·계산·API·재현 공동검수 | A·B·C | 미등록 | 미확인 | 미완료 / C신규분석·A화면·G05필요 |

## 갱신 시점과 책임

- **전달자:** 본인 검사 후 전달 기록과 이 표에 실제 브랜치·SHA·PR·실행법을 등록한다. 상태를 `수신 확인 대기`로 변경한다.
- **수신자:** 별도 확인 브랜치에서 재현하고 결과·환경·제한·수신자 커밋을 등록한다. `수정 필요` 또는 `수신 확인 완료`로 변경한다.
- **해당 PR을 병합하는 팀원:** PR 결과·병합 커밋을 확인해 `integration 병합 완료`로 갱신한다. 테스트하지 않고 자동 승인하지 않는다.
- **최종 통합 확인자:** S5 검증 후에만 최종 기능을 `main 반영 완료`로 표시한다.

상태: `미착수 → 작업 중 → 수신 확인 대기 → 수정 필요/수신 확인 완료 → integration 병합 완료 → main 반영 완료`. 입력 미확보·부분 완료·합성 검증은 별도로 명시한다. Bronze 입력이 없어도 제공 Silver·Gold의 독립 개발은 계속한다. S4 샘플 연동 성공을 실제 API 검증으로 표시하지 않는다.

전달 기록이나 PR을 등록하는 것만으로 상대에게 별도 알림이 전송됐다고 주장하지 않는다. 보고 위치는 이 표·전달 기록·해당 PR이며, 외부 메시지는 팀원이 별도로 공유한다.
