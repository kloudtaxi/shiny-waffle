"""The settled check: read, attested, or fail."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from preflight.checks.settled import check_settled, foundation_values
from preflight.config import Attest
from preflight.foundations import FoundationSnapshot
from preflight.foundations.attest import Attestation, read_attestation

NOW = datetime(2026, 10, 21, 9, 30, tzinfo=UTC)


def snap(**kw: Any) -> FoundationSnapshot:
    base: dict[str, Any] = {
        "at": NOW,
        "counts": {"base.facts": 1880},
        "settings": {},
        "binary_sha256": None,
        "jobs_active": 0,
        "jobs_failed_since": 0,
        "documents_unfinished": 0,
        "log_errors": [],
    }
    base.update(kw)
    return FoundationSnapshot(**base)


def make_attest(
    tmp_path: Path, kind: str | None, line: str = "commit: 02e9cc9"
) -> Attestation | None:
    if kind is None:
        return None
    run = tmp_path / "run"
    (run / "attest").mkdir(parents=True)
    f = run / "attest" / "b20-settled.md"
    f.write_text(f"settled by hand\n{line}\n")
    age = timedelta(hours=3) if kind == "stale" else timedelta(minutes=5)
    ts = (NOW - age).timestamp()
    os.utime(f, (ts, ts))
    cfg = Attest(
        file="attest/b20-settled.md", max_age_hours=2, covers=["jobs", "log", "documents", "commit"]
    )
    return read_attestation(cfg, run, NOW)


def test_counts_moving_in_the_window_fail() -> None:
    r = check_settled("utopia", snap(), snap(counts={"base.facts": 1912}), None, 60)
    assert r.status == "fail"
    assert "counts moved during the window: base.facts 1,880 → 1,912" in r.problems


def test_utopia_settled_when_every_signal_reads_clean() -> None:
    r = check_settled("utopia", snap(), snap(), None, 60)
    assert r.status == "pass" and all(v.state in ("read", "read twice") for v in r.values)


@pytest.mark.parametrize("attest, status", [(None, "fail"), ("stale", "fail"), ("fresh", "pass")])
def test_b20_needs_a_fresh_attestation(tmp_path: Path, attest: str | None, status: str) -> None:
    b = snap(jobs_active=None, jobs_failed_since=None, documents_unfinished=None, log_errors=None)
    a = make_attest(tmp_path, attest)
    r = check_settled("b20", b, b, a, 60)
    assert r.status == status
    if status == "pass":
        assert {v.state for v in r.values if v.field != "settled.counts"} == {"attested"}
    if attest == "stale":
        assert any("attestation older than 2 h" in p for p in r.problems)
    if attest is None:
        assert "jobs: not readable here and not attested" in r.problems


def test_attestation_age_is_utc(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    f = run / "a.md"
    f.write_text("x\n")
    ts = (NOW - timedelta(hours=1)).timestamp()
    os.utime(f, (ts, ts))
    local = NOW.astimezone(timezone(timedelta(hours=-4)))
    ok = read_attestation(Attest(file="a.md", max_age_hours=2, covers=["jobs"]), run, local)
    old = read_attestation(Attest(file="a.md", max_age_hours=0.5, covers=["jobs"]), run, local)
    assert ok is not None and ok.fresh
    assert old is not None and not old.fresh


def test_missing_attestation_is_none(tmp_path: Path) -> None:
    cfg = Attest(file="nope.md", max_age_hours=2, covers=["jobs"])
    assert read_attestation(cfg, tmp_path, NOW) is None


def test_attested_commit_is_read_from_the_note(tmp_path: Path) -> None:
    a = make_attest(tmp_path, "fresh")
    assert a is not None and a.commit == "02e9cc9"
    assert a.covers == frozenset({"jobs", "log", "documents", "commit"})


def test_local_is_not_applicable() -> None:
    r = check_settled("local", snap(), snap(), None, 60)
    assert r.status == "n/a" and r.summary == "not applicable (local foundation)"


def test_provider_errors_in_the_log_fail() -> None:
    r = check_settled("utopia", snap(), snap(log_errors=["…429…"]), None, 60)
    assert r.status == "fail" and any("provider errors" in p for p in r.problems)


def test_dirty_jobs_and_documents_are_named() -> None:
    r = check_settled(
        "utopia", snap(), snap(jobs_active=2, jobs_failed_since=1, documents_unfinished=3), None, 60
    )
    assert "2 jobs queued or running" in r.problems
    assert "1 job failed since 09:30 UTC" in r.problems
    assert "3 documents not finished" in r.problems


def test_foundation_values(tmp_path: Path) -> None:
    s = snap(settings={"w.chat_model": "m"}, binary_sha256="ab")
    vals = {v.field: v for v in foundation_values("utopia", s, None)}
    assert vals["foundation.binary_sha256"].compare == "equal"
    assert vals["foundation.settings.w.chat_model"].label.startswith("Utopia")
    assert vals["foundation.counts.base.facts"].value == 1880
    assert "foundation.commit" not in vals
    b = {v.field: v for v in foundation_values("b20", snap(), make_attest(tmp_path, "fresh"))}
    assert b["foundation.commit"].state == "attested" and b["foundation.commit"].value == "02e9cc9"
    none = {v.field: v for v in foundation_values("b20", snap(), None)}
    assert none["foundation.commit"].state == "unread"


@pytest.mark.parametrize(
    "line",
    ["commit: 02e9cc9", "commit: `02e9cc9`", "**commit:** 02e9cc9", "Commit: 02e9cc9",
     "- commit: 02e9cc9", "commit: 02E9CC9"],
)  # fmt: skip
def test_commit_line_forms(tmp_path: Path, line: str) -> None:
    a = make_attest(tmp_path, "fresh", line)
    assert a is not None and a.commit == "02e9cc9"


def test_commit_unread_without_line_or_when_stale(tmp_path: Path) -> None:
    a = make_attest(tmp_path, "fresh", "no commit here")
    assert a is not None and a.commit is None
    v = {x.field: x for x in foundation_values("b20", snap(), a)}
    assert v["foundation.commit"].state == "unread"
    stale = make_attest(tmp_path / "s", "stale")
    v = {x.field: x for x in foundation_values("b20", snap(), stale)}
    assert v["foundation.commit"].state == "unread"


def test_utopia_binary_hash_is_always_listed() -> None:
    v = {x.field: x for x in foundation_values("utopia", snap(binary_sha256=None), None)}
    assert v["foundation.binary_sha256"].state == "unread"
    assert v["foundation.binary_sha256"].value is None


def test_attestation_details_reach_the_record(tmp_path: Path) -> None:
    b = snap(jobs_active=None, jobs_failed_since=None, documents_unfinished=None, log_errors=None)
    a = make_attest(tmp_path, "fresh")
    assert a is not None
    r = check_settled("b20", b, b, a, 60)
    v = {x.field: x for x in r.values}
    assert v["settled.attestation"].value == {
        "path": a.path, "sha256": a.sha256, "mtime": a.mtime,
    }  # fmt: skip
    assert v["settled.jobs"].source == a.path


def test_fail_summary_counts_problems() -> None:
    r = check_settled("utopia", snap(), snap(jobs_active=1), None, 60)
    assert r.summary.endswith("1 problem")
