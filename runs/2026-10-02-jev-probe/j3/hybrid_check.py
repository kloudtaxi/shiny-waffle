"""J3-H: the hybrid engine's input check. It diffs the submitted record against the CRM row in code.

    python3 runs/2026-10-02-jev-probe/j3/hybrid_check.py

Two structured records are compared field by field (`../plan.md`: a code job, not a Jev one). A
conflict means the engine decides on the system of record and flags the fields. The decision itself
is the oracle's (`dataset/answer-key`).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
FIELDS = ["requested_discount_pct", "request_date", "status", "product_sku", "account_id",
          "requested_by", "justification"]  # fmt: skip


def main() -> None:
    with (LAB / "dataset/evidence/structured/discount_requests.csv").open() as f:
        crm = {r["request_id"]: r for r in csv.DictReader(f)}
    out = {}
    for line in (HERE / "questions.tsv").read_text().splitlines()[1:]:
        sid, _kb, q = line.split("\t")
        sub = json.loads(q.split("The request, as submitted: ", 1)[1])
        row = crm[sub["request_id"]]
        conflicts = [k for k in FIELDS if str(sub[k]) != str(row[k])]
        out[sid] = {"conflicts": conflicts, "decided_on": "system of record",
                    "flagged": bool(conflicts)}  # fmt: skip
        print(sid, conflicts or "no conflict")
    (HERE / "hybrid_check.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
