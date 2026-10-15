"""표준 사전 산출물 + MySQL DDL + ERD(개념·논리·물리·메달리온 흐름) 생성.

실행: python code/build_model.py [--a-dir ...] [--b-dir ...]   (run_pipeline.py 이후 실행 권장)
출력: 02_standard_dictionary/, 03_model/ddl/, 03_model/erd/
"""
from __future__ import annotations
import argparse, re, subprocess
from pathlib import Path

import pandas as pd

from common import ROOT, input_dirs, read_csv, write_csv, A_FILES, B_FILES
from std_dictionary import WORDS, DOMAINS, CODES, TABLES, STD_VERSION, PIPELINE_VERSION, check_name

DICT = ROOT / "02_standard_dictionary"
DDL = ROOT / "03_model" / "ddl"
ERD = ROOT / "03_model" / "erd"
DB = {"BRONZE": "tz_bronze", "SILVER": "tz_silver", "GOLD": "tz_gold", "META": "tz_meta"}

# Bronze 적재 대상(인계 원본 그대로) — 논리명: (팀, 상대경로)
BRONZE_SRC = {f"b_a_{k}": ("A", v) for k, v in A_FILES.items()} | \
             {f"b_b_{k}": ("B", v) for k, v in B_FILES.items()}
LONG_TEXT_COLS = {"koreanMarketDetail", "individual", "foreigner", "institution", "otherCorporation",
                  "foreignerHolding", "cfd", "api_record_json"}


def code_rows(metric_defs: pd.DataFrame):
    CODES["MTRC"] = ("재무 지표", [(m.upper(), l, i + 1, m) for i, (m, l) in enumerate(zip(metric_defs.metric, metric_defs.label_ko))])
    return [dict(cd_grp_id=g, cd_grp_nm=gn, cd_val=v, cd_nm=n, sort_ord_no=o, asis_val_txt=a)
            for g, (gn, items) in CODES.items() for v, n, o, a in items]


