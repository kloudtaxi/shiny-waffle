"""Levels, the subject's floor, the ratchet and the service's own flags (B-06 Task 11; spec §6.5,
§6.6 and §6.2's flags; G-46). Replay only.

The level comes from the registered policy's terms, never from the kernel; the floor belongs to
the subject and is rebuilt from the log; a version below it gets a blocking `ratchet` condition
for whoever holds the floor's role (passed up, never the requester), one more for the holder of
each concurrence it drops (R26, contract v1.3), and a `ratchet` flag."""

from __future__ import annotations

import copy
import dataclasses
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from owm_service import _lab
from owm_service.assemble import ratchet_flag, revoked_flags
from owm_service.clock import DEMO_TZ
from owm_service.conditions import ratchet_condition
from owm_service.decisions import Decisions
from owm_service.errors import Refused
from owm_service.events import Event
from owm_service.models import (
    Actor,
    DecisionRecord,
    DecisionRequest,
    Flag,
    FlagCode,
    PersonRef,
    RerunRequest,
    ResolveRequest,
)
from owm_service.org import Org
from owm_service.ratchet import (
    FloorState,
    Level,
    below,
    confirmers,
    floor_from,
    floor_of,
    in_force,
    level_for,
    phrases,
    policy_terms,
    raised,
    revoked_by,
)
from owm_service.sessions import Sessions

from . import harness

LAB = Path(__file__).resolve().parents[2]
EXAMPLE: dict[str, Any] = json.loads(
    (LAB / "lab/owm_service/contract/s22.example.json").read_text()
)
SARAH = {"id": "EMP-101", "name": "Sarah Chen", "title": "Enterprise Account Executive",
         "function": "Sales"}  # fmt: skip
MICHAEL = {"id": "EMP-200", "name": "Michael Torres", "title": "VP Sales", "function": "Sales"}
AE, VP, CRO = "Enterprise Account Executive", "VP Sales", "Chief Revenue Officer"
NONE: frozenset[str] = frozenset()


# -- fixtures and helpers -----------------------------------------------------------------------
@pytest.fixture
def sarah(org: Org) -> Actor:  # overrides conftest's plain-dict Sarah for this module
    return Sessions(org).open_person("EMP-101")[1]


@pytest.fixture
def michael(org: Org) -> Actor:
    return Sessions(org).open_person("EMP-200")[1]


@pytest.fixture
def dealdesk(org: Org) -> Actor:
    return Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")[1]


@pytest.fixture
def elena(org: Org) -> Actor:
    return Sessions(org).open_person("EMP-402")[1]


@pytest.fixture
def marcus(org: Org) -> Actor:
    return Sessions(org).open_person("EMP-602")[1]


def dump(m: BaseModel) -> dict[str, Any]:
    return m.model_dump(mode="json", exclude_unset=True)


def ask(
    org: Org, actor: Actor, subject: str, submitted: dict[str, Any] | None = None,
    kind: str = "discount",
) -> DecisionRecord:  # fmt: skip
    key = "ticket" if kind == "sla" else "request_id"
    raw: dict[str, Any] = {"decision_type": kind, "subject": {key: subject}}
    if submitted is not None:
        raw["submitted"] = submitted
    return Decisions(org).ask(actor, DecisionRequest.model_validate(raw))


def ask_s22(org: Org, dealdesk: Actor) -> DecisionRecord:
    return ask(org, dealdesk, "DR-9001", {"requested_discount": 0.08})


def withdraw(org: Org, rec: DecisionRecord) -> None:
    """Free the subject for another decision (the withdraw command comes in Task 12)."""
    sid = rec.subject.request_id or rec.subject.ticket
    assert sid is not None
    with org.log.transaction() as tx:
        payload = {"decision_id": rec.decision_id, "version": rec.version}
        org.log.append(tx, at=org.clock.now(), org=org.org_id, stream=sid,
                       kind="decision.withdrawn", actor=None, payload=payload)  # fmt: skip


def edit(org: Org, actor: Actor, table: str, key: str, fields: dict[str, str]) -> datetime:
    at = org.clock.now()
    with org.log.transaction() as tx:
        org.sor.edit(tx, table, key, fields, actor=dump(actor), at=at)
    return at


def hhmm(at: datetime) -> str:
    return at.astimezone(DEMO_TZ).strftime("%H:%M")


def stored_level(org: Org, rec: DecisionRecord) -> Any:
    """The level the version's `decision.versioned` event keeps beside it."""
    evs = [e for e in Decisions(org).events(rec.decision_id) if e.kind == "decision.versioned"]
    return next(e for e in evs if e.payload["version"]["version"] == rec.version).payload["level"]


def kernel_on(org: Org, kind: _lab.DecisionType, rid: str) -> _lab.KernelResult:
    """The kernel's result on a request the corpus holds, as the service asks for it."""
    row = org.sor.row("discount_requests" if kind == "discount" else "credit_requests", rid)
    assert row is not None
    entries, store = org.procedures()
    as_of = date.fromisoformat(row["request_date"])
    return _lab.decide(
        kind, evidence=org.evidence, inputs={"sid": "pending", "record": row, "as_of": as_of},
        at=as_of, register=org.kernel_register(), entries=entries, store=store, engine=org.engine,
        staff=org.evidence.table("employees"), requested_by=row["requested_by"],
        policy_terms=org.policy_terms, route_mode=False,
    )  # fmt: skip


