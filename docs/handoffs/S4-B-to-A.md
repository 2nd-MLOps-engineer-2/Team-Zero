# S4 API 전달 보완 — B → A (2026-10-15 / API 1.1.0 로컬 검증본)


```powershell
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\pack_c_analysis.py --source .\build\analysis --output .\build\c_api_artifact
& .\backend\service\.venv\Scripts\python.exe -X utf8 .\backend\service\run.py --backend csv --analysis-dir .\build\c_api_artifact
```

현재 B PC에는 검증한 묶음이 `build/s4_api_20261015/c_api_artifact`에 있다. 해당 PC에서는 위 analysis-dir만 이 경로로 바꾼다. 한 번에 서버 하나를 시작하고 종료는 실행 창 Ctrl+C. C CSV의 빈칸만 JSON null로 바꾸며 계산값·상태코드는 바꾸지 않는다. C 묶음을 생략하면 기존 Gold는 조회 가능하고 analysis=null/PENDING_C_DELIVERY로 명확히 남는다.
