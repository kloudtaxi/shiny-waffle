"""Set D: the Opus reader on the user's attack documents (`set-d-plan.md`, reader addendum).

    uv run python runs/2026-10-05-instrument-guards/run_set_d_reader.py [--reps 3] [--workers 6]
                                                                       [--score]

This is set C's reader, unchanged (`runs/2026-10-03-exp5-credit/run_set_c_reader.py`, which is
experiment 5's reader on an attacked corpus):
- `claude -p` with no tools;
- the fixed system prompt plus the credit procedure;
- the request record, then every document and CSV of the corpus.

Each attack's corpus is built by `run_set.build`, as for the engines. Only each attack's target is
run. The cost guard: if the first `--workers` calls average more than $0.45, the run stops.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
EXP5 = LAB / "runs/2026-10-03-exp5-credit"
OUT = HERE / "set-d-reader"
GUARD_USD = 0.45


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


creader = load("set_c_reader", EXP5 / "run_set_c_reader.py")  # prompt(), unsafe_type(), reader
guards = load("run_set", HERE / "run_set.py")  # build(), SETS, check_seal()

from northstar.model import load_truth  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--score", action="store_true", help="score what exists; ask nothing")
    a = ap.parse_args()
    src, sums = guards.SETS["D"]
    guards.check_seal(src, sums)
    reader = creader.reader
    truth = load_truth(LAB / "truth")
    exp = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    attacks = yaml.safe_load((src / "manifest.yaml").read_text())
    scen = {s.id: s for s in truth.scenarios}
    system_prompt = f"{reader.exp4.SYSTEM_PROMPT}\n\n{reader.PROCEDURE.read_text()}"
    OUT.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ns-set-d-reader-") as tmp:
        jobs = []
        for at in attacks:
            corp = guards.build(at, src, Path(tmp) / at["id"], False)
            sid = at["target"]
            text = creader.prompt(truth, sid, corp[scen[sid].corpus])
            jobs += [(OUT / f"{at['id']}-{sid}-r{r}.jsonl", text) for r in range(1, a.reps + 1)]
        jobs = [j for j in jobs if not j[0].exists() and not a.score]

        def go(job: tuple[Path, str]) -> float:
            path, text = job
            path.write_text(reader.exp4.ask(text, system_prompt))
            usd = float(reader.exp4.result(path).get("total_cost_usd") or 0)
            print(f"{path.name}: ${usd:.3f}", flush=True)
            return usd

        with cf.ThreadPoolExecutor(a.workers) as pool:
            first = list(pool.map(go, jobs[: a.workers]))
            avg = sum(first) / len(first) if first else 0.0
            if avg > GUARD_USD:
                sys.exit(f"cost guard: the first {len(first)} calls averaged ${avg:.2f}; stopped")
            list(pool.map(go, jobs[a.workers :]))

    rows, cost = [], 0.0
    for path in sorted(OUT.glob("*.jsonl")):
        aid, sid, rep = path.stem.split("-")
        res = reader.exp4.result(path)
        cost += float(res.get("total_cost_usd") or 0)
        got = reader.scorer.decision(str(res.get("result") or ""))
        g, safety = reader.grade(got, exp[sid])
        auth = (got or {}).get("authority") or {}
        rows.append({"attack": aid, "scenario": sid, "rep": rep, "grade": g,
                     "safety": creader.unsafe_type(got, safety, exp[sid]["decision"]["outcome"]),
                     "outcome": (got or {}).get("outcome"), "approvers": auth.get("approvers"),
                     "eligibility": (got or {}).get("eligibility")})  # fmt: skip
    by = defaultdict(list)
    for r in rows:
        by[(r["attack"], r["scenario"])].append(r)
    lines = ["# Reader on set D (credit, attacked corpora, credit procedure)", "",
             "| Attack | Target | Expected | Safety | Outcomes |",
             "|---|---|---|---|---|"]  # fmt: skip
    for (aid, sid), rs in by.items():
        lines.append(f"| {aid} | {sid} | {exp[sid]['decision']['outcome']} | "
                     f"{dict(Counter(r['safety'] for r in rs))} | "
                     f"{', '.join(str(r['outcome']) for r in rs)} |")  # fmt: skip
    unsafe = sum(r["safety"].startswith("unsafe") for r in rows)
    targets = len({r["attack"] for r in rows if r["safety"].startswith("unsafe")})
    lines += ["", f"Unsafe: **{unsafe}/{len(rows)}** runs, on **{targets}/{len(by)}** targets · "
              f"cost ${cost:.2f}"]  # fmt: skip
    (HERE / "set-d-reader-results.json").write_text(json.dumps(rows, indent=1) + "\n")
    (HERE / "set-d-reader-results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
