TEAM ZERO / B 담당 Medallion 백엔드

무엇을 하는가
  오염 원본 ZIP을 그대로 복사하고, CSV를 Pandas로 진단한 뒤 원본 값 보존용
  Bronze Delta를 만든다. 기존 정제 코드를 새 폴더에서 재실행하고 과거 정제본과
  해시를 비교한다. B의 저장 API 원문 복구도 재현한다. A는 ZIP 내 검증된 인계본을
  사용하며, 재무 상세 66,729행을 재실행한 정제본과 직접 비교한다.
  C의 표준화/조인 코드를 새 출력 폴더에서 재실행하고 17 Silver / 2 Gold를
  실제 Delta 테이블로 저장한다. 기존 C 결과 19개 CSV의 해시와 대조한다.
  그 후 MySQL은 CSV가 아닌 Delta의 고정 버전에서 읽어 새 DB에 적재한다.

실행
  1. start_mysql.cmd를 더블 클릭한다.
  2. Delta 파일 검사가 끝나고 MySQL password가 나오면 root 비밀번호를 입력한다.
     입력 중 글자나 별표가 표시되지 않는다. 입력 후 Enter를 누른다.
  3. SUCCESS가 나오면 완료. 보고서는 실행 폴더 validation/mysql_validation.json.
     중간에 실패하면 같은 파일을 다시 실행한다. 완료 테이블은 값 검증 후 건너뛴다.
     아직 적재되지 않은 테이블만 트랜잭션으로 적재한다.

접속 정보
  root / 127.0.0.1 / 3306. 비밀번호는 저장하지 않는다.
  tz_bronze_<실행ID>, tz_silver_<실행ID>, tz_gold_<실행ID>, tz_meta_<실행ID>를 만든다.
  기존 tz_demo, tz_bronze, tz_silver, tz_gold 등은 수정하지 않는다.
  이번 실행이 생성한 DB라는 소유 기록이 없으면 기존 DB 사용을 거부한다.

