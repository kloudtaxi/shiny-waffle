from __future__ import annotations

import pytest

from owm_service.errors import NotFound, Refused
from owm_service.org import Org
from owm_service.people import People
from owm_service.sor import BASIS_FIELDS, basis_columns, contract_view


def edit(org: Org, table: str, key: str, fields: dict[str, str], actor: dict[str, str]) -> None:
    with org.log.transaction() as tx:
        org.sor.edit(tx, table, key, fields, actor=actor, at=org.clock.now())


def test_dr9001_reads_from_the_csv(org: Org) -> None:
    row = org.sor.row("discount_requests", "DR-9001")
    assert row is not None and row["requested_discount_pct"] == "15.0"


def test_edit_is_logged_with_was_and_now(org: Org, sarah: dict[str, str]) -> None:
    edit(org, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"}, sarah)
    e = org.sor.edits("discount_requests", "DR-9001")[-1]
    assert (e.payload["field"], e.payload["was"], e.payload["now"]) == (
        "requested_discount_pct", "15.0", "8.0")  # fmt: skip
    assert e.actor == sarah
    assert org.sor.edits("discount_requests", "DR-9001", after=e.at) == []


def test_kernel_sees_the_edit(org: Org, sarah: dict[str, str]) -> None:
    edit(org, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"}, sarah)
    rows = org.evidence.table("discount_requests")
    assert next(r for r in rows if r["request_id"] == "DR-9001")["requested_discount_pct"] == "8.0"
    assert next(r for r in org.sor.table("discount_requests") if r["request_id"] == "DR-7001")


def test_two_edits_chain_was(org: Org, sarah: dict[str, str]) -> None:
    edit(org, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"}, sarah)
    edit(org, "discount_requests", "DR-9001", {"requested_discount_pct": "9.5"}, sarah)
    last = org.sor.edits("discount_requests", "DR-9001")[-1]
    assert (last.payload["was"], last.payload["now"]) == ("8.0", "9.5")


@pytest.mark.parametrize(
    "fields",
    [{"requested_discount_pct": "abc"}, {"request_date": "23/09/2026"},
     {"requested_discount_pct": "nan"}, {"request_date": "2026-13-01"}],
)  # fmt: skip
def test_malformed_values_are_refused(
    org: Org, sarah: dict[str, str], fields: dict[str, str]
) -> None:
    with pytest.raises(Refused) as e:
        edit(org, "discount_requests", "DR-9001", fields, sarah)
    assert e.value.status == 422 and e.value.refusals[0].rule == "RR-5"
    assert next(iter(fields)) in e.value.refusals[0].detail
    assert org.sor.edits("discount_requests", "DR-9001") == []


def test_one_bad_field_writes_nothing(org: Org, sarah: dict[str, str]) -> None:
    with pytest.raises(Refused):
        edit(org, "discount_requests", "DR-9001",
             {"requested_discount_pct": "8.0", "request_date": "bad"}, sarah)  # fmt: skip
    assert org.sor.edits("discount_requests", "DR-9001") == []


def test_unknowns(org: Org, sarah: dict[str, str]) -> None:
    with pytest.raises(NotFound):
        edit(org, "nope", "X", {"a": "b"}, sarah)
    with pytest.raises(NotFound):
        edit(org, "discount_requests", "DR-0000", {"status": "x"}, sarah)
    with pytest.raises(Refused) as e:
        edit(org, "discount_requests", "DR-9001", {"colour": "red"}, sarah)
    assert e.value.status == 422


def test_insert_seeds_a_scenario_row(org: Org, sarah: dict[str, str]) -> None:
    assert org.sor.row("discount_requests", "DR-9102") is None
    base = dict(org.sor.row("discount_requests", "DR-9001") or {})
    with org.log.transaction() as tx:
        org.sor.insert(tx, "discount_requests", {**base, "request_id": "DR-9102"},
                       actor=sarah, at=org.clock.now())  # fmt: skip
    assert org.sor.row("discount_requests", "DR-9102") is not None
    with pytest.raises(Refused) as e, org.log.transaction() as tx:
        org.sor.insert(tx, "discount_requests", {**base, "request_id": "DR-9102"},
                       actor=sarah, at=org.clock.now())  # fmt: skip
    assert e.value.status == 409


# -- ruling R60: the overlay writes only the request tables, tickets and the SLA rows ------------
HR_ROWS = [  # the final review's probe: Sarah reroutes DR-9001's VP Sales approval to a rep
    {"employee_id": "EMP-200", "full_name": "Michael Torres", "preferred_name": "",
     "title": "Enterprise Account Executive", "department": "Sales", "manager_id": "EMP-500",
     "email": "michael.torres@northstar.example", "location": "Chicago, IL"},
    {"employee_id": "EMP-500", "full_name": "Kelly Floyd", "preferred_name": "",
     "title": "VP Sales", "department": "Sales", "manager_id": "EMP-300",
     "email": "kelly.floyd@northstar.example", "location": "Chicago, IL"},
]  # fmt: skip


def insert(org: Org, table: str, row: dict[str, str], actor: dict[str, str]) -> None:
    with org.log.transaction() as tx:
        org.sor.insert(tx, table, row, actor=actor, at=org.clock.now())


def assert_read_only(e: pytest.ExceptionInfo[Refused], table: str) -> None:
    assert e.value.status == 422 and e.value.refusals[0].rule == "RR-5"
    assert e.value.refusals[0].detail.startswith(f"{table} is read-only here")


def test_inserting_into_hr_is_refused(org: Org, sarah: dict[str, str]) -> None:
    for row in HR_ROWS:
        with pytest.raises(Refused) as e:
            insert(org, "employees", row, sarah)
        assert_read_only(e, "employees")
    assert org.log.read(org.org_id, stream="sor") == []
    assert {r["employee_id"]: r["title"] for r in org.sor.table("employees")}["EMP-500"] == (
        "Enterprise Account Executive")  # fmt: skip


@pytest.mark.parametrize(("table", "key", "fields"), [
    ("crm_accounts", "CRM-2048", {"account_tier": "Commercial"}),
    ("customers", "C-1001", {"payment_terms": "Net 90"}),
    ("employees", "EMP-500", {"title": "VP Sales"}),
    ("ticket_events", "SR-39385", {"event": "x"}),
])  # fmt: skip
def test_editing_any_other_table_is_refused(
    org: Org, sarah: dict[str, str], table: str, key: str, fields: dict[str, str]
) -> None:
    with pytest.raises(Refused) as e:
        edit(org, table, key, fields, sarah)
    assert_read_only(e, table)
    assert org.log.read(org.org_id, stream="sor") == []


@pytest.mark.parametrize("table", ["products", "crm_accounts", "erp_invoices"])
def test_inserting_into_any_other_table_is_refused(
    org: Org, sarah: dict[str, str], table: str
) -> None:
    row = dict(org.sor.table(table)[0])
    with pytest.raises(Refused) as e:
        insert(org, table, row, sarah)
    assert_read_only(e, table)


def test_the_writable_tables_still_take_their_writes(org: Org, sarah: dict[str, str]) -> None:
    edit(org, "service_tickets", "SR-39385", {"status": "Open"}, sarah)
    for table in ("ticket_events", "service_credits"):
        insert(org, table, dict(org.sor.table(table)[0]), sarah)
    kinds = [(e.kind, e.payload["table"]) for e in org.log.read(org.org_id, stream="sor")]
    assert kinds == [("sor.edited", "service_tickets"), ("sor.inserted", "ticket_events"),
                     ("sor.inserted", "service_credits")]  # fmt: skip


def test_contract_view_converts_units(org: Org) -> None:
    row = org.sor.row("discount_requests", "DR-9001")
    assert row is not None
    v = contract_view("discount", row, org.people)
    assert v["requested_discount"] == 0.15
    assert v["customer"] == row["account_id"] and v["requestor"] == "EMP-101"
    cr = org.sor.row("credit_requests", "CR-9201")
    assert cr is not None
    c = contract_view("credit", cr, org.people)
    assert c["requested_limit_usd"] == 400000.0 and c["current_limit_usd"] == 250000.0


def test_basis_fields() -> None:
    assert BASIS_FIELDS["discount"][0] == "account_id"
    assert BASIS_FIELDS["sla"][-1] == "events"
    assert basis_columns("sla", {"ticket_id": "T", "status": "x"}) == [
        "ticket_id",
        "status",
        "events",
    ]


def test_people(org: Org) -> None:
    p = org.people.ref("EMP-200")
    assert (p.name, p.title) == ("Michael Torres", "VP Sales")
    assert org.people.function_of("EMP-200") == "Sales"
    assert org.people.by_name("Sarah Chen") is not None
    assert org.people.by_email("SARAH.CHEN@northstar.example") is not None
    assert org.people.by_name("Nobody At All") is None
    dup = People([
        {"employee_id": "A", "full_name": "X Y", "title": "t", "department": "d", "email": "a@x"},
        {"employee_id": "B", "full_name": "X Y", "title": "t", "department": "d", "email": "b@x"},
    ])  # fmt: skip
    with pytest.raises(ValueError):
        dup.by_name("X Y")
    with pytest.raises(NotFound):
        org.people.ref("EMP-0")
