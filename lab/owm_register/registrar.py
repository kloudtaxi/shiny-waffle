"""The document registrar: every change to the OWM's register of governing documents after the
bootstrap import (`runs/2026-10-08-register-attacks/plan.md`, rules RR-1 to RR-14).

The bootstrap (`build_register.py`, the 17 / 14 / 16 entries per corpus) is a one-time import of
the approved set; this module governs what happens to it afterwards. A change is one of:

- **register** a new governing document: its text, kind, window, structured terms and relations;
- **revoke** a registered document from a date.

Each change is submitted by one principal and approved by another. The lab models authentication:
a case declares the principals its actor controls (`acting_as`), and a step taken `by` anyone else
is refused. The registrar's clock is fixed (2026-09-01) so a change can reach the 2026-09-23
decisions only by being effective before them, and never by being backdated.

    from registrar import State, apply, RefusedError
    state = State.bootstrap("base")
    state = apply(state, change, text, acting_as={"EMP-401", "EMP-402"})

A refusal raises `RefusedError` naming the rule. `State.register()` gives a `kernel.Register`
(with a store of approved texts) that the decision engines read.
"""

from __future__ import annotations

import copy
import csv
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
sys.path[:0] = [str(LAB / "lab/owm_kernel"), str(LAB / "lab/decision_engine")]
from kernel import Register, fingerprint, parse_doc  # noqa: E402

CLOCK = date(2026, 9, 1)
EXECUTIVE = "Executive"
CORPORA = {"base": LAB / "dataset/evidence",
           "missing-contract-evidence": LAB / "dataset/evidence-variants/missing-contract-evidence",
           "missing-guarantee-evidence":
               LAB / "dataset/evidence-variants/missing-guarantee-evidence"}  # fmt: skip
OWNER = {"credit_policy": "Finance", "guarantee": "Finance",
         "pricing_policy": "Sales", "agreement": "Sales", "amendment": "Sales",
         "exception": "Sales",
         "sla_schedule": "Customer Support", "support_terms": "Customer Support",
         "severity_guide": "Customer Support", "escalation_procedure": "Customer Support",
         "holiday_calendar": "Customer Support"}  # fmt: skip
CUSTOMER_KINDS = {"guarantee", "agreement", "amendment", "exception", "support_terms"}
SCHEMA: dict[str, set[str]] = {
    "credit_policy": {"bands", "concurrence", "lookback_months", "max_days_late", "caps",
                      "separation_of_duties", "separation_of_duties_passes_to",
                      "authority_basis", "tier_source", "guarantee_rule",
                      "decisions_recorded_in"},
    "guarantee": {"amount", "guarantor", "customer"},
    "pricing_policy": {"bands", "approval_evidence_required_above", "rules",
                       "authority_reference"},
    "agreement": {"customer", "products", "pricing", "grants_approval_authority"},
    "amendment": {"customer", "products", "pricing", "grants_approval_authority"},
    "exception": {"customer", "product", "maximum_discount", "grants_approval_authority"},
    "sla_schedule": {"version", "published", "targets", "credits", "cap_pct", "claim_days",
                     "notice_business_days"},
    "support_terms": {"customer", "plan", "products", "coverage_start"},
    "holiday_calendar": {"holidays"},
    "severity_guide": set(),
    "escalation_procedure": set(),
}  # fmt: skip
REQUIRED: dict[str, set[str]] = {
    "credit_policy": {"bands", "concurrence", "lookback_months", "max_days_late", "caps",
                      "separation_of_duties"},
    "guarantee": {"amount", "guarantor", "customer"},
    "pricing_policy": {"bands"},
    "agreement": {"customer", "products", "grants_approval_authority"},
    "amendment": {"customer", "products", "grants_approval_authority"},
    "exception": {"customer", "product", "maximum_discount", "grants_approval_authority"},
    "sla_schedule": {"version", "targets", "credits", "cap_pct", "claim_days",
                     "notice_business_days"},
    "support_terms": {"customer", "plan", "products", "coverage_start"},
    "holiday_calendar": {"holidays"},
    "severity_guide": set(),
    "escalation_procedure": set(),
}  # fmt: skip
NO_GRANT = ("does not grant approval authority", "does not modify northstar's internal approval")
SOD = "no one may approve"


class RefusedError(Exception):
    def __init__(self, rule: str, message: str) -> None:
        super().__init__(f"{rule}: {message}")
        self.rule = rule


