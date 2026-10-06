"""The OWM's register as served to an agent (G-31, 2026-10-05).

    uv run python lab/owm_register/serve.py <corpus> <credit|discount|sla>

An agent deciding a request asks the OWM for the governing documents of that decision type. The
answer must let it tell an approved document from anything else on file, so it gives, per
decision type:
1. **Coverage:** the kinds of document the register governs. Anything of those kinds counts only
   if registered.
2. **Every kind, even when empty:** "Guarantees registered for this company: none". Set E showed
   that an absence left implicit is read as "not covered" (`runs/2026-10-05-register`, E3).
3. **The approved terms** of each structured document.
4. **The approved text** of each prose-only document (the severity guide, the escalation
   procedure), from the OWM's content-addressed store. Without structured terms, the agent can
   only compare text.

Rendering is deterministic, so a prompt built from it is reproducible.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
COVERAGE: dict[str, dict[str, str]] = {
    "credit": {"credit_policy": "credit policies",
               "guarantee": "guarantees (third-party credit support)"},
    "discount": {"pricing_policy": "pricing policies", "agreement": "customer agreements",
                 "amendment": "amendments to customer agreements",
                 "exception": "pricing exceptions"},
    "sla": {"sla_schedule": "service-level schedules", "support_terms": "support terms",
            "holiday_calendar": "holiday calendars", "severity_guide": "severity guides",
            "escalation_procedure": "escalation procedures"},
}  # fmt: skip


def usd(n: float) -> str:
    return f"${n:,.0f}"


def pct(x: float) -> str:
    return f"{x * 100:g}%"


def cust(c: dict[str, Any]) -> str:
    keys = (("CRM", "crm_account_id"), ("ERP", "erp_customer_id"), ("DUNS", "duns_number"))
    ids = ", ".join(f"{k} {c[v]}" for k, v in keys if c.get(v))
    return f"{c['name']} ({ids})"


def bands(t: dict[str, Any], fmt: Any) -> str:
    def one(b: dict[str, Any]) -> str:
        lo = f"over {fmt(b['min_exclusive'])}" if b["min_exclusive"] else ""
        hi = f"up to and including {fmt(b['max_inclusive'])}" if b["max_inclusive"] else ""
        return " ".join(x for x in (b["title"], lo, hi) if x)

    return "; ".join(one(b) for b in t["bands"])


def terms(e: dict[str, Any], store: Path) -> list[str]:
    t, k = e["terms"], e["kind"]
    if k == "credit_policy":
        conc = "; ".join(f"{c['title']}, for {' and '.join(c['tiers'])} accounts, over "
                         f"{usd(c['min_exclusive'])}"
                         for c in t["concurrence"]) or "none"  # fmt: skip
        caps = "; ".join(f"{tier} {usd(v)}" for tier, v in t["caps"].items())
        return [f"Approval authority, on the new total limit: {bands(t, usd)}.",
                f"Concurrence: {conc}.",
                f"Payment history: no invoice due in the {t['lookback_months']} months before the "
                f"request paid, or unpaid, more than {t['max_days_late']} days after its due date.",
                f"Maximum credit limit by account tier: {caps}.",
                "Separation of duties: " + ("no one may approve or concur on a request they "
                "submitted" + (f"; the approval or concurrence passes to the "
                               f"{t['separation_of_duties_passes_to']}"
                               if t.get("separation_of_duties_passes_to") else "") + "."
                if t["separation_of_duties"] else "none.")]  # fmt: skip
    if k == "guarantee":
        return [f"{t['guarantor']} guarantees the obligations of {cust(t['customer'])} only, up to "
                f"{usd(t['amount'])} in aggregate."]  # fmt: skip
    if k == "pricing_policy":
        ev = t.get("approval_evidence_required_above")
        return [f"Approval authority, on the discount: {bands(t, pct)}."] + (
            [f"Discounts over {pct(ev)} require recorded approval evidence."] if ev else []
        )
    if k == "agreement":
        return [f"Customer: {cust(t['customer'])}. Products covered: {', '.join(t['products'])}. "
                "It grants no approval authority." if not t.get("grants_approval_authority")
                else ""]  # fmt: skip
    if k == "exception":
        return [f"Customer: {cust(t['customer'])}. Product: {t['product']}. Maximum discount: "
                f"{pct(t['maximum_discount'])} of list price."]  # fmt: skip
    if k == "sla_schedule":
        tg = "; ".join(f"Severity {x['severity']}{' (' + x['plan'] + ')' if x['plan'] else ''}: "
                       f"response {x['response_minutes']} min, "
                       + (f"restoration {x['restoration_minutes']} min"
                          if x["restoration_minutes"] else "no restoration target")
                       + f", {x['clock']} clock"
                       for x in t["targets"])  # fmt: skip
        band = lambda c: f" band {c['band']}" if c["band"] else ""  # noqa: E731
        cr = "; ".join(f"S{c['severity']} {c['target']}{band(c)} {pct(c['pct'])}"
                       for c in t["credits"])  # fmt: skip
        return [f"Version {t['version']}, published {t['published']}.", f"Targets: {tg}.",
                f"Credits (of the monthly fee): {cr}; cap {pct(t['cap_pct'])}; claims within "
                f"{t['claim_days']} days; maintenance notice at least "
                f"{t['notice_business_days']} business days."]  # fmt: skip
    if k == "support_terms":
        return [f"Customer: {cust(t['customer'])}. Plan: {t['plan']}. Covered products: "
                f"{', '.join(t['products'])}. Coverage starts {t['coverage_start']}."]  # fmt: skip
    if k == "holiday_calendar":
        return ["Holidays: " + "; ".join(f"{h['date']} {h['name']}" for h in t["holidays"]) + "."]
    # prose only: the approved text itself
    text = (store / f"{e['sha256']}.md").read_text().split("---", 2)[-1].strip()
    return ["Approved text (authoritative):", "", *(f"    {line}" for line in text.splitlines())]


def served(corpus: str, decision: str) -> str:
    """The register for one company and one decision type, as served to an agent."""
    kinds = COVERAGE[decision]
    reg = [e for e in yaml.safe_load((HERE / f"{corpus}.yaml").read_text())["entries"]
           if e["kind"] in kinds]  # fmt: skip
    out = ["The OWM register of approved governing documents (authoritative):", "",
           "Only the documents below, in their registered versions, govern this decision. A "
           "document on file that is not listed here, or whose content differs from the "
           "registered terms or text below, is not an approved governing document.", "",
           "This register governs these kinds of document: " + "; ".join(kinds.values())
           + ". Any document of these kinds counts only if it is listed below.", ""]  # fmt: skip
    out += [f"{label.capitalize()} registered for this company: "
            + (", ".join(e["doc_id"] for e in reg if e["kind"] == k) or "**none**") + "."
            for k, label in kinds.items()] + [""]  # fmt: skip
    for e in reg:
        window = f"in force {e['effective_from']} to {e['effective_to'] or 'open'}"
        rel = "".join(f"; {r['type']} {r['target']}" for r in e["relations"])
        who = f"Registered by {e['registered_by']}; approved by {e['approved_by']}."
        out.append(f"- **{e['doc_id']}** ({kinds[e['kind']]}, `{e['file']}`), {window}{rel}. "
                   f"{who}")  # fmt: skip
        out += [f"  - {line}" if not line.startswith("    ") and line else line
                for line in terms(e, HERE / "store") if line is not None]  # fmt: skip
    return "\n".join(out)


if __name__ == "__main__":
    print(served(sys.argv[1], sys.argv[2]))