파일 위치
  LATEST_RUN.txt: 준비된 실행 폴더
  runs/<실행ID>/delta/{bronze,silver,gold,meta}/: Delta 테이블
    각 테이블에 _delta_log/와 Parquet 파일이 실제로 존재한다.
  exports/silver/*.csv, exports/gold/*.csv: 재실행한 C 결과 CSV
  raw_archives/: 원본 ZIP의 바이트 보존 사본
  profiling/: 실제 오염 원본 91개 CSV의 Pandas 진단
  evidence/cleanup_replay/: 정제 재실행, 격리, 복원 근거 및 검증
  evidence/B_api_merge_replay/: 저장 API 기반 B 복구 재실행
  dictionary/: 단어·용어·도메인·코드·명명 규칙·컬럼 매핑 CSV/XLSX
  Meta Delta/MySQL: 표준 사전 원문 스냅샷 7개와 물리 모델에 따른 표준 메타 4개
    m_exec_log, m_std_word, m_std_dmn, m_std_term을 실제 정의된 타입과 기본키로 생성한다.
  sql/: 새 DB용 DDL과 검증 SQL
  catalog.json: 테이블·버전·행 수·스키마·전체 값 해시·원천 해시
  validation/pandas_summary.json: Pandas 검증
  validation/delta_summary.json: Delta 준비 결과
  validation/mysql_validation.json: 실제 MySQL 적재 후 생성되는 검증 결과

핵심 모델과 조인
  s_corp / s_stock / s_corp_stock_map: 기업과 종목 기준 정보
  s_fin_rpt: 기업 × 사업연도 × 보고서 × 연결/별도 보고서 헤더
  s_fin_mtrc: 보고서 × 표준 재무지표 × 기간 유형
  s_fin_item: 원본 계정 상세, 당기·전기·누적·전전기 금액 모두 보존
  s_stock_daily_prc: 종목 × 거래일
  s_invstr_trd_daily: 종목 × 거래일 × 투자자 유형
  s_conn_stts / s_dq_issue: 결측·연결 상태·검토 사유

  주가+수급: stock_cd, trd_dt로 연결한다. 11종 투자자 행은 먼저 피벗한다.
  TOP_LEVEL 기관 값과 기관 세부 7종을 동시에 합산하지 않는다.
  순매수 단위는 원이 아니라 주이다.
  기업+재무: corp_cd와 fin_rpt_id로 연결한다.
  일별 재무: dscl_dt < trd_dt인 공개 보고서 중 최신 사업기간을 선택한다.
  같은 날 공개된 보고서는 그날 거래에 사용하지 않는다.
  연결 우선 규칙과 보고서 종류/기간 구분을 유지한다.

Gold 결과
  g_ai_stock_daily: 종목·거래일별 가격, 수익률, 수급, 재무를 연결한 분석 기반
  g_fin_rpt_mkt_smry: 보고서별 기간 가격 변화와 누적 수급을 요약한 분석 기반
  공시 이전 일별 특징과 같은 회계기간 사후 비교는 사용 목적이 다르다.
  보고서 기간 요약은 당시 투자 의사결정에 쓸 수 있는 PIT 특징으로 취급하지 않는다.

현재 범위와 해석
  - 최초 오염 원본은 수정하지 않는다. Bronze는 오염 값도 그대로 보존한다.
  - b_raw_*는 오염 원본, b_a_*와 b_b_*는 이미 정제된 팀 인계 계약의 스냅샷이다.
    인계 스냅샷을 최초 오염 원본이라고 부르지 않는다.
  - OpenDART는 제공된 before/after 변경 명세의 after 일치를 확인하고 before로 복원한다.
    오염 전 원본 ZIP 자체를 받은 것은 아니므로 원본 ZIP 전체 바이트 복원을 주장하지 않는다.
  - Toss의 사라진 가격 등은 추정하지 않는다. 정제에서 741행을 격리하고,
    B가 저장한 API 근거로 740행을 복구한다. 1행 수급은 검토 대기 상태로 남는다.
  - A 재무 지표 매핑기와 B API 복구 전 변환기 전체는 이번에 다시 실행하지 않는다.
    A/B 전달본 해시, A 상세의 원천 일치, B 저장 API 복구 재현을 검증한다.
  - Delta는 delta-rs로 만든 실제 Delta 형식이다. Spark를 실행한 것은 아니다.
  - MySQL은 Delta의 분석/서비스 조회용 복제본이다. MySQL 자체가 Delta 테이블인 것은 아니다.
  - NULL을 0으로 채우지 않는다. 정상적인 선택 항목 빈값과 오염 결측을 구분한다.
  - 현재 Gold는 C 통합본을 재현한 분석 기반이다. 동반 개선/괴리 판정, 전년 동기 변화,
    학습 목표·시계열 분할·최종 학습 대상 선정은 별도 분석 규칙 확정이 필요하다.
  - C 기간 요약의 full_cvrg_yn은 전역 가격 범위 기준이다. 개별 종목·수급의 모든
    거래일이 완전하다는 의미로 해석하지 않는다.
  - MySQL 적재 완료는 mysql_validation.json의 status=PASS로 확인한다.
    delta_summary.json만 존재하면 Delta 준비가 끝난 것이며 DB 적재는 아직 대기 상태이다.

재현 명령 (프로젝트 루트에서 실행하는 경우)
  backend\medallion_pipeline\.venv\Scripts\python.exe backend\medallion_pipeline\prepare.py
  backend\medallion_pipeline\.venv\Scripts\python.exe backend\medallion_pipeline\verify_prepared.py

환경 구성
  requirements.txt에 필요한 버전을 고정했다. 이번 PC에서는 기존 데모의 Delta/PyArrow/
  PyMySQL과 Codex Python의 Pandas/openpyxl을 읽어 쓰는 별도 venv를 준비한다.
  다른 PC에서는 Python 3.12 가상환경에 pip install -r requirements.txt로 설치한다.
  입력 프로젝트/원본 경로는 prepare.py --project, --raw로 바꿀 수 있다.
  준비 도중 중단된 경우 --resume runs\<실행ID>로 재개할 수 있다.
  재개 시 원본/정제 해시와 기존 Delta의 모든 값을 다시 비교하고 일치할 때만 재사용한다.

원본 코드의 출처
  vendor/common.py, std_dictionary.py, run_pipeline.py, build_model.py:
    C의 03_C_integration_20261014/code (변환·사전·모델 함수 재사용)
  vendor/clean_bronze.py: Bronze_Cleanup_20261014/05_code
  vendor/merge_recovery.py: Team_B_Silver_Handoff/code
  기존 C load_mysql.py는 사용하지 않는다. 새 mysql_load.py는 기존 DB 삭제 없이 적재한다.
