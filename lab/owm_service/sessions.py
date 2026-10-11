"""Demo sessions, the Deal Desk mandate fixture, suspension and `me` (spec §3.1, contract §9).

A bearer token maps to an `Actor`: a person from the HR export, or an agent acting for a person.
Sessions live in the org's event log (`session.opened`, `session.closed`) on a stream named for a
prefix of the token's sha256; the raw token is never stored. Expiry is 12 h of demo time.

The mandate is a service fixture held outside the registrar's state; `Mandates.entry` shapes it
as a register entry so it can be shown beside the registered documents.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict

from .config import Settings
from .errors import NotFound, Unauthenticated
from .models import (
    Actor,
    AgentActor,
    FileCheck,
    FunctionParty,
    Mandate,
    MeResponse,
    PersonActor,
    PersonRef,
    RegisterEntry,
)
from .org import Org

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SESSION_TTL = timedelta(hours=12)
UNKNOWN_VERSION = "sha256:unknown"
_BOOTSTRAP = FunctionParty(
    kind="function", function="Sales", note="bootstrap import (service fixture)"
)


class _T(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AgentInfo(_T):
    id: str
    name: str
    purpose: str
    runtime: Literal["agno", "external"]


class Owner(_T):
    function: str
    accountable: PersonRef


class MayAsk(_T):
    decision_type: Literal["discount", "credit", "sla"]
    scope: str


class MayDo(_T):
    action: str
    decision_types: list[Literal["discount", "credit", "sla"]]
    match: dict[str, Literal["exact", "at_most"]]
    limits: dict[str, float] | None


class MandateTerms(_T):
    """Contract §9 AgentMandateTerms."""

    agent: AgentInfo
    owner: Owner
    principal: Literal["delegated", "service"]
    team: str | None
    versions: list[str]
    may_ask: list[MayAsk]
    may_do: list[MayDo]
    may_propose: list[Literal["register_change", "procedure", "identity_merge"]]


def _sha(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _stream(sha: str) -> str:
    return f"session:{sha[:12]}"


class Mandates:
    def __init__(self, org: Org) -> None:
        self.org = org
        raw: list[dict[str, Any]] = yaml.safe_load((FIXTURES / "mandates.yaml").read_text())
        self._raw = {e["doc_id"]: e for e in raw}
        self._terms = {d: self._load(e["terms"]) for d, e in self._raw.items()}

    def _load(self, terms: dict[str, Any]) -> MandateTerms:
        """The fixture names the accountable person by id; the contract carries a PersonRef."""
        owner = dict(terms["owner"])
        owner["accountable"] = self.org.people.ref(owner["accountable"]).model_dump()
        return MandateTerms.model_validate({**terms, "owner": owner})

    def entry(self, doc_id: str) -> RegisterEntry:
        if doc_id not in self._raw:
            raise NotFound(f"mandate {doc_id}")
        e = self._raw[doc_id]
        text = (FIXTURES / e["text_file"]).read_bytes()
        sha = hashlib.sha256(text).hexdigest()
        return RegisterEntry(
            doc_id=doc_id,
            kind=e["kind"],
            title=e["title"],
            owning_function=self._terms[doc_id].owner.function,
            scope="company",
            sha256=sha,
            effective_from=e["effective_from"],
            effective_to=e["effective_to"],
            relations=[],
            terms=self._terms[doc_id].model_dump(),
            proposed_by=None,
            registered_by=_BOOTSTRAP,
            approved_by=_BOOTSTRAP,
            registered_on=e["effective_from"],
            approved_on=e["effective_from"],
            revoked=None,
            status="in_force",
            superseded_by=None,
            file=FileCheck(
                sha256=sha, matches=True, detail=None, source_id=f"fixtures/{e['text_file']}"
            ),
        )

    def for_agent(self, agent_id: str) -> MandateTerms | None:
        return next((t for t in self._terms.values() if t.agent.id == agent_id), None)

    def doc_id_for(self, agent_id: str) -> str | None:
        return next((d for d, t in self._terms.items() if t.agent.id == agent_id), None)


class Sessions:
    def __init__(self, org: Org) -> None:
        self.org = org
        self.mandates = Mandates(org)

    def _open(self, actor: Actor) -> str:
        token = secrets.token_urlsafe(32)
        sha = _sha(token)
        now = self.org.clock.now()
        data = actor.model_dump(mode="json")
        with self.org.log.transaction() as tx:
            self.org.log.append(
                tx,
                at=now,
                org=self.org.org_id,
                stream=_stream(sha),
                kind="session.opened",
                actor=data,
                payload={
                    "token_sha256": sha,
                    "actor": data,
                    "expires_at": (now + SESSION_TTL).isoformat(),
                },
            )
        return token

    def open_person(self, person_id: str) -> tuple[str, Actor]:
        actor = PersonActor(kind="person", person=self.org.people.ref(person_id))
        return self._open(actor), actor

    def open_agent(
        self, agent_id: str, on_behalf_of: str, version: str | None = None
    ) -> tuple[str, Actor]:
        principal = self.org.people.ref(on_behalf_of)
        terms = self.mandates.for_agent(agent_id)
        doc_id = self.mandates.doc_id_for(agent_id)
        if version is None:
            version = terms.versions[0] if terms and terms.versions else UNKNOWN_VERSION
        actor = AgentActor(
            kind="agent",
            id=agent_id,
            name=terms.agent.name if terms else agent_id,
            version=version,
            on_behalf_of=principal,
            mandate=Mandate(doc_id=doc_id) if doc_id else None,
        )
        return self._open(actor), actor

    def resolve(self, token: str | None) -> Actor:
        if not token:
            raise Unauthenticated
        sha = _sha(token)
        events = self.org.log.read(self.org.org_id, stream=_stream(sha))
        opened = next(
            (e for e in events if e.kind == "session.opened" and e.payload["token_sha256"] == sha),
            None,
        )
        if opened is None or any(e.kind == "session.closed" for e in events):
            raise Unauthenticated
        if self.org.clock.now() > datetime.fromisoformat(opened.payload["expires_at"]):
            raise Unauthenticated
        a = opened.payload["actor"]
        return (
            PersonActor.model_validate(a) if a["kind"] == "person" else AgentActor.model_validate(a)
        )

    def close(self, token: str) -> None:
        sha = _sha(token)
        if not any(
            e.kind == "session.opened"
            for e in self.org.log.read(self.org.org_id, stream=_stream(sha))
        ):
            return
        with self.org.log.transaction() as tx:
            self.org.log.append(
                tx,
                at=self.org.clock.now(),
                org=self.org.org_id,
                stream=_stream(sha),
                kind="session.closed",
                actor=None,
                payload={"token_sha256": sha},
            )

    def acting_as(self, actor: Actor) -> frozenset[str]:
        return frozenset({actor.person.id}) if isinstance(actor, PersonActor) else frozenset()

    def me(self, actor: Actor) -> MeResponse:
        return MeResponse(actor=actor)


def suspended(actor: Actor, settings: Settings) -> bool:
    """True when the agent (`AGT-X`) or its version (`AGT-X@<sha>`) is in OWM_SUSPENDED."""
    if not isinstance(actor, AgentActor):
        return False
    return actor.id in settings.suspended or f"{actor.id}@{actor.version}" in settings.suspended
