"""The register queue (spec §7.1, §7.4; contract §4.2-4.4): the contract's two steps, a person
submits and another approves, over the lab's one-shot registrar, without changing any rule.

`registrar.apply` takes the submitter and the approver together and raises the first rule that
fails. The queue calls it (through `_lab.apply`, always with the service clock's date, RR-9) at
three points:

1. **Draft** (anyone, agents included): a dry run with stand-ins, the owning function's head as
   submitter and an Executive as approver, so the content rules (RR-5 to RR-14) speak before any
   person is named. The first refusal is the draft's `checks`, and the register doesn't move.
   With no head, an Executive stands in as submitter too, and RR-3 is then the check.
2. **Submit** (a person; a stored draft, or directly): a dry run with the real submitter and a
   stand-in approver (the first of the head and the Executives who isn't the submitter), against
   the `base_version` the submitter sends, so the registrar's own RR-13 is strict here (409). A
   refusal is returned and nothing is queued. On a pass the change is pending, waiting on the head
   and the Executives other than the submitter (RR-4).
3. **Approve** (a person among the approvers): scoped RR-13 first (a change approved since this
   one was submitted that touched the same kind and scope, or a document this one names, leaves it
   refused, 409), then the real run against the register as it is now, acting as the submitter and
   the approver. A refusal leaves it refused with the rule named (422; 403 for RR-1). A pass
   stores what the registrar wrote (`_lab.register_result`) in `change.approved`, with
   `proposed_by` added to the entry, and the text goes to the org's content store.

Stand-in runs are always thrown away; approval runs every rule again with the real people. A
registrar error that isn't a rule (terms of the wrong shape, say) is reported as RR-5, never a 500.

Before any of that, a principal in the body that differs from the session's is RR-1 (403), and an
agent taking a people step (submit, approve, decline, withdraw, remind) is RR-2. A step on a change
in the wrong state (approving a draft, anything on a closed change) is DC-2: nothing waits there.

Every write is one `BEGIN IMMEDIATE` transaction that reads the change and the register inside it.
Events go on one stream per change, `change:<CHG-nnnn>`:
- `change.drafted`: `action`, `base_version`, `fields` (the change's input fields), `text`,
  `sha256`, `owning_function`, `diff`, `proposed_by`, `proposed_at`, `checks`;
- `change.submitted`: `base_version` (the submitter's), `submitted_by`, `submitted_at`,
  `approvers`. A direct submit also carries the draft's opening fields, with `proposed_by` and
  `proposed_at` null;
- `change.approved`: `approved_by`, `approved_at`, `result` (what `Org.register_state` replays) and
  `touched` (what scoped RR-13 compares);
- `change.refused` (`refusals`), `change.declined` (`declined`), `change.withdrawn` (`by`, `at`),
  `change.reminded` (`by`, `at`, `on`: the clock's date).

Task 18's `procedure` kind plugs in at three seams, each one method: `_function` (a procedure's
owner comes from its decision type), `_run` (the one place a change meets its rules: ADM through
the procedure registrar instead of `registrar.apply`) and the approved `result` (a procedure
version for `Org.procedures` instead of a register entry).
"""

from __future__ import annotations

import builtins
import copy
import json
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from . import _lab
from .errors import NotFound, Refused
from .events import Event
from .models import (
    Actor,
    AgentActor,
    PersonActor,
    PersonRef,
    Refusal,
    RegisterChange,
    RegisterRelation,
    RuleCode,
)
from .org import Org

STATUS: Final[Mapping[str, int]] = {"RR-1": 403, "RR-13": 409}  # every other rule: 422
FIELDS: Final[Mapping[str, tuple[str, ...]]] = {
    "register": ("doc_id", "kind", "title", "effective_from", "effective_to", "terms", "relations"),
    "revoke": ("target", "revoked_on"),
}
NEEDED: Final[Mapping[str, tuple[str, ...]]] = {
    "register": ("doc_id", "kind", "effective_from"), "revoke": ("target",),
}  # fmt: skip
STATE_OF: Final[Mapping[str, str]] = {
    "change.drafted": "draft", "change.submitted": "pending", "change.approved": "approved",
    "change.refused": "refused", "change.declined": "declined", "change.withdrawn": "withdrawn",
}  # fmt: skip
KINDS: Final = (*STATE_OF, "change.reminded")


