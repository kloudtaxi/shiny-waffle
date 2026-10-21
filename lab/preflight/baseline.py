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
    """`latest` is the run's newest pass/accepted record; otherwise a repo-relative record path.

    A record without a fingerprint check holds nothing to compare with, so it is no baseline
    (F-10): this evaluation's record sets one.
    """
    if spec == "latest":
        found = latest_record(run)
        if found is None:
            return None
        path, record = found
        same = True
    else:
        path = repo / spec
        if not path.is_file():
            raise ConfigError(f"baseline record not found: {spec}")
        record = load_record(path)
        same = path.parent.parent.resolve() == run.resolve()
    if not any(c.name == "fingerprint" for c in record.checks):
        return None
    return Baseline(path, record, same)


def compared_groups(baseline: Baseline | None) -> frozenset[Group]:
    """No baseline compares nothing; another run's says nothing about this run's inputs."""
    if baseline is None:
        return frozenset()
    if not baseline.same_run:
        return frozenset({"reader", "foundation"})
    return frozenset({"inputs", "reader", "foundation"})


def baseline_values(record: Record) -> dict[str, Value]:
    """The fingerprint check's values in `record`, by field."""
    for check in record.checks:
        if check.name == "fingerprint":
            return {v.field: v for v in check.values}
    return {}
