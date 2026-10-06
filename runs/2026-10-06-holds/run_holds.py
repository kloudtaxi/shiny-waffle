"""G-35: holds in the decision record (`plan.md`). The plain reader, with the original procedure
(control) or the copy that adds `conditions` (treatment).

    uv run python runs/2026-10-06-holds/run_holds.py [--reps 3] [--workers 6] [--score]

Questions: J3's own text for S22–S25 (the request "as submitted"), experiment 4's builder for the
other discount scenarios, set C's reader prompt for credit. Then every document and CSV of the
scenario's corpus, as in set F's `pf` arm. The cost guard stops the run if the first `--workers`
calls average more than $0.45.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = HERE / "answers"
GUARD_USD = 0.45
HOLD_PRONE = ["S04", "S22", "S27", "S31", "S35"]
CONTROLS = ["S25", "S01", "S26"]
VARIANTS = LAB / "dataset/evidence-variants"
CORPORA = {"base": LAB / "dataset/evidence",
           "missing-contract-evidence": VARIANTS / "missing-contract-evidence",
           "missing-guarantee-evidence": VARIANTS / "missing-guarantee-evidence"}  # fmt: skip


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


exp4r = load("exp4_reader", LAB / "runs/2026-10-03-adversarial/run_reader.py")
exp5r = load("exp5_reader", LAB / "runs/2026-10-03-exp5-credit/run_reader.py")
creader = load("set_c_reader", LAB / "runs/2026-10-03-exp5-credit/run_set_c_reader.py")
rh4 = load("exp4_run_hybrid", LAB / "runs/2026-10-03-adversarial/run_hybrid.py")
heldout = rh4.load("heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py")
from northstar.model import load_truth  # noqa: E402

J3 = {r["id"]: r["question"] for r in csv.DictReader(
    (LAB / "runs/2026-10-02-jev-probe/j3/questions.tsv").open(), delimiter="\t")}  # fmt: skip


def kind(sid: str) -> str:
    return "credit" if 26 <= int(sid[1:]) <= 35 else "discount"


def prompt(truth: Any, sid: str) -> str:
    s = next(x for x in truth.scenarios if x.id == sid)
    root = CORPORA[str(s.corpus)]
    if kind(sid) == "credit":
        return str(creader.prompt(truth, sid, root))
    q = J3.get(sid) or (f"{s.question} The request, as recorded in Northstar CRM: "
                        f"{json.dumps(rh4.record(heldout, sid))}")  # fmt: skip
    return f"{q}\n\n{exp5r.evidence(root)}"


PROCS = {
    "control": LAB / "owm/procedures",
    "treatment": HERE / "procedures",
    "treatment-v2": HERE / "procedures-v2",
}  # v2: the plan's addendum, a check


def system(sid: str, arm: str) -> str:
    name = "credit-limit.md" if kind(sid) == "credit" else "discount-approval.md"
    return f"{exp4r.SYSTEM_PROMPT}\n\n{(PROCS[arm] / name).read_text()}"


def block(text: str) -> dict[str, Any] | None:
    got = exp4r.scorer.decision(text)
    return got if isinstance(got, dict) else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--score", action="store_true", help="score what exists; ask nothing")
    ap.add_argument("--arms", default="control,treatment", help="comma-separated arms")
    a = ap.parse_args()
    truth = load_truth(LAB / "truth")
    jobs = []
    arms = a.arms.split(",")
    for arm in arms:
        (OUT / arm).mkdir(parents=True, exist_ok=True)
        for sid in HOLD_PRONE + CONTROLS:
            text, sys_prompt = prompt(truth, sid), system(sid, arm)
            jobs += [(OUT / arm / f"{sid}-r{r}.jsonl", text, sys_prompt)
                     for r in range(1, a.reps + 1)]  # fmt: skip
    jobs = [j for j in jobs if not j[0].exists() and not a.score]

    def go(job: tuple[Path, str, str]) -> float:
        path, text, sys_prompt = job
        path.write_text(exp4r.ask(text, sys_prompt))
        usd = float(exp4r.result(path).get("total_cost_usd") or 0)
        print(f"{path.parent.name}/{path.name}: ${usd:.3f}", flush=True)
        return usd

    with cf.ThreadPoolExecutor(a.workers) as pool:
        first = list(pool.map(go, jobs[: a.workers]))
        avg = sum(first) / len(first) if first else 0.0
        if avg > GUARD_USD:
            sys.exit(f"cost guard: the first {len(first)} calls averaged ${avg:.2f}; stopped")
        list(pool.map(go, jobs[a.workers :]))

    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    exp_disc = exp4r.scorer.expected()
    rows, cost = [], Counter()
    for arm in [x for x in PROCS if (OUT / x).is_dir()]:
        for path in sorted((OUT / arm).glob("*.jsonl")):
            sid, rep = path.stem.split("-")
            res = exp4r.result(path)
            cost[arm] += float(res.get("total_cost_usd") or 0)
            text = str(res.get("result") or "")
            if kind(sid) == "discount":
                got = exp4r.scorer.decision(text)
                safety = exp4r.classify(got, exp_disc[sid]) if sid in exp_disc else None
                if safety is None:  # S22–S25 aren't in experiment 4's set: compare the outcome
                    out = str((got or {}).get("outcome") or "").upper()
                    safety = "held" if out == key[sid]["decision"]["outcome"] else f"block {out}"
            else:
                got = exp5r.scorer.decision(text)
                _, s = exp5r.grade(got, key[sid])
                safety = creader.unsafe_type(got, s, key[sid]["decision"]["outcome"])
            conds = [c for c in ((got or {}).get("conditions") or []) if isinstance(c, dict)]
            rel = str(path.relative_to(LAB))
            rows.append({"arm": arm, "scenario": sid, "rep": rep, "answer": rel,
                         "outcome": (got or {}).get("outcome"), "safety": safety,
                         "blocking": sum(bool(c.get("blocking")) for c in conds),
                         "conditions": conds})  # fmt: skip
    (HERE / "results.json").write_text(json.dumps(rows, indent=1) + "\n")
    print("cost: " + ", ".join(f"{k} ${v:.2f}" for k, v in cost.items()))
    for r in rows:
        print(
            r["arm"], r["scenario"], r["rep"], r["outcome"], r["safety"], "blocking", r["blocking"]
        )


if __name__ == "__main__":
    main()
