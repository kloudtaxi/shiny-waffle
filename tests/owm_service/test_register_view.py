"""The register's read side and its settings (B-06 Task 17; spec §7.2; contract §4.1, §4.4)."""

from __future__ import annotations

import copy
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from owm_service import _lab
from owm_service.config import load_settings
from owm_service.decisions import Decisions
from owm_service.errors import NotFound, Refused
from owm_service.models import Actor, FunctionParty, PersonRef, RegisterEntry
from owm_service.org import Org
from owm_service.register_view import _status, entry, put_settings, settings, text, view
from owm_service.sessions import Sessions

from . import harness


def _person(org: Org, emp: str) -> Actor:
    return Sessions(org).open_person(emp)[1]


@pytest.fixture
def david(org: Org) -> Actor:
    return _person(org, "EMP-300")


@pytest.fixture
def michael(org: Org) -> Actor:
    return _person(org, "EMP-200")


def _by_id(entries: list[RegisterEntry], doc_id: str) -> RegisterEntry:
    return next(e for e in entries if e.doc_id == doc_id)


def test_bootstrap_view(org: Org) -> None:
    v = view(org, None)
    assert v.version == 17 and any(e.doc_id == "MANDATE-DEALDESK-2026" for e in v.entries)
    assert v.clock.startswith("2026-09-23T09:00:00")  # the org clock, with its offset
    pp = next(s for s in v.series if s.kind == "pricing_policy")
    assert pp.entries == ["PRICING-POLICY-2025", "PRICING-POLICY-2026", "PRICING-POLICY-2027"]
    assert pp.in_force == "PRICING-POLICY-2026"  # at the default clock, 2026-09-23
    assert v.settings.on_mismatch == "use_registered"
    assert sorted(c.decision_type for c in v.coverage) == ["credit", "discount", "sla"]


def test_every_entry_is_in_exactly_one_series(org: Org) -> None:
    v = view(org, None)
    listed = [d for s in v.series for d in s.entries]
    assert sorted(listed) == sorted(e.doc_id for e in v.entries)  # the mandate included
    assert len(listed) == len(set(listed))
    one = next(s for s in v.series if s.entries == ["MANDATE-DEALDESK-2026"])
    assert one.in_force == "MANDATE-DEALDESK-2026"


def test_status_as_of(org: Org) -> None:
    def status(doc: str, on: str) -> str:
        return _by_id(view(org, date.fromisoformat(on)).entries, doc).status

    assert status("PRICING-POLICY-2025", "2025-09-23") == "in_force"
    assert status("PRICING-POLICY-2026", "2025-09-23") == "scheduled"
    assert status("PRICING-POLICY-2025", "2026-09-23") == "superseded"
    assert status("PRICING-POLICY-2026", "2026-09-23") == "in_force"
    assert status("PRICING-POLICY-2027", "2026-09-23") == "scheduled"
    v = view(org, date(2026, 9, 23))
    assert _by_id(v.entries, "PRICING-POLICY-2025").superseded_by == "PRICING-POLICY-2026"
    assert _by_id(v.entries, "PRICING-POLICY-2026").superseded_by is None
    old = view(org, date(2025, 9, 23))
    assert next(s for s in old.series if s.kind == "pricing_policy").in_force == (
        "PRICING-POLICY-2025"
    )


def test_expired_when_nothing_follows(org: Org) -> None:
    v = view(org, date(2030, 6, 1))
    assert _by_id(v.entries, "CREDIT-POLICY-2026").status == "expired"


def _entries(org: Org) -> list[dict[str, Any]]:
    """Copies of the registrar's entries: a test edits these, never the cached state."""
    return copy.deepcopy(org.register_state().entries)


def _one(entries: list[dict[str, Any]], doc_id: str) -> dict[str, Any]:
    return next(e for e in entries if e["doc_id"] == doc_id)


