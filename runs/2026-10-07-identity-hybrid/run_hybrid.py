"""G-18: hybrid identity routing. Jev decides what it is sure of, Opus judges I2's routed band,
and a person sees what is still open. Design and predictions in `plan.md`.

    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py probe     # cost probe, off-band
    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py ask [--workers 8]
    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py repeat    # 100 inputs asked again
    uv run python runs/2026-10-07-identity-hybrid/run_hybrid.py score

Inputs are I2's: the labelled pairs (`../2026-10-02-jev-probe/i2/local/pairs-*.jsonl`, gitignored)
and Jev's committed answers (`judged-*.csv.gz`). The band is I2's pre-registered operating point
(guard, merge at `same` >= 0.9, keep at `different` >= 0.5); everything it routes goes to Opus.
Opus sees exactly what Jev saw (name, type, also-known-as, facts) and Jev's question, word for
word. Each distinct input is asked once (the two KBs share most pairs).

Blindness: every call runs in a fresh temporary directory outside the repo, with no tools, no
MCP servers and a fixed system prompt. Answers land in `answers.jsonl` (one line per input hash),
so a crashed run resumes; `probe.jsonl` holds the off-band cost probe.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
I2 = LAB / "runs/2026-10-02-jev-probe/i2"
KBS = ["base", "missing-contract"]
MODEL = "claude-opus-5-5"
ANSWERS = HERE / "answers.jsonl"
PROBE = HERE / "probe.jsonl"
REPEAT = HERE / "answers-repeat.jsonl"
REPEAT_N, REPEAT_SEED = 100, 20261007
GUARD_USD = 0.03  # stop if the first calls average more than this per pair (probe: ~$0.0093)
TAU, KEEP, KEEP_LOW = 0.9, 0.5, 0.3
KINDS = [(r"so-\d+", "order"), (r"dr-\d+", "request"), (r"crm-\d+", "customer"),
         (r"c-\d+", "customer"), (r"emp-\d+", "employee"), (r"prod-\d+", "product")]  # fmt: skip

# Fixed before the run. Jev's question and criteria (J4's Q_SAME), word for word.
SYSTEM_PROMPT = "You judge whether two records describe the same real-world thing."
QUESTION = "Do `record_a` and `record_b` refer to the same real-world thing?"
CRITERIA = {
    "same": "Yes: the same real-world thing",
    "different": "No: two different things",
    "unsure": "Cannot tell from these records",
}


def prompt(a: dict[str, Any], b: dict[str, Any]) -> str:
    crit = "\n".join(f'- "{k}": {v}' for k, v in CRITERIA.items())
    records = json.dumps({"record_a": a, "record_b": b}, ensure_ascii=False, indent=2)
    return (
        f"{QUESTION}\n\nAnswer with exactly one of:\n{crit}\n\n{records}\n\n"
        'Reply with only a JSON object: {"answer": "same" | "different" | "unsure", '
        '"reason": "<one sentence>"}'
    )


def view(s: dict[str, Any]) -> dict[str, Any]:
    return {"name": s["name"], "type": s["type"], "also_known_as": s["also_known_as"],
            "facts": s["facts"]}  # fmt: skip


def key(p: dict[str, Any]) -> str:
    body = json.dumps([view(p["left"]), view(p["right"])], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode()).hexdigest()


def id_kind(name: str) -> str | None:
    s = name.strip().lower()
    return next((k for pat, k in KINDS if re.match(pat, s)), None)


def jev_call(r: dict[str, Any], keep: float = KEEP) -> str:
    """I2's rule: the guard, then merge / keep by Jev's confidence, else route."""
    ka, kb = id_kind(r["a"]), id_kind(r["b"])
    if ka and kb and ka != kb:
        return "keep"
    conf = float(r["conf"])
    if r["choice"] == "same" and conf >= TAU:
        return "merge"
    if r["choice"] == "different" and conf >= keep:
        return "keep"
    return "route"


def load(kb: str) -> list[dict[str, Any]]:
    """Every labelled pair of one KB, joined with Jev's committed answer."""
    with gzip.open(I2 / f"judged-{kb}.csv.gz", "rt") as f:
        jev = {r["review_id"]: r for r in csv.DictReader(f)}
    rows = []
    for line in (I2 / f"local/pairs-{kb}.jsonl").read_text().splitlines():
        p = json.loads(line)
        r = jev[p["review_id"]]
        rows.append({**r, "key": key(p), "a_view": view(p["left"]), "b_view": view(p["right"])})
    return rows


