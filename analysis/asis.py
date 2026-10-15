"""C01/C02 original-contamination AS-IS by defect type, from the local cleanup ZIP.

Aggregate counts only: no cell values, no evaluator manifest content. The repair
log's `before` values are the contaminated originals, so counting repaired cells
per rule measures the original defects without the corrupted ZIP itself.
"""
from __future__ import annotations

import csv
import io
import re
import zipfile
from collections import Counter, defaultdict

AXES = ("MISSING", "DUPLICATE", "FORMAT", "CODE_MIX", "VALUE_CONSISTENCY")
RULE_AXIS = {
    # OpenDART specification rules
    "amount_blank_literal": "MISSING", "duplicate_receipt": "DUPLICATE",
    "date_format": "FORMAT", "invisible_space": "FORMAT", "nfd_hangul": "FORMAT", "mojibake": "FORMAT",
    "stock_leading_zero": "CODE_MIX", "corp_code_swap": "CODE_MIX",
    "date_offset": "VALUE_CONSISTENCY", "amount_x1000": "VALUE_CONSISTENCY", "amount_sign_flip": "VALUE_CONSISTENCY",
    "prior_current_swap": "VALUE_CONSISTENCY", "year_shift": "VALUE_CONSISTENCY",
    "zip_path_swap": "VALUE_CONSISTENCY", "sha256_swap": "VALUE_CONSISTENCY",
    # Toss repair rules (cleanup package) and quarantine issue codes
    "NULL_REPRESENTATION": "MISSING", "MISSING_DATE_FROM_ALIGNED_FILES": "MISSING", "MISSING_REQUIRED_VALUE": "MISSING",
    "TRIM_OUTER_WHITESPACE": "FORMAT", "DATE_CANONICAL": "FORMAT", "TIME_CANONICAL_KST": "FORMAT",
    "MOJIBAKE_REVERSE": "FORMAT",
    "SYMBOL_FROM_FILENAME": "CODE_MIX", "SYMBOL_FROM_ISIN": "CODE_MIX", "ENUM_UPPERCASE": "CODE_MIX",
    "CURRENCY_FROM_MASTER": "VALUE_CONSISTENCY", "NET_BUY_FROM_BUY_MINUS_SELL": "VALUE_CONSISTENCY",
    "OHLC_INCONSISTENT": "VALUE_CONSISTENCY",
}
# Same concept, different column names across the two sources (checked against the headers).
SYNONYMS = [("stock_code", "symbol"), ("corp_name", "name"), ("corp_eng_name", "englishName"),
            ("rcept_dt", "date"), ("currency", "currency")]


def name_style(col):
    if col.startswith("_"):
        return "leading_underscore"
    if re.fullmatch(r"[a-z][a-z0-9]*(_[a-z0-9]+)*", col):
        return "snake_case" if "_" in col else "single_lower"
    if re.fullmatch(r"[a-z]+([A-Z][a-z0-9]*)+", col):
        return "camelCase"
    return "other"


def defect_axes(repairs, quarantine_issues):
    """repairs: rows with source_file/source_data_row_1based/column/rules (dataset key added).
    quarantine_issues: rows with source_file/source_data_row_1based/column_or_group/issue_code."""
    cells = defaultdict(set)
    rows = defaultdict(set)
    rule_counts = defaultdict(Counter)
    unmapped = Counter()
    for r in repairs:
        if r.get("resolution") == "NULL_NORMALIZED_STILL_UNRESOLVED":
            continue  # counted once through the quarantine issue entry
        for rule in r["rules"].split("|"):
            axis = RULE_AXIS.get(rule)
            if axis is None:
                unmapped[rule] += 1
                continue
            key = (r["dataset"], r["source_file"], r["source_data_row_1based"], r["column"])
            cells[(r["dataset"], axis)].add(key)
            rows[(r["dataset"], axis)].add(key[:3])
            rule_counts[(r["dataset"], axis)][rule] += 1
    for q in quarantine_issues:
        axis = RULE_AXIS[q["issue_code"]]
        key = ("Toss", q["source_file"], q["source_data_row_1based"], q["column_or_group"])
        cells[("Toss", axis)].add(key)
        rows[("Toss", axis)].add(key[:3])
        rule_counts[("Toss", axis)][q["issue_code"]] += 1
    out = {}
    for (dataset, axis), c in sorted(cells.items()):
        out.setdefault(dataset, {})[axis] = {"cells": len(c), "rows": len(rows[(dataset, axis)]),
                                             "rules": dict(sorted(rule_counts[(dataset, axis)].items()))}
    return out, dict(unmapped)


def naming_profile(headers):
    """headers: {dataset: {file_group: [columns]}} -> naming styles of distinct columns."""
    result = {}
    for dataset, groups in headers.items():
        cols = sorted({c for cs in groups.values() for c in cs})
        result[dataset] = {"distinct_columns": len(cols), "styles": dict(Counter(name_style(c) for c in cols))}
    all_cols = {d: {c for cs in g.values() for c in cs} for d, g in headers.items()}
    result["synonym_pairs"] = [f"OpenDART.{a} ≠ Toss.{b}" for a, b in SYNONYMS
                               if a != b and a in all_cols.get("OpenDART", ()) and b in all_cols.get("Toss", ())]
    return result


