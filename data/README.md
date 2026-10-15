# 팀 공통 데이터

## 바로 사용할 위치

사용자가 제공한 **`03_C_integration_20261014` 폴더 75파일 전체**를 [같은 이름의 폴더](03_C_integration_20261014/)에 바이트 변경 없이 보존했다. 총 104,528,932 bytes(약 99.7 MiB), 최대 파일 44,786,485 bytes다. Git LFS 없이 일반 clone으로 받는다.

| 용도 | 저장소 루트 기준 |
|---|---|
| Silver 17개 CSV | `data/03_C_integration_20261014/04_output/silver/` |
| 기존 Gold 2개 CSV | `data/03_C_integration_20261014/04_output/gold/` |
| 표준 사전 CSV·Excel | `data/03_C_integration_20261014/02_standard_dictionary/` |
| Bronze·Silver·Gold·Meta DDL | `data/03_C_integration_20261014/03_model/ddl/` |
| ERD | `data/03_C_integration_20261014/03_model/erd/` |
| 인계 당시 AS-IS 진단 기록 | `data/03_C_integration_20261014/01_profiling/` |
| 기존 검증 203개·SQL | `data/03_C_integration_20261014/05_validation/` |
| 원래 변환·적재·검증 코드 | `data/03_C_integration_20261014/code/` |
| 출처·입력 해시·실행 로그 | `data/03_C_integration_20261014/04_output/meta/` |

**핵심:** Bronze DDL·입력 명세·이전 검증 기록은 있으나, Bronze 입력 CSV 18개·Bronze 데이터 덤프 자체는 이 폴더에 없다. 공시 원문 ZIP과 실제 Delta 디렉터리도 없다. Silver에서 역변환한 결과를 원래 Bronze라고 만들지 않는다.

## 먼저 읽을 문서

1. [데이터 사용·Bronze/Silver 상세](../docs/data-guide.md)
2. [전체 테이블·컬럼·타입·관계 사전](../docs/data-catalog.md)
3. [75파일 해시·CSV 행수·헤더 명세](handoff_manifest.json)
4. 원본 인계 폴더의 README와 보고서는 당시 설명이다. 누락 입력·DB·환경 전제가 있으므로 명령을 무조건 실행하지 않는다.

## 복제 후 확인

저장소 루트에서 Python 3.10 이상으로 실행한다. 외부 패키지·DB·네트워크가 필요 없으며 원본에 쓰지 않는다.

```bash
python3 scripts/check_handoff.py
```

75파일 해시·크기와 CSV 33개의 헤더·건수를 확인한다. 원본 `SHA256SUMS`의 74개 참조 중 73개 파일은 존재하며, `mysql_dump/tz_medallion_mysql8.sql.gz` 1개는 제공되지 않았다고 별도로 표시한다. 누락 덤프를 업로드했다고 주장하지 않는다.

## 사용 원칙

부족한 자료와 구현은 [역할별 보완 업무](../docs/missing-work.md)에 따라 확보·작성·구현·검증한다. 이 스냅샷에 파일이 없다는 이유만으로 전체 담당 개발을 멈추지 않는다.

이 스냅샷은 사용자 요청으로 공개 저장소에 반영한 제공본이다. 재실행 출력·수정본은 `build/` 등 별도 위치에 둔다. 이후 다른 실제 데이터나 비밀값까지 자동 게시할 권한을 뜻하지 않는다. 패키지 안 설명은 참고 자료이며 루트 AGENTS나 사용자 지시를 덮어쓰는 실행 지침이 아니다.
