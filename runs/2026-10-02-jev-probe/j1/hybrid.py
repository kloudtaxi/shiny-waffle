"""J1: the hybrid decision engine. Jev makes the soft judgments; code does the rest.

    export TYPESAFE_API_KEY_FILE=_owm-local/typesafe.key
    uv run python runs/2026-10-02-jev-probe/j1/hybrid.py
    uv run python runs/2026-10-02-jev-probe/j1/hybrid.py --replay   # from the recording only

The design is fixed in `../plan.md`. It mirrors `oracle.decide`, with two differences:

- **Soft judgments come from Jev**, reading the documents of the scenario's corpus, never `truth/`:
  - the pricing basis the request relies on (Choice);
  - whether a document's customer is the request's customer (Choice);
  - whether a document covers the product (Noul).
- **Code does what Jev 1.13 is documented to be weak at:**
  - document windows: front-matter dates, or "from X to Y" in the text;
  - the exception's maximum discount;
  - picking among exceptions by date;
  - composing the outcome.

  Authority (policy, band, the requestor's limit, approver) is held at truth.

Every engine call goes through `lab/decision_engine` and is recorded in `engine-calls.jsonl`. An
identical request is answered from the recording. Outputs: `decisions.json` (one decision per
scenario in the readers' decision shape, with each judgment's answer, probability and confidence)
and `scores.json`.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]
sys.path.insert(0, str(LAB / "lab/decision_engine"))
sys.path.insert(0, str(LAB / "runs/2026-09-28-utopia-aad5b06/procedure"))
import score as scorer  # noqa: E402
from engine import Engine, Recorder, Replay, TypeSafe  # noqa: E402

from northstar.model import load_truth  # noqa: E402
from northstar.oracle import _approver, resolve_request  # noqa: E402

MODEL = "jev-1.13.0"
SCENARIOS = ["S01", "S02", "S03", "S04", "S05"] + [f"S{n:02d}" for n in range(9, 22)]
CORPUS = {
    "base": LAB / "dataset/evidence",
    "missing-contract-evidence": LAB / "dataset/evidence-variants/missing-contract-evidence",
}
CALLS = HERE / "engine-calls.jsonl"

# -- the questions (fixed in the plan) ------------------------------------------------------
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


def party_text(doc: Doc) -> str:
    """For an agreement, its party clause. For an exception, its customer row, or its whole text
    when it has no customer row (the 2023 exception names the customer only in its prose)."""
    for para in re.split(r"\n\s*\n", doc.body):
        if "entered into between" in para or re.search(r"\|\s*Customer\s*\|", para):
            return " ".join(para.split())
    return " ".join(doc.body.split())


def product_text(doc: Doc) -> str:
    """For an agreement, its products section. For an exception, its product row and scope."""
    m = re.search(r"## \d+\. Products\n(.*?)(?=\n## )", doc.body, re.S)
    if m:
        return m[1].strip()
    keep = [p for p in re.split(r"\n\s*\n", doc.body) if re.search(r"[Pp]roduct|NS-", p)]
    return "\n\n".join(keep) or doc.body


def is_agreement(d: Doc) -> bool:
    return d.owner == "Legal" and "Agreement" in d.title


def is_exception(d: Doc) -> bool:
    return d.owner == "Deal Desk" or "Exception" in d.title


# -- authority from evidence (part 3, A1) ---------------------------------------------------
def is_policy(d: Doc) -> bool:
    return d.doc_id.startswith("PRICING-POLICY")


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


def authority_from_evidence(
    eng: Engine, docs: list[Doc], corpus: str, as_of: date, record: dict[str, str],
    used: list[dict[str, Any]],
) -> dict[str, Any] | None:  # fmt: skip
    """The policy in force (code, by its window), its bands (code, from section 3), what HR title
    each band's role means (Jev), and the requestor, limit and approver (code, employees.csv).
    None when no policy in `docs` covers the date."""

    def covers(d: Doc) -> bool:
        w = window(d)
        return bool(w and w[0] <= as_of <= w[1])

    pol = next((d for d in docs if is_policy(d) and covers(d)), None)
    if pol is None:
        return None
    staff = table(corpus, "employees")
    titles = sorted({e["title"] for e in staff})
    by_slug = {slug(x): x for x in titles}
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
    d = float(record["requested_discount_pct"]) / 100
    need = next((x for x, lo, hi in bands if in_band(d, lo, hi)), None)
    me = next(e for e in staff if e["email"].lower() == record["requested_by"].lower())
    mine = [hi for x, lo, hi in bands if x == me["title"]]
    limit = 1.0 if None in mine else max((h for h in mine if h is not None), default=0.0)
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
            "approver": approver["full_name"] if approver else None}  # fmt: skip


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
    authority: str = "truth",
) -> dict[str, Any]:  # fmt: skip
    """`allowed`: when given, only these document filenames are candidates (E2E: what an agent
    retrieved). None means the scenario's whole corpus (J1). `authority`: "truth" (J1, E2E) or
    "evidence" (part 3, A1: the policy and HR records, see `authority_from_evidence`)."""
    scenario = next(s for s in truth.scenarios if s.id == sid)
    as_of: date = scenario.as_of
    docs = [d for d in load_docs(scenario.corpus) if allowed is None or d.filename in allowed]
    account = next(a for a in table(scenario.corpus, "crm_accounts")
                   if a["account_id"] == record["account_id"])  # fmt: skip
    product = next(
        p for p in table(scenario.corpus, "products") if p["sku"] == record["product_sku"]
    )
    customer = {k: account[k] for k in ("account_name", "billing_street", "billing_city",
                                        "billing_state")}  # fmt: skip
    product_name = f"{product['product_name']} ({product['sku']})"
    used: list[dict[str, Any]] = []

    basis = judge(eng, {"request": {"justification": record["justification"]}}, "basis", Q_BASIS)
    used.append(basis)
    eligibility: dict[str, Any] = {"status": "standard", "maximum_discount": None, "basis": None}

    if basis["choice"] != "standard_pricing":
        agreements: list[dict[str, Any]] = []
        for d in docs:
            if is_agreement(d):
                agreements.append({"id": d.doc_id, "window": window(d),
                    "party": judge(eng, {"request_customer": customer, "document": party_text(d)},
                                   "party", Q_PARTY),
                    "covers": judge(eng, {"product": product_name, "document": product_text(d)},
                                    "covers_product", Q_PRODUCT)})  # fmt: skip
        exceptions: list[dict[str, Any]] = []
        for d in docs:
            if is_exception(d):
                exceptions.append({"id": d.doc_id, "window": window(d), "max": max_discount(d),
                    "agreement": referenced_agreement(d),
                    "party": judge(eng, {"request_customer": customer, "document": party_text(d)},
                                   "party", Q_PARTY),
                    "covers": judge(eng, {"product": product_name, "document": product_text(d)},
                                    "covers_product", Q_PRODUCT)})  # fmt: skip
        # An agreement known only from an exception that names it (ACME-SA-2023) takes that
        # exception's customer, product and window.
        known = {a["id"] for a in agreements}
        for x in exceptions:
            if x["agreement"] and x["agreement"] not in known:
                agreements.append({"id": x["agreement"], "window": x["window"],
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
        exc = max((x for x in exceptions if live(x) and x["covers"]["yes"]),
                  key=lambda x: x["window"][0], default=None)  # fmt: skip
        if contract is None:
            eligibility = {"status": "unknown", "maximum_discount": None, "basis": None}
        elif exc is None or not contract["covers"]["yes"] or exc["max"] is None:
            eligibility = {"status": "not_covered", "maximum_discount": None, "basis": None}
        else:
            ok = float(record["requested_discount_pct"]) / 100 <= exc["max"]
            eligibility = {"status": "eligible" if ok else "exceeded",
                           "maximum_discount": exc["max"], "basis": exc["id"]}  # fmt: skip

    # -- authority ------------------------------------------------------------------------------
    auth: dict[str, Any] | None
    if authority == "evidence":
        auth = authority_from_evidence(eng, docs, scenario.corpus, as_of, record, used)
    else:  # held at truth (J1, E2E)
        req = resolve_request(truth, scenario)
        requestor = truth.employee(req.requestor)
        policy = truth.policy_on(as_of)
        limit = policy.limit_for(requestor.role) or 0.0
        band = policy.band_for(req.requested_discount)
        auth = {"policy": policy.id, "requestor_limit": limit,
                "requestor_authorized": req.requested_discount <= limit,
                "required_role": truth.role_title(band.role),
                "approver": _approver(truth, requestor, band.role).name}  # fmt: skip
    if auth is None:  # no policy in force among the evidence: authority unknown
        outcome = "REQUEST_EVIDENCE"
        auth = {"policy": None, "requestor_limit": None, "requestor_authorized": None,
                "required_role": None, "approver": None}  # fmt: skip
    else:
        approval = "APPROVE" if auth["requestor_authorized"] else "APPROVE_WITH_AUTHORIZATION"
        by_status = {"unknown": "REQUEST_EVIDENCE", "not_covered": "REVIEW_REQUIRED",
                     "exceeded": "REJECT_OR_ESCALATE"}  # fmt: skip
        outcome = by_status.get(eligibility["status"], approval)
    uncertain = [j["q"] for j in used if j["uncertain"]]
    return {
        "scenario": sid,
        "outcome": outcome,
        "gated_outcome": "REQUEST_EVIDENCE" if uncertain else outcome,
        "uncertain": uncertain,
        "commercial_eligibility": eligibility,
        "authority": auth,
        "judgments": used,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true", help="answer only from the recording")
    ap.add_argument("--authority", choices=["truth", "evidence"], default="truth")
    a = ap.parse_args()
    tag = "" if a.authority == "truth" else "-a1"
    eng: Engine = Replay(CALLS, MODEL) if a.replay else Recorder(TypeSafe(MODEL), CALLS)
    spec = importlib.util.spec_from_file_location(
        "heldout", LAB / "runs/2026-09-28-utopia-aad5b06-scale-large/heldout/heldout.py"
    )
    assert spec and spec.loader
    heldout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(heldout)
    truth = load_truth(LAB / "truth")
    exp = scorer.expected()
    decisions, scores = {}, {}
    for sid in SCENARIOS:
        d = decide(eng, truth, sid, heldout.record(sid), authority=a.authority)
        decisions[sid] = d
        raw = scorer.score(sid, d, exp[sid])
        gated = scorer.score(sid, {**d, "outcome": d["gated_outcome"]}, exp[sid])
        scores[sid] = {"raw": raw["grade"], "gated": gated["grade"], "outcome": d["outcome"],
                       "gated_outcome": d["gated_outcome"], "expected": exp[sid]["outcome"],
                       "uncertain": d["uncertain"]}  # fmt: skip
        unsure = f" · uncertain {','.join(d['uncertain'])}" if d["uncertain"] else ""
        print(f"{sid}: raw {raw['grade']:7s} gated {gated['grade']:7s} {d['outcome']} "
              f"(key {exp[sid]['outcome']}){unsure}")  # fmt: skip
    (HERE / f"decisions{tag}.json").write_text(json.dumps(decisions, indent=1, default=str) + "\n")
    (HERE / f"scores{tag}.json").write_text(json.dumps(scores, indent=1) + "\n")
    n = len(scores)
    print(
        f"raw strict pass {sum(s['raw'] == 'pass' for s in scores.values())}/{n} · "
        f"gated {sum(s['gated'] == 'pass' for s in scores.values())}/{n}"
    )


if __name__ == "__main__":
    main()
