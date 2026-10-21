"""The settled check: the foundation's background work is finished, read or attested."""

from __future__ import annotations

from preflight.foundations import FoundationSnapshot
from preflight.foundations.attest import Attestation
from preflight.record import CheckResult, State, Value

_LABEL = {"utopia": "Utopia", "b20": "B-20"}


def _fmt(n: int) -> str:
    return f"{n:,}"


def _hours(h: float) -> str:
    return f"{h:g}"


def _signal(
    name: str,
    read: bool,
    dirty: str | None,
    attest: Attestation | None,
    problems: list[str],
) -> tuple[State, object]:
    """Resolve one signal to a state and a value, adding any problem."""
    if read:
        if dirty is not None:
            problems.append(dirty)
            return "read", dirty
        return "read", "clean"
    if attest is not None and attest.fresh and name in attest.covers:
        return "attested", "clean"
    if attest is not None and not attest.fresh and name in attest.covers:
        problems.append(f"{name}: attestation older than {_hours(attest.max_age_hours)} h")
    else:
        problems.append(f"{name}: not readable here and not attested")
    return "unread", None


def check_settled(
    kind: str,
    first: FoundationSnapshot,
    second: FoundationSnapshot,
    attest: Attestation | None,
    window_seconds: float,
) -> CheckResult:
    """Pass when jobs, documents and the log are clean and counts held across both reads."""
    if kind == "local":
        return CheckResult(
            name="settled", status="n/a", summary="not applicable (local foundation)"
        )
    problems: list[str] = []
    s = second

    jobs_dirty: str | None = None
    jobs_read = s.jobs_active is not None and s.jobs_failed_since is not None
    if jobs_read:
        parts: list[str] = []
        if s.jobs_active:
            parts.append(
                f"{s.jobs_active} job{'s' if s.jobs_active != 1 else ''} queued or running"
            )
        if s.jobs_failed_since:
            n = s.jobs_failed_since
            at = first.at.strftime("%H:%M")
            parts.append(f"{n} job{'s' if n != 1 else ''} failed since {at} UTC")
        if parts:
            problems.extend(parts)
            jobs_dirty = "; ".join(parts)
    jobs_state, jobs_val = _signal("jobs", jobs_read, None, attest, problems)
    if jobs_dirty is not None:
        jobs_val = jobs_dirty

    docs_dirty = None
    if s.documents_unfinished:
        n = s.documents_unfinished
        docs_dirty = f"{n} document{'s' if n != 1 else ''} not finished"
    docs_state, docs_val = _signal(
        "documents", s.documents_unfinished is not None, docs_dirty, attest, problems
    )

    log_dirty = None
    if s.log_errors:
        log_dirty = f"provider errors in the server log: {len(s.log_errors)}"
    log_state, log_val = _signal("log", s.log_errors is not None, log_dirty, attest, problems)

    moved = [
        f"{k} {_fmt(first.counts.get(k, 0))} → {_fmt(second.counts.get(k, 0))}"
        for k in sorted(set(first.counts) | set(second.counts))
        if first.counts.get(k, 0) != second.counts.get(k, 0)
    ]
    if moved:
        problems.append("counts moved during the window: " + "; ".join(moved))

    src = f"foundation {kind}"
    values = [
        Value(field="settled.jobs", label="Jobs settled", group="foundation", value=jobs_val,
              source=src, state=jobs_state),
        Value(field="settled.documents", label="Documents settled", group="foundation",
              value=docs_val, source=src, state=docs_state),
        Value(field="settled.log", label="Log clean", group="foundation", value=log_val,
              source=src, state=log_state),
        Value(field="settled.counts", label="Counts steady", group="foundation",
              value=not moved, source=src, state="read twice"),
    ]  # fmt: skip

    name = _LABEL.get(kind, kind)
    if problems:
        return CheckResult(
            name="settled", status="fail", summary=f"{name} not settled: {len(problems)} problems",
            values=values, problems=problems,
        )  # fmt: skip
    secs = f"{window_seconds:g}"
    signals = {"jobs": jobs_state, "documents": docs_state, "log": log_state}
    attested = [k for k, v in signals.items() if v == "attested"]
    read = [k for k, v in signals.items() if v == "read"]
    tail = []
    if read:
        tail.append(f"{', '.join(read)} read")
    if attested and attest is not None:
        tail.append(f"{', '.join(attested)} attested ({attest.path})")
    summary = " · ".join([name, f"counts stable {secs} s", *tail])
    return CheckResult(name="settled", status="pass", summary=summary, values=values)


def foundation_values(
    kind: str, snap: FoundationSnapshot, attest: Attestation | None
) -> list[Value]:
    """The foundation facts the fingerprint compares."""
    name = _LABEL.get(kind, kind)
    src = f"foundation {kind}"
    out: list[Value] = []
    if snap.binary_sha256 is not None:
        out.append(Value(field="foundation.binary_sha256", label=f"{name} binary sha256",
                         group="foundation", value=snap.binary_sha256, source=src,
                         state="read", compare="equal"))  # fmt: skip
    for k, v in sorted(snap.settings.items()):
        out.append(Value(field=f"foundation.settings.{k}", label=f"{name} setting {k}",
                         group="foundation", value=v, source=src, state="read",
                         compare="equal"))  # fmt: skip
    for k, n in sorted(snap.counts.items()):
        out.append(Value(field=f"foundation.counts.{k}", label=f"{name} count {k}",
                         group="foundation", value=n, source=src, state="read",
                         compare="equal"))  # fmt: skip
    if kind == "b20":
        ok = attest is not None and "commit" in attest.covers
        out.append(Value(
            field="foundation.commit", label=f"{name} commit", group="foundation",
            value=attest.commit if ok and attest is not None else None,
            source=attest.path if ok and attest is not None else src,
            state="attested" if ok else "unread", compare="equal",
        ))  # fmt: skip
    return out
