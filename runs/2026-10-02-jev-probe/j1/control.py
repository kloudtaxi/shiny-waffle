"""J1 control: the hybrid pipeline with a perfect judge, before any Jev call.

    uv run python runs/2026-10-02-jev-probe/j1/control.py

The judge answers each soft question from the visible text, by a rule written for this corpus.
If the pipeline then reproduces the oracle on all 18 scenarios, any J1 miss is Jev's judgment,
not the pipeline's code.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(HERE))
import hybrid  # noqa: E402

ACME_MFG = ("Acme Manufacturing", "Acme Mfg")


class PerfectJudge:
    model = "perfect-judge"

    def ask(self, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
        ((name, q),) = questions.items()
        doc = str(state.get("document", ""))
        if name == "basis":
            contract = "contract" in state["request"]["justification"].lower()
            choice = "contract_terms" if contract else "standard_pricing"
            return {"answers": {name: {"choice": choice, "confidence": 1.0,
                                       "probabilities": {choice: 1.0}}}}  # fmt: skip
        if name == "party":
            mine = state["request_customer"]["account_name"] == "Acme Manufacturing"
            names_acme = any(n in doc for n in ACME_MFG)
            choice = "same_legal_entity" if mine and names_acme else "different_entity"
            return {"answers": {name: {"choice": choice, "confidence": 1.0,
                                       "probabilities": {choice: 1.0}}}}  # fmt: skip
        sku = state["product"].split("(")[-1].rstrip(")")
        return {"answers": {name: {"noul": 1.0 if sku in doc else 0.0}}}


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    assert spec and spec.loader
    heldout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heldout)
    truth = hybrid.load_truth(LAB / "truth")
    exp = hybrid.scorer.expected()
    passes = 0
    for sid in hybrid.SCENARIOS:
        d = hybrid.decide(PerfectJudge(), truth, sid, heldout.record(sid))
        g = hybrid.scorer.score(sid, d, exp[sid])
        passes += g["grade"] == "pass"
        flag = "" if g["grade"] == "pass" else f"   <-- {g['note']}"
        print(f"{sid}: {g['grade']:7s} {d['outcome']:27s} key {exp[sid]['outcome']}{flag}")
    print(f"perfect judge: {passes}/{len(hybrid.SCENARIOS)}")


if __name__ == "__main__":
    main()