class ChangeBody(BaseModel):
    """`POST /register/changes` as the core takes it: the `RegisterChange` input fields, the full
    `text`, and `submit` (false: a draft). `proposed_by` and `submitted_by` are only compared with
    the session's (RR-1): a change's people always come from the session."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["register", "revoke"]
    base_version: int
    submit: bool
    text: str | None = None
    doc_id: str | None = None
    kind: str | None = None
    title: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    terms: dict[str, Any] | None = None
    relations: list[RegisterRelation] | None = None
    target: str | None = None
    revoked_on: str | None = None
    proposed_by: Actor | None = None
    submitted_by: str | None = None

    @field_validator("effective_from", "effective_to", "revoked_on")
    @classmethod
    def _a_date(cls, v: str | None) -> str | None:
        if v is not None:
            date.fromisoformat(v)
        return v

    @model_validator(mode="after")
    def _fits_the_action(self) -> ChangeBody:
        """A register names its document; a revoke names its target and carries no document."""
        if self.action == "register":
            foreign = FIELDS["revoke"]
        else:
            foreign = (*FIELDS["register"], "text")
        missing = [k for k in NEEDED[self.action] if getattr(self, k) is None]
        extra = [k for k in foreign if getattr(self, k) is not None]
        parts = [*([f"needs {', '.join(missing)}"] if missing else []),
                 *([f"takes no {', '.join(extra)}"] if extra else [])]  # fmt: skip
        if parts:
            raise ValueError(f"a {self.action} change {' and '.join(parts)}")
        return self

    def fields(self) -> dict[str, Any]:
        """The action's input fields, JSON-plain."""
        dumped = self.model_dump(mode="json")
        return {k: dumped[k] for k in FIELDS[self.action]}


@dataclass
class _Change:
    """One change, folded from its events: the contract's fields and what the steps need."""

    change_id: str
    action: str
    state: str
    base_version: int
    fields: dict[str, Any]
    text: str | None
    sha256: str | None
    owning_function: str | None
    diff: list[dict[str, Any]]
    proposed_by: dict[str, Any] | None
    proposed_at: str | None
    checks: list[dict[str, Any]]
    submitted_by: dict[str, Any] | None = None
    submitted_at: str | None = None
    submitted_seq: int = 0
    approvers: list[dict[str, Any]] = field(default_factory=list)
    approved_by: dict[str, Any] | None = None
    approved_at: str | None = None
    declined: dict[str, Any] | None = None
    refused: list[dict[str, Any]] | None = None
    reminded_on: list[str] = field(default_factory=list)

    def submitter(self) -> str | None:
        return None if self.submitted_by is None else str(self.submitted_by["id"])

    def submitter_name(self) -> str:
        return _named([self.submitted_by] if self.submitted_by else [])

    def what(self) -> str:
        if self.action == "revoke":
            return f"the revocation of {self.fields['target']}"
        return f"{self.fields['kind']} {self.fields['doc_id']}"


def _stream(change_id: str) -> str:
    return f"change:{change_id}"


def _fold(events: Sequence[Event]) -> _Change:
    c: _Change | None = None
    for e in events:
        p = e.payload
        if e.kind == "change.drafted" or (e.kind == "change.submitted" and "fields" in p):
            c = _Change(
                change_id=p["change_id"], action=p["action"], state="draft",
                base_version=p["base_version"], fields=p["fields"], text=p["text"],
                sha256=p["sha256"], owning_function=p["owning_function"], diff=p["diff"],
                proposed_by=p["proposed_by"], proposed_at=p["proposed_at"],
                checks=p.get("checks", []),
            )  # fmt: skip
        if c is None:
            raise RuntimeError(f"corrupt log: {e.stream} starts with {e.kind}")
        if e.kind == "change.submitted":
            c.base_version, c.submitted_by = p["base_version"], p["submitted_by"]
            c.submitted_at, c.submitted_seq, c.approvers = p["submitted_at"], e.seq, p["approvers"]
        elif e.kind == "change.approved":
            c.approved_by, c.approved_at = p["approved_by"], p["approved_at"]
        elif e.kind == "change.refused":
            c.refused = p["refusals"]
        elif e.kind == "change.declined":
            c.declined = p["declined"]
        elif e.kind == "change.reminded":
            c.reminded_on.append(p["on"])
        c.state = STATE_OF.get(e.kind, c.state)
    if c is None:
        raise RuntimeError("corrupt log: a register change with no events")
    return c


