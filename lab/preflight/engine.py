"""The engine: run the collectors, build the checks, write the record and any amendment.

`evaluate` observes and judges and writes nothing but the probe's own stream (and its spend
reservation, released before it returns). `finish` turns an evaluation into one write-once record
and, when drift is accepted, one appended line in notes.md. Both front ends call these two.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from preflight.baseline import Baseline, compared_groups, pick_baseline
from preflight.checks.agent_context import check_agent_context, reader_values
from preflight.checks.fingerprint import check_fingerprint
from preflight.checks.inputs import check_inputs, inputs_values
from preflight.checks.settled import check_settled, foundation_values
from preflight.config import (
    AgentContextConfig,
    CheckName,
    FoundationConfig,
    InputsConfig,
    RunConfig,
)
from preflight.foundations import Foundation, FoundationSnapshot
from preflight.foundations import make_foundation as _make_foundation
from preflight.foundations.attest import Attestation, read_attestation
from preflight.markers import Markers, redact
from preflight.markers import default_markers as _default_markers
from preflight.observe.inputs import InputsObservation
from preflight.observe.inputs import observe_inputs as _observe_inputs
from preflight.observe.lab import LabObservation, lab_values
from preflight.observe.lab import observe_lab as _observe_lab
from preflight.observe.probe import ProbeObservation
from preflight.observe.probe import claude_cli_version as _claude_cli_version
from preflight.observe.probe import run_probe as _run_probe
from preflight.record import (
    Accepted,
    BaselineRef,
    CheckResult,
    Group,
    LabRef,
    ProbeRef,
    Record,
    Value,
    amendment_line,
    append_amendment,
    record_name,
    write_record,
)
from preflight.spend import CapReached, Guard

ORDER: tuple[CheckName, ...] = ("inputs", "fingerprint", "settled", "agent_context")
GROUPS: tuple[Group, ...] = ("lab", "inputs", "reader", "foundation")
STEP_SECONDS = 5.0
RETRIES = 5
UNREAD_COMMIT = "unread"


@dataclass(frozen=True)
class Event:
    """Progress for a front end. May arrive from a worker thread; the receiver marshals."""

    check: str
    kind: Literal["started", "progress", "done"]
    text: str
    result: CheckResult | None = None


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _local_date(t: datetime) -> date:
    """The operator's local date at `t`: what an agent on this machine is told is today."""
    return t.astimezone().date()


@dataclass
class Deps:
    """Everything with I/O or a clock, so tests can pass fakes."""

    observe_inputs: Callable[[InputsConfig, Path, Path], InputsObservation] = _observe_inputs
    observe_lab: Callable[[Path], LabObservation] = _observe_lab
    make_foundation: Callable[[FoundationConfig, Path, Path], Foundation] = _make_foundation
    run_probe: Callable[[AgentContextConfig, Path, Path, Markers, datetime], ProbeObservation] = (
        _run_probe
    )
    claude_version: Callable[[], str | None] = _claude_cli_version
    markers: Callable[[Path, list[date]], Markers] = _default_markers
    now: Callable[[], datetime] = _now_utc
    local_date: Callable[[datetime], date] = _local_date
    sleep: Callable[[float], None] = time.sleep


@dataclass(frozen=True)
class Evaluation:
    """One evaluation's results, in check order; `drift` is the fingerprint's `ok is False`."""

    started: datetime
    finished: datetime
    checks: list[CheckResult]
    lab: LabObservation
    baseline: Baseline | None
    probe: ProbeRef | None
    drift: list[Value]
    # In memory only, for `finish` to redact problems with (F-7). Never serialise it.
    markers: Markers = field(default_factory=lambda: Markers({}), repr=False)


@dataclass(frozen=True)
class Outcome:
    """The record written, where, and why an acceptance was refused or not needed."""

    record: Record
    path: Path
    note: str | None


@dataclass(frozen=True)
class _FoundationRead:
    first: FoundationSnapshot | None = None
    second: FoundationSnapshot | None = None
    attest: Attestation | None = None
    problems: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _ProbeRead:
    obs: ProbeObservation | None  # None when the probe step itself broke
    cli: str | None
    ran: bool  # whether run_probe produced `obs` (not a spend-guard refusal)
    problem: str | None = None


def describe_exc(exc: BaseException) -> str:
    """`Type: first line of the message (≤200 chars)`, or just `Type` when there is no message."""
    first = (str(exc).splitlines() or [""])[0][:200]
    return f"{type(exc).__name__}: {first}" if first else type(exc).__name__


