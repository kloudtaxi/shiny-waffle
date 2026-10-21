"""The fingerprint check, the lab observation and the baseline (R1)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import JsonValue

from preflight.baseline import (
    Baseline,
    baseline_values,
    compared_groups,
    pick_baseline,
)
from preflight.checks.fingerprint import check_fingerprint
from preflight.config import ConfigError
from preflight.observe.lab import lab_values, observe_lab
from preflight.record import (
    BaselineRef,
    CheckResult,
    Compare,
    Group,
    LabRef,
    Record,
    Value,
    write_record,
)


def v(field: str, value: JsonValue, group: Group = "reader", compare: Compare = "equal") -> Value:
    return Value(
        field=field,
        label=field,
        group=group,
        value=value,
        source="t",
        state="read",
        compare=compare,
    )


def _record(values: list[Value], status: str = "pass") -> Record:
    check = CheckResult(name="fingerprint", status="pass", summary="s", values=values)
    return Record(
        run="r",
        started="s",
        finished="f",
        status=status,
        lab=LabRef(commit="c", dirty_paths=[]),
        baseline=BaselineRef(record=None, compared_groups=[]),
        checks=[check],
    )


def baseline_with(run: Path, values: list[Value], same_run: bool = True) -> Baseline:
    rec = _record(values)
    path = write_record(run, rec, datetime(2026, 10, 20, 1, 2, 3, tzinfo=UTC))
    return Baseline(path=path, record=rec, same_run=same_run)


def test_no_baseline_sets_one(run_dir: Path) -> None:
    r = check_fingerprint([v("reader.claude_cli_version", "2.1.299")], None)
    assert r.status == "pass" and "baseline set by this record" in r.summary


def test_a_cli_update_is_drift(run_dir: Path) -> None:
    base = baseline_with(run_dir, [v("reader.claude_cli_version", "2.1.299")])
    r = check_fingerprint([v("reader.claude_cli_version", "2.1.304")], base)
    bad = [x for x in r.values if x.ok is False]
    assert r.status == "fail" and [(x.baseline, x.value) for x in bad] == [("2.1.299", "2.1.304")]


def test_a_matching_field_passes_with_ok_true(run_dir: Path) -> None:
    base = baseline_with(run_dir, [v("reader.model", "opus")])
    r = check_fingerprint([v("reader.model", "opus")], base)
    assert r.status == "pass" and r.values[0].ok is True
    assert "every compared field matches" in r.summary


def test_another_run_s_baseline_compares_reader_and_foundation_only(run_dir: Path) -> None:
    other = baseline_with(
        run_dir.parent / "2026-10-19-other", [v("inputs.questions_sha256", "a", "inputs")], False
    )
    assert compared_groups(other) == {"reader", "foundation"}
    assert check_fingerprint([v("inputs.questions_sha256", "b", "inputs")], other).status == "pass"


def test_an_unread_compared_field_counts_as_differing(run_dir: Path) -> None:
    base = baseline_with(run_dir, [v("foundation.commit", "02e9cc9", "foundation")])
    now = v("foundation.commit", None, "foundation").model_copy(update={"state": "unread"})
    assert check_fingerprint([now], base).status == "fail"


def test_fields_missing_on_either_side_differ(run_dir: Path) -> None:
    base = baseline_with(run_dir, [v("foundation.counts.base.facts", 1880, "foundation")])
    r = check_fingerprint([v("foundation.counts.base.entities", 9, "foundation")], base)
    assert r.status == "fail" and len([x for x in r.values if x.ok is False]) == 2
    assert r.values[0].field == "foundation.counts.base.entities"
    assert r.values[1].state == "unread" and r.values[1].baseline == 1880


def test_record_values_pass_through(run_dir: Path) -> None:
    base = baseline_with(run_dir, [])
    r = check_fingerprint([v("lab.commit", "abc", "lab", "record")], base)
    assert r.status == "pass" and r.values[0].ok is None


def test_baseline_values_without_fingerprint_is_empty() -> None:
    rec = _record([]).model_copy(update={"checks": []})
    assert baseline_values(rec) == {}


def _git(args: list[str]) -> str:
    return {
        "rev-parse": "81f24e8\n",
        "status": " M lab/exam/reader.py\n?? lab/x/__pycache__/a.pyc\n?? runs/r/notes.md\n"
        "?? lab/new.py\n?? lab/newdir/__pycache__/b.pyc\n",
    }[args[0]]


def test_an_uncommitted_lab_patch_fails_clean(tmp_path: Path) -> None:
    obs = observe_lab(tmp_path, _git)
    assert obs.commit == "81f24e8"
    assert obs.dirty_paths == ["lab/exam/reader.py", "lab/new.py"]
    r = check_fingerprint(lab_values(obs), None)
    assert r.status == "fail" and r.values[1].field == "lab.clean"
    assert r.values[1].ok is False


def test_a_clean_tree_passes(tmp_path: Path) -> None:
    obs = observe_lab(tmp_path, lambda a: {"rev-parse": "abc\n", "status": ""}[a[0]])
    assert check_fingerprint(lab_values(obs), None).status == "pass"


def test_latest_is_the_default_baseline(run_dir: Path, repo: Path) -> None:
    for sec, status in ((1, "pass"), (2, "accepted"), (3, "fail")):
        write_record(run_dir, _record([], status), datetime(2026, 10, 20, 0, 0, sec, tzinfo=UTC))
    picked = pick_baseline("latest", run_dir, repo)
    assert picked is not None and picked.same_run
    assert picked.path.name == "2026-10-20T00-00-02Z.json"
    assert picked.record.status == "accepted"


def test_no_records_means_no_baseline(run_dir: Path, repo: Path) -> None:
    assert pick_baseline("latest", run_dir, repo) is None


def test_a_path_baseline_from_another_run(tmp_path: Path, run_dir: Path) -> None:
    other = tmp_path / "runs" / "2026-10-19-other"
    path = write_record(other, _record([]), datetime(2026, 10, 19, 0, 0, 0, tzinfo=UTC))
    got = pick_baseline(str(path.relative_to(tmp_path)), run_dir, tmp_path)
    assert got is not None and not got.same_run
    same = pick_baseline(str(path.relative_to(tmp_path)), other, tmp_path)
    assert same is not None and same.same_run


def test_a_dirty_tree_against_a_baseline_counts_in_the_summary(run_dir: Path) -> None:
    base = baseline_with(run_dir, [v("reader.model", "opus")])
    dirty = observe_lab(run_dir, lambda a: {"rev-parse": "a", "status": " M lab/x.py\n"}[a[0]])
    r = check_fingerprint([v("reader.model", "opus"), *lab_values(dirty)], base)
    assert r.status == "fail"
    assert r.summary == "1 of 2 compared fields differ from the baseline"


def test_no_baseline_summary_names_the_failing_field() -> None:
    dirty = observe_lab(Path("."), lambda a: {"rev-parse": "a", "status": " M lab/x.py\n"}[a[0]])
    r = check_fingerprint(lab_values(dirty), None)
    assert r.summary == "baseline set by this record; Lab code tree clean is False"


def test_a_missing_baseline_path_is_a_config_error(run_dir: Path, repo: Path) -> None:
    with pytest.raises(ConfigError, match="baseline record not found: runs/nope/preflight/x.json"):
        pick_baseline("runs/nope/preflight/x.json", run_dir, repo)


def test_unread_with_unread_baseline_still_fails(run_dir: Path) -> None:
    old = v("foundation.commit", None, "foundation").model_copy(update={"state": "unread"})
    base = baseline_with(run_dir, [old])
    r = check_fingerprint([old], base)
    assert r.status == "fail" and r.values[0].ok is False