# ---------------------------------------------------------------- 사전 산출물
def build_dictionary(metric_defs):
    words = pd.DataFrame([dict(word_nm=k, word_kor_nm=v[0], word_eng_nm=v[1], word_cls_cd=v[2],
                               used_col_cnt=sum(k in c["phys"].split("_") for t in TABLES.values() for c in t["cols"]))
                          for k, v in WORDS.items()])
    dom = pd.DataFrame([dict(dmn_nm=k, cls_word_nm=v[0], data_type_nm=v[1], data_len_txt=v[2], allow_ptrn_txt=v[3],
                             dmn_desc_txt=v[4]) for k, v in DOMAINS.items()])
    codes = pd.DataFrame(code_rows(metric_defs))
    terms = []
    for t in TABLES.values():
        for c in t["cols"]:
            terms.append(dict(layer_cd=t["layer"], tbl_nm=t["name"], tbl_kor_nm=t["kor"], col_nm=c["phys"],
                              term_kor_nm=c["kor"], dmn_nm=c["dmn"], data_type_nm=DOMAINS[c["dmn"]][1],
                              null_allow_yn="Y" if c["null"] else "N", pk_yn="Y" if c["phys"] in t["pk"] else "N",
                              cd_grp_id=c["code"], asis_src_txt=c["src"],
                              word_combination=" + ".join(f"{w}({WORDS[w][0]})" for w in c["phys"].split("_")),
                              std_check="OK" if not check_name(c["phys"], c["dmn"]) else ";".join(check_name(c["phys"], c["dmn"]))))
    terms = pd.DataFrame(terms)
    # 같은 물리명은 같은 한글 의미·도메인이어야 함(동음이의 금지) 점검
    amb = terms.groupby("col_nm").dmn_nm.nunique()
    assert (amb == 1).all(), f"동일 물리명 다른 도메인: {list(amb[amb > 1].index)}"
    tbls = pd.DataFrame([dict(layer_cd=t["layer"], db_nm=DB[t["layer"]], tbl_nm=t["name"], tbl_kor_nm=t["kor"],
                              grain_txt=t["grain"], pk_txt="+".join(t["pk"]),
                              fk_txt="; ".join(f"{a}→{b}.{c}" for a, b, c in t["fks"]),
                              logical_fk_txt="; ".join(f"{a}→{b}.{c} ({n})" for a, b, c, n in t["logical_fks"]),
                              col_cnt=len(t["cols"]), src_txt=t["src"]) for t in TABLES.values()])
    rules = pd.DataFrame([
        ("R01", "물리명은 소문자 snake_case, 영문 시작", "정규식 ^[a-z][a-z0-9_]*$"),
        ("R02", "물리명 = 표준 단어 토큰의 조합", "모든 토큰이 std_word 에 등록돼야 함"),
        ("R03", "마지막 토큰은 분류어(class word)", "id·cd·nm·no·dt·dttm·yr·amt·prc·qty·rt·val·yn·cnt·txt·path·hash·ver"),
        ("R04", "분류어가 도메인을 결정", "예) *_dt→DATE, *_yn→YN(CHAR1 Y/N), *_amt→AMT_KRW(DECIMAL(20,0))"),
        ("R05", "같은 물리명 = 같은 의미·같은 도메인", "동음이의 금지: stock_cd 는 모든 테이블에서 CHAR(6) 종목코드"),
        ("R06", "같은 의미 = 같은 물리명", "이음동의 금지: symbol·stock_code → stock_cd, _source_file·source_file → src_file_path"),
        ("R07", "물리명 길이 ≤ 40자, SQL 예약어 단독 사용 금지", "type·date·year·key 등 단독 사용 불가"),
        ("R08", "테이블 접두사 = 계층", "b_(Bronze) s_(Silver) g_(Gold) m_(Meta)"),
        ("R09", "코드 컬럼(*_cd)은 공통코드 허용값만", "s_cmn_cd 코드그룹, 코드값은 대문자 snake(UPPER_CODE)"),
        ("R10", "여부 컬럼(*_yn)은 Y/N 두 값만", "True/true/1 혼용 금지"),
        ("R11", "일자는 DATE(YYYY-MM-DD, KST), 일시는 KST DATETIME", "YYYYMMDD·오프셋 문자열은 변환 후 적재"),
        ("R12", "빈값은 NULL, 0 대체 금지", "금액·수량의 결측과 0을 구분"),
    ], columns=["rule_id", "rule_txt", "detail_txt"])
    colmap = terms[terms.layer_cd == "SILVER"][["tbl_nm", "col_nm", "term_kor_nm", "asis_src_txt"]]

    DICT.mkdir(parents=True, exist_ok=True)
    write_csv(words, DICT / "std_word.csv"); write_csv(dom, DICT / "std_domain.csv")
    write_csv(codes, DICT / "std_code.csv"); write_csv(terms, DICT / "std_term.csv")
    write_csv(tbls, DICT / "std_table.csv"); write_csv(rules, DICT / "std_naming_rule.csv")
    write_csv(colmap, DICT / "asis_tobe_column_map.csv")
    with pd.ExcelWriter(DICT / "AI_데이터_표준사전.xlsx", engine="openpyxl") as xw:
        info = pd.DataFrame([("표준 버전", STD_VERSION), ("파이프라인 버전", PIPELINE_VERSION),
                             ("단어", len(words)), ("도메인", len(dom)), ("코드그룹", codes.cd_grp_id.nunique()),
                             ("코드값", len(codes)), ("테이블", len(tbls)), ("용어(컬럼)", len(terms))], columns=["항목", "값"])
        for nm, df in [("개요", info), ("조합규칙", rules), ("표준단어", words), ("표준도메인", dom), ("표준코드", codes),
                       ("표준용어_컬럼", terms), ("테이블", tbls), ("AS-IS_TO-BE_매핑", colmap)]:
            df.to_excel(xw, sheet_name=nm, index=False)
            ws = xw.sheets[nm]
            for i, col in enumerate(df.columns, 1):
                w = max([len(str(col))] + [len(str(v)) for v in df[col].head(200)])
                ws.column_dimensions[ws.cell(1, i).column_letter].width = min(60, max(8, w * 1.3))
            ws.freeze_panes = "A2"
    return terms


