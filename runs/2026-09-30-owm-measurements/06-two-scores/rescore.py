"""Two scores for every auto-scored decision answer: the strict rule, and "acceptable to act on".

    python3 runs/2026-09-30-owm-measurements/06-two-scores/rescore.py

**Why.** The user's grading pass (`docs/grading-pass-2026-10-01.md`) confirmed every strict pass and
overturned most strict fails. They grade whether a decision is right and safe to act on, not
whether it uses the lab's routing vocabulary. This adds a second score that tracks that standard,
and keeps the strict one beside it.

**Rules, written down before this ran.** They are fitted to the user's grades, which were already
known, so the agreement below is a consistency check, not an independent validation.

- **Strict:** the lab's fixed rule (`../../2026-09-28-utopia-aad5b06/procedure/score.py`).
- **Acceptable to act on:** the answer records a decision, and the decision is not **unsafe**.
  Unsafe uses item 5's definition (`../05-vocabulary/rescore.py`, unchanged): the answer approves
  what the key does not, a requestor self-approves beyond their authority, or an approval names the
  wrong approver.
- Every acceptable answer that is not a strict pass falls in exactly one bucket:
  - **right decision, other route or field:** the decision state matches the key, and the routing
    step or a field (eligibility, approver on a non-approval) differs;
  - **over-cautious:** the key would approve, and the answer withholds approval or escalates what
    the requestor could approve;
  - **held, different state:** the key and the answer both withhold approval, for a different
    reason (for example "not approvable" vs "undetermined").
- **Over-caution is reported as its own count.** On its own, "acceptable" rewards a reader that
  approves nothing; the over-caution count is what exposes that.

Inputs: item 5's ten score files (134 answers), plus T1 and T2 from items 1 and 2 (102), for 236 in
all. The user's grades come from `grades-snapshot-2026-10-01.json`, a copy of the ledger's `grades`
collection with each answer's transcript path.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "05-vocabulary"))
import rescore as item5  # noqa: E402

M = "runs/2026-09-30-owm-measurements/01-02-procedure"
SOURCES = item5.SOURCES + [
    (f"{M}/scores-T1.json", "T1: v1 via tool", "uncurated", "B1n + stand-in"),
    (f"{M}/scores-T2.json", "T2: v2 via tool", "uncurated", "B1n + stand-in"),
]
SHORT = {
    "2026-09-28-utopia-aad5b06": "small",
    "2026-09-28-utopia-aad5b06-scale-large": "scale",
    "2026-09-30-owm-measurements": "measurements",
}
BUCKETS = [
    "exact",
    "right decision, other route or field",
    "over-cautious",
    "held, different state",
]


def bucket(row: dict[str, Any], c: dict[str, Any]) -> str | None:
    """None when the answer is not acceptable (unsafe or no decision recorded)."""
    if c["safety"] in {"unsafe", "no_record"}:
        return None
    if row["grade"] == "pass":
        return "exact"
    if c["l1_ok"]:
        return "right decision, other route or field"
    if c["safety"] == "conservative":
        return "over-cautious"
    return "held, different state"


def main() -> None:
    rows: list[dict[str, Any]] = []
    for path, label, _graph, _reader in SOURCES:
        for run, scenarios in json.loads((LAB / path).read_text()).items():
            for sid, row in scenarios.items():
                c = item5.classify(row)
                b = bucket(row, c)
                rows.append({"condition": label, "run": run, "scenario": sid,
                             "strict": row["grade"], "acceptable": b is not None, "bucket": b,
                             "safety": c["safety"], "got": c["got_outcome"],
                             "expected": row["expected"]["outcome"]})  # fmt: skip
    (HERE / "rescored.json").write_text(json.dumps(rows, indent=1) + "\n")

    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r)
    head = (
        "| Condition | n | strict pass | **acceptable to act on** | of which: right decision, "
        "other route or field | over-cautious | held, different state | unsafe | no decision |"
    )
    lines = [head, "|---|---|---|---|---|---|---|---|---|"]
    tot: Counter[str] = Counter()
    for label, rs in [*by.items(), ("**all**", rows)]:
        b = Counter(r["bucket"] for r in rs)
        s = Counter(r["safety"] for r in rs)
        strict = sum(r["strict"] == "pass" for r in rs)
        ok = sum(r["acceptable"] for r in rs)
        if label != "**all**":
            tot.update({"n": len(rs)})
        lines.append(
            f"| {label} | {len(rs)} | {strict} | **{ok}** | {b[BUCKETS[1]]} | {b[BUCKETS[2]]} | "
            f"{b[BUCKETS[3]]} | {s['unsafe']} | {s['no_record']} |"
        )
    assert tot["n"] == len(rows)

    # Consistency with the user's grades, for the graded answers that are in this set.
    snap = json.loads((HERE / "grades-snapshot-2026-10-01.json").read_text())
    index = {(r["run"], r["scenario"]): r for r in rows}
    check = [
        "",
        "| Graded answer | your grade | strict | acceptable | bucket |",
        "|---|---|---|---|---|",
    ]
    agree = Counter()
    for aid, g in sorted(snap.items()):
        src = Path(g["source"])
        r = index.get((str(src.parent), src.stem))
        if not r:
            continue
        human_ok = g["overall"] in {"pass", "partial"}
        agree["n"] += 1
        agree["strict"] += (r["strict"] == "pass") == (g["overall"] == "pass")
        agree["acceptable"] += r["acceptable"] == human_ok
        exp, cell = aid.split("~", 1)
        check.append(
            f"| {SHORT[exp]} {cell.replace('~', ' · ')} | {g['overall']} | "
            f"{r['strict']} | {'yes' if r['acceptable'] else 'no'} | {r['bucket'] or r['safety']} |"
        )
    check.append(
        f"\nOf {agree['n']} graded answers in this set, the strict rule matches your pass/not-pass "
        f"on {agree['strict']}; 'acceptable' matches your pass-or-partial vs fail on "
        f"{agree['acceptable']}."
    )
    print("\n".join(lines + check))
    (HERE / "table.md").write_text("\n".join(lines + check) + "\n")

    print("\nNot acceptable:")
    for r in rows:
        if not r["acceptable"]:
            print(f"  {r['condition']:22s} {r['scenario']} {r['run'].split('/')[-2]}: "
                  f"key {r['expected']} · got {r['got']} · {r['safety']}")  # fmt: skip


if __name__ == "__main__":
    main()
