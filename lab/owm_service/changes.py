"""A register change as data (spec §7.1; contract §4.2): what `POST /register/changes` takes
(`ChangeBody`), the change folded from its events (`Change`, `fold`), its contract shape
(`to_model`), and what the queue compares and shows about it: what it touches (`touched`, for
scoped RR-13), whether two changes clash (`overlap`, ruling R45) and the reviewer's `diff` (G-33).

The register queue (`register_queue.py`) writes the events this module folds; its docstring lists
their payloads. Nothing here runs a rule or writes anything.

A procedure version (contract §4.5) is a `register` change of kind `procedure` whose fields are
`proc_id`, `decision_type`, `version`, its window and `report` (the admission report, as JSON),
with the spec as its `text`. The contract's `RegisterChange` has no fields of its own for it, so
it reads as one: `doc_id` is the version's name (`PROC-SLA v2`, as the procedure register names a
version it supersedes), `terms` the procedure's fields and `relations` the version it supersedes.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from . import _lab
from .events import Event
from .models import Actor, RegisterChange, RegisterRelation

PROCEDURE: Final = "procedure"
# the input fields of each shape of change: a document registered, a revocation, a procedure version
FIELDS: Final[Mapping[str, tuple[str, ...]]] = {
    "register": ("doc_id", "kind", "title", "effective_from", "effective_to", "terms", "relations"),
    "revoke": ("target", "revoked_on"),
    PROCEDURE: ("kind", "proc_id", "decision_type", "version", "effective_from", "effective_to",
                "report"),
}  # fmt: skip
NEEDED: Final[Mapping[str, tuple[str, ...]]] = {
    "register": ("doc_id", "kind", "effective_from"), "revoke": ("target",),
    PROCEDURE: ("proc_id", "decision_type", "version", "effective_from"),
}  # fmt: skip
STATE_OF: Final[Mapping[str, str]] = {
    "change.drafted": "draft", "change.submitted": "pending", "change.approved": "approved",
    "procedure.approved": "approved", "change.refused": "refused", "change.declined": "declined",
    "change.withdrawn": "withdrawn",
}  # fmt: skip
KINDS: Final = (*STATE_OF, "change.reminded")


def is_procedure(fields: Mapping[str, Any]) -> bool:
    """The change registers a procedure version."""
    return fields.get("kind") == PROCEDURE


def version_name(proc_id: str, version: int) -> str:
    """A procedure version's name, as the procedure register names the version it supersedes."""
    return f"{proc_id} v{version}"


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
    proc_id: str | None = None
    decision_type: str | None = None
    version: int | None = None
    report: dict[str, Any] | None = None
    proposed_by: Actor | None = None
    submitted_by: str | None = None

    @field_validator("effective_from", "effective_to", "revoked_on")
    @classmethod
    def _a_date(cls, v: str | None) -> str | None:
        if v is not None:
            date.fromisoformat(v)
        return v

    def shape(self) -> str:
        """`register`, `revoke`, or `procedure` (a register of kind procedure)."""
        return PROCEDURE if self.action == "register" and self.kind == PROCEDURE else self.action

    @model_validator(mode="after")
    def _fits_the_action(self) -> ChangeBody:
        """A register names its document; a revoke names its target and carries no document; a
        procedure version names the procedure, its decision type and version, and no document."""
        shape = self.shape()
        mine = {*FIELDS[shape], *(("text",) if shape != "revoke" else ())}
        every = [k for s in FIELDS.values() for k in s] + ["text"]
        foreign = list(dict.fromkeys(k for k in every if k not in mine))
        missing = [k for k in NEEDED[shape] if getattr(self, k) is None]
        extra = [k for k in foreign if getattr(self, k) is not None]
        parts = [*([f"needs {', '.join(missing)}"] if missing else []),
                 *([f"takes no {', '.join(extra)}"] if extra else [])]  # fmt: skip
        if parts:
            raise ValueError(f"a {shape} change {' and '.join(parts)}")
        return self

    def fields(self) -> dict[str, Any]:
        """The input fields of the change's shape, JSON-plain."""
        dumped = self.model_dump(mode="json")
        return {k: dumped[k] for k in FIELDS[self.shape()]}


