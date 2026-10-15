# B 진행 기록 — 설호현 / 백엔드

2026-10-15 상태: **기존 C Gold 기반 Delta·MySQL·API·새덤프 복원 로컬 검증 완료 / A·C 수신 검증 대기**. 활성 경로는 기존 `backend/medallion_pipeline/`과 신규 `backend/service/`를 재사용한다. 예정 apps/api 등에 중복 구현하지 않았다.

선행 integration `b9b73a49bf169b17e3c324fcc9e51564d350b1ea`, 작업 feature/b-pipeline-api. 최종 전달 브랜치·SHA·원격 상태는 [S4](../handoffs/S4-B-to-A.md). 버전·설치·실행·종료는 [환경 계약](../../contracts/runtime.md)·[서비스 안내](../../backend/service/README.md), 전량 결과는 [G04](../handoffs/G04-validation.md).

| 작업 | 결과·증빙 | 남은 범위 |
|---|---|---|
| B01 | Python3.12,39패키지lock,Delta-rs/MySQL/API실행 | Spark미사용 명시,운영배포 별도 |
| B02~B03 / M01·M03·M05 | 실제오염91CSV/원본ZIP보존·프로파일링·A/B18입력해시·Bronze28Delta | 공시기간61보고서 C검토유지 |
| B04 / M06 | C사전·모델·DDL재사용,Meta11실제적재 | C의새분석모델미전달 |
| B05~B06 / M06·M08 | 기존정제·저장API복구·C변환 재실행,Silver17/371437행 | A지표매핑/B복구전변환기는전달본사용,수급1건유지 |
| B07 / M09·M11 | 기존Gold2Delta/17760행,신규C입력어댑터 구현·합성검사 | 신규분석Gold실제계산·적재는대기 |
| B08·B10·B11 | MySQL58테이블/32609487값,SQL87/Pandas599PASS,해시기반재개 | 새run/스냅샷증분운영은별도 |
| B09 / M12 | 비교·일별·재무·품질·근거·CSV·OpenAPI | A화면연결/C수치수신검증 |
| B12 / M04·M14 | 새덤프4/새DB4복원58전량PASS,API9MySQL비교PASS,문서·샘플 | 과거덤프미확보,AI규격/G05공동확인 |

M09의 B API/환경 계약은 구현했고 C계산/시각화 정의는 C가 작성한다. M11은 기존Gold 실제Delta/MySQL은 완료, 신규두테이블 실데이터 검증은 C입력대기다. M14의 B재현부분은 구현했으며 최종AI학습규격·화면대사까지 완료로 표시하지 않는다. 원본·새덤프·출력·비밀번호는 커밋하지 않는다. 기존75파일 SHA보존.

정확한 의미: NULL≠0, 수급단위주, 비율소수, 공시일<거래일, 당일제외, 기간/연결구분보존. 일별반복재무·기관합계와세부중복합산 금지. 기준일2026-06-30/20종목. 괴리분류·매매추천을 임의추가하지 않았다.

현재 PC에서 이미 DB적재는 끝났다. Workbench에127.0.0.1:3306으로 접속해 `backend/service/inspect_database.sql`을 실행한다. 서비스는 start_api.cmd 또는 start_mysql_api.cmd로 시작,Ctrl+C종료. 팀원PC는 CSV모드부터 사용한다. 새복원검증은 verify_mysql.cmd(로컬암호),기존DB는보존되며새검증DB가추가된다.


## S4 요청 대응 추가 (2026-10-15, 미커밋)

C전달6a61b13을 별도읽기스냅샷으로재현,18테스트/320·17440출력해시일치. B51테스트,CSV/Delta API각각C값1604320개전량대사,차트동일기준100·CSV추가,새C2Delta왕복PASS. S4에요청1~5·A계약차이·실제기대값·로컬ZIP을등록했다. 새C MySQL은미실행이며정식C reviewmerge/A실제연결/새전달SHA는미확인. 이번커밋·push·PR변경없음.