def test_window_boundary_days(org: Org) -> None:
    es = _entries(org)
    old, new = _one(es, "PRICING-POLICY-2025"), _one(es, "PRICING-POLICY-2026")
    last = date.fromisoformat(old["effective_to"])
    assert date.fromisoformat(new["effective_from"]) == last + timedelta(days=1)
    assert _status(old, es, last) == ("in_force", None)  # its last day, successor not yet
    assert _status(old, es, last + timedelta(days=1)) == ("superseded", new["doc_id"])  # R47
    assert _status(new, es, last) == ("scheduled", None)
    assert _status(new, es, last + timedelta(days=1)) == ("in_force", None)
    # nothing follows: the day after the window is `expired`
    alone = [e for e in es if e["doc_id"] != "PRICING-POLICY-2026"]
    assert _status(_one(alone, "PRICING-POLICY-2025"), alone, last) == ("in_force", None)
    day_after = last + timedelta(days=1)
    assert _status(_one(alone, "PRICING-POLICY-2025"), alone, day_after) == ("expired", None)


def test_revoked_on_boundary_day(org: Org) -> None:
    es = _entries(org)
    new = _one(es, "PRICING-POLICY-2026")
    new["revoked_on"] = "2026-03-01"
    assert _status(new, es, date(2026, 2, 28))[0] == "in_force"
    assert _status(new, es, date(2026, 3, 1)) == ("revoked", None)
    assert _status(new, es, date(2026, 3, 2)) == ("revoked", None)


def test_revoked_successor_restores_its_predecessor(org: Org) -> None:
    es = _entries(org)
    old, new = _one(es, "PRICING-POLICY-2025"), _one(es, "PRICING-POLICY-2026")
    new["revoked_on"] = new["effective_from"]  # revoked the day it starts: never in force
    on = date(2026, 6, 1)
    assert _status(old, es, on) == ("expired", None)  # past its own window
    old["effective_to"] = None  # an open window: it is back in force
    assert _status(old, es, on) == ("in_force", None)
    es2 = _entries(org)
    _one(es2, "PRICING-POLICY-2025")["effective_to"] = None
    assert _status(_one(es2, "PRICING-POLICY-2025"), es2, on) == ("superseded", new["doc_id"])


def test_past_window_with_live_successor_is_superseded(org: Org) -> None:
    v = view(org, date(2026, 9, 23))
    assert _by_id(v.entries, "PRICING-POLICY-2025").status == "superseded"


def test_revoked_from_its_date(org: Org) -> None:
    victim = next(e for e in org.register_state().entries if e["doc_id"] == "PRICING-POLICY-2026")
    victim.update(
        revoked_on="2026-03-01",
        revoked_by="Michael Torres (EMP-200, VP Sales)",
        revocation_approved_by="David Morgan (EMP-300, Chief Revenue Officer)",
    )
    after = _by_id(view(org, date(2026, 6, 1)).entries, "PRICING-POLICY-2026")
    assert after.status == "revoked" and after.revoked is not None
    assert after.revoked.by.id == "EMP-200" and after.revoked.approved_by.id == "EMP-300"
    before = _by_id(view(org, date(2026, 2, 1)).entries, "PRICING-POLICY-2026")
    assert before.status == "in_force"


def test_parties_owner_scope(org: Org) -> None:
    v = view(org, None)
    e = _by_id(v.entries, "CREDIT-POLICY-2025")
    assert isinstance(e.registered_by, PersonRef) and e.registered_by.id == "EMP-401"
    assert e.owning_function == "Finance" and e.scope == "company"
    assert e.proposed_by is None
    parties = [x.registered_by for x in v.entries if isinstance(x.registered_by, FunctionParty)]
    assert parties and parties[0].note.startswith("by function")


def test_file_check_matches(org: Org) -> None:
    e = _by_id(view(org, None).entries, "CREDIT-POLICY-2025")
    assert e.file.matches and e.file.detail is None and e.file.sha256 == e.sha256


def test_source_id_is_a_corpus_path(org: Org) -> None:
    e = _by_id(view(org, None).entries, "CREDIT-POLICY-2025")
    assert e.file.source_id == "documents/credit_policy_2025.md"
    assert (_lab.corpus_root("base") / e.file.source_id).exists()


def test_title_never_empty(org: Org) -> None:
    v = view(org, None)
    assert all(e.title for e in v.entries)
    assert _by_id(v.entries, "CREDIT-POLICY-2025").title != "CREDIT-POLICY-2025"