def _model(c: _Change) -> RegisterChange:
    """The contract's `RegisterChange`. Optional fields are set only when they apply (ruling R13):
    a register's document fields (with `effective_to` even when null), a revoke's target and date,
    the fingerprint when there is a text, and `checks` on a draft only."""
    out: dict[str, Any] = {
        "change_id": c.change_id, "action": c.action, "state": c.state,
        "base_version": c.base_version, "proposed_by": c.proposed_by,
        "proposed_at": c.proposed_at, "submitted_by": c.submitted_by,
        "submitted_at": c.submitted_at, "approvers": c.approvers, "approved_by": c.approved_by,
        "approved_at": c.approved_at, "declined": c.declined, "refused": c.refused,
        "diff": c.diff,
    }  # fmt: skip
    out |= {k: v for k, v in c.fields.items() if v is not None or k == "effective_to"}
    if c.sha256 is not None:
        out["sha256"] = c.sha256
    if c.state == "draft":
        out["checks"] = c.checks
    return RegisterChange.model_validate(out)


# -- refusals -----------------------------------------------------------------------------------
def _no(rule: RuleCode, detail: str) -> Refusal:
    return Refusal(rule=rule, detail=detail)


def _refused(r: Refusal) -> Refused:
    return Refused(STATUS.get(r.rule, 422), [r])


def _dump(r: Refusal) -> dict[str, Any]:
    return r.model_dump(mode="json", exclude_unset=True)


def refusal(e: _lab.RefusedError) -> Refusal:
    """The registrar's refusal in the contract's shape (§3.4): its rule and message, with
    `unmatched` (RR-6, RR-7) and `fix` (RR-10) only when the registrar gave them (ruling R13)."""
    raw: dict[str, Any] = {"rule": e.rule, "detail": str(e).removeprefix(f"{e.rule}: ")}
    if e.unmatched is not None:
        raw["unmatched"] = e.unmatched
    if e.fix is not None:
        raw["fix"] = e.fix
    return Refusal.model_validate(raw)


def _named(people: Sequence[Mapping[str, Any]]) -> str:
    names = [str(p["name"]) for p in people]
    if not names:
        return "nobody"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def _identity(actor: Actor) -> tuple[str, str]:
    return ("person", actor.person.id) if isinstance(actor, PersonActor) else ("agent", actor.id)


# -- what a change is about ---------------------------------------------------------------------
def _registrar_change(
    action: str, fields: Mapping[str, Any], base_version: int, submit_by: str | None,
    approve_by: str | None,
) -> dict[str, Any]:  # fmt: skip
    """The change as `registrar.apply` reads it: copies, so the registrar never holds the log's."""
    ch: dict[str, Any] = {"action": action, "base_version": base_version,
                          "submit_by": submit_by, "approve_by": approve_by}  # fmt: skip
    if action == "register":
        ch |= {k: fields[k] for k in ("doc_id", "kind", "effective_from", "effective_to")}
        ch |= {"terms": copy.deepcopy(fields["terms"] or {}),
               "relations": copy.deepcopy(fields["relations"] or [])}  # fmt: skip
    else:
        ch |= {"target": fields["target"], "revoked_on": fields["revoked_on"]}
    return ch


def _supersedes(fields: Mapping[str, Any]) -> list[str]:
    return [str(r["target"]) for r in fields.get("relations") or [] if r["type"] == "supersedes"]


def _target(fields: Mapping[str, Any], state: Any) -> dict[str, Any] | None:
    found: dict[str, Any] | None = next(
        (e for e in state.entries if e["doc_id"] == fields.get("target")), None)  # fmt: skip
    return found


def _touched(action: str, fields: Mapping[str, Any], state: Any) -> dict[str, Any]:
    """What a change touches, for scoped RR-13: its kind and scope (the registrar's `scope`; a
    revocation's are its target's) and the documents it names (registers, supersedes, revokes)."""
    if action == "register":
        entry = {"kind": fields["kind"], "doc_id": fields["doc_id"], "terms": fields["terms"] or {}}
        docs = [str(fields["doc_id"]), *_supersedes(fields)]
        return {"kind": fields["kind"], "scope": _lab.scope(entry), "docs": docs}
    target = _target(fields, state)
    return {"kind": None if target is None else target["kind"],
            "scope": None if target is None else _lab.scope(target),
            "docs": [str(fields["target"])]}  # fmt: skip


