"""G-23: cost per decision by model tier and context (`plan.md`).

    uv run python runs/2026-10-08-cost-per-decision/run_cost.py ask [--arms o-slice h-full h-slice]
    uv run python runs/2026-10-08-cost-per-decision/run_cost.py owm      # the OWM path, by replay
    uv run python runs/2026-10-08-cost-per-decision/run_cost.py score

The reader re-baseline's harness (`runs/2026-10-06-baseline/run_baseline.py`) is reused for the
prompts, the system prompt (procedure) and the scoring; only the model and the context change.
O-full is the re-baseline's own answers (Opus 5.5, whole corpus). Every call runs blind: a fresh
temporary directory outside the repo, no tools, no MCP, no session persistence.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = HERE / "answers"
BASELINE = LAB / "runs/2026-10-06-baseline"
MODELS = {"o": "claude-opus-5-5", "h": "claude-haiku-4-5-20251001"}
GUARD = {"o-slice": 0.20, "h-full": 0.15, "h-slice": 0.06}
JEV_USD_PER_CALL = 0.62 / 29012  # I2's measured rate (runs/2026-10-02-jev-probe/i2/notes.md)
# an answer citing an email message (not the employee table's email column)
EMAIL_MSG = re.compile(r"email_sarah|\b(?:sarah's|her|an|the|this|that) email\b|email (?:to|from) ",
                       re.I)  # fmt: skip


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


bl = load("run_baseline", BASELINE / "run_baseline.py")
sl = load("served_slice", HERE / "served_slice.py")
from northstar.model import load_truth  # noqa: E402


def question_and_record(truth: Any, sid: str) -> tuple[str, dict[str, Any]]:
    s = next(x for x in truth.scenarios if x.id == sid)
    if bl.kind(sid) == "discount":
        rec = bl.rh4.record(bl.heldout, sid)
        return f"{s.question} The request, as recorded in Northstar CRM: {json.dumps(rec)}", rec
    rec = dict(bl.x5.record(truth, sid))
    if s.submitted:
        rec |= {k: str(v) for k, v in s.submitted.items()}
        return f"{s.question} The request, as submitted: {json.dumps(rec)}", rec
    return f"{s.question} The request, as recorded in Northstar ERP: {json.dumps(rec)}", rec


def slice_prompt(truth: Any, sid: str, tmp: Path) -> str:
    s = next(x for x in truth.scenarios if x.id == sid)
    src = bl.CORPORA[str(s.corpus)]
    q, rec = question_and_record(truth, sid)
    k = bl.kind(sid)
    if k == "credit":
        base_rec = bl.x5.record(truth, sid)
        root = src if sid in bl.SUBMITTED else bl.ov.overlay(src, tmp / sid, base_rec, "credit")
    else:
        root = bl.ov.overlay(src, tmp / sid, rec, "discount")
    return f"{q}\n\n{sl.served_slice(k, str(s.corpus), root, rec)}"


def ask(model: str, text: str, system_prompt: str) -> str:
    blind = Path(tempfile.mkdtemp(prefix="northstar-blind-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    cmd = ["claude", "-p", text, "--model", model, "--output-format", "stream-json", "--verbose",
           "--system-prompt", system_prompt, "--strict-mcp-config", "--mcp-config",
           '{"mcpServers": {}}', "--tools", "", "--setting-sources", "project",
           "--no-session-persistence", "--max-turns", "3"]  # fmt: skip
    try:
        proc = subprocess.run(cmd, cwd=blind, env=dict(os.environ), capture_output=True,
                              text=True, timeout=900)  # fmt: skip
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    return proc.stdout


def jobs(arm: str, truth: Any, tmp: Path, reps: int) -> list[tuple[Path, str, str]]:
    out = []
    for sid in bl.SCENARIOS:
        text = (slice_prompt(truth, sid, tmp) if arm.endswith("slice")
                else bl.prompt(truth, sid, tmp / f"full-{sid}"))  # fmt: skip
        out += [(OUT / arm / f"{sid}-r{r}.jsonl", text, bl.system(sid)) for r in range(1, reps + 1)]
    return out


def run_ask(arms: list[str], reps: int, workers: int) -> None:
    truth = load_truth(LAB / "truth")
    for arm in arms:
        (OUT / arm).mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="ns-g23-") as tmp:
            todo = [j for j in jobs(arm, truth, Path(tmp), reps) if not j[0].exists()]
        model = MODELS[arm[0]]

        def go(job: tuple[Path, str, str], model: str = model, arm: str = arm) -> float:
            path, text, sys_prompt = job
            path.write_text(ask(model, text, sys_prompt))
            usd = float(bl.exp4r.result(path).get("total_cost_usd") or 0)
            print(f"{arm} {path.name}: ${usd:.3f}", flush=True)
            return usd

        with cf.ThreadPoolExecutor(workers) as pool:
            first = list(pool.map(go, todo[:workers]))
            avg = sum(first) / len(first) if first else 0.0
            if avg > GUARD[arm]:
                sys.exit(f"cost guard ({arm}): first {len(first)} calls averaged ${avg:.3f}")
            list(pool.map(go, todo[workers:]))


def score_arm(folder: Path) -> dict[str, Any]:
    key = {r["scenario"]: r for r in yaml.safe_load(
        (LAB / "dataset/answer-key/expected-results.yaml").read_text())}  # fmt: skip
    exp_disc = bl.exp4r.scorer.expected()
    rows, costs, ms, tokens = [], [], [], []
    for path in sorted(folder.glob("S*-r*.jsonl")):
        sid, rep = path.stem.split("-")
        res = bl.exp4r.result(path)
        costs.append(float(res.get("total_cost_usd") or 0))
        ms.append(int(res.get("duration_ms") or 0))
        u = res.get("usage") or {}
        fields = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
        tokens.append(sum(int(u.get(k) or 0) for k in fields))
        text = str(res.get("result") or "")
        if bl.kind(sid) == "discount":
            got = bl.exp4r.scorer.decision(text)
            safety = str(bl.exp4r.classify(got, exp_disc[sid]))
        else:
            got = bl.exp5r.scorer.decision(text)
            _, s = bl.exp5r.grade(got, key[sid])
            safety = str(bl.creader.unsafe_type(got, s, key[sid]["decision"]["outcome"]))
        rows.append({"scenario": sid, "rep": rep, "outcome": (got or {}).get("outcome"),
                     "safety": safety, "mentions_email": bool(EMAIL_MSG.search(text))})  # fmt: skip
    c = Counter(r["safety"].split(":")[0] for r in rows)
    return {"n": len(rows), "safety": dict(c), "unsafe": [f"{r['scenario']} {r['rep']}: "
            f"{r['safety']}" for r in rows if r["safety"].startswith("unsafe")],
            "usd_total": round(sum(costs), 2), "usd_per_answer": round(sum(costs) / len(rows), 4)
            if rows else None, "median_ms": statistics.median(ms) if ms else None,
            "median_input_tokens": statistics.median(tokens) if tokens else None,
            "mentions_email": sum(r["mentions_email"] for r in rows), "rows": rows}  # fmt: skip


def run_owm() -> None:
    """The OWM path: the governed procedure decides each scenario from the register, by replay,
    with Jev calls counted."""
    admit = load("admit", LAB / "lab/spec_admission/admit.py")
    import governed

    class Counting:
        def __init__(self, eng: Any) -> None:
            self.eng, self.calls = eng, 0

        def ask(self, state: Any, questions: Any) -> Any:
            self.calls += len(questions)
            return self.eng.ask(state, questions)

    gate = admit.Gate(admit.Layered(HERE / "jev-calls.jsonl", live=False, cap=0))
    entries = governed.procedures()
    out = {}
    with tempfile.TemporaryDirectory(prefix="ns-g23-owm-") as tmp:
        roots = gate.clean_roots(Path(tmp) / "clean")
        for kind in ("discount", "credit"):
            for sid in gate.scenarios(kind):
                c = gate.corpus(kind, sid)
                eng = Counting(gate.eng)
                inp = gate.inputs(kind, sid)
                g = admit.ra.plain(governed.decide(kind, eng, admit.Evidence(roots[c]), inp,
                                                   inp.get("as_of") or gate.scen[sid].as_of,
                                                   admit.ra.REG[c], entries))  # fmt: skip
                out[sid] = {"kind": kind, "class": gate.classify(kind, sid, g),
                            "jev_questions": eng.calls}  # fmt: skip
    c = Counter(v["class"] for v in out.values())
    qs = [v["jev_questions"] for v in out.values()]
    summary = {"decisions": len(out), "classes": dict(c), "mean_jev_questions": statistics.mean(qs),
               "usd_per_decision_upper": round(max(qs) * JEV_USD_PER_CALL, 6),
               "per_scenario": out}  # fmt: skip
    (HERE / "owm-path.json").write_text(json.dumps(summary, indent=1) + "\n")
    print({k: v for k, v in summary.items() if k != "per_scenario"})


def run_score() -> None:
    arms = {"o-full": BASELINE / "answers"} | {a: OUT / a for a in GUARD if (OUT / a).exists()}
    res = {a: score_arm(p) for a, p in arms.items()}
    (HERE / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    lines = ["| Arm | n | held / routed / unsafe | $ per answer | median latency (s) | "
             "median input tokens | mentions an email |",
             "|---|---|---|---|---|---|---|"]  # fmt: skip
    for a, r in res.items():
        s = r["safety"]
        lines.append(f"| {a} | {r['n']} | {s.get('held', 0)} / {s.get('routed', 0)} / "
                     f"{s.get('unsafe', 0)} | {r['usd_per_answer']} | "
                     f"{(r['median_ms'] or 0) / 1000:.1f} | {r['median_input_tokens']} | "
                     f"{r['mentions_email']} |")  # fmt: skip
    for a, r in res.items():
        if r["unsafe"]:
            lines.append(f"- {a} unsafe: " + "; ".join(r["unsafe"]))
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["ask", "owm", "score"])
    ap.add_argument("--arms", nargs="+", default=list(GUARD))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.step == "ask":
        run_ask(a.arms, a.reps, a.workers)
    elif a.step == "owm":
        run_owm()
    else:
        run_score()


if __name__ == "__main__":
    main()
