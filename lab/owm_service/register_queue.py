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
3. **Approve** (a person among the approvers): scoped RR-13 first, then the real run against the
   register as it is now, acting as the submitter and the approver. Scoped RR-13 (ruling R45)
   leaves the change refused (409) when a change approved since it was submitted touched the same
   kind and scope, a document both name (registered, superseded or revoked), or a document one of
   them is `under` that the other names: an exception under an agreement revoked since, or a
   revocation of an agreement something was registered under since. Two changes that are merely
   under the same document don't clash. The real run's refusal also leaves it refused with the
   rule named (422; 403 for RR-1). A pass stores what the registrar wrote
   (`_lab.register_result`) in `change.approved`, with `proposed_by` added to the entry, and the
   text goes to the org's content store.

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
  `touched` (what scoped RR-13 compares: `kind`, `scope`, `docs`, and `reads`, its `under`
  targets);
- `procedure.approved`, for a procedure version instead: `approved_by`, `approved_at` and `entry`
  (what `Org.procedures` replays);
- `change.refused` (`refusals`), `change.declined` (`declined`), `change.withdrawn` (`by`, `at`),
  `change.reminded` (`by`, `at`, `on`: the clock's date).
`changes.py` holds the change as data: the body, the fold of these events, the contract model,
what a change touches, `overlap` and the reviewer's diff.

**A procedure version** (kind `procedure`, contract §4.5) takes the same steps and differs at three
seams: `_function` (its owner comes from its decision type), `_run` (its rules are
`procedures.check`: the people rules for the decision type's owner, RR-5 on its numbering, RR-9
(ruling R52) and ADM through the lab's procedure registrar, instead of `registrar.apply`) and the
approval (scoped RR-13 doesn't apply, and it writes `procedure.approved`, never `change.approved`,
so the document register's replay and scoped RR-13 never see it; ruling R50). The register's
version doesn't move, so a procedure change's `base_version` is recorded and not compared: the
next-version rule is its stale check.
"""

from __future__ import annotations

import builtins
import copy
import sqlite3
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Final

from . import _lab, procedures
from .changes import (
    KINDS,
    Change,
    ChangeBody,
    diff,
    fold,
    is_procedure,
    named,
    overlap,
    target_entry,
    to_model,
    touched,
)
from .errors import NotFound, Refused
from .events import Event
from .models import (
    Actor,
    AgentActor,
    PersonActor,
    PersonRef,
    Refusal,
    RegisterChange,
    RuleCode,
)
from .org import Org

STATUS: Final[Mapping[str, int]] = {"RR-1": 403, "RR-13": 409}  # every other rule: 422


def _stream(change_id: str) -> str:
    return f"change:{change_id}"


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
            _, found = self._run(tx, state, body.action, fields, body.text, body.base_version,
                                 submit_by, approve_by, now.date())  # fmt: skip
            cid = self.org.log.next_id(tx, self.org.org_id, "CHG", 4)
            self._append(tx, actor, now, cid, "change.drafted", {
                **self._opening(tx, cid, body, fields, function, state),
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
            self._dry_submit(tx, state, body.action, fields, body.text, body.base_version, me,
                             function, now.date())  # fmt: skip
            cid = self.org.log.next_id(tx, self.org.org_id, "CHG", 4)
            self._append(tx, actor, now, cid, "change.submitted", {
                **self._opening(tx, cid, body, fields, function, state),
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
            self._dry_submit(tx, state, c.action, c.fields, c.text, base_version, me,
                             c.owning_function, now.date())  # fmt: skip
            self._append(tx, actor, now, change_id, "change.submitted",
                         {"change_id": change_id,
                          **self._submitted(me, now, base_version, c.owning_function)})  # fmt: skip
        return self.get(change_id)

    # -- the steps on a change ----------------------------------------------------------------
    def approve(self, actor: Actor, change_id: str) -> RegisterChange:
        """A document: scoped RR-13, then the real run on the register as it is now. A procedure
        version: its rules again with the real people. Any refusal leaves the change refused with
        the rule named, and is raised (409 for RR-13)."""
        me = self._person(actor, "approve")
        now = self.org.clock.now()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            self._in(c, "pending")
            self._approver(c, me)
            if is_procedure(c.fields):
                found = self._approve_procedure(tx, actor, now, c, me)
            else:
                found = self._approve_document(tx, actor, now, c, me)
            if found is not None:
                self._append(tx, actor, now, change_id, "change.refused",
                             {"change_id": change_id, "refusals": [_dump(found)]})  # fmt: skip
        if found is not None:
            raise _refused(found)
        return self.get(change_id)

    def _approve_document(
        self, tx: sqlite3.Connection, actor: Actor, now: datetime, c: Change, me: PersonRef
    ) -> Refusal | None:
        """Scoped RR-13, then the registrar; on a pass, `change.approved` with what it wrote."""
        state = self.org.register_state(tx=tx)
        mine = touched(c.action, c.fields, state)
        found = self._moved(c, mine, state, tx)
        if found is not None:
            return found
        new, found = self._run(tx, state, c.action, c.fields, c.text, state.version,
                               c.submitter(), me.id, now.date())  # fmt: skip
        if found is not None:
            return found
        result = _lab.register_result(state, new)
        if "entry" in result:
            result["entry"]["proposed_by"] = c.proposed_by
            if c.text is not None:
                self.org.put_register_text(c.text)
        self._append(tx, actor, now, c.change_id, "change.approved", {
            "change_id": c.change_id, "approved_by": me.model_dump(mode="json"),
            "approved_at": now.isoformat(), "result": result, "touched": mine,
        })  # fmt: skip
        return None

    def _approve_procedure(
        self, tx: sqlite3.Connection, actor: Actor, now: datetime, c: Change, me: PersonRef
    ) -> Refusal | None:
        """The version's rules with the submitter and the approver, against the procedure
        register as it is now; on a pass, the text to the procedure store and
        `procedure.approved` with the entry. Never `change.approved` (ruling R50): neither the
        register's replay nor scoped RR-13 reads a procedure version."""
        entry, found = self._run(tx, None, c.action, c.fields, c.text, c.base_version,
                                 c.submitter(), me.id, now.date())  # fmt: skip
        if found is not None:
            return found
        assert c.text is not None  # the rules refuse a version without one
        self.org.put_procedure_text(c.text)
        self._append(tx, actor, now, c.change_id, "procedure.approved", {
            "change_id": c.change_id, "approved_by": me.model_dump(mode="json"),
            "approved_at": now.isoformat(), "entry": procedures.approved(entry, c, now.date()),
        })  # fmt: skip
        return None

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
        """Dismiss a draft (anyone in the owning function, or its drafter: the person who drafted
        it, or the person an agent drafted it for; ruling R42) or withdraw a pending change (its
        submitter). Anyone else: RR-3."""
        me = self._person(actor, "withdraw")
        now = self.org.clock.now()
        with self.org.log.transaction() as tx:
            c = self._read(change_id, tx)
            if c.state == "draft":
                owns = c.owning_function is not None and me.function == c.owning_function
                if not owns and me.id not in c.drafters():
                    owner = c.owning_function or "no function (the registrar doesn't know its kind)"
                    raise _refused(_no("RR-3", f"{me.name} is in {me.function} and didn't draft "
                                               f"{c.change_id}; a draft of {c.what()} is dismissed "
                                               f"by its drafter or by {owner}, which owns "
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
        return to_model(self._read(change_id))

    def list(
        self, state: str | None = None, waiting_on: str | None = None
    ) -> builtins.list[RegisterChange]:
        """Every change, by id; `state` filters by state and `waiting_on` by a person's id."""
        out = []
        for c in self.changes():
            if state is not None and c.state != state:
                continue
            if waiting_on is not None and waiting_on not in {p.id for p in self._waiting(c)}:
                continue
            out.append(to_model(c))
        return out

    def waiting_on(self, change_id: str) -> builtins.list[PersonRef]:
        """Who the change waits on (the work items, Task 19)."""
        return self._waiting(self._read(change_id))

    def _waiting(self, c: Change) -> builtins.list[PersonRef]:
        """A pending change waits on its approvers; a draft on `draft_waiting`."""
        if c.state == "pending":
            return [PersonRef.model_validate(p) for p in c.approvers]
        return self.draft_waiting(c) if c.state == "draft" else []

    def draft_waiting(self, c: Change) -> builtins.list[PersonRef]:
        """Who a draft is for: a person's own draft, that person; an agent's, everyone in the
        owning function plus the person it drafted for, who may dismiss it (ruling R42). A draft
        of a kind no function owns waits on that person alone."""
        p = c.proposed_by
        if p is None:
            return []
        if p["kind"] == "person":
            return [PersonRef.model_validate(p["person"])]
        function = c.owning_function
        out = [self.org.people.ref(e) for e, r in self.staff.rows.items()
               if function is not None and r["department"] == function]  # fmt: skip
        whom = p.get("on_behalf_of")
        if whom is not None and whom["id"] not in {x.id for x in out}:
            out.append(PersonRef.model_validate(whom))
        return out

    def changes(self) -> builtins.list[Change]:
        """Every change folded from its events, by id (the work items read these)."""
        streams: dict[str, builtins.list[Event]] = {}
        for e in self.org.log.read(self.org.org_id, kinds=KINDS):
            streams.setdefault(e.stream, []).append(e)
        return [fold(streams[s]) for s in sorted(streams)]

    def _read(self, change_id: str, tx: sqlite3.Connection | None = None) -> Change:
        events = self.org.log.read(self.org.org_id, stream=_stream(change_id), tx=tx)
        if not events:
            raise NotFound(f"register change {change_id}")
        return fold(events)

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

    def _in(self, c: Change, want: str) -> None:
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

    def _approver(self, c: Change, me: PersonRef) -> None:
        """RR-4: the session is among the approvers listed at submit."""
        if me.id in {p["id"] for p in c.approvers}:
            return
        waits = f"it waits on {named(c.approvers)}"
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
        """The function owning the change's kind (a revocation: its target's; a procedure
        version: its decision type's), or None when the registrar doesn't know the kind (RR-5),
        the target isn't registered (RR-12) or the decision type is unknown (RR-5)."""
        if is_procedure(fields):
            return procedures.owner(fields.get("decision_type"))
        target = target_entry(fields, state) if action == "revoke" else None
        kind = fields.get("kind") if action == "register" else target and target["kind"]
        return _lab.OWNER.get(kind) if isinstance(kind, str) else None

    # -- the registrar ------------------------------------------------------------------------
    def _run(
        self, tx: sqlite3.Connection, state: Any, action: str, fields: Mapping[str, Any],
        text: str | None, base_version: int, submit_by: str | None, approve_by: str | None,
        today: date,
    ) -> tuple[Any, Refusal | None]:  # fmt: skip
        """The one place a change meets its rules, on the service clock's date: (what it would
        write, None), or (None, the first rule it breaks). A document goes through the registrar
        (the new state; the input state is never changed), a procedure version through its
        rules against the procedure register as it is now (the entry; `procedures.check`)."""
        try:
            if is_procedure(fields):
                entries, _ = self.org.procedures(tx=tx)
                return procedures.check(entries, self.staff, fields, text, submit_by, approve_by,
                                        today), None  # fmt: skip
            change = _registrar_change(action, fields, base_version, submit_by, approve_by)
            acting = {p for p in (submit_by, approve_by) if p is not None}
            return _lab.apply(state, change, text, acting, clock=today, staff=self.staff), None
        except _lab.RefusedError as e:
            return None, refusal(e)
        except Exception as e:  # noqa: BLE001 - a change the registrar can't read is no 500
            return None, _no("RR-5", f"the registrar can't read this change: "
                                     f"{type(e).__name__}: {e}")  # fmt: skip

    def _dry_submit(
        self, tx: sqlite3.Connection, state: Any, action: str, fields: Mapping[str, Any],
        text: str | None, base_version: int, me: PersonRef, function: str | None, today: date,
    ) -> None:  # fmt: skip
        """The submit's dry run: the real submitter, a stand-in approver. Raises its refusal."""
        stand_in = next((p for p in self._may_approve(function) if p != me.id), None)
        _, found = self._run(tx, state, action, fields, text, base_version, me.id, stand_in,
                             today)  # fmt: skip
        if found is not None:
            raise _refused(found)

    def _moved(
        self, c: Change, mine: Mapping[str, Any], state: Any, tx: sqlite3.Connection
    ) -> Refusal | None:
        """Scoped RR-13: a change approved since this one was submitted clashes with it."""
        approved = self.org.log.read(self.org.org_id, kinds=("change.approved",), tx=tx)
        for e in approved:
            what = overlap(mine, e.payload["touched"]) if e.seq > c.submitted_seq else None
            if what is not None:
                return _no("RR-13", f"{e.payload['change_id']} was approved after {c.change_id} "
                                    f"was submitted and {what}; the register is at version "
                                    f"{state.version}. Prepare it again against that version "
                                    "and submit it.")  # fmt: skip
        return None

    # -- events -------------------------------------------------------------------------------
    def _opening(
        self, tx: sqlite3.Connection, cid: str, body: ChangeBody, fields: dict[str, Any],
        function: str | None, state: Any,
    ) -> dict[str, Any]:  # fmt: skip
        """What a new change records first, whether drafted or submitted directly."""
        sha = None if body.text is None else _lab.fingerprint(body.text)
        if is_procedure(fields):
            shown = procedures.diff(fields, sha, self.org.procedures(tx=tx)[0])
        else:
            shown = diff(body.action, fields, state)
        return {
            "change_id": cid, "action": body.action, "base_version": body.base_version,
            "fields": fields, "text": body.text, "sha256": sha, "owning_function": function,
            "diff": shown,
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