# ---------------------------------------------------------------- DDL
def col_ddl(c, tname):
    typ = DOMAINS[c["dmn"]][1]
    s = f"  `{c['phys']}` {typ}{'' if c['null'] else ' NOT NULL'} COMMENT '{c['kor']}'"
    return s


def checks(t):
    out = []
    for c in t["cols"]:
        p, d = c["phys"], c["dmn"]
        nullok = f"`{p}` IS NULL OR " if c["null"] else ""
        if c["code"] and c["code"] not in ("MTRC",):
            vals = ",".join(f"'{v}'" for v, *_ in CODES[c["code"]][1])
            out.append(f"  CONSTRAINT `ck_{t['name']}_{p}` CHECK ({nullok}`{p}` IN ({vals}))")
        elif d in ("CORP_CD", "STOCK_CD", "RCEPT_NO", "YEAR", "ISIN_CD"):
            rx = {"CORP_CD": "^[0-9]{8}$", "STOCK_CD": "^[0-9]{6}$", "RCEPT_NO": "^[0-9]{14}$", "YEAR": "^[0-9]{4}$",
                  "ISIN_CD": "^[A-Z]{2}[A-Z0-9]{9}[0-9]$"}[d]
            out.append(f"  CONSTRAINT `ck_{t['name']}_{p}` CHECK ({nullok}REGEXP_LIKE(`{p}`, '{rx}', 'c'))")
        elif d in ("PRICE", "COUNT") :
            out.append(f"  CONSTRAINT `ck_{t['name']}_{p}` CHECK ({nullok}`{p}` >= 0)")
    # 업무 규칙
    if t["name"] in ("s_stock_daily_prc", "s_idx_daily_prc"):
        out.append(f"  CONSTRAINT `ck_{t['name']}_ohlc` CHECK (`high_prc` >= `low_prc` AND `high_prc` >= `open_prc` AND `high_prc` >= `close_prc` AND `low_prc` <= `open_prc` AND `low_prc` <= `close_prc`)")
    if t["name"] == "s_invstr_trd_daily":
        out.append("  CONSTRAINT `ck_s_invstr_trd_daily_net` CHECK (`buy_qty` - `sell_qty` = `net_buy_qty`)")
    if t["name"] == "s_frgn_hold_daily":
        out.append("  CONSTRAINT `ck_s_frgn_hold_daily_rt` CHECK (`hold_rt` BETWEEN 0 AND 1)")
    return out


def table_ddl(t, physical_fk=True):
    lines = [col_ddl(c, t["name"]) for c in t["cols"]]
    lines.append(f"  PRIMARY KEY ({', '.join('`'+p+'`' for p in t['pk'])})")
    if physical_fk and t["layer"] == "SILVER":
        for a, b, c in t["fks"]:
            lines.append(f"  CONSTRAINT `fk_{t['name']}_{a}` FOREIGN KEY (`{a}`) REFERENCES `{b}` (`{c}`)")
    lines += checks(t)
    fk_note = "; ".join(f"{a}->{b}.{c}" for a, b, c in t["fks"]) if t["layer"] == "GOLD" else ""
    cm = t["kor"] + " | 단위: " + t["grain"] + (" | 논리FK: " + fk_note if fk_note else "")
    return (f"CREATE TABLE `{t['name']}` (\n" + ",\n".join(lines) +
            f"\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='{cm}';\n")


SILVER_ORDER = ["s_cmn_cd", "s_corp", "s_stock", "s_dscl", "s_dscl_doc", "s_fin_rpt", "s_fin_mtrc_def", "s_fin_mtrc",
                "s_fin_item", "s_stock_daily_prc", "s_idx_daily_prc", "s_invstr_trd_daily", "s_frgn_hold_daily",
                "s_cfd_bal_daily", "s_corp_stock_map", "s_conn_stts", "s_dq_issue"]


