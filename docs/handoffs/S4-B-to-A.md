# S4 — B API를 A 화면 작업에 전달

2026-10-15 상태: B 실제 구현·로컬 검증 완료 / A·C 수신 확인 대기. 전달자는 B 설호현, 수신자는 A 이어진(화면)·C 김형준(수치)이다. integration/main 병합·S5 완료로 표시하지 않는다.

| 항목 | 실제 값 |
|---|---|
| 검증 코드 전달 브랜치 | `handoff/s4-b-to-a-v1` |
| 고정 구현 전체 SHA | `ba2aaf1008d52dc96d983f61cae40d8a628366a2` |
| 선행 integration SHA | `b9b73a49bf169b17e3c324fcc9e51564d350b1ea` |
| 작업·문서 브랜치 | `feature/b-pipeline-api`; 고정 구현 이후 인계 문서 커밋만 추가 |
| integration 대상 PR | PR_PENDING |
| API / 데이터 / 기존 C 계산 | 1.0.0 / delta-run:20261015_101647_d567 또는 handoff SHA / c-integration-1.0.0 |
| A 수신 브랜치·SHA·결과 | 미등록; A 자신의 작업 HEAD에서 review/s4-a-v1 생성 후 고정 구현SHA merge |

## 바로 실행

프로젝트 루트 PowerShell, Python3.12. 설치 후 CSV 서버를 실행한다. 서버 종료 Ctrl+C. 동일 포트의 서버를 중복 시작하지 않는다.

```powershell
& .\backend\service\setup.ps1 -Python python
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\run.py --backend csv
```

브라우저 `http://127.0.0.1:8000/docs`. 현재 DB를 가진 PC에서는 `backend/service/start_mysql_api.cmd`, 암호는 로컬 입력(표시 안 됨). 팀원 PC는 우선 CSV 모드를 쓴다. 원격 DB 공유·배포는 구성하지 않았다. 설정·설치·종료·검사 전체는 [서비스 README](../../backend/service/README.md), [환경 계약](../../contracts/runtime.md).

## 전달 범위

- [x] 실제 기업 목록·비교·일별·재무·품질·근거·CSV API. [계약](../../contracts/api.md), [정상/결측/오류 샘플](../../fixtures/api/README.md), OpenAPI·TypeScript 표시용 타입 제공.
- [x] 금액·수량·비율은 문자열, NULL≠0, 원/주/소수 비율, 최종일2026-06-30/20종목을 명시.
- [x] 실제 Delta58/MySQL58와 전량 값 대사, 새덤프4/새복원DB4/58테이블 전량일치 PASS. [G04](G04-validation.md).
- [x] 새 가상환경39패키지 고정 설치·pip check PASS. 실제 반영 코드 자동검사45PASS, 실제 Delta HTTP13PASS. 고정75파일 무결성PASS.
- [x] 실제 MySQL API9응답과 CSV 전량응답비교PASS. 이전 품질/재무CSV 물리순서 문제를 명시정렬로 수정하고 역순 원본 회귀검사 추가.
- [ ] C 신규 분석계산 g_fin_rpt_analysis/g_stock_daily_analysis 전달·합의·실제적재. 현재 analysis=null/PENDING_C_DELIVERY. B 어댑터는 합성경계검사만 완료.
- [ ] A 화면 실제연결·C 독립수치대조·G05/S5 공동검수.

최신 로컬 증빙: `build/api_http/20261015_113540_68a2/http_validation.json`(실제HTTP13), `build/mysql_operations/20261015_112252_60d6/api_mysql_validation.json`(MySQL9), 같은 폴더 `backup_restore_validation.json`(58복원). 45자동검사 JUnit은 로컬 `build/b_handoff_20261015/published_pytest.xml`에 보존한다. 입력18개 확보/해시/크기/행/헤더는 같은 폴더 input_manifest.csv. 원본·덤프·Delta실물·비밀번호·venv는 Git 미포함이다.

## A가 자기 작업에 합쳐 확인

미커밋 변경을 보존한 뒤 A 본인 작업 HEAD에서 review 브랜치를 만들고 원격 고정 브랜치·SHA가 일치하는지 확인해 위 구현 SHA를 merge한다. B 브랜치로 단순 이동해 A 화면이 없는 상태를 검수하지 않는다. 이 문서 후속 변경은 feature 브랜치·PR에서 확인한다.

005930/2026-06-30: API 일별 매출·영업이익·순이익·영업현금, 선택보고서/공시일, 재무94지표, 화면·CSV를 비교한다. 247540/2026-04-16: 가격은 유지되고 수급null/미제공 플래그가 보이는지 확인한다. 404/422/409·빈 범위·로딩·CORS·큰금액을 검사한다. 재무 누적값을 일별 합산하지 않는다. 비교창·휴일실제관측일·공시당일제외를 표시한다.

수신 보고는 본인 review SHA, 실행 환경·명령, 실제 화면/수치 증거, 충돌·계약수정요청, 남은 일을 여기에 추가한다. A 화면은 B가 수정하지 않았다.

## 수신·통합 결과

A 수신 확인: 미확인. C 독립 검토: 미확인. integration 병합: 미실행. main 반영: 미실행. 신규 분석/화면/AI최종학습입력 규격까지 완료한 것으로 발표하지 않는다.
