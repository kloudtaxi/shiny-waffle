"""Load and cross-check the hand-authored truth under ``truth/``.

Every reference is resolved at load time: a truth that points at an entity it
never defines is a broken laboratory control, and must fail loudly here rather
than surface later as a confusing evidence artifact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Protocol, TypeVar

import yaml

from northstar.model.entities import (
    Account,
    Contract,
    CreditPolicy,
    CreditRequest,
    Customer,
    DiscountRequest,
    Employee,
    Fact,
    Guarantee,
    Holiday,
    Invoice,
    MaintenanceNotice,
    Order,
    Organization,
    Policy,
    PricingException,
    Product,
    Relationship,
    ServiceCredit,
    SlaSchedule,
    SupportAgreement,
    Ticket,
)
from northstar.model.scenarios import Scenario


class TruthError(ValueError):
    """The hand-authored truth is internally inconsistent."""


@dataclass(frozen=True)
class Corpus:
    name: str
    description: str
    exclude: tuple[str, ...]


@dataclass
class Truth:
    organization: Organization
    customers: list[Customer]
    accounts: list[Account]
    employees: list[Employee]
    products: list[Product]
    contracts: list[Contract]
    exceptions: list[PricingException]
    orders: list[Order]
    discount_requests: list[DiscountRequest]
    policies: list[Policy]
    principles: list[str]
    relationships: list[Relationship]
    facts: list[Fact]
    corpora: dict[str, Corpus]
    scenarios: list[Scenario]
    # credit (experiment 5, lab extension)
    guarantees: list[Guarantee] = field(default_factory=list)
    invoices: list[Invoice] = field(default_factory=list)
    credit_requests: list[CreditRequest] = field(default_factory=list)
    credit_policies: list[CreditPolicy] = field(default_factory=list)
    # SLA (experiment 6, lab extension; truth/support.yaml)
    support_agreements: list[SupportAgreement] = field(default_factory=list)
    sla_schedules: list[SlaSchedule] = field(default_factory=list)
    holidays: list[Holiday] = field(default_factory=list)
    maintenance_notices: list[MaintenanceNotice] = field(default_factory=list)
    service_credits: list[ServiceCredit] = field(default_factory=list)
    tickets: list[Ticket] = field(default_factory=list)
    _index: dict[str, Any] = field(default_factory=dict, repr=False)

    # -- lookups ------------------------------------------------------------
    def customer(self, cid: str) -> Customer:
        return _one(self.customers, cid)

    def employee(self, eid: str) -> Employee:
        return _one(self.employees, eid)

    def product(self, pid: str) -> Product:
        return _one(self.products, pid)

    def contract(self, cid: str) -> Contract:
        return _one(self.contracts, cid)

    def exception(self, xid: str) -> PricingException:
        return _one(self.exceptions, xid)

    def policy(self, pid: str) -> Policy:
        return _one(self.policies, pid)

    def discount_request(self, rid: str) -> DiscountRequest:
        return _one(self.discount_requests, rid)

    def role_title(self, role_id: str) -> str:
        return next(r.title for r in self.organization.roles if r.id == role_id)

    def policy_on(self, when: date) -> Policy | None:
        return next((p for p in self.policies if p.active_on(when)), None)

    def holders_of(self, role_id: str) -> list[Employee]:
        return [e for e in self.employees if e.role == role_id]

    def account_for(self, customer_id: str) -> Account | None:
        return next((a for a in self.accounts if a.customer == customer_id), None)

    def credit_request(self, rid: str) -> CreditRequest:
        return _one(self.credit_requests, rid)

    def credit_policy_on(self, when: date) -> CreditPolicy | None:
        return next((p for p in self.credit_policies if p.active_on(when)), None)

    def ticket(self, tid: str) -> Ticket:
        return _one(self.tickets, tid)

    def customer_by_crm(self, crm_id: str) -> Customer | None:
        return next((c for c in self.customers if c.source_ids.get("crm") == crm_id), None)


class _HasId(Protocol):
    @property
    def id(self) -> str: ...


T = TypeVar("T", bound=_HasId)


def _one(items: list[T], key: str) -> T:
    for item in items:
        if item.id == key:
            return item
    raise KeyError(key)


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_truth(root: Path) -> Truth:
    org = Organization.model_validate(_read(root / "organization.yaml"))
    ent = _read(root / "entities.yaml")
    pol = _read(root / "policies.yaml")
    rel = _read(root / "relationships.yaml")["relationships"]
    corpora_raw = _read(root / "corpora.yaml")["corpora"]

    relationships = []
    for row in rel:
        subject, predicate, obj, *validity = row
        relationships.append(
            Relationship(
                subject=subject,
                predicate=predicate,
                object=obj,
                valid_from=validity[0] if validity else None,
                valid_to=validity[1] if validity else None,
            )
        )

    truth = Truth(
        organization=org,
        customers=[Customer.model_validate(c) for c in ent["customers"]],
        accounts=[Account.model_validate(a) for a in ent["accounts"]],
        employees=[Employee.model_validate(e) for e in ent["employees"]],
        products=[Product.model_validate(p) for p in ent["products"]],
        contracts=[Contract.model_validate(c) for c in ent["contracts"]],
        exceptions=[PricingException.model_validate(x) for x in ent["pricing_exceptions"]],
        orders=[Order.model_validate(o) for o in ent["orders"]],
        discount_requests=[DiscountRequest.model_validate(d) for d in ent["discount_requests"]],
        policies=[Policy.model_validate(p) for p in pol["policies"]],
        principles=list(pol["principles"]),
        relationships=relationships,
        facts=[Fact.model_validate(f) for f in _read(root / "facts.yaml")["facts"]],
        corpora={
            name: Corpus(name, spec["description"], tuple(spec["exclude"]))
            for name, spec in corpora_raw.items()
        },
        scenarios=[
            Scenario.model_validate(_read(p)) for p in sorted((root / "scenarios").glob("*.yaml"))
        ],
        guarantees=[Guarantee.model_validate(g) for g in ent.get("guarantees", [])],
        invoices=[Invoice.model_validate(i) for i in ent.get("invoices", [])],
        credit_requests=[CreditRequest.model_validate(c) for c in ent.get("credit_requests", [])],
        credit_policies=[CreditPolicy.model_validate(c) for c in pol.get("credit_policies", [])],
    )
    sup = _read(root / "support.yaml") if (root / "support.yaml").exists() else {}
    truth.support_agreements = [
        SupportAgreement.model_validate(a) for a in sup.get("agreements", [])
    ]
    truth.sla_schedules = [SlaSchedule.model_validate(x) for x in sup.get("schedules", [])]
    truth.holidays = [Holiday.model_validate(h) for h in sup.get("holidays", [])]
    truth.maintenance_notices = [
        MaintenanceNotice.model_validate(m) for m in sup.get("notices", [])
    ]
    truth.service_credits = [ServiceCredit.model_validate(c) for c in sup.get("credits", [])]
    truth.tickets = [Ticket.model_validate(t) for t in sup.get("tickets", [])]
    _cross_check(truth)
    return truth


def _cross_check(t: Truth) -> None:
    problems: list[str] = []
    role_ids = {r.id for r in t.organization.roles}
    emp_ids = {e.id for e in t.employees}
    cust_ids = {c.id for c in t.customers}
    prod_ids = {p.id for p in t.products}
    contract_ids = {c.id for c in t.contracts}
    exc_ids = {x.id for x in t.exceptions}
    policy_ids = {p.id for p in t.policies}

    for e in t.employees:
        if e.role not in role_ids:
            problems.append(f"{e.id}: unknown role {e.role}")
        if e.manager is not None and e.manager not in emp_ids:
            problems.append(f"{e.id}: unknown manager {e.manager}")
    for a in t.accounts:
        if a.customer not in cust_ids or a.owner not in emp_ids:
            problems.append(f"{a.id}: dangling customer/owner")
    for c in t.contracts:
        if c.customer not in cust_ids or not set(c.covers) <= prod_ids:
            problems.append(f"{c.id}: dangling customer/product")
    for x in t.exceptions:
        if x.contract not in contract_ids or x.product not in prod_ids:
            problems.append(f"{x.id}: dangling contract/product")
        if x.supersedes is not None and x.supersedes not in exc_ids:
            problems.append(f"{x.id}: supersedes unknown {x.supersedes}")
    for d in t.discount_requests:
        if d.customer not in cust_ids or d.product not in prod_ids or d.requestor not in emp_ids:
            problems.append(f"{d.id}: dangling reference")
    for p in t.policies:
        for band in p.bands:
            if band.role not in role_ids:
                problems.append(f"{p.id}: band for unknown role {band.role}")
    for cp in t.credit_policies:
        roles = [b.role for b in cp.bands] + [c.role for c in cp.concurrence]
        problems += [f"{cp.id}: unknown role {r}" for r in roles if r not in role_ids]
    for g in t.guarantees:
        if g.customer not in cust_ids:
            problems.append(f"{g.id}: guarantees unknown customer {g.customer}")
    for i in t.invoices:
        if i.customer not in cust_ids:
            problems.append(f"{i.id}: unknown customer {i.customer}")
    for cr in t.credit_requests:
        if cr.customer not in cust_ids or cr.requestor not in emp_ids:
            problems.append(f"{cr.id}: dangling reference")
        if cr.basis_ref is not None and cr.basis_ref not in {g.id for g in t.guarantees}:
            problems.append(f"{cr.id}: basis_ref {cr.basis_ref} is not a guarantee")

    # Relationships must agree with the attribute form of the same fact.
    reports = {(r.subject, r.object) for r in t.relationships if r.predicate == "reports_to"}
    for e in t.employees:
        if e.manager is not None and e.id in {s for s, _ in reports}:
            if (e.id, e.manager) not in reports:
                problems.append(f"{e.id}: reports_to disagrees with manager")
    owns = {(r.subject, r.object) for r in t.relationships if r.predicate == "owns"}
    for a in t.accounts:
        if (a.owner, a.customer) not in owns:
            problems.append(f"{a.id}: owner not reflected as an 'owns' relationship")

    known = (
        emp_ids
        | cust_ids
        | prod_ids
        | contract_ids
        | exc_ids
        | policy_ids
        | role_ids
        | {a.id for a in t.accounts}
        | {o.id for o in t.orders}
        | {d.id for d in t.discount_requests}
        | {t.organization.id}
        | set(t.organization.departments)
        | {sid for c in t.customers for sid in c.source_ids.values()}
        | {alias for c in t.contracts for alias in c.aliases}
    )
    for r in t.relationships:
        for end in (r.subject, r.object):
            if end not in known:
                problems.append(f"relationship {r.subject} {r.predicate} {r.object}: unknown {end}")

    for sa in t.support_agreements:
        if sa.customer not in cust_ids or not set(sa.products) <= prod_ids:
            problems.append(f"{sa.id}: dangling customer/product")
    for tk in t.tickets:
        if tk.product not in prod_ids:
            problems.append(f"{tk.id}: unknown product {tk.product}")
    for m in t.maintenance_notices:
        if m.customer not in cust_ids or not set(m.products) <= prod_ids:
            problems.append(f"{m.id}: dangling customer/product")
    for s in t.scenarios:
        if s.kind == "sla_decision" and s.ticket not in {tk.id for tk in t.tickets}:
            problems.append(f"{s.id}: unknown ticket {s.ticket}")
    for s in t.scenarios:
        if s.corpus not in t.corpora:
            problems.append(f"{s.id}: unknown corpus {s.corpus}")
    if problems:
        raise TruthError("; ".join(problems))
