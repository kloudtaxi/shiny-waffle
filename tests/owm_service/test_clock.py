"""The demo clock: starts at the demo time, survives restart, moves forward only."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import owm_service.clock as clock_mod
from owm_service.clock import Clock
from owm_service.events import EventLog

START = "2026-09-23T09:00:00-05:00"


class Wall:
    def __init__(self) -> None:
        self.t = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.t


@pytest.fixture
def wall(monkeypatch: pytest.MonkeyPatch) -> Wall:
    w = Wall()
    monkeypatch.setattr(clock_mod, "_real_now", w)
    return w


def test_clock_starts_at_the_demo_time_and_survives_restart(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    c = Clock(log, "northstar", START)
    assert c.now().isoformat().startswith("2026-09-23T09:00")
    assert c.today().isoformat() == "2026-09-23"
    wall.t += timedelta(minutes=5)
    first = c.now()
    assert first.isoformat().startswith("2026-09-23T09:05")
    wall.t += timedelta(hours=1)
    again = Clock(log, "northstar", "2000-01-01T00:00:00-05:00")  # a restart keeps clock.started
    assert again.now().isoformat().startswith("2026-09-23T10:05")
    assert again.now() >= first
    assert [e.kind for e in log.read("northstar")] == ["clock.started"]


def test_clock_moves_forward_only(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    c = Clock(log, "northstar", START)
    c.now()
    c.set(datetime.fromisoformat("2026-09-25T09:00:00-05:00"), {"id": "ops"})
    assert c.now().isoformat().startswith("2026-09-25T09:00")
    wall.t += timedelta(minutes=2)
    assert Clock(log, "northstar", START).now().isoformat().startswith("2026-09-25T09:02")
    with pytest.raises(ValueError):
        c.set(datetime.fromisoformat("2026-09-24T09:00:00-05:00"), None)
    assert [e.kind for e in log.read("northstar")] == ["clock.started", "clock.set"]


def test_clock_real(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    c = Clock(log, "northstar", "real")
    assert c.now() == wall.t
    assert c.now().utcoffset() == timedelta(hours=-6)  # America/Chicago in January
    wall.t += timedelta(days=1)
    assert c.now() == wall.t
    assert len(log.read("northstar")) == 1


def test_clocks_are_per_org(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    Clock(log, "a", START).now()
    assert Clock(log, "b", "2027-01-01T00:00:00-06:00").now().year == 2027


def test_logged_mode_wins_over_the_constructor(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    Clock(log, "northstar", START).now()
    Clock(log, "northstar", START).set(datetime.fromisoformat("2026-09-25T09:00:00-05:00"), None)
    wall.t += timedelta(minutes=3)
    again = Clock(log, "northstar", "real")
    assert again.now().isoformat().startswith("2026-09-25T09:03")
    again.set(datetime.fromisoformat("2026-09-26T09:00:00-05:00"), None)  # still settable


def test_real_clock_cannot_be_set(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    c = Clock(log, "northstar", "real")
    with pytest.raises(ValueError, match="real"):
        c.set(wall.t + timedelta(days=1), None)
    # a log that began real stays real even if restarted with a fixed start
    assert Clock(log, "northstar", START).now() == wall.t


def test_naive_start_is_rejected(tmp_path: Path, wall: Wall) -> None:
    log = EventLog(tmp_path / "e.db")
    with pytest.raises(ValueError):
        Clock(log, "northstar", "2026-09-23T09:00:00").now()
    assert log.read("northstar") == []