def ask_opus(text: str) -> dict[str, Any]:
    blind = Path(tempfile.mkdtemp(prefix="northstar-blind-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    cmd = ["claude", "-p", text, "--model", MODEL, "--output-format", "json",
           "--system-prompt", SYSTEM_PROMPT, "--strict-mcp-config", "--mcp-config",
           '{"mcpServers": {}}', "--tools", "", "--setting-sources", "project",
           "--no-session-persistence", "--max-turns", "1"]  # fmt: skip
    try:
        proc = subprocess.run(cmd, cwd=blind, env=dict(os.environ), capture_output=True,
                              text=True, timeout=300)  # fmt: skip
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(proc.stderr[-2000:])
    res: dict[str, Any] = json.loads(proc.stdout)
    return res


def parse(res: dict[str, Any]) -> str:
    """Opus's answer, or 'unparsed' (routed to a person, and counted)."""
    text = str(res.get("result") or "")
    m = re.search(r"\{.*\}", text, re.S)
    try:
        ans = str(json.loads(m.group(0)).get("answer", "")).strip().lower() if m else ""
    except json.JSONDecodeError:
        ans = ""
    return ans if ans in CRITERIA else "unparsed"


def record(row: dict[str, Any], out: Path) -> dict[str, Any]:
    res = ask_opus(prompt(row["a_view"], row["b_view"]))
    line = {"key": row["key"], "answer": parse(res), "text": res.get("result"),
            "usd": float(res.get("total_cost_usd") or 0), "model": MODEL}  # fmt: skip
    with out.open("a") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return line


def done(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return {(x := json.loads(line))["key"]: x for line in path.read_text().splitlines()}


def band(rows: list[dict[str, Any]], keep: float = KEEP) -> list[dict[str, Any]]:
    return [r for r in rows if jev_call(r, keep) == "route"]


def probe() -> None:
    """Three off-band pairs (decided by Jev, never in the test set): measure cost only."""
    rows = [r for r in load("base") if jev_call(r) != "route"]
    picks = [rows[0], rows[len(rows) // 2], rows[-1]]
    for r in picks:
        line = record(r, PROBE)
        print(f"{line['answer']:<10} ${line['usd']:.4f}  {r['a']!r} ~ {r['b']!r}")


def ask(workers: int) -> None:
    todo: dict[str, dict[str, Any]] = {}
    for kb in KBS:
        for r in band(load(kb)):
            todo.setdefault(r["key"], r)
    have = done(ANSWERS)
    pending = [r for k, r in todo.items() if k not in have]
    print(f"{len(todo)} distinct band inputs; {len(have)} answered; {len(pending)} to ask")
    first = pending[:workers]
    with cf.ThreadPoolExecutor(workers) as pool:
        got = list(pool.map(lambda r: record(r, ANSWERS), first))
    if got:
        avg = sum(g["usd"] for g in got) / len(got)
        print(f"first {len(got)} calls: ${avg:.4f} per pair")
        if avg > GUARD_USD:
            sys.exit(f"cost guard: ${avg:.4f} per pair is over ${GUARD_USD}; stopped")
    with cf.ThreadPoolExecutor(workers) as pool:
        list(pool.map(lambda r: record(r, ANSWERS), pending[workers:]))
    spent = sum(x["usd"] for x in done(ANSWERS).values())
    print(f"done; Opus spend so far ${spent:.2f}")


def repeat(workers: int) -> None:
    """Ask a fixed random 100 of the band's inputs a second time: Opus's repeatability."""
    import random

    keys = sorted(done(ANSWERS))
    picks = set(random.Random(REPEAT_SEED).sample(keys, REPEAT_N))
    rows: dict[str, dict[str, Any]] = {}
    for kb in KBS:
        for r in band(load(kb)):
            if r["key"] in picks:
                rows.setdefault(r["key"], r)
    pending = [r for k, r in rows.items() if k not in done(REPEAT)]
    with cf.ThreadPoolExecutor(workers) as pool:
        list(pool.map(lambda r: record(r, REPEAT), pending))
    first, second = done(ANSWERS), done(REPEAT)
    same = sum(first[k]["answer"] == second[k]["answer"] for k in second)
    print(f"repeat: {same}/{len(second)} answers identical")


def decide(r: dict[str, Any], opus: dict[str, dict[str, Any]], arm: str) -> str:
    """One routing decision: merge, keep, or person."""
    keep = KEEP_LOW if arm.endswith("-low") else KEEP
    j = jev_call(r, keep)
    if j != "route":
        return j
    if arm.startswith("jev"):
        return "person"
    o = opus[r["key"]]["answer"]
    if arm.startswith("r1"):  # Opus decides the band; unsure or unparsed goes to a person
        return {"same": "merge", "different": "keep"}.get(o, "person")
    # r2: act only when Opus agrees with Jev's lean (Jev's choice, below its bar)
    if o == r["choice"] == "same":
        return "merge"
    if o == r["choice"] == "different":
        return "keep"
    return "person"


ARMS = {
    "jev": "I2 as pre-registered: Jev + guard, routed band to a person",
    "jev-low": "Jev + guard, keep bar 0.3 (I2 exploratory; tuned on this data)",
    "r1": "Hybrid R1: Opus decides I2's band; unsure to a person",
    "r2": "Hybrid R2: act only when Opus agrees with Jev's lean",
    "r1-low": "R1 on the keep-bar-0.3 band",
    "r2-low": "R2 on the keep-bar-0.3 band",
}


def score() -> None:
    opus = done(ANSWERS)
    lines = ["# G-18: hybrid identity routing, results", ""]
    for kb in KBS:
        rows = load(kb)
        n, same = len(rows), sum(r["label"] == "same" for r in rows)
        lines += [f"## {kb} KB: {n} labelled pairs, {same} truly the same", "",
                  "| Arm | merged | kept | to a person (share) | false merges | missed merges |",
                  "|---|---|---|---|---|---|"]  # fmt: skip
        for arm, desc in ARMS.items():
            c: Counter[str] = Counter()
            for r in rows:
                d = decide(r, opus, arm)
                c[d] += 1
                c["false"] += d == "merge" and r["label"] == "different"
                c["missed"] += d == "keep" and r["label"] == "same"
            lines.append(f"| {desc} | {c['merge']} | {c['keep']} | {c['person']} "
                         f"({c['person'] / n:.2%}) | {c['false']} | {c['missed']} |")  # fmt: skip
        b = band(rows)
        oc = Counter((opus[r["key"]]["answer"], r["label"]) for r in b)
        gc = Counter((r["gpt4o"], r["label"]) for r in b)
        lines += ["", f"Opus on I2's band (n = {len(b)}), (answer, truth): "
                  + ", ".join(f"{k[0]}/{k[1]} {v}" for k, v in sorted(oc.items())),
                  "", "gpt-4o (Utopia governance) on the same band, (call, truth): "
                  + ", ".join(f"{k[0]}/{k[1]} {v}" for k, v in sorted(gc.items())), ""]  # fmt: skip
        queue = sorted((r for r in rows if decide(r, opus, "r2") == "person"),
                       key=lambda r: -float(r["p_same"]))  # fmt: skip
        trues = sum(r["label"] == "same" for r in queue)
        for k in (50, 100, 200):
            hit = sum(r["label"] == "same" for r in queue[:k])
            lines.append(f"- R2's person queue ranked by Jev P(same): top {k} hold {hit} of "
                         f"{trues} true matches")  # fmt: skip
        lines.append("")
    spent = sum(x["usd"] for x in opus.values())
    rep = done(REPEAT)
    spent += sum(x["usd"] for x in rep.values())
    if rep:
        agree = sum(opus[k]["answer"] == rep[k]["answer"] for k in rep)
        lines.append(f"Opus repeatability: {agree}/{len(rep)} answers identical on a second ask.")
    lines.append(f"Opus calls: {len(opus)} distinct inputs plus {len(rep)} repeats, ${spent:.2f}.")
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["probe", "ask", "repeat", "score"])
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    steps = {"probe": probe, "ask": lambda: ask(a.workers), "repeat": lambda: repeat(a.workers),
             "score": score}  # fmt: skip
    steps[a.step]()


if __name__ == "__main__":
    main()
