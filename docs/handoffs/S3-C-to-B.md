# S3 — C Gold 계산을 B 실행·저장에 전달 (A는 차트 의미 확인)

**상태: 작업 중 — C 로컬 구현·검사 완료, 전달 브랜치·PR 미생성.** [절차](../integration-workflow.md) · [진행표](../integration-status.md).

## 전달 요약

| 항목 | 실제 값 |
|---|---|
| 단계·회차·대상 | S3 v1 / C06~C09·C11, G01·G04(C 측), M07·M09·M10·M14(C 범위) |
| 전달자 → 수신 확인자 | C 김형준 → B 설호현(실행·저장·SQL 대조), A 이어진(차트 의미) |
| 상태 | 작업 중. 수신 확인 없음 |
| PR base·선행 integration SHA | `integration` / `1971dcb`(origin/main=integration, 2026-10-15 fetch) |
| 전달 원격 브랜치·전체 SHA·PR URL | 미등록 — 예정 `handoff/s3-c-to-b-v1` |
| 데이터·계약·계산 버전 | `03_C_integration_20261014`(75파일 PASS) / [contracts/analysis.md](../../contracts/analysis.md) 제안 / `c-gold-0.1.0` |
| 포함 범위 | `analysis/`(gold·rules·asis·audit·standards·run·tests·sql·evidence), `contracts/analysis.md`, `contracts/visualization.md` |
| 제외 범위 | 원천 오염·정화 ZIP, 평가자 정답 이력, 전체 Gold CSV(재생성 대상), DB·Delta·API |

## 바로 실행할 방법

- Python 3.13.15, `analysis/requirements.txt`(pandas 3.0.6·numpy 2.5.4·matplotlib 3.11.2). B의 공통 lockfile을 대체하지 않는다.
- 입력: 저장소 고정 인계본(읽기 전용). 선택 입력 `--cleanup-zip`은 개인 로컬 안쪽 `Bronze_Cleanup_20261014.zip`, 없으면 C01·C02·원문 대조만 빠진다.
- 원본·DB 변경 없음. 출력은 `build/analysis/`(Git 제외).

```bash
python3 -m venv build/c-venv
build/c-venv/bin/python -m pip install -r analysis/requirements.txt
build/c-venv/bin/python -m unittest discover -s analysis/tests -v
build/c-venv/bin/python -m analysis.run
```

기대값: 테스트 18개 OK, `{"rows": {"financial": 320, "daily": 17440}, "checks": "PASS"}`, 출력 Gold SHA-256 `g_fin_rpt_analysis.csv` `4514982c…d22b`, `g_stock_daily_analysis.csv` `a094a995…0707`(전체는 `analysis/evidence/validation.json` `output_sha256`).

## 전달자 검사 (C, 로컬, 실제 공개 인계본)

| 검사 | 결과 |
|---|---|
| Silver 17테이블 PK·FK(DDL 기준) | 위반 0 |
| Gold 행·PK, PIT(공시일<거래일), 원천 종가·TOP_LEVEL 대사, 기존 일별 Gold와 시점 보고서 일치 | PASS |
| SS02 기관 합계 = 세부 7유형 합 | 17,439/17,439 |
| C08 `g_fin_rpt_mkt_smry` 1:1 연결, 부분 커버리지 값 없음 | PASS (320, 전체 커버리지 240) |
| SF04 누적 연속성 / SF06 재작성 (발견 사항) | REVIEW 20행(보고서 11) — 원문 있는 11행 모두 원문 일치 / 매출 32·영업이익 38·순이익 13 |
| 정화 총계 대조 6항목, 최초 오염 결함 유형 집계 | PASS, [asis-original.md](../../analysis/asis-original.md) |
| 재현성 | 같은 입력에서 Gold CSV·schema·samples·profile·차트 바이트 동일 재생성 |

미실행: MySQL·Delta·API·화면. 기존 203 PASS와 별개다.

## B가 합친 뒤 확인할 것

- [ ] B 작업 HEAD에서 `review/s3-b-v1` 생성 후 전달 SHA merge, 위 명령으로 같은 행 수·출력 SHA-256 재현.
- [ ] 두 Gold를 Delta·MySQL에 저장하고 `analysis/sql/reconcile.sql` 실행 결과를 C 기대값과 대조(G04): 행 수, PK 중복 0, PIT 위반 0, 매출 성장률 불일치 0, 금액 합계.
- [ ] `schema.json`의 제안 타입(금액 DECIMAL(21,0), 비율 DECIMAL(18,8))과 DDL 차이, NULL ↔ 빈 문자열 처리를 기록.
- [ ] 상태 코드(`*_stts_cd`)·`review_required_yn`을 저장 과정에서 바꾸지 않음.

## A가 확인할 것

- [ ] [contracts/visualization.md](../../contracts/visualization.md)의 축·단위(%, %p, 조 원 표시)·툴팁·분석 불가 문구와 `analysis/evidence/analysis-preview.png` 시안이 화면에 표현 가능한지.

## 수신자 확인

수신자 브랜치/HEAD, 반영 SHA, 실행 결과, 충돌·계약 차이, 판정(미확인 / 수정 필요 / 수신 확인 완료), 확인자·일시: **미등록**.

## 병합 후 보고

integration 병합 PR·SHA, 남은 일: **미등록**. 남은 C 입력: 원문 없는 보고서 61건(R2, SF04 미판정 5건 포함), 오염 ZIP 실물(파일 수준 결함 직접 측정, 선택).
