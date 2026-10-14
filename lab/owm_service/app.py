"""The HTTP surface (spec §11): FastAPI over the core, with the contract's status codes (§3.4).

- **Contract routes, under `/api/v1`.** Every one needs a session: `Authorization: Bearer
  <token>`. A missing, unknown, closed or expired token is 401, never a default user. It serves
  `GET /me`, the decision and clearance routes, `GET /approvals` and, for the register, the
  entries and their text, the settings, the change queue and the procedures (spec §11).
- **Lab-only routes, under `/lab`,** sit visibly outside the contract and are mounted only when
  `OWM_LAB_ROUTES` is on: demo sign-in, systems-of-record edits and inserts, the demo adapter,
  the clock and a reset. Anyone who can reach them can sign in as anyone, so a deployment keeps
  them off or reachable only from web-next's server.
- **`GET /healthz`** is always there.

Responses are the contract's models, serialised with `exclude_unset` (ruling R13): an absent
`?:` field stays absent and a required nullable one is null. Errors map as follows; anything else
is a bug and surfaces as a 500, with no catch-all to hide it:
- `Refused` → its status (403 RR-1; 409 DC-5, DC-6, RR-13 or a moved write; 422 any other rule),
  body `{"refusals": [...]}`;
- `NotFound` → 404 and `Unauthenticated` → 401, body `{"error", "detail"}`;
- `CannotDecide` and `JevUnavailable` → 503, body `{"error": "cannot_decide", "detail"}`;
- a body that fails validation, an extra field such as `as_of` included → FastAPI's own 422.
A clearance or redemption refusal is an answer, so it is 200.

The register and procedure routes live in `app_register.py`, the `Service` and the session
dependencies in `service.py`. One `Service` per app holds the org and the core over it;
`/lab/reset` archives the org's event log and swaps in a fresh org. The core never imports
FastAPI; the HTTP modules are its only users.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Final

from fastapi import APIRouter, Body, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from . import _lab, approvals, history, lab_adapter
from .app_register import router as register_router
from .config import Settings, load_settings
from .errors import CannotDecide, NotFound, Refused, Unauthenticated
from .models import (
    Actor,
    ApprovalsView,
    ClearanceAttempt,
    ClearanceRequest,
    Cleared,
    DecisionEvent,
    DecisionRecord,
    DecisionRequest,
    DecisionState,
    DecisionType,
    DryRun,
    MeResponse,
    NotCleared,
    NotRedeemed,
    Page,
    Redeemed,
    RedeemRequest,
    Refusal,
    Refusals,
    ReportRequest,
    ReportResponse,
    RerunRequest,
    ResolveRequest,
    StepRequest,
    one_page,
)
from .service import Me, Service, Svc, bearer, session
from .sor import KEYS

LAB_ACTOR: Final[dict[str, Any]] = {"kind": "system", "id": "lab"}


# -- health -------------------------------------------------------------------------------------
health = APIRouter(tags=["health"])


@health.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# -- the contract, under /api/v1 ----------------------------------------------------------------
api = APIRouter(prefix="/api/v1", dependencies=[Depends(session)], tags=["owm-decisions"])


@api.get("/me", response_model_exclude_unset=True)
def me(svc: Svc, actor: Me) -> MeResponse:
    return svc.sessions.me(actor)


@api.post("/decisions", status_code=201, response_model_exclude_unset=True)
def ask(svc: Svc, actor: Me, body: DecisionRequest) -> DecisionRecord:
    return svc.decisions.ask(actor, body)


@api.get("/decisions", response_model_exclude_unset=True)
def list_decisions(
    svc: Svc, decision_type: DecisionType | None = None, subject: str | None = None,
    state: DecisionState | None = None,
) -> Page[DecisionRecord]:  # fmt: skip
    given = {"decision_type": decision_type, "subject": subject, "state": state}
    return one_page(svc.decisions.list(**{k: v for k, v in given.items() if v is not None}))


@api.get("/decisions/{decision_id}", response_model_exclude_unset=True)
def get_decision(svc: Svc, decision_id: str) -> DecisionRecord:
    return svc.decisions.get(decision_id)


@api.get("/decisions/{decision_id}/versions/{version}", response_model_exclude_unset=True)
def get_version(svc: Svc, decision_id: str, version: int) -> DecisionRecord:
    return svc.decisions.get(decision_id, version)


@api.get("/decisions/{decision_id}/events", response_model_exclude_unset=True)
def decision_events(svc: Svc, decision_id: str) -> Page[DecisionEvent]:
    return one_page(history.events(svc.org, svc.decisions, decision_id))


@api.post("/decisions/{decision_id}/conditions/{condition_id}/resolve",
          response_model_exclude_unset=True)  # fmt: skip
def resolve(
    svc: Svc, actor: Me, decision_id: str, condition_id: str, body: ResolveRequest
) -> DecisionRecord:
    return svc.decisions.resolve(actor, decision_id, condition_id, body)


@api.post("/decisions/{decision_id}/approve", response_model_exclude_unset=True)
def approve(svc: Svc, actor: Me, decision_id: str, body: StepRequest) -> DecisionRecord:
    return svc.decisions.approve(actor, decision_id, body)


@api.post("/decisions/{decision_id}/decline", response_model_exclude_unset=True)
def decline(svc: Svc, actor: Me, decision_id: str, body: StepRequest) -> DecisionRecord:
    return svc.decisions.decline(actor, decision_id, body)


@api.post("/decisions/{decision_id}/withdraw", response_model_exclude_unset=True)
def withdraw(svc: Svc, actor: Me, decision_id: str, body: StepRequest) -> DecisionRecord:
    return svc.decisions.withdraw(actor, decision_id, body)


@api.post("/decisions/{decision_id}/rerun", response_model_exclude_unset=True)
def rerun(svc: Svc, actor: Me, decision_id: str, body: RerunRequest) -> DecisionRecord:
    return svc.decisions.rerun(actor, decision_id, body)


@api.post("/decisions/{decision_id}/clearance", response_model_exclude_unset=True)
def clear(
    svc: Svc, actor: Me, decision_id: str, body: ClearanceRequest
) -> Cleared | NotCleared | DryRun:
    """A real attempt is `Cleared` or `NotCleared`; a dry run is `DryRun` (v1.3, R34)."""
    return svc.clearances.ask(actor, decision_id, body)


@api.get("/decisions/{decision_id}/clearances", response_model_exclude_unset=True)
def clearance_attempts(svc: Svc, decision_id: str) -> Page[ClearanceAttempt]:
    return one_page(svc.clearances.attempts(decision_id))


@api.post("/clearances/{clearance_id}/redeem", response_model_exclude_unset=True)
def redeem(svc: Svc, actor: Me, clearance_id: str, body: RedeemRequest) -> Redeemed | NotRedeemed:
    """The session's actor is recorded beside the executor (ruling R35)."""
    return svc.clearances.redeem(clearance_id, body, by=actor)


