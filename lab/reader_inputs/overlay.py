"""Each scenario's own request in its system of record (G-36, `runs/2026-10-06-baseline/plan.md`).

The reader prompts present a scenario's request "as recorded in Northstar CRM" (or ERP). The
scenarios are alternative versions of one situation, so the shared exports can't hold them all:
each would see the others as live duplicates. `overlay` copies one corpus and makes its
system-of-record export consistent with the question:
- it drops any row with the scenario's request id, or a *pending* request for the same subject on
  the same day (discount: account, product and date; credit: ERP customer and date);
- it appends the scenario's request.

Use it only where the question says "as recorded in". A request "as submitted" must meet the
export as it is, because the conflict is the point there.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

EXPORTS = {
    "discount": ("discount_requests.csv", ("account_id", "product_sku", "request_date")),
    "credit": ("credit_requests.csv", ("erp_customer_id", "request_date")),
}


def overlay(src: Path, dst: Path, record: dict[str, str], kind: str) -> Path:
    """A copy of the corpus at `src`, at `dst`, whose export holds `record` and no alternative
    version of it. Returns `dst`."""
    name, subject = EXPORTS[kind]
    shutil.copytree(src, dst)
    path = dst / "structured" / name
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        rows = list(reader)

    def replaced(r: dict[str, str]) -> bool:
        if r["request_id"] == record["request_id"]:
            return True
        same = all(r.get(k) == record.get(k) for k in subject)
        return same and r.get("status") == "Pending Approval"

    kept = [r for r in rows if not replaced(r)]
    kept.append({h: record.get(h, "") for h in header})
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(kept)
    return dst
