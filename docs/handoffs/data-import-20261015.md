# 데이터 공통 인계 — 2026-10-15

## 준비된 것

사용자가 지정한 `03_C_integration_20261014` 75파일을 `data/03_C_integration_20261014/`에 바이트 그대로 보존했다. 새 `data/handoff_manifest.json`이 실제 제공 범위를 고정한다. Git clone으로 실제 Silver·Gold·사전·DDL·ERD·코드·보고서·기존 검증을 받는다.

## 직접 수행한 확인

| 검사 | 결과·범위 |
|---|---|
| 원본 폴더→복사본 | 75파일, 104,528,932 bytes, 해시·크기 일치 |
| `python3 scripts/check_handoff.py` | 75파일, CSV 33개 전체 헤더·행수 일치 |
| 원래 `SHA256SUMS` | 존재하는 참조 73개 일치. 덤프 참조 1개는 미포함으로 별도 표시 |
| Silver 전체 CSV + DDL PK | 17테이블, 371,437행, 중복 초과 행 0 |
| Silver DDL FK | 선언 관계 15개, 비어 있지 않은 값의 참조 실패 0 |
| 기존 일별 Gold 날짜 검사 | `dscl_dt >= trd_dt` 위반 0 |
| `python3 -m unittest discover -s scripts/tests -v` | 2개 테스트 통과. 손상·누락·행수 변경·추가 파일·한글 정규화·빈 CSV 검사 |
| 가져온 Python 코드 | import·DB 실행 없이 모든 `.py` 구문 확인 |
| 작성 문서 | 상대 링크 존재, 데이터 행·컬럼 합계 확인 |

기존 `05_validation` 203 PASS는 과거 기록이다. 이번에 MySQL 복원·SQL/Pandas 203개 재실행·Delta 저장·API·화면 검사는 하지 않았다. 무결성 검사 통과는 향후 기능 검증 완료를 뜻하지 않는다.

## 역할별 다음 행동

- A: 저장소의 `s_stock`·Gold·표준 사전으로 실제 기간·단위·NULL을 확인하고 API·화면 계약을 구체화한다. API가 없는 동안은 샘플 응답임을 표시한다.
- B: 제공 CSV·DDL·기존 코드를 재사용 검토해 저장·조회·API와 실제 Delta Silver/Gold를 준비한다. 원래 `load_mysql.py`는 A/B 입력·DB와 파괴적 DDL을 전제하므로 무조건 실행하지 않는다.
- C: 저장소 Silver·Gold로 지표·현금흐름·기간·시점·차트 작업을 시작한다. 원래 `std_dictionary.py`, `pit_select`, `build_gold`의 정책을 확인하고 고정 원본을 수정하지 않는 활성 코드로 확장한다.

## 빠진 입력·열린 항목

Bronze의 A/B 입력 원본 18개, 최초 오염 원본·명세서의 전체 증빙, 공시 원문 ZIP, 별도 MySQL 덤프, 실제 Delta 테이블·로그는 이번 제공 범위에 없다. C 관점 AS-IS와 최초 교환 오염 원본을 혼동하지 않는다. Silver/Gold 파일을 다시 요청하지 않고 빠진 입력이 필요한 작업만 요청한다.

원래 인계본의 재무 기간 미검증 61건, 수급 검토 키 1건, CFD 범위 부재, 재무 상세 빈값·지표 충돌·OPEN 등은 자료 업로드로 해결되지 않는다. [데이터 안내](../data-guide.md)와 [체크북](../workbook.md)에 따라 유지·검증한다.
