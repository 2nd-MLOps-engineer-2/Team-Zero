"""TEAM ZERO AI 데이터 표준 사전 (C 담당) — 단일 정의 원본(single source of truth).

이 파일 하나에서 표준 단어·도메인·코드·용어(=테이블 컬럼)를 정의한다.
- 02_standard_dictionary/*.csv, AI_데이터_표준사전.xlsx 는 이 파일로 생성한다.
- MySQL DDL(03_model/ddl/*.sql)과 ERD도 이 파일의 TABLES 정의에서 생성한다.
- 표준 준수율 검사(validate.py)도 이 파일의 규칙으로 수행한다.

표준 단어 조합 규칙
  물리명 = [수식어_]*[주제어_]+분류어   (소문자 snake_case, 토큰은 모두 표준 단어여야 함)
  - 마지막 토큰은 반드시 '분류어'(class word)이며, 분류어가 허용하는 도메인만 쓸 수 있다.
  - 물리명 길이 ≤ 40자, 숫자로 시작 금지, 예약어 단독 사용 금지.
  - 같은 의미는 같은 단어 하나만 사용(동음이의·이음동의 금지): symbol/stock_code → stock_cd.
"""
from __future__ import annotations

PIPELINE_VERSION = "c-integration-1.0.0"
STD_VERSION = "tz-std-1.0.0"

# --------------------------------------------------------------------------
# 1. 표준 단어  token: (한글명, 영문명, 구분)   구분: CLASS=분류어, WORD=일반어
# --------------------------------------------------------------------------
WORDS: dict[str, tuple[str, str, str]] = {
    # 분류어 (class words) — 컬럼 마지막 토큰
    "id": ("식별자", "Identifier", "CLASS"),
    "cd": ("코드", "Code", "CLASS"),
    "nm": ("명", "Name", "CLASS"),
    "no": ("번호", "Number", "CLASS"),
    "dt": ("일자", "Date", "CLASS"),
    "dttm": ("일시", "Datetime", "CLASS"),
    "yr": ("연도", "Year", "CLASS"),
    "amt": ("금액", "Amount", "CLASS"),
    "prc": ("가격", "Price", "CLASS"),
    "qty": ("수량", "Quantity", "CLASS"),
    "rt": ("율", "Rate", "CLASS"),
    "val": ("값", "Value", "CLASS"),
    "yn": ("여부", "Yes/No", "CLASS"),
    "cnt": ("건수", "Count", "CLASS"),
    "txt": ("내용", "Text", "CLASS"),
    "path": ("경로", "Path", "CLASS"),
    "hash": ("해시값", "Hash", "CLASS"),
    "ver": ("버전", "Version", "CLASS"),
    # 일반어 (subject / modifier words)
    "corp": ("기업", "Corporation", "WORD"),
    "stock": ("종목", "Stock", "WORD"),
    "eng": ("영문", "English", "WORD"),
    "isin": ("국제증권식별", "ISIN", "WORD"),
    "mkt": ("시장", "Market", "WORD"),
    "sec": ("증권", "Security", "WORD"),
    "type": ("유형", "Type", "WORD"),
    "cmn": ("보통", "Common", "WORD"),
    "shr": ("주식", "Share", "WORD"),
    "stts": ("상태", "Status", "WORD"),
    "crncy": ("통화", "Currency", "WORD"),
    "list": ("상장", "Listing", "WORD"),
    "delist": ("상장폐지", "Delisting", "WORD"),
    "outstd": ("발행", "Outstanding", "WORD"),
    "lvrg": ("레버리지", "Leverage", "WORD"),
    "dtl": ("상세", "Detail", "WORD"),
    "chg": ("변경", "Change", "WORD"),
    "cls": ("분류", "Class", "WORD"),
    "trd": ("거래", "Trade", "WORD"),
    "candle": ("봉", "Candle", "WORD"),
    "open": ("시가", "Open", "WORD"),
    "high": ("고가", "High", "WORD"),
    "low": ("저가", "Low", "WORD"),
    "close": ("종가", "Close", "WORD"),
    "idx": ("지수", "Index", "WORD"),
    "invstr": ("투자자", "Investor", "WORD"),
    "upper": ("상위", "Upper", "WORD"),
    "aggr": ("집계", "Aggregation", "WORD"),
    "lvl": ("수준", "Level", "WORD"),
    "buy": ("매수", "Buy", "WORD"),
    "sell": ("매도", "Sell", "WORD"),
    "net": ("순", "Net", "WORD"),
    "frgn": ("외국인", "Foreigner", "WORD"),
    "inst": ("기관", "Institution", "WORD"),
    "indv": ("개인", "Individual", "WORD"),
    "other": ("기타", "Other", "WORD"),
    "hold": ("보유", "Holding", "WORD"),
    "limit": ("한도", "Limit", "WORD"),
    "cfd": ("차액결제거래", "CFD", "WORD"),
    "bal": ("잔고", "Balance", "WORD"),
    "src": ("원천", "Source", "WORD"),
    "file": ("파일", "File", "WORD"),
    "row": ("행", "Row", "WORD"),
    "col": ("컬럼", "Column", "WORD"),
    "json": ("JSON", "JSON", "WORD"),
    "kind": ("종류", "Kind", "WORD"),
    "team": ("팀", "Team", "WORD"),
    "bronze": ("브론즈", "Bronze", "WORD"),
    "pipln": ("파이프라인", "Pipeline", "WORD"),
    "fetch": ("조회", "Fetch", "WORD"),
    "api": ("API", "API", "WORD"),
    "raw": ("원응답", "Raw", "WORD"),
    "rcrd": ("레코드", "Record", "WORD"),
    "rcept": ("접수", "Receipt", "WORD"),
    "rpt": ("보고서", "Report", "WORD"),
    "flr": ("제출인", "Filer", "WORD"),
    "rmk": ("비고", "Remark", "WORD"),
    "doc": ("문서", "Document", "WORD"),
    "zip": ("압축", "Zip", "WORD"),
    "err": ("오류", "Error", "WORD"),
    "msg": ("메시지", "Message", "WORD"),
    "dscl": ("공시", "Disclosure", "WORD"),
    "fin": ("재무", "Financial", "WORD"),
    "bsns": ("사업", "Business", "WORD"),
    "fs": ("재무제표", "Financial Statement", "WORD"),
    "div": ("구분", "Division", "WORD"),
    "stmt": ("보고서양식", "Statement", "WORD"),
    "acnt": ("계정", "Account", "WORD"),
    "cur": ("당기", "Current Term", "WORD"),
    "prev": ("전기", "Previous Term", "WORD"),
    "bfr": ("전전", "Before", "WORD"),
    "cum": ("누적", "Cumulative", "WORD"),
    "qtr": ("분기", "Quarter", "WORD"),
    "prd": ("기간", "Period", "WORD"),
    "sort": ("정렬", "Sort", "WORD"),
    "ord": ("순서", "Order", "WORD"),
    "item": ("항목", "Item", "WORD"),
    "mtrc": ("지표", "Metric", "WORD"),
    "def": ("정의", "Definition", "WORD"),
    "start": ("시작", "Start", "WORD"),
    "end": ("종료", "End", "WORD"),
    "flow": ("흐름", "Flow", "WORD"),
    "mm": ("개월", "Month", "WORD"),
    "cal": ("달력", "Calendar", "WORD"),
    "cf": ("현금흐름", "Cash Flow", "WORD"),
    "pit": ("시점", "Point-in-time", "WORD"),
    "join": ("조인", "Join", "WORD"),
    "elig": ("적격", "Eligible", "WORD"),
    "same": ("동일", "Same", "WORD"),
    "cmpr": ("비교", "Comparison", "WORD"),
    "review": ("검토", "Review", "WORD"),
    "custom": ("사용자정의", "Custom", "WORD"),
    "map": ("매핑", "Mapping", "WORD"),
    "conflict": ("충돌", "Conflict", "WORD"),
    "core": ("핵심", "Core", "WORD"),
    "miss": ("누락", "Missing", "WORD"),
    "stmt_list": ("보고서양식목록", "Statement List", "WORD"),
    "rsn": ("사유", "Reason", "WORD"),
    "select": ("선정", "Selection", "WORD"),
    "guard": ("제외조건", "Guard", "WORD"),
    "mthd": ("방법", "Method", "WORD"),
    "cand": ("후보", "Candidate", "WORD"),
    "match": ("일치", "Match", "WORD"),
    "conn": ("연결", "Connection", "WORD"),
    "exist": ("존재", "Existence", "WORD"),
    "avail": ("가용", "Available", "WORD"),
    "issue": ("이슈", "Issue", "WORD"),
    "sev": ("심각도", "Severity", "WORD"),
    "tbl": ("테이블", "Table", "WORD"),
    "key": ("키", "Key", "WORD"),
    "detect": ("탐지", "Detection", "WORD"),
    "stage": ("단계", "Stage", "WORD"),
    "resolve": ("조치", "Resolution", "WORD"),
    "grp": ("그룹", "Group", "WORD"),
    "desc": ("설명", "Description", "WORD"),
    "asis": ("현행", "AS-IS", "WORD"),
    "rtn": ("수익률", "Return", "WORD"),
    "elps": ("경과", "Elapsed", "WORD"),
    "day": ("일", "Day", "WORD"),
    "ytd": ("연초누적", "Year-to-date", "WORD"),
    "rev": ("매출", "Revenue", "WORD"),
    "op": ("영업", "Operating", "WORD"),
    "prft": ("이익", "Profit", "WORD"),
    "incm": ("순이익", "Income", "WORD"),
    "tot": ("총", "Total", "WORD"),
    "asst": ("자산", "Asset", "WORD"),
    "liab": ("부채", "Liability", "WORD"),
    "eqty": ("자본", "Equity", "WORD"),
    "first": ("첫", "First", "WORD"),
    "last": ("마지막", "Last", "WORD"),
    "cvrg": ("커버리지", "Coverage", "WORD"),
    "full": ("전체", "Full", "WORD"),
    "run": ("실행", "Run", "WORD"),
    "step": ("절차", "Step", "WORD"),
    "input": ("입력", "Input", "WORD"),
    "ldng": ("적재", "Loading", "WORD"),
    "word": ("단어", "Word", "WORD"),
    "term": ("용어", "Term", "WORD"),
    "dmn": ("도메인", "Domain", "WORD"),
    "data": ("데이터", "Data", "WORD"),
    "len": ("길이", "Length", "WORD"),
    "scale": ("소수자리", "Scale", "WORD"),
    "ptrn": ("패턴", "Pattern", "WORD"),
    "allow": ("허용", "Allowed", "WORD"),
    "null": ("널", "Null", "WORD"),
    "pk": ("기본키", "Primary Key", "WORD"),
    "unit": ("단위", "Unit", "WORD"),
    "kor": ("한글", "Korean", "WORD"),
    "phys": ("물리", "Physical", "WORD"),
    "layer": ("계층", "Layer", "WORD"),
    "attr": ("속성", "Attribute", "WORD"),
}
# stmt_list는 조합 검사 편의상 넣지 않는다(오등록 방지)
WORDS.pop("stmt_list")