# -- people ---------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Staff:
    rows: dict[str, dict[str, str]]

    @classmethod
    def load(cls, root: Path = CORPORA["base"]) -> Staff:
        with (root / "structured/employees.csv").open() as f:
            return cls({r["employee_id"]: r for r in csv.DictReader(f)})

    def head(self, dept: str) -> str | None:
        """The function's head: its member whose manager is outside it (or who has none)."""
        heads = [e for e, r in self.rows.items() if r["department"] == dept
                 and self.rows.get(r["manager_id"], {}).get("department") != dept]  # fmt: skip
        return heads[0] if len(heads) == 1 else None

    def label(self, emp: str) -> str:
        r = self.rows[emp]
        return f"{r['full_name']} ({emp}, {r['title']})"


# -- the register's state -------------------------------------------------------------------------
@dataclass
class State:
    corpus: str
    entries: list[dict[str, Any]]
    store: dict[str, str]  # sha256 -> approved text
    version: int
    log: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def bootstrap(cls, corpus: str) -> State:
        entries = yaml.safe_load((HERE / f"{corpus}.yaml").read_text())["entries"]
        store = {e["sha256"]: (HERE / "store" / f"{e['sha256']}.md").read_text() for e in entries}
        return cls(corpus, entries, store, len(entries))

    def register(self, into: Path | None = None) -> Register:
        """A kernel Register over this state, with its store written to `into` (or a temp dir)."""
        d = into or Path(tempfile.mkdtemp(prefix="ns-registrar-"))
        (d / "store").mkdir(parents=True, exist_ok=True)
        for sha, text in self.store.items():
            (d / "store" / f"{sha}.md").write_text(text)
        return Register(copy.deepcopy(self.entries), d / "store")


def day(x: Any) -> date:
    return x if isinstance(x, date) else date.fromisoformat(str(x))


def overlaps(a: dict[str, Any], b: dict[str, Any]) -> bool:
    a0, b0 = day(a["effective_from"]), day(b["effective_from"])
    a1 = day(a["effective_to"]) if a.get("effective_to") else date.max
    b1 = day(b["effective_to"]) if b.get("effective_to") else date.max
    if b.get("revoked_on"):
        b1 = min(b1, day(b["revoked_on"]))
    return a0 <= b1 and b0 <= a1 and not (b.get("revoked_on") and b1 <= a0)


def duns(e: dict[str, Any]) -> str | None:
    c = (e.get("terms") or {}).get("customer")
    return str(c.get("duns_number")) if isinstance(c, dict) else None


def scope(e: dict[str, Any]) -> str:
    """What one entry in force at a time is about: the company, or a customer (and, for an
    exception, its product; for a guarantee, its guarantor). Amendments accumulate: each is its
    own scope."""
    t = e.get("terms") or {}
    c = t.get("customer")
    if e.get("kind") == "amendment":
        return f"amendment {e['doc_id']}"
    if not isinstance(c, dict):
        return "company"
    s = f"customer {c.get('duns_number')}"
    if e.get("kind") == "exception":
        s += f", product {t.get('product')}"
    if e.get("kind") == "guarantee":
        s += f", guarantor {t.get('guarantor')}"
    return s


# -- text checks ----------------------------------------------------------------------------------
def flat(text: str) -> str:
    return " ".join(text.lower().split())


def usd(n: float) -> str:
    return f"${n:,.0f}"


def pct(x: float) -> str:
    return f"{x * 100:g}%"


def duration(minutes: int, clock: str) -> str:
    unit = "business hours" if clock == "business" else "hours"
    if minutes % 60 == 0:
        h = minutes // 60
        return f"{h} {unit[:-1] if h == 1 else unit}"
    return f"{minutes} minutes"


def stated(text: str, needles: list[str], what: str) -> None:
    f = flat(text)
    missing = [n for n in needles if flat(n) not in f]
    if missing:
        raise RefusedError("RR-6", f"{what} not stated in the text: {missing}")


def lines_with(text: str, needle: str) -> list[str]:
    n = flat(needle)
    return [flat(x) for x in text.splitlines() if n in flat(x)]


def co_located(text: str, title: str, bound: str, what: str) -> None:
    if not any(flat(bound) in line for line in lines_with(text, title)):
        raise RefusedError("RR-6", f"{what}: '{title}' and '{bound}' are not stated together")


