"""Write-once pre-flight records and the append-only drift amendment line."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from preflight.config import CheckName

Group = Literal["lab", "inputs", "reader", "foundation"]
State = Literal["read", "read twice", "attested", "unread"]
Compare = Literal["equal", "record", "true"]

_NAME = re.compile(r"^\d{4}-\d\d-\d\dT\d\d-\d\d-\d\dZ\.json$")


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Value(_Model):
    """One observed fact about the run's setup."""

    field: str
    label: str
    group: Group
    value: JsonValue
    source: str
    state: State
    compare: Compare = "record"
    baseline: JsonValue = None
    ok: bool | None = None


class CheckResult(_Model):
    name: CheckName
    status: Literal["pass", "fail", "n/a"]
    summary: str
    values: list[Value] = []
    problems: list[str] = []


class LabRef(_Model):
    commit: str
    dirty_paths: list[str]


class BaselineRef(_Model):
    record: str | None
    compared_groups: list[Group]


class Accepted(_Model):
    reason: str
    fields: list[str]
    amendment: str


class ProbeRef(_Model):
    """`stream` is the repo-relative path of the saved probe stream, or None if none was saved."""

    stream: str | None
    cost_usd: float | None


class Record(_Model):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_version: int = Field(1, alias="schema")
    run: str
    started: str
    finished: str
    status: Literal["pass", "fail", "accepted"]
    lab: LabRef
    baseline: BaselineRef
    checks: list[CheckResult]
    accepted: Accepted | None = None
    probe: ProbeRef | None = None


def _utc(at: datetime) -> datetime:
    if at.tzinfo is None or at.utcoffset() is None:
        raise ValueError("a record time must be timezone-aware")
    return at.astimezone(UTC)


def record_name(at: datetime) -> str:
    """The UTC file name for a record written at `at`."""
    return _utc(at).strftime("%Y-%m-%dT%H-%M-%SZ.json")


def write_record(run: Path, record: Record, at: datetime) -> Path:
    """Write a record once; an existing name raises FileExistsError."""
    folder = run / "preflight"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / record_name(at)
    text = json.dumps(record.model_dump(by_alias=True, mode="json"), indent=1, ensure_ascii=False)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(text + "\n")
    return path


def load_record(path: Path) -> Record:
    return Record.model_validate_json(path.read_text(encoding="utf-8"))


def latest_record(
    run: Path, statuses: frozenset[str] = frozenset({"pass", "accepted"})
) -> tuple[Path, Record] | None:
    """The newest record whose status is in `statuses`, or None."""
    folder = run / "preflight"
    if not folder.is_dir():
        return None
    for path in sorted((p for p in folder.iterdir() if _NAME.match(p.name)), reverse=True):
        record = load_record(path)
        if record.status in statuses:
            return path, record
    return None


def _fmt(v: JsonValue) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, list):
        return f"[{len(v)} items]"
    return str(v)


def amendment_line(at: datetime, drifted: list[Value], reason: str, record_rel: str) -> str:
    """The one-line note appended to notes.md when drift is accepted."""
    parts = [
        f"{v.label}: {_fmt(v.value)}"
        if v.baseline is None
        else f"{v.label} {_fmt(v.baseline)} → {_fmt(v.value)}"
        for v in drifted
    ]
    stamp = _utc(at).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"- **Amendment (pre-flight drift, {stamp}):** {'; '.join(parts)}. "
        f"Reason: {reason}. Record: {record_rel}."
    )


def append_amendment(notes: Path, line: str) -> None:
    """Append `line` to notes.md, never touching earlier bytes; create it if missing."""
    needs_break = False
    if notes.exists() and notes.stat().st_size > 0:
        with notes.open("rb") as fh:
            fh.seek(-1, 2)
            needs_break = fh.read(1) != b"\n"
    with notes.open("a", encoding="utf-8") as fh:
        fh.write(("\n" if needs_break else "") + line + "\n")
