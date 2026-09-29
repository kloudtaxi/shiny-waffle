"""Held-out decisions S09–S14: build the reader's questions, and score the answers.

    uv run python runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py questions
    uv run python runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py score DIR ...

The scenarios live in `truth/scenarios/09-*.yaml` … `14-*.yaml`. They were written and proven
by the oracle after the OWM procedure (`owm/procedures/discount-approval.md`, sha256 6e72951c…)
was frozen, and committed before any reader saw them. Each varies DR-9001 into a new pending
request (DR-9101…DR-9106) and adds no evidence, so both scale KBs stay as ingested.

`questions` writes `questions.tsv` in the request arm's format: the scenario's verbatim question,
then "The request, as recorded in Northstar CRM:" and the request row as JSON. The row is built
from the truth by the oracle's own `resolve_request`, with the CRM generator's conventions:
`Contract pricing per <agreement title>` or `Competitive`, the account's CRM id, the product
SKU, the employee's e-mail, status `Pending Approval`.

`score` applies `../../2026-09-28-utopia-aad5b06/procedure/score.py`'s fixed rule to S09–S14
and writes `scores-<name>.json` next to this file.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(LAB / "runs" / "2026-09-28-utopia-aad5b06" / "procedure"))
import score as scorer  # noqa: E402

from northstar.model import load_truth  # noqa: E402
from northstar.oracle import resolve_request  # noqa: E402

HELD_OUT = ("S09", "S10", "S11", "S12", "S13", "S14")
KB = {"base": "01a0ea56-61e7-79e3-99d1-e82b5d6af79a"}  # the scale base KB (../kbs.jsonl)


def record(sid: str) -> dict[str, str]:
    truth = load_truth(LAB / "truth")
    scenario = next(s for s in truth.scenarios if s.id == sid)
    req = resolve_request(truth, scenario)
    cust = truth.customer(req.customer)
    who = truth.employee(req.requestor)
    product = next(p for p in truth.products if p.id == req.product)
    justification = (
        f"Contract pricing per {truth.contract(req.basis_ref).title}"
        if req.basis == "contract_exception" and req.basis_ref
        else "Competitive"
    )
    return {
        "request_id": req.id,
        "account_id": cust.source_ids["crm"],
        "product_sku": product.sku,
        "requested_discount_pct": f"{req.requested_discount * 100:.1f}",
        "list_value_usd": str(req.list_value_usd),
        "discount_value_usd": str(req.discount_value_usd),
        "net_value_usd": str(req.net_value_usd),
        "requested_by": f"{who.name.lower().replace(' ', '.')}@{truth.organization.email_domain}",
        "request_date": req.request_date.isoformat(),
        "justification": justification,
        "status": "Pending Approval",
    }


def cmd_questions() -> None:
    truth = load_truth(LAB / "truth")
    rows = ["id\tkb\tquestion"]
    for sid in HELD_OUT:
        s = next(x for x in truth.scenarios if x.id == sid)
        text = (
            f"{s.question} The request, as recorded in Northstar CRM: "
            f"{json.dumps(record(sid), ensure_ascii=False)}"
        )
        rows.append(f"{sid}\t{KB[s.corpus]}\t{text}")
    (HERE / "questions.tsv").write_text("\n".join(rows) + "\n")
    print("\n".join(rows))


def cmd_score(dirs: list[str], name: str) -> None:
    exp = scorer.expected()
    report: dict[str, Any] = {}
    for d in dirs:
        run = Path(d).resolve()
        rows = {}
        for sid in HELD_OUT:
            got = scorer.decision(scorer.result_text(run / f"{sid}.jsonl"))
            rows[sid] = {"expected": exp[sid], "got": got, **scorer.score(sid, got, exp[sid])}
        report[str(run.relative_to(LAB))] = rows
        print(
            f"{run.relative_to(LAB)}: "
            + " ".join(f"{s}:{r['grade'][0].upper()}" for s, r in rows.items())
        )
        for sid, r in rows.items():
            if r["grade"] != "pass":
                print(f"    {sid} {r['grade']}: {r['note']}")
    (HERE / f"scores-{name}.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False) + "\n"
    )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("questions")
    sp = sub.add_parser("score")
    sp.add_argument("--name", required=True, help="suffix for scores-<name>.json")
    sp.add_argument("dirs", nargs="+")
    a = p.parse_args()
    if a.cmd == "questions":
        cmd_questions()
    else:
        cmd_score(a.dirs, a.name)


if __name__ == "__main__":
    main()
