# G01 보조 — C 결과 저장·제공 형식 제안

상태: B 어댑터 구현·합성 경계 검사 완료 / C 합의·실제 신규 결과 미전달. 지표 정의·계산식·시각화 계약은 C의 `analysis.md`/`visualization.md`에서 별도로 정한다. 사용자 지시에 따라 현재 API는 기존 Gold로 제공한다.

C가 `g_fin_rpt_analysis.csv`(PK fin_rpt_id,320행), `g_stock_daily_analysis.csv`(PK stock_cd+trd_dt,17440행), `manifest.json`을 같은 폴더로 전달하는 방식을 제안한다. 지표 컬럼은 C가 정하고 아래 columns에 명시한다. 아래 JSON의 값은 형식 설명용이며 실행 자료가 아니다.

```json
{
  "contract_version": "tz-analysis-artifact/1.0",
  "calculation_version": "C가_고정한_계산버전",
  "input_version": "handoff-sha256:<data/handoff_manifest.json SHA256 앞16자리>",
  "tables": {
    "g_fin_rpt_analysis": {
      "file": "g_fin_rpt_analysis.csv", "sha256": "<실제 파일 SHA256>", "rows": 320,
      "primary_key": ["fin_rpt_id"],
      "columns": [{"name":"fin_rpt_id","sql":"VARCHAR(64)","nullable":false}]
    },
    "g_stock_daily_analysis": {
      "file": "g_stock_daily_analysis.csv", "sha256": "<실제 파일 SHA256>", "rows": 17440,
      "primary_key": ["stock_cd","trd_dt"],
      "columns": [
        {"name":"stock_cd","sql":"CHAR(6)","nullable":false},
        {"name":"trd_dt","sql":"DATE","nullable":false}
      ]
    }
  }
}
```

CSV 헤더는 columns 순서와 같아야 한다. NULL은 빈칸, PK는 nonnullable. 지원 타입은 CHAR/VARCHAR/TEXT/DATE/INT/BIGINT/DECIMAL(p,s; 최대38)이다. UTF-8 또는 UTF-8 BOM. 경로는 묶음 안에 한정하고 해시·행수·PK 중복/범위·타입/길이/정밀도·기준320/17440키 전량 일치를 검사한다. 일별 fin_rpt_id가 있으면 기존 Gold의 PIT 선택과 같아야 한다. 정정된 선택 규칙이 필요하면 새 입력 버전과 합의가 먼저다.

입력 버전은 아래로 얻는다.

```powershell
& .\backend\service\.venv\Scripts\python.exe -c "import hashlib,pathlib; print('handoff-sha256:'+hashlib.sha256(pathlib.Path('data/handoff_manifest.json').read_bytes()).hexdigest()[:16])"
```

전달 이후 서버를 `run.py --backend csv --analysis-dir <C폴더>`로 시작하면 analysis 필드와 C CSV 다운로드가 활성화된다. `import_analysis.py --source <C폴더>`는 두 테이블의 실제 Delta를 새 `build/analysis_import/<run>`에 저장한다. `--mysql` 추가 시 로컬 비밀번호로 새 `tz_gold_analysis_<run>`에 저장하고 전량 대사한다. 기존 DB는 거부한다. 이 명령의 실제 C 입력 실행·MySQL 적재는 C 전달 전이므로 아직 검증하지 않았다. 합성 테스트의2테이블 저장 성공을 실제 C 분석 완료라고 표시하지 않는다.
