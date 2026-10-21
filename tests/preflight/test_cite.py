"""The exam reader cites the latest pre-flight record and warns, never blocks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from preflight.cite import cite_preflight
from preflight.record import (
    BaselineRef,
    CheckResult,
    LabRef,
    Record,
    Value,
    write_record,
)

AT = datetime(2026, 10, 21, 9, 14, 2, tzinfo=UTC)
MIN = timedelta(minutes=1)


def record_with(
    *, status: Literal["pass", "fail", "accepted"], q: str, model: str, flags: str
) -> Record:
    def v(field: str, value: str) -> Value:
        return Value(
            field=field, label=field, group="reader", value=value, source="t", state="read"
        )

    return Record(
        run="r",
        started="2026-10-21T09:14:00Z",
        finished="2026-10-21T09:14:02Z",
        status=status,
        lab=LabRef(commit="abc1234", dirty_paths=[]),
        baseline=BaselineRef(record=None, compared_groups=["reader"]),
        checks=[
            CheckResult(
                name="fingerprint",
                status="pass",
                summary="ok",
                values=[
                    v("inputs.questions_sha256", q),
                    v("reader.model", model),
                    v("reader.flags", flags),
                ],
            )
        ],
    )


def test_no_record_warns(run_dir: Path) -> None:
    c = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.58)
    assert c == {
        "record": None,
        "status": "missing",
        "estimate_usd": 1.58,
        "warnings": ["no pre-flight record in preflight/"],
    }


def test_a_matching_record_is_cited_without_warnings(run_dir: Path) -> None:
    p = write_record(run_dir, record_with(status="pass", q="q", model="m", flags="f"), AT)
    c = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)
    assert c["record"] == str(p.relative_to(run_dir))
    assert c["status"] == "pass" and c["warnings"] == []


def test_a_failed_or_mismatched_record_warns(run_dir: Path) -> None:
    write_record(run_dir, record_with(status="fail", q="q", model="m", flags="f"), AT)
    assert (
        "the latest pre-flight record failed"
        in cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)[
            "warnings"
        ]
    )
    write_record(run_dir, record_with(status="pass", q="other", model="m2", flags="f"), AT + MIN)
    w = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)["warnings"]
    assert w == [
        "the pre-flight checked another questions file",
        "the pre-flight checked another model",
    ]
    write_record(run_dir, record_with(status="pass", q="q", model="m", flags="x"), AT + 2 * MIN)
    w = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)["warnings"]
    assert w == ["the pre-flight checked other flags"]


def test_an_unreadable_record_warns_and_does_not_raise(run_dir: Path) -> None:
    folder = run_dir / "preflight"
    folder.mkdir()
    (folder / "2026-10-21T09-14-02Z.json").write_text("{garbage")
    c = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)
    assert c == {
        "record": None,
        "status": "unreadable",
        "estimate_usd": 1.0,
        "warnings": ["the latest pre-flight record could not be read"],
    }


def test_a_record_without_a_fingerprint_gets_one_warning(run_dir: Path) -> None:
    rec = record_with(status="pass", q="q", model="m", flags="f")
    rec = rec.model_copy(update={"checks": []})
    write_record(run_dir, rec, AT)
    c = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)
    assert c["warnings"] == ["the pre-flight record has no fingerprint"]
