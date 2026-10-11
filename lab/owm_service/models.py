"""Pydantic mirror of `contract/owm-decisions.ts` (garbanzo 30977cd), field for field.

Every model forbids extra fields. TS unions become `Literal` unions; unions the TS
discriminates are discriminated here (Actor on `kind`, Judgment on `form`, Findings on `type`,
ClearanceResponse on `cleared`, RedeemResponse on `redeemed`). `Optional` TS fields (`?:`)
default to None; `unknown` is `Any`.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- §3 common


class PersonRef(_M):
    id: str
    name: str
    title: str
    function: str


class Mandate(_M):
    doc_id: str


class PersonActor(_M):
    kind: Literal["person"]
    person: PersonRef


class AgentActor(_M):
    kind: Literal["agent"]
    id: str
    name: str
    version: str
    on_behalf_of: PersonRef | None
    mandate: Mandate | None


Actor = Annotated[PersonActor | AgentActor, Field(discriminator="kind")]


class MeResponse(_M):
    actor: Actor


class FunctionParty(_M):
    kind: Literal["function"]
    function: str
    note: str


Party = PersonRef | FunctionParty

RuleCode = Literal[
    "RR-1",
    "RR-2",
    "RR-3",
    "RR-4",
    "RR-5",
    "RR-6",
    "RR-7",
    "RR-8",
    "RR-9",
    "RR-10",
    "RR-11",
    "RR-12",
    "RR-13",
    "RR-14",
    "ADM",
    "DC-1",
    "DC-2",
    "DC-3",
    "DC-4",
    "DC-5",
    "DC-6",
]

Relation = Literal["supersedes", "under"]


class RegisterRelation(_M):
    type: Relation
    target: str


class SupersedesRelation(_M):
    type: Literal["supersedes"]
    target: str


class RefusalFix(_M):
    relations: list[SupersedesRelation]


class Refusal(_M):
    rule: RuleCode
    detail: str
    unmatched: str | None = None
    fix: RefusalFix | None = None
    existing: str | None = None


class Refusals(_M):
    refusals: list[Refusal]


SubmittedValue = str | int | float


class Submitted(_M):
    """Partial<Record<SubmittedField, string | number>> (§3.5)."""

    requested_discount: SubmittedValue | None = None
    requested_limit_usd: SubmittedValue | None = None
    current_limit_usd: SubmittedValue | None = None
    request_date: SubmittedValue | None = None
    status: SubmittedValue | None = None
    customer: SubmittedValue | None = None
    product: SubmittedValue | None = None
    requestor: SubmittedValue | None = None


SubmittedField = Literal[
    "requested_discount",
    "requested_limit_usd",
    "current_limit_usd",
    "request_date",
    "status",
    "customer",
    "product",
    "requestor",
]

# ---------------------------------------------------------------- §4 register

DocKind = str
EntryStatus = Literal["scheduled", "in_force", "superseded", "expired", "revoked"]


class Revoked(_M):
    on: str
    by: PersonRef
    approved_by: PersonRef


class FileCheck(_M):
    sha256: str
    matches: bool
    detail: str | None
    source_id: str | None


class RegisterEntry(_M):
    doc_id: str
    kind: DocKind
    title: str
    owning_function: str
    scope: str
    sha256: str
    effective_from: str
    effective_to: str | None
    relations: list[RegisterRelation]
    terms: dict[str, Any]
    proposed_by: Actor | None
    registered_by: Party
    approved_by: Party
    registered_on: str
    approved_on: str
    revoked: Revoked | None
    status: EntryStatus
    superseded_by: str | None
    file: FileCheck


class RegisterSeries(_M):
    series_id: str
    kind: DocKind
    scope: str
    title: str
    entries: list[str]
    in_force: str | None


class CoverageProcedure(_M):
    id: str
    version: int


class CoverageDocument(_M):
    doc_id: str
    title: str


class Coverage(_M):
    decision_type: str
    label: str
    procedure: CoverageProcedure | None
    documents: list[CoverageDocument]
    gap: str | None


MismatchMode = Literal["use_registered", "route"]


class RegisterSettings(_M):
    on_mismatch: MismatchMode


class RegisterView(_M):
    version: int
    clock: str
    entries: list[RegisterEntry]
    series: list[RegisterSeries]
    coverage: list[Coverage]
    settings: RegisterSettings


ChangeState = Literal["draft", "pending", "approved", "declined", "withdrawn", "refused"]


class Declined(_M):
    by: PersonRef
    at: str
    note: str


class DiffRow(_M):
    key: str
    label: str
    was: str | None
    now: str | None


class RegisterChange(_M):
    change_id: str
    action: Literal["register", "revoke"]
    state: ChangeState
    base_version: int
    doc_id: str | None = None
    kind: DocKind | None = None
    title: str | None = None
    sha256: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    terms: dict[str, Any] | None = None
    relations: list[RegisterRelation] | None = None
    target: str | None = None
    revoked_on: str | None = None
    proposed_by: Actor | None
    proposed_at: str | None
    submitted_by: PersonRef | None
    submitted_at: str | None
    approvers: list[PersonRef]
    approved_by: PersonRef | None
    approved_at: str | None
    declined: Declined | None
    refused: list[Refusal] | None
    diff: list[DiffRow]
    checks: list[Refusal] | None = None


class _RegisterChangeCommon(_M):
    base_version: int
    submit: bool
    proposed_by: Actor | None = None
    submitted_by: str | None = None


class RegisterDocRequest(_RegisterChangeCommon):
    action: Literal["register"]
    doc_id: str
    kind: DocKind
    title: str
    text: str
    effective_from: str
    effective_to: str | None
    terms: dict[str, Any]
    relations: list[RegisterRelation]


class RevokeDocRequest(_RegisterChangeCommon):
    action: Literal["revoke"]
    target: str
    revoked_on: str


class RegisterChangeRequest(
    RootModel[Annotated[RegisterDocRequest | RevokeDocRequest, Field(discriminator="action")]]
):
    """POST /register/changes."""


# ---------------------------------------------------------------- §5 decisions

DecisionType = Literal["discount", "credit", "sla"]
ApprovalOutcome = Literal[
    "APPROVE",
    "APPROVE_WITH_AUTHORIZATION",
    "REJECT_OR_ESCALATE",
    "REVIEW_REQUIRED",
    "REQUEST_EVIDENCE",
]
SlaOutcome = Literal[
    "BREACH_CREDIT_OWED", "BREACH_NO_CREDIT", "NO_BREACH", "OUT_OF_SCOPE", "CANNOT_DECIDE"
]
Outcome = ApprovalOutcome | SlaOutcome

ROUTE_TO: dict[DecisionType, Outcome] = {
    "discount": "REQUEST_EVIDENCE",
    "credit": "REQUEST_EVIDENCE",
    "sla": "CANNOT_DECIDE",
}


class Authority(_M):
    policy: str | None
    requestor_limit: float | None
    requestor_authorized: bool | None
    required_role: str | None
    approver: PersonRef | None


class CommercialEligibility(_M):
    status: Literal["eligible", "exceeded", "not_covered", "unknown", "standard"]
    maximum_discount: float | None
    basis: str | None


class DiscountFindings(_M):
    type: Literal["discount"]
    commercial_eligibility: CommercialEligibility
    authority: Authority | None


class CreditEligibility(_M):
    status: Literal["eligible", "exceeded", "ineligible", "unknown"]
    maximum_limit_usd: float | None
    basis: str | None


class CreditFindings(_M):
    type: Literal["credit"]
    eligibility: CreditEligibility
    authority: Authority | None
    registered: list[str]


class Obligation(_M):
    party: Literal["organization", "counterparty"]
    duty: Literal[
        "engage",
        "notify",
        "decide_claim",
        "issue_memo",
        "record_root_cause",
        "phone_report",
        "claim",
    ]
    role: str | None
    holder: PersonRef | None
    holder_ref: str | None
    due: str | None
    status: Literal["met", "not_met"] | None


class Breach(_M):
    response: Literal["met", "missed", "not_applicable", "cannot_decide"]
    restoration: Literal[
        "met", "missed", "missed_band1", "missed_band2", "not_applicable", "cannot_decide"
    ]


class SlaFindings(_M):
    type: Literal["sla"]
    scope: Literal["in", "out"] | None
    severity: Literal[1, 2, 3, 4] | None
    breach: Breach | None
    credit_usd: float | None
    obligations: list[Obligation]
    account_owner: PersonRef | None


Findings = Annotated[DiscountFindings | CreditFindings | SlaFindings, Field(discriminator="type")]


class ChoiceJudgment(_M):
    q: str
    about: str | None
    form: Literal["choice"]
    choice: str
    probabilities: dict[str, float]
    confidence: float
    uncertain: bool


class YesNoJudgment(_M):
    q: str
    about: str | None
    form: Literal["yes_no"]
    yes: bool
    p_yes: float
    uncertain: bool


Judgment = Annotated[ChoiceJudgment | YesNoJudgment, Field(discriminator="form")]

FlagCode = Literal[
    "routed",
    "withheld",
    "incident",
    "conflict",
    "tamper",
    "mismatch",
    "set_aside",
    "not_on_file",
    "revoked",
    "self_sourced_basis",
    "ratchet",
    "cannot_decide",
    "out_of_scope",
    "note",
    "possible_duplicate",
]


class FlagRelated(_M):
    subject: str
    decision_id: str
    floor: int | float | None


class Flag(_M):
    code: FlagCode
    text: str
    routes: bool
    about: list[str]
    related: FlagRelated | None = None


ConditionSource = Literal["input_conflict", "missing_record", "ratchet"]
Resolution = Literal["confirmed_record", "corrected_record", "confirmed_lower_level"]


class ConditionResolved(_M):
    by: PersonRef
    at: str
    resolution: Resolution
    note: str | None
    rerun_version: int


class Condition(_M):
    id: str
    source: ConditionSource
    what: str
    who: list[PersonRef]
    blocking: bool
    field: SubmittedField | None
    submitted: Any
    on_record: Any
    opened_in_version: int
    resolved: ConditionResolved | None


class PassedFrom(_M):
    person: PersonRef
    reason: Literal["separation_of_duties"]


class ApprovalGiven(_M):
    by: PersonRef
    at: str
    note: str | None


class ApprovalRequirement(_M):
    kind: Literal["approval", "concurrence", "claim_decision"]
    role: str
    person: PersonRef | None
    passed_from: PassedFrom | None
    given: ApprovalGiven | None
    declined: Declined | None


ActionName = Literal["apply_discount", "set_credit_limit", "issue_service_credit"]


class DecidedAction(_M):
    action: ActionName
    params: dict[str, Any]
    expected_actor: PersonRef | None


class LastChanged(_M):
    by: PersonRef | None
    at: str


class BasisRecord(_M):
    system: str
    table: str
    id: str
    fields: dict[str, Any]
    read_at: str
    last_changed: LastChanged | None


class BasisDocument(_M):
    doc_id: str
    sha256: str
    registered: bool


class Basis(_M):
    records: list[BasisRecord]
    documents: list[BasisDocument]


DecisionState = Literal[
    "no_action", "not_ready", "awaiting_approval", "declined", "ready", "spent", "withdrawn"
]


class Subject(_M):
    request_id: str | None = None
    ticket: str | None = None
    account_id: str | None = None
    customer_id: str | None = None
    product: str | None = None


class ProcedureRef(_M):
    id: str
    version: int
    sha256: str


class DecidedBy(_M):
    kind: Literal["owm"]
    procedure: ProcedureRef
    judgments: int
    uncertain: int


class RegisterUsed(_M):
    doc_id: str
    sha256: str
    status: Literal["in_force", "revoked"]
    file_matches: bool


class SetBy(_M):
    decision_id: str
    version: int


class Floor(_M):
    subject: str
    level: int | float
    set_by: SetBy
    confirmed_by: PersonRef | None


class Execution(_M):
    action: ActionName
    decision_id: str
    version: int
    clearance_id: str
    redeemed_at: str
    report: Literal["applied", "failed"] | None
    incident_id: str | None


class Previous(_M):
    version: int
    what_changed: str


class DecisionRecord(_M):
    decision_id: str
    version: int
    decision_type: DecisionType
    subject: Subject
    submitted: Submitted | None
    requested_by: PersonRef | None
    actor: Actor
    requested_at: str
    as_of: str
    decided_at: str
    decided_by: DecidedBy
    outcome: Outcome | None
    gated_outcome: Outcome
    routed: bool
    findings: Findings
    judgments: list[Judgment]
    flags: list[Flag]
    conditions: list[Condition]
    approvals: list[ApprovalRequirement]
    actions: list[DecidedAction]
    state: DecisionState
    basis: Basis
    register_used: list[RegisterUsed]
    floor: Floor | None
    executed: list[Execution]
    previous: Previous | None


class RequestSubject(_M):
    request_id: str


class TicketSubject(_M):
    ticket: str


class DecisionRequest(_M):
    """POST /decisions. There is deliberately no `as_of` (§3.5, S23's trap)."""

    decision_type: DecisionType
    subject: RequestSubject | TicketSubject
    submitted: Submitted | None = None


class ResolveRequest(_M):
    decision_version: int
    resolution: Resolution
    note: str | None = None


class StepRequest(_M):
    """POST /decisions/{id}/approve and /decline: the version the approver saw, and a note."""

    decision_version: int
    note: str | None = None


class RerunRequest(_M):
    """POST /decisions/{id}/rerun: the version being superseded."""

    decision_version: int


class DecisionEvent(_M):
    at: str
    actor: Actor
    version: int
    kind: Literal[
        "requested",
        "decided",
        "condition_resolved",
        "rerun",
        "approved",
        "declined",
        "withdrawn",
        "clearance_cleared",
        "clearance_refused",
        "clearance_redeemed",
        "execution_reported",
        "incident_raised",
    ]
    detail: str


# ---------------------------------------------------------------- §7 clearance

ClearanceCode = Literal[
    "stale",
    "spent",
    "suspended",
    "outside_mandate",
    "differs",
    "condition_open",
    "awaiting_approval",
    "declined",
]


class ClearanceRequest(_M):
    decision_id: str
    decision_version: int
    action: ActionName
    params: dict[str, Any]
    actor: Actor | None = None
    dry_run: bool | None = None


class ClearanceReason(_M):
    code: ClearanceCode
    detail: str
    waiting_on: list[PersonRef] | None = None
    condition_id: str | None = None


class ClearanceBound(_M):
    decision_id: str
    decision_version: int
    action: ActionName
    params: dict[str, Any]
    actor: Actor


class Cleared(_M):
    cleared: Literal[True]
    clearance_id: str
    bound: ClearanceBound
    expires_at: str
    single_use: Literal[True]


class NotCleared(_M):
    cleared: Literal[False]
    reasons: list[ClearanceReason]


class ClearanceResponse(RootModel[Annotated[Cleared | NotCleared, Field(discriminator="cleared")]]):
    pass


class Executor(_M):
    system: str
    adapter: str


class RedeemRequest(_M):
    params: dict[str, Any]
    executor: Executor


class Redeemed(_M):
    redeemed: Literal[True]
    at: str


class RedeemReason(_M):
    code: Literal["used", "expired", "mismatch", "stale", "spent", "condition_open", "suspended"]
    detail: str


class NotRedeemed(_M):
    redeemed: Literal[False]
    reasons: list[RedeemReason]


class RedeemResponse(RootModel[Annotated[Redeemed | NotRedeemed, Field(discriminator="redeemed")]]):
    pass


class ReportRequest(_M):
    status: Literal["applied", "failed"]
    external_ref: str | None
    detail: str | None


class ReportResponse(_M):
    incident_id: str | None


class ClearanceAttempt(_M):
    at: str
    actor: Actor
    request: ClearanceRequest
    response: ClearanceResponse


# ---------------------------------------------------------------- §8 approvals


class HeldBy(_M):
    condition_id: str
    what: str
    who: list[PersonRef]


class WorkItem(_M):
    kind: Literal["register_change", "register_draft", "decision_approval", "condition"]
    id: str
    title: str
    detail: str
    raised_by: Actor
    raised_at: str
    waiting_on: list[PersonRef]
    held_by: list[HeldBy]
    href: str


class DoneWorkItem(WorkItem):
    result: str
    at: str


class ApprovalsView(_M):
    waiting_on_you: list[WorkItem]
    waiting_on_others: list[WorkItem]
    done: list[DoneWorkItem]


# ---------------------------------------------------------------- §9 agents


class MandateAgent(_M):
    id: str
    name: str
    purpose: str
    runtime: Literal["agno", "external"]


class MandateOwner(_M):
    function: str
    accountable: PersonRef


class MayAsk(_M):
    decision_type: DecisionType
    scope: str


class MayDo(_M):
    action: ActionName
    decision_types: list[DecisionType]
    match: dict[str, Literal["exact", "at_most"]]
    limits: dict[str, float] | None


class AgentMandateTerms(_M):
    agent: MandateAgent
    owner: MandateOwner
    principal: Literal["delegated", "service"]
    team: str | None
    versions: list[str]
    may_ask: list[MayAsk]
    may_do: list[MayDo]
    may_propose: list[Literal["register_change", "procedure", "identity_merge"]]
