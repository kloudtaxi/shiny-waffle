"""Experiment 5, step 3: the hybrid (frozen kernel + credit spec) on the credit scenarios S26–S35.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-03-exp5-credit/run_hybrid.py [--replay]

Each scenario's request is the ERP credit-request row, built from truth like `heldout.record` is
for discounts (the input, not the answer). The engine reads gold evidence: the scenario's corpus
in `dataset/`. Scored against the answer key (`plan.md`):
- pass: outcome, eligibility status and requestor-authorized match, and for an approval the
  approvers (name and kind, in order) match;
- partial: the outcome matches, but something else doesn't;
- fail: the outcome doesn't match.
The gated outcome (uncertain judgments routed to a person) is scored too. Jev calls are recorded
in `engine-calls.jsonl`, seeded from experiment 4's recording.
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
import credit  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402
from northstar.oracle import resolve_credit_request  # noqa: E402

MODEL = "jev-1.13.0"
CALLS = HERE / "engine-calls.jsonl"
SCENARIOS = [f"S{n}" for n in range(26, 36)]
VARIANTS = LAB / "dataset/evidence-variants"
CORPUS = {"base": LAB / "dataset/evidence",
          "missing-guarantee-evidence": VARIANTS / "missing-guarantee-evidence"}  # fmt: skip


def record(truth: Any, sid: str) -> dict[str, str]:
    s = next(x for x in truth.scenarios if x.id == sid)
    r = resolve_credit_request(truth, s)
    domain = truth.organization.email_domain
    return {"request_id": r.id, "erp_customer_id": truth.customer(r.customer).source_ids["erp"],
            "current_limit_usd": str(r.current_limit_usd),
            "requested_limit_usd": str(r.requested_limit_usd),
            "requested_by": truth.employee(r.requestor).email(domain),
            "request_date": r.request_date.isoformat(), "justification": r.justification,
            "status": r.status}  # fmt: skip


def grade(d: dict[str, Any], exp: dict[str, Any], outcome: str) -> str:
    if outcome != exp["decision"]["outcome"]:
        return "fail"
    authorized = exp["authority"]["requestor"]["authorized"]
    same = (d["eligibility"]["status"] == exp["eligibility"]["status"]
            and d["authority"].get("requestor_authorized") is authorized)  # fmt: skip
    if outcome in credit.APPROVALS:
        want = [(a["name"], a["kind"]) for a in exp["authority"]["approvers"]]
        same &= [(a["name"], a["kind"]) for a in d["approvers"]] == want
    return "pass" if same else "partial"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if not CALLS.exists():
        shutil.copy(LAB / "runs/2026-10-03-adversarial/engine-calls.jsonl", CALLS)
    eng = Replay(CALLS, MODEL) if a.replay else Recorder(TypeSafe(MODEL), CALLS)
    truth = load_truth(LAB / "truth")
    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    out, lines = {}, ["| Scenario | Expected | Hybrid (raw) | Gated | Grade raw / gated | Basis | "
                      "Approvers | Uncertain |", "|---|---|---|---|---|---|---|---|"]  # fmt: skip
    tally = {"raw": 0, "gated": 0}
    for sid in SCENARIOS:
        s = next(x for x in truth.scenarios if x.id == sid)
        d = credit.decide(eng, Evidence(CORPUS[s.corpus]), s.as_of, record(truth, sid), sid)
        exp = key[sid]
        raw, gated = grade(d, exp, d["outcome"]), grade(d, exp, d["gated_outcome"])
        tally["raw"] += raw == "pass"
        tally["gated"] += gated == "pass"
        appr = ", ".join(f"{x['name']} ({x['kind']})" for x in d["approvers"]) or "none"
        lines.append(f"| {sid} | {exp['decision']['outcome']} | {d['outcome']} | "
                     f"{d['gated_outcome']} | {raw} / {gated} | {d['eligibility'].get('basis')} "
                     f"(key {exp['eligibility']['basis']}) | {appr} | "
                     f"{', '.join(d['uncertain']) or '—'} |")  # fmt: skip
        out[sid] = d
    lines += ["", f"Strict pass: raw **{tally['raw']}/10**, gated **{tally['gated']}/10**."]
    (HERE / "hybrid-decisions.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    (HERE / "hybrid-results.md").write_text(
        "# Hybrid on S26–S35 (credit)\n\n" + "\n".join(lines) + "\n"
    )
    print("\n".join(lines))


if __name__ == "__main__":
    main()
