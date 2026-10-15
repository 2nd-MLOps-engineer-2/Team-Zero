# TEAM ZERO B 서비스

상태: 기존 C Gold 기반 조회 API 구현·로컬 검증 완료. A의 화면 수신 검증, C의 신규 분석 Gold, integration/main 반영은 별도다.

## 팀원 PC에서 시작

프로젝트 루트의 PowerShell에서 Python 3.12로 실행한다.

```powershell
& .\backend\service\setup.ps1 -Python python
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\run.py --backend csv
```

브라우저에서 `http://127.0.0.1:8000/docs`를 열고 Try it out을 사용한다. 종료는 실행 창에서 Ctrl+C. 서버를 켜 둔 동안 A 화면이 접속한다. CSV 모드는 저장소의 고정 75파일로 바로 실행한다. 다른 PC의 localhost는 이 PC의 MySQL이 아니므로 팀원은 우선 CSV API를 실행한다. 원격 DB 공유·배포는 아직 구성하지 않았다.

현재 PC에서는 준비한 Delta와 MySQL을 사용할 수 있다.

```powershell
& .\backend\service\start_api.cmd
& .\backend\service\start_mysql_api.cmd
```

첫 명령은 auto(Delta run이 있으면 Delta, 없으면 CSV), 둘째는 MySQL이다. 각각 별도로 실행한다. MySQL 비밀번호는 PC에서 입력하고 Enter. 화면에는 글자나 별표가 나타나지 않는다. 서비스는 읽기 전용이며 변경된 고정 스냅샷은 거부한다. 정상적 새 데이터도 재시작·새 버전 검증 후 반영한다.

## 검사

```powershell
& .\backend\service\.venv\Scripts\python.exe -X utf8 -m pytest .\backend\service\tests -q
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\verify_http.py --backend csv
& .\backend\service\verify_mysql.cmd
```

HTTP 검사는 전용 자식 서버를 18000 포트에 띄우고 자기 서버만 종료한다. MySQL 검사는 로컬 암호 입력 후 API 9개 응답을 CSV와 비교하고 새 덤프 4개를 만든다. 기존 DB는 보존하고 `tz_restore_<layer>_<new_run_id>` DB 4개에 복원해 58개 테이블의 모든 값을 대조한다. 복원 DB·덤프는 검사용으로 남는다. 매 실행마다 새 대상이 생기므로 완료 증빙 확인 목적으로 반복 실행할 필요는 없다.

MySQL Workbench에서 [inspect_database.sql](inspect_database.sql)을 열면 현재 DB 건수와 삼성전자 재무·주가를 확인할 수 있다. 적재 명령은 `backend\medallion_pipeline\start_mysql.cmd`이며 검증 명령과 다르다. 현재 58테이블 적재는 이미 PASS다.

## 구조·환경

`tz_api/`: CSV·Delta·MySQL 읽기 어댑터 / API / 타입 / C 결과 전달 어댑터. `run.py`: 서버. `verify_http.py`: 실제 HTTP. `verify_mysql.py`: 실제 DB API·덤프·복원. `import_analysis.py`: C 결과 전달 후 저장. 기존 `backend/medallion_pipeline`의 엔진·표준 사전·DDL을 재사용한다. 원본 75파일은 수정하지 않는다.

[API 계약](../../contracts/api.md), [환경 계약](../../contracts/runtime.md), [C 전달 형식 제안](../../contracts/analysis-artifact.md), [B→A 전달 기록](../../docs/handoffs/S4-B-to-A.md), [검증 결과](../../docs/handoffs/G04-validation.md)를 참조한다.

설정은 `.env.example`의 환경 변수 또는 `run.py --help`의 옵션으로 받는다. `.env` 자동 로드는 하지 않는다. CORS 기본 허용 주소는 localhost:3000/5173 및 127.0.0.1:5173이며 `TZ_CORS_ORIGINS`로 쉼표 구분 변경한다. 비밀번호·실데이터·덤프·venv·build는 커밋하지 않는다.
