"""The decision kernel: the generic core of the lab's hybrid engine.

Refactored for experiment 5 (`runs/2026-10-03-exp5-credit/plan.md`) out of experiment 4's guarded
discount engine (`runs/2026-10-03-adversarial/hybrid_v3.py`). The code moved verbatim; what the
discount engine hard-coded about its own documents (kind names, title words, owning functions, how
to read a document's value) became a parameter. Nothing was added. A decision type is a *spec*
that calls this kernel: `discount.py` is the first.

The kernel does:
- evidence access, one corpus at a time (the knowledge-foundation port): documents and
  system-of-record tables;
- document kinds and provenance (G1): the owning function, not-in-force markers, approval
  authority;
- validity windows, the policy in force, and conflict (G2);
- tamper signs (G3), and consistency across documents (G5);
- Jev judgments and confidence gating;
- the policy's authority bands, roles mapped to HR titles, and approver resolution up the
  manager chain.

The spec does the rest: its questions, how its eligibility follows from the evidence, its outcome
table, and its record.
"""

from __future__ import annotations

import csv
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "decision_engine"))
from engine import Engine  # noqa: E402

CHOICE_FLOOR, NOUL_BAND = 0.5, (0.30, 0.70)  # an uncertain judgment routes to a human
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

Bands = list[tuple[str | None, float, float | None]]
ValueOf = Callable[["Doc"], float | None]


# -- evidence (the knowledge-foundation port) -------------------------------------------------
@dataclass
class Doc:
    filename: str
    doc_id: str
    title: str
    owner: str
    front: dict[str, Any]
    body: str


class Evidence:
    """One corpus: its documents and its system-of-record tables."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def docs(self) -> list[Doc]:
        docs = []
        for p in sorted((self.root / "documents").glob("*.md")):
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

    def table(self, name: str) -> list[dict[str, str]]:
        with (self.root / "structured" / f"{name}.csv").open() as f:
            return list(csv.DictReader(f))


def window(doc: Doc) -> tuple[date, date] | None:
    f, t = doc.front.get("effective_from"), doc.front.get("effective_to")
    if f and t:
        return date.fromisoformat(str(f)), date.fromisoformat(str(t))
    m = re.search(r"from (\d{4}-\d{2}-\d{2}) to\s+(\d{4}-\d{2}-\d{2})", doc.body)
    return (date.fromisoformat(m[1]), date.fromisoformat(m[2])) if m else None


def referenced_agreement(doc: Doc) -> str | None:
    m = re.search(r"[Aa]greement:?\s+([A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+)", doc.body)
    return m[1] if m else None


def row(doc: Doc, field: str) -> str | None:
    """One row of a document's field table, as "Field: value"."""
    m = re.search(rf"^\|\s*{field}\s*\|\s*(.+?)\s*\|\s*$", doc.body, re.M)
    return f"{field}: {m[1]}" if m else None


# -- G1 provenance and G3 tamper signs --------------------------------------------------------
@dataclass(frozen=True)
class KindRule:
    """A decision-bearing kind of document, recognized by its id or title (or an owner that only
    issues that kind). The first matching rule wins."""

    kind: str
    id_prefixes: tuple[str, ...] = ()
    title_words: tuple[str, ...] = ()
    owner_hints: tuple[str, ...] = ()


def classify(d: Doc, rules: tuple[KindRule, ...]) -> str | None:
    for r in rules:
        if (
            any(d.doc_id.startswith(p) for p in r.id_prefixes)
            or any(w in d.title for w in r.title_words)
            or d.owner in r.owner_hints
        ):
            return r.kind
    return None


def not_in_force(d: Doc) -> bool:
    front = " ".join(str(v) for v in d.front.values())
    return bool(NOT_IN_FORCE.search(front) or NOT_IN_FORCE.search(d.body))


def tampered(d: Doc) -> bool:
    return bool(TAMPER.search(d.body))


# -- G5 consistency across documents ----------------------------------------------------------
def products_in(text: str, products: list[dict[str, str]]) -> set[str]:
    """The SKUs a text names, by SKU or full product name."""
    found = set()
    for p in products:
        sku = rf"(?<![A-Za-z0-9-]){re.escape(p['sku'])}(?![A-Za-z0-9])"
        if re.search(sku, text, re.I) or p["product_name"].lower() in text.lower():
            found.add(p["sku"])
    return found


