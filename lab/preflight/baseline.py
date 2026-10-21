"""Choosing the baseline a run is compared against (R1: latest passing or accepted record)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from preflight.config import ConfigError
from preflight.record import Group, Record, Value, latest_record, load_record


@dataclass(frozen=True)
class Baseline:
    path: Path
    record: Record
    same_run: bool


def pick_baseline(spec: str, run: Path, repo: Path) -> Baseline | None:
    """`latest` is the run's newest pass/accepted record; otherwise a repo-relative record path."""
    if spec == "latest":
        found = latest_record(run)
        return None if found is None else Baseline(found[0], found[1], True)
    path = repo / spec
    if not path.is_file():
        raise ConfigError(f"baseline record not found: {spec}")
    same = path.parent.parent.resolve() == run.resolve()
    return Baseline(path, load_record(path), same)


def compared_groups(baseline: Baseline | None) -> frozenset[Group]:
    """Another run's baseline says nothing about this run's questions or evidence."""
    if baseline is not None and not baseline.same_run:
        return frozenset({"reader", "foundation"})
    return frozenset({"inputs", "reader", "foundation"})


def baseline_values(record: Record) -> dict[str, Value]:
    """The fingerprint check's values in `record`, by field."""
    for check in record.checks:
        if check.name == "fingerprint":
            return {v.field: v for v in check.values}
    return {}
