"""Load the systems-of-record exports into one read-only SQLite file (G-51's three-arm test,
`runs/2026-10-19-sor-reads-arms/plan.md`).

    uv run python lab/sor_reads/load_sqlite.py OUT.sqlite [--evidence dataset/evidence]

One table per `structured/<name>.csv`, columns in file order. A column is INTEGER or REAL only when
every non-empty value parses as one; everything else is TEXT, exactly as exported (timestamps keep
their offsets). An empty cell is NULL, as a database export renders NULL. The file is made
read-only (mode 0444). Prints the sha256 of a canonical dump, so the content can be checked
whatever SQLite's page layout.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sqlite3
from pathlib import Path

INT = re.compile(r"^-?\d+$")
REAL = re.compile(r"^-?(\d+\.\d*|\.\d+|\d+)([eE][-+]?\d+)?$")


def column_type(values: list[str]) -> str:
    vals = [v for v in values if v != ""]
    if vals and all(INT.match(v) for v in vals):
        return "INTEGER"
    if vals and all(REAL.match(v) for v in vals):
        return "REAL"
    return "TEXT"


def convert(v: str, kind: str) -> int | float | str | None:
    if v == "":
        return None
    return int(v) if kind == "INTEGER" else float(v) if kind == "REAL" else v


def canonical_sha(db: Path) -> str:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return hashlib.sha256("\n".join(con.iterdump()).encode()).hexdigest()
    finally:
        con.close()


def load(evidence: Path, out: Path) -> dict[str, int]:
    if out.exists():
        out.chmod(0o644)
        out.unlink()
    out.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(out)
    counts = {}
    for path in sorted((evidence / "structured").glob("*.csv")):
        with path.open(newline="") as f:
            rows = list(csv.reader(f))
        header, body = rows[0], rows[1:]
        kinds = [column_type([r[i] for r in body]) for i in range(len(header))]
        cols = ", ".join(f'"{h}" {k}' for h, k in zip(header, kinds, strict=True))
        con.execute(f'CREATE TABLE "{path.stem}" ({cols})')
        marks = ", ".join("?" for _ in header)
        values = [[convert(v, k) for v, k in zip(r, kinds, strict=True)] for r in body]
        con.executemany(f'INSERT INTO "{path.stem}" VALUES ({marks})', values)
        counts[path.stem] = len(body)
    con.commit()
    con.close()
    out.chmod(0o444)
    return counts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--evidence", type=Path, default=Path("dataset/evidence"))
    a = ap.parse_args()
    counts = load(a.evidence, a.out)
    print(
        f"{len(counts)} tables, {sum(counts.values())} rows · canonical sha256 "
        f"{canonical_sha(a.out)}"
    )


if __name__ == "__main__":
    main()
