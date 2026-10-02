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
    eng: Engine, truth: Any, sid: str, record: dict[str, str], allowed: set[str] | None = None
) -> dict[str, Any]:
    """`allowed`: when given, only these document filenames are candidates (E2E: what an agent
    retrieved). None means the scenario's whole corpus (J1)."""
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

    # -- authority, held at truth (plan) --------------------------------------------------------
    req = resolve_request(truth, scenario)
    requestor = truth.employee(req.requestor)
    policy = truth.policy_on(as_of)
    limit = policy.limit_for(requestor.role) or 0.0
    authorized = req.requested_discount <= limit
    band = policy.band_for(req.requested_discount)
    approver = _approver(truth, requestor, band.role)
    approval = "APPROVE" if authorized else "APPROVE_WITH_AUTHORIZATION"
    outcome = {"unknown": "REQUEST_EVIDENCE", "not_covered": "REVIEW_REQUIRED",
               "exceeded": "REJECT_OR_ESCALATE"}.get(eligibility["status"], approval)  # fmt: skip
    uncertain = [j["q"] for j in used if j["uncertain"]]
    return {
        "scenario": sid,
        "outcome": outcome,
        "gated_outcome": "REQUEST_EVIDENCE" if uncertain else outcome,
        "uncertain": uncertain,
        "commercial_eligibility": eligibility,
        "authority": {"policy": policy.id, "requestor_limit": limit,
                      "requestor_authorized": authorized,
                      "required_role": truth.role_title(band.role), "approver": approver.name},
        "judgments": used,
    }  # fmt: skip


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true", help="answer only from the recording")
    a = ap.parse_args()
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
        d = decide(eng, truth, sid, heldout.record(sid))
        decisions[sid] = d
        raw = scorer.score(sid, d, exp[sid])
        gated = scorer.score(sid, {**d, "outcome": d["gated_outcome"]}, exp[sid])
        scores[sid] = {"raw": raw["grade"], "gated": gated["grade"], "outcome": d["outcome"],
                       "gated_outcome": d["gated_outcome"], "expected": exp[sid]["outcome"],
                       "uncertain": d["uncertain"]}  # fmt: skip
        unsure = f" · uncertain {','.join(d['uncertain'])}" if d["uncertain"] else ""
        print(f"{sid}: raw {raw['grade']:7s} gated {gated['grade']:7s} {d['outcome']} "
              f"(key {exp[sid]['outcome']}){unsure}")  # fmt: skip
    (HERE / "decisions.json").write_text(json.dumps(decisions, indent=1, default=str) + "\n")
    (HERE / "scores.json").write_text(json.dumps(scores, indent=1) + "\n")
    n = len(scores)
    print(
        f"raw strict pass {sum(s['raw'] == 'pass' for s in scores.values())}/{n} · "
        f"gated {sum(s['gated'] == 'pass' for s in scores.values())}/{n}"
    )


if __name__ == "__main__":
    main()