@api.post("/clearances/{clearance_id}/report", response_model_exclude_unset=True)
def report(svc: Svc, actor: Me, clearance_id: str, body: ReportRequest) -> ReportResponse:
    return svc.clearances.report(clearance_id, body, by=actor)


@api.get("/approvals", response_model_exclude_unset=True)
def work(svc: Svc, actor: Me) -> ApprovalsView:
    return approvals.view(svc.org, actor)


api.include_router(register_router)  # the register and procedures (spec §11)


# -- lab-only, outside the contract -------------------------------------------------------------
class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PersonSession(_Body):
    person_id: str


class AgentSession(_Body):
    agent_id: str
    on_behalf_of: str
    version: str | None = None


class SessionOpened(_Body):
    token: str
    actor: Actor


class ClockRequest(_Body):
    to: datetime


class AdapterRequest(_Body):
    clearance_id: str
    fail: bool = False


lab = APIRouter(prefix="/lab", tags=["lab (outside the contract)"])


@lab.post("/sessions", status_code=201)
def open_session(svc: Svc, body: PersonSession | AgentSession) -> SessionOpened:
    """Demo sign-in as a person from the HR export, or as an agent acting for one."""
    if isinstance(body, PersonSession):
        token, actor = svc.sessions.open_person(body.person_id)
    else:
        token, actor = svc.sessions.open_agent(body.agent_id, body.on_behalf_of, body.version)
    return SessionOpened(token=token, actor=actor)


@lab.delete("/sessions/current", status_code=204)
def close_session(
    svc: Svc, actor: Me, authorization: Annotated[str | None, Header()] = None
) -> None:
    """Sign out: the session's token stops working (`actor` has already checked it)."""
    svc.sessions.close(bearer(authorization) or "")


@lab.patch("/sor/{table}/{key}")
def edit_row(
    svc: Svc, actor: Me, table: str, key: str, fields: Annotated[dict[str, Any], Body()]
) -> dict[str, Any]:
    """Edit a row of a system of record, as the session's actor (the edit is G-46's threat)."""
    if not fields:
        raise Refused(422, [Refusal(rule="RR-5", detail="Nothing to edit: name a column.")])
    now = svc.org.clock.now()  # before the write: never first read inside one
    with svc.org.log.transaction() as tx:
        svc.org.sor.edit(tx, table, key, fields, actor=actor.model_dump(mode="json"), at=now)
    return {"table": table, "id": key, "row": svc.org.sor.row(table, key)}