def original_profile(path):
    with zipfile.ZipFile(path) as z:
        root = next(n.removesuffix("00_README_KO.md") for n in z.namelist() if n.endswith("/00_README_KO.md"))

        def rows(name):
            return list(csv.DictReader(io.StringIO(z.read(root + name).decode("utf-8-sig"))))

        repairs = [r | {"dataset": d} for d in ("OpenDART", "Toss") for r in rows(f"04_audit/{d}_repair_log.csv")]
        issues = rows("03_quarantine/Toss/unresolved_issues.csv")
        axes, unmapped = defect_axes(repairs, issues)

        # OpenDART: restored Bronze keeps every row. Toss: the preserved copy keeps all 36,644 rows
        # (the Toss Bronze drops 741 quarantined rows, which would undercount normal blanks).
        csvs = [n for n in z.namelist() if n.endswith(".csv") and (
            n.startswith(root + "01_bronze/OpenDART/") or n.startswith(root + "02_preserved_rows/Toss/"))]
        headers, cells_total = defaultdict(dict), Counter()
        validation = {r["source_file"].removeprefix("dataset/"): r for r in rows("04_audit/file_validation.csv")}
        normal = Counter()
        for n in csvs:
            rel = n.removeprefix(root).split("/", 1)[1]
            dataset = rel.split("/", 1)[0]
            group = re.sub(r"\d{6}_|_\d{6}|_\d{4}(?=\.csv)", "", rel.rsplit("/", 1)[-1])
            text = z.read(n).decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            headers[dataset][group] = reader.fieldnames
            key = rel.split("/", 1)[1].removeprefix("dataset/")
            v = validation.get(key) or validation.get(rel.rsplit("/", 1)[-1])
            cells_total[dataset] += int(v["input_rows"]) * len(reader.fieldnames)
            # Normal (allowed) blanks that must not be counted as defects.
            if group in ("investor_trading.csv",):
                normal["Toss.investor_trading.cfd_blank"] += sum(1 for r in reader if r["cfd"] == "")
            elif group == "candles.csv":
                normal["Toss.candles.volume_zero_rows"] += sum(1 for r in reader if r["volume"] == "0")
            elif group == "stocks.csv":
                rs = list(reader)
                normal["Toss.stocks.delistDate_blank"] += sum(1 for r in rs if r["delistDate"] == "")
                normal["Toss.stocks.leverageFactor_blank"] += sum(1 for r in rs if r["leverageFactor"] == "")
            elif group == "financial.csv":
                normal["OpenDART.financials.thstrm_amount_blank"] += sum(1 for r in reader if r["thstrm_amount"] == "")
            elif group == "disclosure_documents.csv":
                normal["OpenDART.disclosure_documents.status_unavailable"] += sum(1 for r in reader if r["status"] == "unavailable")
    for dataset, a in axes.items():
        for axis in a.values():
            axis["cell_rate"] = round(axis["cells"] / cells_total[dataset], 6)
    return {"scope": "Original contaminated inputs measured through the cleanup repair log (before values) and Toss "
                     "quarantine issues. Aggregate only. Naming uses the preserved original headers.",
            "denominator_cells": dict(cells_total), "defect_axes": axes, "unmapped_rules": unmapped,
            "naming": naming_profile(headers), "normal_missing_not_defect": dict(sorted(normal.items()))}


def _amount_in_text(text, amount):
    """True if the KRW amount appears in the document in KRW, KRW thousand or KRW million units."""
    v = int(amount)
    forms = [f"{v:,}"] + [f"{v // u:,}" for u in (1000, 1_000_000) if v % u == 0]
    return any(re.search(r"(?<![\d,])" + re.escape(f) + r"(?![\d,])", text) for f in forms)


def review_documents(path, s, detail):
    """C05/M07: for SF04 REVIEW rows, check whether the Silver YTD and Q3M amounts appear in the
    local original disclosure (presence only; no document text is exported)."""
    rcept = s["s_fin_rpt"].set_index("fin_rpt_id").rcept_no
    out = []
    with zipfile.ZipFile(path) as z:
        root = next(n.removesuffix("00_README_KO.md") for n in z.namelist() if n.endswith("/00_README_KO.md"))
        names = set(z.namelist())
        for r in detail[detail.gap_cls_cd == "REVIEW"].itertuples():
            name = f"{root}01_bronze/OpenDART/dataset/documents/{rcept[r.fin_rpt_id]}.zip"
            row = {"fin_rpt_id": r.fin_rpt_id, "mtrc_cd": r.mtrc_cd, "document": name in names}
            if row["document"]:
                with zipfile.ZipFile(io.BytesIO(z.read(name))) as doc:
                    text = " ".join(doc.read(n).decode("utf-8", "ignore") for n in doc.namelist())
                row["ytd_in_document"] = _amount_in_text(text, r.ytd_amt)
                row["q3m_in_document"] = _amount_in_text(text, r.q3m_amt)
            out.append(row)
    with_doc = [r for r in out if r["document"]]
    return {"review_rows": len(out), "rows_with_document": len(with_doc),
            "silver_matches_document": sum(r["ytd_in_document"] and r["q3m_in_document"] for r in with_doc),
            "reports_without_document": sorted({r["fin_rpt_id"] for r in out if not r["document"]}),
            "interpretation": "When both amounts match the report's own document, the gap is between reports "
                              "(later restatement of an earlier period), not a Silver extraction error.",
            "rows": out}
