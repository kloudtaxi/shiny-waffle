"""The demo clock: demo time, monotonic across restarts (spec §5).

State lives in the event log. The base is the latest `clock.set` (`{"to", "wall"}`) or otherwise
`clock.started` (`{"start", "wall"}`); `now()` is the base time plus the real time since the
base's `wall`. With `start == "real"`, `now()` is the real now. Demo time is shown in
America/Chicago.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from .events import EventLog

DEMO_TZ = ZoneInfo("America/Chicago")
_STREAM = "clock"


def _real_now() -> datetime:
    return datetime.now(UTC)


class Clock:
    def __init__(self, log: EventLog, org: str, start: str) -> None:
        self.log = log
        self.org = org
        self.start = start

    def _base(self, tx: sqlite3.Connection | None = None) -> tuple[datetime, datetime, bool] | None:
        """(demo time at the base, wall time at the base, is real), or None before the start.

        The logged `clock.started` decides the mode; the constructor's `start` is only used to
        write that event when the org has none.
        """
        base: tuple[datetime, datetime, bool] | None = None
        real = False
        for ev in self.log.read(self.org, stream=_STREAM, tx=tx):
            if ev.kind == "clock.started" and base is None:
                wall = datetime.fromisoformat(ev.payload["wall"])
                start = ev.payload["start"]
                real = start == "real"
                base = (wall if real else datetime.fromisoformat(start), wall, real)
            elif ev.kind == "clock.set":
                base = (
                    datetime.fromisoformat(ev.payload["to"]),
                    datetime.fromisoformat(ev.payload["wall"]),
                    real,
                )
        return base

    def _ensure_started(self) -> tuple[datetime, datetime, bool]:
        base = self._base()
        if base is not None:
            return base
        with self.log.transaction() as tx:
            base = self._base(tx)
            if base is None:
                wall = _real_now()
                at = wall if self.start == "real" else datetime.fromisoformat(self.start)
                if at.tzinfo is None:
                    raise ValueError("the clock start needs an offset")
                self.log.append(
                    tx,
                    at=at.astimezone(DEMO_TZ),
                    wall=wall,
                    org=self.org,
                    stream=_STREAM,
                    kind="clock.started",
                    actor=None,
                    payload={"start": self.start, "wall": wall.isoformat()},
                )
                base = self._base(tx)
        assert base is not None
        return base

    def now(self) -> datetime:
        at, wall, real = self._ensure_started()
        if real:
            return _real_now().astimezone(DEMO_TZ)
        return (at + (_real_now() - wall)).astimezone(DEMO_TZ)

    def today(self) -> date:
        return self.now().date()

    def set(self, to: datetime, actor: dict[str, Any] | None) -> None:
        """Move demo time forward to `to`; an earlier time raises ValueError."""
        if to.tzinfo is None:
            raise ValueError("the clock needs a time with an offset")
        self._ensure_started()
        with self.log.transaction() as tx:
            base = self._base(tx)
            assert base is not None
            if base[2]:
                raise ValueError("the clock is real; it can't be set")
            wall = _real_now()
            current = base[0] + (wall - base[1])
            if to < current:
                raise ValueError(f"the clock moves forward only: {to.isoformat()} < {current}")
            self.log.append(
                tx,
                at=to.astimezone(DEMO_TZ),
                wall=wall,
                org=self.org,
                stream=_STREAM,
                kind="clock.set",
                actor=actor,
                payload={"to": to.isoformat(), "wall": wall.isoformat()},
            )
