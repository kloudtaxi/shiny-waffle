"""Shared test helpers for the pre-flight tests."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from preflight.config import AgentContextConfig
from preflight.engine import Deps
from preflight.markers import Markers, collect_markers
from preflight.observe.lab import LabObservation
from preflight.observe.probe import ProbeObservation


def write_config(run: Path, text: str) -> None:
    """Write a run's preflight.yaml."""
    (run / "preflight.yaml").write_text(text)


def fake_git(args: list[str]) -> str:
    """Stand in for `git config --get <key>`."""
    return {"user.name": "ada-ops", "user.email": "ada.ops@example.test"}[args[-1]]


MARKERS = collect_markers(Path("/w/shiny-waffle"), date(2026, 10, 20), "/Users/ada", fake_git)


def stream(
    *,
    init: dict[str, Any] | None = None,
    answer: str = "",
    cost: float | None = 0.0,
    extra: list[dict[str, Any]] | None = None,
) -> str:
    """A stream-json transcript: an optional init event, extra events, then the result."""
    events: list[dict[str, Any]] = []
    if init is not None:
        events.append({"type": "system", "subtype": "init", **init})
    events.extend(extra or [])
    result: dict[str, Any] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": answer,
    }
    if cost is not None:
        result["total_cost_usd"] = cost
    events.append(result)
    return "".join(json.dumps(e) + "\n" for e in events)


AT = datetime(2026, 10, 21, 9, 14, 0, tzinfo=UTC)

# The evidence lives in the repo (load_config refuses paths outside it); the questions in the run.
LOCAL_CFG = r"""checks: [inputs, fingerprint, settled, agent_context]
inputs:
  id_patterns: ['\bCRM-\d{4}\b']
  evidence: {base: [tests/preflight/fixtures/evidence]}
foundation: {kind: local}
agent_context:
  probe: [runner, probe]
  est_usd: 0.25
  cap_usd: 5
"""
QUESTIONS = "id\tcorpus\tprocess\tquestion\nS01\tbase\tdiscount\tWhat did CRM-0001 ask for?\n"

INIT: dict[str, Any] = {
    "cwd": "/tmp/northstar-exam-blind-x",
    "tools": ["mcp__foundation__find_entities"],
    "mcp_servers": [{"name": "foundation", "status": "connected"}],
    "model": "claude-opus-5-5",
    "claude_code_version": "2.1.299",
    "apiKeySource": "none",
    "skills": [],
    "plugins": [],
    "agents": [],
    "slash_commands": [],
}
META: dict[str, Any] = {
    "runner": "exam-reader",
    "model": "claude-opus-5-5",
    "flags": "f",
    "expected_tools": ["mcp__foundation__find_entities"],
    "expected_servers": ["foundation"],
    "system_prompt_sha256": "s",
    "problems": [],
}

ProbeFn = Callable[[AgentContextConfig, Path, Path, Markers, datetime], ProbeObservation]


class Clock:
    """A fake clock: each read advances `tick` seconds; `sleep` advances the time slept."""

    def __init__(self, t0: datetime, tick: float = 1.0) -> None:
        self.t = t0
        self.tick = timedelta(seconds=tick)
        self.lock = threading.Lock()

    def now(self) -> datetime:
        with self.lock:
            t = self.t
            self.t += self.tick
            return t

    def sleep(self, seconds: float) -> None:
        with self.lock:
            self.t += timedelta(seconds=seconds)


def probe_with(meta: dict[str, Any] = META, saved: Path | None = None) -> ProbeFn:
    def run_probe(
        cfg: AgentContextConfig, run: Path, repo: Path, markers: Markers, started: datetime
    ) -> ProbeObservation:
        return ProbeObservation(
            raw_stream=stream(init=INIT, answer="I don't know.", cost=0.05),
            meta=meta,
            cost_usd=0.05,
            saved=saved,
            error=None,
        )

    return run_probe


def fake_deps(
    version: str | None = "2.1.299", t0: datetime = AT, probe: ProbeFn | None = None
) -> Deps:
    """Deps for a local run: a clean lab at 81f24e8, the given `claude --version`, a fake clock."""
    return Deps(
        observe_lab=lambda repo: LabObservation(commit="81f24e8", dirty_paths=[]),
        run_probe=probe or probe_with(),
        claude_version=lambda: version,
        markers=lambda repo, today: MARKERS,
        now=Clock(t0).now,
        sleep=lambda seconds: None,
    )