# -- levels -------------------------------------------------------------------------------------
def test_levels_from_pricing_bands(org: Org) -> None:
    t = org.policy_terms("PRICING-POLICY-2026")
    assert t is not None
    levels = [level_for("discount", x, t, None) for x in (0.08, 0.10, 0.15, 0.25)]
    assert [lv.band if lv else None for lv in levels] == [0, 0, 1, 2]
    assert levels == [Level(0, NONE, AE), Level(0, NONE, AE), Level(1, NONE, VP),
                      Level(2, NONE, CRO)]  # fmt: skip
    t25 = org.policy_terms("PRICING-POLICY-2025")
    assert t25 is not None
    assert [level_for("discount", x, t25, None) for x in (0.15, 0.16)] == [
        Level(0, NONE, AE), Level(1, NONE, VP)]  # fmt: skip


def test_credit_concurrence_counts(org: Org) -> None:
    t = org.policy_terms("CREDIT-POLICY-2026")
    assert t is not None
    assert level_for("credit", 650_000, t, "Strategic") == Level(
        2, frozenset({"VP Sales"}), "Director of Finance")  # fmt: skip
    assert level_for("credit", 650_000, t, "Standard") == Level(2, NONE, "Director of Finance")
    assert level_for("credit", 650_000, t, None) == Level(2, NONE, "Director of Finance")
    assert level_for("credit", 400_000, t, "Strategic") == Level(1, NONE, "Finance Manager")
    assert level_for("credit", 500_000, t, "Strategic") == Level(1, NONE, "Finance Manager")
    anyone = {**t, "concurrence": [{"title": "CFO", "min_exclusive": 100_000.0, "tiers": []}]}
    assert level_for("credit", 400_000, anyone, None) == Level(1, frozenset({"CFO"}),
                                                               "Finance Manager")  # fmt: skip
    assert level_for("sla", 4200.0, t, None) is None


def test_below_and_raised() -> None:
    ae, vp, cro = Level(0, NONE, AE), Level(1, NONE, VP), Level(2, NONE, CRO)
    assert below(ae, vp) and not below(vp, vp) and not below(cro, vp)
    fm, dof = Level(1, NONE, "Finance Manager"), Level(2, NONE, "Director of Finance")
    fm_vp = Level(1, frozenset({"VP Sales"}), "Finance Manager")
    assert below(fm, fm_vp)  # drops a concurrence the floor required
    assert not below(fm_vp, fm)
    assert below(dof, fm_vp)  # a higher band still drops the concurrence
    assert raised(vp, ae) == vp and raised(ae, vp) == vp and raised(vp, vp) == vp
    assert raised(fm_vp, dof) == Level(2, frozenset({"VP Sales"}), "Director of Finance")


def test_policy_terms_from_the_register(org: Org) -> None:
    entries = org.register_state().entries
    day = date(2026, 9, 23)
    p26, p25 = org.policy_terms("PRICING-POLICY-2026"), org.policy_terms("PRICING-POLICY-2025")
    assert p26 is not None and p25 is not None
    assert policy_terms("discount", None, entries, day, org.policy_terms) == p26  # withheld
    assert policy_terms("discount", None, entries, date(2025, 9, 23), org.policy_terms) == p25
    assert policy_terms("credit", None, entries, day, org.policy_terms) == org.policy_terms(
        "CREDIT-POLICY-2026")  # fmt: skip
    # the authority's policy wins; one the register doesn't hold falls back to the one in force
    assert policy_terms("discount", "PRICING-POLICY-2025", entries, day, org.policy_terms) == p25
    assert policy_terms("discount", "PRICING-POLICY-1999", entries, day, org.policy_terms) == p26
    assert policy_terms("discount", None, entries, date(2030, 1, 1), org.policy_terms) is None
    revoked = copy.deepcopy(entries)
    next(e for e in revoked if e["doc_id"] == "PRICING-POLICY-2026")["revoked_on"] = "2026-09-01"
    assert policy_terms("discount", None, revoked, day, org.policy_terms) is None
    assert policy_terms("discount", None, revoked, date(2026, 8, 31), org.policy_terms) == p26


# -- the floor on asking --------------------------------------------------------------------------
def test_s22_v1_floor(org: Org, dealdesk: Actor) -> None:
    v1 = ask_s22(org, dealdesk)
    assert v1.floor is not None
    assert v1.floor.model_dump() == {"subject": "DR-9001", "level": 1, "set_by": {
        "decision_id": v1.decision_id, "version": 1}, "confirmed_by": None}  # fmt: skip
    assert stored_level(org, v1) == {"band": 1, "concurrences": [], "title": "VP Sales"}
    assert [c.source for c in v1.conditions] == ["input_conflict"] and v1.flags == []
    assert floor_of(org, "DR-9001") == FloorState("DR-9001", Level(1, NONE, VP),
                                                  (v1.decision_id, 1), None)  # fmt: skip


