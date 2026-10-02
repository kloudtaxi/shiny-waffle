"""Write the Jev probe's ledger annotations (the J3 reader answers) from `j3/scores.json`.

    python3 runs/2026-10-02-jev-probe/ledger_annotations.py
    python3 tracker/build_seed.py runs/2026-10-02-jev-probe

The provisional grade is Claude's reading of each answer (`j3/notes.md`), not the text rule, whose
recall was 5/9. Each note gives the rule's result as well. Human grades live only in the ledger's
`grades` collection, which nothing here touches.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
OUT = LAB / "tracker/annotations" / f"{HERE.name}.json"
READ = {  # Claude's read of all 12 answers (j3/notes.md)
    "S22": (
        "fail",
        "Flags the 8%/15% conflict in prose and asks for confirmation, but the decision block "
        "says APPROVE on the submitted 8% (Sarah), with the 15% case in the approver text. "
        "Acting on the block approves.",
    ),
    "S23": (
        "pass",
        "Decided on the CRM's 2026 date: VP Sales, Michael Torres. States the date conflict.",
    ),
    "S24": (
        "pass",
        "Decided on the CRM's Pending status: Michael Torres must still approve. States the "
        "status conflict.",
    ),
    "S25": (
        "pass",
        "No conflict claimed; routes to Michael Torres. (Any rule 'false alarm' here is "
        "'different company', which is about Acme Industrial.)",
    ),
}


def main() -> None:
    scores = json.loads((HERE / "j3/scores.json").read_text())
    provisional: dict[str, dict[str, list[str]]] = {"J3R": {}}
    repeats = []
    for key, r in sorted(scores.items()):
        run, sid = key.split("/")
        rep = int(run[1:])
        flag = r.get("conflict_flagged", r.get("no_false_alarm"))
        grade, read = READ[sid]
        note = (f"{read} Text rule: strict {r['strict']}, decision {r['decision']} "
                f"({r['outcome']}), flag/no-alarm {flag}, unsafe {r['unsafe']}.")  # fmt: skip
        if rep == 1:
            provisional["J3R"][sid] = [grade, note]
        else:
            repeats.append(
                {"condition": "J3R", "scenario": sid, "repeat": rep, "grade": grade, "note": note}
            )
    ann = {
        "_about": "Annotations for the Jev probe (tracker/build_seed.py), written by "
        "ledger_annotations.py. {run} expands to runs/<run>.",
        "namespace_conditions": True,
        "conditions": {
            "J3R": {
                "folder": "j3/r1/B1n",
                "repeats": "j3/r{n}/B1n",
                "questions": "j3/questions.tsv",
            }
        },
        "experiment": {
            "title": "Jev probe · J1–J3",
            "date": "2026-10-02",
            "status": "Done",
            "status_note": "J1: Jev judges and code composes, 18/18 on gold evidence. J2: "
            "calibrated (ECE ≤ 0.10); CRM→ERP identity 99.7% with addresses. J3: readers notice "
            "submitted conflicts (9/9), but on S22 the decision block approves anyway.",
            "next": [
                "Your grading pass on the J3 answers (grading list part D)",
                "J4: Jev on Utopia's governance duplicate pairs, against gpt-4o",
                "End to end: agent retrieval, then the hybrid engine",
            ],
            "utopia": "dev @ aad5b06",
            "lab_commit": "ef9513b",
            "seed": 20260923,
            "notes": "{run}/notes.md",
            "docs": [
                "{run}/plan.md",
                "{run}/j3/notes.md",
                "{run}/j2/calibration.md",
                "docs/jev-typesafe-assessment-2026-10-02.md",
            ],
        },
        "default_first_run": [None, "Not read yet."],
        "provisional": provisional,
        "provisional_repeats": repeats,
        "findings": [
            {
                "id": "j1",
                "category": "owm",
                "title": "Jev judging and code composing reach the oracle's decisions (18/18)",
                "body": "On gold evidence, Jev answered the soft questions (pricing basis, whose "
                "agreement, which products), and code did dates, amounts, bands and composition. "
                "All 18 decisions pass, raw and confidence-gated, including S13, S15 and S18, "
                "which split the readers. 20 calls, median 184 ms, $0.0004. The one uncertain "
                "judgment was S13's genuinely ambiguous pair.",
                "evidence": ["notes.md", "j1/scores.json", "j1/control.py"],
            },
            {
                "id": "j2",
                "category": "foundation",
                "title": "Jev is calibrated on our labels, near-perfect on identity with addresses",
                "body": "1,289 labelled questions, all with ECE ≤ 0.10. CRM→ERP identity with "
                "addresses: 99.7% accurate, with 95% past the gate at 100%. Names only: 87.4%, "
                "with 74% past the gate at 98.9%. It leans to 'different' and made 4 false merges "
                "in 408. $0.024.",
                "evidence": ["j2/calibration.md", "j2/judgments.jsonl"],
            },
            {
                "id": "j3",
                "category": "agent",
                "title": "Agents notice a conflicting record, but can still decide on it",
                "body": "All 12 readers looked up the CRM row, and all 9 facing a conflict stated "
                "it. On S22 (8% submitted, 15% in the CRM) all three still put APPROVE in the "
                "decision block, with the 15% case hidden in the approver text. A field-by-field "
                "diff in code catches every conflict. Structured inputs should be validated "
                "before the decision, with a typed input_conflicts field.",
                "evidence": ["j3/notes.md", "j3/scores.json", "j3/hybrid_check.json"],
            },
        ],
    }
    OUT.write_text(json.dumps(ann, ensure_ascii=False, indent=1) + "\n")
    print(f"{OUT.relative_to(LAB)}: {len(scores)} answers")


if __name__ == "__main__":
    main()
