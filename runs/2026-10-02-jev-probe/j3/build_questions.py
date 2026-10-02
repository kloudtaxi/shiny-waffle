"""J3: the questions for S22–S25, each followed by the request *as submitted*.

    uv run python runs/2026-10-02-jev-probe/j3/build_questions.py

The record starts as DR-9001's CRM row, in the same shape `heldout.record` gives the held-out runs.
The scenario's `submitted` fields are then applied from `truth/`, so the reader sees exactly the
conflict the oracle checks. The amounts are recomputed when the discount changes. The suffix is
"The request, as submitted:", not "as recorded in Northstar CRM": the CRM is the system of record.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
BASE_KB = "01a0ea56-61e7-79e3-99d1-e82b5d6af79a"  # scale base KB, as it stands (curated)
SCENARIOS = ["S22", "S23", "S24", "S25"]


def submitted_record(sid: str) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    assert spec and spec.loader
    heldout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heldout)
    from northstar.model import load_truth

    scenario = next(s for s in load_truth(LAB / "truth").scenarios if s.id == sid)
    rec: dict[str, Any] = heldout.record(sid)  # the system of record: DR-9001's CRM row
    for field, value in (scenario.submitted or {}).items():
        if field == "requested_discount":
            listed = int(rec["list_value_usd"])
            rec["requested_discount_pct"] = f"{value * 100:.1f}"
            rec["discount_value_usd"] = str(round(listed * value))
            rec["net_value_usd"] = str(listed - round(listed * value))
        elif field == "request_date":
            rec["request_date"] = value.isoformat()
        elif field == "status":
            rec["status"] = value
        else:
            raise ValueError(f"{sid}: no record mapping for submitted field {field}")
    return rec


def main() -> None:
    from northstar.model import load_truth

    truth = {s.id: s for s in load_truth(LAB / "truth").scenarios}
    rows = ["id\tkb\tquestion"]
    for sid in SCENARIOS:
        record = json.dumps(submitted_record(sid), ensure_ascii=False)
        rows.append(f"{sid}\t{BASE_KB}\t{truth[sid].question} The request, as submitted: {record}")
    (HERE / "questions.tsv").write_text("\n".join(rows) + "\n")
    print("\n".join(r[:230] for r in rows))


if __name__ == "__main__":
    main()
