"""Assemble the seeded background population around the truth."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from northstar.factories._base import SeededFactory, is_reserved
from northstar.factories.credit import (
    BgCreditRequest,
    BgInvoice,
    CreditRequestFactory,
    InvoiceFactory,
    invoice_for,
)
from northstar.factories.customer import CITIES, LEGAL_SUFFIXES, BgCustomer, CustomerFactory
from northstar.factories.discount import BgDiscountRequest, DiscountRequestFactory
from northstar.factories.employee import (
    DEPARTMENT_OF,
    MANAGER_OF_DEPARTMENT,
    BgEmployee,
    EmployeeFactory,
)
from northstar.factories.order import BgOrder, OrderFactory
from northstar.factories.product import NOUNS, BgProduct, ProductFactory
from northstar.model import Truth

SCALES: dict[str, dict[str, int]] = {
    # doc 04: "~10 entities + ~20 relationships + ~10 documents" for the first iteration.
    "small": {
        "customers": 8,
        "employees": 10,
        "products": 6,
        "orders": 30,
        "requests": 24,
        "credit_requests": 10,
    },
    # doc 04: the scale-up target once the boundary is found.
    "large": {
        "customers": 200,
        "employees": 40,
        "products": 80,
        "orders": 500,
        "requests": 1000,
        "credit_requests": 200,
    },
}
MIN_BACKGROUND_AES = 3


@dataclass
class Background:
    customers: list[BgCustomer]
    employees: list[BgEmployee]
    products: list[BgProduct]
    orders: list[BgOrder]
    discount_requests: list[BgDiscountRequest]
    # Owners the truth leaves unspecified (BlueRiver, Cedar, Acme Industrial Supply).
    truth_customer_owners: dict[str, str]
    # credit (experiment 5): generated after everything else, from their own factories
    invoices: list[BgInvoice] = field(default_factory=list)
    credit_limits: dict[str, int] = field(default_factory=dict)  # background CUST id → USD
    credit_requests: list[BgCreditRequest] = field(default_factory=list)


def build_background(truth: Truth, seed: int, scale: str = "small") -> Background:
    counts = SCALES[scale]
    factories: tuple[type[SeededFactory[Any]], ...] = (
        EmployeeFactory,
        CustomerFactory,
        ProductFactory,
        OrderFactory,
        DiscountRequestFactory,
        InvoiceFactory,  # experiment 5: appended, so the streams above don't move
        CreditRequestFactory,
    )
    for offset, factory in enumerate(factories):
        factory.reseed(seed + offset)

    employees = _employees(truth, counts["employees"])
    aes = [e.id for e in employees if e.title == "Enterprise Account Executive"]
    truth_owned = {a.customer for a in truth.accounts}
    truth_customer_owners = {
        c.id: aes[i % len(aes)]
        for i, c in enumerate(c for c in truth.customers if c.id not in truth_owned)
    }
    customers = _customers(counts["customers"], aes)
    products = _products(counts["products"])
    erp_ids = [c.erp_id for c in customers] + [
        c.source_ids["erp"] for c in truth.customers if c.id not in truth_owned
    ]
    drafts = [
        OrderFactory.build(id="", erp_customer_id=OrderFactory.__random__.choice(erp_ids))
        for _ in range(counts["orders"])
    ]
    drafts.sort(key=lambda o: o.order_date)
    orders = [
        o.model_copy(
            update={"id": f"SO-{5001 + i}", "order_value_usd": round(o.order_value_usd, -2)}
        )
        for i, o in enumerate(drafts)
    ]
    requests = _requests(truth, counts["requests"], customers, truth_customer_owners, products)
    invoices = _invoices(truth, orders, customers)
    limits, credit = _credit(truth, counts["credit_requests"], customers, employees, invoices)
    return Background(
        customers, employees, products, orders, requests, truth_customer_owners,
        invoices, limits, credit,
    )  # fmt: skip


def _invoices(truth: Truth, orders: list[BgOrder], customers: list[BgCustomer]) -> list[BgInvoice]:
    """One invoice per invoiced or completed order. Truth customers always pay within 10 days of
    the due date; background customers sometimes pay late."""
    rnd = InvoiceFactory.__random__
    terms = {c.erp_id: c.payment_terms for c in customers}
    truth_erp = {c.source_ids["erp"] for c in truth.customers}
    out = []
    for o in orders:
        if o.status not in ("Invoiced", "Completed"):
            continue
        if o.erp_customer_id in truth_erp:
            delay = rnd.randint(-10, 10)
        else:
            delay = rnd.choice((-5, 0, 2, 5, 10, 20, 35, 50))
        t = terms.get(o.erp_customer_id, "Net 45")
        out.append(invoice_for(o.id, o.erp_customer_id, o.order_date, o.order_value_usd, t, delay))
    out.sort(key=lambda i: (i.invoice_date, i.reference))
    return [i.model_copy(update={"id": f"INV-{30001 + n}"}) for n, i in enumerate(out)]


def late_invoices(
    invoices: list[BgInvoice], erp_id: str, as_of: date, lookback: int, max_late: int
) -> list[str]:
    """Invoices due in the lookback window that were paid, or are still unpaid, more than
    ``max_late`` days after their due date, as known on ``as_of``."""
    late = []
    for i in invoices:
        if i.erp_customer_id != erp_id or not (
            as_of - timedelta(days=lookback) <= i.due_date <= as_of
        ):
            continue
        known = i.paid_date if i.paid_date is not None and i.paid_date <= as_of else as_of
        if (known - i.due_date).days > max_late:
            late.append(i.id)
    return late


def _credit(
    truth: Truth, n: int, customers: list[BgCustomer], employees: list[BgEmployee],
    invoices: list[BgInvoice],
) -> tuple[dict[str, int], list[BgCreditRequest]]:  # fmt: skip
    """Background customers' credit limits, and credit requests decided by the policy in force, in
    date order. An approval raises the customer's limit, and the final limits are the credit
    master's."""
    rnd = CreditRequestFactory.__random__
    limits = {c.id: rnd.choice((50000, 75000, 100000, 150000)) for c in customers}
    ar = sorted(e.id for e in employees if e.title == "Accounts Receivable Specialist")
    by_id = {c.id: c for c in customers}
    drafts = []
    for _ in range(n):
        cust = by_id[rnd.choice(sorted(by_id))]
        drafts.append(CreditRequestFactory.build(
            id="", customer=cust.id, current_limit_usd=0, requestor=cust.owner, approved_by="",
            status="",
        ))  # fmt: skip
    drafts.sort(key=lambda r: r.request_date)
    out = []
    for draft in drafts:
        cust = by_id[draft.customer]
        r = draft.model_copy(update={"current_limit_usd": limits[cust.id]})
        policy = truth.credit_policy_on(r.request_date)
        assert policy is not None, r.request_date  # the window lies inside the policies
        late = late_invoices(invoices, cust.erp_id, r.request_date, policy.lookback_days,
                             policy.max_days_late)  # fmt: skip
        if late or r.requested_limit_usd > policy.caps["Standard"]:
            out.append(r.model_copy(update={"status": "Declined"}))
            continue
        role = policy.band_for(r.requested_limit_usd).role
        if role == "AR_SPECIALIST":
            approver = ar[0] if ar else truth.holders_of("FINANCE_MANAGER")[0].id
        else:
            approver = truth.holders_of(role)[0].id
        out.append(r.model_copy(update={"status": "Approved", "approved_by": approver}))
        limits[cust.id] = r.requested_limit_usd
    return limits, [r.model_copy(update={"id": f"CR-{7001 + i}"}) for i, r in enumerate(out)]