def _overlap(mine: Mapping[str, Any], theirs: Mapping[str, Any]) -> str | None:
    """What two changes both touch, in words, or None."""
    if mine["kind"] is not None and (mine["kind"], mine["scope"]) == (theirs["kind"],
                                                                      theirs["scope"]):  # fmt: skip
        return f"the {mine['kind']} for {mine['scope']}"
    both = sorted(set(mine["docs"]) & set(theirs["docs"]))
    return ", ".join(both) if both else None


def _shown(v: Any) -> str | None:
    if v is None or isinstance(v, str):
        return v
    if isinstance(v, date):
        return v.isoformat()
    return json.dumps(v, sort_keys=True, default=str)


def _diff(action: str, fields: Mapping[str, Any], state: Any) -> list[dict[str, Any]]:
    """Against the entry the change supersedes, for the reviewer (G-33): the window dates and each
    term that differ. A revocation, or a change that supersedes nothing registered, has none."""
    targets = set(_supersedes(fields)) if action == "register" else set()
    was = next((e for e in state.entries if e["doc_id"] in targets), None)
    if was is None:
        return []
    old, new = was.get("terms") or {}, fields["terms"] or {}
    pairs = [(k, k, was.get(k), fields[k]) for k in ("effective_from", "effective_to")]
    pairs += [(f"terms.{k}", k, old.get(k), new.get(k)) for k in sorted(set(old) | set(new))]
    return [{"key": key, "label": name.replace("_", " ").capitalize(), "was": _shown(a),
             "now": _shown(b)} for key, name, a, b in pairs if _shown(a) != _shown(b)]  # fmt: skip


