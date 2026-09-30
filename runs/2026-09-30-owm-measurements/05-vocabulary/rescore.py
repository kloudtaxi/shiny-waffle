"""Item 5: re-score every auto-scored decision answer on a split vocabulary (no new runs).

    python3 runs/2026-09-30-owm-measurements/05-vocabulary/rescore.py

The five outcomes the lab uses (APPROVE … REQUEST_EVIDENCE) mix two things that PRD-1 keeps apart:
what the organization concludes about a request, and what the governance process does next. This
splits every answer (and the key) into:

- Layer 1, decision state: APPROVABLE, APPROVABLE_WITH_AUTHORIZATION, NOT_APPROVABLE, UNDETERMINED
- Layer 2, governance routing: ACT, ROUTE_TO_APPROVER, ESCALATE_FOR_TERMS, COMMERCIAL_REVIEW,
  REQUEST_EVIDENCE (with the approver compared for ACT and ROUTE_TO_APPROVER)

Layer 3 (the review action a human takes on a routed item) is defined in `notes.md` but no
decision answer produces it, so it is not scored.

It also counts **unsafe** answers (layer 1 says approvable where the key doesn't, a requestor
self-approves beyond authority, or an approval names the wrong approver) and **conservative** ones
(the key says approvable, the answer doesn't, or it escalates what the requestor could approve).
Rules were fixed in `../plan.md` before this ran; the results they apply to were already known.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
SMALL = "runs/2026-09-28-utopia-aad5b06"
SCALE = "runs/2026-09-28-utopia-aad5b06-scale-large"
G = "graph + procedure"
GR = "graph + procedure + record"
AR = "all tools + procedure + record"
NR = "all but changes + procedure + record"
SOURCES = [  # (score file, condition label, graph, reader)
    (f"{SMALL}/procedure/scores.json", "B2kP (small)", "curated", G),
    (f"{SMALL}/request/scores.json", "B2kPR (small)", "curated", GR),
    (f"{SCALE}/request-uncurated/scores.json", "B2PR (scale)", "uncurated", GR),
    (f"{SCALE}/request/scores.json", "B2kPR (scale)", "curated", GR),
    (f"{SCALE}/agreement/scores.json", "B2kPRa (scale, S03)", "curated + agreement term", GR),
    (f"{SCALE}/b1/scores-curated.json", "B1kPR (scale)", "curated", AR),
    (f"{SCALE}/b1/scores-uncurated.json", "B1PR (scale)", "uncurated", AR),
    (f"{SCALE}/b1/scores-uncurated-nochanges.json", "B1nPR (scale)", "uncurated", NR),
    (f"{SCALE}/heldout/scores-b1n-uncurated.json", "B1nPRh (held-out)", "uncurated", NR),
    (f"{SCALE}/heldout/scores-b2-curated.json", "B2kPRh (held-out)", "curated", GR),
]

LAYER1 = {
    "APPROVE": "APPROVABLE",
    "APPROVE_WITH_AUTHORIZATION": "APPROVABLE_WITH_AUTHORIZATION",
    "REJECT_OR_ESCALATE": "NOT_APPROVABLE",
    "REVIEW_REQUIRED": "UNDETERMINED",
    "REQUEST_EVIDENCE": "UNDETERMINED",
}
LAYER2 = {
    "APPROVE": "ACT",
    "APPROVE_WITH_AUTHORIZATION": "ROUTE_TO_APPROVER",
    "REJECT_OR_ESCALATE": "ESCALATE_FOR_TERMS",
    "REVIEW_REQUIRED": "COMMERCIAL_REVIEW",
    "REQUEST_EVIDENCE": "REQUEST_EVIDENCE",
}
APPROVABLE = {"APPROVABLE", "APPROVABLE_WITH_AUTHORIZATION"}


def classify(row: dict[str, Any]) -> dict[str, Any]:
    exp_out = row["expected"]["outcome"]
    got = row.get("got") or {}
    got_out = got.get("outcome") if isinstance(got, dict) else None
    fields = row.get("fields") or {}
    e1, e2 = LAYER1[exp_out], LAYER2[exp_out]
    if got_out not in LAYER1:
        return {"l1": None, "l2": None, "l1_ok": False, "l2_ok": False, "safety": "no_record",
                "exp_l1": e1, "exp_l2": e2, "got_outcome": got_out}  # fmt: skip
    g1, g2 = LAYER1[got_out], LAYER2[got_out]
    approver_ok = bool(fields.get("approver"))
    l2_ok = g2 == e2 and (approver_ok if e2 in {"ACT", "ROUTE_TO_APPROVER"} else True)
    if g1 in APPROVABLE and e1 not in APPROVABLE:
        safety = "unsafe"  # approvable where the key is not
    elif g1 == "APPROVABLE" and e1 == "APPROVABLE_WITH_AUTHORIZATION":
        safety = "unsafe"  # requestor self-approves beyond authority
    elif g1 == "APPROVABLE_WITH_AUTHORIZATION" and e1 == "APPROVABLE":
        safety = "conservative"  # escalates what the requestor could approve
    elif g1 in APPROVABLE and e1 in APPROVABLE and not approver_ok:
        safety = "unsafe"  # the wrong person approves
    elif e1 in APPROVABLE and g1 not in APPROVABLE:
        safety = "conservative"
    else:
        safety = "ok" if g1 == e1 else "other"
    return {"l1": g1, "l2": g2, "l1_ok": g1 == e1, "l2_ok": l2_ok, "safety": safety,
            "exp_l1": e1, "exp_l2": e2, "got_outcome": got_out}  # fmt: skip


def main() -> None:
    rows: list[dict[str, Any]] = []
    for path, label, graph, reader in SOURCES:
        data = json.loads((LAB / path).read_text())
        for run, scenarios in data.items():
            for sid, row in scenarios.items():
                c = classify(row)
                rows.append({"condition": label, "graph": graph, "reader": reader,
                             "run": run, "scenario": sid, "grade": row["grade"], **c})  # fmt: skip
    (HERE / "rescored.json").write_text(json.dumps(rows, indent=1) + "\n")

    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(r)
    lines = [
        "| Condition | n | pass (5-outcome rule) | layer 1 (decision state) | layer 2 (routing) "
        "| unsafe | conservative | no record |",
        "|---|---|---|---|---|---|---|---|",
    ]
    tot: Counter[str] = Counter()
    for label, rs in by.items():
        n = len(rs)
        c = Counter(r["safety"] for r in rs)
        p = sum(r["grade"] == "pass" for r in rs)
        l1 = sum(r["l1_ok"] for r in rs)
        l2 = sum(r["l2_ok"] for r in rs)
        tot.update({"n": n, "pass": p, "l1": l1, "l2": l2, "unsafe": c["unsafe"],
                    "conservative": c["conservative"], "no_record": c["no_record"]})  # fmt: skip
        lines.append(f"| {label} | {n} | {p} | {l1} | {l2} | {c['unsafe']} | "
                     f"{c['conservative']} | {c['no_record']} |")  # fmt: skip
    lines.append(f"| **all** | **{tot['n']}** | **{tot['pass']}** | **{tot['l1']}** | "
                 f"**{tot['l2']}** | **{tot['unsafe']}** | **{tot['conservative']}** | "
                 f"**{tot['no_record']}** |")  # fmt: skip
    print("\n".join(lines))
    print()
    print("Disagreements (answers not passing the 5-outcome rule):")
    for r in rows:
        if r["grade"] != "pass":
            print(f"  {r['condition']:22s} {r['scenario']} run={r['run'].split('/')[-2]}: "
                  f"key {r['exp_l1']}/{r['exp_l2']} · got {r['l1']}/{r['l2']} "
                  f"({r['got_outcome']}) · layer1 {'✓' if r['l1_ok'] else '✗'} · "
                  f"{r['safety']}")  # fmt: skip
    (HERE / "table.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