def _could_not_read(exc: BaseException) -> str:
    """The single problem a collector's exception becomes."""
    return f"could not read: {describe_exc(exc)}"


def _failed(name: CheckName, problems: list[str]) -> CheckResult:
    return CheckResult(name=name, status="fail", summary=problems[0], problems=problems)


def repo_relative(path: Path, repo: Path) -> str:
    """`path` relative to the repo when it is inside it, else as given."""
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def _iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _wait_window(
    first_at: datetime, window: float, deps: Deps, emit: Callable[[Event], None]
) -> None:
    """Sleep until `first_at + window`, in steps, reporting progress. Bounded by the step count."""
    now = deps.now()
    deadline = min(first_at, now) + timedelta(seconds=window)
    for _ in range(math.ceil(window / STEP_SECONDS) + 2):
        left = (deadline - now).total_seconds()
        if left <= 0:
            return
        done = max(0, int(window - left))
        emit(Event("settled", "progress", f"counts stable {done} of {window:g} s"))
        deps.sleep(min(STEP_SECONDS, left))
        now = deps.now()


def _read_foundation(
    cfg: FoundationConfig,
    run: Path,
    repo: Path,
    deps: Deps,
    started: datetime,
    window: float | None,
    emit: Callable[[Event], None],
) -> _FoundationRead:
    """The first snapshot; with a window, the wait and the second; then any attestation."""
    try:
        foundation = deps.make_foundation(cfg, run, repo)
        first = foundation.snapshot(started)
    except Exception as exc:
        return _FoundationRead(problems=[_could_not_read(exc)])
    second: FoundationSnapshot | None = None
    problems: list[str] = []
    if window is not None and cfg.kind != "local":
        _wait_window(first.at, window, deps, emit)  # outside the try: an emit error is a bug
        try:
            second = foundation.snapshot(first.at)
        except Exception as exc:
            problems.append(_could_not_read(exc))
    attest: Attestation | None = None
    if cfg.attest is not None:
        try:
            attest = read_attestation(cfg.attest, run, deps.now())
        except Exception as exc:
            problems.append(_could_not_read(exc))
    return _FoundationRead(first, second, attest, problems)


def _read_probe(
    cfg: AgentContextConfig,
    run: Path,
    repo: Path,
    markers: Markers,
    started: datetime,
    deps: Deps,
) -> _ProbeRead:
    """Run the probe inside a spend reservation, released once its stream is on disk."""
    try:
        cli = deps.claude_version()
    except Exception:
        cli = None
    try:
        reservation = Guard(run, cfg.cap_usd, cfg.est_usd, "preflight").reserve("probe")
    except CapReached as exc:
        return _ProbeRead(ProbeObservation("", {}, None, None, str(exc)), cli, ran=False)
    except Exception as exc:
        return _ProbeRead(None, cli, ran=False, problem=_could_not_read(exc))
    with reservation:
        try:
            obs = deps.run_probe(cfg, run, repo, markers, started)
        except Exception as exc:
            return _ProbeRead(None, cli, ran=False, problem=_could_not_read(exc))
    return _ProbeRead(obs, cli, ran=True)


