"""§12.2 item 1 (spec §10): all 42 decision scenarios through the service. Replay only, $0.

Each scenario gets a fresh org: its corpus (SLA: `base`), its clock (`decided_at` for S45; the
service's default, or for S40 and S44 2026-10-01, after every deadline on their tickets), and its
request row seeded through the overlay. Its requester (Marcus for
SLA) asks with the scenario's `submitted`. The kernel's record for version 1, as the service
stored it, must equal the harness's reference (`governed.decide` called directly on the gate's
inputs) on every key but `scenario`, and the committed record on the fields `check_equivalence`
compares: experiment 5 for credit, experiment 6 for SLA, experiment 4 v3's clean rows for
discount."""

from __future__ import annotations

from datetime import datetime, time
from pathlib import Path
from typing import Any

import pytest

from .. import harness


def due_after(reference: dict[str, Any], decided_at: str) -> list[str]:
    """The duties in the reference's obligations that don't fall due before `decided_at`. A date
    without a time falls due at the end of that day."""
    decided = datetime.fromisoformat(decided_at)
    late = []
    for o in reference["obligations"]:
        if o.get("due") is None:
            continue
        due = datetime.fromisoformat(o["due"])
        if due.tzinfo is None:
            due = datetime.combine(due.date(), time.max, decided.tzinfo)
        if not due < decided:
            late.append(str(o["duty"]))
    return late


@pytest.mark.parametrize("sid", harness.ALL)
def test_kernel_part_reproduces(sid: str, tmp_path: Path) -> None:
    org = harness.scenario_org(sid, tmp_path)
    v1 = harness.ask(org, sid)
    assert v1.version == 1
    kernel = harness.kernel_part(org, v1)
    reference = harness.plain(harness.reference(sid))
    assert harness.strip(kernel) == harness.strip(reference)
    mine, theirs = harness.committed_view(sid, kernel), harness.committed(sid)
    for k in harness.committed_fields(sid):
        assert mine[k] == theirs[k], k
    assert not org.engine.calls.exists()  # every Jev answer was a recorded one
    if sid in harness.SLA and harness.scenario(sid).decided_at is None:
        # Asked at a clock after every deadline on the ticket (`harness.clock_for`, ruling R41),
        # which decides as 'after all events' (`decided_at: None`) does: the SLA spec reads
        # `decided_at` only in deadline comparisons (`sla.yaml` lines 144 and 150)
        assert due_after(reference, v1.decided_at) == []
