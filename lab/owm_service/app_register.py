"""The register and procedure routes (spec §11), under `/api/v1`. Handlers are thin: the cores
(`register_queue`, `register_view`, `procedures`) hold the logic. The router carries no session
dependency of its own: `app.py` includes it into `/api/v1`, whose router requires one (R39)."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, ConfigDict, Discriminator, Tag, ValidationError

from . import procedures, register_view
from .changes import ChangeBody
from .models import (
    Actor,
    ChangeState,
    Page,
    PersonActor,
    RegisterChange,
    RegisterChangeRequest,
    RegisterEntry,
    RegisterSettings,
    RegisterView,
    one_page,
)
from .service import Me, Svc

router = APIRouter()


class ProcedureChangeRequest(BaseModel):
    """`POST /register/changes` for a new procedure version (contract §4.5). The contract's
    `RegisterChange` has no fields for it, so this is the lab's: `action: "register"`, `kind:
    "procedure"`, `base_version`, `submit` (false: a draft), `proc_id` (`PROC-` then capitals,
    digits and hyphens), `decision_type` (discount, credit or sla), `version` (the next number),
    `effective_from`, `effective_to` (or null), `text` (the spec) and `report` (its admission
    report, as JSON), with the optional `proposed_by` and `submitted_by` of any change. An extra
    field is a 422."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["register"]
    kind: Literal["procedure"]
    base_version: int
    submit: bool
    proc_id: str
    decision_type: str
    version: int
    effective_from: str
    effective_to: str | None
    text: str
    report: dict[str, Any]
    proposed_by: Actor | None = None
    submitted_by: str | None = None


def _which(raw: Any) -> str:
    kind = raw.get("kind") if isinstance(raw, dict) else getattr(raw, "kind", None)
    return "procedure" if kind == "procedure" else "document"


ChangeRequest = Annotated[
    Annotated[RegisterChangeRequest, Tag("document")]
    | Annotated[ProcedureChangeRequest, Tag("procedure")],
    Discriminator(_which),
]


class SubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_version: int


class DeclineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = None


def _change_body(req: RegisterChangeRequest | ProcedureChangeRequest) -> ChangeBody:
    """The validated request as the core's (looser) `ChangeBody`; a failure there is a 422."""
    inner = req.root if isinstance(req, RegisterChangeRequest) else req
    try:
        return ChangeBody.model_validate(inner.model_dump(mode="json", exclude_unset=True))
    except ValidationError as e:
        raise RequestValidationError(e.errors(include_url=False, include_context=False)) from e


@router.get("/register", response_model_exclude_unset=True)
def get_register(svc: Svc, as_of: date | None = None) -> RegisterView:
    return register_view.view(svc.org, as_of)


@router.get("/register/entries/{doc_id}", response_model_exclude_unset=True)
def get_entry(svc: Svc, doc_id: str) -> RegisterEntry:
    return register_view.entry(svc.org, doc_id)


@router.get("/register/entries/{doc_id}/text", response_class=PlainTextResponse)
def get_entry_text(svc: Svc, doc_id: str) -> PlainTextResponse:
    """The approved text, byte for byte, as `text/plain; charset=utf-8`."""
    return PlainTextResponse(register_view.text(svc.org, doc_id))


@router.get("/register/settings", response_model_exclude_unset=True)
def get_settings(svc: Svc) -> RegisterSettings:
    return RegisterSettings.model_validate(register_view.settings(svc.org))


@router.put("/register/settings", response_model_exclude_unset=True)
def put_settings(svc: Svc, actor: Me, body: Annotated[dict[str, Any], Body()]) -> RegisterSettings:
    """Executives only (RR-4; an agent is RR-2); logged as `settings.changed`."""
    return RegisterSettings.model_validate(register_view.put_settings(svc.org, actor, body))


@router.post("/register/changes", status_code=201, response_model_exclude_unset=True)
def propose_change(svc: Svc, actor: Me, body: ChangeRequest) -> RegisterChange:
    """A document change (`RegisterChangeRequest`) or a procedure version
    (`ProcedureChangeRequest`: `kind: "procedure"`, with `proc_id`, `decision_type`, `version`,
    `text` and `report`). `submit: false` stores a draft, which anyone may make, agents included;
    otherwise a person submits it directly."""
    change = _change_body(body)
    return (
        svc.register.submit_new(actor, change)
        if change.submit
        else svc.register.draft(actor, change)
    )


@router.get("/register/changes", response_model_exclude_unset=True)
def list_changes(
    svc: Svc, actor: Me, state: ChangeState | None = None, waiting_on: Literal["me"] | None = None
) -> Page[RegisterChange]:
    """`waiting_on=me`: the changes waiting on the session's person. Nothing waits on an agent
    and an agent takes no register step (RR-2), so an agent's list is empty, as in /approvals."""
    who = None
    if waiting_on is not None:
        who = actor.person.id if isinstance(actor, PersonActor) else ""
    return one_page(svc.register.list(state=state, waiting_on=who))


@router.get("/register/changes/{change_id}", response_model_exclude_unset=True)
def get_change(svc: Svc, change_id: str) -> RegisterChange:
    """One change, drafts included."""
    return svc.register.get(change_id)


@router.post("/register/changes/{change_id}/submit", response_model_exclude_unset=True)
def submit_change(svc: Svc, actor: Me, change_id: str, body: SubmitRequest) -> RegisterChange:
    """Submit a stored draft against the `base_version` the submitter reviewed it at (B-11)."""
    return svc.register.submit(actor, change_id, body.base_version)


@router.post("/register/changes/{change_id}/approve", response_model_exclude_unset=True)
def approve_change(svc: Svc, actor: Me, change_id: str) -> RegisterChange:
    """Approve a pending change as one of its approvers. Known demo limit: approving a new
    entry of a kind that decisions read can change what the kernel sends to Jev, so the next
    such decision may miss the replay and return 503 in replay mode."""
    return svc.register.approve(actor, change_id)


@router.post("/register/changes/{change_id}/decline", response_model_exclude_unset=True)
def decline_change(
    svc: Svc, actor: Me, change_id: str, body: DeclineRequest | None = None
) -> RegisterChange:
    """Decline a pending change; the note is needed (DC-2 without one)."""
    return svc.register.decline(actor, change_id, body.note if body else None)


@router.post("/register/changes/{change_id}/withdraw", response_model_exclude_unset=True)
def withdraw_change(svc: Svc, actor: Me, change_id: str) -> RegisterChange:
    """Dismiss a draft, or withdraw a pending change (its submitter)."""
    return svc.register.withdraw(actor, change_id)


@router.post("/register/changes/{change_id}/remind", response_model_exclude_unset=True)
def remind_change(svc: Svc, actor: Me, change_id: str) -> RegisterChange:
    return svc.register.remind(actor, change_id)


@router.get("/procedures")
def list_procedures(svc: Svc) -> Page[dict[str, Any]]:
    return one_page(procedures.list_procedures(svc.org))


@router.get("/procedures/{proc_id}")
def get_procedure(svc: Svc, proc_id: str) -> dict[str, Any]:
    return procedures.get_procedure(svc.org, proc_id)
