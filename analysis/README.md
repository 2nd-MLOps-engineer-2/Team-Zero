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

`--cleanup-zip`은 선택이다. 개인 로컬의 **안쪽 정화 패키지 ZIP**을 읽고 원천 값·평가자 manifest·문서 내용을 내보내지 않는 집계 검사만 추가한다. 없는 경우에도 Silver/Gold 계산·차트·검사는 완료된다. 정화 코드를 재실행하거나 원본을 압축 해제하지 않는다.

## 생성 파일

| 파일 | 의미 |
|---|---|
| `g_fin_rpt_analysis.csv` | 320개 보고서와 원천 금액·비율·기간·검토 상태 |
| `g_stock_daily_analysis.csv` | 17,440 종목·일, 시점 실적·가격·수급·동행/괴리·보조 근거 |
| `schema.json` | 전체 컬럼·타입 제안·키·실제 빈값. B의 최종 DDL 합의 대상 |
| `samples.json` | 공개 인계본에서 계산한 소량 실제 예시. 큰 금액·비율은 문자열 |
| `validation.json` | Silver PK/FK·Gold 원천 대사·행/키/PIT 검사·입출력 해시·정화 집계(선택)·Silver 업무 규칙(`silver_rules`: SS02 통과/실패, SF04·SF06 발견 사항) |
| `std_gold_terms_proposal.csv`, `std_gold_words_proposal.csv` | C03 신규 Gold 컬럼 용어·단어 제안(기존 사전 재사용 표시). 원 표준 사전은 수정하지 않음 |
| `validation.json` 선택 항목(`--cleanup-zip`) | `original_asis`: C01·C02 최초 오염 결함 유형별 집계·명명·정상 결측, `sf04_review_documents`: REVIEW 행 원문 대조. 설명은 [asis-original.md](asis-original.md) |
| `rule_period_continuity.csv`, `rule_prior_ytd_restatement.csv` | SF04 누적 연속성 불일치·SF06 전년동기 재작성 차이 상세(MATCH 제외). 원문 대조 목록용 |
| `silver-profile.csv` | 현재 Silver 17테이블·260컬럼의 전체 행·빈값·고유값 수. 최초 오염 원본 진단과 구분 |
| `analysis-preview.png` | 실제 자료의 4패널 차트 시안. 그래프상의 금액 표시만 조 단위 변환 |

전체 출력 CSV는 Git 제외 `build/`에 생성한다. PR에는 코드·계약·집계 증빙·작은 예시·차트만 담는다. `analysis/evidence/`는 로컬 실행 당시의 검토용 출력이고 재생성 명령·해시로 대조한다.

## 재사용과 제한

기존 Gold 34컬럼을 기반으로 확장하되 Silver에서 **시점 보고서 선택·종가·TOP_LEVEL 수급을 독립 대조**한다. PIT 우선순위는 원래 `code/run_pipeline.py:pit_select`의 c-integration-1.0.0 정책을 명시적으로 재구현했다. 금융 금액과 비율은 Decimal로 계산하고 변동성·그래프 표현에만 float를 사용한다.

원천의 장기차입금 충돌 1건은 핵심 7지표와 다른 보조 지표다. 핵심 지표를 일괄 격리하지 않고 `review_required_yn`을 유지한다. 원문 XML 파싱 성공을 계정 매핑 해결로 해석하지 않는다. 기간 미검증 61건은 금액을 보존하고 관련 비율·비교는 `PRD_UNVERIFIED`로 둔다.

실제 Delta·DB 적재·SQL 대조는 B의 역할이며 이 결과만으로 F04/F05/G04/G05를 완료 처리하지 않는다. 원본 오염 ZIP이 없으므로 최초 오염본 전체·인코딩 결함 전수 진단 완료를 주장하지 않는다.
