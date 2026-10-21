"""Worker for the multi-process spend test (spawned, so importable by name)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from preflight.spend import CapReached, Guard


def reserve_and_hold(run: str, cap: float, est: float, gate: Any, done: Any, results: Any) -> None:
    """Wait at the gate, try one reservation, report, and hold it until `done`."""
    gate.wait(timeout=60)
    try:
        reservation = Guard(Path(run), cap, est, "w").reserve("x")
    except CapReached:
        results.put(False)
        done.wait(timeout=60)
        return
    results.put(True)
    done.wait(timeout=60)
    reservation.release()
