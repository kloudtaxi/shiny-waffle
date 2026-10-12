"""The service's one boundary to lab code (B-06; spec §2 and §8.3).

Only this module touches the lab: the kernel and the governed runner (`lab/owm_kernel`), the
registrar, the procedure register and the served register's coverage (`lab/owm_register`) and the
decision-engine port (`lab/decision_engine`), each imported with importlib after a sys.path insert.
The rest of the service calls the typed functions below, and `Any` stays here. It never loads the
admission gate, because the gate loads the lab's scenarios and answer side.

It also owns:
- `ReplayEngine`, the Jev engine: every recording under `runs/`, by request hash. It goes live
  only when the settings switch live on, and then only up to a cap of calls in its own file;
- `make_evidence`, the kernel's own `Evidence` with each table passed through the systems-of-record
  overlay. The documents are untouched.
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import sys
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any, Final, Literal

from .errors import CannotDecide

LAB_ROOT: Final = Path(__file__).resolve().parents[2]
for _dir in ("lab/decision_engine", "lab/owm_kernel", "lab/owm_register"):
    if str(LAB_ROOT / _dir) not in sys.path:
        sys.path.insert(0, str(LAB_ROOT / _dir))


def _load(name: str) -> ModuleType:
    return importlib.import_module(name)


_engine = _load("engine")
_kernel = _load("kernel")
_governed = _load("governed")
_additions = _load("additions")
_registrar = _load("registrar")
_build_procedures = _load("build_procedures")
_serve = _load("serve")

DecisionType = Literal["discount", "credit", "sla"]
ROUTE_TO: Final[Mapping[DecisionType, str]] = {
    "discount": "REQUEST_EVIDENCE", "credit": "REQUEST_EVIDENCE", "sla": "CANNOT_DECIDE",
}  # fmt: skip
MODEL: Final = "jev-1.13.0"


# -- Jev ----------------------------------------------------------------------------------------
class JevUnavailable(Exception):  # noqa: N818 (the name the plan fixes)
    """Jev can't answer: a request never recorded with live off, or the live cap is reached."""


def replay_files(lab_root: Path) -> list[Path]:
    """Every recorded Jev exchange under `<lab_root>/runs`, as the admission gate reads them."""
    runs = lab_root / "runs"
    return sorted({*runs.rglob("*engine-calls*.jsonl"), *runs.rglob("*jev-calls*.jsonl")})


class ReplayEngine:
    """Recorded answers by request hash, from `files` and from `calls` (this engine's own file).
    A miss raises `JevUnavailable`, unless `live` is on and `calls` holds fewer than `cap` lines;
    then the request goes to TypeSafe's Jev through the recorder, which appends it to `calls`.
    The live engine is built on the first live call, and TypeSafe reads the key itself
    (`TYPESAFE_API_KEY`, else the file `TYPESAFE_API_KEY_FILE` names); the service never does.
    Answers are copies: the kernel puts parts of an answer into the record, and one engine serves
    every decision the service makes."""

    model: Final = MODEL

    def __init__(self, files: list[Path], calls: Path, *, live: bool, cap: int) -> None:
        self.calls, self.live, self.cap = calls, live, cap
        self._seen: dict[str, Any] = {}
        self._recorder: Any = None
        self._lock = threading.Lock()
        for path in [*files, *([calls] if calls.exists() and calls not in files else [])]:
            for line in path.read_text().splitlines():
                rec = json.loads(line)
                self._seen.setdefault(rec["hash"], rec["response"])

    def ask(self, state: Any, questions: dict[str, Any]) -> Any:
        h: str = _engine.request_hash(self.model, state, questions)
        if h in self._seen:
            return copy.deepcopy(self._seen[h])
        if not self.live:
            raise JevUnavailable(f"not recorded: {h[:12]}")
        with self._lock:  # one live call at a time, so the cap holds across threads
            if h not in self._seen:
                made = len(self.calls.read_text().splitlines()) if self.calls.exists() else 0
                if made >= self.cap:
                    raise JevUnavailable(f"live Jev cap reached ({self.cap})")
                if self._recorder is None:
                    self._recorder = _engine.Recorder(_engine.TypeSafe(self.model), self.calls)
                self._seen[h] = copy.deepcopy(self._recorder.ask(state, questions))
            return copy.deepcopy(self._seen[h])


