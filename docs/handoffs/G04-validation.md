# G04 — B 저장·API·복원 검증 인계

2026-10-15 / B 로컬 실행 검증 완료, C 독립 대사·A 화면 대조 대기. 선행 origin/integration `b9b73a49bf169b17e3c324fcc9e51564d350b1ea`, B 작업 기준 `2b2f12b6b01dd59ae33f442d5659a82413f32718`. 전달 소스 SHA는 S4 기록에서 확인한다.

## 실제 입력·재현 범위

로컬 원본 경로는 run_config.json의 project/raw로 받는다. 저장소 고정75파일 외에 오염 원본 ZIP, 정제 패키지, 검증된 A ZIP, B 입력·저장 API JSON270개, 실제 공시 문서 자료를 확보해 실행했다. 입력18개의 크기·행·헤더까지 갖춘 표는 `build/b_handoff_20261015/input_manifest.csv`다. 파일별 출처·해시는 아래 로컬 증빙에 있고 새로운 원본/덤프는 Git에 추가하지 않았다.

- `backend/medallion_pipeline/runs/20261015_101647_d567/evidence/input_manifest.json`: A7/B11 입력18개, 이름·SHA.
- 같은 run의 `catalog.json`: 전체 타입·키·행수·값 해시·Delta버전·원천/코드 해시.
- `profiling/`: 최초 오염91개CSV의 Pandas진단. `evidence/cleanup_replay/`: 정제 재실행. OpenDART는 제공 변경 명세 before/after 일치 기반107846셀 복원. Toss741격리 후 저장 API근거740복원,1건 유지.
- `evidence/handoff_lineage.json`, `validation/B_clean_source_lineage.json`: A상세66729행 원천 대사, B사업값959059개 불일치0. A 지표 매핑기 전체와 B 복구 전 변환기는 새로 실행한 것이 아니라 전달본을 검증해 사용했다.
- `dictionary/`, `sql/`: 표준 단어·용어·도메인·코드·명명규칙·모델·DDL·검증SQL. C 기존19개CSV를 재현하고 SHA 일치.

과거 MySQL 덤프는 확보하지 않았다. 아래 덤프는 이번 실행으로 새로 만든 버전이다. 기간 미검증61보고서·선택 계정빈값2202·계정충돌1·수급 검토247540/2026-04-16은 원래 상태를 유지한다. A의 수정된 펼친 요약CSV 대신 해시가 일치하는 ZIP 인계본을 사용했다. Silver에서 오염 원본을 역생성하지 않았다.

## 저장 검증

| 레이어 | 실제 Delta/MySQL 테이블 | 행수 |
|---|---:|---:|
| Bronze |28|1592478|
| Silver |17|371437|
| 기존 Gold |2|17760|
| Meta |11|1527|

모든 Delta는 version0, 실제 `_delta_log`·Parquet·전량 재조회 증빙이 있다. MySQL 서버8.4.11, 검증58테이블/32609487값/SQL87검사 PASS. Pandas599검사 PASS. 기존 Gold17440일별행 가운데 재무연결15833,미연결1607. 보고서320,재무상세66729,표준기간별지표30080. Meta는 사전스냅샷7+정의형4테이블이다.

증빙: run의 `validation/delta_summary.json`, `pandas_summary.json`, `mysql_validation.json`, `meta_checks.json`. 기존 데이터·DDL 삭제 없이 새run DB를 사용했다. 중단 재개는 이미 완료된 테이블도 전량 검증하고 같을 때만 건너뛴다. MySQL 원본 DB는 `tz_bronze_20261015_101647_d567`, `tz_silver_20261015_101647_d567`, `tz_gold_20261015_101647_d567`, `tz_meta_20261015_101647_d567`.

## 실제 MySQL API·덤프 복원

사용자가 로컬 비밀번호를 입력해 실행했으며 B가 결과 JSON을 직접 확인했다. 증빙 폴더는 **Team-Zero**의 `build/mysql_operations/20261015_112252_60d6`이다.

- `api_mysql_validation.json`: 기업·일별·재무·품질·근거·CSV 포함9개 응답이 CSV와 PASS. 이전 두 실행에서 드러난 issue/재무CSV 정렬 차이를 수정하고 재검사했다. 원본 물리 행 순서와 관계없이 동일 응답을 제공한다.
- `backup_restore_validation.json`: 신규덤프4개 → 새복원DB4개 → 58테이블 모든값의 canonical SHA 일치 PASS. 원래 DB는 보존했다.
- 대상: `tz_restore_bronze_20261015_112252_60d6`, `tz_restore_silver_20261015_112252_60d6`, `tz_restore_gold_20261015_112252_60d6`, `tz_restore_meta_20261015_112252_60d6`.
- dump gzip크기: Bronze52247327 /Silver10484596 /Gold979294 /Meta36424바이트. 각 SHA는 보고서에 기록했다. 덤프·비밀번호는 Git 미포함.

서비스 자동검사와 실제HTTP의 최신 증빙 경로·개수는 S4 기록에 적는다. 실행 명령은 `backend/service/README.md`. 검증용 API는 읽기 전용, 덤프는 새DB만 만들며 기존DB 대상 복원은 거부한다. 계정 root는 현재 로컬 시험용이다.

## C/A가 별도로 확인할 내용

C는 본인 계산 HEAD에서 같은20종목/기간으로 지표·기간·NULL·수급 단위를 대사한다. 기존599PASS를 신규분류 계산의 성과로 쓰지 않는다. 신규320/17440분석 Gold 및계약은 아직 없다. B는 계산을 대신 만들지 않았으며 전달 어댑터의 합성 경계만 검사했다.

A는 삼성전자005930/2026-06-30과 수급미제공247540/2026-04-16로 API→화면→CSV를 대조한다. 현재 API 반환값·CSV·DB는 검증했지만 화면·브라우저 검증은 A가 수행해야 한다. G05/S5/AI최종특징·시계열분할 완료는 아직 주장하지 않는다.
