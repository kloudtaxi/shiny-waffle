"""`python -m rounds`: the proof-rounds runner on 127.0.0.1 (spec §7).

Env: ROUNDS_PORT (8010), ROUNDS_STATE_DIR (.owm-rounds), ROUNDS_CAP_USD (30, finite and above 0),
ROUNDS_SERVICE_PORT (8001), ROUNDS_KB (the base id, required unless ROUNDS_SCRIPTED=1),
ROUNDS_CLAUDE_TOKEN_FILE (_owm-local/rounds-agent.token).
Scripted mode swaps the Claude agent for a deterministic one and mints nothing, for rehearsing
the page without spend. Live mode needs `claude` on the PATH and a private token file (the output
of `claude setup-token`, mode 600), and exits at once without either.
"""

from __future__ import annotations

import math
import os
import shutil
from collections.abc import Mapping
from functools import partial
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from rounds import foundation
from rounds.agent import claude_agent
from rounds.api import create_app
from rounds.runner import Runner, RunnerConfig
from rounds.scripted_agent import Step, scripted
from rounds.service_child import ServiceChild
from rounds.store import Store

REPO = Path(__file__).resolve().parents[2]
TOKEN_FILE = REPO / "_owm-local" / "rounds-agent.token"

GET: Step = ("get_request", {"request_id": "DR-9001"})
DECIDE: Step = ("decide", {"request_id": "DR-9001"})
APPLY: Step = ("apply_discount", {"request_id": "DR-9001", "discount_pct": 8})

DEMO_STEPS: dict[str, list[Step]] = {
    "alone_realistic": [GET, APPLY],
    "alone_neutral": [GET],
    "with_blueleaf": [DECIDE, APPLY],
}


def _cap(raw: str) -> float:
    """The spend cap: a NaN or infinite cap would never stop a round, and 0 or less stops all."""
    try:
        cap = float(raw)
    except ValueError:
        cap = math.nan
    if not (math.isfinite(cap) and cap > 0):
        raise SystemExit("ROUNDS_CAP_USD must be a finite number of dollars above 0")
    return cap


def _claude_token(env: Mapping[str, str]) -> str:
    """The long-lived token the agent signs in with, so it never sees the operator's account."""
    path = Path(env.get("ROUNDS_CLAUDE_TOKEN_FILE", str(TOKEN_FILE)))
    if not path.is_file():
        raise SystemExit(f"no Claude token at {path}: save `claude setup-token`'s output there")
    if path.stat().st_mode & 0o077:
        raise SystemExit(f"the Claude token at {path} is readable by others: chmod 600 it")
    token = path.read_text().strip()
    if not token:
        raise SystemExit(f"the Claude token at {path} is empty")
    return token


def build_app_from_env(env: Mapping[str, str]) -> FastAPI:
    state_dir = Path(env.get("ROUNDS_STATE_DIR", ".owm-rounds"))
    service_port = int(env.get("ROUNDS_SERVICE_PORT", "8001"))
    is_scripted = env.get("ROUNDS_SCRIPTED") == "1"
    kb = env.get("ROUNDS_KB")
    if not kb and not is_scripted:
        raise SystemExit("ROUNDS_KB is required (the knowledge base id) unless ROUNDS_SCRIPTED=1")
    if not is_scripted and shutil.which("claude") is None:
        raise SystemExit("claude is not on the PATH: live rounds need Claude Code installed")
    config = RunnerConfig(
        state_dir=state_dir,
        service_port=service_port,
        cap_usd=_cap(env.get("ROUNDS_CAP_USD", "30")),
        kb=kb,
        model="scripted" if is_scripted else RunnerConfig.model,
        scripted=is_scripted,
    )
    store = Store(state_dir, REPO / "runs")
    service = ServiceChild(service_port, state_dir / "service")
    if is_scripted:
        agent = scripted(DEMO_STEPS, f"http://127.0.0.1:{service_port}")
        runner = Runner(config, agent=agent, store=store, service=service, foundation=None)
    else:
        agent_fn = partial(claude_agent, token=_claude_token(env))
        runner = Runner(config, agent=agent_fn, store=store, service=service, foundation=foundation)
    return create_app(runner, store)


def main() -> None:
    app = build_app_from_env(os.environ)
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("ROUNDS_PORT", "8010")))


if __name__ == "__main__":
    main()
