"""Exploratory, NOT pre-registered (`notes.md`): gate C's idle reliance, measured on the outcome and
the approvers only, without the eligibility maximum that the pre-registered key includes.

    uv run python runs/2026-10-06-spec-admission/explore_outcome_idle.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
s = importlib.util.spec_from_file_location("admit", LAB / "lab/spec_admission/admit.py")
assert s and s.loader
admit = importlib.util.module_from_spec(s)
sys.modules["admit"] = admit
s.loader.exec_module(admit)


class OutcomeGate(admit.Gate):  # type: ignore[misc,name-defined]
    def kkey(self, kind: str, d: dict[str, Any]) -> Any:
        if d.get("gated_outcome") == "ERROR":
            return ("ERROR",)
        return (d.get("gated_outcome"), tuple(admit.setc.approvers(d)))


def main() -> None:
    gate = OutcomeGate(admit.Layered(HERE / "jev-calls.jsonl", live=False, cap=0))
    out = {}
    for name in ("credit_v2.yaml", "credit_agent.yaml", "credit_agent_v2.yaml"):
        r = gate.run(LAB / "lab/owm_kernel/specs" / name, "credit")
        out[name] = {"relied": r["C"]["relied"], "idle": r["C"]["idle"],
                     "unknown": len(r["C"]["unknown"])}  # fmt: skip
        print(f"{name}: {len(r['C']['idle'])} outcome-idle of {r['C']['relied']} relied; "
              f"{len(r['C']['unknown'])} unknown")  # fmt: skip
    (HERE / "explore-outcome-idle.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
