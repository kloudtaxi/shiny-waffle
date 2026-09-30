"""Item 4: the questions agent B is asked (M1–M3), identical in every arm.

uv run python runs/2026-09-30-owm-measurements/04-decision-memory/build_questions.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
BASE_KB = "01a0ea56-61e7-79e3-99d1-e82b5d6af79a"

M1 = (
    "Has Sarah Chen's discount request DR-9001 (15% on the NS-500 for Acme Manufacturing, "
    "requested on 2026-09-23) been decided? If it has: what was the outcome, who approved it, "
    "under which pricing policy, and on what eligibility basis? End your answer with a JSON block: "
    '{"decided": true or false, "outcome": "...", "approved_by": "...", "policy": "...", '
    '"eligibility_basis": "..."}, using null for anything you cannot establish.'
)
M2 = (
    "Today is 2027-02-01. Was the decision on Sarah Chen's discount request DR-9001 valid under "
    "the rules in force when it was made? End your answer with a JSON block: "
    '{"decision_found": true or false, "valid_when_made": true, false or null, '
    '"policy_then": "...", "approved_by": "...", "approver_role_then": "..."}, using null for '
    "anything you cannot establish."
)


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    assert spec and spec.loader
    heldout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heldout)
    from northstar.model import load_truth

    s21 = next(x for x in load_truth(LAB / "truth").scenarios if x.id == "S21")
    m3 = (
        f"Today is 2027-02-01. {s21.question} The request, as recorded in Northstar CRM: "
        f"{json.dumps(heldout.record('S21'), ensure_ascii=False)}"
    )
    rows = [
        "id\tkb\tquestion",
        f"M1\t{BASE_KB}\t{M1}",
        f"M2\t{BASE_KB}\t{M2}",
        f"M3\t{BASE_KB}\t{m3}",
    ]
    (HERE / "questions.tsv").write_text("\n".join(rows) + "\n")
    print("\n".join(r[:160] for r in rows))


if __name__ == "__main__":
    main()
