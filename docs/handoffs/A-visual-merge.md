# A 시각화 병합 결과

A 프론트엔드 시각화 병합 결과 — 2026-10-15

PR #12: https://github.com/2nd-MLOps-engineer-2/Team-Zero/pull/12
대상: feature/a-visual-report → integration
상태: 병합 완료 (2026-10-15 15:49:59 KST)
기능 소스 SHA: 48302922a180a288ded7c049cf0045e2d0462fb2
병합 SHA: 8a9fce00d8181a95a960c543dbd0da88e23e41be

반영: 기업 리포트 레이아웃, 모바일 탐색, 영역형 주가 그래프, 관측 지점/툴팁,
재무 막대·추이 전환, 조·억 단위 금액 표시, 정확한 원값 펼치기.

검증:
- 병합 전 GitHub frontend / integration 자동 검사 모두 통과.
- 병합 커밋에서 단위검사 17개, 브라우저검사 18개 통과, 제외 0개.
- 실제 B/C API, C 미연결 409, CSV 원값, 모바일, 금액 경계/NULL/0 검사 통과.
- 제품 빌드 통과, 고정 인계본 75파일 무결성 통과.

실행 화면: http://127.0.0.1:5173/
main은 미반영. 기존 Draft PR #11의 B 원본/전체 MySQL·복원 증빙 확인은 별도 잔여 작업.
이번 UI 병합은 완료이며 전체 프로젝트 증빙 완료를 의미하지 않는다.