class RegisterQueue:
    def __init__(self, org: Org) -> None:
        self.org = org
        self.staff = _lab.Staff.load(_lab.corpus_root(org.corpus))

    # -- creating a change --------------------------------------------------------------------
    def draft(self, actor: Actor, body: ChangeBody) -> RegisterChange:
        """A stored draft, by anyone: the stand-ins' dry run gives its `checks`."""
        self._principals(actor, body)
        now = self.org.clock.now()  # before the write: never first read inside one
        fields = body.fields()
        with self.org.log.transaction() as tx:
            state = self.org.register_state(tx=tx)
            function = self._function(body.action, fields, state)
            submit_by, approve_by = self._stand_ins(function)
            change = _registrar_change(body.action, fields, body.base_version, submit_by,
                                       approve_by)  # fmt: skip
            _, found = self._run(state, change, body.text, now.date())
            cid = self.org.log.next_id(tx, self.org.org_id, "CHG", 4)
            self._append(tx, actor, now, cid, "change.drafted", {
                **self._opening(cid, body, fields, function, state),
                "proposed_by": actor.model_dump(mode="json"), "proposed_at": now.isoformat(),
                "checks": [] if found is None else [_dump(found)],
            })  # fmt: skip
        return self.get(cid)

    def submit_new(self, actor: Actor, body: ChangeBody) -> RegisterChange:
        """A change submitted directly by a person: pending, or the first rule it breaks."""
        self._principals(actor, body)
        me = self._person(actor, "submit")
        now = self.org.clock.now()
        fields = body.fields()
        with self.org.log.transaction() as tx:
            state = self.org.register_state(tx=tx)
            function = self._function(body.action, fields, state)
            self._dry_submit(state, body.action, fields, body.text, body.base_version, me,
                             function, now.date())  # fmt: skip
            cid = self.org.log.next_id(tx, self.org.org_id, "CHG", 4)
            self._append(tx, actor, now, cid, "change.submitted", {
                **self._opening(cid, body, fields, function, state),
                "proposed_by": None, "proposed_at": None,
                **self._submitted(me, now, body.base_version, function),
            })  # fmt: skip
        return self.get(cid)

    def submit(self, actor: Actor, change_id: str, base_version: int) -> RegisterChange:
        """Submit a stored draft against the version the submitter reviewed it at (RR-13 reads
        the submitter's `base_version`, not the drafter's). It becomes the submitter's change;
        `proposed_by` stays."""
        me = self._person(actor, "submit")
        now = self.org.clock.now()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            self._in(c, "draft")
            state = self.org.register_state(tx=tx)
            self._dry_submit(state, c.action, c.fields, c.text, base_version, me,
                             c.owning_function, now.date())  # fmt: skip
            self._append(tx, actor, now, change_id, "change.submitted",
                         {"change_id": change_id,
                          **self._submitted(me, now, base_version, c.owning_function)})  # fmt: skip
        return self.get(change_id)

    # -- the steps on a change ----------------------------------------------------------------
    def approve(self, actor: Actor, change_id: str) -> RegisterChange:
        """Scoped RR-13, then the real run on the register as it is now. Any refusal leaves the
        change refused with the rule named, and is raised (409 for RR-13)."""
        me = self._person(actor, "approve")
        now = self.org.clock.now()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            self._in(c, "pending")
            self._approver(c, me)
            state = self.org.register_state(tx=tx)
            mine = _touched(c.action, c.fields, state)
            found = self._moved(c, mine, state, tx)
            new: Any = None
            if found is None:
                change = _registrar_change(c.action, c.fields, state.version, c.submitter(), me.id)
                new, found = self._run(state, change, c.text, now.date())
            if found is not None:
                self._append(tx, actor, now, change_id, "change.refused",
                             {"change_id": change_id, "refusals": [_dump(found)]})  # fmt: skip
            else:
                result = _lab.register_result(state, new)
                if "entry" in result:
                    result["entry"]["proposed_by"] = c.proposed_by
                    if c.text is not None:
                        self.org.put_register_text(c.text)
                self._append(tx, actor, now, change_id, "change.approved", {
                    "change_id": change_id, "approved_by": me.model_dump(mode="json"),
                    "approved_at": now.isoformat(), "result": result, "touched": mine,
                })  # fmt: skip
        if found is not None:
            raise _refused(found)
        return self.get(change_id)

    def decline(self, actor: Actor, change_id: str, note: str | None) -> RegisterChange:
        """An approver declines a pending change, with a note. No rule is named."""
        me = self._person(actor, "decline")
        now = self.org.clock.now()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            self._in(c, "pending")
            self._approver(c, me)
            if not (note and note.strip()):
                raise _refused(_no("DC-2", "A decline needs a note: say why, so the submitter "
                                           "can act on it."))  # fmt: skip
            declined = {"by": me.model_dump(mode="json"), "at": now.isoformat(), "note": note}
            self._append(tx, actor, now, change_id, "change.declined",
                         {"change_id": change_id, "declined": declined})  # fmt: skip
        return self.get(change_id)

    def withdraw(self, actor: Actor, change_id: str) -> RegisterChange:
        """Dismiss a draft (anyone in the owning function) or withdraw a pending change (its
        submitter). Anyone else: RR-3."""
        me = self._person(actor, "withdraw")
        now = self.org.clock.now()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            if c.state == "draft":
                if c.owning_function is None or me.function != c.owning_function:
                    owner = c.owning_function or "no function (the registrar doesn't know its kind)"
                    raise _refused(_no("RR-3", f"{me.name} is in {me.function}; a draft of "
                                               f"{c.what()} is dismissed by {owner}, which owns "
                                               "it."))  # fmt: skip
            elif c.state == "pending":
                if me.id != c.submitter():
                    raise _refused(_no("RR-3", f"Only its submitter ({c.submitter_name()}) "
                                               f"withdraws {c.change_id}."))  # fmt: skip
            else:
                self._in(c, "pending")
            self._append(tx, actor, now, change_id, "change.withdrawn",
                         {"change_id": change_id, "by": me.model_dump(mode="json"),
                          "at": now.isoformat()})  # fmt: skip
        return self.get(change_id)

    def remind(self, actor: Actor, change_id: str) -> RegisterChange:
        """The submitter reminds a pending change's approvers, at most once a clock day."""
        me = self._person(actor, "remind")
        now = self.org.clock.now()
        today = now.date().isoformat()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            self._in(c, "pending")
            if me.id != c.submitter():
                raise _refused(_no("RR-3", f"Only its submitter ({c.submitter_name()}) reminds "
                                           f"{c.change_id}'s approvers."))  # fmt: skip
            if today in c.reminded_on:
                raise _refused(_no("DC-2", f"{c.change_id}'s approvers were reminded today "
                                           f"({today}); remind them again tomorrow."))  # fmt: skip
            self._append(tx, actor, now, change_id, "change.reminded",
                         {"change_id": change_id, "by": me.model_dump(mode="json"),
                          "at": now.isoformat(), "on": today})  # fmt: skip
        return self.get(change_id)

    # -- reads --------------------------------------------------------------------------------
    def get(self, change_id: str) -> RegisterChange:
        """One change, drafts included."""
        return _model(self._read(change_id))

    def list(
        self, state: str | None = None, waiting_on: str | None = None
    ) -> builtins.list[RegisterChange]:
        """Every change, by id; `state` filters by state and `waiting_on` by a person's id."""
        streams: dict[str, builtins.list[Event]] = {}
        for e in self.org.log.read(self.org.org_id, kinds=KINDS):
            streams.setdefault(e.stream, []).append(e)
        out = []
        for stream in sorted(streams):
            c = _fold(streams[stream])
            if state is not None and c.state != state:
                continue
            if waiting_on is not None and waiting_on not in {p.id for p in self._waiting(c)}:
                continue
            out.append(_model(c))
        return out

    def waiting_on(self, change_id: str) -> builtins.list[PersonRef]:
        """Who the change waits on (the work items, Task 19)."""
        return self._waiting(self._read(change_id))

    def _waiting(self, c: _Change) -> builtins.list[PersonRef]:
        """A pending change waits on its approvers. An agent's draft waits on everyone in the
        owning function, to submit or dismiss it; a person's own draft on that person."""
        if c.state == "pending":
            return [PersonRef.model_validate(p) for p in c.approvers]
        if c.state != "draft" or c.proposed_by is None:
            return []
        if c.proposed_by["kind"] == "person":
            return [PersonRef.model_validate(c.proposed_by["person"])]
        return [self.org.people.ref(e) for e, r in self.staff.rows.items()
                if r["department"] == c.owning_function]  # fmt: skip

    def _read(self, change_id: str, tx: sqlite3.Connection | None = None) -> _Change:
        events = self.org.log.read(self.org.org_id, stream=_stream(change_id), tx=tx)
        if not events:
            raise NotFound(f"register change {change_id}")
        return _fold(events)

    # -- who may act --------------------------------------------------------------------------
    def _principals(self, actor: Actor, body: ChangeBody) -> None:
        """RR-1 (403): a principal in the body that isn't the session's."""
        me = actor.person.id if isinstance(actor, PersonActor) else None
        if body.submitted_by is not None and body.submitted_by != me:
            session = (f"the session's person is {me}" if me else
                       "an agent's session acts as no person")  # fmt: skip
            raise _refused(_no("RR-1", f"submitted_by is {body.submitted_by}, but {session}: the "
                                       "submitter is always the session's."))  # fmt: skip
        if body.proposed_by is not None and _identity(body.proposed_by) != _identity(actor):
            named, mine = _identity(body.proposed_by)[1], _identity(actor)[1]
            raise _refused(_no("RR-1", f"proposed_by names {named}, but the session's actor is "
                                       f"{mine}: who proposed a change is always the "
                                       "session's."))  # fmt: skip

    def _person(self, actor: Actor, step: str) -> PersonRef:
        """RR-2: an agent may draft, never take a people step."""
        if isinstance(actor, AgentActor):
            raise _refused(_no("RR-2", f"{actor.name} is an agent: an agent may draft a register "
                                       "change but never submit, approve, decline, withdraw or "
                                       f"remind. A person must {step} it."))  # fmt: skip
        return actor.person

    def _in(self, c: _Change, want: str) -> None:
        """DC-2: the step needs the change in `want` (draft or pending)."""
        if c.state == want:
            return
        if c.state == "draft":
            detail = f"{c.change_id} is a draft: submit it first."
        elif c.state == "pending":
            detail = f"{c.change_id} was submitted already and is pending."
        else:
            detail = f"{c.change_id} is {c.state}: it takes no more steps."
        raise _refused(_no("DC-2", detail))

    def _approver(self, c: _Change, me: PersonRef) -> None:
        """RR-4: the session is among the approvers listed at submit."""
        if me.id in {p["id"] for p in c.approvers}:
            return
        waits = f"it waits on {_named(c.approvers)}"
        if me.id == c.submitter():
            detail = f"the approver is the submitter: {me.name} submitted {c.change_id}; {waits}."
        else:
            detail = (f"{me.name} may not approve {c.what()} (it needs the "
                      f"{c.owning_function} head or an Executive); {waits}.")  # fmt: skip
        raise _refused(_no("RR-4", detail))

    def _executives(self) -> builtins.list[str]:
        return [e for e, r in self.staff.rows.items() if r["department"] == _lab.EXECUTIVE]

    def _may_approve(self, function: str | None) -> builtins.list[str]:
        """RR-4's approvers, in order: the owning function's head, then the Executives."""
        head = self.staff.head(function) if function else None
        out: builtins.list[str] = []
        for p in (head, *self._executives()):
            if p is not None and p not in out:
                out.append(p)
        return out

    def _stand_ins(self, function: str | None) -> tuple[str | None, str | None]:
        """A draft's stand-ins: the head submits (an Executive when there is no head) and an
        Executive approves."""
        executives = self._executives()
        executive = executives[0] if executives else None
        head = self.staff.head(function) if function else None
        return head or executive, executive

    def _function(self, action: str, fields: Mapping[str, Any], state: Any) -> str | None:
        """The function owning the change's kind (a revocation: its target's), or None when the
        registrar doesn't know the kind (RR-5) or the target isn't registered (RR-12)."""
        target = _target(fields, state) if action == "revoke" else None
        kind = fields.get("kind") if action == "register" else target and target["kind"]
        return _lab.OWNER.get(kind) if isinstance(kind, str) else None

    # -- the registrar ------------------------------------------------------------------------
    def _run(
        self, state: Any, change: dict[str, Any], text: str | None, today: date
    ) -> tuple[Any, Refusal | None]:
        """One registrar run on the service clock's date: (the new state, None), or (None, the
        first rule it breaks). The input state is never changed."""
        acting = {p for p in (change["submit_by"], change["approve_by"]) if p is not None}
        try:
            return _lab.apply(state, change, text, acting, clock=today, staff=self.staff), None
        except _lab.RefusedError as e:
            return None, refusal(e)
        except Exception as e:  # noqa: BLE001 - a change the registrar can't read is no 500
            return None, _no("RR-5", f"the registrar can't read this change: "
                                     f"{type(e).__name__}: {e}")  # fmt: skip

    def _dry_submit(
        self, state: Any, action: str, fields: Mapping[str, Any], text: str | None,
        base_version: int, me: PersonRef, function: str | None, today: date,
    ) -> None:  # fmt: skip
        """The submit's dry run: the real submitter, a stand-in approver. Raises its refusal."""
        stand_in = next((p for p in self._may_approve(function) if p != me.id), None)
        change = _registrar_change(action, fields, base_version, me.id, stand_in)
        _, found = self._run(state, change, text, today)
        if found is not None:
            raise _refused(found)

    def _moved(
        self, c: _Change, mine: Mapping[str, Any], state: Any, tx: sqlite3.Connection
    ) -> Refusal | None:
        """Scoped RR-13: a change approved since this one was submitted touched what it touches."""
        approved = self.org.log.read(self.org.org_id, kinds=("change.approved",), tx=tx)
        for e in approved:
            what = _overlap(mine, e.payload["touched"]) if e.seq > c.submitted_seq else None
            if what is not None:
                return _no("RR-13", f"{e.payload['change_id']} was approved after {c.change_id} "
                                    f"was submitted and changed {what}; the register is at "
                                    f"version {state.version}. Prepare it again against that "
                                    "version and submit it.")  # fmt: skip
        return None

    # -- events -------------------------------------------------------------------------------
    def _opening(
        self, cid: str, body: ChangeBody, fields: dict[str, Any], function: str | None,
        state: Any,
    ) -> dict[str, Any]:  # fmt: skip
        """What a new change records first, whether drafted or submitted directly."""
        return {
            "change_id": cid, "action": body.action, "base_version": body.base_version,
            "fields": fields, "text": body.text,
            "sha256": None if body.text is None else _lab.fingerprint(body.text),
            "owning_function": function, "diff": _diff(body.action, fields, state),
        }  # fmt: skip

    def _submitted(
        self, me: PersonRef, now: datetime, base_version: int, function: str | None
    ) -> dict[str, Any]:
        approvers = [self.org.people.ref(p).model_dump(mode="json")
                     for p in self._may_approve(function) if p != me.id]  # fmt: skip
        return {"base_version": base_version, "submitted_by": me.model_dump(mode="json"),
                "submitted_at": now.isoformat(), "approvers": approvers}  # fmt: skip

    def _append(
        self, tx: sqlite3.Connection, actor: Actor, at: datetime, change_id: str, kind: str,
        payload: dict[str, Any],
    ) -> None:  # fmt: skip
        self.org.log.append(tx, at=at, org=self.org.org_id, stream=_stream(change_id), kind=kind,
                            actor=actor.model_dump(mode="json"), payload=payload)  # fmt: skip
