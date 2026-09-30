"""Write this batch's ledger annotations from its score files.

    python3 runs/2026-09-30-owm-measurements/ledger_annotations.py
    python3 tracker/build_seed.py runs/2026-09-30-owm-measurements

Every grade here is the auto-scorer's, copied from `01-02-procedure/scores-T{1,2}.json` and
`04-decision-memory/scores.json`: provisional, never a human grade. The ledger keeps human grades
in its own `grades` collection, which neither this script nor the seed touches.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = LAB / "tracker/annotations" / f"{HERE.name}.json"
MARK = {True: "✓", False: "✗"}

CONDITIONS = {
    "T1": {"prefix": "01-02-procedure/T1", "questions": "01-02-procedure/questions.tsv"},
    "T2": {"prefix": "01-02-procedure/T2", "questions": "01-02-procedure/questions.tsv"},
    "DMa": {"prefix": "04-decision-memory/a", "questions": "04-decision-memory/questions.tsv"},
    "DMb": {"prefix": "04-decision-memory/b", "questions": "04-decision-memory/questions.tsv"},
    "DMc": {"prefix": "04-decision-memory/c", "questions": "04-decision-memory/questions.tsv"},
}

FINDINGS = [
    {
        "id": "m1",
        "category": "owm",
        "title": "Agents call for a procedure served as a governed object",
        "body": "With the procedure removed from the system prompt and served by the OWM "
        "stand-in's get_procedure, 102 of 102 blind readers found and called it unprompted. On "
        "S01-S14 accuracy held: 29/33 via the tool against 30/33 with the same procedure in the "
        "prompt; the one extra miss is conservative (a 2025 request routed to VP Sales).",
        "evidence": ["01-02-procedure/notes.md", "01-02-procedure/table.md"],
    },
    {
        "id": "m2",
        "category": "owm",
        "title": "A prose procedure behaves like untested code",
        "body": "Procedure v2's one-sentence applicability rule fixed S13 and the fresh S15 "
        "(0/3 -> 3/3 each) with no over-triggering on S16, S17 or S19, but regressed S18 "
        "(3/3 -> 1/3): readers judged the agreement the request cites instead of the terms in "
        "force that day. The fix moved the failure to a neighbouring boundary. v2 is not "
        "adopted; a governed procedure plausibly needs an executable, test-covered reference "
        "beside the prose.",
        "evidence": ["01-02-procedure/notes.md", "01-02-procedure/scores-T2.json"],
    },
    {
        "id": "m3",
        "category": "owm",
        "title": "Rank constraints flag the inverted org graph, with the evidence attached",
        "body": "A deterministic check over the foundation's reports_to facts flagged 13 of 13 "
        "inverted lines in the small graph as ingested (C2 one manager, C3 rank) and 0 of 49 "
        "correct lines. Acyclicity caught nothing: an inverted tree is still a tree. The "
        "conflict records keep the extractor's quote, which shows it misread the org chart; a "
        "silent fix would have hidden that. At scale, before curation, there were no edges at "
        "all: a coverage gap, not a conflict.",
        "evidence": ["03-constraints/notes.md", "03-constraints/table.md"],
    },
    {
        "id": "m4",
        "category": "owm",
        "title": "A decision stored as a document becomes evidence",
        "body": "Written back to Utopia as a document, agent A's decision was extracted as "
        "graph facts with no validity window (Sarah Chen limit 10%, authorized no), and 2 of 3 "
        "later readers cited the decision as a source for the customer identity, one noting it "
        "did not recheck the source files. The same decision served as a typed record was "
        "consulted as precedent and cited as evidence by none. Decision records need their own "
        "provenance class, apart from evidence.",
        "evidence": [
            "04-decision-memory/notes.md",
            "04-decision-memory/extracted-from-decision-log.tsv",
        ],
    },
    {
        "id": "m5",
        "category": "agent",
        "title": "No stale reuse after the policy changed",
        "body": "On the DR-9001 request again in 2027 (S21), all 9 readers named the CRO, "
        "David Morgan, under the 2027 policy, including the 6 that had the 2026 decision "
        "(Michael Torres) in memory. They used it as precedent and said the rules had changed. "
        "Retrieval on 'was it decided' worked for both carriers; the typed record was cheaper "
        "(3.3 vs 5.3 turns, no source reads) but not on 'was it valid when made', where both "
        "re-read the 2026 policy.",
        "evidence": ["04-decision-memory/notes.md", "04-decision-memory/table.md"],
    },
    {
        "id": "m6",
        "category": "method",
        "title": "With procedure and record present, every miss is routing, not decision state",
        "body": "Re-scoring 134 earlier answers on a split vocabulary (decision state / "
        "governance routing / review action): every miss with the procedure and request record "
        "present is a COMMERCIAL_REVIEW vs REQUEST_EVIDENCE disagreement with the decision "
        "state right. 1 unsafe answer in 134, 0 in 119 once the record is present. Not blind: "
        "the answers were known when the rules were written.",
        "evidence": ["05-vocabulary/notes.md", "05-vocabulary/table.md"],
    },
    {
        "id": "m7",
        "category": "foundation",
        "title": "Deleting a document leaves its name facts live",
        "body": "Deleting the decision-log fixture invalidated its content facts but left 23 "
        "known_as facts live, 15 of them with the deleted document as their only evidence "
        "(for example 'Decision record DEC-2026-0001'). Names only, no decision content; "
        "disclosed rather than removed by hand.",
        "evidence": ["04-decision-memory/extracted-from-decision-log.tsv"],
    },
]


def decision_note(row: dict[str, Any]) -> str:
    fields = ", ".join(f"{k} {MARK[bool(v)]}" for k, v in row.get("fields", {}).items())
    note = f"Auto-scored vs answer key: {row.get('note', '')}. Fields: {fields}."
    if "called_get_procedure" in row:
        note += f" get_procedure called: {MARK[bool(row['called_get_procedure'])]}."
    return note


def memory_note(qid: str, row: dict[str, Any]) -> str:
    a = row.get("answer") or {}
    if qid == "M3":
        auth = a.get("authority") or {}
        return (
            f"Auto-scored vs S21's key (CRO, David Morgan): outcome {a.get('outcome')}, "
            f"approver {auth.get('approver')}."
        )
    keys = (
        ("decided", "outcome", "approved_by", "policy")
        if qid == "M1"
        else (
            "decision_found",
            "valid_when_made",
            "approved_by",
            "approver_role_then",
        )
    )
    got = "; ".join(f"{k}: {a.get(k)}" for k in keys)
    return f"Auto-scored (item 4 rule, prereg.md): {got}."


def grades() -> dict[tuple[str, str, int], tuple[str, str]]:
    out: dict[tuple[str, str, int], tuple[str, str]] = {}
    for arm in ("T1", "T2"):
        scores = json.loads((HERE / f"01-02-procedure/scores-{arm}.json").read_text())
        for run, rows in scores.items():
            rep = int(run.split("/")[-2][1:])
            for sid, row in rows.items():
                out[(arm, sid, rep)] = (row["grade"], decision_note(row))
    for key, row in json.loads((HERE / "04-decision-memory/scores.json").read_text()).items():
        arm, r, qid = key.split("/")
        out[(f"DM{arm}", qid, int(r[1:]))] = (row["grade"], memory_note(qid, row))
    return out


def main() -> None:
    g = grades()
    provisional: dict[str, dict[str, list[str]]] = {}
    repeats = []
    for (cid, sid, rep), (grade, note) in sorted(g.items()):
        if rep == 1:
            provisional.setdefault(cid, {})[sid] = [grade, note]
        else:
            repeats.append(
                {"condition": cid, "scenario": sid, "repeat": rep, "grade": grade, "note": note}
            )
    ann = {
        "_about": "Annotations for the OWM measurements batch (tracker/build_seed.py), written by "
        "ledger_annotations.py from the batch's score files. Every grade is the auto-scorer's. "
        "{run} expands to runs/<run>.",
        "namespace_conditions": True,
        "conditions": {
            cid: {
                "folder": f"{c['prefix']}/r1/B1n",
                "repeats": f"{c['prefix']}/r{{n}}/B1n",
                "questions": c["questions"],
            }
            for cid, c in CONDITIONS.items()
        },
        "experiment": {
            "title": "OWM measurements · items 1–5",
            "date": "2026-09-30",
            "status": "Done",
            "status_note": "Procedure via tool: called 102/102, accuracy held. v2 fixed S13/S15 "
            "but regressed S18. Constraints flag 13/13 inverted lines. Decision memory: both "
            "carriers retrieve; the document carrier became evidence. No stale reuse (9/9).",
            "next": [
                "Your grading pass in the ledger: calibrate Claude's provisional grades",
                "Rulings on the amendment candidates "
                "(docs/owm-overhaul-reconciliation-2026-09-29.md §3-4)",
                "Decision memory with many decisions: retrieval among hundreds of records",
                "Any procedure v3 only with its own fresh held-out scenarios",
            ],
            "utopia": "dev @ aad5b06",
            "lab_commit": "fe41e59",
            "seed": 20260923,
            "notes": "{run}/notes.md",
            "docs": [
                "{run}/plan.md",
                "{run}/01-02-procedure/notes.md",
                "{run}/03-constraints/notes.md",
                "{run}/04-decision-memory/notes.md",
                "{run}/05-vocabulary/notes.md",
                "docs/owm-overhaul-reconciliation-2026-09-29.md",
            ],
        },
        "default_first_run": [None, "Not read yet."],
        "provisional": provisional,
        "provisional_repeats": repeats,
        "findings": FINDINGS,
    }
    OUT.write_text(json.dumps(ann, ensure_ascii=False, indent=1) + "\n")
    print(f"{OUT.relative_to(LAB)}: {len(g)} grades, {len(FINDINGS)} findings")


if __name__ == "__main__":
    main()
