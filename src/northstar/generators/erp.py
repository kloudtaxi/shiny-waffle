"""Northstar ERP exports: customer master, item master, sales orders, HR roster."""

from __future__ import annotations

from northstar.artifacts import Artifact
from northstar.export.csv import to_csv
from northstar.factories import Background
from northstar.model import Truth


def generate(truth: Truth, bg: Background) -> list[Artifact]:
    return [_customers(truth, bg), _products(truth, bg), _orders(truth, bg), _employees(truth, bg)]


def _customers(truth: Truth, bg: Background) -> Artifact:
    header = [
        "erp_customer_id",
        "customer_name",
        "industry",
        "bill_to_street",
        "bill_to_city",
        "bill_to_state",
        "bill_to_postal_code",
        "duns_number",
        "payment_terms",
    ]
    rows = [
        [
            c.source_ids["erp"],
            c.erp_name,
            c.industry,
            c.address.street,
            c.address.city,
            c.address.state,
            c.address.postal_code,
            c.duns,
            "Net 45",
        ]
        for c in truth.customers
    ] + [
        [
            b.erp_id,
            b.erp_name,
            b.industry,
            b.street,
            b.city,
            b.state,
            b.postal_code,
            b.duns,
            b.payment_terms,
        ]
        for b in bg.customers
    ]
    rows.sort(key=lambda r: (len(r[0]), r[0]))
    return Artifact(
        id="customers",
        path="structured/customers.csv",
        source_system="Northstar ERP",
        description="ERP bill-to customer master. Legal names differ from CRM display names.",
        content=to_csv(header, rows),
        supports=("C-1001", "C-1044"),
    )


def _products(truth: Truth, bg: Background) -> Artifact:
    header = ["product_id", "sku", "product_name", "category", "list_price_usd"]
    rows = [[p.id, p.sku, p.name, p.category, p.list_price_usd] for p in truth.products]
    rows += [[p.id, p.sku, p.name, p.category, p.list_price_usd] for p in bg.products]
    return Artifact(
        id="products",
        path="structured/products.csv",
        source_system="Northstar ERP",
        description="Item master with current list prices.",
        content=to_csv(header, rows),
        supports=tuple(p.id for p in truth.products),
    )


def _orders(truth: Truth, bg: Background) -> Artifact:
    header = ["order_id", "erp_customer_id", "order_date", "order_value_usd", "currency", "status"]
    rows = [
        [
            o.id,
            truth.customer(o.customer).source_ids["erp"],
            o.date.isoformat(),
            o.value_usd,
            "USD",
            o.status,
        ]
        for o in truth.orders
    ] + [
        [o.id, o.erp_customer_id, o.order_date.isoformat(), o.order_value_usd, "USD", o.status]
        for o in bg.orders
    ]
    rows.sort(key=lambda r: (str(r[2]), str(r[0])))
    return Artifact(
        id="erp_orders",
        path="structured/erp_orders.csv",
        source_system="Northstar ERP",
        description="Sales orders by ERP customer id.",
        content=to_csv(header, rows),
        supports=tuple(o.id for o in truth.orders),
    )


def _employees(truth: Truth, bg: Background) -> Artifact:
    header = [
        "employee_id",
        "full_name",
        "preferred_name",
        "title",
        "department",
        "manager_id",
        "email",
        "location",
    ]
    domain = truth.organization.email_domain
    rows = [
        [
            e.id,
            e.name,
            e.preferred_name,
            truth.role_title(e.role),
            e.department,
            e.manager,
            e.email(domain),
            "Chicago, IL",
        ]
        for e in truth.employees
    ] + [
        [
            e.id,
            e.name,
            None,
            e.title,
            e.department,
            e.manager,
            f"{e.name.lower().replace(' ', '.')}@{domain}",
            e.location,
        ]
        for e in bg.employees
    ]
    return Artifact(
        id="employees",
        path="structured/employees.csv",
        source_system="Northstar ERP (HR module)",
        description="Employee roster with titles and manager ids.",
        content=to_csv(header, rows),
        supports=tuple(e.id for e in truth.employees),
        asserts=("F05", "F06", "F07"),
    )
