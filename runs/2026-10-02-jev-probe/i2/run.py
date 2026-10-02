"""I2: customer matching on the whole duplicate queue, with a guard and a chosen operating point.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-02-jev-probe/i2/run.py [--replay]

The design is in `../plan-3.md`:
- Every labelled pair in the scale base KB and in the scale missing-contract KB, labelled and
  rebuilt by `../j4/build_pairs.py` (including the merge-time fix).
- Jev answers J4's question for each pair.
- The guard (code): two id-named sides of different kinds are kept apart.
- The sweep: merge threshold τ in {0.5, 0.6, 0.7, 0.8, 0.9}; keep at confidence ≥ 0.5; anything
  else is routed to a person.
- The operating point: the smallest τ with zero false merges on the base KB, else the fewest
  (ties to the fewest routed). It is applied unchanged to the replication.

The recording and the pair files are large, so they stay under `local/` (gitignored). The
recording is seeded with J4's calls. Committed: `judged-<kb>.csv.gz` (one compact row per pair)
and `results.md`.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import shutil
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "j4"))
sys.path.insert(0, str(LAB / "lab/decision_engine"))
import build_pairs as bp  # noqa: E402
import judge as j4  # noqa: E402
from engine import Recorder, Replay, TypeSafe  # noqa: E402

LOCAL = HERE / "local"
CALLS = LOCAL / "engine-calls.jsonl"
KBS = {"base": "01a0ea56-61e7-79e3-99d1-e82b5d6af79a",
       "missing-contract": "01a0ea56-65d0-73d2-940d-6f1f9da0d800"}  # fmt: skip
TAUS = [0.5, 0.6, 0.7, 0.8, 0.9]
KINDS = [(r"so-\d+", "order"), (r"dr-\d+", "request"), (r"crm-\d+", "customer"),
         (r"c-\d+", "customer"), (r"emp-\d+", "employee"), (r"prod-\d+", "product")]  # fmt: skip


def id_kind(name: str) -> str | None:
    s = name.strip().lower()
    return next((k for pat, k in KINDS if re.match(pat, s)), None)


def call(row: dict[str, Any], tau: float) -> str:
    ka, kb = id_kind(row["a"]), id_kind(row["b"])
    if ka and kb and ka != kb:
        return "keep"  # guard: an order is never a customer
    if row["choice"] == "same" and row["conf"] >= tau:
        return "merge"
    if row["choice"] == "different" and row["conf"] >= 0.5:
        return "keep"
    return "route"


def tally(rows: list[dict[str, Any]], decide: Any) -> dict[str, int]:
    c: Counter[str] = Counter()
    for r in rows:
        d = decide(r)
        c[d] += 1
        c["false_merge"] += d == "merge" and r["label"] == "different"
        c["missed_merge"] += d == "keep" and r["label"] == "same"
        c["right"] += d != "route" and (d == "merge") == (r["label"] == "same")
    return dict(c)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    LOCAL.mkdir(exist_ok=True)
    (LOCAL / ".gitignore").write_text("*\n")
    if not CALLS.exists():
        shutil.copy(j4.CALLS, CALLS)  # J4's recorded calls answer the pairs it already asked
    eng = Replay(CALLS, j4.MODEL) if a.replay else Recorder(TypeSafe(j4.MODEL), CALLS)

    judged: dict[str, list[dict[str, Any]]] = {}
    for name, kb in KBS.items():
        resolve = bp.Resolver(bp.corpus(kb))
        pairs = bp.label_all(kb, resolve)
        with (LOCAL / f"pairs-{name}.jsonl").open("w") as f:
            for p in pairs:
                f.write(json.dumps(p, ensure_ascii=False, default=str) + "\n")

        def ask(p: dict[str, Any]) -> dict[str, Any]:
            state = {"record_a": j4.side(p["left"]), "record_b": j4.side(p["right"])}
            ans = eng.ask(state, {"same": j4.Q_SAME})["answers"]["same"]
            return {"review_id": p["review_id"], "label": p["label"], "composite": p["composite"],
                    "a": p["left_name"], "b": p["right_name"], "gpt4o": j4.gpt_call(p),
                    "choice": ans["choice"], "conf": ans["confidence"],
                    "p_same": ans["probabilities"].get("same", 0.0)}  # fmt: skip

        with ThreadPoolExecutor(a.workers) as pool:
            judged[name] = list(pool.map(ask, pairs))
        with gzip.open(HERE / f"judged-{name}.csv.gz", "wt", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(judged[name][0]))
            w.writeheader()
            w.writerows(judged[name])
        print(f"{name}: {len(pairs)} labelled pairs judged")

    base = judged["base"]
    sweep = {t: tally(base, lambda r, t=t: call(r, t)) for t in TAUS}
    zero = [t for t in TAUS if sweep[t]["false_merge"] == 0]
    chosen = zero[0] if zero else min(TAUS, key=lambda t: (sweep[t]["false_merge"],
                                                           sweep[t].get("route", 0)))  # fmt: skip

    lines = ["# I2: customer matching on the whole duplicate queue", ""]
    hdr = ["| | merged | kept | routed (share) | false merges | missed merges "
           "| right when acting |", "|---|---|---|---|---|---|---|"]  # fmt: skip

    def row(label: str, t: dict[str, int], n: int) -> str:
        acted = t.get("merge", 0) + t.get("keep", 0)
        share = t["right"] / max(acted, 1)
        return (f"| {label} | {t.get('merge', 0)} | {t.get('keep', 0)} | "
                f"{t.get('route', 0)} ({t.get('route', 0) / n:.1%}) | {t['false_merge']} | "
                f"{t['missed_merge']} | {t['right']}/{acted} ({share:.2%}) |")  # fmt: skip

    for name, rows in judged.items():
        n = len(rows)
        lines += [f"## {name} KB: {n} labelled pairs, {sum(r['label'] == 'same' for r in rows)} "
                  "truly the same", ""] + hdr  # fmt: skip
        lines.append(row("gpt-4o (Utopia governance)", tally(rows, lambda r: r["gpt4o"]), n))
        for t in TAUS:
            mark = " **(chosen)**" if t == chosen else ""
            lines.append(
                row(f"Jev + guard, τ = {t}{mark}", tally(rows, lambda r, t=t: call(r, t)), n)
            )
        lines.append("")
    lines.append(f"Operating point, by the pre-registered rule on the base KB: **τ = {chosen}**, "
                 "applied unchanged to the missing-contract KB.")  # fmt: skip
    (HERE / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
