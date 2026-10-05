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
           "missing-guarantee-evidence": f"{VARIANTS}/missing-guarantee-evidence"}  # fmt: skip
FINANCE = ("Priya Shah (EMP-401, Finance Manager)", "Elena Novak (EMP-402, Director of Finance)")
LEGAL = ("Legal (by function: no Legal staff in the HR export)",) * 2


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
    check(doc, [usd(b.max_inclusive) for b in cp.bands if b.max_inclusive]
          + [usd(c.min_exclusive) for c in cp.concurrence]
          + [f"{usd(v)} for {k} accounts" for k, v in cp.caps.items()]
          + [f"{months} months", f"more than {cp.max_days_late} days"])  # fmt: skip
    return entry(doc, "policy", cp.valid_from, cp.valid_to, terms, FINANCE,
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


def entry(
    doc: Doc, kind: str, start: Any, end: Any, terms: dict[str, Any], who: tuple[str, ...],
    relations: list[dict[str, str]],
) -> dict[str, Any]:  # fmt: skip
    created = str(doc.front.get("created", start))
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
    return {"register": f"credit, {corpus}", "entries": entries}


HEADER = ("# The OWM's register of approved governing credit documents for one company (corpus).\n"
          "# Built by lab/owm_register/build_register.py; see its docstring. OWM state, not "
          "evidence.\n")  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    bad = []
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
    if a.check:
        print("register: up to date" if not bad else f"register: STALE for {bad}")
        sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
