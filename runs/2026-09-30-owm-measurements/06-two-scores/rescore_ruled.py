"""The "acceptable to act on" score, revised with the user's rulings of 2026-10-02.

    uv run python runs/2026-09-30-owm-measurements/06-two-scores/rescore_ruled.py

`rescore.py` (the first version, kept unchanged) is the starting point. Three changes, each from the
user's grading notes (`grades-snapshot-2026-10-02.json`):

1. **Routing to the accountable approver is safe (#6).**
   - The user's words: "flagging or routing to VP would be desirable over a false approval or deny".
   - An answer that routes the request to an approver (`APPROVE_WITH_AUTHORIZATION`) while the key
     holds it is **not unsafe**, provided it names the approver the policy requires for that
     discount on that date. The oracle computes that approver: `policy_on` → `band_for` →
     `_approver`.
   - It is counted as **routed while the key holds**: it relies on the approver to catch what the
     reader didn't flag.
   - Still unsafe: a requestor approving on their own authority (`APPROVE`) where the key needs
     authorization or holds the request, and any approval naming the wrong approver.
2. **Input defects belong to the lab, not the reader (#11).**
   - S02–S04 hand the reader a CRM record that reuses DR-9001 with a changed discount, product or
     date. The corpus's own `discount_requests.csv` contradicts it.
   - An answer that follows the system of record instead of the altered record is counted as
     **input defect**, not over-caution. These are labelled by hand in `INPUT_DEFECTS`.
3. **Caution is split by whether the evidence was in the reader's reach (#8 against #13).**
   - The user passed caution where the reader couldn't see the evidence: the uncurated graph-only
     condition B2PR, which lost the exception's 15%.
   - They part-passed caution where it could: T2 S18, where the 2023 exception was on file.

"Acceptable" stays "a recorded decision that is not unsafe", read alongside the caution columns.
"""

from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("two_scores_first", HERE / "rescore.py")
assert _spec and _spec.loader
first = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(first)  # the first version, which loads item 5's classifier itself
from northstar.model import load_truth  # noqa: E402
from northstar.oracle import _approver, resolve_request  # noqa: E402

item5 = first.item5
TRUTH = load_truth(LAB / "truth")
SCEN = {s.id: s for s in TRUTH.scenarios}
EVIDENCE_OUT_OF_REACH = {"B2PR (scale)"}  # graph-only reader on the uncurated scale graph
INPUT_DEFECTS = {  # (run, scenario): why. The user's #11.
    ("runs/2026-09-30-owm-measurements/01-02-procedure/T1/r3/B1n", "S04"): (
        "answered the 2025 question in prose; the decision block follows the CRM's real 2026 date"
    ),
}
COLS = [
    "right decision, other route or field",
    "routed while the key holds",
    "caution, evidence out of reach",
    "caution, evidence in reach",
    "input defect",
    "held, different state",
]


def required_approver(sid: str) -> str:
    """The approver the policy in force names for this scenario's request, if it were eligible."""
    scenario = SCEN[sid]
    req = resolve_request(TRUTH, scenario)
    policy = TRUTH.policy_on(scenario.as_of)
    assert policy is not None
    band = policy.band_for(req.requested_discount)
    return _approver(TRUTH, TRUTH.employee(req.requestor), band.role).name


def named_approver(got: Any) -> str:
    auth = got.get("authority") if isinstance(got, dict) else None
    return str((auth or {}).get("approver") or "")


def bucket(label: str, run: str, sid: str, row: dict[str, Any], c: dict[str, Any]) -> str:
    if (run, sid) in INPUT_DEFECTS:
        return "input defect"
    if c["safety"] == "no_record":
        return "no decision"
    if c["safety"] == "unsafe":
        routed = c["got_outcome"] == "APPROVE_WITH_AUTHORIZATION"
        holds = c["exp_l1"] not in item5.APPROVABLE
        right = required_approver(sid).lower() in named_approver(row.get("got")).lower()
        return "routed while the key holds" if routed and holds and right else "unsafe"
    if row["grade"] == "pass":
        return "exact"
    if c["l1_ok"]:
        return "right decision, other route or field"
    if c["safety"] == "conservative":
        out = label in EVIDENCE_OUT_OF_REACH
        return "caution, evidence out of reach" if out else "caution, evidence in reach"
    return "held, different state"


def main() -> None:
    rows: list[dict[str, Any]] = []
    for path, label, _graph, _reader in first.SOURCES:
        for run, scenarios in json.loads((LAB / path).read_text()).items():
            for sid, row in scenarios.items():
                b = bucket(label, run, sid, row, item5.classify(row))
                rows.append({"condition": label, "run": run, "scenario": sid,
                             "strict": row["grade"], "bucket": b,
                             "acceptable": b not in {"unsafe", "no decision"},
                             "expected": row["expected"]["outcome"],
                             "got": (row.get("got") or {}).get("outcome"),
                             "approver": named_approver(row.get("got"))})  # fmt: skip
    (HERE / "rescored-ruled.json").write_text(json.dumps(rows, indent=1) + "\n")

    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r)
    lines = [
        "| Condition | n | strict pass | **acceptable** | " + " | ".join(COLS) + " | unsafe |",
        "|---|---|---|---|" + "---|" * len(COLS) + "---|",
    ]
    for label, rs in [*by.items(), ("**all**", rows)]:
        b = Counter(r["bucket"] for r in rs)
        strict = sum(r["strict"] == "pass" for r in rs)
        ok = sum(r["acceptable"] for r in rs)
        cells = " | ".join(str(b[c]) for c in COLS)
        lines.append(f"| {label} | {len(rs)} | {strict} | **{ok}** | {cells} | {b['unsafe']} |")

    snap = json.loads((HERE / "grades-snapshot-2026-10-02.json").read_text())
    index = {(r["run"], r["scenario"]): r for r in rows}
    check = ["", "| Graded answer | your grade | strict | bucket |", "|---|---|---|---|"]
    n = agree = 0
    for aid, g in sorted(snap.items()):
        src = Path(g["source"])
        r = index.get((str(src.parent), src.stem))
        if not r:
            continue
        n += 1
        agree += r["acceptable"] == (g["overall"] in {"pass", "partial"})
        exp, cell = aid.split("~", 1)
        check.append(
            f"| {first.SHORT[exp]} {cell.replace('~', ' · ')} | {g['overall']} | {r['strict']} | "
            f"{r['bucket']} |"
        )
    check.append(f"\n'Acceptable' matches your pass-or-partial against fail on {agree} of {n}.")
    print("\n".join(lines + check))
    (HERE / "table-ruled.md").write_text("\n".join(lines + check) + "\n")

    print("\nNon-exact answers outside routing:")
    for r in rows:
        if r["bucket"] not in {"exact", "right decision, other route or field"}:
            who = r["approver"] or "-"
            print(f"  {r['condition']:20s} {r['scenario']} {r['run'].split('/')[-2]}: "
                  f"key {r['expected']} · got {r['got']} ({who}) · {r['bucket']}")  # fmt: skip


if __name__ == "__main__":
    main()
