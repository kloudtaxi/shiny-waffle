"""Records are write-once; the amendment line is exact."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

import pytest
from pydantic import JsonValue

from preflight.record import (
    BaselineRef,
    CheckResult,
    Compare,
    LabRef,
    ProbeRef,
    Record,
    RecordError,
    Value,
    amendment_line,
    append_amendment,
    drift_text,
    latest_record,
    load_record,
    record_name,
    write_record,
)

AT = datetime(2026, 10, 21, 9, 14, 2, tzinfo=UTC)


def sample_record(status: Literal["pass", "fail", "accepted"] = "pass") -> Record:
    return Record(
        run="2026-10-21-test",
        started="2026-10-21T09:14:00Z",
        finished="2026-10-21T09:14:02Z",
        status=status,
        lab=LabRef(commit="abc1234", dirty_paths=[]),
        baseline=BaselineRef(record=None, compared_groups=["lab"]),
        checks=[CheckResult(name="inputs", status="pass", summary="ok")],
    )


def value(
    field: str,
    label: str,
    v: JsonValue,
    baseline: JsonValue = None,
    compare: Compare = "equal",
) -> Value:
    return Value(
        field=field,
        label=label,
        group="lab",
        value=v,
        source="test",
        state="read",
        compare=compare,
        baseline=baseline,
    )


def test_names_are_utc_even_from_another_zone() -> None:
    est = AT.astimezone(timezone(timedelta(hours=-4)))
    assert record_name(est) == "2026-10-21T09-14-02Z.json"


def test_a_naive_time_is_a_programming_error(run_dir: Path) -> None:
    with pytest.raises(ValueError):
        record_name(datetime(2026, 10, 21, 9, 14, 2))
    with pytest.raises(ValueError):
        write_record(run_dir, sample_record(), datetime(2026, 10, 21, 9, 14, 2))


def test_a_record_is_written_once(run_dir: Path) -> None:
    p = write_record(run_dir, sample_record(), AT)
    assert p == run_dir / "preflight" / "2026-10-21T09-14-02Z.json"
    before = p.read_bytes()
    with pytest.raises(FileExistsError):
        write_record(run_dir, sample_record(status="fail"), AT)
    assert p.read_bytes() == before
    assert json.loads(before)["schema"] == 1
    assert load_record(p) == sample_record()


def test_latest_skips_failed_records_and_probe_streams(run_dir: Path) -> None:
    write_record(run_dir, sample_record(status="pass"), AT)
    write_record(run_dir, sample_record(status="fail"), AT + timedelta(minutes=1))
    (run_dir / "preflight" / "2026-10-21T09-20-00Z.probe.jsonl").write_text("{}\n")
    path, rec = latest_record(run_dir) or pytest.fail("none")
    assert path.name == "2026-10-21T09-14-02Z.json" and rec.status == "pass"
    assert latest_record(run_dir, frozenset({"fail"}))[1].status == "fail"  # type: ignore[index]


def test_latest_is_none_without_records(run_dir: Path) -> None:
    assert latest_record(run_dir) is None


def test_the_amendment_line_is_exact() -> None:
    drift = [
        value("reader.claude_cli_version", "claude --version", "2.1.304", baseline="2.1.299"),
        value("foundation.counts.base.facts", "B-20 base facts", 1880, baseline=1912),
    ]
    assert amendment_line(AT, drift, "CLI auto-updated", "preflight/2026-10-21T09-14-02Z.json") == (
        "- **Amendment (pre-flight drift, 2026-10-21 09:14 UTC):** claude --version 2.1.299 → "
        "2.1.304; B-20 base facts 1,912 → 1,880. Reason: CLI auto-updated. "
        "Record: preflight/2026-10-21T09-14-02Z.json."
    )


def test_a_field_without_a_baseline_shows_its_value() -> None:
    v = value("lab.clean", "lab tree clean", False, compare="true")
    assert "lab tree clean: false" in amendment_line(AT, [v], "r", "x")


def test_lists_render_as_counts() -> None:
    v = value("lab.dirty", "dirty paths", ["a", "b"], compare="true")
    assert "dirty paths: [2 items]" in amendment_line(AT, [v], "r", "x")


def test_drift_text_is_the_amendment_s_rendering() -> None:
    moved = value("foundation.counts.base.facts", "B-20 base facts", 1880, baseline=1912)
    clean = value("lab.clean", "lab tree clean", False, compare="true")
    assert drift_text(moved) == "B-20 base facts 1,912 → 1,880"
    assert drift_text(clean) == "lab tree clean: false"
    line = amendment_line(AT, [moved, clean], "r", "x")
    assert f"{drift_text(moved)}; {drift_text(clean)}. Reason: r." in line


def test_a_probe_ref_records_its_estimate() -> None:
    assert ProbeRef(stream=None, cost_usd=0.05).estimate_usd is None  # older records still load
    assert ProbeRef(stream=None, cost_usd=0.05, estimate_usd=0.25).estimate_usd == 0.25


def test_appending_keeps_every_earlier_byte(run_dir: Path, tmp_path: Path) -> None:
    notes = run_dir / "notes.md"
    notes.write_text("# Notes\nno newline at end")
    append_amendment(notes, "- line")
    assert notes.read_text() == "# Notes\nno newline at end\n- line\n"
    fresh = tmp_path / "new" / "notes.md"
    fresh.parent.mkdir()
    append_amendment(fresh, "- line")  # a missing notes.md is created
    assert fresh.read_text() == "- line\n"


# --- final review (F-6): a crash mid-write bricks nothing --------------------------------------


def test_a_crash_before_the_record_is_named_leaves_no_record(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def crash(fd: int) -> None:
        raise OSError("disk went away")

    monkeypatch.setattr("preflight.record.os.fsync", crash)  # after the write, before the name
    with pytest.raises(OSError, match="disk went away"):
        write_record(run_dir, sample_record(), AT)
    assert list((run_dir / "preflight").iterdir()) == []  # no record, no temp file
    assert latest_record(run_dir) is None


def test_a_stray_temp_file_is_not_a_record(run_dir: Path) -> None:
    folder = run_dir / "preflight"
    folder.mkdir()
    (folder / ".2026-10-21T09-14-02Z.json.k3j2.tmp").write_text("")  # a killed writer's leftover
    assert latest_record(run_dir) is None
    path = write_record(run_dir, sample_record(), AT)
    assert load_record(path) == sample_record()


def test_a_written_record_is_whole_and_still_write_once(run_dir: Path) -> None:
    path = write_record(run_dir, sample_record(), AT)
    assert json.loads(path.read_text())["status"] == "pass"
    with pytest.raises(FileExistsError):
        write_record(run_dir, sample_record("fail"), AT)
    assert load_record(path).status == "pass"
    assert sorted(p.name for p in path.parent.iterdir()) == [path.name]


def test_an_unreadable_record_s_error_names_it(run_dir: Path) -> None:
    folder = run_dir / "preflight"
    folder.mkdir()
    (folder / "2026-10-21T09-14-02Z.json").write_text("")
    with pytest.raises(
        RecordError, match=r"^unreadable pre-flight record 2026-10-21T09-14-02Z\.json: "
    ):
        latest_record(run_dir)
    with pytest.raises(RecordError, match="2026-10-21T09-14-02Z.json"):
        load_record(folder / "2026-10-21T09-14-02Z.json")