def _employees(truth: Truth, n: int) -> list[BgEmployee]:
    taken = {e.name for e in truth.employees}
    out: list[BgEmployee] = []
    for i in range(n):
        overrides: dict[str, Any] = (
            {"title": "Enterprise Account Executive"} if i < MIN_BACKGROUND_AES else {}
        )
        while True:
            emp = EmployeeFactory.build(id=f"EMP-{500 + i}", **overrides)
            if emp.name not in taken:
                break
        dept = DEPARTMENT_OF[emp.title]
        emp = emp.model_copy(update={"department": dept, "manager": MANAGER_OF_DEPARTMENT[dept]})
        taken.add(emp.name)
        out.append(emp)
    return out


def _customers(n: int, owners: list[str]) -> list[BgCustomer]:
    rnd = CustomerFactory.__random__
    seen: set[str] = set()
    out: list[BgCustomer] = []
    for i in range(n):
        while True:
            cust = CustomerFactory.build(
                id=f"CUST-{2001 + i}",
                crm_id=f"CRM-{3001 + i}",
                erp_id=f"C-{2001 + i}",
                owner=rnd.choice(owners),
            )
            if not is_reserved(cust.name) and cust.name not in seen:
                break
        seen.add(cust.name)
        base = cust.name.split(",")[0]
        city, state = rnd.choice(CITIES)
        update = {
            "erp_name": f"{base} {rnd.choice(LEGAL_SUFFIXES)}",
            "city": city,
            "state": state,
            "postal_code": CustomerFactory.fake().zipcode_in_state(state),
        }
        out.append(cust.model_copy(update=update))
    return out


def _products(n: int) -> list[BgProduct]:
    rnd = ProductFactory.__random__
    out: list[BgProduct] = []
    used: set[str] = set()
    for i in range(n):
        prod = ProductFactory.build(id=f"PROD-{101 + i}")
        while True:
            model = rnd.randrange(100, 990, 10)
            noun = rnd.choice(NOUNS[prod.category])
            name = f"NS-{model} {noun}"
            if name not in used:
                break
        used.add(name)
        out.append(
            prod.model_copy(
                update={
                    "sku": f"NS-{model}-{prod.category[:3].upper()}",
                    "name": name,
                    "list_price_usd": round(prod.list_price_usd, -3),
                }
            )
        )
    return out


def _requests(
    truth: Truth,
    n: int,
    customers: list[BgCustomer],
    truth_customer_owners: dict[str, str],
    products: list[BgProduct],
) -> list[BgDiscountRequest]:
    rnd = DiscountRequestFactory.__random__
    owner_of = {c.id: c.owner for c in customers} | truth_customer_owners
    customer_ids = sorted(owner_of)
    product_ids = [p.id for p in truth.products] + [p.id for p in products]
    out: list[BgDiscountRequest] = []
    for _ in range(n):
        customer = rnd.choice(customer_ids)
        draft = DiscountRequestFactory.build(
            id="",
            customer=customer,
            product=rnd.choice(product_ids),
            requestor=owner_of[customer],
            approved_by="",
        )
        policy = truth.policy_on(draft.request_date)
        assert policy is not None, draft.request_date  # the window lies inside the policies
        band = policy.band_for(draft.requested_discount)
        approver = (
            draft.requestor if band.role == "ENTERPRISE_AE" else truth.holders_of(band.role)[0].id
        )
        out.append(draft.model_copy(update={"approved_by": approver}))
    # Ids are issued in date order, as a real CRM would issue them.
    out.sort(key=lambda r: r.request_date)
    return [r.model_copy(update={"id": f"DR-{7001 + i}"}) for i, r in enumerate(out)]