# -- evidence -----------------------------------------------------------------------------------
Overlay = Callable[[str, list[dict[str, str]]], list[dict[str, str]]]
_Evidence: Any = _kernel.Evidence


class OverlayEvidence(_Evidence):  # type: ignore[misc]
    """The kernel's `Evidence` over a corpus, each table passed through the overlay first."""

    def __init__(self, root: Path, overlay: Overlay) -> None:
        super().__init__(root)
        self.overlay = overlay

    def table(self, name: str) -> list[dict[str, str]]:
        return self.overlay(name, super().table(name))


def make_evidence(root: Path, overlay: Overlay) -> Any:
    """What the kernel reads for one corpus: its documents as they are, its tables overlaid."""
    return OverlayEvidence(root, overlay)


def doc_prints(evidence: Any) -> list[tuple[str, str, str]]:
    """(filename, doc_id, fingerprint) of every document in `evidence`, fingerprinted as the
    register records a document (`kernel.fingerprint`)."""
    return [(str(d.filename), str(d.doc_id), str(_kernel.fingerprint(d.raw)))
            for d in evidence.docs()]  # fmt: skip


def corpus_root(corpus: str) -> Path:
    """The corpus's folder: `base` is the evidence itself; any other is a variant of it."""
    if corpus == "base":
        return LAB_ROOT / "dataset/evidence"
    return LAB_ROOT / "dataset/evidence-variants" / corpus


def staff(root: Path) -> list[dict[str, str]]:
    """The corpus's HR export (`employees`)."""
    rows: list[dict[str, str]] = _kernel.Evidence(root).table("employees")
    return rows


def credit_tier(evidence: Any, row: Mapping[str, str]) -> str | None:
    """The account tier of a credit request's customer: the ERP customer, the CRM account linked
    to it by DUNS number (never by name), then its tier. None when either is missing."""
    erp = next((c for c in evidence.table("customers")
                if c["erp_customer_id"] == row.get("erp_customer_id")), None)  # fmt: skip
    account = erp and _kernel.linked(erp, evidence.table("crm_accounts"), ("duns_number",))
    return str(account["account_tier"]) if account else None


def pass_up(staff: list[dict[str, str]], requester_id: str, title: str) -> dict[str, str] | None:
    """The holder of `title` for a request by `requester_id`, under separation of duties."""
    holder: dict[str, str] | None = _additions.pass_up(staff, requester_id, title)
    return holder


# -- registers ----------------------------------------------------------------------------------
def register_bootstrap(corpus: str) -> Any:
    """The registrar's state for the corpus at its bootstrap import."""
    return _registrar.State.bootstrap(corpus)


def kernel_register(state: Any, into: Path) -> Any:
    """A `kernel.Register` over a registrar state, its store of approved texts under `into`."""
    return state.register(into=into)


def entry_in_force(entries: Sequence[Mapping[str, Any]], on: date) -> dict[str, Any] | None:
    """The kernel's own rule (`kernel.entry_in_force`): the one entry among `entries` in force on
    `on` (inside its window, not revoked on or before it, not superseded by another in force),
    or None when none is or two are. The caller filters by kind; the kernel's flags are dropped."""
    found: dict[str, Any] | None = _kernel.entry_in_force(list(entries), on, [])
    return found


def revoked_on_or_before(entry: Mapping[str, Any], on: date) -> bool:
    """RR-12 as the kernel applies it (`kernel.Register.as_of`): the entry was revoked on or before
    `on`, so it no longer counts as registered."""
    return not _kernel.Register([dict(entry)]).as_of(on).entries


def procedures_bootstrap() -> tuple[list[dict[str, Any]], Path]:
    """The procedure register's entries and the store of their approved texts."""
    entries: list[dict[str, Any]] = _governed.procedures()
    store: Path = _governed.STORE
    return entries, store


def procedure_in_force(
    entries: Sequence[Mapping[str, Any]], decision_type: str, on: date
) -> dict[str, Any] | None:
    """The governed runner's own rule (`governed.in_force`): the highest version of the decision
    type's procedure whose window holds `on`, which is the one a decision on `on` runs."""
    found: dict[str, Any] | None = _governed.in_force(list(entries), decision_type, on)
    return found