def named(people: Sequence[Mapping[str, Any]]) -> str:
    names = [str(p["name"]) for p in people]
    if not names:
        return "nobody"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


@dataclass
class Change:
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
    withdrawn: dict[str, Any] | None = None
    refused: list[dict[str, Any]] | None = None
    refused_by: dict[str, Any] | None = None  # the approver whose approval was refused
    refused_at: str | None = None
    reminded_on: list[str] = field(default_factory=list)

    def submitter(self) -> str | None:
        return None if self.submitted_by is None else str(self.submitted_by["id"])

    def submitter_name(self) -> str:
        return named([self.submitted_by] if self.submitted_by else [])

    def drafters(self) -> set[str]:
        """Who may dismiss the draft as its drafter (ruling R42): the person who drafted it, or
        the person an agent drafted it for (`on_behalf_of`)."""
        p = self.proposed_by or {}
        person = p.get("person") if p.get("kind") == "person" else p.get("on_behalf_of")
        return {str(person["id"])} if person else set()

    def what(self) -> str:
        if self.action == "revoke":
            return f"the revocation of {self.fields['target']}"
        if is_procedure(self.fields):
            return f"procedure {version_name(self.fields['proc_id'], self.fields['version'])}"
        return f"{self.fields['kind']} {self.fields['doc_id']}"