def bronze_ddl(adir: Path, bdir: Path):
    out = []
    for tname, (team, rel) in BRONZE_SRC.items():
        base = adir if team == "A" else bdir
        hdr = list(read_csv(base / rel).columns) if (base / rel).stat().st_size < 2_000_000 else \
            pd.read_csv(base / rel, dtype=str, nrows=0, encoding="utf-8-sig").columns.tolist()
        cols = ["  `ldng_row_no` INT NOT NULL COMMENT '적재 행 번호(원천 CSV 데이터 행, 1부터)'"]
        for h in hdr:
            typ = "MEDIUMTEXT" if h in LONG_TEXT_COLS else "TEXT"
            cols.append(f"  `{h}` {typ} NULL COMMENT 'AS-IS 원본 컬럼(문자열 그대로)'")
        cols += ["  `ldng_file_path` VARCHAR(500) NOT NULL COMMENT '적재 원천 파일(인계 폴더 기준)'",
                 "  `ldng_file_hash` VARCHAR(80) NOT NULL COMMENT '적재 원천 파일 SHA-256'",
                 "  `ldng_run_id` VARCHAR(64) NOT NULL COMMENT '적재 실행 식별자'",
                 "  PRIMARY KEY (`ldng_row_no`)"]
        out.append(f"CREATE TABLE `{tname}` (\n" + ",\n".join(cols) +
                   f"\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin COMMENT='Bronze 랜딩: {team} {rel} (AS-IS 그대로, 전 컬럼 TEXT)';\n")
    return out


