B 담당 첫 실습: 주가 CSV → 실제 Delta 테이블 → 새 MySQL DB → 값 대조

1. 이번 실습의 범위
현재 C가 검증한 Silver 주가 표 하나(20종목, 17,440행)를 사용합니다.
전체 Bronze/Silver/Gold 구현의 완료본이 아니라 저장소 연결을 익히는 첫 실습입니다.
재무·Gold 계산과 API는 이번 연결을 확인한 뒤 확장합니다.

Delta Lake Python 구현인 delta-rs(deltalake)를 사용합니다.
실제 Parquet 데이터와 _delta_log를 만들며 Delta 버전을 고정해 다시 읽습니다.
이 첫 실습에는 Java·Spark가 필요하지 않습니다. 후속 PySpark 구현과는 실행 엔진이 다릅니다.
공식 설명: https://delta-io.github.io/delta-rs/latest/usage/writing/

2. 설치(전용 가상환경만 변경)
이 폴더에서 실행합니다. Python 3.12를 권장합니다.
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt

3. Delta만 먼저 실습하기
  .\.venv\Scripts\python.exe price_demo.py --source <s_stock_daily_prc.csv의 실제 위치> --delta-only

이 프로젝트의 기본 폴더 구조를 유지했다면 다음 PowerShell 명령도 가능합니다.
  .\run_demo.ps1 -Step delta

기존 runs 아래에 Delta 검증 완료 폴더가 있다면 MySQL 단계부터 이어서 진행할 수 있습니다.
각 실행은 새 runs/run_실행일시_식별자를 만들고 입력 파일과 기존 결과는 덮어쓰지 않습니다.

4. 만든 Delta를 MySQL에 적재하기
MySQL 사용자 root / 주소 127.0.0.1 / 포트 3306으로 설정했습니다.
가장 간단한 방법: start_mysql.cmd를 더블클릭합니다.
또는 이 폴더의 PowerShell에서:
  .\.venv\Scripts\python.exe continue_mysql.py

PowerShell 스크립트를 사용할 경우:
실행 결과 폴더가 하나뿐이라면:
  .\run_demo.ps1 -Step mysql

여러 개라면:
  .\.venv\Scripts\python.exe price_demo.py --load-existing <사용할 runs 하위 폴더>

실행 중 MySQL password:가 나오면 PC의 터미널에서 직접 입력합니다.
입력 문자는 표시되지 않으며 비밀번호는 파일·로그·명령줄 인자에 저장되지 않습니다.
비밀번호를 잊었다고 해서 이 실습에서 계정이나 서버 비밀번호를 초기화하지 마세요.

5. 어떤 DB와 테이블이 만들어지는가
새 실습 DB: tz_demo_실행일시_식별자
그 안의 테이블: s_stock_daily_prc
기존 tz_bronze/tz_silver/tz_gold 및 수업 DB는 변경하지 않습니다.
동일한 실습 DB가 이미 존재하면 중복 적재하지 않고 중단합니다.
실습 코드에는 DROP/TRUNCATE/REPLACE가 없습니다.

Delta의 가격은 DECIMAL(18,4), 거래량은 BIGINT, 종목코드는 문자열입니다.
입력의 19개 비즈니스·출처 컬럼을 모두 보존합니다.
NULL과 0을 구분하고 가격에 float를 사용하지 않습니다.
통화는 KRW, 일시의 의미는 기존 C 테이블과 같은 KST 로컬 시각입니다.

6. 실행 폴더에서 볼 것
- delta/silver/s_stock_daily_prc/: 실제 Delta 테이블.
- delta/silver/s_stock_daily_prc/_delta_log/: Delta 트랜잭션 기록.
- delta_validation.json: 입력 해시, 건수, 날짜 범위, Delta 버전, 값 대조.
- 01_create_mysql.sql: 이번 실행의 테이블 구조 참고용.
- 02_check_mysql.sql: Workbench에서 볼 수 있는 조회 예시.
- mysql_validation.json: MySQL 적재와 전체 행·컬럼 값 대조가 성공한 경우 생성.

7. 성공 기준
Delta: 17,440행 / 20개 종목 / 키 중복 0 / 입력→Delta 전체 값 일치.
MySQL: 같은 건수·기업·기간 / Delta→MySQL 331,360개 값 전체 일치.
mysql_validation.json의 status=PASS를 확인해야 DB 적재까지 완료입니다.
DELTA_PASS_MYSQL_PENDING은 Delta만 확인했고 MySQL은 아직이라는 뜻입니다.
MySQL CREATE 작업은 트랜잭션 롤백 대상이 아니므로 실패 시 새 실습 스키마가 남을 수 있습니다.
실패한 스키마를 자동 삭제하지 않습니다. 원인을 확인하고 새 실행 폴더로 재실행합니다.

8. 이후 확장
① 교환받은 오염 원본을 Bronze Delta에 보존하고 Pandas로 AS-IS 진단.
② 기존 정화 코드와 C의 표준 사전으로 Silver를 구성.
③ C가 정의한 Gold 지표·AI 입력 데이터를 생성.
④ 각 레이어를 별도 MySQL 스키마에 적재하고 SQL·Pandas로 대조.
⑤ 검증된 Gold를 조회하는 API를 만든 뒤 A의 화면에 연결.

기존 C의 load_mysql.py는 원본 테이블을 DROP 후 재생성하는 방식이므로
이 실습에서는 실행하지 않습니다. 검증을 마친 뒤 적재 정책을 합의해 확장합니다.
