"""The discount-approval spec on the decision kernel (doc 03 §11).

Moved verbatim from `runs/2026-10-03-adversarial/hybrid_v3.py` for experiment 5, apart from what
became kernel parameters. Its parts:
- its questions (J1's plan);
- how a discount's eligibility follows from agreements and pricing exceptions;
- its outcome table;
- its record.

`decide` returns the same object v3 returned.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from kernel import (
    Doc,
    Engine,
    Evidence,
    Guards,
    KindRule,
    authority_from_evidence,
    gate,
    judge,
    referenced_agreement,
    row,
    screen,
    window,
)

Q_BASIS = {
    "type": "choice",
    "instructions": "What pricing basis does the request in `request` rely on?",
    "criteria": {
        "contract_terms": "A customer contract, agreement or negotiated pricing exception",
        "standard_pricing": "Standard pricing, or competitive or commercial reasons; no contract",
        "unclear": "The request does not say what it relies on",
    },
}
Q_PARTY = {
    "type": "choice",
    "instructions": (
        "Is the customer in `request_customer` the same legal entity as the customer named in "
        "`document`?"
    ),
    "criteria": {
        "same_legal_entity": (
            "Yes: the same company, possibly under a trading name (doing business as) or a "
            "shortened or differently spelled name"
        ),
        "different_entity": "No: a different company, even if the names look alike",
        "unclear": "The information given cannot tell",
    },
}
Q_PRODUCT = {
    "type": "noul",
    "instructions": "The document in `document` covers or applies to the product in `product`.",
}


def max_discount(doc: Doc) -> float | None:
    m = re.search(r"Maximum eligible discount\s*\|\s*(\d+)%", doc.body) or re.search(
        r"up to \**(\d+)%", doc.body
    )
    return int(m[1]) / 100 if m else None


def party_text(doc: Doc) -> str:
    """For an agreement, its party clause. For an exception, its customer row, or its whole text
    when it has no customer row."""
    for para in re.split(r"\n\s*\n", doc.body):
        if "entered into between" in para:
            return " ".join(para.split())
    return row(doc, "Customer") or " ".join(doc.body.split())


def product_text(doc: Doc) -> str:
    """For an agreement, its products section. For an exception, its product row, else the
    paragraphs that name a product."""
    m = re.search(r"## \d+\. Products\n(.*?)(?=\n## )", doc.body, re.S)
    if m:
        return m[1].strip()
    if r := row(doc, "Product"):
        return r
    keep = [p for p in re.split(r"\n\s*\n", doc.body) if re.search(r"[Pp]roduct|NS-", p)]
    return "\n\n".join(keep) or doc.body


GUARDS = Guards(
    rules=(
        KindRule("policy", id_prefixes=("PRICING-POLICY",), title_words=("Pricing Policy",)),
        KindRule("amendment", title_words=("Amendment",)),
        KindRule("agreement", title_words=("Agreement",)),
        KindRule("exception", ("EXC-",), ("Exception",), ("Deal Desk",)),
    ),
    owners={
        "policy": {"Revenue Operations"},
        "agreement": {"Legal"},
        "amendment": {"Legal"},
        "exception": {"Deal Desk"},
    },
    value_of=max_discount,
    product_of=product_text,
)


def decide(
    eng: Engine, ev: Evidence, as_of: date, record: dict[str, str], sid: str
) -> dict[str, Any]:
    """One discount decision on one corpus, with authority from evidence and guards G1–G5."""
    docs = ev.docs()
    staff, products = ev.table("employees"), ev.table("products")
    account = next(a for a in ev.table("crm_accounts")
                   if a["account_id"] == record["account_id"])  # fmt: skip
    product = next(p for p in products if p["sku"] == record["product_sku"])
    customer = {k: account[k] for k in ("account_name", "billing_street", "billing_city",
                                        "billing_state")}  # fmt: skip
    product_name = f"{product['product_name']} ({product['sku']})"
    used: list[dict[str, Any]] = []
    flags: list[str] = []
    s = screen(eng, docs, GUARDS, staff, products, used, flags)
    good = s.good

    basis = judge(eng, {"request": {"justification": record["justification"]}}, "basis", Q_BASIS)
    used.append(basis)
    eligibility: dict[str, Any] = {"status": "standard", "maximum_discount": None, "basis": None}
    relied: list[Doc] = []

    if basis["choice"] != "standard_pricing":
        agreements: list[dict[str, Any]] = []
        for d in good["agreement"]:
            agreements.append({"id": d.doc_id, "window": window(d), "doc": d,
                "party": judge(eng, {"request_customer": customer, "document": party_text(d)},
                               "party", Q_PARTY),
                "covers": judge(eng, {"product": product_name, "document": product_text(d)},
                                "covers_product", Q_PRODUCT)})  # fmt: skip
        exceptions: list[dict[str, Any]] = []
        for d in good["exception"] + [d for d in good["amendment"] if max_discount(d)]:
            exceptions.append({"id": d.doc_id, "window": window(d), "max": max_discount(d),
                "agreement": referenced_agreement(d), "doc": d,
                "supersedes": set(re.findall(r"Supersedes (EXC-[A-Z0-9-]+)", d.body)),
                "party": judge(eng, {"request_customer": customer, "document": party_text(d)},
                               "party", Q_PARTY),
                "covers": judge(eng, {"product": product_name, "document": product_text(d)},
                                "covers_product", Q_PRODUCT)})  # fmt: skip
        known = {a["id"] for a in agreements}
        for x in exceptions:
            if x["agreement"] and x["agreement"] not in known:
                agreements.append({"id": x["agreement"], "window": x["window"], "doc": x["doc"],
                                   "party": x["party"], "covers": x["covers"]})  # fmt: skip
                known.add(x["agreement"])
        for a in agreements:
            used += [a["party"], a["covers"]]
        for x in exceptions:
            used += [x["party"], x["covers"]]

        def live(item: dict[str, Any]) -> bool:
            w = item["window"]
            same = item["party"]["choice"] == "same_legal_entity"
            return bool(w and w[0] <= as_of <= w[1] and same)

        contract = max((a for a in agreements if live(a)), key=lambda a: a["window"][0],
                       default=None)  # fmt: skip
        cands = [x for x in exceptions if live(x) and x["covers"]["yes"]]
        # G2: drop what a live candidate explicitly supersedes; disagreement left → route
        beaten = set().union(*(x["supersedes"] for x in cands)) if cands else set()
        cands = [x for x in cands if x["id"] not in beaten]
        exc = max(cands, key=lambda x: x["window"][0], default=None)
        if len({x["max"] for x in cands}) > 1:
            flags.append("conflict: exceptions " + ", ".join(x["id"] for x in cands))
            eligibility = {"status": "unknown", "maximum_discount": None, "basis": None}
        elif contract is None:
            eligibility = {"status": "unknown", "maximum_discount": None, "basis": None}
        elif exc is None or not contract["covers"]["yes"] or exc["max"] is None:
            eligibility = {"status": "not_covered", "maximum_discount": None, "basis": None}
            relied.append(contract["doc"])
        else:
            ok = float(record["requested_discount_pct"]) / 100 <= exc["max"]
            eligibility = {"status": "eligible" if ok else "exceeded",
                           "maximum_discount": exc["max"], "basis": exc["id"]}  # fmt: skip
            relied += [contract["doc"], exc["doc"]]
        relied += [x["doc"] for x in exceptions if live(x)]

    amount = float(record["requested_discount_pct"]) / 100
    auth = authority_from_evidence(eng, s.pols, staff, as_of, amount, record["requested_by"],
                                   used, flags)  # fmt: skip
    if auth is None:  # no single policy in force among the evidence: authority unknown
        outcome = "REQUEST_EVIDENCE"
        auth = {"policy": None, "requestor_limit": None, "requestor_authorized": None,
                "required_role": None, "approver": None}  # fmt: skip
    else:
        relied.append(auth.pop("_doc"))
        approval = "APPROVE" if auth["requestor_authorized"] else "APPROVE_WITH_AUTHORIZATION"
        by_status = {"unknown": "REQUEST_EVIDENCE", "not_covered": "REVIEW_REQUIRED",
                     "exceeded": "REJECT_OR_ESCALATE"}  # fmt: skip
        outcome = by_status.get(eligibility["status"], approval)
    uncertain, gated = gate(outcome, relied, s.inconsistent, used, flags)
    return {
        "scenario": sid,
        "outcome": outcome,
        "gated_outcome": gated,
        "uncertain": uncertain,
        "commercial_eligibility": eligibility,
        "authority": auth,
        "judgments": used,
        "flags": flags,
    }
