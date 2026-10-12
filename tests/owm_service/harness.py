"""The OWM service tests' window on the lab (test side only).

It loads the committed admission gate (`lab/spec_admission/admit.py`) by path, as
`runs/2026-10-06-procedures-governed/run_governed.py` does, and uses its scenario inputs, its
register and its clean corpora. Jev is replay only: the engine reads every recording under `runs/`
and never goes live, and its own calls file sits in a temp dir, so nothing is written under `runs/`.
The corpora are copied once per test session.

The acceptance suite (§12.2, B-06 Task 15) adds, at the end: an org per scenario (its corpus, its
clock, its row seeded through the overlay), the scenario's request and asker, and the committed
records the kernel's part is held to. This module and `acceptance/` are the only code that reads
the truth; the service never does.
"""

from __future__ import annotations

import atexit
import csv
import functools
import importlib
import importlib.util
import json
import sys
import tempfile
from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

from owm_service.config import DEFAULT_CLOCK, Settings, load_settings
from owm_service.decisions import Decisions
from owm_service.models import Actor, DecisionRecord, DecisionRequest
from owm_service.org import Org
from owm_service.prepare import TABLE
from owm_service.sessions import Sessions

LAB = Path(__file__).resolve().parents[2]

# the 42 decision scenarios, by decision type
DECISIONS: dict[str, list[str]] = {
    "discount": [f"S{n:02d}" for n in (*range(1, 6), *range(9, 26))],
    "credit": [f"S{n}" for n in range(26, 36)],
    "sla": [f"S{n}" for n in range(36, 46)],
}
KIND_OF = {sid: kind for kind, sids in DECISIONS.items() for sid in sids}
ROUTE_TO = {"discount": "REQUEST_EVIDENCE", "credit": "REQUEST_EVIDENCE", "sla": "CANNOT_DECIDE"}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@functools.cache
def admit() -> ModuleType:
    """The admission gate's module. Loading it puts the kernel on `sys.path`."""
    return _load("admit", LAB / "lab/spec_admission/admit.py")


def lab(name: str) -> ModuleType:
    """A kernel module (`kernel`, `flow`, `governed`, `additions`), as the gate imports it."""
    admit()
    return importlib.import_module(name)


@functools.cache
def _tmp() -> Path:
    d = tempfile.TemporaryDirectory(prefix="ns-owm-tests-")
    atexit.register(d.cleanup)
    return Path(d.name)


@functools.cache
def gate() -> Any:
    """The gate, on a replay-only engine (live off, cap 0)."""
    a = admit()
    return a.Gate(a.Layered(_tmp() / "none.jsonl", live=False, cap=0))


@functools.cache
def roots() -> dict[str, Path]:
    """The clean corpora, copied once: corpus name -> root."""
    return dict(gate().clean_roots(_tmp() / "clean"))


def doc_ids(corpus: str) -> set[str]:
    """The doc_id of every document in the corpus."""
    kernel = lab("kernel")
    return {kernel.parse_doc(p.name, p.read_text()).doc_id
            for p in (roots()[corpus] / "documents").glob("*.md")}  # fmt: skip


def inputs(sid: str) -> dict[str, Any]:
    return dict(gate().inputs(KIND_OF[sid], sid))


def corpus(sid: str) -> str:
    return str(gate().corpus(KIND_OF[sid], sid))


def at_of(sid: str) -> Any:
    """The decision's date, as the committed gate run chooses it."""
    inp = inputs(sid)
    return inp.get("as_of") or gate().scen[sid].as_of or inp.get("decided_at")


def subject_of(sid: str) -> str:
    """The request id (discount, credit) or the ticket (SLA)."""
    inp = inputs(sid)
    return str(inp["ticket_id"] if KIND_OF[sid] == "sla" else inp["record"]["request_id"])


@functools.cache
def attacked_roots(attack: str) -> dict[str, Path]:
    """Copies of the corpora with one of set F's sealed attacks in place (`run_set_f.build`, as
    `runs/2026-10-06-register-fixes/check_withhold.py` builds them), built once per attack."""
    setf = admit().setf
    setf.check_seal()
    manifest = yaml.safe_load((setf.SET / "manifest.yaml").read_text())
    at = next(x for x in manifest if x["id"] == attack)
    return dict(setf.build(at, _tmp() / f"set-f-{attack}"))


def entries(sid: str, route: bool = False) -> list[dict[str, Any]]:
    """The procedure register's entries. With `route`, every version of the scenario's decision
    type is deployed in G-32 route mode (`on_mismatch: route`), as run_all.py's `+R` engines are."""
    out = []
    for e in lab("governed").procedures():
        if route and e["decision_type"] == KIND_OF[sid]:
            e = dict(e, deployment={**(e.get("deployment") or {}), "on_mismatch": "route"})
        out.append(e)
    return out


