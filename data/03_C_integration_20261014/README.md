# C 담당 통합·품질 패키지: 03_C_integration_20261014

TEAM ZERO 실버 단계 C 담당(통합·실행·공통 품질 관리)의 결과물입니다.
A(`02_C_handoff_20261014`)와 B(`Team_B_Silver_Handoff` v1.1.0) 인계본을 입력으로 받아 다음 작업을 했습니다.

1. AS-IS 프로파일링(Pandas)
2. AI 데이터 표준 사전 구축
3. Medallion(Bronze→Silver→Gold) TO-BE 모델 설계와 MySQL 구현
4. 변환·적재·검증(SQL·Pandas)

**결과 요약:** 검증 203개 항목 전부 PASS. 명명 표준 준수율 AS-IS 2.92% → TO-BE 100%. 도메인·코드 규칙 위반 0건. 재실행 시 결과 해시 동일.

## 읽는 순서

1. `06_report/C_통합품질_보고서.pdf`: 전체 보고서(미해결 사항·다음 업무 포함). docx·md 원본도 있습니다.
2. `03_model/erd/`: 메달리온 흐름, 개념·논리·물리 ERD. 크게 볼 때는 SVG를 여세요.
3. `02_standard_dictionary/AI_데이터_표준사전.xlsx`: 표준 단어·도메인·코드·용어(컬럼)와 AS-IS→TO-BE 대응.
4. `05_validation/validation_results.csv`: 검증 결과 203개 항목. SQL 결과와 Pandas 결과가 나란히 있습니다.
5. `04_output/gold/g_ai_stock_daily.csv`: AI 학습용 데이터셋(17,440행).

## 폴더

| 폴더 | 내용 |
|---|---|
| `01_profiling/` | AS-IS 컬럼·테이블 프로파일, 5개 축 23개 진단 지표 |
| `02_standard_dictionary/` | 표준 사전 CSV 7종 + 엑셀 통합본 |
| `03_model/ddl/` | MySQL 8.0 DDL: `00_databases` `01_bronze` `02_silver` `03_gold` `04_meta` |
| `03_model/erd/` | ERD 4종(PNG·SVG·DOT) |
| `04_output/silver/` | Silver 표준 테이블 17개(A·B 표준화 13개 + C 통합 4개) |
| `04_output/gold/` | `g_ai_stock_daily`, `g_fin_rpt_mkt_smry` |
| `04_output/meta/` | 입력 파일 목록·해시, 실행 기록(`m_exec_log`) |
| `05_validation/` | 검증 결과·요약·실행 SQL·컬럼별 표준 준수 상세 |
| `06_report/` | 보고서(pdf·docx·md)와 그림 |
| `mysql_dump/` | 4개 DB(`tz_bronze`·`tz_silver`·`tz_gold`·`tz_meta`) 덤프. 용량 때문에 `03_C_integration_20261014_mysql_dump.zip`으로 따로 전달합니다. 같은 위치에 풀면 이 폴더 안으로 들어갑니다 |
| `code/` | 실행 코드 |

## 다시 실행하기

준비물은 Python 3.10 이상, `pip install pandas openpyxl pymysql`, MySQL 8.0.16 이상입니다(CHECK 제약 필요). ERD를 다시 그리려면 Graphviz도 있어야 합니다.

A·B 인계 폴더를 이 폴더와 같은 위치에 풀어 두면 경로를 따로 지정하지 않아도 됩니다.

```
작업폴더/
├─ 02_C_handoff_20261014/      (A 인계)
├─ Team_B_Silver_Handoff/      (B 인계)
└─ 03_C_integration_20261014/  (이 패키지)
```

다른 위치에 있으면 각 명령에 `--a-dir`·`--b-dir`를 붙이거나 환경변수 `TZ_A_DIR`·`TZ_B_DIR`를 지정하세요.

```bash
cd 03_C_integration_20261014
python code/profile_asis.py                       # 1) AS-IS 진단 → 01_profiling
python code/run_pipeline.py                       # 2) 표준 적용 → 04_output (Silver·Gold·품질이슈·실행기록)
python code/build_model.py                        # 3) 표준 사전·DDL·ERD → 02, 03
python code/load_mysql.py --user root --password ****            # 4) MySQL 적재
python code/validate.py   --user root --password **** --rerun    # 5) 검증 + 재실행 일관성 → 05_validation
```

DB만 복원하려면 이렇게 하세요. 기존 `tz_*` DB를 덮어씁니다.

```bash
gunzip -c mysql_dump/tz_medallion_mysql8.sql.gz | mysql -u root -p
```

## 지킨 원칙

- A·B 인계본은 수정하지 않았습니다(읽기 전용).
- 식별자는 문자열로 다뤄 선행 0을 보존했습니다. 금액은 Decimal로 처리했습니다(float 미사용).
- 빈값은 NULL로 두었고, 0 대체나 보간은 하지 않았습니다.
- 가격·수급은 내부조인하지 않았습니다. 키 합집합으로 연결 상태를 기록했습니다.
- 시점 조인 조건은 공시일 < 거래일입니다. A의 `join_daily_for_c.py` 결과와 17,440행 전부 일치합니다.
- 결과는 덮어쓰기 방식이라 재실행해도 중복이 생기지 않습니다. 실행 기록만 누적됩니다.
- 표준 정의는 `code/std_dictionary.py` 한 곳에만 있습니다. 여기를 고치면 사전·DDL·ERD·검사가 함께 바뀝니다.
