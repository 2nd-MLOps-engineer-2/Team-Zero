# S3 C → A 차트 의미·실제 계산값 수신 검토

2026-10-15 / A 이어진 / **A 차트 의미 확인 및 C 실제 계산값 화면·CSV 대조 완료. B 저장/API 및 G05 전체는 미확인.**

| 항목 | 값 |
|---|---|
| C 전달 PR | https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/4 |
| C 검사 대상 SHA | fb1f802c88e2d5b275c737200aa392deac0e628b |
| A 시작 HEAD | 4459054464381329b369b64c48c7407fe08ec802 |
| A 수신 브랜치 | review/s3-a-v1 |
| 병합 직후 HEAD | 0b3cb61dc4e6842247423dda3bf1303e1621a142 |
| 충돌 | 없음, A/C integration-status 변경 자동 병합 |
| 데이터/계산 | 03_C_integration_20261014 / c-gold-0.1.0 |
| 외부 통보 | 별도 메시지 없음. A PR #5의 문서로 전달 |

A 작업 HEAD에서 별도 review를 만들고 C의 고정 SHA를 정상 merge했다. C 브랜치로 단순 이동하여 A 화면 없는 상태를 검사하지 않았다. C 코드·고정 인계본을 수정하지 않았다.

## 재현

Python 3.13.15의 build/a-c-review-venv에 analysis/requirements.txt 설치: pandas 3.0.6 / numpy 2.5.4 / matplotlib 3.11.2. 설치 완료 전 첫 실행은 matplotlib 미설치로 차트 단계 실패했으며 설치 완료 후 같은 명령 재실행으로 해소했다.

```
build/a-c-review-venv/Scripts/python.exe -m unittest discover -s analysis/tests -v
build/a-c-review-venv/Scripts/python.exe -m analysis.run --output build/a-c-review-output
python apps/web/scripts/prepare-c-review.py --c-output build/a-c-review-output --output build/a-c-review-bundle.json
```

- C 테스트 18/18 PASS. 재무 320 / 일별 17,440행, checks PASS.
- g_fin_rpt_analysis.csv SHA256: 4514982c57d1de11ba0cee6899e114d229d730d96c12ea0e17703255a6fcd22b.
- g_stock_daily_analysis.csv SHA256: a094a995d44fd8b8fe73045e8a51ce4e4b6eadff6e9d42feba9cb897b0470707.
- 두 해시 모두 C analysis/evidence/validation.json과 일치.
- 고정 75파일 무결성 검사 PASS. 선택 cleanup ZIP은 없으므로 원본 오염/원문 추가 대사 미실행.

## A 의미 검토·수정

C 시안과 계약을 읽어 사분면, 20관측 수급 비율, 상태 문구와 joint_improve 구분을 추가했다. 가격 기준은 조회 첫 관측일로 수정(합성값만 미리 계산), 재무 축은 prd_end_dt로 수정했다. 비율 문자열과 빈 문자열/null을 처리하고 원문을 보존한다.

API가 아직 없으므로 C 재생성 출력의 종목/일별/재무/근거를 테스트 응답으로 주입했다. 가격 기준값은 C 원본에 없는 필드이므로 null로 두었으며 실제 주가 정규화 검증 완료로 주장하지 않는다. A 업무 계산 없음.

실제 사례: 005930 / 2026-06-30 / report_76a18cf53ffa7baf9975a0d8.

| C 원값 | 화면 | CSV |
|---|---|---|
| rev_ytd_amt 333605938000000 | 333,605,938,000,000 원 | 원문 유지 |
| rev_yoy_rt 0.10880093 | 10.88 % | 원문 유지 |
| event_excess_rt 0.32769823 | 32.77 %p | 원문 유지 |
| frgn_flow_20d_rt -0.06459243 | -6.46 % | 원문 유지 |
| joint_improve_yn N | 조건 미충족 | 원문 유지 |

A npm test 12개, build, C_REVIEW_BUNDLE을 지정한 Chromium 브라우저 12개 검사. 캡처 apps/web/test-results/c-actual-review.png(로컬 생성). CI 기본 검사는 실제 C 입력 없이 해당 1개만 명시적 skip, 나머지 11개 실행.

## B에게 남은 정확한 입력

S4 고정 브랜치·SHA·실행법·실제 API 응답, endpoint/쿼리/인증/CORS 계약, 동일 기준일 가격·시장 정규화, 보고서/공시/단위·상태·출처 필드, 실제 CSV export를 요청한다. A API 표현안은 contracts/A-screen.md. C 금액·비율·상태를 바꾸지 않는 B 응답이 필요하다.

이 수신 확인은 A의 차트 의미와 실제 C 값 표시 범위만 해당한다. B Delta/MySQL/SQL 대사·전체 원본 대사·실제 API·S5/main 반영은 완료하지 않는다. C 구현 전체의 타 역할 수신 승인으로 사용하지 않는다.
