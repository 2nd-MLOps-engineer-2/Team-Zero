"""Run: python -m analysis.run [--cleanup-zip /local/inner.zip]."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from .gold import VERSION, build_daily, build_financial, load_silver, read_csv, validate
from .rules import report_period_join, run_rules
from .standards import write_dictionary

ROOT = Path(__file__).resolve().parents[1]


def silver_checks(s, package):
    checks = []
    ddl = (package / "03_model/ddl/02_silver.sql").read_text(encoding="utf-8")
    for name, body in re.findall(r"CREATE TABLE `([^`]+)` \((.*?)\) ENGINE", ddl, re.S):
        pk = re.findall(r"`([^`]+)`", re.search(r"PRIMARY KEY \((.*?)\)", body).group(1))
        checks.append({"name": name + ".PK", "violations": int(s[name].duplicated(pk).sum())})
        for col, parent, parent_col in re.findall(r"FOREIGN KEY \(`([^`]+)`\) REFERENCES `([^`]+)` \(`([^`]+)`\)", body):
            values = s[name][col]
            checks.append({"name": name + "." + col + "->" + parent, "violations": int(((values != "") & ~values.isin(s[parent][parent_col])).sum())})
    if any(c["violations"] for c in checks):
        raise ValueError(f"Silver integrity failure: {checks}")
    return checks


def field_type(name, existing):
    if name in existing:
        return existing[name]
    if name.endswith("_amt"):
        return "DECIMAL(21,0)"
    if name.endswith("_qty"):
        return "DECIMAL(21,0)"
    if name.endswith("_rt"):
        return "DECIMAL(18,8)"
    if name.endswith("_dt"):
        return "DATE"
    if name.endswith("_yn"):
        return "CHAR(1)"
    return "VARCHAR(100)"


def chart(financial, daily, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    g = daily.query("stock_cd == '005930'").copy()
    x = pd.to_datetime(g.trd_dt)
    fig, axes = plt.subplots(2, 2, figsize=(15, 9), layout="constrained")
    for col, label in (("close_prc", "Stock"), ("idx_close_prc", "KOSPI")):
        y = pd.to_numeric(g[col])
        axes[0, 0].plot(x, y / y.iloc[0] * 100, label=label)
    axes[0, 0].set(title="005930: price and market (first observation = 100)", ylabel="Index (unadjusted prices)")
    f = financial.query("stock_cd == '005930'").sort_values("prd_end_dt")
    for col, label in (("rev_ytd_amt", "Revenue YTD"), ("op_cf_ytd_amt", "Operating CF YTD")):
        axes[0, 1].plot(pd.to_datetime(f.prd_end_dt), pd.to_numeric(f[col]) / 1e12, marker="o", label=label)
    axes[0, 1].set(title="Cumulative YTD amounts (NOT standalone quarter)", ylabel="KRW trillion")
    for col, label in (("frgn_flow_20d_rt", "Foreigner"), ("inst_flow_20d_rt", "Institution")):
        axes[1, 0].plot(x, pd.to_numeric(g[col], errors="coerce") * 100, label=label)
    axes[1, 0].set(title="20-observation net buying / traded volume", ylabel="Percent (share quantity ratio)")
    latest = daily[daily.trd_dt == daily.trd_dt.max()]
    valid = latest.query("co_move_stts_cd == 'OK'")
    axes[1, 1].scatter(pd.to_numeric(valid.rev_yoy_rt) * 100, pd.to_numeric(valid.event_excess_rt) * 100, s=28)
    for r in valid[valid.stock_cd.isin(["005930", "000660"])].itertuples():
        axes[1, 1].annotate(r.stock_cd, (float(r.rev_yoy_rt) * 100, float(r.event_excess_rt) * 100), fontsize=8,
                            xytext=(5, 0), textcoords="offset points")
    axes[1, 1].margins(0.12)
    axes[1, 1].axhline(0, color="gray", linewidth=0.7)
    axes[1, 1].axvline(0, color="gray", linewidth=0.7)
    axes[1, 1].set(title="20-stock sample; latest available reports", xlabel="Revenue YoY (%)", ylabel="Post-disclosure excess (percentage points)")
    for ax in axes.flat:
        ax.grid(alpha=0.2)
        if ax.get_legend_handles_labels()[0]:
            ax.legend(fontsize=8)
        ax.tick_params(axis="x", labelsize=8)
    fig.suptitle("TEAM ZERO | C analysis preview | data through " + daily.trd_dt.max() + " | " + VERSION)
    fig.savefig(out / "analysis-preview.png", dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", type=Path, default=ROOT / "data/03_C_integration_20261014")
    ap.add_argument("--output", type=Path, default=ROOT / "build/analysis")
    ap.add_argument("--cleanup-zip", type=Path)
    args = ap.parse_args()
    package, out = args.package.resolve(), args.output.resolve()
    if out == package or package in out.parents or out == ROOT or out in package.parents:
        ap.error("Output must not overwrite the immutable package or its ancestors")
    s = load_silver(package)
    integrity = silver_checks(s, package)
    baseline = read_csv(package / "04_output/gold/g_ai_stock_daily.csv")
    financial = build_financial(s)
    daily = build_daily(s, baseline, financial)
    checks = validate(s, baseline, financial, daily)
    print("Silver PK/FK and independent Gold source/PIT checks passed.", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    rules = run_rules(s, out)  # SS02 pass/fail; SF04/SF06 findings + detail CSVs
    terms = read_csv(package / "02_standard_dictionary/std_term.csv")
    existing = dict(zip(terms.col_nm, terms.data_type_nm))
    schemas, output_hashes = {}, {}
    for name, frame, pk in (("g_fin_rpt_analysis", financial, ["fin_rpt_id"]), ("g_stock_daily_analysis", daily, ["stock_cd", "trd_dt"])):
        path = out / (name + ".csv")
        frame.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n")
        output_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        schemas[name] = {"primary_key": pk, "rows": len(frame), "columns": [{"name": c, "type": field_type(c, existing), "nullable": c not in pk, "actual_blank_count": int((frame[c] == "").sum())} for c in frame.columns]}
    write_dictionary(schemas, terms, package, out)  # C03 Gold term/word proposal (imported dictionary untouched)

    samples = {"financial": financial.head(3).to_dict("records"), "daily": daily.query("stock_cd == '005930'").tail(3).to_dict("records")}
    for n, obj in (("schema.json", schemas), ("samples.json", samples)):
        (out / n).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    chart(financial, daily, out)
    profile = [{"table": name, "column": col, "rows": len(frame), "blank_cells": int((frame[col] == "").sum()),
                "distinct_nonblank": int(frame.loc[frame[col] != "", col].nunique())}
               for name, frame in s.items() for col in frame.columns]
    import pandas as pd
    pd.DataFrame(profile).to_csv(out / "silver-profile.csv", index=False, encoding="utf-8-sig", lineterminator="\n")
    summary = {"calc_ver": VERSION, "scope": "C local calculation verified; B DB/Delta/SQL and A browser acceptance pending",
               "silver_integrity": integrity, "gold_checks": checks, "rows": {"financial": len(financial), "daily": len(daily)},
               "revenue_growth_status": financial.rev_yoy_rt_stts_cd.value_counts().to_dict(),
               "co_move_counts": daily.co_move_cd.value_counts().to_dict(), "joint_improve_status": daily.joint_improve_stts_cd.value_counts().to_dict(),
               "source_issues": s["s_dq_issue"].resolve_stts_cd.value_counts().to_dict(), "output_sha256": output_hashes,
               "input_sha256": {p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [*sorted((package / "04_output/silver").glob("*.csv")), package / "04_output/gold/g_ai_stock_daily.csv", package / "02_standard_dictionary/std_term.csv"]}}
    summary["silver_rules"] = rules
    summary["c08_report_period_join"] = report_period_join(financial, read_csv(package / "04_output/gold/g_fin_rpt_mkt_smry.csv"))
    if not summary["c08_report_period_join"]["pass"]:
        raise ValueError(f"C08 join failure: {summary['c08_report_period_join']}")
    if args.cleanup_zip:
        from .audit import audit_cleanup
        summary["cleanup_aggregate"] = audit_cleanup(args.cleanup_zip, s)
        from .asis import original_profile
        summary["original_asis"] = original_profile(args.cleanup_zip)  # C01/C02 by defect type
        from .asis import review_documents
        from .rules import period_continuity
        summary["sf04_review_documents"] = review_documents(args.cleanup_zip, s, period_continuity(s)[1])  # C05/M07
    (out / "validation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "version": VERSION, "rows": summary["rows"], "checks": "PASS"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
