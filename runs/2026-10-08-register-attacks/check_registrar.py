"""The registrar's self-check, before the freeze (`plan.md`, step 2). Written by the lab, so it
proves only that each rule does what it says; the blind attack set is the test.

    uv run python runs/2026-10-08-register-attacks/check_registrar.py

Legitimate changes must be admitted; each bad change must be refused by the rule it breaks.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(LAB / "lab/owm_register"))
import registrar as reg_  # noqa: E402
from kernel import entry_in_force, in_window  # noqa: E402

DOCS = LAB / "dataset/evidence/documents"


def text_2027_credit() -> str:
    t = (DOCS / "credit_policy_2026.md").read_text()
    return (t.replace("CREDIT-POLICY-2026", "CREDIT-POLICY-2027")
             .replace("Credit Policy 2026", "Credit Policy 2027")
             .replace("calendar 2026", "calendar 2027")
             .replace("2026-01-01", "2027-01-01").replace("2026-12-31", "2027-12-31")
             .replace("'2025-12-15'", "'2026-09-01'"))  # fmt: skip


def credit_2027(**over: Any) -> dict[str, Any]:
    base = reg_.State.bootstrap("base")
    terms = dict(next(e for e in base.entries if e["doc_id"] == "CREDIT-POLICY-2026")["terms"])
    ch = {"action": "register", "doc_id": "CREDIT-POLICY-2027", "kind": "credit_policy",
          "file": "credit_policy_2027.md", "effective_from": "2027-01-01",
          "effective_to": "2027-12-31", "terms": terms,
          "relations": [{"type": "supersedes", "target": "CREDIT-POLICY-2026"}],
          "submit_by": "EMP-401", "approve_by": "EMP-402", "base_version": 17}  # fmt: skip
    return ch | over


def exception_edge(**over: Any) -> tuple[dict[str, Any], str]:
    text = (DOCS / "acme_pricing_exception.md").read_text()
    text = (text.replace("EXC-ACME-NS500-15", "EXC-ACME-EDGE-12")
                .replace("NS-500 Industrial Controller (NS-500)",
                         "NS-Edge Monitoring Package (NS-EDGE)")
                .replace("Acme NS-500 Strategic", "Acme NS-EDGE Strategic")
                .replace("15% of list price", "12% of list price")
                .replace("2025-04-01", "2026-09-10")
                .replace("Supersedes EXC-ACME-NS500-10 for requests dated on or after 2026-09-10.",
                         "First exception for this product."))  # fmt: skip
    base = reg_.State.bootstrap("base")
    cust = next(e for e in base.entries if e["doc_id"] == "EXC-ACME-NS500-15")["terms"]["customer"]
    ch = {"action": "register", "doc_id": "EXC-ACME-EDGE-12", "kind": "exception",
          "file": "acme_pricing_exception_edge.md", "effective_from": "2026-09-10",
          "effective_to": "2028-03-31",
          "terms": {"customer": dict(cust), "product": "NS-EDGE", "maximum_discount": 0.12,
                    "grants_approval_authority": False},
          "relations": [{"type": "under", "target": "ACME-MFG-2025"}],
          "submit_by": "EMP-200", "approve_by": "EMP-300", "base_version": 17}  # fmt: skip
    return ch | over, text


def run(name: str, ch: dict[str, Any], text: str | None, acting: set[str], want: str,
        state: reg_.State | None = None) -> reg_.State | None:  # fmt: skip
    state = state or reg_.State.bootstrap("base")
    try:
        new = reg_.apply(state, ch, text, acting)
        got = "admitted"
    except reg_.RefusedError as e:
        new, got = None, e.rule
        print(f"   ({e})")
    ok = got == want
    print(f"{'ok ' if ok else 'BAD'} {name}: {got} (want {want})")
    RESULTS.append(ok)
    return new


RESULTS: list[bool] = []


def main() -> None:
    t27 = text_2027_credit()
    both = {"EMP-401", "EMP-402"}
    s = run("L1 Finance registers the 2027 credit policy", credit_2027(), t27, both, "admitted")
    if s is not None:
        reg = s.register()
        flags: list[str] = []
        e = entry_in_force([x for x in reg.entries if x["kind"] == "credit_policy"],
                           date(2027, 3, 1), flags)  # fmt: skip
        RESULTS.append(e is not None and e["doc_id"] == "CREDIT-POLICY-2027")
        print(f"{'ok ' if RESULTS[-1] else 'BAD'} L1 in force on 2027-03-01: {e and e['doc_id']}")
    ch, tx = exception_edge()
    run("L2 Sales registers a second Acme exception (another product)", ch, tx,
        {"EMP-200", "EMP-300"}, "admitted")  # fmt: skip
    rev = {"action": "revoke", "target": "SUP-BRL-2025", "revoked_on": "2026-09-15",
           "submit_by": "EMP-601", "approve_by": "EMP-602", "base_version": 17}  # fmt: skip
    s = run("L3 Support revokes BlueRiver's support terms", rev, None, {"EMP-601", "EMP-602"},
            "admitted")  # fmt: skip
    if s is not None:
        e2 = next(x for x in s.entries if x["doc_id"] == "SUP-BRL-2025")
        RESULTS.append(in_window(e2, date(2026, 9, 14)) and not in_window(e2, date(2026, 9, 15)))
        print(f"{'ok ' if RESULTS[-1] else 'BAD'} L3 in force 09-14, not on 09-15")

    run("B1 an agent submits", credit_2027(submit_by="AGENT-7"), t27, {"AGENT-7", "EMP-402"},
        "RR-2")  # fmt: skip
    run("B2 self-approval", credit_2027(approve_by="EMP-401"), t27, {"EMP-401"}, "RR-4")
    run("B3 approval by someone the actor doesn't control", credit_2027(), t27, {"EMP-401"},
        "RR-1")  # fmt: skip
    run("B4 Sales submits a credit policy", credit_2027(submit_by="EMP-200"), t27,
        {"EMP-200", "EMP-402"}, "RR-3")  # fmt: skip
    run("B5 a Finance analyst approves", credit_2027(approve_by="EMP-507"), t27,
        {"EMP-401", "EMP-507"}, "RR-4")  # fmt: skip
    back = t27.replace("2027-01-01", "2026-08-01")
    run("B6 backdated", credit_2027(effective_from="2026-08-01",
                                    relations=[]), back, both, "RR-9")  # fmt: skip
    swapped = t27.replace("Accounts Receivable Specialists may approve credit limits up to and "
                          "including $100,000", "Accounts Receivable Specialists may approve "
                          "credit limits up to and including $500,000")  # fmt: skip
    run("B7 text raises a band the terms don't", credit_2027(), swapped, both, "RR-6")
    run("B8 stale base", credit_2027(base_version=16), t27, both, "RR-13")
    run("B9 overlap without superseding", credit_2027(relations=[],
        effective_from="2026-12-31"), t27.replace("2027-01-01", "2026-12-31"), both,
        "RR-10")  # fmt: skip
    run("B10 supersedes a document of another kind", credit_2027(relations=[
        {"type": "supersedes", "target": "PRICING-POLICY-2026"}]), t27, both, "RR-11")  # fmt: skip
    ch, tx = exception_edge()
    other = dict(ch["terms"]["customer"], erp_customer_id="C-2001")
    bad11 = exception_edge(terms=dict(ch["terms"], customer=other))[0]
    run("B11 exception with another customer's ERP id", bad11, tx, {"EMP-200", "EMP-300"}, "RR-8")
    run("B12 terms window not in the text", credit_2027(effective_to="2028-12-31"), t27, both,
        "RR-7")  # fmt: skip
    run("B13 company policy naming a customer", credit_2027(terms=dict(
        credit_2027()["terms"], customer=ch["terms"]["customer"])), t27, both, "RR-6")  # fmt: skip
    run("B14 revocation backdated", rev | {"revoked_on": "2026-08-15"}, None,
        {"EMP-601", "EMP-602"}, "RR-9")  # fmt: skip
    run("B15 separation of duties dropped from the terms", credit_2027(terms=dict(
        credit_2027()["terms"], separation_of_duties=False)), t27, both, "RR-6")  # fmt: skip
    print(f"\n{sum(RESULTS)}/{len(RESULTS)} as expected")
    sys.exit(0 if all(RESULTS) else 1)


if __name__ == "__main__":
    main()