def route_mode(sid: str, route: bool = False) -> bool:
    """Whether the procedure in force for the scenario routes on a mismatch (`on_mismatch`)."""
    governed, flow = lab("governed"), lab("flow")
    entry = governed.in_force(entries(sid, route), KIND_OF[sid], at_of(sid))
    spec = flow.loads((governed.STORE / f"{entry['sha256']}.yaml").read_text(), entry["file"])
    spec["documents"].update(entry.get("deployment") or {})
    return bool(spec["documents"].get("on_mismatch", "use_registered") == "route")


def decide(
    sid: str, trace: dict[str, Any] | None = None, *, attack: str | None = None,
    route: bool = False,
) -> dict[str, Any]:  # fmt: skip
    """`governed.decide` on the scenario's inputs, corpus and register; with `attack`, on that set F
    attack's corpus, and with `route`, under route mode (`entries`)."""
    a, governed, c = admit(), lab("governed"), corpus(sid)
    root = (attacked_roots(attack) if attack else roots())[c]
    kwargs = {} if trace is None else {"trace": trace}
    record: dict[str, Any] = governed.decide(
        KIND_OF[sid], gate().eng, a.Evidence(root), inputs(sid), at_of(sid), a.ra.REG[c],
        entries(sid, route), **kwargs,
    )  # fmt: skip
    return record


def reference(sid: str, trace: dict[str, Any] | None = None) -> dict[str, Any]:
    """The reference record `_lab.decide` must reproduce: `governed.decide` called directly, on
    the scenario's inputs, its clean corpus and the committed register (`decide`, unattacked)."""
    return decide(sid, trace)


def decide_with_capture(sid: str) -> tuple[dict[str, Any], list[str | None]]:
    """The decision, made inside `additions.capture`, and what each of its judgments is about."""
    additions = lab("additions")
    with additions.capture(subject=subject_of(sid)) as cap:
        record = decide(sid)
    about: list[str | None] = additions.judgment_about(record, cap)
    return record, about


def staff(sid: str) -> list[dict[str, str]]:
    """The scenario's corpus staff list (`structured/employees.csv`)."""
    with (roots()[corpus(sid)] / "structured/employees.csv").open() as f:
        return list(csv.DictReader(f))


def roles(sid: str) -> list[dict[str, Any]]:
    """`additions.approval_roles` on the scenario's decision, with the terms of the policy named in
    `authority.policy` from the register (replay only)."""
    kind, record = KIND_OF[sid], decide(sid)
    requested_by = None if kind == "sla" else str(inputs(sid)["record"]["requested_by"])
    policy = (record.get("authority") or {}).get("policy")
    entry = admit().ra.REG[corpus(sid)].by_id().get(policy) if policy else None
    out: list[dict[str, Any]] = lab("additions").approval_roles(
        kind, record, staff(sid), requested_by, entry["terms"] if entry else None
    )
    return out


# -- the acceptance suite (§12.2): an org per scenario, its request, its asker, the records -------
DISCOUNT: list[str] = DECISIONS["discount"]  # S01-S05, S09-S25 (22)
CREDIT: list[str] = DECISIONS["credit"]  # S26-S35
SLA: list[str] = DECISIONS["sla"]  # S36-S45
ALL: list[str] = DISCOUNT + CREDIT + SLA
SLA_ASKER = "EMP-602"  # Marcus Adeyemi, Director of Customer Support, asks every SLA question
HARNESS: dict[str, Any] = {"kind": "system", "id": "harness"}  # who seeds a scenario's row
# the committed records each kind's kernel part is held to, and the fields compared
# (`runs/2026-10-04-specs-as-data/check_equivalence.py`'s lists; discount: experiment 4 v3's rows)
COMMITTED: dict[str, str] = {
    "discount": "runs/2026-10-03-adversarial/hybrid-a-v3.json",
    "credit": "runs/2026-10-03-exp5-credit/hybrid-decisions.json",
    "sla": "runs/2026-10-03-exp6-sla/hybrid-decisions.json",
}
FIELDS: dict[str, tuple[str, ...]] = {
    "discount": ("outcome", "approver", "flags"),
    "credit": ("outcome", "gated_outcome", "uncertain", "eligibility", "authority", "approvers",
               "flags"),
    "sla": ("outcome", "gated_outcome", "uncertain", "scope", "severity", "breach", "credit_usd",
            "obligations", "account_owner", "flags"),
}  # fmt: skip


def scenario(sid: str) -> Any:
    """The scenario as the truth states it."""
    return gate().scen[sid]


def expected(sid: str) -> dict[str, Any]:
    """The scenario's hand-authored `expected:`. `northstar build` refuses to write unless the
    oracle's result equals it (`oracle.check`), so it is the oracle's answer too."""
    return dict(scenario(sid).expected)


def scenario_settings(sid: str, tmp: Path) -> Settings:
    """A fresh org's settings for the scenario: its own state dir, its corpus (SLA: `base`), and
    the clock at the scenario's `decided_at` (S45), else the service's default."""
    at = scenario(sid).decided_at
    return load_settings({"OWM_STATE_DIR": str(tmp / "state"), "OWM_CORPUS": corpus(sid),
                          "OWM_CLOCK": at.isoformat() if at else DEFAULT_CLOCK})  # fmt: skip


