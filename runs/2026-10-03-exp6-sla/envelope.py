"""Experiment 6, test (e): do every decision type's answer-key records fit one decision envelope?

    uv run python runs/2026-10-03-exp6-sla/envelope.py

The envelope (fixed in `plan.md`):
- required: `decision_id`, `type`, `as_of`, `subject`, `decision.outcome` from the vocabulary
  declared for the type, `reason[]`, `evidence[]`;
- optional: `request`, `authority`, `obligations[]`.

Type-specific bodies may sit alongside, but never replace, the envelope. Records of the non-decision
scenario kinds (fact selection, provenance, identity) are not decisions and are skipped.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

LAB = Path(__file__).resolve().parents[2]
APPROVAL = {"APPROVE", "APPROVE_WITH_AUTHORIZATION", "REJECT_OR_ESCALATE", "REVIEW_REQUIRED",
            "REQUEST_EVIDENCE"}  # fmt: skip
VOCABULARY: dict[str, set[str]] = {
    "discount_approval": APPROVAL,
    "credit_limit_increase": APPROVAL,
    "sla_response": {
        "BREACH_CREDIT_OWED",
        "BREACH_NO_CREDIT",
        "NO_BREACH",
        "OUT_OF_SCOPE",
        "CANNOT_DECIDE",
    },  # declared with the SLA decision (step 3)
}
DECISION_TYPES = {"discount_approval", "credit_limit_increase", "sla_response"}


def problems(r: dict[str, Any]) -> list[str]:
    out = [f"missing {k}" for k in ("decision_id", "type", "as_of", "subject", "reason", "evidence")
           if k not in r]  # fmt: skip
    outcome = (r.get("decision") or {}).get("outcome")
    vocab = VOCABULARY.get(r.get("type", ""))
    if vocab is None:
        out.append(f"no outcome vocabulary declared for type {r.get('type')!r}")
    elif outcome not in vocab:
        out.append(f"outcome {outcome!r} not in the {r['type']} vocabulary")
    for k in ("reason", "evidence", "obligations"):
        if k in r and not isinstance(r[k], list):
            out.append(f"{k} is not a list")
    return out


def main() -> None:
    rows = yaml.safe_load((LAB / "dataset/answer-key/expected-results.yaml").read_text())
    decisions = [r for r in rows if r.get("type") in DECISION_TYPES]
    bad = {r["scenario"]: p for r in decisions if (p := problems(r))}
    print(f"{len(decisions)} decision records: {dict(Counter(r['type'] for r in decisions))}")
    for sid, p in bad.items():
        print(f"  {sid}: {'; '.join(p)}")
    print("all fit the envelope" if not bad else f"{len(bad)} do not fit")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
