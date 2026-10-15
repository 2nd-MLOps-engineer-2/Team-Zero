# B 실행 환경 계약 1.0

Windows x64 / Python 3.12.14 / MySQL Server 8.4.11(127.0.0.1:3306)에서 검증했다. 서비스 전체39개 의존성은 `backend/service/requirements.lock.txt`로 고정한다. 핵심 버전: Pandas3.0.1, PyArrow26.0.0, deltalake1.6.6(delta-rs), PyMySQL1.2.3, FastAPI0.143.1, Uvicorn0.54.0, httpx0.28.1, pytest9.1.1, openpyxl3.1.5. PySpark/Java는 실행하지 않았다. 실제 Delta 형식의 트랜잭션 로그·Parquet를 delta-rs로 쓰고 조회했다.

## 저장과 제공

오염 원본·정제 인계본 → Bronze Delta → 기존 정제/표준화·C 조인 → Silver Delta → 기존 C Gold Delta → MySQL 복제본 → GET API. Delta가 고정 스냅샷 기준이고 MySQL은 명시 타입·PK/FK의 서비스 조회용 복제본이다. MySQL 테이블 자체가 Delta 형식인 것은 아니다.

고정75파일은 저장소에 포함되어 CSV 모드로 팀원이 실행할 수 있다. 현재 PC만 보유한 오염 원본·ZIP·저장 API JSON·실제 Delta·DB덤프·venv·build는 추가 커밋하지 않는다. 전체 원본 재현에는 [입력·검증 인계](../docs/handoffs/G04-validation.md)의 입력이 필요하다. 기존 DB 이름 대신 `tz_<layer>_<runid>`를 사용해 보존한다. 새 준비 실행은 새run, 중단 재개는 해시·전체값 검증 후 기존run만 재사용한다.

## 설정

| 환경 변수 | 의미·기본 |
|---|---|
| TZ_PROJECT_ROOT | 저장소 루트(기본 코드 위치에서 계산) |
| TZ_DATA_BACKEND | auto / csv / delta / mysql |
| TZ_HANDOFF_DIR | 75파일 기준 디렉터리 |
| TZ_DELTA_RUN | catalog.json을 가진 고정run 폴더 |
| TZ_ANALYSIS_DIR | 향후 C의 manifest+CSV 묶음 |
| TZ_MYSQL_HOST / PORT / USER | 127.0.0.1 /3306 /root |
| TZ_CORS_ORIGINS | 허용 프론트 주소, 쉼표 구분 |

`.env`는 자동 로드하지 않는다. 비밀번호는 로컬 getpass 입력이 우선 사용법이다. TZ_MYSQL_PASSWORD도 지원하지만 문서·커밋·채팅에 저장하지 않는다. DB덤프/복원 자식 프로세스에는 일시 환경으로만 전달한다. 서비스 시작 시 각 원본의 전체값 해시를 확인하며 기존 데이터가 바뀌면 조용히 CSV로 우회하지 않는다.

전체 재현·중단 복구는 `backend/medallion_pipeline/README.txt`, 서비스 설치·실행·종료·검사는 `backend/service/README.md`를 따른다. `.cmd`는 Windows용이며 Linux/Docker 재현 검증은 수행하지 않았다. 로컬 서버는 기본127.0.0.1에만 바인딩하며 공유 서버·TLS·계정 권한·운영 배포는 이번 범위 밖이다.
