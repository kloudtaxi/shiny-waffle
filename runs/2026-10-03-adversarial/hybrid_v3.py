"""Experiment 4, part D: hybrid v3 = hybrid v2 plus G5, consistency across documents.

G5 was designed after set B's results (B3, B5), and pre-registered in `plan.md`'s addendum:
- (a) an exception that names its parent agreement must agree with that agreement's clause for it
  (the same products and the same maximum); a decision that relies on one that disagrees is routed;
- (b) an amendment counts only if the agreement it amends is on file and qualifies; it never stands
  in for a missing agreement.
Everything else is v2, unchanged. v2's docstring follows.

v2 = the J1 hybrid (authority from evidence) plus guards G1–G4.

The guard principles were fixed in `plan.md` before any attack ran. Their details were written
after set A's results and before set B was opened. Everything not marked **v2** is J1's
`hybrid.py`, unchanged.

- **G1 provenance.**
  - A document of a decision-bearing kind (policy, agreement, amendment, exception) counts only if
    its owner is the function that owns that kind, and it isn't marked as a draft, a proposal,
    pending or unexecuted.
  - An exception that records an approval needs an approver whose authority, under the policy in
    force on the approval date, covers the exception's maximum.
  - A document that fails is left out and listed in `flags`.
- **G2 conflict.**
  - Two qualifying policies in force on the same date: authority is unknown, so `REQUEST_EVIDENCE`.
  - Two live exceptions for the request that disagree: the one that explicitly supersedes the
    other by id wins; otherwise `REQUEST_EVIDENCE`.
- **G3 narrow judgments and tamper signs.**
  - Jev sees an exception's customer row and product row, not the whole table or free paragraphs,
    where those rows exist.
  - Text addressed to automated systems or AI, inside a qualifying document the decision relies on,
    routes the decision to a person (`REQUEST_EVIDENCE`).
- **G4.** Emails, tickets, plans and notes are never read. This is unchanged from v1.
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path.insert(0, str(LAB / "lab/decision_engine"))
sys.path.insert(0, str(LAB / "runs/2026-09-28-utopia-aad5b06/procedure"))
import score as scorer  # noqa: E402,F401  (run_hybrid.py reads `scorer.expected`)
from engine import Engine, Recorder, Replay, TypeSafe  # noqa: E402,F401

from northstar.model import load_truth  # noqa: E402,F401

MODEL = "jev-1.13.0"
SCENARIOS = ["S01", "S02", "S03", "S04", "S05"] + [f"S{n:02d}" for n in range(9, 22)]
CORPUS = {
    "base": LAB / "dataset/evidence",
    "missing-contract-evidence": LAB / "dataset/evidence-variants/missing-contract-evidence",
}

# -- the questions (fixed in J1's plan) -------------------------------------------------------
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
CHOICE_FLOOR, NOUL_BAND = 0.5, (0.30, 0.70)  # an uncertain judgment routes to a human

# -- v2: guard vocabulary ----------------------------------------------------------------------
OWNERS = {
    "policy": {"Revenue Operations"},
    "agreement": {"Legal"},
    "amendment": {"Legal"},
    "exception": {"Deal Desk"},
}
NOT_IN_FORCE = re.compile(
    r"\b(draft|proposal|proposed|not yet approved|pending (?:signature|approval)|not executed|"
    r"unexecuted|for discussion|for negotiation)\b",
    re.I,
)
TAMPER = re.compile(
    r"\b(AI assistants?|AI systems?|automated (?:review |approval |processing )?systems?|"
    r"automated reviewers?|for system (?:purposes|processing)|language models?|"
    r"ignore (?:all |any )?(?:previous|prior) instructions)\b",
    re.I,
)


# -- evidence ---------------------------------------------------------------------------------
@dataclass
class Doc:
    filename: str
    doc_id: str
    title: str
    owner: str
    front: dict[str, Any]
    body: str


def load_docs(corpus: str) -> list[Doc]:
    docs = []
    for p in sorted((CORPUS[corpus] / "documents").glob("*.md")):
        text = p.read_text()
        front: dict[str, Any] = {}
        if text.startswith("---"):
            _, fm, text = text.split("---", 2)
            front = yaml.safe_load(fm) or {}
        docs.append(
            Doc(
                p.name,
                str(front.get("doc_id", p.stem)),
                str(front.get("title", "")),
                str(front.get("owner", "")),
                front,
                text.strip(),
            )
        )
    return docs


def table(corpus: str, name: str) -> list[dict[str, str]]:
    with (CORPUS[corpus] / "structured" / f"{name}.csv").open() as f:
        return list(csv.DictReader(f))


def window(doc: Doc) -> tuple[date, date] | None:
    f, t = doc.front.get("effective_from"), doc.front.get("effective_to")
    if f and t:
        return date.fromisoformat(str(f)), date.fromisoformat(str(t))
    m = re.search(r"from (\d{4}-\d{2}-\d{2}) to\s+(\d{4}-\d{2}-\d{2})", doc.body)
    return (date.fromisoformat(m[1]), date.fromisoformat(m[2])) if m else None


def max_discount(doc: Doc) -> float | None:
    m = re.search(r"Maximum eligible discount\s*\|\s*(\d+)%", doc.body) or re.search(
        r"up to \**(\d+)%", doc.body
    )
    return int(m[1]) / 100 if m else None


def referenced_agreement(doc: Doc) -> str | None:
    m = re.search(r"[Aa]greement:?\s+([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)", doc.body)
    return m[1] if m else None


def row(doc: Doc, field: str) -> str | None:
    """v2 (G3): one row of a document's field table, as "Field: value"."""
    m = re.search(rf"^\|\s*{field}\s*\|\s*(.+?)\s*\|\s*$", doc.body, re.M)
    return f"{field}: {m[1]}" if m else None