# registrar access (the register queue, Task 16; procedures, Task 18), typed for the service
if TYPE_CHECKING:

    class RefusedError(Exception):
        rule: str
        unmatched: str | None
        fix: dict[str, Any] | None

        def __init__(self, rule: str, message: str, *, unmatched: str | None = None,
                     fix: dict[str, Any] | None = None) -> None: ...  # fmt: skip

    class Staff:
        rows: dict[str, dict[str, str]]

        def __init__(self, rows: dict[str, dict[str, str]]) -> None: ...
        @classmethod
        def load(cls, root: Path = ...) -> Staff: ...
        def head(self, dept: str) -> str | None: ...
        def label(self, emp: str) -> str: ...

    class ProcedureRefusedError(Exception): ...

else:
    RefusedError = _registrar.RefusedError
    Staff = _registrar.Staff
    ProcedureRefusedError = _build_procedures.RefusedError

OWNER: Final[Mapping[str, str]] = _registrar.OWNER
EXECUTIVE: Final[str] = _registrar.EXECUTIVE
COVERAGE: Final[Mapping[str, Mapping[str, str]]] = _serve.COVERAGE


def apply(
    state: Any, change: dict[str, Any], text: str | None, acting_as: set[str], *,
    clock: date | None = None, staff: Staff | None = None,
) -> Any:  # fmt: skip
    """One register change through the registrar: a new state, or `RefusedError`."""
    kwargs: dict[str, Any] = {"staff": staff} | ({"clock": clock} if clock else {})
    return _registrar.apply(state, change, text, acting_as, **kwargs)


def people(
    kind: str, submit: str | None, approve: str | None, acting_as: set[str], staff: Staff
) -> tuple[str, str]:
    """The registrar's people rules (RR-1 to RR-4): the submitter and approver, or a refusal."""
    pair: tuple[str, str] = _registrar.people(kind, submit, approve, acting_as, staff)
    return pair


def scope(entry: Mapping[str, Any]) -> str:
    """The registrar's own `scope`: what one entry in force at a time is about (the company, or a
    customer, with an exception's product or a guarantee's guarantor; each amendment its own).
    `entry` needs `kind`, `doc_id` and `terms`."""
    found: str = _registrar.scope(dict(entry))
    return found


def fingerprint(text: str) -> str:
    """A document text's sha256 as the register records it (`kernel.fingerprint`, RR-5)."""
    return str(_kernel.fingerprint(text))


def register_result(before: Any, after: Any) -> dict[str, Any]:
    """What one change the registrar admitted wrote, in the shape `register_replay` applies: the
    entry it added (`entry`), or the fields it set on a registered entry (`revocation`: `target`
    and `fields`), with its log line (`log`) and the register's new `version`. Copies."""
    old = {e["doc_id"]: e for e in before.entries}
    out: dict[str, Any] = {"version": after.version, "log": copy.deepcopy(after.log[-1])}
    added = [e for e in after.entries if e["doc_id"] not in old]
    if added:
        return out | {"entry": copy.deepcopy(added[0])}
    for e in after.entries:
        was = old[e["doc_id"]]
        if e != was:
            fields = {k: copy.deepcopy(v) for k, v in e.items() if was.get(k) != v}
            return out | {"revocation": {"target": e["doc_id"], "fields": fields}}
    raise ValueError("the change wrote nothing to the register")


def register_replay(
    corpus: str, results: Sequence[Mapping[str, Any]], text_of: Callable[[str], str]
) -> Any:
    """The registrar's state for the corpus: its bootstrap, then each stored `register_result` in
    order, applied as written. No rule runs (spec §5), so a rule that tightens later never
    un-approves the past. `text_of(sha256)` gives an added entry's approved text. A result whose
    `version` isn't the next one, or a revocation of an entry that isn't there, is a corrupt log."""
    state = _registrar.State.bootstrap(corpus)
    for r in results:
        if "entry" in r:
            entry = copy.deepcopy(dict(r["entry"]))
            state.entries.append(entry)
            state.store[entry["sha256"]] = text_of(entry["sha256"])
        else:
            rev = r["revocation"]
            target = next((e for e in state.entries if e["doc_id"] == rev["target"]), None)
            if target is None:
                raise RuntimeError(f"corrupt log: {rev['target']} revoked but never registered")
            target.update(copy.deepcopy(dict(rev["fields"])))
        state.log.append(copy.deepcopy(dict(r["log"])))
        state.version += 1
        if state.version != r["version"]:
            raise RuntimeError(f"corrupt log: version {r['version']} replayed as {state.version}")
    return state


