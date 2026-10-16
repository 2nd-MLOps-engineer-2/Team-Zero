# MySQL DB 스냅샷 — 2026-10-16

팀원은 [DB Release](https://github.com/2nd-MLOps-engineer-2/Team-Zero/releases/tag/db-snapshot-20261016)에서 **TEAM_ZERO_DB_20261016_VERIFIED.zip**을 내려받는다. SQL 덤프는 Release 첨부 파일로 공유하며 Git 이력에는 넣지 않는다.

## 포함 범위와 검증

| 계층 | 테이블 | 행 |
|---|---:|---:|
| Bronze | 28 | 1,592,478 |
| Silver | 17 | 371,437 |
| Gold | 4 | 35,520 |
| Meta | 11 | 1,527 |
| 합계 | **60** | **2,000,962** |

Gold에는 기존 `g_ai_stock_daily`·`g_fin_rpt_mkt_smry`와 C 분석 `g_fin_rpt_analysis`·`g_stock_daily_analysis`가 포함된다. 20종목, 일별 관측 2022-12-01~2026-06-30, 재무 2022~2025년 범위다.

MySQL **8.4.11**에서 새 DB 4개에 실제 복원한 결과, **34,213,807개 값 전량 대사와 SQL 규칙 92개를 모두 통과**했다. 검증 완료 시각은 **2026-10-16 09:43:25 KST**다.

- [실제 복원 결과](db-snapshot-20261016/restore_validation.json)
- [테이블별 행·열 수와 값 해시](db-snapshot-20261016/table_inventory.csv)
- [ZIP SHA256](db-snapshot-20261016/TEAM_ZERO_DB_20261016_VERIFIED.zip.sha256)

이 파일은 **2026-10-15 기존 58개 실제 MySQL 덤프 + C 계산 버전 `c-gold-0.1.0`의 검증된 2개 분석 테이블**을 합친 고정본이다. 모든 최신 DB를 다시 추출한 파일이나 이후의 추가 분석 전체를 의미하지 않는다. 기존 58개 출처 실행은 `20261015_101647_d567`, 덤프·복원 증빙은 `20261015_112252_60d6`, 신규 분석 Delta 버전은 0이다. C 분석 CSV는 고정 커밋 `5372c4dade48036e8e3265af66472058417d3cf2`의 값과 일치하는 파일을 사용했다.

## 다운로드와 복원

1. Release의 ZIP과 `.sha256`을 내려받고 ZIP의 SHA256을 비교한다.
2. ZIP을 완전히 풀고 `TEAM_ZERO_DB_20261016` 폴더에서 PowerShell을 연다.
3. MySQL Server 8.x와 `mysql` 클라이언트, Python 3.12 또는 3.13을 준비한다.
4. 다음 명령을 실행한다. 비밀번호는 마지막 명령 실행 후 PC에서 직접 입력한다.

```powershell
python -m venv .restore_venv
& ".\.restore_venv\Scripts\python.exe" -m pip install -r requirements.txt
& ".\.restore_venv\Scripts\python.exe" restore_db.py check
& ".\.restore_venv\Scripts\python.exe" restore_db.py restore --host 127.0.0.1 --port 3306 --user root
```

`mysql.exe`를 자동으로 찾지 못하면 마지막 명령에 `--mysql-bin "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"`를 추가한다. 자세한 안내는 ZIP 내부 `먼저읽기_복원안내.txt`에 있다.

복원 도구는 `tz_share_실행시각_임의값_bronze/silver/gold/meta` 형식의 **새 DB 4개**를 만들며 기존 DB는 삭제하거나 덮어쓰지 않는다. 같은 이름의 DB가 있으면 중단한다. 중간 실패 시 생성된 부분 DB는 보존하며 재실행은 새 이름을 사용한다.

성공 시 `SUCCESS: 60 tables restored; every row/column hash and SQL rules matched.`가 표시되고, 생성 DB명과 전량 검증 결과가 `local_restore_results/restore_실행시각_임의값.json`에 저장된다.

## Workbench에서 확인

Schemas를 새로고침하고 결과 JSON의 `databases.gold`에 기록된 이름을 선택한다. 아래 DB명은 실제로 생성된 이름으로 바꾼다.

```sql
SELECT COUNT(*) AS rows_count,
       COUNT(DISTINCT stock_cd) AS stocks_count,
       MIN(trd_dt) AS first_date,
       MAX(trd_dt) AS last_date
FROM `실제_gold_DB명`.`g_stock_daily_analysis`;
-- 기대값: 17440 / 20 / 2022-12-01 / 2026-06-30
```

GitHub 다운로드나 `git pull`은 팀원의 MySQL을 자동 갱신하지 않는다. 데이터 변경은 새 버전의 덤프로 공유하고 새 DB에 복원한다. 공용 DB 접속, API의 연결 환경 설정, 서버 배포는 별도 작업이다. Delta 데이터·로그 자체는 이 MySQL 패키지에 포함하지 않았다.

## 배포 파일 검증값

- 파일: `TEAM_ZERO_DB_20261016_VERIFIED.zip`
- 크기: `67,699,272` bytes
- SHA256: `ea2f8a92c5b24c4d98f64d6e1b9279aea0a9fd15f3346353ab7f2aa776d71926`
- DB 비밀번호·토큰·MySQL 사용자 및 권한 테이블은 포함하지 않는다.

이번 커밋 범위는 DB 배포 안내와 복원 검증 기록이다. 서비스 코드·지표 계산·기존 데이터는 변경하지 않았다.