def test_new_decision_inherits_the_subjects_floor(org: Org, sarah: Actor) -> None:
    """G-46: Sarah withdraws, edits the CRM down to 8%, which is in her own band, and asks again.
    The outcome stands (APPROVE), but the floor stays with DR-9001: Michael must confirm."""
    first = ask(org, sarah, "DR-9001")
    assert first.floor is not None and first.floor.level == 1 and first.conditions == []
    withdraw(org, first)
    at = edit(org, sarah, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"})
    second = ask(org, sarah, "DR-9001")
    assert (second.decision_id, second.outcome, second.gated_outcome) == ("DEC-0002", "APPROVE",
                                                                          "APPROVE")  # fmt: skip
    assert dump(second)["floor"] == {"subject": "DR-9001", "level": 1, "set_by": {
        "decision_id": first.decision_id, "version": 1}, "confirmed_by": None}  # fmt: skip
    assert stored_level(org, second) == {"band": 0, "concurrences": [], "title": AE}
    # R24: the floor was set by another decision, so the wording names it
    assert [dump(c) for c in second.conditions] == [{
        "id": "c1", "source": "ratchet",
        "what": "Confirm the lower approval level: DEC-0001 version 1 needed the VP Sales; this "
                "decision's version 1 is within Sarah Chen's own authority.",
        "who": [MICHAEL], "blocking": True, "field": None, "submitted": None, "on_record": None,
        "opened_in_version": 1, "resolved": None,
    }]  # fmt: skip
    assert [dump(f) for f in second.flags] == [
        {"code": "self_sourced_basis",
         "text": f"DR-9001 requested_discount changed from 0.15 to 0.08 by Sarah Chen at "
                 f"{hhmm(at)}, after the request.",
         "routes": False, "about": ["DR-9001"]},
        {"code": "ratchet",
         "text": "Below DR-9001's floor: DEC-0001 version 1 needed the VP Sales.",
         "routes": False, "about": ["DR-9001"]},
    ]  # fmt: skip
    assert second.state == "not_ready" and second.approvals == []
    assert second.actions[0].params["discount"] == 0.08  # the outcome stands


def test_ratchet_condition_follows_the_input_conflicts(org: Org, sarah: Actor) -> None:
    withdraw(org, ask(org, sarah, "DR-9001"))
    edit(org, sarah, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"})
    v = ask(org, sarah, "DR-9001", {"requested_discount": 0.15})
    assert [(c.id, c.source) for c in v.conditions] == [("c1", "input_conflict"),
                                                        ("c2", "ratchet")]  # fmt: skip


def test_a_version_at_the_floor_keeps_who_set_it(org: Org, sarah: Actor) -> None:
    first = ask(org, sarah, "DR-9001")
    withdraw(org, first)
    again = ask(org, sarah, "DR-9001")
    assert again.floor == first.floor and again.conditions == [] and again.flags == []
    assert again.floor is not None and again.floor.set_by.decision_id == first.decision_id


def test_missing_record_level_from_the_submitted_figure(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The replay has no answers for a record nobody holds, so the kernel is handed DR-9001's
    result; the level is the submitted 25%'s, not the result's."""
    kr = kernel_on(org, "discount", "DR-9001")
    monkeypatch.setattr(_lab, "decide", lambda kind, **kw: kr)
    v = ask(org, sarah, "DR-0001", {"customer": "CRM-2048", "product": "NS-500",
                                    "requested_discount": 0.25})  # fmt: skip
    assert [c.source for c in v.conditions] == ["missing_record"]
    assert stored_level(org, v) == {"band": 2, "concurrences": [], "title": CRO}
    assert v.floor is not None and (v.floor.level, v.floor.set_by.decision_id) == (2, v.decision_id)


def test_below_a_cro_floor_david_morgan_confirms(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A floor at the CRO band (25%), then 15% on the same subject: the VP Sales band, which Sarah
    isn't authorized for (the kernel's authority says so), so the version is `at the VP Sales`
    and the CRO, David Morgan, confirms."""
    kr = kernel_on(org, "discount", "DR-9001")  # requestor_authorized: False
    monkeypatch.setattr(_lab, "decide", lambda kind, **kw: kr)
    figures = {"customer": "CRM-2048", "product": "NS-500"}
    first = ask(org, sarah, "DR-0001", {**figures, "requested_discount": 0.25})
    withdraw(org, first)
    v = ask(org, sarah, "DR-0001", {**figures, "requested_discount": 0.15})
    assert [(c.id, c.source) for c in v.conditions] == [("c1", "missing_record"), ("c2", "ratchet")]
    ratchet = v.conditions[1]
    did = first.decision_id
    assert ratchet.what == (f"Confirm the lower approval level: {did} version 1 needed the "
                            "Chief Revenue Officer; this decision's version 1 is at the VP "
                            "Sales.")  # fmt: skip
    assert [p.id for p in ratchet.who] == ["EMP-300"]
    assert [f.text for f in v.flags] == [
        f"Below DR-0001's floor: {did} version 1 needed the Chief Revenue Officer."]  # fmt: skip
    assert v.floor is not None
    assert (v.floor.level, v.floor.set_by.decision_id) == (2, first.decision_id)


def test_credit_level_counts_the_customers_tier(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    v = ask(org, sarah, "CR-9201", None, "credit")
    assert stored_level(org, v) == {"band": 1, "concurrences": [], "title": "Finance Manager"}
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None and _lab.credit_tier(org.evidence, row) == "Strategic"
    kr = kernel_on(org, "credit", "CR-9201")  # replay: the kernel's answer for CR-9201
    monkeypatch.setattr(_lab, "decide", lambda kind, **kw: kr)
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9299",
                       "requested_limit_usd": "650000"}, actor=dump(sarah),
                       at=org.clock.now())  # fmt: skip
    big = ask(org, sarah, "CR-9299", None, "credit")
    assert stored_level(org, big) == {"band": 2, "concurrences": ["VP Sales"],
                                      "title": "Director of Finance"}  # fmt: skip


def test_dropping_a_concurrence_is_below_the_floor(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """$650,000 for Acme (Strategic) needs the Director of Finance with the VP Sales concurrence.
    Sarah withdraws and moves the request to Blue River (Standard): the same band, without the
    concurrence. The wording names what was dropped instead of repeating the band."""
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None
    kr = kernel_on(org, "credit", "CR-9201")  # replay: the kernel's answer for CR-9201
    monkeypatch.setattr(_lab, "decide", lambda kind, **kw: kr)
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9299",
                       "requested_limit_usd": "650000"}, actor=dump(sarah),
                       at=org.clock.now())  # fmt: skip
    first = ask(org, sarah, "CR-9299", None, "credit")
    withdraw(org, first)
    at = edit(org, sarah, "credit_requests", "CR-9299", {"erp_customer_id": "C-1002"})
    v = ask(org, sarah, "CR-9299", None, "credit")
    assert stored_level(org, v) == {"band": 2, "concurrences": [], "title": "Director of Finance"}
    did = first.decision_id
    want = (f"Confirm the lower approval level: {did} version 1 needed the Director of Finance "
            "with the VP Sales concurrence; this decision's version 1 drops the VP Sales "
            "concurrence.")  # fmt: skip
    # R26: the floor's band holder, then the dropped concurrence's holder, one condition each
    assert [(c.id, c.source, c.blocking, c.what, [p.id for p in c.who]) for c in v.conditions] == [
        ("c1", "ratchet", True, want, ["EMP-402"]),  # Elena Novak, the Director of Finance
        ("c2", "ratchet", True, want, ["EMP-200"]),  # Michael Torres, the VP Sales
    ]  # fmt: skip
    assert [f.text for f in v.flags] == [
        f"CR-9299 customer changed from C-1001 to C-1002 by Sarah Chen at {hhmm(at)}, after the "
        "request.",
        f"Below CR-9299's floor: {did} version 1 needed the Director of Finance with the VP Sales "
        "concurrence.",
    ]  # fmt: skip
    assert v.floor is not None and (v.floor.level, v.floor.set_by.decision_id) == (2, did)


def cr9299_rerun_at(
    org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch, limit: str
) -> DecisionRecord:  # fmt: skip
    """CR-9299: $650,000 for Acme (Strategic), so the Director of Finance with the VP Sales
    concurrence. Sarah, the requester, then edits the ERP to `limit` and asks for a re-run:
    version 2. The kernel replays CR-9201's answer; the level comes from the row."""
    row = org.sor.row("credit_requests", "CR-9201")
    assert row is not None
    kr = kernel_on(org, "credit", "CR-9201")
    monkeypatch.setattr(_lab, "decide", lambda kind, **kw: kr)
    with org.log.transaction() as tx:
        org.sor.insert(tx, "credit_requests", {**row, "request_id": "CR-9299",
                       "requested_limit_usd": "650000"}, actor=dump(sarah),
                       at=org.clock.now())  # fmt: skip
    v1 = ask(org, sarah, "CR-9299", None, "credit")
    assert v1.conditions == []
    edit(org, sarah, "credit_requests", "CR-9299", {"requested_limit_usd": limit})
    return Decisions(org).rerun(sarah, v1.decision_id, RerunRequest(decision_version=1))


def resolve(org: Org, actor: Actor, did: str, cid: str, version: int) -> DecisionRecord:
    body = ResolveRequest(decision_version=version, resolution="confirmed_lower_level")
    return Decisions(org).resolve(actor, did, cid, body)


def open_ratchets(rec: DecisionRecord) -> list[tuple[str, list[str], int]]:
    return [(c.id, [p.id for p in c.who], c.opened_in_version) for c in rec.conditions
            if c.source == "ratchet" and c.resolved is None]  # fmt: skip


def test_a_dropped_concurrence_is_confirmed_by_its_holder_too(
    org: Org, sarah: Actor, michael: Actor, elena: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R26 (contract v1.3): at $450,000 the re-run is in the Finance Manager's band and drops the
    VP Sales concurrence. One ratchet condition per confirmer: Elena Novak for the floor's band,
    Michael Torres for the concurrence. Each resolves only their own, each resolution re-runs,
    and the floor drops to version 2's level only once both have confirmed."""
    v2 = cr9299_rerun_at(org, sarah, monkeypatch, "450000")
    did = v2.decision_id
    assert open_ratchets(v2) == [("c1", ["EMP-402"], 2), ("c2", ["EMP-200"], 2)]
    assert v2.conditions[0].what == v2.conditions[1].what
    assert v2.conditions[0].what.startswith(
        "Confirm the lower approval level: version 1 needed the Director of Finance with the VP "
        "Sales concurrence; version 2 ")  # fmt: skip
    for who, cid in ((michael, "c1"), (elena, "c2"), (sarah, "c1")):  # only their own; never Sarah
        with pytest.raises(Refused):
            resolve(org, who, did, cid, 2)
    v3 = resolve(org, elena, did, "c1", 2)
    assert open_ratchets(v3) == [("c2", ["EMP-200"], 2)]  # the same condition, still open
    c1 = v3.conditions[0]
    assert (c1.id, c1.resolved and c1.resolved.by.id) == ("c1", "EMP-402")  # kept as history
    assert v3.state == "not_ready" and "ratchet" in {f.code for f in v3.flags}
    floor = floor_of(org, "CR-9299")
    assert floor is not None and floor.level == Level(2, frozenset({VP}), "Director of Finance")
    assert v3.previous is not None and v3.previous.what_changed == (
        "Elena Novak confirmed the lower approval level; the lower level still needs Michael "
        "Torres to confirm it.")  # fmt: skip
    v4 = resolve(org, michael, did, "c2", 3)
    assert open_ratchets(v4) == [] and "ratchet" not in {f.code for f in v4.flags}
    assert [(c.id, c.resolved and c.resolved.rerun_version) for c in v4.conditions] == [
        ("c1", 3), ("c2", 4)]  # fmt: skip
    floor = floor_of(org, "CR-9299")
    assert floor is not None and floor.confirmed_by is not None
    assert (floor.level, floor.set_by, floor.confirmed_by.id) == (
        Level(1, NONE, "Finance Manager"), (did, 2), "EMP-200")  # fmt: skip
    assert v4.floor is not None and v4.floor.level == 1
    assert v4.previous is not None and v4.previous.what_changed == (
        "Michael Torres confirmed the lower approval level; no conditions remain.")  # fmt: skip


def test_a_confirmation_counts_only_for_its_own_round(
    org: Org, sarah: Actor, elena: Actor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Elena confirms $450,000, then Sarah edits the ERP to $90,000 and asks for a re-run. That's
    another level, so a new round opens and both confirm again, under new ids; c2, never
    confirmed, is gone, and c1 stays as history."""
    v2 = cr9299_rerun_at(org, sarah, monkeypatch, "450000")
    did = v2.decision_id
    resolve(org, elena, did, "c1", 2)
    edit(org, sarah, "credit_requests", "CR-9299", {"requested_limit_usd": "90000"})
    v4 = Decisions(org).rerun(sarah, did, RerunRequest(decision_version=3))
    assert open_ratchets(v4) == [("c3", ["EMP-402"], 4), ("c4", ["EMP-200"], 4)]
    assert [c.id for c in v4.conditions] == ["c1", "c3", "c4"]
    assert v4.previous is not None and v4.previous.what_changed == (
        "Sarah Chen asked for a re-run; the level is still below the floor.")  # fmt: skip


def test_ratchet_wording() -> None:
    """Ruling R24: another decision's floor is named, this decision's keeps the bare `version N`
    (the contract's `v2Ratchet`, which Task 12's re-runs make)."""
    vp_floor = FloorState("DR-9001", Level(1, NONE, VP), ("DEC-0418", 1))
    ae = Level(0, NONE, AE)
    same = phrases(vp_floor, ae, "DEC-0418", 2, "Sarah Chen", True)
    assert same == ("version 1 needed the VP Sales",
                    "version 2 is within Sarah Chen's own authority")  # fmt: skip
    ex = EXAMPLE["v2Ratchet"]
    michael = PersonRef.model_validate(MICHAEL)
    assert dump(ratchet_condition("c2", *same, 2, michael)) == ex["conditions"][1]
    assert dump(ratchet_flag("DR-9001", same[0])) == ex["flags"][1]
    assert phrases(vp_floor, ae, "DEC-0431", 1, "Sarah Chen", False) == (
        "DEC-0418 version 1 needed the VP Sales",
        "this decision's version 1 is at the Enterprise Account Executive")  # fmt: skip
    dof = "Director of Finance"
    with_vp = FloorState("CR-1", Level(2, frozenset({"VP Sales"}), dof), ("DEC-0001", 1))
    assert phrases(with_vp, Level(2, NONE, dof), "DEC-0001", 3, "x", False) == (
        "version 1 needed the Director of Finance with the VP Sales concurrence",
        "version 3 drops the VP Sales concurrence")  # fmt: skip
    assert phrases(with_vp, Level(1, NONE, "Finance Manager"), "DEC-0002", 1, "x", False) == (
        "DEC-0001 version 1 needed the Director of Finance with the VP Sales concurrence",
        "this decision's version 1 is at the Finance Manager")  # fmt: skip
    two = FloorState("CR-1", Level(2, frozenset({"VP Sales", "CFO"}), dof), ("DEC-0001", 1))
    assert phrases(two, Level(2, NONE, dof), "DEC-0001", 2, "x", False) == (
        "version 1 needed the Director of Finance with the CFO and VP Sales concurrences",
        "version 2 drops the CFO and VP Sales concurrences")  # fmt: skip


@pytest.mark.parametrize(
    ("on", "pricing", "credit"),
    [(date(2025, 9, 23), "PRICING-POLICY-2025", "CREDIT-POLICY-2025"),
     (date(2026, 9, 23), "PRICING-POLICY-2026", "CREDIT-POLICY-2026"),
     (date(2027, 2, 1), "PRICING-POLICY-2027", None)],
)  # fmt: skip
def test_the_policy_in_force_is_the_kernels(
    org: Org, on: date, pricing: str, credit: str | None
) -> None:
    """The level's policy when the authority is withheld is the one the kernel's own
    `entry_in_force` picks on the bootstrap register."""
    kernel = harness.lab("kernel")
    entries = org.register_state().entries
    for kind, doc_kind, want in (("discount", "pricing_policy", pricing),
                                 ("credit", "credit_policy", credit)):  # fmt: skip
        theirs = kernel.entry_in_force([e for e in entries if e["kind"] == doc_kind], on, [])
        mine = in_force(entries, doc_kind, on)
        assert (mine and mine["doc_id"]) == (theirs and theirs["doc_id"]) == want
        terms = policy_terms(kind, None, entries, on, org.policy_terms)
        assert terms == (theirs["terms"] if theirs else None)


def test_sla_has_no_floor(org: Org, marcus: Actor) -> None:
    v = ask(org, marcus, "SR-39385", None, "sla")
    assert v.floor is None and v.conditions == []
    assert not {f.code for f in v.flags} & {"ratchet", "self_sourced_basis"}
    assert stored_level(org, v) is None and floor_of(org, "SR-39385") is None


# -- the floor, rebuilt -------------------------------------------------------------------------
def _ev(seq: int, kind: str, payload: dict[str, Any]) -> Event:
    at = datetime(2026, 9, 23, 10, tzinfo=UTC) + timedelta(minutes=seq)
    return Event(seq, at, at, "northstar", "DR-1", kind, None, payload)


Cond = tuple[str, str, int]  # (id, source, opened_in_version)


def _versioned(seq: int, did: str, n: int, level: Level | None,
               conditions: tuple[Cond, ...] = ()) -> Event:  # fmt: skip
    lv = None if level is None else {"band": level.band, "title": level.title,
                                     "concurrences": sorted(level.concurrences)}  # fmt: skip
    version = {"decision_id": did, "version": n, "subject": {"request_id": "DR-1"},
               "requested_at": _ev(seq, "", {}).at.isoformat(),
               "conditions": [{"id": c, "source": s, "opened_in_version": o}
                              for c, s, o in conditions]}  # fmt: skip
    return _ev(seq, "decision.versioned", {"version": version, "level": lv})


def _resolved(seq: int, did: str, cid: str, resolution: str) -> Event:
    return _ev(seq, "condition.resolved", {"decision_id": did, "condition_id": cid, "resolved": {
        "by": MICHAEL, "at": "t", "resolution": resolution, "note": None,
        "rerun_version": 0}})  # fmt: skip


def test_the_floor_rises_and_only_a_confirmation_lowers_it() -> None:
    ae, vp, cro = Level(0, NONE, AE), Level(1, NONE, VP), Level(2, NONE, CRO)
    evs = [_versioned(1, "DEC-0001", 1, vp)]
    assert floor_from(evs, "DR-1") == FloorState("DR-1", vp, ("DEC-0001", 1), None)
    evs += [_versioned(2, "DEC-0001", 2, ae, (("c2", "ratchet", 2),)),  # below: no move
            _resolved(3, "DEC-0001", "c2", "corrected_record"),  # not a confirmation
            _ev(4, "decision.withdrawn", {"decision_id": "DEC-0001", "version": 2}),
            _ev(5, "decision.failed", {"reason": "x"})]  # fmt: skip
    assert floor_from(evs, "DR-1") == FloorState("DR-1", vp, ("DEC-0001", 1), None)
    evs += [_versioned(6, "DEC-0002", 1, cro), _versioned(7, "DEC-0002", 2, None)]  # rises
    assert floor_from(evs, "DR-1") == FloorState("DR-1", cro, ("DEC-0002", 1), None)
    evs += [_ev(8, "decision.declined", {"decision_id": "DEC-0002", "version": 1, "index": 0,
                                         "declined": {}}),  # declined: the floor stays
            _versioned(9, "DEC-0003", 1, ae, (("c1", "ratchet", 1),))]  # fmt: skip
    assert floor_from(evs, "DR-1") == FloorState("DR-1", cro, ("DEC-0002", 1), None)
    evs += [_resolved(10, "DEC-0003", "c1", "confirmed_lower_level")]
    lowered = FloorState("DR-1", ae, ("DEC-0003", 1), PersonRef.model_validate(MICHAEL))
    assert floor_from(evs, "DR-1") == lowered
    assert lowered.model().model_dump() == {"subject": "DR-1", "level": 0, "set_by": {
        "decision_id": "DEC-0003", "version": 1}, "confirmed_by": MICHAEL}  # fmt: skip
    evs += [_versioned(11, "DEC-0003", 2, ae, (("c1", "ratchet", 1),))]  # confirmed level: same
    assert floor_from(evs, "DR-1") == lowered
    assert floor_from([_versioned(1, "DEC-0001", 1, None)], "DR-1") is None
    assert floor_from([], "DR-1") is None


def test_a_confirmation_lowers_the_floor_wherever_it_is_logged() -> None:
    """A re-run may log the resolution before or after its new version: the floor comes out the
    same, lowered to the level of the version that opened the ratchet (`opened_in_version`), with
    any version logged after that one raising it again."""
    ae, vp = Level(0, NONE, AE), Level(1, NONE, VP)
    c2: Cond = ("c2", "ratchet", 2)
    v1, v2 = _versioned(1, "DEC-0001", 1, vp), _versioned(2, "DEC-0001", 2, ae, (c2,))
    ok = _resolved(3, "DEC-0001", "c2", "confirmed_lower_level")
    v3 = _versioned(4, "DEC-0001", 3, ae, (c2,))  # the re-run, at the confirmed level
    lowered = FloorState("DR-1", ae, ("DEC-0001", 2), PersonRef.model_validate(MICHAEL))
    assert floor_from([v1, v2, ok, v3], "DR-1") == floor_from([v1, v2, v3, ok], "DR-1") == lowered
    up = _versioned(4, "DEC-0001", 3, vp, (c2,))  # the re-run is back in the VP Sales band
    again = FloorState("DR-1", vp, ("DEC-0001", 3), None)
    assert floor_from([v1, v2, ok, up], "DR-1") == floor_from([v1, v2, up, ok], "DR-1") == again
    # only a ratchet's condition counts, and only on its own decision
    held = FloorState("DR-1", vp, ("DEC-0001", 1), None)
    conflict = _versioned(2, "DEC-0001", 2, ae, (("c1", "input_conflict", 1), c2))
    c1_ok = _resolved(3, "DEC-0001", "c1", "confirmed_lower_level")
    assert floor_from([v1, conflict, c1_ok], "DR-1") == held
    elsewhere = _resolved(3, "DEC-0009", "c2", "confirmed_lower_level")
    assert floor_from([v1, v2, elsewhere], "DR-1") == held


def test_a_round_lowers_the_floor_only_once_every_confirmer_has_confirmed() -> None:
    """R26: a version below the floor opens one ratchet condition per confirmer (a round). The
    floor drops to that version's level only when every condition the round opened is confirmed,
    wherever the resolutions are logged; a confirmation in an unfinished round lowers nothing."""
    dof_vp, fm = Level(2, frozenset({VP}), "Director of Finance"), Level(1, NONE, "Finance Manager")
    pair: tuple[Cond, ...] = (("c1", "ratchet", 2), ("c2", "ratchet", 2))
    v1, v2 = _versioned(1, "DEC-0001", 1, dof_vp), _versioned(2, "DEC-0001", 2, fm, pair)
    one = _resolved(3, "DEC-0001", "c1", "confirmed_lower_level")
    v3 = _versioned(4, "DEC-0001", 3, fm, pair)  # c1 resolved, c2 still open
    two = _resolved(5, "DEC-0001", "c2", "confirmed_lower_level")
    v4 = _versioned(6, "DEC-0001", 4, fm, pair)
    held = FloorState("DR-1", dof_vp, ("DEC-0001", 1), None)
    assert floor_from([v1, v2, one, v3], "DR-1") == floor_from([v1, v2, v3, one], "DR-1") == held
    lowered = FloorState("DR-1", fm, ("DEC-0001", 2), PersonRef.model_validate(MICHAEL))
    assert floor_from([v1, v2, one, v3, two, v4], "DR-1") == lowered
    assert floor_from([v1, v2, one, v3, v4, two], "DR-1") == lowered
    # a new round at another level: c1's confirmation doesn't count towards it
    ae = Level(0, NONE, AE)
    fresh: tuple[Cond, ...] = (("c1", "ratchet", 2), ("c3", "ratchet", 4), ("c4", "ratchet", 4))
    v4 = _versioned(6, "DEC-0001", 4, ae, fresh)
    c4 = _resolved(7, "DEC-0001", "c4", "confirmed_lower_level")
    assert floor_from([v1, v2, one, v3, v4, c4], "DR-1") == held


def ids(people: list[PersonRef]) -> list[str]:
    return [p.id for p in people]


def test_confirmers_pass_up(org: Org) -> None:
    ae = Level(0, NONE, AE)
    assert ids(confirmers(org, "EMP-200", Level(1, frozenset(), "VP Sales"), ae)) == ["EMP-300"]
    assert ids(confirmers(org, "EMP-101", Level(1, NONE, VP), ae)) == ["EMP-200"]
    assert ids(confirmers(org, "EMP-101", Level(2, NONE, CRO), ae)) == ["EMP-300"]
    assert [p.model_dump() for p in confirmers(org, "EMP-101", Level(1, NONE, VP), ae)] == [MICHAEL]
    with pytest.raises(ValueError, match="requester"):  # nobody above the CRO: never the requester
        confirmers(org, "EMP-300", Level(2, NONE, CRO), ae)


def test_confirmers_add_each_dropped_concurrence(org: Org) -> None:
    """R26 (contract v1.3): the floor's band holder, then the holder of each concurrence the floor
    required and the level drops, by title; a concurrence the level keeps asks nobody. Each is
    passed up the same way, and one person never confirms twice: that fails closed."""
    dof, fm = "Director of Finance", "Finance Manager"
    floor = Level(2, frozenset({VP, CRO}), dof)
    assert ids(confirmers(org, "EMP-101", floor, Level(1, NONE, fm))) == [
        "EMP-402", "EMP-300", "EMP-200"]  # fmt: skip
    assert ids(confirmers(org, "EMP-101", floor, Level(2, frozenset({CRO}), dof))) == [
        "EMP-402", "EMP-200"]  # fmt: skip
    # Michael asks: the VP Sales concurrence passes up to David Morgan, who holds the CRO's too
    with pytest.raises(ValueError, match="never the same person"):
        confirmers(org, "EMP-200", floor, Level(1, NONE, fm))


# -- self-sourced basis ---------------------------------------------------------------------------
def test_self_sourced_basis_flags_only_the_requesters_later_edits(
    org: Org, sarah: Actor, michael: Actor, dealdesk: Actor
) -> None:
    """R23: after the subject's first ask, by the requester or an agent acting for them, on a basis
    field, and only where the value changed. Every final row is one the replay knows (15%)."""
    edit(org, sarah, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"})
    edit(org, sarah, "discount_requests", "DR-9001", {"requested_discount_pct": "15.0"})
    first = ask(org, sarah, "DR-9001")
    assert first.flags == []  # Sarah's edits came before the request
    withdraw(org, first)
    edit(org, michael, "discount_requests", "DR-9001", {"requested_discount_pct": "8.0"})
    edit(org, sarah, "discount_requests", "DR-9001", {"list_value_usd": "250000"})  # not basis
    at = edit(org, dealdesk, "discount_requests", "DR-9001", {"requested_discount_pct": "15.0"})
    edit(org, sarah, "discount_requests", "DR-9001", {"request_date": "2026-09-23"})  # no change
    second = ask(org, sarah, "DR-9001")
    assert [dump(f) for f in second.flags] == [{
        "code": "self_sourced_basis",
        "text": f"DR-9001 requested_discount changed from 0.08 to 0.15 by Deal Desk Agent for "
                f"Sarah Chen at {hhmm(at)}, after the request.",
        "routes": False, "about": ["DR-9001"],
    }]  # fmt: skip
    assert second.conditions == []  # at the floor: the flag stops nothing


# -- revoked ------------------------------------------------------------------------------------
def test_revoked_flags_name_documents_revoked_by_as_of() -> None:
    entries: list[dict[str, Any]] = [
        {"doc_id": "A", "revoked_on": "2026-09-01"}, {"doc_id": "B", "revoked_on": "2026-09-24"},
        {"doc_id": "C"}, {"doc_id": "D", "revoked_on": None},
    ]  # fmt: skip
    assert revoked_by(entries, date(2026, 9, 23)) == {"A": "2026-09-01"}
    assert revoked_by(entries, date(2026, 9, 1)) == {"A": "2026-09-01"}  # on the day
    assert revoked_by(entries, date(2026, 8, 31)) == {}

    def flag(code: FlagCode, doc: str) -> Flag:
        return Flag(code=code, text=f"{doc}: not registered; set aside until it is", routes=False,
                    about=[doc])  # fmt: skip

    kernel = [flag("set_aside", "A"), flag("set_aside", "B"), flag("incident", "A"),
              flag("set_aside", "A"), flag("set_aside", "C")]  # fmt: skip
    assert [dump(f) for f in revoked_flags(kernel, revoked_by(entries, date(2026, 9, 23)))] == [{
        "code": "revoked", "text": "A was revoked on 2026-09-01; decided without it.",
        "routes": False, "about": ["A"]}]  # fmt: skip


def test_revoked_flag_on_asking(org: Org, sarah: Actor, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nothing is revoked at bootstrap (revocations come with the register queue), so the register
    here carries two: one on or before `as_of`, one after it. The kernel's own register is left as
    it is, so the replay holds; the kernel is said to have set both documents aside."""
    reg = org.kernel_register()
    state = copy.deepcopy(org.register_state())
    for e in state.entries:
        if e["doc_id"] == "GRT-ACME-2026":
            e["revoked_on"] = "2026-09-01"
        if e["doc_id"] == "CREDIT-POLICY-2026":
            e["revoked_on"] = "2026-10-01"  # after as_of: not revoked for this decision
    monkeypatch.setattr(org, "register_state", lambda: state)
    monkeypatch.setattr(org, "kernel_register", lambda: reg)
    real = _lab.decide

    def set_aside(kind: _lab.DecisionType, **kw: Any) -> _lab.KernelResult:
        kr = real(kind, **kw)
        items = [{"code": "set_aside", "text": f"{d}: not registered; set aside until it is",
                  "routes": False} for d in ("GRT-ACME-2026", "CREDIT-POLICY-2026")]  # fmt: skip
        return dataclasses.replace(kr, flag_items=[*kr.flag_items, *items])

    monkeypatch.setattr(_lab, "decide", set_aside)
    v = ask(org, sarah, "DR-9001")
    assert [f.code for f in v.flags] == ["set_aside", "set_aside", "revoked"]
    assert dump(v.flags[-1]) == {"code": "revoked", "routes": False, "about": ["GRT-ACME-2026"],
                                 "text": "GRT-ACME-2026 was revoked on 2026-09-01; decided "
                                         "without it."}  # fmt: skip
