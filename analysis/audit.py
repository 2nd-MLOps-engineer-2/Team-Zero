"""Read local cleanup audit ZIP; publish aggregate counts only, never cell values."""
import csv
import hashlib
import io
import zipfile
from collections import Counter


def aggregate_repairs(rows):
    resolutions, rules, files, columns = Counter(), Counter(), Counter(), Counter()
    cells, changed_rows = set(), set()
    for row in rows:
        key = (row["source_file"], row["source_data_row_1based"], row["column"])
        cells.add(key)
        changed_rows.add(key[:2])
        files[row["source_file"]] += 1
        columns[row["column"]] += 1
        resolutions[row["resolution"]] += 1
        rules.update(row["rules"].split("|"))
    return {"changed_cells": len(cells), "changed_rows": len(changed_rows),
            "by_resolution": dict(sorted(resolutions.items())), "by_rule_overlapping": dict(sorted(rules.items())),
            "by_file": dict(sorted(files.items())), "by_column": dict(sorted(columns.items()))}


def audit_cleanup(path, silver):
    with zipfile.ZipFile(path) as archive:
        roots = [n.removesuffix("00_README_KO.md") for n in archive.namelist() if n.endswith("/00_README_KO.md")]
        if len(roots) != 1:
            raise ValueError("Expected the inner Bronze_Cleanup_20261014 ZIP")
        root = roots[0]
        def rows(name):
            return list(csv.DictReader(io.StringIO(archive.read(root+name).decode("utf-8-sig"))))
        result = {team: aggregate_repairs(rows(f"04_audit/{team}_repair_log.csv")) for team in ("OpenDART", "Toss")}
        resolutions = result["Toss"]["by_resolution"]
        result["Toss"]["restored_cells"] = sum(n for key, n in resolutions.items() if key != "NULL_NORMALIZED_STILL_UNRESOLVED")
        quarantine = rows("03_quarantine/Toss/quarantined_rows.csv")
        result["quarantined_rows"] = len(quarantine)
        result["unresolved_issues"] = len(rows("03_quarantine/Toss/unresolved_issues.csv"))
        # Published specification totals; OHLC unresolved entries are groups, not exact cells.
        actual = {"opendart_repair_cells": result["OpenDART"]["changed_cells"],
                  "toss_changed_rows": result["Toss"]["changed_rows"],
                  "toss_restored_cells": result["Toss"]["restored_cells"],
                  "toss_null_normalized_unresolved": resolutions.get("NULL_NORMALIZED_STILL_UNRESOLVED", 0),
                  "quarantined_rows": result["quarantined_rows"], "unresolved_issue_entries": result["unresolved_issues"]}
        expected = dict(opendart_repair_cells=107846, toss_changed_rows=35074, toss_restored_cells=37303,
                        toss_null_normalized_unresolved=105, quarantined_rows=741, unresolved_issue_entries=747)
        result["spec_checks"] = {k: {"actual": v, "expected": expected[k], "pass": v == expected[k]} for k, v in actual.items()}
        # changed_rows in audit excludes quarantine rows with no repaired cell; their union is the spec population.
        audit_keys = {(r["source_file"], r["source_data_row_1based"]) for r in rows("04_audit/Toss_repair_log.csv")}
        quarantine_keys = {(r["source_file"], r["source_data_row_1based"]) for r in quarantine}
        union = len(audit_keys | quarantine_keys)
        result["spec_checks"]["toss_changed_rows"] = {"actual": union, "expected": 35074, "pass": union == 35074}
        result["toss_repair_or_quarantine_rows"] = union
        documents = {n.rsplit("/", 1)[-1].removesuffix(".zip") for n in archive.namelist() if "/documents/" in n and n.endswith(".zip")}
        rpt = silver["s_fin_rpt"]
        result["document_zip_count"] = len(documents)
        result["reports_with_document"] = int(rpt.rcept_no.isin(documents).sum())
        result["reports_without_document"] = int((~rpt.rcept_no.isin(documents)).sum())
        result["conflict_report_document_present"] = "20240313001650" in documents
        if "20240313001650" in documents:
            # Parse XML to confirm the document is readable; mapping decisions remain open.
            from xml.etree import ElementTree
            from zipfile import ZipFile
            with ZipFile(io.BytesIO(archive.read(root+"01_bronze/OpenDART/dataset/documents/20240313001650.zip"))) as doc:
                xmls = [n for n in doc.namelist() if n.lower().endswith(".xml")]
                parsed, errors = 0, []
                for name in xmls:
                    try:
                        ElementTree.fromstring(doc.read(name))
                        parsed += 1
                    except ElementTree.ParseError as exc:
                        # Preserve source bytes; malformed source is unresolved evidence.
                        errors.append({"file": name, "error": str(exc)})
                result["conflict_document_xml_files_parsed"] = parsed
                result["conflict_document_xml_errors"] = errors
        result["api_requery_rows"] = {name: int((silver[name].src_kind_cd == "API_REQUERY").sum()) for name in ("s_stock_daily_prc", "s_idx_daily_prc", "s_invstr_trd_daily")}
    with open(path, "rb") as stream:
        result["cleanup_zip_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
    result["scope"] = "Aggregate audit evidence; original corrupted ZIP absent. No raw values, evaluator manifest or document content exported. Not a full raw reprocessing."
    return result