def record_of(sid: str) -> dict[str, str]:
    """The request row the reference decides on (discount: `heldout.record` with the S03 list-price
    fix; credit: `x5.record`)."""
    return dict(inputs(sid)["record"])


def seed(org: Org, sid: str) -> None:
    """Put the scenario's request row in the org's systems of record. Only DR-9001 and CR-9201 are
    in the CSVs, and they must hold the reference's row; every other request is inserted through
    the overlay. The SLA tickets are all in `service_tickets.csv` already."""
    kind, tables = KIND_OF[sid], {str(k): v for k, v in TABLE.items()}
    if kind == "sla":
        assert org.sor.row(tables["sla"], subject_of(sid)) is not None
        return
    rec, table = record_of(sid), tables[kind]
    row = org.sor.row(table, rec["request_id"])
    if row is not None:
        assert rec["request_id"] in ("DR-9001", "CR-9201"), rec["request_id"]
        assert {k: row[k] for k in rec} == rec  # the CSV holds the very row the reference reads
        return
    at = org.clock.now()  # before the write: never first read inside one
    with org.log.transaction() as tx:
        org.sor.insert(tx, table, rec, actor=HARNESS, at=at)


def scenario_org(sid: str, tmp: Path) -> Org:
    """A fresh org for the scenario, its row seeded."""
    org = Org(scenario_settings(sid, tmp))
    seed(org, sid)
    return org


def _wire(v: Any) -> Any:
    return v.isoformat() if isinstance(v, date | datetime) else v


def request_for(sid: str) -> DecisionRequest:
    """`POST /decisions` for the scenario: only the subject's id, and the scenario's `submitted`
    (the truth uses the contract's names) for discount and credit."""
    kind = KIND_OF[sid]
    key = "ticket" if kind == "sla" else "request_id"
    raw: dict[str, Any] = {"decision_type": kind, "subject": {key: subject_of(sid)}}
    submitted = scenario(sid).submitted
    if kind != "sla" and submitted is not None:
        raw["submitted"] = {k: _wire(v) for k, v in submitted.items()}
    return DecisionRequest.model_validate(raw)


def asker(org: Org, sid: str) -> Actor:
    """The person who asks: the requester the row names (discount, credit), Marcus for SLA."""
    if KIND_OF[sid] == "sla":
        emp = SLA_ASKER
    else:
        who = org.people.by_email(record_of(sid)["requested_by"])
        assert who is not None
        emp = who.id
    return Sessions(org).open_person(emp)[1]


def ask(org: Org, sid: str) -> DecisionRecord:
    """The scenario's version 1, asked by its asker."""
    return Decisions(org).ask(asker(org, sid), request_for(sid))


def kernel_part(org: Org, v1: DecisionRecord) -> dict[str, Any]:
    """The kernel's record for version 1, exactly as the service stored it."""
    return Decisions(org).kernel_record(v1.decision_id, 1)


def plain(x: Any) -> Any:
    """JSON-plain, as the service stores the kernel's record: dates as ISO strings, sets sorted."""

    def default(o: Any) -> Any:
        if isinstance(o, date | datetime):
            return o.isoformat()
        if isinstance(o, set | frozenset):
            return sorted(o)
        raise TypeError(f"{type(o).__name__} is not JSON-serialisable")

    return json.loads(json.dumps(x, default=default, allow_nan=False))


def strip(record: Mapping[str, Any]) -> dict[str, Any]:
    """A record without `scenario`, the one key that carries the caller's id."""
    return {k: v for k, v in record.items() if k != "scenario"}


@functools.cache
def _committed(kind: str) -> dict[str, dict[str, Any]]:
    data = json.loads((LAB / COMMITTED[kind]).read_text())
    if kind != "discount":
        return dict(data)
    return {r["scenario"]: r for r in data if r["attack"] == "clean"}


def committed_fields(sid: str) -> tuple[str, ...]:
    return FIELDS[KIND_OF[sid]]


def committed(sid: str) -> dict[str, Any]:
    """The committed record's compared fields. Experiment 4's clean rows stop at S21; S22 to S25
    ask about DR-9001 as S01 does, so they are held to S01's row."""
    kind = KIND_OF[sid]
    rows = _committed(kind)
    key = sid if sid in rows else "S01"
    assert key == sid or sid in ("S22", "S23", "S24", "S25"), sid
    return {k: rows[key][k] for k in committed_fields(sid)}


def committed_view(sid: str, record: Mapping[str, Any]) -> dict[str, Any]:
    """A kernel record's fields under the committed record's names. Experiment 4's discount rows
    hold `outcome` (the gated outcome), `approver` (`authority.approver`) and `flags` (or [])."""
    if KIND_OF[sid] == "discount":
        return {"outcome": record["gated_outcome"],
                "approver": (record.get("authority") or {}).get("approver"),
                "flags": record.get("flags", [])}  # fmt: skip
    return {k: record[k] for k in committed_fields(sid)}