def evaluate(
    run: Path,
    repo: Path,
    cfg: RunConfig,
    deps: Deps,
    on_event: Callable[[Event], None],
) -> Evaluation:
    """Observe the run's setup and judge it. Raises ConfigError for a missing baseline record."""
    listed = set(cfg.checks)
    started = deps.now()
    baseline = pick_baseline(cfg.baseline, run, repo)  # before anything runs or costs
    for name in ORDER:
        if name in listed:
            on_event(Event(name, "started", "running"))

    # Always read: `finish` redacts every check's problems with them (F-7). Today is both the
    # operator's local date and the UTC date (F-1).
    markers = Markers({})
    markers_problem: str | None = None
    try:
        days = list(dict.fromkeys([deps.local_date(started), started.astimezone(UTC).date()]))
        markers = deps.markers(repo, days)
    except Exception as exc:
        markers_problem = _could_not_read(exc)

    results: dict[CheckName, CheckResult] = {}

    def done(result: CheckResult) -> None:
        results[result.name] = result
        on_event(Event(result.name, "done", result.summary, result))

    inputs_obs: InputsObservation | None = None
    inputs_problem: str | None = None
    found = _FoundationRead()
    probe = _ProbeRead(None, None, ran=False)

    with ThreadPoolExecutor(4) as pool:
        lab_f = pool.submit(deps.observe_lab, repo)
        inputs_f: Future[InputsObservation] | None = None
        found_f: Future[_FoundationRead] | None = None
        probe_f: Future[_ProbeRead] | None = None
        if {"inputs", "fingerprint"} & listed and cfg.inputs is not None:
            inputs_f = pool.submit(deps.observe_inputs, cfg.inputs, run, repo)
        if {"settled", "fingerprint"} & listed and cfg.foundation is not None:
            window = cfg.settled.window_seconds if "settled" in listed else None
            found_f = pool.submit(
                _read_foundation, cfg.foundation, run, repo, deps, started, window, on_event
            )
        if "agent_context" in listed and cfg.agent_context is not None:
            if markers_problem is not None:
                probe = _ProbeRead(None, None, ran=False, problem=markers_problem)
            else:
                probe_f = pool.submit(
                    _read_probe, cfg.agent_context, run, repo, markers, started, deps
                )

        # Each check is judged as soon as its collector returns, so a front end sees it early.
        pending: list[Future[Any]] = [f for f in (inputs_f, found_f, probe_f) if f is not None]
        for fut in as_completed(pending):
            if inputs_f is not None and fut is inputs_f and cfg.inputs is not None:
                try:
                    inputs_obs = inputs_f.result()
                except Exception as exc:
                    inputs_problem = _could_not_read(exc)
                if "inputs" in listed:
                    if inputs_obs is not None:
                        done(check_inputs(inputs_obs, cfg.inputs))
                    else:
                        done(_failed("inputs", [inputs_problem or "inputs not read"]))
            elif found_f is not None and fut is found_f:
                found = found_f.result()  # its collectors' exceptions are already problems
                if "settled" in listed:
                    done(_settled(cfg, found))
            elif probe_f is not None and fut is probe_f:
                probe = probe_f.result()
                done(_agent_context(probe, repo, markers))
        if "agent_context" in listed and "agent_context" not in results:
            done(_agent_context(probe, repo, markers))

        fp_problems: list[str] = []
        lab_read = True
        try:
            lab = lab_f.result()
        except Exception as exc:
            lab = LabObservation(commit=UNREAD_COMMIT, dirty_paths=[])
            lab_read = False
            fp_problems.append(_could_not_read(exc))

    drift: list[Value] = []
    if "fingerprint" in listed:
        values: list[Value] = []
        if lab_read:
            values += lab_values(lab)
        if inputs_obs is not None:
            values += inputs_values(inputs_obs)
        elif inputs_problem is not None and "inputs" not in listed:
            fp_problems.append(inputs_problem)
        if probe.ran and probe.obs is not None:  # a refused or broken probe read nothing
            values += reader_values(probe.obs, probe.cli, markers)
        snap = found.second if found.second is not None else found.first
        if snap is not None and cfg.foundation is not None:
            values += foundation_values(cfg.foundation.kind, snap, found.attest)
        if found.problems and "settled" not in listed:
            fp_problems.extend(found.problems)
        fp = check_fingerprint(values, baseline)
        if fp_problems:
            fp = fp.model_copy(
                update={
                    "status": "fail",
                    "summary": fp_problems[0],
                    "problems": [*fp_problems, *fp.problems],
                }
            )
        drift = [v for v in fp.values if v.ok is False]
        done(fp)

    probe_ref: ProbeRef | None = None
    if probe.ran and probe.obs is not None and cfg.agent_context is not None:
        stream = None if probe.obs.saved is None else repo_relative(probe.obs.saved, repo)
        probe_ref = ProbeRef(
            stream=stream, cost_usd=probe.obs.cost_usd, estimate_usd=cfg.agent_context.est_usd
        )
    return Evaluation(
        started=started,
        finished=deps.now(),
        checks=[results[n] for n in ORDER if n in results],
        lab=lab,
        baseline=baseline,
        probe=probe_ref,
        drift=drift,
        markers=markers,
    )


def _agent_context(probe: _ProbeRead, repo: Path, markers: Markers) -> CheckResult:
    if probe.obs is None:
        return _failed("agent_context", [probe.problem or "the probe did not run"])
    return check_agent_context(probe.obs, repo, markers)


