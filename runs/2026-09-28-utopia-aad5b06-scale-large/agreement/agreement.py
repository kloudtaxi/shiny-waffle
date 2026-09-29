"""The S03 agreement check: give the scale base graph the one agreement fact the small graph had,
then score the S03 re-runs.

    python3 runs/2026-09-28-utopia-aad5b06-scale-large/agreement/agreement.py plan
    python3 runs/2026-09-28-utopia-aad5b06-scale-large/agreement/agreement.py push --apply
    python3 runs/2026-09-28-utopia-aad5b06-scale-large/agreement/agreement.py verify
    python3 runs/2026-09-28-utopia-aad5b06-scale-large/agreement/agreement.py score

At scale the curated graph + procedure + request record missed S03 in 2 of 3 runs, answering
REQUEST_EVIDENCE instead of REVIEW_REQUIRED. The scale graph holds the "Master Supply
Agreement" as a bare name. The small graph had exactly one fact on it, extracted from
acme_master_supply_agreement.md §1 (byte-identical in both corpora): "Master Supply Agreement
is effective", 2025-04-01 .. 2028-03-31. This pushes that fact and nothing else (base KB only,
where S03 runs), through the scale curation's Statements source, so the one variable that
changes is whether the agreement is established as active.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "curation"))
import curate  # noqa: E402

sys.path.insert(0, str(curate.LAB / "runs" / "2026-09-28-utopia-aad5b06" / "procedure"))
import score as scorer  # noqa: E402

KB = curate.KBS["base"]
AGREEMENT = "Master Supply Agreement"
PUSH: dict[str, Any] = {
    "external_id": "northstar-curation-agreement-term",
    "doc_time": "2025-03-20T00:00:00Z",  # acme_master_supply_agreement.md created
    "e": [[AGREEMENT, "agreement", True]],
    "s": [
        curate.st(
            AGREEMENT,
            "is effective",
            None,
            "from April 1, 2025 to March 31, 2028",
            "2025-04-01",
            "2028-03-31",
        )
    ],
    "n": [],
}


def agreement_facts() -> list[list[str]]:
    return curate.sql(
        "select e.id, coalesce(f.phrase, ''), coalesce(f.object_value->>'value', ''), "
        "coalesce(f.valid_from::date::text, ''), coalesce(f.valid_to::date::text, '') "
        "from entities e left join facts f on f.subject_id = e.id and f.invalidated_at is null "
        f"and f.layer = 'open' where e.kb_id = '{KB}' and e.merged_into is null "
        f"and e.canonical_name = '{AGREEMENT}' order by 1, 2"
    )


def cmd_plan() -> None:
    ids = {r[0] for r in agreement_facts()}
    print(f"base: {len(ids)} live entity named {AGREEMENT!r}")
    print(f"base: push {PUSH['external_id']}: {json.dumps(PUSH['s'], ensure_ascii=False)}")


def cmd_push(apply: bool) -> None:
    cmd_plan()
    if apply:
        print("   ", curate.push(KB, PUSH))


def cmd_verify() -> None:
    for row in agreement_facts():
        print("   ", " | ".join(row))


def cmd_score() -> None:
    exp = scorer.expected()
    report: dict[str, Any] = {}
    for n in (1, 2, 3):
        run = HERE / "arm-b" / f"r{n}" / "B2"
        got = scorer.decision(scorer.result_text(run / "S03.jsonl"))
        row = {"expected": exp["S03"], "got": got, **scorer.score("S03", got, exp["S03"])}
        report[str(run.relative_to(curate.LAB))] = {"S03": row}
        print(f"r{n}: {row['grade']} ({row['note']})")
    (HERE / "scores.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("cmd", choices=["plan", "push", "verify", "score"])
    p.add_argument("--apply", action="store_true", help="write to Utopia (default: print)")
    a = p.parse_args()
    {"plan": cmd_plan, "verify": cmd_verify, "score": cmd_score}.get(
        a.cmd, lambda: cmd_push(a.apply)
    )()


if __name__ == "__main__":
    main()
