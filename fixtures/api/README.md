# B API 샘플

고정 C 인계본과 일치하는 실제 Delta를 GET API로 조회해 생성했다. 새 원본·덤프·비밀번호는 포함하지 않았다. `{fixture_source,request,response}`에서 response만 실제 API 응답이다. openapi.json은 OpenAPI 원문이다. 데이터 최종일2026-06-30, API1.0.0, C기준1.0.0. 신규 analysis는 미전달null이다.

health / stocks / daily / financials / evidence는 정상, missing_investor는 실제 수급 부재, invalid_date·unknown_stock은 실패 응답이다. 원본이 CSV이면 meta.source_backend/data_version은 달라질 수 있으나 업무값은 같아야 한다. JSON의 업무 숫자는 문자열이며 null과0을 구분한다. 전체 필드는 openapi.json을 따른다.

재생성은 B가 verify_http.py --fixtures <새출력폴더>로 수행하고 diff 후 반영한다. 고정 data/75파일을 출력 위치로 지정하지 않는다.
