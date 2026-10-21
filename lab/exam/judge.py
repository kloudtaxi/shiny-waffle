"""P2 and P4: does the base state each item? A blind judge reads the base's own facts.

    uv run python lab/exam/judge.py <snapshot file> [--runs 3] [--workers 6]

For each item of `p2_items.yaml`:
- **What the judge reads** is gathered the same way from every foundation: the entities K15 finds
  for each anchor name (up to 10 each, in the foundation's order), and each one's facts (K15), drawn
  as lines. Entities are E1, E2… in that order. No evidence quote is shown: the item is about what
  the base holds as facts, not about the words of its sources.
- **Dated items are read twice:** each fact with its stated validity, and with the interval the
  foundation serves at `x-holds` where it serves one (as the practice set read temporal).
- **The judge** is Claude Sonnet 5.5 through `claude -p`, with no tools, in a fresh temp directory
  outside the repo, with the fixed prompt below. It never learns which foundation it's reading.
  Three runs per reading; the verdict is the majority, and a three-way split is `partly`.

Writes `<snapshot>.judge.json`: every reading's rendered facts, each run's answer, and the verdict,
so every verdict can be audited and overruled.

**`--resume`** (the exam's infra rule): a run that ended on an API error (the account's session
limit, say) did no judging. It's marked `infra`. A resume keeps every other run, asks the infra ones
once more, and keeps the earlier file as `<snapshot>.judge.infra-<k>.json`.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(LAB / "lab"), str(LAB / "src")]

from exam.part1 import items  # noqa: E402
from preflight.spend import CapReached, Guard, Reservation, run_folder_of  # noqa: E402

MODEL = "claude-sonnet-5-5"
# the exam's judge runs: mean cost of 1026 runs in runs/2026-10-17-b20-northstar-exam/part1 was
# $0.01225, rounded up
EST_USD = 0.02
MAX_FACTS_PER_ENTITY = 60
MAX_LINES = 400
VERDICTS = ("stated", "partly", "not_stated")
PROMPT = (
    "You check whether a knowledge base states a fact. You get a statement and the facts the"
    " knowledge base holds about the things the statement names, drawn one per line. Judge only"
    " from those facts, by what they say, not by their wording: a fact can use other words, split"
    " one statement over several facts, or hold a value as a qualifier. Answer `stated` when the"
    " facts say everything the statement says, `partly` when they say some of it (a value without"
    " its dates, say, or the right value on the wrong thing), and `not_stated` when they don't say"
    " it or say otherwise. Answer with one JSON object and nothing else:"
    ' {"verdict": "stated" | "partly" | "not_stated", "lines": [the numbers of the lines you used],'
    ' "why": "<a few words>"}'
)


def _value(v: dict[str, Any] | None) -> str:
    if not v:
        return "?"
    if v.get("kind") == "entity":
        e = v.get("entity") or {}
        kind = (e.get("kind") or {}).get("key")
        return f"{e.get('name')}" + (f" [{kind}]" if kind else "")
    unit = f" {v['unit']}" if v.get("unit") else ""
    return f"{v.get('value')}{unit} ({v.get('datatype')})"


def _when(a: str | None, b: str | None) -> str:
    return f"{a or '…'} → {b or '…'}" if a or b else ""


def render(snap: dict[str, Any], item: dict[str, Any], holds: bool) -> str:
    ents: list[str] = []
    for name in item["anchors"]:
        for eid in snap["anchors"].get(name, []):
            if eid not in ents and eid in snap["entities"]:
                ents.append(eid)
    lines: list[str] = []
    for i, eid in enumerate(ents, 1):
        e = snap["entities"][eid]
        kind = (e.get("kind") or {}).get("key") or "unclassified"
        names = sorted({n.get("name") for n in e.get("names") or []} - {e.get("name")})
        ids = [f"{x.get('system')}: {x.get('id')}" for x in e.get("identifiers") or []]
        head = f"E{i} · {e.get('name')} [{kind}]"
        if names:
            head += " · also named: " + "; ".join(str(n) for n in names)
        if ids:
            head += " · identifiers: " + "; ".join(ids)
        lines.append(head)
        interval = {}
        if holds and snap.get("x_holds", {}).get(eid):
            interval = {h["fact_id"]: (h.get("from"), h.get("to")) for h in snap["x_holds"][eid]}
        for f in (e.get("facts") or [])[:MAX_FACTS_PER_ENTITY]:
            subj = (f.get("subject") or {}).get("name")
            pred = (f.get("predicate") or {}).get("label") or (f.get("predicate") or {}).get("key")
            quals = ", ".join(
                f"{q.get('label') or q.get('key')}: {_value(q.get('value'))}"
                for q in f.get("qualifiers") or []
            )
            valid = f.get("valid") or {}
            stated = _when(
                (valid.get("from") or {}).get("value"), (valid.get("to") or {}).get("value")
            )
            line = f"{subj} — {pred} — {_value(f.get('object'))}"
            if quals:
                line += f" {{{quals}}}"
            if f.get("fact_id") in interval:
                held = _when(*interval[f["fact_id"]])
                line += f" · holds {held or 'always'}"
            elif stated:
                line += f" · valid {stated}"
            if f.get("status") and f["status"] != "current":
                line += f" · {f['status']}"
            lines.append(line)
    lines = lines[:MAX_LINES]
    return "\n".join(f"{n}. {ln}" for n, ln in enumerate(lines, 1)) or "(no facts found)"


def ask(statement: str, facts: str) -> dict[str, Any]:
    blind = Path(tempfile.mkdtemp(prefix="northstar-exam-judge-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError("judge directory inside the repo")
    message = f"Statement: {statement}\n\nThe knowledge base's facts:\n{facts}"
    cmd = [
        "claude", "-p", message, "--model", MODEL, "--output-format", "json",
        "--system-prompt", PROMPT, "--strict-mcp-config", "--tools", "",
        "--setting-sources", "project", "--no-session-persistence", "--max-turns", "2",
    ]  # fmt: skip
    try:
        proc = subprocess.run(cmd, cwd=blind, capture_output=True, text=True, timeout=600)
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    out = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}
    text = str(out.get("result") or "")
    m = re.search(r"\{.*\}", text, re.S)
    try:
        answer = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        answer = {}
    verdict = answer.get("verdict") if answer.get("verdict") in VERDICTS else None
    return {
        "verdict": verdict,
        "answer": answer,
        "cost_usd": out.get("total_cost_usd"),
        "infra": is_infra(out),
    }


def is_infra(out: dict[str, Any]) -> bool:
    """No judging happened: no result, or an API error (subtype `success`, nothing spent)."""
    return not out or (bool(out.get("is_error")) and not out.get("total_cost_usd"))


def hollow(run: dict[str, Any]) -> bool:
    """A kept run that did no judging. Files from before `infra` was recorded are read by their
    traces: no verdict and nothing spent."""
    return bool(run.get("infra")) or (run.get("verdict") is None and not run.get("cost_usd"))


def majority(verdicts: list[str | None]) -> str:
    got = Counter(v for v in verdicts if v)
    if not got:
        return "no answer"
    top, n = got.most_common(1)[0]
    return top if n * 2 > len(verdicts) else "partly"


def readings(snap: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for part, group in items().items():
        for it in group:
            ways = ["stated", "x-holds"] if it.get("dated") else ["stated"]
            for way in ways:
                out.append(
                    {
                        "part": part,
                        "id": it["id"],
                        "u31": bool(it.get("u31")),
                        "reading": way,
                        "statement": it["statement"],
                        "facts": render(snap, it, holds=way == "x-holds"),
                    }
                )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(prog="exam-judge")
    ap.add_argument("snapshot", type=Path)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--cap-usd", type=float, required=True)
    ap.add_argument("--est-usd", type=float, default=EST_USD, help="reserved for each call")
    a = ap.parse_args()
    snap = json.loads(a.snapshot.read_text())
    rs = readings(snap)
    out = a.snapshot.with_suffix(".judge.json")
    answers: dict[int, list[dict[str, Any]]] = {i: [] for i in range(len(rs))}
    if a.resume:
        before = json.loads(out.read_text())
        if [(r["id"], r["reading"], r["facts"]) for r in before["readings"]] != [
            (r["id"], r["reading"], r["facts"]) for r in rs
        ]:
            raise SystemExit("the snapshot's readings differ from the judged ones; refusing")
        k = len(list(out.parent.glob(out.name.replace(".judge.json", ".judge.infra-*.json")))) + 1
        out.rename(out.with_name(out.name.replace(".judge.json", f".judge.infra-{k}.json")))
        for i, r in enumerate(before["readings"]):
            answers[i] = [x for x in r["runs"] if not hollow(x)]
    jobs = [(i, r) for i in range(len(rs)) for r in range(a.runs - len(answers[i]))]

    guard = Guard(run_folder_of(a.snapshot.resolve()), a.cap_usd, a.est_usd,
                  f"judge {a.snapshot.name}")  # fmt: skip
    held: list[Reservation] = []

    def go(job: tuple[int, int]) -> tuple[int, dict[str, Any]] | None:
        i, _ = job
        try:
            reservation = guard.reserve(f"{i}")
        except CapReached as exc:
            print(f"reading {i} skipped: {exc}", flush=True)
            return None
        held.append(reservation)  # stays live, at its settled cost, until the file is written
        ans = ask(rs[i]["statement"], rs[i]["facts"])
        reservation.settle(float(ans.get("cost_usd") or 0))
        return i, ans

    try:
        with cf.ThreadPoolExecutor(a.workers) as pool:
            for res in pool.map(go, jobs):
                if res is not None:
                    answers[res[0]].append(res[1])
        for i, r in enumerate(rs):
            r["runs"] = answers[i]
            r["verdict"] = majority([x["verdict"] for x in answers[i]])
        out.write_text(json.dumps({"model": MODEL, "prompt": PROMPT, "readings": rs}, indent=1,
                                  ensure_ascii=False) + "\n")  # fmt: skip
    finally:
        for reservation in held:
            reservation.release()
    cost = sum(float(x.get("cost_usd") or 0) for v in answers.values() for x in v)
    left = sum(hollow(x) for v in answers.values() for x in v)
    if left:
        print(f"{left} runs ended on an API error: resume once more, or leave them for the user")
    tally = Counter((r["part"], r["reading"], r["verdict"]) for r in rs)
    print(json.dumps({f"{p} {w} {v}": n for (p, w, v), n in sorted(tally.items())}, indent=1))
    print(f"judge cost ${cost:.2f} -> {out}")


if __name__ == "__main__":
    main()
