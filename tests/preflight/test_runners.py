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
from tests.preflight.fakes import stream

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


def test_blind_reader_requires_a_cap(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # A variant is named: argparse rejects the default variants list against `choices` (a
    # separate, older quirk), which is how this test used to pass without `required=True`.
    argv = ["blind_reader", "run", "--run", "x", "--out", "y", "B1"]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as e:
        blind_reader.main()
    assert e.value.code == 2
    err = capsys.readouterr().err  # F-15: argparse refused it for want of --cap-usd
    assert "the following arguments are required: --cap-usd" in err


def test_blind_reader_probe_prompt_asks_who_and_when() -> None:
    assert (
        "(3) say who you work for, and today's date, if you know them." in blind_reader.PROBE_PROMPT
    )


def test_blind_reader_shares_the_one_probe_writer() -> None:
    assert blind_reader.write_probe_out is reader.write_probe_out


def test_judge_requires_a_cap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["judge", str(tmp_path / "s.json")])
    with pytest.raises(SystemExit) as e:
        judge.main()
    assert e.value.code == 2
    err = capsys.readouterr().err  # F-15: argparse refused it for want of --cap-usd
    assert "the following arguments are required: --cap-usd" in err


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


# --- final review (F-12, F-15) -----------------------------------------------------------------


class _StopError(Exception):
    """Raised by a fake to end `main` once the step under test has passed."""


def test_blind_reader_refuses_an_out_outside_the_guarded_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)

    def no_token(name: str, kbs: list[str]) -> tuple[str, str]:
        raise AssertionError("a token was minted")

    monkeypatch.setattr(blind_reader, "mint_token", no_token)
    argv = ["blind_reader", "run", "--run", str(run), "--out", str(tmp_path / "arm-b")]
    monkeypatch.setattr(sys, "argv", [*argv, "--cap-usd", "5", "B1"])
    with pytest.raises(SystemExit) as e:
        blind_reader.main()
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "--out" in err and "inside --run" in err


def test_blind_reader_accepts_an_out_inside_the_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    (run / "questions.tsv").write_text("id\tkb\tquestion\nS01\tk\tq\n")

    def stop(name: str, kbs: list[str]) -> tuple[str, str]:
        raise _StopError

    monkeypatch.setattr(blind_reader, "mint_token", stop)
    argv = ["blind_reader", "run", "--run", str(run), "--out", str(run / "arm-b")]
    monkeypatch.setattr(sys, "argv", [*argv, "--cap-usd", "5", "B1"])
    with pytest.raises(_StopError):
        blind_reader.main()


def test_blind_reader_s_probe_records_the_flags_it_ran_with(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run = tmp_path / "runs" / "r"
    run.mkdir(parents=True)
    (run / "questions.tsv").write_text("id\tkb\tquestion\nS01\tk\tq\n")
    out = tmp_path / "probe-out"
    turns: list[int] = []

    def fake_reader(
        token: str, kb: str, prompt: str, allowed: list[str], hidden: list[str], model: str,
        max_turns: int = blind_reader.MAX_TURNS, **kw: Any,
    ) -> str:  # fmt: skip
        turns.append(max_turns)
        return stream(init={"tools": []}, answer="I don't know.")

    monkeypatch.setattr(blind_reader, "mint_token", lambda name, kbs: ("tok", "tid"))
    monkeypatch.setattr(blind_reader, "revoke", lambda tid: None)
    monkeypatch.setattr(blind_reader, "mcp_tools", lambda token, kb: [{"name": "find_entities"}])
    monkeypatch.setattr(blind_reader, "reader", fake_reader)
    monkeypatch.setenv("PREFLIGHT_PROBE_OUT", str(out))
    monkeypatch.setattr(sys, "argv", ["blind_reader", "probe", "--run", str(run)])
    blind_reader.main()
    meta = json.loads((out / "probe.json").read_text())
    assert turns and meta["flags"] == blind_reader.flags_for(turns[0])
    assert f"--max-turns {turns[0]};" in meta["flags"]
    assert meta["flags"] == blind_reader.FLAGS  # the probe runs as a counted call: no cite warning