def parent_clause(exc: Doc, parent: Doc) -> str | None:
    """The parent agreement's paragraph that creates the child document (by its id or schedule)."""
    label = re.search(r"Schedule ([A-Z0-9]+)\b", exc.body)
    keys = [exc.doc_id] + ([f"Schedule {label[1]}"] if label else [])
    for para in re.split(r"\n\s*\n", parent.body):
        flat = " ".join(para.split())
        if any(k in flat for k in keys):
            return flat
    return None


def consistency(
    exc: Doc, parent: Doc, products: list[dict[str, str]], value_of: ValueOf,
    product_of: Callable[[Doc], str],
) -> str | None:  # fmt: skip
    """G5a: None if the child agrees with its parent's clause, else why not."""
    clause = parent_clause(exc, parent)
    if clause is None:
        return None
    m = re.search(r"up to \**(\d+)%", clause)
    cmax, emax = (int(m[1]) / 100 if m else None), value_of(exc)
    eprods = products_in(row(exc, "Product") or product_of(exc), products)
    cprods = products_in(clause, products)
    if cmax is not None and emax is not None and cmax != emax:
        return f"{exc.doc_id}: maximum {emax:.0%} disagrees with {parent.doc_id} ({cmax:.0%})"
    if cprods and not eprods <= cprods:
        return (f"{exc.doc_id}: products {sorted(eprods)} go beyond {parent.doc_id} "
                f"({sorted(cprods)})")  # fmt: skip
    return None


# -- policy, authority and approvers -------------------------------------------------------
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
    eng: Engine, pol: Doc, staff: list[dict[str, str]], used: list[dict[str, Any]]
) -> tuple[Bands, dict[str, str]]:
    """A policy's bands with each role mapped to an HR title (Jev), as in A1."""
    by_slug = {slug(x): x for x in sorted({e["title"] for e in staff})}
    q_role = {
        "type": "choice",
        "instructions": "Which job title in this company does the role named in `role` refer to?",
        "criteria": {**by_slug, "none": "None of these job titles"},
    }
    bands: Bands = []
    for role, lo, hi in policy_bands(pol):
        j = judge(eng, {"role": role}, "role", q_role)
        used.append(j)
        bands.append((by_slug.get(j["choice"]), lo, hi))
    return bands, by_slug


def limit_for(bands: Bands, title: str) -> float:
    mine = [hi for x, lo, hi in bands if x == title]
    return 1.0 if None in mine else max((h for h in mine if h is not None), default=0.0)


def authority_of(name: str, title: str, bands: Bands, staff: list[dict[str, str]]) -> float:
    """A person's approval limit: the highest limit held by them or anyone who reports to them
    (HR's manager chain). A manager can approve what their reports can. A name not in HR counts
    only by its stated title."""
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
    eng: Engine, d: Doc, k: str, pols: list[Doc], staff: list[dict[str, str]],
    used: list[dict[str, Any]], owners: Mapping[str, set[str]], value_of: ValueOf,
    approval_kinds: tuple[str, ...], policy_kind: str,
) -> str | None:  # fmt: skip
    """G1: None if the document qualifies, else why not."""
    if d.owner not in owners[k]:
        kinds = "policies" if k == policy_kind else f"{k}s"
        return f"{d.doc_id}: issued by {d.owner or 'no owner'}, which doesn't own {kinds}"
    if not_in_force(d):
        return f"{d.doc_id}: marked as not in force (draft, proposal, pending or unexecuted)"
    if k in approval_kinds:
        m = re.search(
            r"approved by:\s*([^,\n]+),\s*([^,\n]+?)\s*,\s*(\d{4}-\d{2}-\d{2})", d.body, re.I
        )
        top = value_of(d)
        if m and top is not None:
            on = date.fromisoformat(m[3])
            inforce = covering(pols, on)
            if len(inforce) != 1:
                return f"{d.doc_id}: its approval on {on} can't be checked against one policy"
            bands, _ = titled_bands(eng, inforce[0], staff, used)
            if authority_of(m[1].strip(), m[2].strip(), bands, staff) < top:
                return f"{d.doc_id}: approved by {m[2].strip()}, without authority for {top:.0%}"
    return None