def build_ddl(adir, bdir):
    DDL.mkdir(parents=True, exist_ok=True)
    hdr = f"-- TEAM ZERO Medallion (MySQL 8.0) — 자동 생성: code/build_model.py · 표준 {STD_VERSION}\n"
    (DDL / "00_databases.sql").write_text(hdr + "\n".join(
        f"CREATE DATABASE IF NOT EXISTS `{d}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin;" for d in DB.values()) + "\n", encoding="utf-8")
    (DDL / "01_bronze.sql").write_text(hdr + "USE `tz_bronze`;\n\n" + "\n".join(
        f"DROP TABLE IF EXISTS `{n}`;" for n in BRONZE_SRC) + "\n\n" + "\n".join(bronze_ddl(adir, bdir)), encoding="utf-8")
    sil = [TABLES[n] for n in SILVER_ORDER]
    (DDL / "02_silver.sql").write_text(hdr + "USE `tz_silver`;\nSET FOREIGN_KEY_CHECKS = 0;\n" + "\n".join(
        f"DROP TABLE IF EXISTS `{t['name']}`;" for t in reversed(sil)) + "\nSET FOREIGN_KEY_CHECKS = 1;\n\n" +
        "\n".join(table_ddl(t) for t in sil), encoding="utf-8")
    gold = [t for t in TABLES.values() if t["layer"] == "GOLD"]
    (DDL / "03_gold.sql").write_text(hdr + "USE `tz_gold`;\n" + "\n".join(f"DROP TABLE IF EXISTS `{t['name']}`;" for t in gold) +
                                     "\n\n" + "\n".join(table_ddl(t) for t in gold), encoding="utf-8")
    meta = [t for t in TABLES.values() if t["layer"] == "META"]
    m = []
    for t in meta:
        d = table_ddl(t)
        if t["name"] == "m_exec_log":   # 실행 기록은 누적 보존
            m.append(d.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS"))
            # 누적 보존 테이블은 표준 변경 시 컬럼 정의를 맞춘다(스키마 드리프트 방지)
            m.append(f"ALTER TABLE `{t['name']}`\n" + ",\n".join("  MODIFY" + col_ddl(c, t["name"])[1:] for c in t["cols"]) + ";\n")
        else:
            m.append(f"DROP TABLE IF EXISTS `{t['name']}`;\n" + d)
    (DDL / "04_meta.sql").write_text(hdr + "USE `tz_meta`;\n\n" + "\n".join(m), encoding="utf-8")


# ---------------------------------------------------------------- ERD
FONT = "Noto Sans CJK KR"
LAYER_COLOR = {"BRONZE": "#c8875a", "SILVER": "#8c9aa8", "GOLD": "#d4a72c", "META": "#7b8d6f"}
LAYER_FILL = {"BRONZE": "#f7ede5", "SILVER": "#eef1f4", "GOLD": "#fbf4dd", "META": "#eef2ea"}
TEAM_OF = {"s_corp": "A", "s_dscl": "A", "s_dscl_doc": "A", "s_fin_rpt": "A", "s_fin_mtrc_def": "A", "s_fin_mtrc": "A",
           "s_fin_item": "A", "s_stock": "B", "s_stock_daily_prc": "B", "s_idx_daily_prc": "B", "s_invstr_trd_daily": "B",
           "s_frgn_hold_daily": "B", "s_cfd_bal_daily": "B"}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(dot: str, stem: str):
    ERD.mkdir(parents=True, exist_ok=True)
    p = ERD / f"{stem}.dot"
    p.write_text(dot, encoding="utf-8")
    for fmt in ("png", "svg"):
        subprocess.run(["dot", f"-T{fmt}", "-Gdpi=130" if fmt == "png" else "-Gdpi=72", str(p), "-o", str(ERD / f"{stem}.{fmt}")], check=True)


def rel_edges(physical=True):
    e = []
    for t in TABLES.values():
        if t["layer"] == "META":
            continue
        for a, b, c in t["fks"]:
            e.append((t["name"], b, a, False))
        for a, b, c, _n in t["logical_fks"]:
            e.append((t["name"], b, a, True))
    # 코드/매핑 관계(개념)
    e.append(("s_corp_stock_map", "s_corp", "corp_cd", False))
    e.append(("s_conn_stts", "s_stock_daily_prc", "stock_cd+trd_dt", True))
    e.append(("s_conn_stts", "s_invstr_trd_daily", "stock_cd+trd_dt", True))
    return list(dict.fromkeys(e))


def erd_conceptual():
    g = [f'digraph G {{ graph [rankdir=LR, fontname="{FONT}", fontsize=20, labelloc=t, label="TEAM ZERO 개념 ERD (주제영역 · 엔터티 · 관계)", pad=0.4, nodesep=0.35, ranksep=0.9];',
         f'node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=13, margin="0.18,0.08"]; edge [fontname="{FONT}", fontsize=10, color="#555555", arrowhead=none];']
    groups = {"A · OpenDART (기업·공시·재무)": ["s_corp", "s_dscl", "s_dscl_doc", "s_fin_rpt", "s_fin_mtrc_def", "s_fin_mtrc", "s_fin_item"],
              "B · 토스증권 (종목·시세·수급)": ["s_stock", "s_stock_daily_prc", "s_idx_daily_prc", "s_invstr_trd_daily", "s_frgn_hold_daily", "s_cfd_bal_daily"],
              "C · 통합·품질": ["s_corp_stock_map", "s_conn_stts", "s_dq_issue", "s_cmn_cd"],
              "Gold · AI 활용": ["g_ai_stock_daily", "g_fin_rpt_mkt_smry"]}
    fills = ["#e8f0fb", "#fdeee6", "#eaf5ea", "#fbf4dd"]
    for i, (gn, ts) in enumerate(groups.items()):
        g.append(f'subgraph cluster_{i} {{ label="{gn}"; style="rounded,filled"; fillcolor="{fills[i]}"; color="#bbbbbb"; fontsize=15;')
        for t in ts:
            g.append(f'"{t}" [label="{TABLES[t]["kor"]}", fillcolor="white"];')
        g.append("}")
    card = {}
    for src, dst, a, logical in rel_edges():
        lab = "N : 1" if not logical else "N : 1 (논리)"
        g.append(f'"{dst}" -> "{src}" [label="{lab}", style={"dashed" if logical else "solid"}];')
    g.append('"s_corp_stock_map" -> "s_stock" [label="1 : 1"];')
    g.append('"g_ai_stock_daily" -> "s_conn_stts" [label="1 : 1", style=dashed];')
    g.append("}")
    render("\n".join(g), "01_conceptual_erd")


def erd_table(physical: bool, stem: str, title: str, layers=("SILVER", "GOLD")):
    g = [f'digraph G {{ graph [rankdir=LR, fontname="{FONT}", fontsize=22, labelloc=t, label="{title}", pad=0.4, nodesep=0.25, ranksep=1.1, splines=true, concentrate=false];',
         f'node [shape=plaintext, fontname="{FONT}", fontsize=10]; edge [fontname="{FONT}", fontsize=9, color="#666666", arrowhead=crow, arrowtail=tee, dir=both];']
    for t in TABLES.values():
        if t["layer"] not in layers:
            continue
        fk_cols = {a for a, *_ in t["fks"]} | {a for a, *_ in t["logical_fks"]}
        head = esc(t["name"] + "  ·  " + t["kor"]) if physical else esc(t["kor"])
        team = TEAM_OF.get(t["name"], "C" if t["layer"] == "SILVER" else t["layer"])
        rows = [f'<tr><td bgcolor="{LAYER_COLOR[t["layer"]]}" colspan="{3 if physical else 2}"><font color="white"><b>{head}</b></font></td></tr>',
                f'<tr><td colspan="{3 if physical else 2}" bgcolor="{LAYER_FILL[t["layer"]]}"><font point-size="8">{esc(t["layer"])} · 담당 {team} · {esc(t["grain"])}</font></td></tr>']
        for c in t["cols"]:
            if c["phys"] in ("pipln_ver", "src_team_cd", "src_kind_cd", "src_ver", "fetch_dttm", "api_raw_file_path",
                             "api_rcrd_path", "bronze_row_no", "src_json_path", "src_col_nm") and not physical:
                continue
            key = ("PK " if c["phys"] in t["pk"] else "") + ("FK" if c["phys"] in fk_cols else "")
            name = c["phys"] if physical else c["kor"]
            bold = "<b>" if "PK" in key else ""
            ebold = "</b>" if "PK" in key else ""
            null = "" if c["null"] else " NN"
            if physical:
                rows.append(f'<tr><td align="left" port="{c["phys"]}">{bold}{esc(name)}{ebold}</td><td align="left"><font color="#555555">{esc(DOMAINS[c["dmn"]][1])}{null}</font></td><td align="left">{('<font color="#a33">'+key.strip()+'</font>') if key else ' '}</td></tr>')
            else:
                rows.append(f'<tr><td align="left" port="{c["phys"]}">{bold}{esc(name)}{ebold}</td><td align="left">{('<font color="#a33">'+key.strip()+'</font>') if key else ' '}</td></tr>')
        if not physical:
            rows.append(f'<tr><td colspan="2" align="left"><font point-size="8" color="#777777">+ 출처 추적 속성(원천 파일·행·버전)</font></td></tr>')
        g.append(f'"{t["name"]}" [label=<<table border="0" cellborder="1" cellspacing="0" cellpadding="3">{"".join(rows)}</table>>];')
    for src, dst, a, logical in rel_edges():
        if TABLES[src]["layer"] not in layers or TABLES[dst]["layer"] not in layers:
            continue
        col = a.split("+")[0]
        tp = f':"{col}"' if col in [c["phys"] for c in TABLES[src]["cols"]] else ""
        dp = f':"{col}"' if col in [c["phys"] for c in TABLES[dst]["cols"]] else ""
        g.append(f'"{dst}"{dp} -> "{src}"{tp} [style={"dashed" if logical else "solid"}];')
    g.append("}")
    render("\n".join(g), stem)


def erd_flow(counts: dict):
    g = [f'digraph G {{ graph [rankdir=LR, fontname="{FONT}", fontsize=22, labelloc=t, label="Medallion 흐름: Bronze(인계 원본) → Silver(표준) → Gold(AI 데이터셋)", pad=0.4, nodesep=0.15, ranksep=1.4];',
         f'node [shape=box, style="rounded,filled", fontname="{FONT}", fontsize=10]; edge [color="#888888", arrowsize=0.6];']
    src_of = {"s_corp": ["b_a_company_master"], "s_dscl": ["b_a_disclosures"], "s_dscl_doc": ["b_a_disclosure_documents"],
              "s_fin_rpt": ["b_a_financial_summary"], "s_fin_mtrc": ["b_a_financial_summary"], "s_fin_mtrc_def": ["b_a_metric_definitions"],
              "s_fin_item": ["b_a_financial_items"], "s_stock": ["b_b_security_master"], "s_stock_daily_prc": ["b_b_stock_daily_price"],
              "s_idx_daily_prc": ["b_b_market_index_daily"], "s_invstr_trd_daily": ["b_b_investor_trading_daily"],
              "s_frgn_hold_daily": ["b_b_foreign_holding_daily"], "s_cfd_bal_daily": ["b_b_cfd_daily"],
              "s_corp_stock_map": ["s_corp", "s_stock"], "s_conn_stts": ["s_stock_daily_prc", "s_invstr_trd_daily", "s_frgn_hold_daily", "s_cfd_bal_daily", "s_fin_rpt"],
              "s_dq_issue": ["b_a_review_issues", "b_b_data_quality_issues", "b_b_bronze_unresolved_issues", "b_b_pending_recovery_review"],
              "g_ai_stock_daily": ["s_stock_daily_prc", "s_idx_daily_prc", "s_invstr_trd_daily", "s_frgn_hold_daily", "s_cfd_bal_daily", "s_fin_rpt", "s_fin_mtrc", "s_dscl", "s_corp_stock_map"],
              "g_fin_rpt_mkt_smry": ["s_fin_rpt", "s_fin_mtrc", "s_stock_daily_prc", "s_invstr_trd_daily"]}
    for layer, names in (("BRONZE", list(BRONZE_SRC)), ("SILVER", SILVER_ORDER), ("GOLD", ["g_ai_stock_daily", "g_fin_rpt_mkt_smry"])):
        g.append(f'subgraph cluster_{layer} {{ label="{layer} ({DB[layer]})"; style="rounded,filled"; fillcolor="{LAYER_FILL[layer]}"; color="{LAYER_COLOR[layer]}"; fontsize=16;')
        for n in names:
            k = TABLES[n]["kor"] if n in TABLES else BRONZE_SRC[n][1].split("/")[-1]
            cnt = counts.get(n, "")
            g.append(f'"{n}" [label="{n}\\n{k}\\n{cnt:,}행" , fillcolor="white", color="{LAYER_COLOR[layer]}"];' if cnt != "" else
                     f'"{n}" [label="{n}\\n{k}", fillcolor="white", color="{LAYER_COLOR[layer]}"];')
        g.append("}")
    for dst, srcs in src_of.items():
        for s in srcs:
            g.append(f'"{s}" -> "{dst}";')
    g.append("}")
    render("\n".join(g), "00_medallion_flow")


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument("--a-dir"); ap.add_argument("--b-dir")
    a = ap.parse_args()
    adir, bdir = input_dirs(a.a_dir, a.b_dir)
    md = read_csv(adir / A_FILES["metric_definitions"])
    terms = build_dictionary(md)
    build_ddl(adir, bdir)
    counts = {}
    for sub in ("silver", "gold"):
        for p in (ROOT / "04_output" / sub).glob("*.csv"):
            with open(p, encoding="utf-8-sig") as f:
                counts[p.stem] = sum(1 for _ in f) - 1
    for n, (team, rel) in BRONZE_SRC.items():
        counts[n] = len(read_csv((adir if team == "A" else bdir) / rel))
    erd_flow(counts)
    erd_conceptual()
    erd_table(False, "02_logical_erd", "TEAM ZERO 논리 ERD (Silver·Gold, 한글 속성 · PK/FK)")
    erd_table(True, "03_physical_erd", "TEAM ZERO 물리 ERD (MySQL 8.0 · 표준 물리명 · 데이터 타입)")
    print("dictionary terms:", len(terms), "| std_check OK:", (terms.std_check == "OK").sum())


if __name__ == "__main__":
    main()
