# C 분석 실행·인수인계

버전: **c-gold-0.1.0**. C 구현·로컬 검사본이며 B의 DB/Delta/SQL 수신 검증과 A의 화면 검증은 아직이다. DB·API·예측 모델을 구현하지 않는다.

## 실행

저장소 루트, 검증 환경 Python 3.13.15. 기존 팀 환경이 있다면 버전 충돌을 확인하고 별도 가상환경을 사용한다. C에서 사용한 버전은 `analysis/requirements.txt`이며 B의 팀 공통 lockfile을 대체하지 않는다.

```bash
python3 -m venv build/c-venv
build/c-venv/bin/python -m pip install -r analysis/requirements.txt
build/c-venv/bin/python -m unittest discover -s analysis/tests -v
build/c-venv/bin/python -m analysis.run
```

기존 검증된 `.venv` 사용 시 `.venv/bin/python`으로 대체할 수 있다. 설치는 최초 한 번 필요하며 분석 실행은 외부 통신·API 키·DB 없이 동작한다.

기본 입력은 `data/03_C_integration_20261014`, 출력은 `build/analysis`다. 고정 인계본을 출력 위치로 지정하면 거부한다. 기존 `build/analysis`의 생성 결과는 같은 이름으로 갱신한다. 보존할 실험은 `--output build/analysis-run2`처럼 분리한다.

```bash
python -m analysis.run --output build/analysis-run2
python -m analysis.run --cleanup-zip /local/path/Bronze_Cleanup_20261014.zip
```


B API가 실행 중이면 C Gold와 API 값을 독립 대조할 수 있다(S4 C 수치 확인, [기록](../docs/handoffs/S4-C-check.md)). 외부 통신은 지정한 API 주소로만 한다.

```bash
python -m analysis.verify_api --gold build/analysis --base http://127.0.0.1:8000 --out build/s4-c-review/api_check.json
```

