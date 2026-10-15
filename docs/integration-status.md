# 단계별 통합 진행표


2026-10-15 추가: B의 S4 1.1.0은 **미커밋 로컬 보완**이다. C계산해시 재현/2Delta/C값API대조·기준100차트PASS. 신규C MySQL/A실제API연결/새전달SHA·원격반영은대기. 최신요청별자료는 [S4](handoffs/S4-B-to-A.md) 상단을따른다. 아래기존SHA는v1코드로새확장미포함이다.

**다른 역할의 결과를 받으면 이 문서에서 단계 → 전달 기록 → 고정 SHA → 실행법 → 검사 결과 순으로 확인한다.** [절차·브랜치 규칙](integration-workflow.md) · [전달 양식](handoffs/TEMPLATE.md).

2026-10-15 B 실제 Delta·MySQL·기존 Gold API·덤프 복원 로컬 검증 완료. 고정 구현 전달은 `handoff/s4-b-to-a-v1` / `ba2aaf1008d52dc96d983f61cae40d8a628366a2`. 문서 후속 커밋은 feature/b-pipeline-api의 [Draft PR #6](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/6). A·C 수신 검증과 integration/main 병합은 별도다.

| 단계 | 합칠 내용 | 전달 → 확인 | 전달 브랜치·고정 SHA·PR | 수신 확인 브랜치·결과 | 상태·열린 의존성 |
|---|---|---|---|---|---|

| **S0 계약** | 지표·API·시각화·환경 계약, 정상/NULL/오류 예시 | B·C → A·B·C | 미등록 | 미등록 | 작업 중 — C 분석·시각화 계약 제안본은 [PR #4](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/4)에 포함, A·B 확인 전 / API·환경 계약 |
| **S1 Bronze** | 원본·명세·해시·AS-IS 근거, Bronze Delta | B 저장·C 진단 → C·B | 미등록 | 미등록 | 입력 미확보 / M01~M05 |
| **S2 Silver** | Silver Delta·MySQL, 사전·키·기간·미해결 상태 | B 저장·C 검증 → C·B | 미등록 | 미등록 | 미착수 / M06~M08 |
| **S3 Gold** | C 계산과 B 실행·저장, 분석·차트 데이터 | C → B 실행·A 해석 확인 | [S3 전달 기록](handoffs/S3-C-to-B.md) / `handoff/s3-c-to-b-v1` / `fb1f802c88e2d5b275c737200aa392deac0e628b` / [PR #4](https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/4) | 미등록 | 수신 확인 대기 / B 저장·SQL 대조(M11·G04), A 차트 확인 |
| **S4 API→화면** | B의 실제 조회·품질·근거·다운로드 API | **B → A 연결 확인 / C 수치 확인** | [S4 전달 기록](handoffs/S4-B-to-A.md) / 브랜치·SHA·PR 미등록 | 미등록 | 미착수 / M12·M13 |
| **S5 전체** | A 화면·B 서버/저장·C 계산·출처/검증·재현 | A·B·C → 공동 확인 | 미등록 | 미등록 | 미착수 / M14·G05·F01~F08 |

## 갱신 시점과 책임

- **전달자:** 본인 검사 후 전달 기록과 이 표에 실제 브랜치·SHA·PR·실행법을 등록한다. 상태를 `수신 확인 대기`로 변경한다.
- **수신자:** 별도 확인 브랜치에서 재현하고 결과·환경·제한·수신자 커밋을 등록한다. `수정 필요` 또는 `수신 확인 완료`로 변경한다.
- **해당 PR을 병합하는 팀원:** PR 결과·병합 커밋을 확인해 `integration 병합 완료`로 갱신한다. 테스트하지 않고 자동 승인하지 않는다.
- **최종 통합 확인자:** S5 검증 후에만 최종 기능을 `main 반영 완료`로 표시한다.

상태: `미착수 → 작업 중 → 수신 확인 대기 → 수정 필요/수신 확인 완료 → integration 병합 완료 → main 반영 완료`. 입력 미확보·부분 완료·합성 검증은 별도로 명시한다. Bronze 입력이 없어도 제공 Silver·Gold의 독립 개발은 계속한다. S4 샘플 연동 성공을 실제 API 검증으로 표시하지 않는다.

전달 기록이나 PR을 등록하는 것만으로 상대에게 별도 알림이 전송됐다고 주장하지 않는다. 보고 위치는 이 표·전달 기록·해당 PR이며, 외부 메시지는 팀원이 별도로 공유한다.