def test_entry_and_text(org: Org) -> None:
    e = entry(org, "PRICING-POLICY-2026")
    assert e.doc_id == "PRICING-POLICY-2026"
    assert _lab.fingerprint(text(org, "PRICING-POLICY-2026")) == e.sha256
    assert entry(org, "MANDATE-DEALDESK-2026").kind
    with pytest.raises(NotFound):
        entry(org, "NOPE")
    with pytest.raises(NotFound):
        text(org, "NOPE")


def test_differing_copy_on_file(tmp_path: Path) -> None:
    org = Org(load_settings({"OWM_STATE_DIR": str(tmp_path / "s")}))
    root = harness.attacked_roots("F1")["base"]
    org.evidence = _lab.make_evidence(root, org._overlay)
    entries = view(org, None).entries
    bad = [e for e in entries if not e.file.matches]
    assert bad and all(e.file.detail in ("differs", "missing") for e in bad)
    assert any(e.file.detail == "differs" for e in bad)
    assert all(e.file.detail is None for e in entries if e.file.matches)


def test_settings_put_executive_only(org: Org, david: Actor, michael: Actor) -> None:
    assert settings(org) == {"on_mismatch": "use_registered"}
    with pytest.raises(Refused) as e:
        put_settings(org, michael, {"on_mismatch": "route"})
    assert e.value.status == 422 and e.value.refusals[0].rule == "RR-4"
    assert org.on_mismatch() == "use_registered"
    assert put_settings(org, david, {"on_mismatch": "route"}) == {"on_mismatch": "route"}
    assert org.on_mismatch() == "route" and view(org, None).settings.on_mismatch == "route"
    put_settings(org, david, {"on_mismatch": "use_registered"})
    assert org.on_mismatch() == "use_registered"
    events = org.log.read(org.org_id, stream="register:settings")
    assert [x.kind for x in events] == ["settings.changed"] * 2


def test_settings_agent_is_rr2_and_bad_bodies_422(org: Org, david: Actor) -> None:
    agent = Sessions(org).open_agent("AGT-DEALDESK", "EMP-300")[1]
    with pytest.raises(Refused) as e:
        put_settings(org, agent, {"on_mismatch": "route"})
    assert e.value.refusals[0].rule == "RR-2"
    for body in ({"on_mismatch": "maybe"}, {}, {"on_mismatch": "route", "x": 1}):
        with pytest.raises(Refused) as r:
            put_settings(org, david, body)
        assert r.value.status == 422
    assert org.log.read(org.org_id, stream="register:settings") == []


def test_content_store_serves_bytes_exactly(org: Org) -> None:
    crlf = "# T\r\nline two  \r\n\r\nend\r\n"
    sha = org.put_register_text(crlf)
    assert (org.register_store / f"{sha}.md").read_bytes() == crlf.encode()
    assert org.register_text(sha) == crlf
    assert not list(org.register_store.glob(".*.part"))


def test_failed_write_leaves_no_part_file(org: Org, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(src: object, dst: object) -> None:
        raise OSError("disk")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        org.put_register_text("# x\n")
    assert not list(org.register_store.glob(".*.part"))


def _f1_org(tmp_path: Path) -> Org:
    """S22's org, its copies on file swapped for set F's F1 attack corpus."""
    org = harness.scenario_org("S22", tmp_path)
    org.evidence = _lab.make_evidence(
        harness.attacked_roots("F1")[harness.corpus("S22")], org._overlay
    )
    return org


def test_default_setting_does_not_route(tmp_path: Path) -> None:
    org = _f1_org(tmp_path)  # the counterfactual: the same mismatch, the default setting
    rec = Decisions(org).ask(harness.asker(org, "S22"), harness.request_for("S22"))
    assert not rec.routed and not any(f.code == "routed" for f in rec.flags)
    assert not org.engine.calls.exists() or org.engine.calls.read_text() == ""


def test_route_mode_changes_decisions(tmp_path: Path) -> None:
    org = _f1_org(tmp_path)
    put_settings(org, _person(org, "EMP-300"), {"on_mismatch": "route"})
    assert org.on_mismatch() == "route"
    rec = Decisions(org).ask(harness.asker(org, "S22"), harness.request_for("S22"))
    assert rec.outcome is None and rec.gated_outcome == "REQUEST_EVIDENCE" and rec.routed
    assert any(f.code == "routed" and f.routes for f in rec.flags)
    assert not org.engine.calls.exists() or org.engine.calls.read_text() == ""  # $0: replay only
