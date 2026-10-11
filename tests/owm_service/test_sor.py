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
