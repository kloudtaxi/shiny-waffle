"""Addendum: Haiku 4.5 on the OWM slice with the record format enforced (`addendum-schema.md`).

    uv run python runs/2026-10-08-cost-per-decision/run_schema.py ask
    uv run python runs/2026-10-08-cost-per-decision/run_schema.py score

Identical to G-23's H-slice except that each call carries `claude -p --json-schema` (the record
format, validated by the API). Answers land in `answers/h-slice-schema/` as the CLI's JSON result.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
ARM = "h-slice-schema"
OUT = HERE / "answers" / ARM
GUARD_USD = 0.08


def load(name: str, path: Path) -> ModuleType:
    s = importlib.util.spec_from_file_location(name, path)
    assert s and s.loader
    mod = importlib.util.module_from_spec(s)
    sys.modules[name] = mod
    s.loader.exec_module(mod)
    return mod


rc = load("run_cost", HERE / "run_cost.py")
bl = rc.bl

OUTCOMES = ["APPROVE", "APPROVE_WITH_AUTHORIZATION", "REJECT_OR_ESCALATE", "REVIEW_REQUIRED",
            "REQUEST_EVIDENCE"]  # fmt: skip


def names() -> list[str]:
    with (LAB / "dataset/evidence/structured/employees.csv").open() as f:
        return sorted(r["full_name"] for r in csv.DictReader(f))


def schema(kind: str) -> dict[str, Any]:
    nullable = {"type": ["string", "number", "null"]}
    cond = {"type": "array", "items": {"type": "object", "properties": {
        "what": {"type": "string"}, "who": {"type": ["string", "null"]},
        "blocking": {"type": "boolean"}}, "required": ["what", "blocking"],
        "additionalProperties": False}}  # fmt: skip
    common = {"evidence": {"type": "array", "items": {"type": "string"}},
              "missing_evidence": {"type": "array", "items": {"type": "string"}},
              "conditions": cond, "request": {"type": "object"}}  # fmt: skip
    if kind == "discount":
        authority = {"type": "object", "properties": {
            "policy": {"type": ["string", "null"]}, "requestor_limit": nullable,
            "requestor_authorized": {"type": "boolean"},
            "required_role": {"type": ["string", "null"]},
            "approver": {"type": "string", "enum": names()}},
            "required": ["policy", "requestor_limit", "requestor_authorized", "required_role",
                         "approver"], "additionalProperties": False}  # fmt: skip
        elig = {"type": "object", "properties": {
            "status": {"enum": ["eligible", "exceeded", "not_covered", "unknown", "standard"]},
            "maximum_discount": nullable, "basis": {"type": ["string", "null"]}},
            "required": ["status"]}  # fmt: skip
        props = {"outcome": {"enum": OUTCOMES}, "commercial_eligibility": elig,
                 "authority": authority} | common  # fmt: skip
        req = ["outcome", "commercial_eligibility", "authority", "conditions"]
    else:
        approver = {"type": "object", "properties": {
            "name": {"type": "string", "enum": names()}, "role": {"type": "string"},
            "kind": {"enum": ["approval", "concurrence"]}},
            "required": ["name", "role", "kind"], "additionalProperties": False}  # fmt: skip
        authority = {"type": "object", "properties": {
            "policy": {"type": ["string", "null"]}, "requestor_limit": nullable,
            "requestor_authorized": {"type": ["boolean", "null"]},
            "required_role": {"type": ["string", "null"]},
            "approvers": {"type": "array", "items": approver}},
            "required": ["policy", "requestor_authorized", "approvers"],
            "additionalProperties": False}  # fmt: skip
        elig = {"type": "object", "properties": {
            "status": {"enum": ["eligible", "exceeded", "ineligible", "unknown"]},
            "maximum_limit": nullable, "basis": {"type": ["string", "null"]},
            "late_invoices": {"type": "array"}}, "required": ["status"]}  # fmt: skip
        props = {"outcome": {"enum": OUTCOMES}, "eligibility": elig,
                 "authority": authority} | common  # fmt: skip
        req = ["outcome", "eligibility", "authority", "conditions"]
    return {"type": "object", "properties": props, "required": req}


def ask(text: str, system_prompt: str, sch: dict[str, Any]) -> str:
    blind = Path(tempfile.mkdtemp(prefix="northstar-blind-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    cmd = ["claude", "-p", text, "--model", rc.MODELS["h"], "--output-format", "json",
           "--json-schema", json.dumps(sch), "--system-prompt", system_prompt,
           "--strict-mcp-config", "--mcp-config", '{"mcpServers": {}}', "--tools", "",
           "--setting-sources", "project", "--no-session-persistence",
           "--max-turns", "4"]  # fmt: skip
    try:
        proc = subprocess.run(cmd, cwd=blind, env=dict(os.environ), capture_output=True,
                              text=True, timeout=900)  # fmt: skip
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    return proc.stdout


def result(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = json.loads(path.read_text())
    return out


def run_ask(workers: int, reps: int = 3) -> None:
    from northstar.model import load_truth

    truth = load_truth(LAB / "truth")
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ns-g23s-") as tmp:
        jobs = [(OUT / f"{sid}-r{r}.json", rc.slice_prompt(truth, sid, Path(tmp)),
                 bl.system(sid), schema(bl.kind(sid)))
                for sid in bl.SCENARIOS for r in range(1, reps + 1)]  # fmt: skip
    jobs = [j for j in jobs if not j[0].exists()]

    def go(job: tuple[Path, str, str, dict[str, Any]]) -> float:
        path, text, sysp, sch = job
        path.write_text(ask(text, sysp, sch))
        usd = float(result(path).get("total_cost_usd") or 0)
        print(f"{ARM} {path.name}: ${usd:.3f}", flush=True)
        return usd

    with cf.ThreadPoolExecutor(workers) as pool:
        first = list(pool.map(go, jobs[:workers]))
        avg = sum(first) / len(first) if first else 0.0
        if avg > GUARD_USD:
            sys.exit(f"cost guard: first {len(first)} averaged ${avg:.3f}")
        list(pool.map(go, jobs[workers:]))


def score() -> None:
    """Wrap each validated record in a fenced block (the harness's input shape), then score with
    G-23's `score_arm` (strict) and `rescore.py`'s rules (exploratory)."""
    wrapped = HERE / "answers" / f"{ARM}-wrapped"
    wrapped.mkdir(parents=True, exist_ok=True)
    errors = []
    for p in sorted(OUT.glob("S*-r*.json")):
        r = result(p)
        rec = r.get("structured_output")
        if rec is None:
            errors.append(f"{p.stem}: {str(r.get('result'))[:120]}")
        text = f"```json\n{json.dumps(rec)}\n```" if rec is not None else ""
        event = {"type": "result", "result": text, "total_cost_usd": r.get("total_cost_usd"),
                 "duration_ms": r.get("duration_ms"), "usage": r.get("usage")}  # fmt: skip
        (wrapped / f"{p.stem}.jsonl").write_text(json.dumps(event) + "\n")
    strict = rc.score_arm(wrapped)
    rs = load("rescore", HERE / "rescore.py")
    key = rs.yaml.safe_load((LAB / "dataset/answer-key/expected-results.yaml").read_text())
    key = {x["scenario"]: x for x in key}
    exp = bl.exp4r.scorer.expected()
    kinds: Counter[str] = Counter()
    wrong = []
    for p in sorted(wrapped.glob("S*-r*.jsonl")):
        sid, rep = p.stem.split("-")
        text = str(bl.exp4r.result(p).get("result") or "")
        if bl.kind(sid) == "discount":
            got = bl.exp4r.scorer.decision(text)
            s0 = str(bl.exp4r.classify(got, exp[sid]))
            g = rs.strip_names(got or {})
            a, e = g.get("authority") or {}, exp[sid]
            if (str(g.get("outcome")).upper() == e["outcome"] == "APPROVE"
                    and a.get("requestor_authorized") is True is e["authorized"]
                    and not a.get("approver")):  # fmt: skip
                g["authority"] = dict(a, approver=e["approver"])
            s1 = str(bl.exp4r.classify(g, e))
        else:
            got = bl.exp5r.scorer.decision(text)
            _, x = bl.exp5r.grade(got, key[sid])
            s0 = str(bl.creader.unsafe_type(got, x, key[sid]["decision"]["outcome"]))
            _, y = bl.exp5r.grade(rs.strip_names(got or {}), key[sid])
            s1 = str(bl.creader.unsafe_type(rs.strip_names(got or {}), y,
                                            key[sid]["decision"]["outcome"]))  # fmt: skip
        if s0.startswith("unsafe") and not s1.startswith("unsafe"):
            kinds["incomplete_or_misformatted"] += 1
        if s1.startswith("unsafe"):
            kinds["wrong_decisions"] += 1
            wrong.append(f"{sid} {rep}: {s1}")
    out = {k: v for k, v in strict.items() if k != "rows"} | dict(kinds) | {
        "wrong": wrong, "no_record": errors}  # fmt: skip
    (HERE / "results-schema.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["ask", "score"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    run_ask(a.workers) if a.step == "ask" else score()


if __name__ == "__main__":
    main()