# --------------------------------------------------------------------------
# 2. 표준 도메인  name: (분류어, MySQL 타입, 길이/정밀도, 형식·허용값 규칙(regex), 설명)
# --------------------------------------------------------------------------
DOMAINS: dict[str, tuple[str, str, str, str, str]] = {
    "ID_V64":    ("id",   "VARCHAR(64)",   "64",   r"^\S{1,64}$", "내부 생성 식별자(해시 기반 등)"),
    "ACNT_ID":   ("id",   "VARCHAR(200)",  "200",  r"^.{1,200}$", "OpenDART 표준계정코드(미사용 표기 포함)"),
    "CORP_CD":   ("cd",   "CHAR(8)",       "8",    r"^\d{8}$", "OpenDART 고유번호 8자리, 선행 0 보존"),
    "STOCK_CD":  ("cd",   "CHAR(6)",       "6",    r"^\d{6}$", "KRX 단축 종목코드 6자리, 선행 0 보존"),
    "ISIN_CD":   ("cd",   "CHAR(12)",      "12",   r"^[A-Z]{2}[A-Z0-9]{9}\d$", "ISIN 12자리"),
    "CODE_V50":  ("cd",   "VARCHAR(50)",   "50",   r"CODE_GROUP", "공통코드(s_cmn_cd) 허용값만 사용"),
    "NAME_V200": ("nm",   "VARCHAR(200)",  "200",  r"^.{0,200}$", "일반 명칭"),
    "NAME_V500": ("nm",   "VARCHAR(500)",  "500",  r"^.{0,500}$", "긴 명칭(계정 상세 경로·보고서명 등)"),
    "RCEPT_NO":  ("no",   "CHAR(14)",      "14",   r"^\d{14}$", "공시 접수번호 14자리"),
    "ROW_NO":    ("no",   "INT",           "10",   r"^\d+$", "1부터 시작하는 행·순서 번호"),
    "DATE":      ("dt",   "DATE",          "10",   r"^\d{4}-\d{2}-\d{2}$", "YYYY-MM-DD, 한국시간(KST) 기준 일자"),
    "DATETIME":  ("dttm", "DATETIME",      "19",   r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", "KST 로 변환한 일시(오프셋 제거)"),
    "YEAR":      ("yr",   "CHAR(4)",       "4",    r"^\d{4}$", "연도 4자리"),
    "AMT_KRW":   ("amt",  "DECIMAL(20,0)", "20,0", r"^-?\d{1,20}$", "원 단위 정수 금액, 음수 허용, 빈값은 NULL(0 대체 금지)"),
    "PRICE":     ("prc",  "DECIMAL(18,4)", "18,4", r"^\d{1,14}(\.\d{1,4})?$", "가격/지수, 0 이상"),
    "QTY":       ("qty",  "BIGINT",        "19",   r"^-?\d+$", "수량(주), 순매수는 음수 허용"),
    "RATE":      ("rt",   "DECIMAL(12,8)", "12,8", r"^-?\d{1,4}(\.\d{1,8})?$", "소수 비율(1=100%)"),
    "CODE_VAL":  ("val",  "VARCHAR(200)",  "200",  r"^.{1,200}$", "공통코드 값(문자)"),
    "DEC_VAL":   ("val",  "DECIMAL(18,6)", "18,6", r"^-?\d+(\.\d+)?$", "일반 수치값"),
    "YN":        ("yn",   "CHAR(1)",       "1",    r"^[YN]$", "Y/N 두 값만 허용(True/true/1 등 혼용 금지)"),
    "COUNT":     ("cnt",  "INT",           "10",   r"^\d+$", "0 이상 건수"),
    "TEXT_V2000":("txt",  "VARCHAR(2000)", "2000", r"^.{0,2000}$", "설명·사유 텍스트"),
    "TEXT_LONG": ("txt",  "TEXT",          "65535",r"^.*$", "JSON 등 긴 텍스트"),
    "PATH":      ("path", "VARCHAR(500)",  "500",  r"^.{0,500}$", "파일 경로 또는 JSONPath"),
    "HASH":      ("hash", "VARCHAR(80)",   "80",   r"^(sha256:)?[0-9a-f]{64}$", "SHA-256 해시"),
    "VERSION":   ("ver",  "VARCHAR(80)",   "80",   r"^.{1,80}$", "데이터/파이프라인 버전 문자열"),
}

# --------------------------------------------------------------------------
# 3. 표준 코드 (공통코드)  group: (그룹 한글명, [(코드값, 코드명, 정렬순서, AS-IS 값들)])
# --------------------------------------------------------------------------
CODES: dict[str, tuple[str, list[tuple[str, str, int, str]]]] = {
    "YN": ("여부", [("Y", "예", 1, "True|true|1|Y"), ("N", "아니오", 2, "False|false|0|N")]),
    "TEAM": ("담당 팀", [("A", "A 담당(OpenDART)", 1, ""), ("B", "B 담당(토스증권)", 2, ""), ("C", "C 담당(통합·품질)", 3, "")]),
    "MKT": ("시장", [("KOSPI", "유가증권시장", 1, "KOSPI|Y"), ("KOSDAQ", "코스닥시장", 2, "KOSDAQ|K")]),
    "IDX": ("지수", [("KOSPI", "코스피 지수", 1, "KOSPI"), ("KOSDAQ", "코스닥 지수", 2, "KOSDAQ")]),
    "CORP_CLS": ("법인구분(OpenDART)", [("Y", "유가", 1, "Y"), ("K", "코스닥", 2, "K"), ("N", "코넥스", 3, "N"), ("E", "기타", 4, "E")]),
    "SEC_TYPE": ("증권 유형", [("STOCK", "주식", 1, "STOCK")]),
    "STOCK_STTS": ("종목 상태", [("ACTIVE", "거래중", 1, "ACTIVE")]),
    "CRNCY": ("통화", [("KRW", "원화", 1, "KRW")]),
    "RPT": ("보고서 코드", [("11013", "1분기보고서", 1, "11013|1분기"), ("11012", "반기보고서", 2, "11012|반기"),
                         ("11014", "3분기보고서", 3, "11014|3분기"), ("11011", "사업보고서", 4, "11011|사업보고서")]),
    "FS_DIV": ("재무제표 구분", [("CFS", "연결재무제표", 1, "CFS"), ("OFS", "별도·개별재무제표", 2, "OFS")]),
    "STMT_DIV": ("재무제표 양식", [("BS", "재무상태표", 1, "BS"), ("IS", "손익계산서", 2, "IS"), ("CIS", "포괄손익계산서", 3, "CIS"),
                              ("CF", "현금흐름표", 4, "CF"), ("SCE", "자본변동표", 5, "SCE")]),
    "DOC_STTS": ("원문 문서 상태", [("DOWNLOADED", "원문 수집 완료", 1, "downloaded"), ("UNAVAILABLE", "원문 없음(OpenDART 014)", 2, "unavailable"),
                                ("NOT_IN_INPUT", "원문 수집 대상 아님", 3, "NOT_IN_INPUT")]),
    "DSCL_JOIN_STTS": ("공시 연결 상태", [("MATCHED", "공시목록과 연결", 1, "MATCHED"), ("NOT_IN_INPUT_COVERAGE", "공시목록 수집 범위 밖", 2, "NOT_IN_INPUT_COVERAGE")]),
    "CAL_PRD_STTS": ("달력 기간 검증 상태", [("VERIFIED_XML", "원문 XML 검증", 1, "VERIFIED_XML"), ("ASSUMED_DECEMBER_FISCAL_YEAR", "12월 결산 가정", 2, "ASSUMED_DECEMBER_FISCAL_YEAR")]),
    "CF_PRD_STTS": ("현금흐름 기간 검증 상태", [("VERIFIED_XML_YTD", "원문 XML 누적기간 검증", 1, "VERIFIED_XML_YTD"), ("UNVERIFIED_NO_DOCUMENT", "원문 없음·미검증", 2, "UNVERIFIED_NO_DOCUMENT")]),
    "PRD_TYPE": ("지표 기간 유형", [("YTD", "당기 누적", 1, "_ytd"), ("PRIOR_YTD", "전년 동기 누적", 2, "_prior_ytd"),
                              ("Q3M", "당기 3개월", 3, "_3m"), ("PRIOR_Q3M", "전년 동기 3개월", 4, "_prior_3m"),
                              ("ASOF", "당기말 잔액", 5, "_asof"), ("PRIOR_YE", "전년도말 잔액", 6, "_prior_year_end")]),
    "INVSTR_TYPE": ("투자자 유형", [("INDIVIDUAL", "개인", 1, "individual"), ("FOREIGNER", "외국인", 2, "foreigner"),
                                ("INSTITUTION", "기관 합계", 3, "institution"), ("OTHER_CORP", "기타법인", 4, "otherCorporation"),
                                ("FIN_INVEST", "금융투자", 11, "financialInvestment"), ("INSURANCE", "보험", 12, "insurance"),
                                ("TRUST", "투신", 13, "trust"), ("PRIVATE_EQUITY", "사모펀드", 14, "privateEquityFund"),
                                ("BANK", "은행", 15, "bank"), ("OTHER_FIN", "기타금융", 16, "otherFinancialInstitution"),
                                ("PENSION", "연기금", 17, "pensionFund")]),
    "AGGR_LVL": ("수급 집계 수준", [("TOP_LEVEL", "상위 4유형", 1, "top_level"), ("INST_DETAIL", "기관 세부 7유형", 2, "institution_detail")]),
    "SRC_KIND": ("원천 종류", [("BRONZE", "브론즈 정화본", 1, "bronze|Bronze_Cleanup_20261014"), ("API_REQUERY", "토스 API 재조회", 2, "toss_api_requery")]),
    "MAP_STTS": ("기업-종목 매핑 상태", [("MATCHED", "1:1 매핑", 1, ""), ("UNMAPPED", "미연결", 2, ""), ("MULTIPLE_CANDIDATES", "다중 후보", 3, "")]),
    "MAP_MTHD": ("매핑 방법", [("STOCK_CD_EXACT", "종목코드 완전일치", 1, ""), ("NONE", "매핑 불가", 9, "")]),
    "CONN_STTS": ("가격·수급 연결 상태", [("BOTH", "가격·수급 모두 있음", 1, "both"), ("PRICE_ONLY", "가격만 있음", 2, "price_only"),
                                     ("INVESTOR_ONLY", "수급만 있음", 3, "investor_only")]),
    "MISS_RSN": ("부재 사유", [("INVESTOR_PENDING_REVIEW", "수급 API 재조회값 검토 대기(updatedAt 불일치)", 1, "investor_api_candidate_requires_review"),
                             ("INVESTOR_NOT_SUPPLIED", "수급 원천 없음", 2, ""), ("PRICE_NOT_SUPPLIED", "가격 원천 없음", 3, "")]),
    "ISSUE_TYPE": ("품질 이슈 유형", [("MISSING_VALUE", "결측", 1, ""), ("DUPLICATE_KEY", "키 중복", 2, ""), ("FORMAT", "형식 불일치", 3, ""),
                                  ("CODE_VALUE", "코드값 위반", 4, ""), ("REFERENCE", "참조 무결성", 5, ""), ("NAMING", "명명 규칙", 6, ""),
                                  ("COVERAGE", "수집 범위·부재", 7, ""), ("PERIOD", "기간 검증", 8, ""), ("MAPPING", "계정·기업 매핑", 9, ""),
                                  ("NAME_MISMATCH", "명칭 불일치", 10, ""), ("RANGE", "값 범위", 11, ""), ("REVIEW", "검토 대기", 12, "")]),
    "SEV": ("심각도", [("ERROR", "오류(적재 차단)", 1, ""), ("WARN", "경고(사용 시 주의)", 2, "REVIEW"), ("INFO", "정보(설명 가능)", 3, "")]),
    "DETECT_STAGE": ("탐지 단계", [("A_SELF", "A 자체 검증", 1, ""), ("B_SELF", "B 자체 검증", 2, ""), ("C_INTEGRATION", "C 통합 검증", 3, "")]),
    "RESOLVE_STTS": ("조치 상태", [("OPEN", "미해결", 1, ""), ("RETAINED", "행 보존·플래그", 2, ""), ("EXCLUDED_FROM_PIT", "시점 조인 제외", 3, ""),
                                ("QUARANTINED", "격리", 4, ""), ("EXPLAINED", "설명 완료", 5, "")]),
    "MTRC": ("재무 지표", []),  # metric_definitions.csv 에서 채움(run_pipeline)
    "LAYER": ("데이터 계층", [("BRONZE", "브론즈", 1, ""), ("SILVER", "실버", 2, ""), ("GOLD", "골드", 3, ""), ("META", "메타", 4, "")]),
    "RUN_STTS": ("실행 상태", [("SUCCESS", "성공", 1, ""), ("FAILED", "실패", 2, "")]),
}

# --------------------------------------------------------------------------
# 4. 표준 용어 = 테이블 컬럼 정의
#    (물리명, 한글 용어명, 도메인, NULL허용, 코드그룹, AS-IS 원천 대응)
# --------------------------------------------------------------------------
def C(phys, kor, dmn, null=False, code="", src=""):
    return dict(phys=phys, kor=kor, dmn=dmn, null=null, code=code, src=src)

LIN_A = [  # A 출처 추적
    C("src_team_cd", "원천 팀 코드", "CODE_V50", code="TEAM", src="(C 부여) A"),
    C("src_file_path", "원천 파일 경로", "PATH", src="_source_file"),
    C("src_row_no", "원천 행 번호", "ROW_NO", src="_source_row"),
    C("src_ver", "원천 버전", "VERSION", src="_source_version"),
    C("pipln_ver", "파이프라인 버전", "VERSION", src="(C 부여)"),
]
LIN_B = [  # B 출처 추적(+API 재조회 추적)
    C("src_team_cd", "원천 팀 코드", "CODE_V50", code="TEAM", src="(C 부여) B"),
    C("src_kind_cd", "원천 종류 코드", "CODE_V50", code="SRC_KIND", src="source_kind"),
    C("src_file_path", "원천 파일 경로", "PATH", src="source_file"),
    C("src_row_no", "원천 행 번호", "ROW_NO", src="source_row"),
    C("bronze_row_no", "브론즈 행 번호", "ROW_NO", null=True, src="bronze_row"),
    C("src_ver", "원천 버전", "VERSION", src="source_version"),
    C("fetch_dttm", "API 조회 일시", "DATETIME", null=True, src="fetched_at"),
    C("api_raw_file_path", "API 원응답 파일 경로", "PATH", null=True, src="api_raw_file"),
    C("api_rcrd_path", "API 레코드 경로", "PATH", null=True, src="api_record_path"),
    C("pipln_ver", "파이프라인 버전", "VERSION", src="pipeline_version → C 버전으로 교체(원 값은 src_ver 계열로 추적)"),
]

TABLES: dict[str, dict] = {}

def T(name, layer, kor, grain, pk, cols, fks=(), src="", logical_fks=()):
    TABLES[name] = dict(name=name, layer=layer, kor=kor, grain=grain, pk=list(pk), cols=cols,
                        fks=list(fks), src=src, logical_fks=list(logical_fks))

# ---------------- SILVER : 공통/메타성 ----------------
T("s_cmn_cd", "SILVER", "공통코드", "코드그룹·코드값당 1행", ["cd_grp_id", "cd_val"], [
    C("cd_grp_id", "코드그룹 식별자", "ID_V64"),
    C("cd_val", "코드값", "CODE_VAL"),
    C("cd_nm", "코드명", "NAME_V200"),
    C("cd_desc_txt", "코드 설명", "TEXT_V2000", null=True),
    C("sort_ord_no", "정렬 순서 번호", "ROW_NO"),
    C("asis_val_txt", "현행(AS-IS) 값 목록", "TEXT_V2000", null=True),
], src="C 표준 사전")

# ---------------- SILVER : A (OpenDART) ----------------
T("s_corp", "SILVER", "기업", "OpenDART 고유번호당 1행", ["corp_cd"], [
    C("corp_cd", "기업 코드", "CORP_CD", src="company_master.corp_code"),
    C("corp_nm", "기업명", "NAME_V200", src="company_master.corp_name"),
    C("corp_eng_nm", "기업 영문명", "NAME_V200", src="company_master.corp_eng_name"),
    C("stock_cd", "종목 코드", "STOCK_CD", src="company_master.stock_code"),
    C("chg_dt", "변경 일자", "DATE", src="company_master.modify_date (YYYYMMDD→DATE)"),
] + LIN_A, src="A support/company_master.csv")

T("s_dscl", "SILVER", "공시", "공시 접수번호당 1행", ["rcept_no"], [
    C("rcept_no", "접수 번호", "RCEPT_NO", src="disclosures.rcept_no"),
    C("corp_cd", "기업 코드", "CORP_CD", src="disclosures.corp_code"),
    C("corp_nm", "기업명(공시 당시)", "NAME_V200", src="disclosures.corp_name"),
    C("corp_cls_cd", "법인구분 코드", "CODE_V50", code="CORP_CLS", src="disclosures.corp_cls"),
    C("stock_cd", "종목 코드", "STOCK_CD", src="disclosures.stock_code"),
    C("rpt_nm", "보고서명", "NAME_V500", src="disclosures.report_nm"),
    C("flr_nm", "제출인명", "NAME_V200", src="disclosures.flr_nm"),
    C("rcept_dt", "접수 일자", "DATE", src="disclosures.rcept_dt (YYYYMMDD→DATE)"),
    C("rmk_txt", "비고 내용", "TEXT_V2000", null=True, src="disclosures.rm"),
] + LIN_A, fks=[("corp_cd", "s_corp", "corp_cd")], src="A support/disclosures_with_documents.csv (문서 컬럼 제외: s_dscl_doc 로 분리)")

T("s_dscl_doc", "SILVER", "공시 원문 문서", "원문 수집 대상 접수번호당 1행", ["rcept_no"], [
    C("rcept_no", "접수 번호", "RCEPT_NO", src="disclosure_documents.rcept_no"),
    C("corp_cd", "기업 코드", "CORP_CD", src="disclosure_documents.corp_code"),
    C("doc_stts_cd", "문서 상태 코드", "CODE_V50", code="DOC_STTS", src="disclosure_documents.status"),
    C("doc_zip_path", "문서 압축파일 경로", "PATH", null=True, src="disclosure_documents.zip_path"),
    C("doc_hash", "문서 해시값", "HASH", null=True, src="disclosure_documents.sha256"),
    C("err_msg_txt", "오류 메시지 내용", "TEXT_V2000", null=True, src="disclosure_documents.error"),
] + LIN_A, fks=[("rcept_no", "s_dscl", "rcept_no"), ("corp_cd", "s_corp", "corp_cd")],
  src="A support/disclosure_documents.csv")

T("s_fin_rpt", "SILVER", "재무 보고서", "기업·사업연도·보고서·연결구분·접수번호당 1행", ["fin_rpt_id"], [
    C("fin_rpt_id", "재무 보고서 식별자", "ID_V64", src="summary.financial_report_id"),
    C("corp_cd", "기업 코드", "CORP_CD", src="summary.corp_code"),
    C("bsns_yr", "사업 연도", "YEAR", src="summary.bsns_year"),
    C("rpt_cd", "보고서 코드", "CODE_V50", code="RPT", src="summary.reprt_code"),
    C("fs_div_cd", "재무제표 구분 코드", "CODE_V50", code="FS_DIV", src="summary.fs_div"),
    C("rcept_no", "접수 번호", "RCEPT_NO", src="summary.rcept_no"),
    C("crncy_cd", "통화 코드", "CODE_V50", code="CRNCY", src="summary.currency"),
    C("flow_prd_mm_cnt", "흐름 기간 개월 건수", "COUNT", src="summary.flow_period_months"),
    C("prd_start_dt", "기간 시작 일자(명목)", "DATE", src="summary.period_start_nominal"),
    C("prd_end_dt", "기간 종료 일자(명목)", "DATE", src="summary.period_end_nominal"),
    C("dscl_join_stts_cd", "공시 연결 상태 코드", "CODE_V50", code="DSCL_JOIN_STTS", src="summary.disclosure_join_status"),
    C("cal_prd_stts_cd", "달력 기간 상태 코드", "CODE_V50", code="CAL_PRD_STTS", src="summary.calendar_period_status"),
    C("cf_prd_stts_cd", "현금흐름 기간 상태 코드", "CODE_V50", code="CF_PRD_STTS", src="summary.cf_period_status"),
    C("pit_join_elig_yn", "시점 조인 적격 여부", "YN", code="YN", src="summary.point_in_time_join_eligible (1/0→Y/N)"),
    C("same_prd_cmpr_elig_yn", "동일 기간 비교 적격 여부", "YN", code="YN", src="summary.same_period_comparison_eligible (1/0→Y/N)"),
    C("mtrc_review_cnt", "지표 검토 건수", "COUNT", src="summary.metric_review_count"),
    C("custom_map_cnt", "사용자정의 매핑 건수", "COUNT", src="summary.custom_mapped_count"),
    C("mtrc_conflict_cnt", "지표 충돌 건수", "COUNT", src="summary.metric_conflict_count"),
    C("core_mtrc_miss_txt", "핵심 지표 누락 내용", "TEXT_V2000", null=True, src="summary.missing_core_metrics"),
    C("src_team_cd", "원천 팀 코드", "CODE_V50", code="TEAM", src="(C 부여) A"),
    C("src_file_path", "원천 파일 경로", "PATH", src="(C 부여) opendart_financial_summary_20_companies.csv"),
    C("src_row_no", "원천 행 번호", "ROW_NO", src="(C 부여) 요약 CSV 데이터 행 번호"),
    C("src_ver", "원천 버전", "VERSION", src="summary.source_version"),
    C("pipln_ver", "파이프라인 버전", "VERSION", src="(C 부여)"),
], fks=[("corp_cd", "s_corp", "corp_cd")], logical_fks=[("rcept_no", "s_dscl", "rcept_no", "61건 공시목록 수집 범위 밖 → 물리 FK 미적용, 검증으로 관리")],
  src="A opendart_financial_summary_20_companies.csv (헤더 컬럼; report_label·report_quarter·report_nm·disclosure_date·document_* 는 정규화로 제거)")

T("s_fin_mtrc_def", "SILVER", "재무 지표 정의", "지표당 1행", ["mtrc_cd"], [
    C("mtrc_cd", "지표 코드", "CODE_V50", code="MTRC", src="metric_definitions.metric (대문자)"),
    C("mtrc_nm", "지표명", "NAME_V200", src="metric_definitions.label_ko"),
    C("stmt_div_txt", "재무제표 양식 내용", "TEXT_V2000", src="metric_definitions.statement"),
    C("acnt_id_txt", "계정 식별자 목록 내용", "TEXT_V2000", src="metric_definitions.account_ids"),
    C("select_rsn_txt", "선정 사유 내용", "TEXT_V2000", src="metric_definitions.reason_ko"),
    C("custom_nm_txt", "사용자정의 계정명 내용", "TEXT_V2000", null=True, src="metric_definitions.custom_names"),
    C("guard_txt", "제외조건 내용", "TEXT_V2000", null=True, src="metric_definitions.name_guard"),
    C("pipln_ver", "파이프라인 버전", "VERSION", src="(C 부여)"),
], src="A support/metric_definitions.csv")

T("s_fin_mtrc", "SILVER", "재무 지표값", "재무보고서·지표·기간유형당 1행(넓은 표 → 세로 표 정규화)",
  ["fin_rpt_id", "mtrc_cd", "prd_type_cd"], [
    C("fin_rpt_id", "재무 보고서 식별자", "ID_V64", src="summary.financial_report_id"),
    C("mtrc_cd", "지표 코드", "CODE_V50", code="MTRC", src="summary.<metric>_* 컬럼명의 지표부"),
    C("prd_type_cd", "기간 유형 코드", "CODE_V50", code="PRD_TYPE", src="summary.<metric>_* 컬럼명의 기간 접미사"),
    C("mtrc_amt", "지표 금액", "AMT_KRW", null=True, src="summary.<metric>_<period> 값(빈값=NULL)"),
    C("src_col_nm", "원천 컬럼명", "NAME_V200", src="summary 컬럼명"),
    C("pipln_ver", "파이프라인 버전", "VERSION", src="(C 부여)"),
], fks=[("fin_rpt_id", "s_fin_rpt", "fin_rpt_id"), ("mtrc_cd", "s_fin_mtrc_def", "mtrc_cd")],
  src="A opendart_financial_summary_20_companies.csv (94개 지표 컬럼 UNPIVOT)")

T("s_fin_item", "SILVER", "재무 계정 상세", "원천 재무 CSV 1행 = 1행", ["fin_item_id"], [
    C("fin_item_id", "재무 항목 식별자", "ID_V64", src="financial_items_all.financial_item_id"),
    C("fin_rpt_id", "재무 보고서 식별자", "ID_V64", src="financial_items_all.financial_report_id"),
    C("corp_cd", "기업 코드", "CORP_CD", src="financial_items_all.corp_code"),
    C("rcept_no", "접수 번호", "RCEPT_NO", src="financial_items_all.rcept_no"),
    C("bsns_yr", "사업 연도", "YEAR", src="financial_items_all.bsns_year"),
    C("rpt_cd", "보고서 코드", "CODE_V50", code="RPT", src="financial_items_all.reprt_code"),
    C("fs_div_cd", "재무제표 구분 코드", "CODE_V50", code="FS_DIV", src="financial_items_all.fs_div"),
    C("stmt_div_cd", "재무제표 양식 코드", "CODE_V50", code="STMT_DIV", src="financial_items_all.sj_div"),
    C("acnt_id", "계정 식별자", "ACNT_ID", src="financial_items_all.account_id ('-표준계정코드 미사용-' 원값 보존)"),
    C("acnt_nm", "계정명", "NAME_V200", src="financial_items_all.account_nm"),
    C("acnt_dtl_nm", "계정 상세명", "NAME_V500", src="financial_items_all.account_detail ('-'=상세 없음, 원값 보존)"),
    C("cur_prd_nm", "당기 기간명", "NAME_V200", null=True, src="thstrm_nm"),
    C("cur_amt", "당기 금액", "AMT_KRW", null=True, src="thstrm_amount"),
    C("cur_cum_amt", "당기 누적 금액", "AMT_KRW", null=True, src="thstrm_add_amount"),
    C("prev_prd_nm", "전기 기간명", "NAME_V200", null=True, src="frmtrm_nm"),
    C("prev_amt", "전기 금액", "AMT_KRW", null=True, src="frmtrm_amount"),
    C("prev_qtr_prd_nm", "전기 분기 기간명", "NAME_V200", null=True, src="frmtrm_q_nm"),
    C("prev_qtr_amt", "전기 분기 금액", "AMT_KRW", null=True, src="frmtrm_q_amount"),
    C("prev_cum_amt", "전기 누적 금액", "AMT_KRW", null=True, src="frmtrm_add_amount"),
    C("bfr_prev_prd_nm", "전전기 기간명", "NAME_V200", null=True, src="bfefrmtrm_nm"),
    C("bfr_prev_amt", "전전기 금액", "AMT_KRW", null=True, src="bfefrmtrm_amount"),
    C("sort_ord_no", "정렬 순서 번호", "ROW_NO", src="ord"),
    C("crncy_cd", "통화 코드", "CODE_V50", code="CRNCY", src="currency"),
] + LIN_A, fks=[("fin_rpt_id", "s_fin_rpt", "fin_rpt_id"), ("corp_cd", "s_corp", "corp_cd")],
  src="A support/financial_items_all.csv (corp_name·stock_code·sj_nm 은 정규화로 제거)")

# ---------------- SILVER : B (토스증권) ----------------
T("s_stock", "SILVER", "종목", "종목코드당 1행", ["stock_cd"], [
    C("stock_cd", "종목 코드", "STOCK_CD", src="security_master.symbol"),
    C("stock_nm", "종목명", "NAME_V200", src="security_master.name"),
    C("stock_eng_nm", "종목 영문명", "NAME_V200", src="security_master.englishName"),
    C("isin_cd", "ISIN 코드", "ISIN_CD", src="security_master.isinCode"),
    C("mkt_cd", "시장 코드", "CODE_V50", code="MKT", src="security_master.market"),
    C("sec_type_cd", "증권 유형 코드", "CODE_V50", code="SEC_TYPE", src="security_master.securityType"),
    C("cmn_shr_yn", "보통 주식 여부", "YN", code="YN", src="security_master.isCommonShare (True/False→Y/N)"),
    C("stock_stts_cd", "종목 상태 코드", "CODE_V50", code="STOCK_STTS", src="security_master.status"),
    C("crncy_cd", "통화 코드", "CODE_V50", code="CRNCY", src="security_master.currency"),
    C("list_dt", "상장 일자", "DATE", src="security_master.listDate"),
    C("delist_dt", "상장폐지 일자", "DATE", null=True, src="security_master.delistDate"),
    C("outstd_shr_qty", "발행 주식 수량", "QTY", src="security_master.sharesOutstanding"),
    C("lvrg_val", "레버리지 값", "DEC_VAL", null=True, src="security_master.leverageFactor"),
    C("mkt_dtl_txt", "시장 상세 내용(JSON)", "TEXT_LONG", src="security_master.koreanMarketDetail"),
] + LIN_B, src="B silver/security_master.csv")

T("s_stock_daily_prc", "SILVER", "종목 일별 가격", "종목·거래일당 1행", ["stock_cd", "trd_dt"], [
    C("stock_cd", "종목 코드", "STOCK_CD", src="stock_daily_price.symbol"),
    C("trd_dt", "거래 일자", "DATE", src="stock_daily_price.trade_date"),
    C("candle_dttm", "봉 일시", "DATETIME", src="stock_daily_price.timestamp (+09:00 → KST DATETIME)"),
    C("open_prc", "시가 가격", "PRICE", src="open_price"),
    C("high_prc", "고가 가격", "PRICE", src="high_price"),
    C("low_prc", "저가 가격", "PRICE", src="low_price"),
    C("close_prc", "종가 가격", "PRICE", src="close_price"),
    C("trd_qty", "거래 수량", "QTY", src="volume"),
    C("crncy_cd", "통화 코드", "CODE_V50", code="CRNCY", src="currency"),
] + LIN_B, fks=[("stock_cd", "s_stock", "stock_cd")], src="B silver/stock_daily_price.csv")

T("s_idx_daily_prc", "SILVER", "지수 일별 가격", "지수·거래일당 1행", ["idx_cd", "trd_dt"], [
    C("idx_cd", "지수 코드", "CODE_V50", code="IDX", src="market_index_daily.index_code"),
    C("trd_dt", "거래 일자", "DATE", src="trade_date"),
    C("candle_dttm", "봉 일시", "DATETIME", src="timestamp"),
    C("open_prc", "시가 가격", "PRICE", src="open_price"),
    C("high_prc", "고가 가격", "PRICE", src="high_price"),
    C("low_prc", "저가 가격", "PRICE", src="low_price"),
    C("close_prc", "종가 가격", "PRICE", src="close_price"),
    C("trd_qty", "거래 수량", "QTY", src="volume (업무 단위 미확정: B 인계 참고)"),
] + LIN_B, src="B silver/market_index_daily.csv")

T("s_invstr_trd_daily", "SILVER", "투자자별 일별 매매", "종목·거래일·투자자유형당 1행", ["stock_cd", "trd_dt", "invstr_type_cd"], [
    C("stock_cd", "종목 코드", "STOCK_CD", src="investor_trading_daily.symbol"),
    C("trd_dt", "거래 일자", "DATE", src="trade_date"),
    C("invstr_type_cd", "투자자 유형 코드", "CODE_V50", code="INVSTR_TYPE", src="investor_type (camelCase→표준 코드)"),
    C("upper_invstr_type_cd", "상위 투자자 유형 코드", "CODE_V50", null=True, code="INVSTR_TYPE", src="parent_type"),
    C("aggr_lvl_cd", "집계 수준 코드", "CODE_V50", code="AGGR_LVL", src="aggregation_level"),
    C("buy_qty", "매수 수량", "QTY", src="buy_volume"),
    C("sell_qty", "매도 수량", "QTY", src="sell_volume"),
    C("net_buy_qty", "순매수 수량", "QTY", src="net_buy_volume"),
    C("src_col_nm", "원천 컬럼명", "NAME_V200", src="source_column"),
    C("src_json_path", "원천 JSON 경로", "PATH", src="json_path"),
] + LIN_B, fks=[("stock_cd", "s_stock", "stock_cd")], src="B silver/investor_trading_daily.csv")

T("s_frgn_hold_daily", "SILVER", "외국인 보유 일별", "종목·거래일당 1행", ["stock_cd", "trd_dt"], [
    C("stock_cd", "종목 코드", "STOCK_CD", src="foreign_holding_daily.symbol"),
    C("trd_dt", "거래 일자", "DATE", src="trade_date"),
    C("hold_qty", "보유 수량", "QTY", src="holding_quantity"),
    C("limit_qty", "한도 수량", "QTY", src="limit_quantity"),
    C("hold_rt", "보유 율", "RATE", src="holding_rate (소수 비율)"),
    C("src_col_nm", "원천 컬럼명", "NAME_V200", src="source_column"),
    C("src_json_path", "원천 JSON 경로", "PATH", src="json_path"),
] + LIN_B, fks=[("stock_cd", "s_stock", "stock_cd")], src="B silver/foreign_holding_daily.csv")

T("s_cfd_bal_daily", "SILVER", "CFD 잔고 일별", "종목·거래일당 1행", ["stock_cd", "trd_dt"], [
    C("stock_cd", "종목 코드", "STOCK_CD", src="cfd_daily.symbol"),
    C("trd_dt", "거래 일자", "DATE", src="trade_date"),
    C("buy_bal_qty", "매수 잔고 수량", "QTY", src="buy_balance_quantity"),
    C("buy_bal_rt", "매수 잔고 율", "RATE", src="buy_balance_rate"),
    C("sell_bal_qty", "매도 잔고 수량", "QTY", src="sell_balance_quantity"),
    C("sell_bal_rt", "매도 잔고 율", "RATE", src="sell_balance_rate"),
    C("src_col_nm", "원천 컬럼명", "NAME_V200", src="source_column"),
    C("src_json_path", "원천 JSON 경로", "PATH", src="json_path"),
] + LIN_B, fks=[("stock_cd", "s_stock", "stock_cd")], src="B silver/cfd_daily.csv")

# ---------------- SILVER : C (통합) ----------------
T("s_corp_stock_map", "SILVER", "기업-종목 매핑", "기업·종목 대응 1건당 1행(미연결 포함)", ["map_id"], [
    C("map_id", "매핑 식별자", "ID_V64", src="(C 생성) corp_cd|stock_cd"),
    C("corp_cd", "기업 코드", "CORP_CD", null=True, src="s_corp.corp_cd"),
    C("stock_cd", "종목 코드", "STOCK_CD", null=True, src="s_stock.stock_cd / s_corp.stock_cd"),
    C("map_stts_cd", "매핑 상태 코드", "CODE_V50", code="MAP_STTS"),
    C("map_mthd_cd", "매핑 방법 코드", "CODE_V50", code="MAP_MTHD"),
    C("cand_cnt", "후보 건수", "COUNT"),
    C("corp_nm", "기업명", "NAME_V200", null=True, src="s_corp.corp_nm (검증 근거)"),
    C("stock_nm", "종목명", "NAME_V200", null=True, src="s_stock.stock_nm (검증 근거)"),
    C("nm_match_yn", "명칭 일치 여부", "YN", code="YN"),
    C("map_rsn_txt", "매핑 사유 내용", "TEXT_V2000", null=True),
    C("pipln_ver", "파이프라인 버전", "VERSION"),
], fks=[("corp_cd", "s_corp", "corp_cd"), ("stock_cd", "s_stock", "stock_cd")], src="C 생성")

T("s_conn_stts", "SILVER", "가격·수급 연결 상태", "종목·거래일 키 합집합당 1행", ["stock_cd", "trd_dt"], [
    C("stock_cd", "종목 코드", "STOCK_CD"),
    C("trd_dt", "거래 일자", "DATE"),
    C("corp_cd", "기업 코드", "CORP_CD", null=True),
    C("map_stts_cd", "매핑 상태 코드", "CODE_V50", code="MAP_STTS"),
    C("prc_exist_yn", "가격 존재 여부", "YN", code="YN", src="B price_investor_availability.has_price 대응"),
    C("invstr_exist_yn", "수급 존재 여부", "YN", code="YN", src="B price_investor_availability.has_investor_data 대응"),
    C("frgn_hold_exist_yn", "외국인 보유 존재 여부", "YN", code="YN"),
    C("cfd_exist_yn", "CFD 잔고 존재 여부", "YN", code="YN"),
    C("fin_avail_yn", "재무 가용 여부(시점 기준)", "YN", code="YN"),
    C("conn_stts_cd", "연결 상태 코드", "CODE_V50", code="CONN_STTS"),
    C("miss_rsn_cd", "부재 사유 코드", "CODE_V50", null=True, code="MISS_RSN"),
    C("miss_rsn_txt", "부재 사유 내용", "TEXT_V2000", null=True),
    C("pipln_ver", "파이프라인 버전", "VERSION"),
], fks=[("stock_cd", "s_stock", "stock_cd")], src="C 생성 (가격 ∪ 수급 키, 내부조인 아님)")

T("s_dq_issue", "SILVER", "데이터 품질 이슈", "이슈 1건당 1행", ["issue_id"], [
    C("issue_id", "이슈 식별자", "ID_V64"),
    C("detect_stage_cd", "탐지 단계 코드", "CODE_V50", code="DETECT_STAGE"),
    C("src_team_cd", "원천 팀 코드", "CODE_V50", code="TEAM"),
    C("tbl_nm", "테이블명", "NAME_V200"),
    C("col_nm", "컬럼명", "NAME_V200", null=True),
    C("rcrd_key_txt", "레코드 키 내용", "TEXT_V2000", null=True),
    C("src_file_path", "원천 파일 경로", "PATH", null=True),
    C("src_row_no", "원천 행 번호", "ROW_NO", null=True),
    C("issue_type_cd", "이슈 유형 코드", "CODE_V50", code="ISSUE_TYPE"),
    C("sev_cd", "심각도 코드", "CODE_V50", code="SEV"),
    C("issue_rsn_txt", "이슈 사유 내용", "TEXT_V2000"),
    C("resolve_stts_cd", "조치 상태 코드", "CODE_V50", code="RESOLVE_STTS"),
    C("pipln_ver", "파이프라인 버전", "VERSION"),
], src="A review_issues + B data_quality_issues/bronze_unresolved/pending + C 통합 검증")

# ---------------- GOLD ----------------
T("g_ai_stock_daily", "GOLD", "AI 학습용 종목 일별 데이터셋", "종목·거래일당 1행(가격 기준)", ["stock_cd", "trd_dt"], [
    C("stock_cd", "종목 코드", "STOCK_CD"),
    C("trd_dt", "거래 일자", "DATE"),
    C("corp_cd", "기업 코드", "CORP_CD", null=True),
    C("mkt_cd", "시장 코드", "CODE_V50", code="MKT"),
    C("open_prc", "시가 가격", "PRICE"),
    C("high_prc", "고가 가격", "PRICE"),
    C("low_prc", "저가 가격", "PRICE"),
    C("close_prc", "종가 가격", "PRICE"),
    C("trd_qty", "거래 수량", "QTY"),
    C("close_rtn_rt", "종가 수익률(전 관측일 대비)", "RATE", null=True),
    C("idx_close_prc", "지수 종가 가격", "PRICE", null=True),
    C("idx_rtn_rt", "지수 수익률(전 관측일 대비)", "RATE", null=True),
    C("indv_net_buy_qty", "개인 순매수 수량", "QTY", null=True),
    C("frgn_net_buy_qty", "외국인 순매수 수량", "QTY", null=True),
    C("inst_net_buy_qty", "기관 순매수 수량", "QTY", null=True),
    C("other_corp_net_buy_qty", "기타법인 순매수 수량", "QTY", null=True),
    C("frgn_hold_rt", "외국인 보유 율", "RATE", null=True),
    C("cfd_buy_bal_rt", "CFD 매수 잔고 율", "RATE", null=True),
    C("invstr_exist_yn", "수급 존재 여부", "YN", code="YN"),
    C("fin_avail_yn", "재무 가용 여부", "YN", code="YN"),
    C("fin_rpt_id", "재무 보고서 식별자", "ID_V64", null=True),
    C("fin_bsns_yr", "재무 사업 연도", "YEAR", null=True),
    C("fin_rpt_cd", "재무 보고서 코드", "CODE_V50", null=True, code="RPT"),
    C("fin_fs_div_cd", "재무 재무제표 구분 코드", "CODE_V50", null=True, code="FS_DIV"),
    C("dscl_dt", "공시 일자", "DATE", null=True),
    C("dscl_elps_day_cnt", "공시 경과 일 건수", "COUNT", null=True),
    C("rev_ytd_amt", "매출 누적 금액", "AMT_KRW", null=True),
    C("op_prft_ytd_amt", "영업 이익 누적 금액", "AMT_KRW", null=True),
    C("net_incm_ytd_amt", "순이익 누적 금액", "AMT_KRW", null=True),
    C("op_cf_ytd_amt", "영업 현금흐름 누적 금액", "AMT_KRW", null=True),
    C("tot_asst_amt", "총 자산 금액", "AMT_KRW", null=True),
    C("tot_liab_amt", "총 부채 금액", "AMT_KRW", null=True),
    C("tot_eqty_amt", "총 자본 금액", "AMT_KRW", null=True),
    C("pipln_ver", "파이프라인 버전", "VERSION"),
], fks=[("stock_cd", "s_stock", "stock_cd"), ("fin_rpt_id", "s_fin_rpt", "fin_rpt_id")],
  src="s_stock_daily_prc ⟕ s_invstr_trd_daily(TOP_LEVEL) ⟕ s_frgn_hold_daily ⟕ s_cfd_bal_daily ⟕ s_idx_daily_prc ⟕ 시점 기준 s_fin_rpt/s_fin_mtrc")

T("g_fin_rpt_mkt_smry", "GOLD", "재무 보고기간 시장 요약", "재무 보고서당 1행", ["fin_rpt_id"], [
    C("fin_rpt_id", "재무 보고서 식별자", "ID_V64"),
    C("corp_cd", "기업 코드", "CORP_CD"),
    C("stock_cd", "종목 코드", "STOCK_CD"),
    C("bsns_yr", "사업 연도", "YEAR"),
    C("rpt_cd", "보고서 코드", "CODE_V50", code="RPT"),
    C("fs_div_cd", "재무제표 구분 코드", "CODE_V50", code="FS_DIV"),
    C("prd_start_dt", "기간 시작 일자", "DATE"),
    C("prd_end_dt", "기간 종료 일자", "DATE"),
    C("same_prd_cmpr_elig_yn", "동일 기간 비교 적격 여부", "YN", code="YN"),
    C("trd_day_cnt", "거래 일 건수", "COUNT"),
    C("full_cvrg_yn", "기간 전체 커버리지 여부", "YN", code="YN"),
    C("first_close_prc", "첫 종가 가격", "PRICE", null=True),
    C("last_close_prc", "마지막 종가 가격", "PRICE", null=True),
    C("prd_rtn_rt", "기간 수익률", "RATE", null=True),
    C("frgn_net_buy_qty", "외국인 순매수 수량(기간 합)", "QTY", null=True),
    C("inst_net_buy_qty", "기관 순매수 수량(기간 합)", "QTY", null=True),
    C("indv_net_buy_qty", "개인 순매수 수량(기간 합)", "QTY", null=True),
    C("rev_ytd_amt", "매출 누적 금액", "AMT_KRW", null=True),
    C("op_prft_ytd_amt", "영업 이익 누적 금액", "AMT_KRW", null=True),
    C("op_cf_ytd_amt", "영업 현금흐름 누적 금액", "AMT_KRW", null=True),
    C("pipln_ver", "파이프라인 버전", "VERSION"),
], fks=[("fin_rpt_id", "s_fin_rpt", "fin_rpt_id")], src="s_fin_rpt + s_fin_mtrc + s_stock_daily_prc + s_invstr_trd_daily (A 인계 '방법 B')")

# ---------------- META ----------------
T("m_exec_log", "META", "실행 기록", "실행·절차·테이블당 1행", ["run_id", "step_nm", "tbl_nm"], [
    C("run_id", "실행 식별자", "ID_V64"),
    C("step_nm", "절차명", "NAME_V200"),
    C("tbl_nm", "테이블명", "NAME_V200"),
    C("layer_cd", "계층 코드", "CODE_V50", code="LAYER"),
    C("input_ver", "입력 버전", "VERSION"),
    C("rcrd_cnt", "레코드 건수", "COUNT"),
    C("start_dttm", "시작 일시", "DATETIME"),
    C("end_dttm", "종료 일시", "DATETIME"),
    C("run_stts_cd", "실행 상태 코드", "CODE_V50", code="RUN_STTS"),
    C("pipln_ver", "파이프라인 버전", "VERSION"),
], src="C run_pipeline.py / load_mysql.py")

# 표준 사전 자체(메타)
T("m_std_word", "META", "표준 단어", "단어당 1행", ["word_nm"], [
    C("word_nm", "단어 물리명", "NAME_V200"), C("word_kor_nm", "단어 한글명", "NAME_V200"),
    C("word_eng_nm", "단어 영문명", "NAME_V200"), C("word_cls_cd", "단어 분류 코드", "CODE_V50"),
])
T("m_std_dmn", "META", "표준 도메인", "도메인당 1행", ["dmn_nm"], [
    C("dmn_nm", "도메인명", "NAME_V200"), C("cls_word_nm", "분류어명", "NAME_V200"),
    C("data_type_nm", "데이터 유형명", "NAME_V200"), C("data_len_txt", "데이터 길이 내용", "TEXT_V2000"),
    C("allow_ptrn_txt", "허용 패턴 내용", "TEXT_V2000"), C("dmn_desc_txt", "도메인 설명 내용", "TEXT_V2000"),
])
T("m_std_term", "META", "표준 용어(컬럼)", "테이블·컬럼당 1행", ["tbl_nm", "col_nm"], [
    C("tbl_nm", "테이블명", "NAME_V200"), C("col_nm", "컬럼명", "NAME_V200"),
    C("term_kor_nm", "용어 한글명", "NAME_V200"), C("dmn_nm", "도메인명", "NAME_V200"),
    C("data_type_nm", "데이터 유형명", "NAME_V200"), C("null_allow_yn", "널 허용 여부", "YN"),
    C("pk_yn", "기본키 여부", "YN"), C("cd_grp_id", "코드그룹 식별자", "ID_V64", null=True),
    C("layer_cd", "계층 코드", "CODE_V50"), C("asis_src_txt", "현행 원천 내용", "TEXT_V2000", null=True),
])

RESERVED = {"select", "from", "where", "order", "group", "key", "desc", "limit", "table", "type", "year", "date", "rank"}


def check_name(phys: str, dmn: str | None = None) -> list[str]:
    """표준 단어 조합 규칙 검사. 위반 사유 목록 반환(빈 목록=준수)."""
    errs = []
    import re
    if not re.fullmatch(r"[a-z][a-z0-9_]*", phys):
        errs.append("소문자 snake_case 아님")
    if len(phys) > 40:
        errs.append("40자 초과")
    if phys in RESERVED:
        errs.append("예약어 단독 사용")
    toks = phys.split("_")
    unknown = [t for t in toks if t not in WORDS]
    if unknown:
        errs.append("미등록 단어:" + ",".join(unknown))
    last = toks[-1]
    if last not in WORDS or WORDS[last][2] != "CLASS":
        errs.append("분류어로 끝나지 않음")
    if dmn is not None and not errs:
        if dmn not in DOMAINS:
            errs.append("미등록 도메인")
        elif DOMAINS[dmn][0] != last:
            errs.append(f"분류어({last})와 도메인({dmn}) 불일치")
    return errs


def self_check():
    bad = []
    for t in TABLES.values():
        names = [c["phys"] for c in t["cols"]]
        assert len(names) == len(set(names)), t["name"]
        for p in t["pk"]:
            assert p in names, (t["name"], p)
        for c in t["cols"]:
            e = check_name(c["phys"], c["dmn"])
            if e:
                bad.append((t["name"], c["phys"], e))
            if c["code"]:
                assert c["code"] in CODES, c["code"]
    return bad


if __name__ == "__main__":
    print("violations:", self_check())
    print(len(WORDS), "words", len(DOMAINS), "domains", len(TABLES), "tables",
          sum(len(t["cols"]) for t in TABLES.values()), "columns")
