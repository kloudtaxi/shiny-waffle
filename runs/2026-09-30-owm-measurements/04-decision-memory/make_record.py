"""Item 4, phase 1: turn agent A's decision into the two memory carriers the arms compare.

    python3 runs/2026-09-30-owm-measurements/04-decision-memory/make_record.py

Agent A is a real run: T2 r1 S01 in `../01-02-procedure/` (blind reader B1n, procedure v2 served by
the OWM stand-in), which decided DR-9001 correctly. Its decision JSON is carried unchanged into:

- `decisions.json`: a **typed decision record** (arm c), served by the stand-in's
  `find_decisions` / `get_decision` tools, the shape PRD-3 §5.6 / §17 describe;
- `decision_log_DEC-2026-0001.md`: the **same record as a document** (arm b), uploaded into
  Utopia's base KB like any other organizational evidence.

Both carry identical content. Two fields are lab fixtures, identical in both carriers and
disclosed in `notes.md`: the decision id, and Michael Torres's approval on 2026-09-24 (the corpus
has DR-9001 as "Pending Approval"; the approval event is what makes "who approved it" answerable).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
AGENT_A = HERE.parent / "01-02-procedure/T2/r1/B1n/S01.md"
V2 = LAB / "owm/procedures/discount-approval-v2.md"


def agent_a_decision() -> dict[str, object]:
    text = AGENT_A.read_text()
    blocks = re.findall(r"```json\n(.*?)```", text, re.S)
    decision: dict[str, object] = json.loads(blocks[-1])
    return decision


def main() -> None:
    d = agent_a_decision()
    auth = d["authority"]
    elig = d["commercial_eligibility"]
    req = d["request"]
    assert isinstance(auth, dict) and isinstance(elig, dict) and isinstance(req, dict)
    record = {
        "decision_id": "DEC-2026-0001",
        "decision_kind": "discount_approval",
        "status": "approved",
        "decided_at": "2026-09-23",
        "decided_by": {
            "kind": "agent",
            "procedure": "discount_approval",
            "procedure_version": hashlib.sha256(V2.read_bytes()).hexdigest()[:12],
        },
        "request": req,
        "outcome": d["outcome"],
        "commercial_eligibility": elig,
        "authority": auth,
        "approval": {
            "approved_by": "Michael Torres",
            "role": "VP Sales",
            "approved_at": "2026-09-24",
            "result": "approved",
        },
        "evidence": d["evidence"],
    }
    (HERE / "decisions.json").write_text(json.dumps([record], indent=1, ensure_ascii=False) + "\n")

    ev = "\n".join(f"- {e}" for e in d["evidence"])  # type: ignore[union-attr]
    version = record["decided_by"]["procedure_version"]  # type: ignore[index]
    doc = f"""---
doc_id: DEC-2026-0001
title: Decision record — discount request DR-9001
owner: Revenue Operations
created: '2026-09-24'
classification: Internal
---

# Decision record DEC-2026-0001 — discount request DR-9001

**Status:** approved · **Decided:** 2026-09-23 · **Decision kind:** discount approval
**Decided by:** governance agent, discount-approval procedure version {version}

## Request

- Request: {req["id"]}
- Customer: {req["customer"]}
- Product: {req["product"]}
- Requested discount: {req["requested_discount"]}
- Request date: {req["date"]}
- Requestor: {req["requestor"]}
- Basis claimed: {req["basis"]}

## Outcome

**{d["outcome"]}**

## Commercial eligibility

- Status: {elig["status"]}
- Maximum discount: {elig["maximum_discount"]}
- Basis: {elig["basis"]}

## Authority

- Policy in force: {auth["policy"]}
- Requestor's limit: {auth["requestor_limit"]}
- Requestor authorized: {"yes" if auth["requestor_authorized"] else "no"}
- Required role: {auth["required_role"]}
- Approver: {auth["approver"]}

## Approval

Approved by Michael Torres (VP Sales) on 2026-09-24.

## Evidence relied on

{ev}
"""
    (HERE / "decision_log_DEC-2026-0001.md").write_text(doc)
    print(json.dumps(record, indent=1, ensure_ascii=False)[:900])


if __name__ == "__main__":
    main()