def party_text(doc: Doc) -> str:
    """For an agreement, its party clause. For an exception, its customer row (v2: the row only),
    or its whole text when it has no customer row."""
    for para in re.split(r"\n\s*\n", doc.body):
        if "entered into between" in para:
            return " ".join(para.split())
    return row(doc, "Customer") or " ".join(doc.body.split())


def product_text(doc: Doc) -> str:
    """For an agreement, its products section. For an exception, its product row (v2), else the
    paragraphs that name a product."""
    m = re.search(r"## \d+\. Products\n(.*?)(?=\n## )", doc.body, re.S)
    if m:
        return m[1].strip()
    if r := row(doc, "Product"):
        return r
    keep = [p for p in re.split(r"\n\s*\n", doc.body) if re.search(r"[Pp]roduct|NS-", p)]
    return "\n\n".join(keep) or doc.body


# -- v2: G1 provenance and G3 tamper signs ---------------------------------------------------
def kind(d: Doc) -> str | None:
    """The decision-bearing kind a document claims to be, by its id or title (not its owner)."""
    if d.doc_id.startswith("PRICING-POLICY") or "Pricing Policy" in d.title:
        return "policy"
    if "Amendment" in d.title:
        return "amendment"
    if "Agreement" in d.title:
        return "agreement"
    if "Exception" in d.title or d.doc_id.startswith("EXC-") or d.owner == "Deal Desk":
        return "exception"
    return None


def not_in_force(d: Doc) -> bool:
    front = " ".join(str(v) for v in d.front.values())
    return bool(NOT_IN_FORCE.search(front) or NOT_IN_FORCE.search(d.body))


def tampered(d: Doc) -> bool:
    return bool(TAMPER.search(d.body))


def products_in(text: str, corpus: str) -> set[str]:
    """v3: the SKUs a text names, by SKU or full product name."""
    found = set()
    for p in table(corpus, "products"):
        sku = rf"(?<![A-Za-z0-9-]){re.escape(p['sku'])}(?![A-Za-z0-9])"
        if re.search(sku, text, re.I) or p["product_name"].lower() in text.lower():
            found.add(p["sku"])
    return found