def register_procedure(
    version: dict[str, Any], employees: set[str], spec_text: str, report_path: Path
) -> tuple[dict[str, Any], str]:
    """One procedure version through the procedure registrar (the admission check): its entry
    and approved text, or `ProcedureRefusedError`. The registrar records the report's path
    relative to the lab root, lexically (`Path.relative_to`), so a report outside it (a temp file)
    is passed as that same file reached from the lab root."""
    reached = LAB_ROOT / os.path.relpath(os.path.realpath(report_path), LAB_ROOT)
    out: tuple[dict[str, Any], str] = _build_procedures.register(
        version, employees, spec_text, reached
    )
    return out


# -- decide -------------------------------------------------------------------------------------
@dataclass(frozen=True)
class KernelResult:
    record: dict[str, Any]  # the record exactly as `governed.decide` returned it
    judgment_about: list[str | None]  # one per `record["judgments"]` item
    flag_items: list[dict[str, Any]]  # one per `record["flags"]` item: {code, text, routes}
    approval_roles: list[dict[str, Any]]
    relied: list[tuple[str, str]]  # (filename, doc_id) of each document the decision relied on
    relied_entries: list[str]  # doc_id of each register entry it read terms from (R21)


def _route(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Every entry deployed with `on_mismatch: route` (G-32), as copies."""
    return [dict(e, deployment={**(e.get("deployment") or {}), "on_mismatch": "route"})
            for e in entries]  # fmt: skip


def decide(
    kind: DecisionType, *, evidence: Any, inputs: dict[str, Any], at: date | datetime,
    register: Any, entries: list[dict[str, Any]], store: Path, engine: ReplayEngine,
    staff: list[dict[str, str]], requested_by: str | None,
    policy_terms: Callable[[str], dict[str, Any] | None], route_mode: bool,
    specs: Path | None = None,
) -> KernelResult:  # fmt: skip
    """The registered procedure in force on `at`, run on `inputs` (discount and credit: `sid`,
    `record`, `as_of`; SLA: `sid`, `ticket_id`, `decided_at`), with what each judgment is about,
    the flags as items and who must approve. `route_mode` deploys every procedure with
    `on_mismatch: route`. `specs` is the directory the kernel checks each version's file in
    (`incident: the procedure file … differs`); the lab's own specs when None. `JevUnavailable`
    propagates; any other failure is `CannotDecide`."""
    subject = str(inputs["ticket_id"] if kind == "sla" else inputs["record"]["request_id"])
    deployed = _route(entries) if route_mode else list(entries)
    trace: dict[str, Any] = {}
    where: dict[str, Any] = {} if specs is None else {"specs": specs}
    try:
        with _additions.capture(subject=subject) as cap:
            record: dict[str, Any] = _governed.decide(
                kind, engine, evidence, inputs, at, register, deployed, store=store, trace=trace,
                **where,
            )  # fmt: skip
        # by identity: the raw record, before any copy
        about: list[str | None] = _additions.judgment_about(record, cap)
        routed = (record["gated_outcome"] == ROUTE_TO[kind]
                  and record["outcome"] != record["gated_outcome"])  # fmt: skip
        items: list[dict[str, Any]] = _additions.flag_items(
            list(record.get("flags") or []), route_mode=route_mode, routed=routed
        )
        policy = (record.get("authority") or {}).get("policy")
        terms = policy_terms(str(policy)) if policy else None
        roles: list[dict[str, Any]] = _additions.approval_roles(
            kind, record, staff, requested_by, terms
        )
    except JevUnavailable:
        raise
    except Exception as e:  # noqa: BLE001 - the kernel couldn't decide; nothing is written
        raise CannotDecide(str(e)) from e
    relied = [(str(f), str(d)) for f, d in trace.get("relied", [])]
    relied_entries = [str(d) for d in trace.get("relied_entries", [])]
    return KernelResult(record, about, items, roles, relied, relied_entries)