def fold(events: Sequence[Event]) -> Change:
    c: Change | None = None
    for e in events:
        p = e.payload
        if e.kind == "change.drafted" or (e.kind == "change.submitted" and "fields" in p):
            c = Change(
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
        elif e.kind in ("change.approved", "procedure.approved"):
            c.approved_by, c.approved_at = p["approved_by"], p["approved_at"]
        elif e.kind == "change.refused":
            c.refused = p["refusals"]
            who = (e.actor or {}).get("person")  # an agent never reaches an approval (RR-2)
            c.refused_by, c.refused_at = who, e.at.isoformat()
        elif e.kind == "change.declined":
            c.declined = p["declined"]
        elif e.kind == "change.withdrawn":
            c.withdrawn = {"by": p["by"], "at": p["at"]}
        elif e.kind == "change.reminded":
            c.reminded_on.append(p["on"])
        c.state = STATE_OF.get(e.kind, c.state)
    if c is None:
        raise RuntimeError("corrupt log: a register change with no events")
    return c


def _as_document(fields: Mapping[str, Any]) -> dict[str, Any]:
    """A procedure version's fields as the contract's document fields (module docstring)."""
    pid, n = fields["proc_id"], fields["version"]
    return {
        "doc_id": version_name(pid, n), "kind": PROCEDURE,
        "effective_from": fields["effective_from"], "effective_to": fields["effective_to"],
        "terms": {"proc_id": pid, "decision_type": fields["decision_type"], "version": n},
        "relations": ([{"type": "supersedes", "target": version_name(pid, n - 1)}]
                      if isinstance(n, int) and n > 1 else []),
    }  # fmt: skip


def to_model(c: Change) -> RegisterChange:
    """The contract's `RegisterChange`. Optional fields are set only when they apply (ruling R13):
    a register's document fields (with `effective_to` even when null), a revoke's target and date,
    the fingerprint when there is a text, and `checks` on a draft only. A procedure version reads
    as a document (`_as_document`); its admission report isn't shown."""
    out: dict[str, Any] = {
        "change_id": c.change_id, "action": c.action, "state": c.state,
        "base_version": c.base_version, "proposed_by": c.proposed_by,
        "proposed_at": c.proposed_at, "submitted_by": c.submitted_by,
        "submitted_at": c.submitted_at, "approvers": c.approvers, "approved_by": c.approved_by,
        "approved_at": c.approved_at, "declined": c.declined, "refused": c.refused,
        "diff": c.diff,
    }  # fmt: skip
    fields = _as_document(c.fields) if is_procedure(c.fields) else c.fields
    out |= {k: v for k, v in fields.items() if v is not None or k == "effective_to"}
    if c.sha256 is not None:
        out["sha256"] = c.sha256
    if c.state == "draft":
        out["checks"] = c.checks
    return RegisterChange.model_validate(out)


# -- what a change is about ---------------------------------------------------------------------
def _supersedes(fields: Mapping[str, Any]) -> list[str]:
    return [str(r["target"]) for r in fields.get("relations") or [] if r["type"] == "supersedes"]


def target_entry(fields: Mapping[str, Any], state: Any) -> dict[str, Any] | None:
    """The registered entry a revocation names, or None."""
    found: dict[str, Any] | None = next(
        (e for e in state.entries if e["doc_id"] == fields.get("target")), None)  # fmt: skip
    return found


def touched(action: str, fields: Mapping[str, Any], state: Any) -> dict[str, Any]:
    """What a change touches, for scoped RR-13: its kind and scope (the registrar's `scope`; a
    revocation's are its target's), the documents it names (`docs`: registers, supersedes,
    revokes) and the documents it depends on (`reads`: its `under` targets; ruling R45)."""
    if action == "register":
        entry = {"kind": fields["kind"], "doc_id": fields["doc_id"], "terms": fields["terms"] or {}}
        docs = [str(fields["doc_id"]), *_supersedes(fields)]
        reads = [str(r["target"]) for r in fields["relations"] or [] if r["type"] == "under"]
        return {"kind": fields["kind"], "scope": _lab.scope(entry), "docs": docs, "reads": reads}
    target = target_entry(fields, state)
    return {"kind": None if target is None else target["kind"],
            "scope": None if target is None else _lab.scope(target),
            "docs": [str(fields["target"])], "reads": []}  # fmt: skip


def overlap(mine: Mapping[str, Any], theirs: Mapping[str, Any]) -> str | None:
    """Scoped RR-13 (ruling R45): what `theirs`, approved since `mine` was submitted, did to what
    `mine` touches, as the end of a sentence; None when they don't clash. They clash on the same
    kind and scope, on a document both name, or on a document one is `under` that the other
    names. Two changes merely `under` the same document never clash."""
    if mine["kind"] is not None and (mine["kind"], mine["scope"]) == (theirs["kind"],
                                                                      theirs["scope"]):  # fmt: skip
        return f"changed the {mine['kind']} for {mine['scope']}"
    docs, their_docs = set(mine["docs"]), set(theirs["docs"])
    reads, their_reads = set(mine.get("reads", [])), set(theirs.get("reads", []))
    if shared := sorted(docs & their_docs):
        return f"changed {', '.join(shared)}"
    if under := sorted(reads & their_docs):
        return f"changed {', '.join(under)}, which this change is under"
    if above := sorted(docs & their_reads):
        return f"put a document under {', '.join(above)}, which this change names"
    return None


def _shown(v: Any) -> str | None:
    if v is None or isinstance(v, str):
        return v
    if isinstance(v, date):
        return v.isoformat()
    return json.dumps(_whole(v), sort_keys=True, default=str)


def _whole(v: Any) -> Any:
    """Whole floats as ints, so a term on file as 100000.0 and sent as 100000 is one value. A bool
    stays a bool: true and 1 still differ."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, Mapping):
        return {k: _whole(x) for k, x in v.items()}
    if isinstance(v, list | tuple):
        return [_whole(x) for x in v]
    return v


def diff(action: str, fields: Mapping[str, Any], state: Any) -> list[dict[str, Any]]:
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