def bands_check(text: str, terms: dict[str, Any], fmt: Any, staff: Staff) -> None:
    """Terms ⊆ text (each band's title and bound on one line) and text ⊆ terms (every line that
    names an HR title and a bound is a registered band)."""
    bands = terms["bands"]
    for b in bands:
        bound = b["max_inclusive"] if b["max_inclusive"] is not None else b["min_exclusive"]
        co_located(text, b["title"], fmt(bound), "band")
    titles = {r["title"] for r in staff.rows.values()}
    unit = re.compile(r"\$[\d,]+|\d+(?:\.\d+)?%")
    for line in text.splitlines():
        lf = flat(line)
        if "concurrence" in lf or "maximum credit limit" in lf or "require recorded" in lf:
            continue
        named = [t for t in titles if flat(t) in lf]
        if named and unit.search(line):
            if not any(flat(b["title"]) in lf for b in bands):
                raise RefusedError("RR-6", f"the text states authority not in the terms: {line!r}")


def grants_check(text: str, grants: Any) -> None:
    says_no = any(n in flat(text) for n in NO_GRANT)
    if grants is False and not says_no:
        raise RefusedError("RR-6", "terms say it grants no approval authority; the text doesn't")
    if grants is True and says_no:
        raise RefusedError("RR-6", "terms say it grants approval authority; the text says not")
    if grants not in (True, False):
        raise RefusedError("RR-6", "grants_approval_authority must be true or false")


def customer_check(text: str, c: Any, root: Path) -> None:
    """RR-8: the ids resolve to one customer in the systems of record, and the text names it."""
    if not isinstance(c, dict):
        raise RefusedError("RR-8", "a customer kind must name its customer by registered ids")
    with (root / "structured/customers.csv").open() as f:
        erp = {r["erp_customer_id"]: r for r in csv.DictReader(f)}
    with (root / "structured/crm_accounts.csv").open() as f:
        crm = {r["account_id"]: r for r in csv.DictReader(f)}
    e, a = erp.get(c.get("erp_customer_id") or ""), crm.get(c.get("crm_account_id") or "")
    if e is None or a is None:
        raise RefusedError("RR-8", "the customer's ERP and CRM ids must both exist")
    if not (e["duns_number"] == a["duns_number"] == c.get("duns_number")):
        raise RefusedError("RR-8", "the customer's ERP id, CRM id and DUNS are not one customer")
    if c.get("name") not in (e["customer_name"], a["account_name"]):
        raise RefusedError("RR-8", "the registered name isn't the customer's name of record")
    if not any(flat(n) in flat(text) for n in (e["customer_name"], a["account_name"])):
        raise RefusedError("RR-8", "the text doesn't name the customer")


def terms_check(kind: str, terms: dict[str, Any], text: str, root: Path, staff: Staff) -> None:
    extra = set(terms) - SCHEMA[kind]
    if extra:
        raise RefusedError("RR-6", f"terms not in the {kind} schema: {sorted(extra)}")
    missing = REQUIRED[kind] - set(terms)
    if missing:
        raise RefusedError("RR-6", f"required terms missing: {sorted(missing)}")
    strings = [v for k, v in terms.items()
               if isinstance(v, str) and k not in ("published", "version")]  # fmt: skip
    if kind == "credit_policy":
        bands_check(text, terms, usd, staff)
        for c in terms["concurrence"]:
            co_located(text, c["title"], usd(c["min_exclusive"]), "concurrence")
            stated(text, list(c["tiers"]), "concurrence tiers")
        if not terms["concurrence"] and "concurrence" in flat(text):
            raise RefusedError("RR-6", "the text requires concurrence; the terms have none")
        caps = [f"{usd(v)} for {k} accounts" for k, v in terms["caps"].items()]
        timing = [f"{terms['lookback_months']} months", f"more than {terms['max_days_late']} days"]
        stated(text, caps + timing + strings, "credit terms")
        if bool(terms["separation_of_duties"]) != (SOD in flat(text)):
            raise RefusedError("RR-6", "separation of duties differs between terms and text")
    elif kind == "pricing_policy":
        bands_check(text, terms, pct, staff)
        ev = terms.get("approval_evidence_required_above")
        stated(text, [r.rstrip(".") for r in terms.get("rules", [])]
               + ([pct(ev)] if ev is not None else [])
               + (["Approval Authority Matrix"] if terms.get("authority_reference") else []),
               "pricing terms")  # fmt: skip
    elif kind == "guarantee":
        customer_check(text, terms["customer"], root)
        stated(text, [usd(terms["amount"]), terms["guarantor"]], "guarantee terms")
    elif kind in ("agreement", "amendment"):
        customer_check(text, terms["customer"], root)
        stated(text, list(terms["products"])
               + [pct(x["maximum_discount"]) for x in terms.get("pricing", [])]
               + [x["product"] for x in terms.get("pricing", [])], f"{kind} terms")  # fmt: skip
        grants_check(text, terms["grants_approval_authority"])
    elif kind == "exception":
        customer_check(text, terms["customer"], root)
        stated(text, [terms["product"], pct(terms["maximum_discount"])], "exception terms")
        grants_check(text, terms["grants_approval_authority"])
    elif kind == "sla_schedule":
        for t in terms["targets"]:
            rows = [x for x in lines_with(text, f"| {t['severity']}")
                    if not t.get("plan") or flat(t["plan"]) in x]  # fmt: skip
            want = [duration(t["response_minutes"], t["clock"])] + (
                [duration(t["restoration_minutes"], t["clock"])]
                if t.get("restoration_minutes") else ["no restoration target"])  # fmt: skip
            if not any(all(flat(w) in r for w in want) for r in rows):
                raise RefusedError("RR-6", f"severity {t['severity']} targets not stated: {want}")
        stated(text, [pct(c["pct"]) for c in terms["credits"]]
               + [pct(terms["cap_pct"]), f"{terms['notice_business_days']} business days",
                  str(terms["version"])], "SLA terms")  # fmt: skip
    elif kind == "support_terms":
        customer_check(text, terms["customer"], root)
        stated(text, [terms["plan"], str(terms["coverage_start"]), *terms["products"]],
               "support terms")  # fmt: skip
    elif kind == "holiday_calendar":
        stated(text, [str(h["date"]) for h in terms["holidays"]], "holidays")
    if kind not in CUSTOMER_KINDS and "customer" in terms:
        raise RefusedError("RR-8", f"a {kind} applies company-wide and can't name a customer")


