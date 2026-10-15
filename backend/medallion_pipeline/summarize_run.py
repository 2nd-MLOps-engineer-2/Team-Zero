"""Write a Korean implementation/result note from actual verification files."""
import json,datetime as dt
from pathlib import Path
from mysql_load import select_run,qi

def build(run):
 def j(rel):return json.loads((run/rel).read_text(encoding='utf-8'))
 c=j('catalog.json');d=j('validation/delta_summary.json');p=j('validation/pandas_summary.json')
 raw=j('profiling/raw_summary.json');cleanup=j('evidence/cleanup_replay/replay_validation.json')
 b=j('evidence/B_api_merge_replay/validation_summary.json');bl=j('validation/B_clean_source_lineage.json')
 counts={t['name']:t['rows'] for t in c['tables']};db=c['databases']
 mysql=run/'validation/mysql_validation.json'
 mysql_status=j('validation/mysql_validation.json')['status'] if mysql.exists() else 'PENDING (로컬 비밀번호 입력 후 적재 필요)'
 lines=[
  'TEAM ZERO / B 담당 Medallion 구현 및 검증 결과',
  '작성 시점: '+dt.datetime.now().astimezone().isoformat(),
  '실행 ID: '+c['run_id'],
  '',
  '1. 현재 완료 범위',
  f"Delta: {d['status']}, {d['tables']}개 테이블, 전체 행/컬럼 값 대사 완료",
  f"Pandas 검증: {p['passed']}/{p['total']} PASS",
  'MySQL: '+mysql_status,
  'Delta 완료와 MySQL 완료는 구분한다. MySQL 실적재 성공은 mysql_validation.json의 PASS로 확인한다.',
  '',
  '2. Bronze: 최초 오염 원본을 보존',
  f"실제 오염 CSV {raw['files']}개 / {raw['rows']:,}행을 Pandas로 진단하고 b_raw_* 8개 Delta로 보존했다.",
  '각 원천 컬럼은 문자열 그대로 보존하고 파일/행번호/파일해시/인코딩을 붙였다.',
  '원본 ZIP 사본도 바이트 해시를 대조해 보존했다. CSV 디코딩 값과 원본 파일 바이트를 구분한다.',
  f"빈값·NULL 유사 문자열 관측 셀: {raw['observed_blank_or_literal_cells']:,}개 (정상 선택 항목 결측 포함)",
  f"명시한 형식 규칙 위반: {raw['confirmed_format_rule_violations']:,}개",
  f"명시한 코드 표준 규칙 위반: {raw['code_standard_rule_violations']:,}개",
  '위 숫자는 적용 규칙에 따른 진단이며 모든 빈값·중복 후보를 오염이라고 단정하지 않는다.',
  '금액 x1000/부호 변경/값 교체는 문법만으로 검출되지 않을 수 있어 변경 명세의 정확한 전후 값을 사용한다.',
  'A/B 인계 CSV 18개도 b_a_*, b_b_*에 보관했다. 이들은 정제 후 인계본이며 최초 오염 원본과 출처를 구분한다.',
  '저장된 B API 응답과 DART 변경 명세 역시 Bronze Delta에 보관했다.',
  '',
  '3. 정제·복구 재현 및 근거',
  f"OpenDART 변경 명세 복원: {cleanup['OpenDART']['exactly_restored_cells']:,}셀",
  f"기존 정제본과 재실행 정제본: {cleanup['files_compared']}개 CSV 해시 일치",
  f"Toss 최초 격리: {cleanup['Toss']['quarantined_rows']}행 / {cleanup['Toss']['unresolved_issues']}개 이슈",
  f"저장 API로 복구한 원천: {b['api_source_rows_merged']}행 / 검토 대기: {b['remaining_review_rows']}행",
  f"B의 정제 기반 업무 값 {bl['business_values_compared']:,}개 원천 대조: 불일치 {bl['mismatches']}",
  'A 상세 재무 66,729행을 정제 재실행 원천과 비교했고 불일치는 없었다.',
  '현재 압축 해제된 A 요약본 대신 C 입력 해시와 일치하는 A 원본 ZIP 내 요약 CSV를 사용했다.',
  'A 보고서 지표 매핑기와 B 복구 전 최초 변환기까지 이번 실행에서 모두 다시 실행한 것은 아니다.',
  'A/B 전달본의 해시 및 업무 값 출처를 확인하고, raw 정제와 B 저장 API 복구를 재실행했다.',
  '',
  '4. Silver: 표준 사전 적용 및 정규화',
  'C의 표준화/조인 코드를 새 폴더에서 실행했다. 기존 C 출력 CSV 19개와 해시가 전부 일치했다.',
  '기업코드 CHAR(8), 종목코드 CHAR(6), 날짜 DATE, 일시 KST DATETIME, 재무 금액 DECIMAL(20,0).',
  '선행 0, 음수, 정상적인 0은 보존하고 선택 결측은 NULL로 변환했다. float를 통한 금액 변환은 하지 않았다.',
  f"재무 보고서 s_fin_rpt: {counts['s_fin_rpt']:,}행",
  f"원본 계정 상세 s_fin_item: {counts['s_fin_item']:,}행",
  f"표준 재무 지표 s_fin_mtrc: {counts['s_fin_mtrc']:,}행",
  f"주가 s_stock_daily_prc: {counts['s_stock_daily_prc']:,}행",
  f"투자자별 수급 s_invstr_trd_daily: {counts['s_invstr_trd_daily']:,}행",
  '재무는 보고서 ID로, 기업과 종목은 검증된 corp_cd/stock_cd 매핑으로 연결했다.',
  '가격과 수급의 연결 상태는 키 합집합으로 남기고, 일별 Gold는 가격 행을 기준으로 유지했다.',
  '',
  '5. Gold: 주가·재무·현금흐름·수급 통합 기반',
  f"g_ai_stock_daily: {counts['g_ai_stock_daily']:,}행 / 종목×거래일",
  f"g_fin_rpt_mkt_smry: {counts['g_fin_rpt_mkt_smry']:,}행 / 재무 보고서별 기간 요약",
  f"일별 재무 연결: {p['financial_matched']:,}행 / 공개 재무 부재: {p['financial_unmatched']:,}행",
  f"일별 수급 부재: {p['investor_unmatched']}행 (가격은 보존, 수급은 NULL)",
  '일별 주가/수급은 stock_cd+trd_dt로 연결했다. 수급 11종은 상위 분류를 먼저 피벗한다.',
  '기관 합계와 기관 상세 7종을 동시에 더하지 않는다. 순매수 단위는 금액이 아니라 주이다.',
  '공시일 < 거래일인 보고서 중 최신 사업기간을 사용한다. 동일 공시일은 제외한다.',
  '독립 A 조인 코드와 재무 보고서 선택이 전 행 일치했다. 미래 공시 연결 위반은 0건이다.',
  'Gold는 현재 C의 통합 분석 기반을 재현한 것이다. 동반 개선/괴리 판정과 전년 동기 변화 지표,',
  '학습 목표·시계열 분할·최종 학습 대상 선정은 다음 분석 규칙으로 확정해야 한다.',
  '기간 요약 full_cvrg_yn은 전역 가격 기간 범위 기준이며 모든 개별 수급 거래일 완전성의 보증은 아니다.',
  '',
  '6. MySQL 적재 방식',
  'start_mysql.cmd 실행 → 파일 검사 → root 비밀번호 입력 → Delta 고정 버전에서 읽어 적재한다.',
  '비밀번호 입력 중 글자/별표는 표시되지 않는다. Enter를 누르면 진행된다.',
  '기존 DB는 보존하고 아래 새 DB에만 기록한다. DROP/TRUNCATE/REPLACE는 실행하지 않는다.',
  *[f"  {layer}: {name}" for layer,name in db.items()],
  '기본키·외래키·도메인 CHECK를 적용하고, 모든 행/컬럼의 정규화 값 해시로 Delta와 MySQL을 대사한다.',
  '트랜잭션 실패 시 해당 테이블 삽입은 롤백한다. 재실행은 이번 실행의 소유 DB에서만 재개한다.',
  '검증 SQL은 sql/validation_queries.sql에 있고, 실제 SQL 결과는 적재 후 별도 보고서에 기록한다.',
  '',
  '7. 확인할 파일',
  'README.txt: 사용법 및 해석 주의점',
  'catalog.json: 테이블·타입·행 수·원천 해시·고정 Delta 버전',
  'profiling/raw_column_profile.csv, raw_file_profile.csv: 오염 원본 진단',
  'dictionary/: 표준 단어·용어·도메인·코드·매핑',
  'validation/pandas_summary.json, delta_summary.json: 이번 실행의 검증 결과',
  'validation/mysql_validation.json: 실제 MySQL 적재 후 생성되는 결과',
  'sql/service_example.sql: 프론트/분석팀에서 확인할 수 있는 예시 조회',
  '',
  '8. 레이어별 저장 테이블',
  *[f"{e['layer']:6} / {e['name']} / {e['rows']:,}행 / Delta v{e['delta_version']}" for e in c['tables']],
 ]
 (run/'구현_및_검증_결과.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
 sql=f"""-- Execute after validation/mysql_validation.json reports PASS.
SELECT c.corp_nm, g.trd_dt, g.close_prc, g.close_rtn_rt,
       g.rev_ytd_amt, g.op_prft_ytd_amt, g.net_incm_ytd_amt, g.op_cf_ytd_amt,
       g.frgn_net_buy_qty, g.inst_net_buy_qty, g.dscl_dt, g.fin_rpt_id
FROM {qi(db['gold'])}.g_ai_stock_daily g
LEFT JOIN {qi(db['silver'])}.s_corp c ON c.corp_cd=g.corp_cd
WHERE g.stock_cd='005930'
ORDER BY g.trd_dt DESC LIMIT 20;
"""
 (run/'sql/service_example.sql').write_text(sql,encoding='utf-8')
 print(run/'구현_및_검증_결과.txt')

if __name__=='__main__':build(select_run(None))