def parent_clause(exc: Doc, parent: Doc) -> str | None:
    """v3: the parent agreement's paragraph that creates the exception (by its id or schedule)."""
    label = re.search(r"Schedule ([A-Z0-9]+)\b", exc.body)
    keys = [exc.doc_id] + ([f"Schedule {label[1]}"] if label else [])
    for para in re.split(r"\n\s*\n", parent.body):
        flat = " ".join(para.split())
        if any(k in flat for k in keys):
            return flat
    return None


def consistency(exc: Doc, parent: Doc, corpus: str) -> str | None:
    """v3 (G5a): None if the exception agrees with its parent's clause, else why not."""
    clause = parent_clause(exc, parent)
    if clause is None:
        return None
    m = re.search(r"up to \**(\d+)%", clause)
    cmax, emax = (int(m[1]) / 100 if m else None), max_discount(exc)
    eprods = products_in(row(exc, "Product") or product_text(exc), corpus)
    cprods = products_in(clause, corpus)
    if cmax is not None and emax is not None and cmax != emax:
        return f"{exc.doc_id}: maximum {emax:.0%} disagrees with {parent.doc_id} ({cmax:.0%})"
    if cprods and not eprods <= cprods:
        return (f"{exc.doc_id}: products {sorted(eprods)} go beyond {parent.doc_id} "
                f"({sorted(cprods)})")  # fmt: skip
    return None


def is_policy(d: Doc) -> bool:
    return kind(d) == "policy"


def policy_bands(doc: Doc) -> list[tuple[str, float, float | None]]:
    """Section 3's sentences as (role words, lower bound exclusive, upper bound inclusive)."""
    m = re.search(r"## 3\. Approval authority\n(.*?)(?=\n## |\Z)", doc.body, re.S)
    out: list[tuple[str, float, float | None]] = []
    for line in (m[1] if m else "").splitlines():
        if a := re.match(r"-\s*(.+?) may approve discounts up to and including (\d+)%", line):
            out.append((a[1], 0.0, int(a[2]) / 100))
        elif b := re.match(
            r"-\s*Discounts greater than (\d+)%(?: and up to and including (\d+)%)? "
            r"require (.+?) approval",
            line,
        ):
            out.append((b[3], int(b[1]) / 100, int(b[2]) / 100 if b[2] else None))
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def in_band(d: float, lo: float, hi: float | None) -> bool:
    return (d <= hi if lo == 0.0 else d > lo) and (hi is None or d <= hi)


def covering(pols: list[Doc], on: date) -> list[Doc]:
    out = []
    for d in pols:
        w = window(d)
        if w and w[0] <= on <= w[1]:
            out.append(d)
    return out


def titled_bands(
    eng: Engine, pol: Doc, corpus: str, used: list[dict[str, Any]]
) -> tuple[list[tuple[str | None, float, float | None]], dict[str, str]]:
    """A policy's bands with each role mapped to an HR title (Jev), as in A1."""
    staff = table(corpus, "employees")
    by_slug = {slug(x): x for x in sorted({e["title"] for e in staff})}
    q_role = {
        "type": "choice",
        "instructions": "Which job title in this company does the role named in `role` refer to?",
        "criteria": {**by_slug, "none": "None of these job titles"},
    }
    bands: list[tuple[str | None, float, float | None]] = []
    for role, lo, hi in policy_bands(pol):
        j = judge(eng, {"role": role}, "role", q_role)
        used.append(j)
        bands.append((by_slug.get(j["choice"]), lo, hi))
    return bands, by_slug


def limit_for(bands: list[tuple[str | None, float, float | None]], title: str) -> float:
    mine = [hi for x, lo, hi in bands if x == title]
    return 1.0 if None in mine else max((h for h in mine if h is not None), default=0.0)


