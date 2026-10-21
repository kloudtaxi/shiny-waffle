"""The exam reader cites the latest pre-flight record and warns, never blocks."""

from __future__ import annotations

import ast
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

import pytest

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


# --- final review (F-3): blind_reader stays standard-library only ------------------------------


def test_cite_without_the_record_module_is_unreadable(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "preflight.record", None)  # importing it raises
    c = cite_preflight(run_dir, questions_sha256="q", model="m", flags="f", est_usd=1.0)
    assert c["status"] == "unreadable" and c["record"] is None


def test_cite_and_spend_import_only_the_standard_library(repo: Path) -> None:
    for name in ("cite.py", "spend.py"):
        tree = ast.parse((repo / "lab/preflight" / name).read_text())
        top: list[str] = []
        for node in tree.body:  # module level only; a lazy import inside a function is fine
            if isinstance(node, ast.Import):
                top += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                top.append(node.module)
        roots = {t.split(".")[0] for t in top} - {"__future__"}
        assert roots <= sys.stdlib_module_names, (name, roots - sys.stdlib_module_names)


def test_blind_reader_runs_without_pydantic_or_yaml(repo: Path, tmp_path: Path) -> None:
    script = repo / "lab/utopia/blind_reader.py"
    code = "\n".join(
        [
            "import runpy, sys",
            "sys.modules['pydantic'] = None",
            "sys.modules['yaml'] = None",
            f"sys.path.insert(0, {str(script.parent)!r})",
            "sys.argv = ['blind_reader', '--help']",
            f"runpy.run_path({str(script)!r}, run_name='__main__')",
        ]
    )
    done = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, cwd=tmp_path
    )
    assert done.returncode == 0, done.stderr
    assert "usage: blind_reader" in done.stdout
