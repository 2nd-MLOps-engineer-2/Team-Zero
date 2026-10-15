# C S4 수정 — 실패 종료 코드

기준 `review/s4-c-v1` / `37e54515b340f6000ef523a788ca3a05a4a5a1e8`. 수신 검토 대기, 기능/공유 브랜치 병합 아님.

`python -m analysis.verify_api`가 JSON의 전체 판정 PASS이면 0, FAIL이면 1로 종료한다. Gold 읽기 예외도 기존대로 FAIL JSON을 보존한 뒤 1로 종료한다. API·계산값·CSV 바이트 비교 정책은 바꾸지 않는다. 따라서 현재 일별 CSV 해시 불일치는 여전히 FAIL이며 이제 종료 코드도 1이다.

실제 CLI 검사는 로컬 합성 HTTP 서버를 사용한다. PASS, 값 불일치, Gold 파일 부재, 연결 실패를 각각 별도 프로세스로 실행해 JSON과 종료 코드를 확인한다.

```bash
.venv/bin/python -m unittest discover -s analysis/tests -v
```

실제 B API·MySQL·Delta·A 브라우저 검사는 별도다. 이번 수정만으로 기존 S4 수신·G04·G05 전체를 완료 처리하지 않는다. 이전 증빙 파일은 당시 실행 기록으로 보존한다.