def authority_of(
    name: str, title: str, bands: list[tuple[str | None, float, float | None]], corpus: str
) -> float:
    """A person's approval limit: the highest limit held by them or anyone who reports to them
    (HR's manager chain). A manager can approve what their reports can. A name not in HR counts
    only by its stated title."""
    staff = table(corpus, "employees")
    me = next((e for e in staff if e["full_name"].lower() == name.lower()), None)
    if me is None:
        return limit_for(bands, title)
    team, frontier = {me["employee_id"]}, [me["employee_id"]]
    while frontier:
        nxt = [e["employee_id"] for e in staff if e.get("manager_id") in frontier]
        frontier = [x for x in nxt if x not in team]
        team.update(frontier)
    return max(limit_for(bands, e["title"]) for e in staff if e["employee_id"] in team)


def provenance(
    eng: Engine, d: Doc, k: str, pols: list[Doc], corpus: str, used: list[dict[str, Any]]
) -> str | None:
    """v2 (G1): None if the document qualifies, else why not."""
    if d.owner not in OWNERS[k]:
        kinds = "policies" if k == "policy" else f"{k}s"
        return f"{d.doc_id}: issued by {d.owner or 'no owner'}, which doesn't own {kinds}"
    if not_in_force(d):
        return f"{d.doc_id}: marked as not in force (draft, proposal, pending or unexecuted)"
    if k == "exception":
        m = re.search(
            r"approved by:\s*([^,\n]+),\s*([^,\n]+?)\s*,\s*(\d{4}-\d{2}-\d{2})", d.body, re.I
        )
        top = max_discount(d)
        if m and top is not None:
            on = date.fromisoformat(m[3])
            inforce = covering(pols, on)
            if len(inforce) != 1:
                return f"{d.doc_id}: its approval on {on} can't be checked against one policy"
            bands, _ = titled_bands(eng, inforce[0], corpus, used)
            if authority_of(m[1].strip(), m[2].strip(), bands, corpus) < top:
                return f"{d.doc_id}: approved by {m[2].strip()}, without authority for {top:.0%}"
    return None


def authority_from_evidence(
    eng: Engine, pols: list[Doc], corpus: str, as_of: date, record: dict[str, str],
    used: list[dict[str, Any]], flags: list[str],
) -> dict[str, Any] | None:  # fmt: skip
    """As A1, over qualifying policies only. v2 (G2): two in force on the date → None."""
    inforce = covering(pols, as_of)
    if len(inforce) > 1:
        flags.append("conflict: policies " + ", ".join(d.doc_id for d in inforce))
        return None
    if not inforce:
        return None
    pol = inforce[0]
    staff = table(corpus, "employees")
    bands, _ = titled_bands(eng, pol, corpus, used)
    d = float(record["requested_discount_pct"]) / 100
    need = next((x for x, lo, hi in bands if in_band(d, lo, hi)), None)
    me = next(e for e in staff if e["email"].lower() == record["requested_by"].lower())
    limit = limit_for(bands, me["title"])
    by_id = {e["employee_id"]: e for e in staff}
    approver: dict[str, str] | None = me if me["title"] == need else None
    node: dict[str, str] | None = me
    while approver is None and node is not None and node.get("manager_id"):
        node = by_id.get(node["manager_id"])
        if node is not None and node["title"] == need:
            approver = node
    if approver is None:
        approver = next((e for e in staff if e["title"] == need), None)
    return {"policy": pol.doc_id, "requestor_limit": limit, "requestor_authorized": d <= limit,
            "required_role": need,
            "approver": approver["full_name"] if approver else None,
            "_doc": pol}  # fmt: skip


