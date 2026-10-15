"""공통 유틸: 입력 위치, CSV 읽기/쓰기(문자열 보존), 해시."""
from __future__ import annotations
import csv, hashlib, json, os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent          # 패키지 루트(03_C_integration_...)


def input_dirs(a_dir: str | None = None, b_dir: str | None = None):
    """A·B 인계 폴더. 인자 > 환경변수(TZ_A_DIR/TZ_B_DIR) > 패키지 옆 기본 위치 순."""
    a = Path(a_dir or os.environ.get("TZ_A_DIR") or ROOT.parent / "02_C_handoff_20261014")
    b = Path(b_dir or os.environ.get("TZ_B_DIR") or ROOT.parent / "Team_B_Silver_Handoff")
    for p, n in ((a, "A"), (b, "B")):
        if not p.exists():
            raise SystemExit(f"{n} 인계 폴더가 없습니다: {p}  (--a-dir/--b-dir 또는 TZ_A_DIR/TZ_B_DIR 지정)")
    return a, b


A_FILES = {  # 논리명: A 폴더 기준 상대경로
    "company_master": "support/company_master.csv",
    "disclosures": "support/disclosures_with_documents.csv",
    "disclosure_documents": "support/disclosure_documents.csv",
    "financial_items": "support/financial_items_all.csv",
    "financial_summary": "opendart_financial_summary_20_companies.csv",
    "metric_definitions": "support/metric_definitions.csv",
    "review_issues": "support/review_issues.csv",
}
B_FILES = {
    "security_master": "silver/security_master.csv",
    "stock_daily_price": "silver/stock_daily_price.csv",
    "market_index_daily": "silver/market_index_daily.csv",
    "investor_trading_daily": "silver/investor_trading_daily.csv",
    "foreign_holding_daily": "silver/foreign_holding_daily.csv",
    "cfd_daily": "silver/cfd_daily.csv",
    "price_investor_availability": "silver/price_investor_availability.csv",
    "investor_source_daily": "silver/investor_source_daily.csv",
    "data_quality_issues": "silver/data_quality_issues.csv",
    "bronze_unresolved_issues": "silver/bronze_unresolved_issues.csv",
    "pending_recovery_review": "silver/pending_recovery_review.csv",
}


def read_csv(path: Path) -> pd.DataFrame:
    """모든 값을 문자열로 읽는다. 빈 셀은 '' 로 유지(NULL 판정은 호출부에서)."""
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False, na_filter=False)


def write_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_inputs(a: Path, b: Path):
    A = {k: read_csv(a / v) for k, v in A_FILES.items()}
    B = {k: read_csv(b / v) for k, v in B_FILES.items()}
    return A, B


def input_manifest(a: Path, b: Path) -> pd.DataFrame:
    rows = []
    for team, base, files in (("A", a, A_FILES), ("B", b, B_FILES)):
        for k, rel in files.items():
            p = base / rel
            rows.append(dict(src_team_cd=team, logical_nm=k, rel_path=rel, size_bytes=p.stat().st_size,
                             sha256=sha256_file(p)))
    df = pd.DataFrame(rows)
    return df


def input_version(manifest: pd.DataFrame) -> str:
    h = hashlib.sha256("".join(manifest.sha256).encode()).hexdigest()
    return "inputs-sha256:" + h[:16]


def dump_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
