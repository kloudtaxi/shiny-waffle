"""One `Service` per app, and the dependencies every route shares: the service itself, and the
session's actor (spec §8.1). The core never imports FastAPI; this module and the routers do."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, Request

from .clearance import Clearances
from .config import Settings
from .decisions import Decisions
from .models import AgentActor, PersonActor
from .org import Org
from .register_queue import RegisterQueue
from .sessions import Sessions


class Service:
    """One organisation and the core over it. `reset` archives the event log and starts afresh:
    a new `Org`, so no cache (sessions, the overlay, the register) outlives the old log."""

    org: Org
    sessions: Sessions
    decisions: Decisions
    clearances: Clearances
    register: RegisterQueue

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._open()

    def _open(self) -> None:
        self.org = Org(self.settings)
        self.sessions = Sessions(self.org)
        self.decisions = Decisions(self.org)
        self.clearances = Clearances(self.org, self.decisions, self.sessions.mandates)
        self.register = RegisterQueue(self.org)

    def reset(self) -> str:
        """Rename the log aside with a timestamp, open a fresh org; the archived file's name.
        A request already running when this happens may still be using the old org."""
        with self._lock:
            archived = self.org.log.archive(datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
            self._open()
        return archived.name


def service(request: Request) -> Service:
    svc: Service = request.app.state.owm
    return svc


def bearer(authorization: str | None) -> str | None:
    """The token from `Authorization: Bearer <token>`; None for anything else."""
    scheme, _, token = (authorization or "").partition(" ")
    return (token.strip() or None) if scheme.lower() == "bearer" else None


def session(
    request: Request, authorization: Annotated[str | None, Header()] = None
) -> PersonActor | AgentActor:
    """The session's actor (spec §8.1); Unauthenticated (401) without a valid token."""
    return service(request).sessions.resolve(bearer(authorization))


Svc = Annotated[Service, Depends(service)]
Me = Annotated[PersonActor | AgentActor, Depends(session)]