def authority_from_evidence(
    eng: Engine, pols: list[Doc], staff: list[dict[str, str]], as_of: date, amount: float,
    requested_by: str, used: list[dict[str, Any]], flags: list[str],
) -> dict[str, Any] | None:  # fmt: skip
    """The policy in force (G2: two in force → None), its bands, the requestor's limit, and the
    approver: the first holder of the required title up the requestor's manager chain, else any
    holder."""
    inforce = covering(pols, as_of)
    if len(inforce) > 1:
        flags.append("conflict: policies " + ", ".join(d.doc_id for d in inforce))
        return None
    if not inforce:
        return None
    pol = inforce[0]
    bands, _ = titled_bands(eng, pol, staff, used)
    need = next((x for x, lo, hi in bands if in_band(amount, lo, hi)), None)
    me = next(e for e in staff if e["email"].lower() == requested_by.lower())
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
    return {"policy": pol.doc_id, "requestor_limit": limit, "requestor_authorized": amount <= limit,
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


# -- the guard pipeline -------------------------------------------------------------------------
@dataclass(frozen=True)
class Guards:
    """What a spec tells the kernel about its documents."""

    rules: tuple[KindRule, ...]
    owners: Mapping[str, set[str]]
    value_of: ValueOf  # a document's value (an exception's maximum), for G1 and G5
    product_of: Callable[[Doc], str]  # the text naming what a document covers, for G5
    policy_kind: str = "policy"
    graded: tuple[str, ...] = ("agreement", "amendment", "exception")
    approval_kinds: tuple[str, ...] = ("exception",)  # G1: their recorded approver is checked
    parent_kind: str = "agreement"
    amending_kinds: tuple[str, ...] = ("amendment",)  # G5b: need their parent on file
    schedule_kinds: tuple[str, ...] = ("exception",)  # G5a: must agree with their parent


@dataclass
class Screened:
    pols: list[Doc]
    good: dict[str, list[Doc]]
    inconsistent: set[str]


def screen(
    eng: Engine, docs: list[Doc], g: Guards, staff: list[dict[str, str]],
    products: list[dict[str, str]], used: list[dict[str, Any]], flags: list[str],
) -> Screened:  # fmt: skip
    """G1 (provenance) and G5 (consistency) over a corpus's documents, in that order."""

    def why(d: Doc, k: str, pols: list[Doc]) -> str | None:
        return provenance(
            eng, d, k, pols, staff, used, g.owners, g.value_of, g.approval_kinds, g.policy_kind
        )

    claimed = [(d, classify(d, g.rules)) for d in docs]
    pol_claims = [d for d, k in claimed if k == g.policy_kind]
    pols = [d for d in pol_claims if d.owner in g.owners[g.policy_kind] and not not_in_force(d)]
    for d in pol_claims:
        if d not in pols:
            flags.append(str(why(d, g.policy_kind, pols)))
    good: dict[str, list[Doc]] = {k: [] for k in g.graded}
    for d, k in claimed:
        if k in good:
            reason = why(d, k, pols)
            if reason:
                flags.append(reason)
            else:
                good[k].append(d)

    # G5b: an amending document counts only if the document it amends is on file and qualifies
    on_file = {d.doc_id: d for d in good.get(g.parent_kind, [])}
    for k in g.amending_kinds:
        kept = []
        for d in good.get(k, []):
            parent = referenced_agreement(d)
            if parent in on_file:
                kept.append(d)
            else:
                flags.append(f"{d.doc_id}: amends {parent or 'an unnamed agreement'}, not on file")
        good[k] = kept
    # G5a: schedules that disagree with the clause that creates them
    inconsistent: set[str] = set()
    for k in g.schedule_kinds:
        for d in good.get(k, []):
            parent_doc = on_file.get(referenced_agreement(d) or "")
            reason = (consistency(d, parent_doc, products, g.value_of, g.product_of)
                      if parent_doc else None)  # fmt: skip
            if reason:
                flags.append(reason)
                inconsistent.add(d.doc_id)
    return Screened(pols, good, inconsistent)


def gate(
    outcome: str, relied: list[Doc], inconsistent: set[str], used: list[dict[str, Any]],
    flags: list[str],
) -> tuple[list[str], str]:  # fmt: skip
    """G3 tamper signs and G5a on what the decision relies on, then confidence gating: the
    uncertain judgments and the outcome a person should see."""
    marked = sorted({d.doc_id for d in relied if tampered(d)})
    if marked:
        flags.append("tamper signs in " + ", ".join(marked))
    bad = sorted({d.doc_id for d in relied if d.doc_id in inconsistent})
    uncertain = [j["q"] for j in used if j["uncertain"]]
    return uncertain, "REQUEST_EVIDENCE" if uncertain or marked or bad else outcome