@lab.post("/sor/{table}", status_code=201)
def insert_row(
    svc: Svc, actor: Me, table: str, row: Annotated[dict[str, Any], Body()]
) -> dict[str, Any]:
    """Insert a row into a system of record, as the session's actor (the harness seeds with it)."""
    now = svc.org.clock.now()
    with svc.org.log.transaction() as tx:
        svc.org.sor.insert(tx, table, row, actor=actor.model_dump(mode="json"), at=now)
    col = KEYS.get(table)
    stored = svc.org.sor.row(table, str(row[col])) if col else svc.org.sor.table(table)[-1]
    return {"table": table, "row": stored}


@lab.get("/sor/{table}")
def read_table(svc: Svc, table: str) -> dict[str, Any]:
    """A keyed table now, with every edit and insert made to it, in event order (read-only)."""
    if table not in KEYS:
        raise HTTPException(status_code=404, detail=f"No such table: {table}")
    edits: list[dict[str, Any]] = []
    for ev in svc.org.sor.events():
        p = ev.payload
        if p["table"] != table:
            continue
        inserted = ev.kind == "sor.inserted"
        edits.append(
            {
                "seq": ev.seq,
                "kind": ev.kind,
                "key": str(p["row"][KEYS[table]]) if inserted else p["key"],
                "field": None if inserted else p["field"],
                "was": None if inserted else p["was"],
                "now": None if inserted else p["now"],
                "row": p["row"] if inserted else None,
                "actor": ev.actor,
            }
        )
    return {"table": table, "rows": svc.org.sor.table(table), "edits": edits}


@lab.get("/clock")
def get_clock(svc: Svc) -> dict[str, str]:
    """Demo time and the demo date (read-only)."""
    return {
        "now": svc.org.clock.now().isoformat(),
        "date": svc.org.clock.today().isoformat(),
    }


@lab.post("/adapter/execute")
def execute(svc: Svc, actor: Me, body: AdapterRequest) -> dict[str, Any]:
    """The demo adapter (spec §8.3): redeem, write the effect, report."""
    return lab_adapter.execute(svc.org, svc.clearances, body.clearance_id, fail=body.fail,
                               by=actor)  # fmt: skip


@lab.post("/clock")
def set_clock(svc: Svc, body: ClockRequest) -> dict[str, str]:
    """Move demo time forward (never back) to `to`, which needs an offset."""
    try:
        svc.org.clock.set(body.to, LAB_ACTOR)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {"now": svc.org.clock.now().isoformat()}


@lab.post("/reset")
def reset(svc: Svc) -> dict[str, str]:
    """Archive the org's event log and start afresh: sessions, decisions and edits go with it."""
    return {"archived": svc.reset()}


# -- the app ------------------------------------------------------------------------------------
def _error(status: int, error: str, detail: str, **headers: str) -> JSONResponse:
    return JSONResponse({"error": error, "detail": detail}, status_code=status, headers=headers)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else load_settings()
    app = FastAPI(title="OWM service (lab)", version="1.2",
                  summary="The owm-decisions contract v1.2 over the lab's kernel.")  # fmt: skip
    app.state.owm = Service(settings)
    app.include_router(health)
    app.include_router(api)
    if settings.lab_routes:
        app.include_router(lab)

    @app.exception_handler(Refused)
    async def refused(request: Request, exc: Refused) -> JSONResponse:
        body = Refusals(refusals=exc.refusals).model_dump(mode="json", exclude_unset=True)
        return JSONResponse(body, status_code=exc.status)

    @app.exception_handler(NotFound)
    async def not_found(request: Request, exc: NotFound) -> JSONResponse:
        return _error(404, "not_found", exc.what)

    @app.exception_handler(Unauthenticated)
    async def unauthenticated(request: Request, exc: Unauthenticated) -> JSONResponse:
        return _error(401, "unauthenticated", "A valid session is needed: send Authorization: "
                      "Bearer <token>.", **{"WWW-Authenticate": "Bearer"})  # fmt: skip

    @app.exception_handler(CannotDecide)
    async def cannot_decide(request: Request, exc: CannotDecide) -> JSONResponse:
        return _error(503, "cannot_decide", exc.detail)

    @app.exception_handler(_lab.JevUnavailable)
    async def jev_unavailable(request: Request, exc: _lab.JevUnavailable) -> JSONResponse:
        return _error(503, "cannot_decide", str(exc))

    return app
