"""Read-only handoff integrity check; Python standard library only."""
import csv
import hashlib
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized_files(package):
    result = {}
    for path in package.rglob("*"):
        if path.is_file():
            key = unicodedata.normalize("NFC", path.relative_to(package).as_posix())
            if key in result:
                raise ValueError(f"Unicode filename collision: {key}")
            result[key] = path
    return result


def check(package, manifest):
    files = normalized_files(package)
    expected = {item["path"]: item for item in manifest["files"]}
    errors = []
    for name in sorted(files.keys() - expected.keys()):
        errors.append(f"Unexpected file: {name}")
    for name, item in expected.items():
        if name not in files:
            errors.append(f"Missing file: {name}")
            continue
        path = files[name]
        # ponytail: largest snapshot file is 45 MB; stream hashes if files grow.
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.stat().st_size != item["bytes"] or digest != item["sha256"]:
            errors.append(f"Changed bytes: {name}")
        if "rows" in item:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                columns = next(reader, [])
                rows = sum(1 for _ in reader)
            if columns != item["columns"] or rows != item["rows"]:
                errors.append(f"CSV header/row mismatch: {name}")
    if len(expected) != manifest["file_count"]:
        errors.append("Manifest file_count mismatch")
    if sum(item["bytes"] for item in expected.values()) != manifest["total_bytes"]:
        errors.append("Manifest total_bytes mismatch")
    return errors


def main():
    manifest = json.loads((ROOT / "data/handoff_manifest.json").read_text(encoding="utf-8"))
    package = ROOT / "data" / manifest["package"]
    errors = check(package, manifest)
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    csv_count = sum("rows" in item for item in manifest["files"])
    print(f"PASS: {manifest['file_count']} files, hashes, sizes and {csv_count} CSV headers/row counts")
    files = normalized_files(package)
    missing = []
    for line in (package / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        name = unicodedata.normalize("NFC", name.removeprefix("./"))
        if name not in files:
            missing.append(name)
        elif hashlib.sha256(files[name].read_bytes()).hexdigest() != digest:
            print(f"FAIL: original SHA256SUMS mismatch: {name}")
            return 1
    for name in missing:
        print(f"NOT INCLUDED in supplied package (original manifest reference): {name}")
    print("Bronze input CSVs, disclosure ZIPs, MySQL dump and Delta tables are not bundled.")
    print("This is file verification, not a rerun of the 203 MySQL/Pandas checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