def window_check(text: str, change: dict[str, Any]) -> None:
    for k in ("effective_from", "effective_to"):
        v = change.get(k)
        if v is not None and str(day(v)) not in text:
            raise RefusedError("RR-7", f"{k} {v} is not stated in the text")


# -- people checks --------------------------------------------------------------------------------
def people(kind: str, submit: str | None, approve: str | None, acting_as: set[str],
           staff: Staff) -> tuple[str, str]:  # fmt: skip
    for who in (submit, approve):
        if who is not None and who not in acting_as:
            raise RefusedError("RR-1", f"{who} acted, but the actor doesn't control {who}")
    if submit is None or submit not in staff.rows:
        raise RefusedError("RR-2", f"submitter {submit!r} is not an employee; an agent may propose "
                                   "but never submit or approve")  # fmt: skip
    if approve is None:
        raise RefusedError("RR-4", "no approval")
    if approve not in staff.rows:
        raise RefusedError("RR-2", f"approver {approve!r} is not an employee")
    dept = OWNER[kind]
    if staff.rows[submit]["department"] != dept:
        raise RefusedError("RR-3", f"{submit} is not in {dept}, which owns {kind}")
    may = {staff.head(dept)} | {e for e, r in staff.rows.items() if r["department"] == EXECUTIVE}
    if approve == submit:
        raise RefusedError("RR-4", "the approver is the submitter")
    if approve not in may:
        raise RefusedError("RR-4", f"{approve} may not approve {kind} (needs the {dept} head or an "
                                   "Executive)")  # fmt: skip
    return submit, approve


# -- the two changes ------------------------------------------------------------------------------
def apply(state: State, change: dict[str, Any], text: str | None, acting_as: set[str],
          clock: date = CLOCK, staff: Staff | None = None) -> State:  # fmt: skip
    """Apply one change, or raise RefusedError. Returns a new state; the old one is unchanged."""
    staff = staff or Staff.load()
    root = CORPORA[state.corpus]
    if change.get("base_version") != state.version:
        got = change.get("base_version")
        raise RefusedError("RR-13", f"prepared against version {got}, but the register is at "
                                    f"version {state.version}; re-prepare")  # fmt: skip
    action = change.get("action")
    new = State(state.corpus, copy.deepcopy(state.entries), dict(state.store), state.version + 1,
                list(state.log))  # fmt: skip
    if action == "register":
        _register(new, change, text, acting_as, clock, staff, root)
    elif action == "revoke":
        _revoke(new, change, acting_as, clock, staff)
    else:
        raise RefusedError("RR-5", f"unknown action {action!r}")
    return new


