"""blind_reader and the judge share the spend guard (G-50, Task 11)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from exam import (
    judge,
    reader,  # noqa: F401  (puts lab/utopia on sys.path)
)
from preflight.spend import live_reservations, recorded_usd

import blind_reader  # noqa: E402  isort: skip


def _snapshot(tmp_path: Path) -> tuple[Path, Path]:
    run = tmp_path / "runs" / "r"
    (run / "part1").mkdir(parents=True)
    snap = run / "part1" / "s.json"
    snap.write_text("{}")
    return run, snap


def _one_reading(monkeypatch: pytest.MonkeyPatch) -> None:
    reading = {
        "part": "p1",
        "id": "I1",
        "u31": False,
        "reading": "stated",
        "statement": "s",
        "facts": "f",
    }
    monkeypatch.setattr(judge, "readings", lambda snap: [dict(reading)])


def test_blind_reader_requires_a_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["blind_reader", "run", "--run", "x", "--out", "y"])
    with pytest.raises(SystemExit) as e:
        blind_reader.main()
    assert e.value.code == 2  # argparse: --cap-usd is required


def test_blind_reader_probe_prompt_asks_who_and_when() -> None:
    assert (
        "(3) say who you work for, and today's date, if you know them." in blind_reader.PROBE_PROMPT
    )


def test_blind_reader_shares_the_one_probe_writer() -> None:
    assert blind_reader.write_probe_out is reader.write_probe_out


def test_judge_requires_a_cap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys, "argv", ["judge", str(tmp_path / "s.json")])
    with pytest.raises(SystemExit) as e:
        judge.main()
    assert e.value.code == 2


def test_judge_settles_each_call_and_releases_after_writing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run, snap = _snapshot(tmp_path)
    _one_reading(monkeypatch)
    seen_settled: list[list[float]] = []

    def ask(statement: str, facts: str) -> dict[str, Any]:
        seen_settled.append(
            [r.settled_usd for r in live_reservations(run) if r.settled_usd is not None]
        )
        return {"verdict": "stated", "cost_usd": 0.02}

    monkeypatch.setattr(judge, "ask", ask)
    monkeypatch.setattr(
        sys, "argv", ["judge", str(snap), "--runs", "2", "--workers", "1", "--cap-usd", "1"]
    )
    judge.main()
    assert seen_settled[-1] == [0.02]  # the first call's settled cost is live at the second
    assert live_reservations(run) == []
    assert recorded_usd(run) == pytest.approx(0.04)


def test_judge_refusal_skips_a_reading_and_says_so(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run, snap = _snapshot(tmp_path)
    _one_reading(monkeypatch)
    (run / "S00.jsonl").write_text(json.dumps({"type": "result", "total_cost_usd": 1.0}) + "\n")
    calls: list[str] = []

    def ask(statement: str, facts: str) -> dict[str, Any]:
        calls.append(statement)
        return {"verdict": "stated", "cost_usd": 0.02}

    monkeypatch.setattr(judge, "ask", ask)
    monkeypatch.setattr(
        sys, "argv", ["judge", str(snap), "--runs", "1", "--workers", "1", "--cap-usd", "1.0"]
    )
    judge.main()
    assert "skipped: spend guard:" in capsys.readouterr().out and calls == []
