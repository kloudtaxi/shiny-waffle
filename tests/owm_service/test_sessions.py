from __future__ import annotations

import hashlib
from datetime import timedelta
from pathlib import Path

import pytest

from owm_service.config import Settings, load_settings
from owm_service.errors import NotFound, Unauthenticated
from owm_service.models import AgentActor, FunctionParty, PersonActor
from owm_service.org import Org
from owm_service.sessions import Mandates, Sessions, suspended

FIXTURE = Path(__file__).resolve().parents[2] / "lab/owm_service/fixtures"


def test_person_session(org: Org) -> None:
    tok, a = Sessions(org).open_person("EMP-101")
    assert Sessions(org).resolve(tok) == a
    assert isinstance(a, PersonActor) and a.person.function == "Sales"


def test_agent_session_carries_mandate_and_principal(org: Org) -> None:
    tok, a = Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")
    assert isinstance(a, AgentActor)
    assert a.on_behalf_of is not None and a.on_behalf_of.id == "EMP-101"
    assert a.mandate is not None and a.mandate.doc_id == "MANDATE-DEALDESK-2026"
    assert a.version == "sha256:demo-dealdesk-v1" and a.name == "Deal Desk Agent"
    assert Sessions(org).resolve(tok) == a


def test_unknown_agent_is_external_without_mandate(org: Org) -> None:
    _, a = Sessions(org).open_agent("AGT-OTHER", "EMP-101")
    assert isinstance(a, AgentActor) and a.mandate is None and a.version == "sha256:unknown"


def test_unknown_people_are_not_found(org: Org) -> None:
    with pytest.raises(NotFound):
        Sessions(org).open_person("EMP-nope")
    with pytest.raises(NotFound):
        Sessions(org).open_agent("AGT-DEALDESK", "EMP-nope")


def test_agents_act_as_nobody(org: Org) -> None:
    s = Sessions(org)
    _, agent = s.open_agent("AGT-DEALDESK", "EMP-101")
    _, person = s.open_person("EMP-101")
    assert s.acting_as(agent) == frozenset()
    assert s.acting_as(person) == frozenset({"EMP-101"})


@pytest.mark.parametrize("tok", [None, "nope"])
def test_missing_or_unknown_token_is_unauthenticated(org: Org, tok: str | None) -> None:
    with pytest.raises(Unauthenticated):
        Sessions(org).resolve(tok)


def test_expired_token(org: Org) -> None:
    s = Sessions(org)
    tok, _ = s.open_person("EMP-101")
    org.clock.set(org.clock.now() + timedelta(hours=12, seconds=1), None)
    with pytest.raises(Unauthenticated):
        s.resolve(tok)


def test_close_revokes(org: Org) -> None:
    s = Sessions(org)
    tok, _ = s.open_person("EMP-101")
    s.close(tok)
    with pytest.raises(Unauthenticated):
        s.resolve(tok)


def test_tokens_survive_a_restart_and_are_not_stored(org: Org) -> None:
    tok, a = Sessions(org).open_person("EMP-101")
    assert Sessions(org).resolve(tok) == a
    ev = org.log.read(org.org_id, kinds=["session.opened"])[0]
    assert ev.payload["token_sha256"] == hashlib.sha256(tok.encode()).hexdigest()
    assert ev.stream == f"session:{ev.payload['token_sha256'][:12]}"
    assert tok not in str(ev.payload) and tok not in ev.stream


def test_suspension_by_agent_or_version(tmp_path: Path, org: Org) -> None:
    def settings(spec: str) -> Settings:
        return load_settings({"OWM_STATE_DIR": str(tmp_path / "s"), "OWM_SUSPENDED": spec})

    _, agent = Sessions(org).open_agent("AGT-DEALDESK", "EMP-101")
    _, person = Sessions(org).open_person("EMP-101")
    assert suspended(agent, settings("AGT-DEALDESK"))
    assert suspended(agent, settings("AGT-DEALDESK@sha256:demo-dealdesk-v1"))
    assert not suspended(agent, settings("AGT-DEALDESK@sha256:other"))
    assert not suspended(agent, settings(""))
    assert not suspended(person, settings("AGT-DEALDESK"))


def test_me_returns_function(org: Org) -> None:
    s = Sessions(org)
    _, a = s.open_person("EMP-101")
    me = s.me(a)
    assert isinstance(me.actor, PersonActor) and me.actor.person.function == "Sales"


def test_mandate_entry(org: Org) -> None:
    m = Mandates(org)
    e = m.entry("MANDATE-DEALDESK-2026")
    assert e.kind == "agent_mandate" and e.status == "in_force"
    assert isinstance(e.registered_by, FunctionParty) and e.registered_by.function == "Sales"
    assert isinstance(e.approved_by, FunctionParty)
    assert e.file.source_id == "fixtures/mandate-dealdesk-2026.md" and e.file.matches
    text = (FIXTURE / "mandate-dealdesk-2026.md").read_bytes()
    assert e.sha256 == hashlib.sha256(text).hexdigest()
    terms = m.for_agent("AGT-DEALDESK")
    assert terms is not None and terms.may_do[0].limits == {"per_day": 200}
    assert m.for_agent("AGT-OTHER") is None
    with pytest.raises(NotFound):
        m.entry("MANDATE-NOPE")
