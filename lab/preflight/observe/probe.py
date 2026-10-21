"""Run the runner's own probe and keep a redacted copy of its stream."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from preflight.config import AgentContextConfig
from preflight.markers import Markers, redact
from preflight.record import record_name

TIMEOUT_SECONDS = 900
RETRIES = 5


@dataclass(frozen=True)
class ProbeObservation:
    """What the probe produced. `raw_stream` is unredacted and lives in memory only."""

    raw_stream: str
    meta: dict[str, Any]
    cost_usd: float | None
    saved: Path | None
    error: str | None


def run_subprocess(cmd: list[str], env: dict[str, str], cwd: Path) -> int:
    """Run `cmd` and return its exit code; a timeout counts as exit 124."""
    try:
        return subprocess.run(
            cmd, env=env, cwd=cwd, capture_output=True, timeout=TIMEOUT_SECONDS, check=False
        ).returncode
    except subprocess.TimeoutExpired:
        return 124


def stream_events(raw: str) -> list[dict[str, Any]]:
    """The JSON objects in a stream-json transcript; unreadable lines are skipped."""
    out: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _cost(raw: str) -> float | None:
    for ev in reversed(stream_events(raw)):
        if ev.get("type") == "result":
            cost = ev.get("total_cost_usd")
            return float(cost) if isinstance(cost, int | float) else None
    return None


def _save(folder: Path, started: datetime, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for k in range(RETRIES + 1):
        name = record_name(started + timedelta(seconds=k)).removesuffix(".json") + ".probe.jsonl"
        path = folder / name
        try:
            with path.open("x", encoding="utf-8") as fh:
                fh.write(text)
        except FileExistsError:
            continue
        return path
    raise FileExistsError(f"no free probe stream name near {record_name(started)}")


def run_probe(
    cfg: AgentContextConfig,
    run: Path,
    repo: Path,
    markers: Markers,
    started: datetime,
    runner: Callable[[list[str], dict[str, str], Path], int] = run_subprocess,
) -> ProbeObservation:
    """Run the runner's probe from the repo and save its stream with markers redacted.

    The caller holds the spend reservation; this does not reserve.
    """
    out = Path(tempfile.mkdtemp(prefix="preflight-probe-"))
    try:
        env = {**os.environ, "PREFLIGHT_PROBE_OUT": str(out)}
        code = runner(cfg.probe, env, repo)
        stream_file = out / "probe.jsonl"
        if not stream_file.is_file():
            return ProbeObservation("", {}, None, None, f"the probe wrote no stream (exit {code})")
        raw = stream_file.read_text(encoding="utf-8")
        meta_file = out / "probe.json"
        meta: dict[str, Any] = json.loads(meta_file.read_text()) if meta_file.is_file() else {}
        saved = _save(run / "preflight", started, redact(raw, markers))
        return ProbeObservation(raw, meta, _cost(raw), saved, None)
    finally:
        shutil.rmtree(out, ignore_errors=True)


def _cli_version_output() -> str:
    done = subprocess.run(["claude", "--version"], capture_output=True, text=True, check=False)
    return done.stdout


def claude_cli_version(read: Callable[[], str] = _cli_version_output) -> str:
    """The first token of `claude --version`'s output."""
    words = read().split()
    return words[0] if words else ""
