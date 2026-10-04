"""Specs as data, phase 2: run and score the agent-authored credit spec (`specs/credit_agent.yaml`).

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-04-specs-as-data/run_agent_spec.py --errors-only  # the fix round
    uv run python runs/2026-10-04-specs-as-data/run_agent_spec.py                 # scores

- `--errors-only` prints only what the runner rejected (load errors, or exceptions per scenario),
  never outcomes or scores. That is all the author sees in its one fix round (`plan.md`).
- The scored run grades S26–S35 against the answer key like experiment 5's hybrid:
  - strict: outcome, eligibility status, requestor-authorized, and the approvers' names and kinds;
  - partial: the outcome matches, but something else doesn't;
  - fail: the outcome doesn't match.

  Approvers are compared in any order (the order is reported too).

Jev calls are recorded in this folder's `engine-calls.jsonl`, seeded from experiment 6's.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
import flow  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402
from kernel import Evidence  # noqa: E402

from northstar.model import load_truth  # noqa: E402

CALLS = HERE / "engine-calls.jsonl"
SPEC = LAB / "lab/owm_kernel/specs/credit_agent.yaml"


def exp5() -> Any:
    spec = importlib.util.spec_from_file_location(
        "exp5_run_hybrid", LAB / "runs/2026-10-03-exp5-credit/run_hybrid.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def grade(d: dict[str, Any], exp: dict[str, Any]) -> tuple[str, bool]:
    if d.get("outcome") != exp["decision"]["outcome"]:
        return "fail", False
    elig = (d.get("eligibility") or {}).get("status") == exp["eligibility"]["status"]
    auth = (d.get("authority") or {}).get("requestor_authorized") is exp["authority"]["requestor"][
        "authorized"
    ]
    want = [(a["name"], a["kind"]) for a in exp["authority"]["approvers"]]
    have = [(a.get("name"), a.get("kind")) for a in d.get("approvers") or []]
    appr = sorted(have) == sorted(want)
    return ("strict" if elig and auth and appr else "partial"), have == want


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--errors-only", action="store_true")
    ap.add_argument("--replay", action="store_true")
    a = ap.parse_args()
    if not CALLS.exists():
        shutil.copy(LAB / "runs/2026-10-03-exp6-sla/engine-calls.jsonl", CALLS)
    try:
        spec = flow.load(SPEC)
    except Exception as e:  # noqa: BLE001 — every load failure goes back to the author
        print(f"LOAD ERROR: {type(e).__name__}: {e}")
        sys.exit(1)
    eng = Replay(CALLS, "jev-1.13.0") if a.replay else Recorder(TypeSafe("jev-1.13.0"), CALLS)
    truth = load_truth(LAB / "truth")
    x5 = exp5()
    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    errors, rows = [], []
    for sid in x5.SCENARIOS:
        s = next(x for x in truth.scenarios if x.id == sid)
        try:
            inputs = {"sid": sid, "record": x5.record(truth, sid), "as_of": s.as_of}
            d = flow.run(spec, eng, Evidence(x5.CORPUS[s.corpus]), inputs)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{sid}: {type(e).__name__}: {e}")
            continue
        rows.append((sid, d))
    if a.errors_only:
        print("\n".join(errors) if errors else "no errors: the spec ran on every scenario")
        sys.exit(1 if errors else 0)
    lines = ["| Scenario | Expected | Agent spec (raw / gated) | Grade raw / gated | Approvers |",
             "|---|---|---|---|---|"]  # fmt: skip
    tally = {"raw": 0, "gated": 0}
    out = {}
    for sid, d in rows:
        k = key[sid]
        g_raw, _ = grade(d, k)
        g_gated, _ = grade({**d, "outcome": d.get("gated_outcome")}, k)
        tally["raw"] += g_raw == "strict"
        tally["gated"] += g_gated == "strict"
        appr = ", ".join(f"{x.get('name')} ({x.get('kind')})" for x in d.get("approvers") or [])
        lines.append(f"| {sid} | {k['decision']['outcome']} | {d.get('outcome')} / "
                     f"{d.get('gated_outcome')} | {g_raw} / {g_gated} | "
                     f"{appr or 'none'} |")  # fmt: skip
        out[sid] = d
    lines += [f"| {e.split(':')[0]} | | error | fail / fail | |" for e in errors]
    lines += ["", f"Strict: raw **{tally['raw']}/10**, gated **{tally['gated']}/10**."]
    (HERE / "agent-decisions.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    (HERE / "agent-results.md").write_text("# Agent-authored credit spec on S26–S35\n\n"
                                           + "\n".join(lines) + "\n")  # fmt: skip
    print("\n".join(lines))


if __name__ == "__main__":
    main()