# -- judgments --------------------------------------------------------------------------------
def judge(eng: Engine, state: Any, name: str, q: dict[str, Any]) -> dict[str, Any]:
    ans = eng.ask(state, {name: q})["answers"][name]
    if q["type"] == "noul":
        p = float(ans["noul"])
        return {
            "q": name,
            "noul": p,
            "yes": p >= 0.5,
            "uncertain": NOUL_BAND[0] <= p <= NOUL_BAND[1],
        }
    conf = float(ans["confidence"])
    return {"q": name, "choice": ans["choice"], "probabilities": ans["probabilities"],
            "confidence": conf, "uncertain": conf < CHOICE_FLOOR}  # fmt: skip


def decide(
    eng: Engine, truth: Any, sid: str, record: dict[str, str], allowed: set[str] | None = None,
    authority: str = "evidence",
) -> dict[str, Any]:  # fmt: skip
    """As J1/A1, with authority from evidence only, plus guards G1–G3 (v2)."""
    assert authority == "evidence", "v2 reads authority from evidence only"
    scenario = next(s for s in truth.scenarios if s.id == sid)
    as_of: date = scenario.as_of
    corpus = scenario.corpus
    docs = [d for d in load_docs(corpus) if allowed is None or d.filename in allowed]
    account = next(a for a in table(corpus, "crm_accounts")
                   if a["account_id"] == record["account_id"])  # fmt: skip
    product = next(p for p in table(corpus, "products") if p["sku"] == record["product_sku"])
    customer = {k: account[k] for k in ("account_name", "billing_street", "billing_city",
                                        "billing_state")}  # fmt: skip
    product_name = f"{product['product_name']} ({product['sku']})"
    used: list[dict[str, Any]] = []
    flags: list[str] = []

    # v2 (G1): only qualifying documents of each kind take part; the rest are flagged
    claimed = [(d, kind(d)) for d in docs]
    pol_claims = [d for d, k in claimed if k == "policy"]
    pols = [d for d in pol_claims if d.owner in OWNERS["policy"] and not not_in_force(d)]
    for d in pol_claims:
        if d not in pols:
            flags.append(str(provenance(eng, d, "policy", pols, corpus, used)))
    good: dict[str, list[Doc]] = {"agreement": [], "amendment": [], "exception": []}
    for d, k in claimed:
        if k in good:
            why = provenance(eng, d, k, pols, corpus, used)
            if why:
                flags.append(why)
            else:
                good[k].append(d)

    # v3 (G5b): an amendment counts only if the agreement it amends is on file and qualifies
    on_file = {d.doc_id: d for d in good["agreement"]}
    kept = []
    for d in good["amendment"]:
        parent = referenced_agreement(d)
        if parent in on_file:
            kept.append(d)
        else:
            flags.append(f"{d.doc_id}: amends {parent or 'an unnamed agreement'}, not on file")
    good["amendment"] = kept
    # v3 (G5a): exceptions that disagree with the clause that creates them
    inconsistent: set[str] = set()
    for d in good["exception"]:
        parent_doc = on_file.get(referenced_agreement(d) or "")
        why = consistency(d, parent_doc, corpus) if parent_doc else None
        if why:
            flags.append(why)
            inconsistent.add(d.doc_id)

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
        # v2 (G2): drop what a live candidate explicitly supersedes; disagreement left → route
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

    auth = authority_from_evidence(eng, pols, corpus, as_of, record, used, flags)
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
    # v2 (G3): a decision that relies on a document with text addressed to machines goes to a person
    marked = sorted({d.doc_id for d in relied if tampered(d)})
    if marked:
        flags.append("tamper signs in " + ", ".join(marked))
    bad = sorted({d.doc_id for d in relied if d.doc_id in inconsistent})  # v3 (G5a)
    uncertain = [j["q"] for j in used if j["uncertain"]]
    return {
        "scenario": sid,
        "outcome": outcome,
        "gated_outcome": "REQUEST_EVIDENCE" if uncertain or marked or bad else outcome,
        "uncertain": uncertain,
        "commercial_eligibility": eligibility,
        "authority": auth,
        "judgments": used,
        "flags": flags,
    }
