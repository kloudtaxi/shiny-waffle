"""One spend cap per run folder, held across processes and threads (G-50, R6 incident 2).

Every reader process used to total its own spend. Here the recorded cost on disk and the live
reservations of every process are summed under one `fcntl.flock`, so no process can overshoot.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import time
import uuid
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import TracebackType
from typing import Any, Self

_JUDGE = re.compile(r"^(?P<prefix>.*)\.judge(?:\.infra-(?P<k>\d+))?\.json$")


class CapReached(Exception):  # noqa: N818 - the name is the interface
    """Reserving the next call would push the run folder past its cap."""


@dataclass(frozen=True)
class ReservationInfo:
    path: Path
    pid: int
    label: str
    item: str
    est_usd: float
    cap_usd: float
    started: str
    settled_usd: float | None


def run_folder_of(path: Path) -> Path:
    """The ancestor of `path` whose parent is named `runs`."""
    for candidate in (path, *path.parents):
        if candidate.parent.name == "runs":
            return candidate
    raise ValueError(f"{path} is not inside a runs/<run> folder")


def _events(text: str) -> Iterator[dict[str, Any]]:
    for line in text.splitlines():
        if not line.strip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def result_cost(text: str) -> float:
    """`total_cost_usd` of the first result event, or 0.0 (same as exam.reader)."""
    for event in _events(text):
        if event.get("type") == "result":
            return float(event.get("total_cost_usd") or 0)
    return 0.0


def _judge_cost(path: Path) -> float:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return 0.0
    total = 0.0
    for reading in data.get("readings", []) if isinstance(data, dict) else []:
        for run in reading.get("runs", []):
            cost = run.get("cost_usd")
            if isinstance(cost, int | float) and not isinstance(cost, bool):
                total += float(cost)
    return total


def recorded_usd(run: Path) -> float:
    """Everything already written under the run folder, counted once."""
    spend_dir = run / ".spend"
    total = 0.0
    for path in sorted(run.rglob("*.jsonl")):
        if path.name.endswith(".calls.jsonl") or spend_dir in path.parents:
            continue
        try:
            total += result_cost(path.read_text(errors="replace"))
        except OSError:
            continue
    # Judge files (P3): per snapshot prefix, `.judge.json` else the newest infra-<k>.
    chosen: dict[tuple[Path, str], tuple[int, Path]] = {}
    for path in run.rglob("*.judge*.json"):
        m = _JUDGE.match(path.name)
        if m is None or spend_dir in path.parents:
            continue
        rank = int(m["k"]) if m["k"] is not None else 1 << 62
        key = (path.parent, m["prefix"])
        if key not in chosen or rank > chosen[key][0]:
            chosen[key] = (rank, path)
    for _, path in chosen.values():
        total += _judge_cost(path)
    return total


def _inflight(run: Path) -> Path:
    return run / ".spend" / "inflight"


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def live_reservations(run: Path) -> list[ReservationInfo]:
    """Reservations whose process is alive; files of dead processes are removed."""
    found: list[ReservationInfo] = []
    folder = _inflight(run)
    if not folder.is_dir():
        return found
    for path in folder.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            info = ReservationInfo(path=path, **data)
        except (OSError, json.JSONDecodeError, TypeError):
            continue
        if not _alive(info.pid):
            path.unlink(missing_ok=True)
            continue
        found.append(info)
    return sorted(found, key=lambda i: i.started)


@contextlib.contextmanager
def _locked(run: Path) -> Iterator[None]:
    """An exclusive flock on a fresh file descriptor, so threads contend too."""
    (run / ".spend").mkdir(parents=True, exist_ok=True)
    with open(run / ".spend" / "lock", "a+") as fd:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def _write_info(info: ReservationInfo) -> None:
    data = asdict(info)
    del data["path"]
    tmp = info.path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    os.replace(tmp, info.path)


class Reservation:
    """A held slice of the cap; a context manager that releases on exit."""

    def __init__(self, run: Path, info: ReservationInfo) -> None:
        self._run = run
        self._info = info

    def settle(self, cost_usd: float) -> None:
        """Count this reservation at its real cost until it is released."""
        with _locked(self._run):
            if self._info.path.exists():
                self._info = ReservationInfo(**{**asdict(self._info), "settled_usd": cost_usd})
                _write_info(self._info)

    def release(self) -> None:
        # Under the lock, so a reserve never sees the answer file missing and the
        # reservation gone (T4-c), and settle cannot resurrect a released file.
        with _locked(self._run):
            self._info.path.unlink(missing_ok=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()


class Guard:
    def __init__(self, run: Path, cap_usd: float, est_usd: float, label: str) -> None:
        self.run = run
        self.cap_usd = cap_usd
        self.est_usd = est_usd
        self.label = label

    def reserve(self, item: str) -> Reservation:
        with _locked(self.run):
            recorded = recorded_usd(self.run)
            live = sum(
                r.settled_usd if r.settled_usd is not None else r.est_usd
                for r in live_reservations(self.run)
            )
            if recorded + live + self.est_usd > self.cap_usd:
                raise CapReached(
                    f"spend guard: ${recorded:.2f} recorded + ${live:.2f} running + "
                    f"${self.est_usd:.2f} next > ${self.cap_usd:.2f} cap"
                )
            pid = os.getpid()
            folder = _inflight(self.run)
            folder.mkdir(parents=True, exist_ok=True)
            info = ReservationInfo(
                path=folder / f"{pid}-{uuid.uuid4().hex}.json",
                pid=pid,
                label=self.label,
                item=item,
                est_usd=self.est_usd,
                cap_usd=self.cap_usd,
                started=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                settled_usd=None,
            )
            _write_info(info)
        return Reservation(self.run, info)


def spend_view(run: Path) -> str:
    """The run folder's spend, for people: recorded, running, and the caps in use."""
    live = live_reservations(run)
    running = sum(r.settled_usd if r.settled_usd is not None else r.est_usd for r in live)
    lines = [
        f"recorded: ${recorded_usd(run):.2f}",
        f"running: ${running:.2f} across {len(live)} reservations",
    ]
    now = time.time()
    for r in live:
        cost = r.settled_usd if r.settled_usd is not None else r.est_usd
        started = datetime.strptime(r.started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        age = int(now - started.timestamp())
        lines.append(f"  pid {r.pid} {r.label} {r.item} ${cost:.2f} {age}s")
    caps = sorted({r.cap_usd for r in live})
    lines.append("caps in use: " + (", ".join(f"${c:.2f}" for c in caps) or "none"))
    return "\n".join(lines)