def _settled(cfg: RunConfig, found: _FoundationRead) -> CheckResult:
    assert cfg.foundation is not None
    kind = cfg.foundation.kind
    if found.problems or found.first is None:
        return _failed("settled", found.problems or ["foundation not read"])
    second = found.second if found.second is not None else found.first
    if kind != "local" and found.second is None:
        return _failed("settled", ["foundation not read a second time"])
    return check_settled(kind, found.first, second, found.attest, cfg.settled.window_seconds)


def _status(ev: Evaluation, reason: str) -> tuple[Literal["pass", "fail", "accepted"], str | None]:
    """§6 and P5: pass, accepted (fingerprint drift only, with a reason), or fail with a note."""
    counted = [c for c in ev.checks if c.status != "n/a"]
    failing = [c for c in counted if c.status == "fail"]
    if not failing:
        return "pass", ("nothing drifted; no amendment written" if reason else None)
    if not reason:
        return "fail", None
    fp = next((c for c in failing if c.name == "fingerprint"), None)
    if fp is not None and fp.problems:
        return "fail", (
            "drift can be accepted only when the fingerprint read everything "
            f"({fp.problems[0]}); no amendment written"
        )
    if not ev.drift:
        return "fail", "nothing drifted; no amendment written"
    others = [c.name for c in failing if c.name != "fingerprint"]
    if others:
        return "fail", (
            "drift can be accepted only when the other checks pass "
            f"({', '.join(others)} failed); no amendment written"
        )
    return "accepted", None


REDACTED_KINDS = frozenset({"operator", "home", "repo"})  # not dates: record times hold them


def _redacted(checks: list[CheckResult], markers: Markers) -> list[CheckResult]:
    """Every check's summary and problems without operator, home or repo values (F-7)."""
    return [
        c.model_copy(
            update={
                "summary": redact(c.summary, markers, REDACTED_KINDS),
                "problems": [redact(p, markers, REDACTED_KINDS) for p in c.problems],
            }
        )
        for c in checks
    ]


def finish(
    run: Path,
    repo: Path,
    ev: Evaluation,
    accept_reason: str | None,
    deps: Deps,
    *,
    at: datetime | None = None,
) -> Outcome:
    """Write the evaluation's record once; on accepted drift, append the amendment to notes.md.

    `at` names the record and stamps the amendment (default: now), so a front end can preview
    the exact line it will write (T12-a). A taken name moves on a second at a time. Problems and
    summaries are redacted before they are written (F-7).
    """
    reason = " ".join((accept_reason or "").split())  # T2-a: an amendment stays one line
    status, note = _status(ev, reason)
    checks = _redacted(ev.checks, ev.markers)
    if note is not None:  # it may quote a problem: shown as the record shows it
        note = redact(note, ev.markers, REDACTED_KINDS)
    has_fp = any(c.name == "fingerprint" for c in ev.checks)
    groups = compared_groups(ev.baseline) if has_fp else frozenset()
    at = deps.now() if at is None else at
    for k in range(RETRIES + 1):
        when = at + timedelta(seconds=k)
        accepted: Accepted | None = None
        line: str | None = None
        if status == "accepted":
            line = amendment_line(when, ev.drift, reason, f"preflight/{record_name(when)}")
            accepted = Accepted(reason=reason, fields=[v.field for v in ev.drift], amendment=line)
        record = Record(
            run=run.name,
            started=_iso(ev.started),
            finished=_iso(ev.finished),
            status=status,
            lab=LabRef(commit=ev.lab.commit, dirty_paths=list(ev.lab.dirty_paths)),
            baseline=BaselineRef(
                record=None if ev.baseline is None else repo_relative(ev.baseline.path, repo),
                compared_groups=[g for g in GROUPS if g in groups],
            ),
            checks=checks,
            accepted=accepted,
            probe=ev.probe,
        )
        try:
            path = write_record(run, record, when)
        except FileExistsError:
            continue
        if line is not None:
            append_amendment(run / "notes.md", line)
        return Outcome(record=record, path=path, note=note)
    raise FileExistsError(f"no free record name near {record_name(at)}")


def run_preflight(
    run: Path,
    repo: Path,
    cfg: RunConfig,
    *,
    accept_reason: str | None = None,
    deps: Deps | None = None,
    on_event: Callable[[Event], None] = lambda e: None,
) -> Outcome:
    """Evaluate, then finish: the plain front end's whole job."""
    deps = deps or Deps()
    return finish(run, repo, evaluate(run, repo, cfg, deps, on_event), accept_reason, deps)
