"""Experiment 6, step 4: the hybrid (kernel + SLA spec) on the SLA situations S36–S45.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-03-exp6-sla/run_hybrid.py [--replay]

The engine reads gold evidence (`dataset/evidence/`) and is given only the ticket id, and, for S45,
the moment to decide as of. It is scored against the answer key (`plan.md`):
- pass: outcome, scope, true severity, both breach findings, the credit, and every obligation (each
  of Northstar's duties with its role, holder and due time; each customer duty with met/not met)
  match;
- partial: the outcome matches, but something else doesn't;
- fail: the outcome doesn't match.

The gated outcome is scored too. Jev calls are recorded in `engine-calls.jsonl`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
import sla  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402

CALLS = HERE / "engine-calls.jsonl"
SCENARIOS = [f"S{n}" for n in range(36, 46)]


def compare(d: dict[str, Any], key: dict[str, Any]) -> dict[str, bool]:
    org = sorted([o["duty"], o["role"], o["holder"], o["due"]]
                 for o in d["obligations"] if o["party"] == "organization")  # fmt: skip
    cp = sorted([o["duty"], o["status"]] for o in d["obligations"] if o["party"] == "counterparty")
    want_org = sorted([o["duty"], o["role"], o["holder"], o["due"]]
                      for o in key["obligations"] if o["party"] == "northstar")  # fmt: skip
    want_cp = sorted([o["duty"], o["status"]] for o in key["obligations"]
                     if o["party"] == "customer")  # fmt: skip
    return {
        "scope": d["scope"] == key["scope"],
        "severity": d["severity"] == key["severity"]["true"],
        "response": d["breach"]["response"] == key["breach"]["response"],
        "restoration": d["breach"]["restoration"] == key["breach"]["restoration"],
        "credit": d["credit_usd"] == key["remedy"]["credit_usd"],
        "northstar_obligations": org == want_org,
        "customer_obligations": cp == want_cp,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if not CALLS.exists():
        shutil.copy(HERE.parent / "2026-10-03-exp5-credit/engine-calls.jsonl", CALLS)
    eng = Replay(CALLS, "jev-1.13.0") if a.replay else Recorder(TypeSafe("jev-1.13.0"), CALLS)
    truth = load_truth(LAB / "truth")
    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    lines = ["| Scenario | Expected | Hybrid (raw / gated) | Grade raw / gated | Mismatched | "
             "Uncertain |", "|---|---|---|---|---|---|"]  # fmt: skip
    out, tally = {}, {"raw": 0, "gated": 0}
    for sid in SCENARIOS:
        s = next(x for x in truth.scenarios if x.id == sid)
        d = sla.decide(eng, Evidence(LAB / "dataset/evidence"), str(s.ticket), s.decided_at, sid)
        k = key[sid]
        fields = compare(d, k)
        grades = []
        for o in (d["outcome"], d["gated_outcome"]):
            g = ("fail" if o != k["decision"]["outcome"] else
                 "pass" if all(fields.values()) else "partial")  # fmt: skip
            grades.append(g)
        tally["raw"] += grades[0] == "pass"
        tally["gated"] += grades[1] == "pass"
        miss = ", ".join(f for f, v in fields.items() if not v) or "—"
        lines.append(f"| {sid} | {k['decision']['outcome']} | {d['outcome']} / "
                     f"{d['gated_outcome']} | {grades[0]} / {grades[1]} | {miss} | "
                     f"{', '.join(d['uncertain']) or '—'} |")  # fmt: skip
        out[sid] = d
    lines += ["", f"Strict pass: raw **{tally['raw']}/10**, gated **{tally['gated']}/10**."]
    (HERE / "hybrid-decisions.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    (HERE / "hybrid-results.md").write_text(
        "# Hybrid on S36–S45 (SLA)\n\n" + "\n".join(lines) + "\n"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
