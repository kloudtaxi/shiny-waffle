"""The registrar: builds the OWM's register of approved governing credit documents, per company.

    uv run python lab/owm_register/build_register.py          # writes <corpus>.yaml here
    uv run python lab/owm_register/build_register.py --check  # rebuilds, compares, writes nothing

The register is OWM state (gap G-01, decided 2026-10-05: it lives in the OWM; documents are
registered by their owning function and approved by a second person). It is not evidence: it
never goes into `dataset/evidence/`, and an attacker who can add or replace documents can't touch
it. See `runs/2026-10-05-register/plan.md`.

This script plays a **correct registrar**:
- For each corpus (each company's documents), it registers the governing credit documents present
  there: the credit policies and the guarantees.
- It records each approved version's fingerprint (`kernel.fingerprint`), its validity window,
  explicit relations (a policy supersedes its predecessor) and **structured terms**.
- The terms come from `truth/`, as a registrar who transcribes the document correctly would enter
  them. Before registering, it **checks** that every registered amount, threshold, period and
  party appears in the document's text, and fails loudly if one doesn't.

**Who registered:**
- policies: Finance registers (Priya Shah) and Elena Novak approves;
- guarantees: Legal owns them, but the HR export has no Legal staff, so they are recorded by
  function. The lab can't show the two-person rule for Legal; no check depends on who registered.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
from kernel import Doc, Evidence, fingerprint  # noqa: E402

from northstar.model import load_truth  # noqa: E402

VARIANTS = "dataset/evidence-variants"
CORPORA = {"base": "dataset/evidence",
           "missing-contract-evidence": f"{VARIANTS}/missing-contract-evidence",
           "missing-guarantee-evidence": f"{VARIANTS}/missing-guarantee-evidence"}  # fmt: skip
STORE: dict[
    str, str
] = {}  # sha256 -> the approved text as registered (the content-addressed store)
FINANCE = ("Priya Shah (EMP-401, Finance Manager)", "Elena Novak (EMP-402, Director of Finance)")
SUPPORT = ("Hannah Lindqvist (EMP-601, Support Escalation Manager)",
           "Marcus Adeyemi (EMP-602, Director of Customer Support)")  # fmt: skip


def by_function(name: str) -> tuple[str, str]:
    return (f"{name} (by function: no {name} staff in the HR export)",) * 2


LEGAL = by_function("Legal")


def usd(n: float) -> str:
    return f"${n:,.0f}"


def check(doc: Doc, needles: list[str]) -> None:
    flat = " ".join(doc.raw.split())
    missing = [n for n in needles if n not in flat]
    if missing:
        sys.exit(f"registrar: {doc.doc_id} doesn't state {missing}; refusing to register it")


def policy_entry(truth: Any, cp: Any, doc: Doc, previous: str | None) -> dict[str, Any]:
    title = truth.role_title
    months = round(cp.lookback_days * 12 / 365)
    terms = {
        "bands": [{"title": title(b.role), "min_exclusive": b.min_exclusive,
                   "max_inclusive": b.max_inclusive} for b in cp.bands],
        "concurrence": [{"title": title(c.role), "min_exclusive": c.min_exclusive,
                         "tiers": list(c.tiers)} for c in cp.concurrence],
        "lookback_months": months,
        "max_days_late": cp.max_days_late,
        "caps": dict(cp.caps),
        "separation_of_duties": cp.separation_of_duties,
    }  # fmt: skip
    if cp.separation_of_duties:  # set F: a term must carry the whole rule, not just "yes"
        terms["separation_of_duties_passes_to"] = "requestor's manager"
    check(doc, [usd(b.max_inclusive) for b in cp.bands if b.max_inclusive]
          + [usd(c.min_exclusive) for c in cp.concurrence]
          + [f"{usd(v)} for {k} accounts" for k, v in cp.caps.items()]
          + [f"{months} months", f"more than {cp.max_days_late} days"]
          + (["passes to the requestor's manager"] if cp.separation_of_duties else []))  # fmt: skip
    return entry(doc, "credit_policy", cp.valid_from, cp.valid_to, terms, FINANCE,
                 [{"type": "supersedes", "target": previous}] if previous else [])  # fmt: skip


def guarantee_entry(truth: Any, g: Any, doc: Doc, root: Path) -> dict[str, Any]:
    cust = truth.customer(g.customer)
    erp_id = cust.source_ids["erp"]
    with (root / "structured/customers.csv").open() as f:
        row = next(r for r in csv.DictReader(f) if r["erp_customer_id"] == erp_id)
    terms = {"amount": g.amount_usd, "guarantor": g.guarantor,
             "customer": {"erp_customer_id": erp_id, "name": row["customer_name"],
                          "duns_number": row["duns_number"]}}  # fmt: skip
    check(doc, [usd(g.amount_usd), g.guarantor, row["customer_name"]])
    return entry(doc, "guarantee", g.valid_from, g.valid_to, terms, LEGAL, [])


def ids_of(truth: Any, root: Path, cust_id: str) -> dict[str, str]:
    """A customer by its registered ids: CRM account, ERP customer, DUNS (never by name)."""
    cust = truth.customer(cust_id)
    erp_id = cust.source_ids["erp"]
    with (root / "structured/customers.csv").open() as f:
        row = next(r for r in csv.DictReader(f) if r["erp_customer_id"] == erp_id)
    return {"crm_account_id": cust.source_ids.get("crm"), "erp_customer_id": erp_id,
            "name": row["customer_name"], "duns_number": row["duns_number"]}  # fmt: skip


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def pricing_policy_entry(truth: Any, p: Any, doc: Doc, previous: str | None) -> dict[str, Any]:
    terms = {"bands": [{"title": truth.role_title(b.role), "min_exclusive": b.min_exclusive,
                        "max_inclusive": b.max_inclusive} for b in p.bands],
             "approval_evidence_required_above": p.approval_evidence_required_above}  # fmt: skip
    check(doc, [pct(b.max_inclusive) for b in p.bands if b.max_inclusive])
    return entry(doc, "pricing_policy", p.valid_from, p.valid_to, terms,
                 by_function("Revenue Operations"),
                 [{"type": "supersedes", "target": previous}] if previous else [])  # fmt: skip


def sku(truth: Any, pid: str) -> str:
    return str(next(x.sku for x in truth.products if x.id == pid))


def agreement_entry(truth: Any, c: Any, doc: Doc, root: Path) -> dict[str, Any]:
    terms = {"customer": ids_of(truth, root, c.customer),
             "products": [sku(truth, pid) for pid in c.covers],
             "grants_approval_authority": c.grants_approval_authority}  # fmt: skip
    check(doc, terms["products"])
    return entry(doc, "agreement", c.valid_from, c.valid_to, terms, LEGAL, [])


def exception_entry(truth: Any, x: Any, doc: Doc, root: Path, agreement: str | None
                    ) -> dict[str, Any]:  # fmt: skip
    terms = {"customer": ids_of(truth, root, x.customer), "product": sku(truth, x.product),
             "maximum_discount": x.maximum_discount}  # fmt: skip
    check(doc, [pct(x.maximum_discount), terms["product"]])
    rel = ([{"type": "supersedes", "target": x.supersedes}] if x.supersedes else []) + (
        [{"type": "under", "target": agreement}] if agreement else []
    )
    return entry(doc, "exception", x.valid_from, x.valid_to, terms, by_function("Deal Desk"), rel)


def sla_schedule_entry(sch: Any, doc: Doc, previous: str | None) -> dict[str, Any]:
    terms = {"version": sch.version, "published": str(sch.published),
             "targets": [t.model_dump() for t in sch.targets],
             "credits": [c.model_dump() for c in sch.credits], "cap_pct": sch.cap_pct,
             "claim_days": sch.claim_days,
             "notice_business_days": sch.notice_business_days}  # fmt: skip
    check(doc, [pct(sch.cap_pct), f"{sch.notice_business_days} business days"])
    return entry(doc, "sla_schedule", sch.valid_from, sch.valid_to, terms, SUPPORT,
                 [{"type": "supersedes", "target": previous}] if previous else [])  # fmt: skip


def support_terms_entry(truth: Any, a: Any, doc: Doc, root: Path, under: str | None
                        ) -> dict[str, Any]:  # fmt: skip
    terms = {"customer": ids_of(truth, root, a.customer), "plan": a.plan,
             "products": [sku(truth, pid) for pid in a.products],
             "coverage_start": str(a.coverage_start)}  # fmt: skip
    check(doc, [a.plan, str(a.coverage_start)] + terms["products"])
    return entry(doc, "support_terms", a.coverage_start, None, terms, LEGAL,
                 [{"type": "under", "target": under}] if under else [])  # fmt: skip


def holiday_entry(truth: Any, doc: Doc) -> dict[str, Any]:
    terms = {"holidays": [{"date": str(h.date), "name": h.name} for h in truth.holidays]}
    check(doc, [str(h.date) for h in truth.holidays])
    start = doc.front.get("effective_from") or min(h.date for h in truth.holidays)
    return entry(doc, "holiday_calendar", start, doc.front.get("effective_to"), terms,
                 by_function("People Operations"), [])  # fmt: skip


def prose_entry(doc: Doc, kind: str) -> dict[str, Any]:
    """A governing document with no structured terms yet: its approved text is registered."""
    return entry(doc, kind, doc.front.get("effective_from") or doc.front.get("created"),
                 doc.front.get("effective_to"), {}, SUPPORT, [])  # fmt: skip


def entry(
    doc: Doc, kind: str, start: Any, end: Any, terms: dict[str, Any], who: tuple[str, ...],
    relations: list[dict[str, str]],
) -> dict[str, Any]:  # fmt: skip
    created = str(doc.front.get("created", start))
    STORE[fingerprint(doc.raw)] = doc.raw
    return {"doc_id": doc.doc_id, "kind": kind, "version": 1, "file": doc.filename,
            "sha256": fingerprint(doc.raw), "effective_from": str(start),
            "effective_to": str(end) if end else None, "relations": relations, "terms": terms,
            "registered_by": who[0], "approved_by": who[1], "registered_on": created,
            "approved_on": created}  # fmt: skip


def build(corpus: str) -> dict[str, Any]:
    truth = load_truth(LAB / "truth")
    root = LAB / CORPORA[corpus]
    docs = Evidence(root).docs()
    entries, previous = [], None
    for cp in sorted(truth.credit_policies, key=lambda p: p.valid_from):
        doc = next((d for d in docs if d.title == cp.title), None)
        if doc is not None:
            entries.append(policy_entry(truth, cp, doc, previous))
            previous = doc.doc_id
    for g in truth.guarantees:
        doc = next((d for d in docs if d.doc_id == g.id), None)
        if doc is not None:  # a company registers the instruments it has
            entries.append(guarantee_entry(truth, g, doc, root))
    # discount (G-30)
    previous = None
    for p in sorted(truth.policies, key=lambda p: p.valid_from):
        doc = next((d for d in docs if d.title == p.title), None)
        if doc is not None:
            entries.append(pricing_policy_entry(truth, p, doc, previous))
            previous = doc.doc_id
    agreement_ids: dict[str, str] = {}
    for c in truth.contracts:
        doc = next((d for d in docs if d.doc_id in [c.id, *c.aliases]), None)
        if doc is not None:
            entries.append(agreement_entry(truth, c, doc, root))
            agreement_ids[c.id] = doc.doc_id
    for x in truth.exceptions:
        doc = next((d for d in docs if d.doc_id == x.id), None)
        if doc is not None:
            entries.append(exception_entry(truth, x, doc, root, agreement_ids.get(x.contract)))
    # SLA (G-30)
    previous = None
    for sch in sorted(truth.sla_schedules, key=lambda x: x.valid_from):
        doc = next((d for d in docs if d.doc_id == f"SLA-SCHEDULE-{sch.version}"), None)
        if doc is not None:
            entries.append(sla_schedule_entry(sch, doc, previous))
            previous = doc.doc_id
    for a in truth.support_agreements:
        doc = next((d for d in docs if d.doc_id == a.id), None)
        if doc is not None:
            under = next((v for k, v in agreement_ids.items() if v in a.reference), None)
            entries.append(support_terms_entry(truth, a, doc, root, under))
    for d in docs:
        if d.doc_id == "HR-HOLIDAYS-2025-26":
            entries.append(holiday_entry(truth, d))
        elif d.doc_id == "SUP-SEVERITY-GUIDE":
            entries.append(prose_entry(d, "severity_guide"))
        elif d.doc_id == "SOP-SUPPORT-007":
            entries.append(prose_entry(d, "escalation_procedure"))
    return {"register": f"governing documents, {corpus}", "entries": entries}


HEADER = ("# The OWM's register of approved governing documents for one company (corpus).\n"
          "# Built by lab/owm_register/build_register.py; see its docstring. OWM state, not "
          "evidence.\n")  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = []
    store = HERE / "store"
    for corpus in CORPORA:
        text = HEADER + yaml.safe_dump(
            build(corpus), sort_keys=False, allow_unicode=True, width=100
        )
        path = HERE / f"{corpus}.yaml"
        if a.check:
            if not path.exists() or path.read_text() != text:
                bad.append(corpus)
        else:
            path.write_text(text)
            n = len(yaml.safe_load(text)["entries"])
            print(f"{corpus}: {n} entries -> {path.relative_to(LAB)}")
    for sha, raw in sorted(STORE.items()):  # the approved texts, keyed by fingerprint
        path = store / f"{sha}.md"
        if a.check:
            if not path.exists() or path.read_text() != raw:
                bad.append(f"store/{sha[:12]}")
        else:
            store.mkdir(exist_ok=True)
            path.write_text(raw)
    if not a.check:
        print(f"store: {len(STORE)} approved texts -> {store.relative_to(LAB)}")
    if a.check:
        print("register: up to date" if not bad else f"register: STALE for {bad}")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
