"""`python -m rounds`: the proof-rounds runner on 127.0.0.1 (spec §7).

Env: ROUNDS_PORT (8010), ROUNDS_STATE_DIR (.owm-rounds), ROUNDS_CAP_USD (30),
ROUNDS_SERVICE_PORT (8001), ROUNDS_KB (the base id, required unless ROUNDS_SCRIPTED=1).
Scripted mode swaps the Claude agent for a deterministic one and mints nothing, for rehearsing
the page without spend.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
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

GET: Step = ("get_request", {"request_id": "DR-9001"})
DECIDE: Step = ("decide", {"request_id": "DR-9001"})
APPLY: Step = ("apply_discount", {"request_id": "DR-9001", "discount_pct": 8})

DEMO_STEPS: dict[str, list[Step]] = {
    "alone_realistic": [GET, APPLY],
    "alone_neutral": [GET],
    "with_blueleaf": [DECIDE, APPLY],
}


def build_app_from_env(env: Mapping[str, str]) -> FastAPI:
    state_dir = Path(env.get("ROUNDS_STATE_DIR", ".owm-rounds"))
    service_port = int(env.get("ROUNDS_SERVICE_PORT", "8001"))
    is_scripted = env.get("ROUNDS_SCRIPTED") == "1"
    kb = env.get("ROUNDS_KB")
    if not kb and not is_scripted:
        raise SystemExit("ROUNDS_KB is required (the knowledge base id) unless ROUNDS_SCRIPTED=1")
    config = RunnerConfig(
        state_dir=state_dir,
        service_port=service_port,
        cap_usd=float(env.get("ROUNDS_CAP_USD", "30")),
        kb=kb,
    )
    store = Store(state_dir, REPO / "runs")
    service = ServiceChild(service_port, state_dir / "service")
    if is_scripted:
        agent = scripted(DEMO_STEPS, f"http://127.0.0.1:{service_port}")
        runner = Runner(config, agent=agent, store=store, service=service, foundation=None)
    else:
        runner = Runner(
            config, agent=claude_agent, store=store, service=service, foundation=foundation
        )
    return create_app(runner, store)


def main() -> None:
    app = build_app_from_env(os.environ)
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("ROUNDS_PORT", "8010")))


if __name__ == "__main__":
    main()