def _register(state: State, ch: dict[str, Any], text: str | None, acting_as: set[str],
              clock: date, staff: Staff, root: Path) -> None:  # fmt: skip
    kind = ch.get("kind")
    if kind not in OWNER:
        raise RefusedError("RR-5", f"unknown kind {kind!r}")
    submit, approve = people(kind, ch.get("submit_by"), ch.get("approve_by"), acting_as, staff)
    if not text:
        raise RefusedError("RR-5", "no document text")
    doc = parse_doc(ch.get("file") or f"{ch.get('doc_id')}.md", text)
    if doc.doc_id != ch.get("doc_id"):
        raise RefusedError("RR-5", f"doc_id {ch.get('doc_id')!r} isn't the text's ({doc.doc_id!r})")
    if any(e["doc_id"] == doc.doc_id for e in state.entries):
        raise RefusedError("RR-5", f"{doc.doc_id} is already registered")
    sha = fingerprint(text)
    if sha in state.store:
        raise RefusedError("RR-5", "this exact text is already registered")
    start = day(ch["effective_from"])
    end = day(ch["effective_to"]) if ch.get("effective_to") else None
    if end is not None and end < start:
        raise RefusedError("RR-7", "the window ends before it starts")
    if start < clock:
        raise RefusedError("RR-9", f"effective {start}, before the register's clock {clock}")
    window_check(text, ch)
    terms = ch.get("terms") or {}
    terms_check(kind, terms, text, root, staff)
    entry: dict[str, Any] = {
        "doc_id": doc.doc_id, "kind": kind, "version": 1, "file": ch.get("file") or doc.filename,
        "sha256": sha, "effective_from": str(start), "effective_to": str(end) if end else None,
        "relations": list(ch.get("relations") or []), "terms": terms,
        "registered_by": staff.label(submit), "approved_by": staff.label(approve),
        "registered_on": str(clock), "approved_on": str(clock),
    }  # fmt: skip
    if ch.get("proposed_by"):
        entry["proposed_by"] = str(ch["proposed_by"])
    by_id = {e["doc_id"]: e for e in state.entries}
    targets = []
    for r in entry["relations"]:
        if r.get("type") == "supersedes":
            t = by_id.get(r.get("target"))
            if t is None:
                raise RefusedError("RR-11", f"{r.get('target')!r} isn't registered")
            if t["kind"] != kind or scope(t) != scope(entry):
                raise RefusedError("RR-11", f"{t['doc_id']} is a {t['kind']} for {scope(t)}; this "
                                            f"is a {kind} for {scope(entry)}")  # fmt: skip
            if day(t["effective_from"]) >= start:
                raise RefusedError("RR-11", f"{t['doc_id']} doesn't start before this one")
            if t.get("revoked_on") or any(
                x.get("type") == "supersedes" and x.get("target") == t["doc_id"]
                for e in state.entries
                for x in e.get("relations", [])
            ):
                raise RefusedError("RR-11", f"{t['doc_id']} is already superseded or revoked")
            targets.append(t["doc_id"])
        elif r.get("type") == "under":
            a = by_id.get(r.get("target"))
            if a is None or a["kind"] != "agreement" or duns(a) != duns(entry):
                raise RefusedError("RR-14", "'under' must name a registered agreement of the same "
                                            "customer")  # fmt: skip
        else:
            raise RefusedError("RR-14", f"relation type {r.get('type')!r} isn't allowed")
    for e in state.entries:
        if (e["kind"] == kind and scope(e) == scope(entry) and e["doc_id"] not in targets
                and overlaps(entry, e)):  # fmt: skip
            until = e["effective_to"] or "open"
            raise RefusedError("RR-10", f"overlaps {e['doc_id']} ({e['effective_from']} to "
                                        f"{until}) without superseding it")  # fmt: skip
    state.entries.append(entry)
    state.store[sha] = text
    state.log.append({"action": "register", "doc_id": doc.doc_id, "by": submit,
                      "approved_by": approve})  # fmt: skip


def _revoke(state: State, ch: dict[str, Any], acting_as: set[str], clock: date,
            staff: Staff) -> None:  # fmt: skip
    target = next((e for e in state.entries if e["doc_id"] == ch.get("target")), None)
    if target is None:
        raise RefusedError("RR-12", f"{ch.get('target')!r} isn't registered")
    submit, approve = people(target["kind"], ch.get("submit_by"), ch.get("approve_by"), acting_as,
                             staff)  # fmt: skip
    when = day(ch.get("revoked_on") or clock)
    if when < clock:
        raise RefusedError("RR-9", f"revocation effective {when}, before the clock {clock}")
    if target.get("revoked_on") or not (
        target.get("effective_to") is None or day(target["effective_to"]) >= when
    ):
        raise RefusedError("RR-12", f"{target['doc_id']} is no longer live on {when}")
    target["revoked_on"] = str(when)
    target["revoked_by"] = staff.label(submit)
    target["revocation_approved_by"] = staff.label(approve)
    state.log.append({"action": "revoke", "doc_id": target["doc_id"], "on": str(when),
                      "by": submit, "approved_by": approve})  # fmt: skip
