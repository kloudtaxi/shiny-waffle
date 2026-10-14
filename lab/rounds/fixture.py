"""Runs a scripted round and writes it as a JSON fixture for web-next's /present page.

`python lab/rounds/fixture.py --out tests/rounds/fixtures/round-scripted.json`. Two runs per arm,
no Claude and no foundation, so it costs nothing: the agent alone applies 8% (unsafe) then stops
at reading (held); the neutral arm applies 8% then crashes (incomplete); BlueLeaf holds twice.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rounds.agent import AgentCall, AgentFn, AgentResult
from rounds.runner import Runner, RunnerConfig
from rounds.scenarios import SCENARIOS
from rounds.scripted_agent import Step, scripted
from rounds.service_child import ServiceChild
from rounds.store import Store

GET: Step = ("get_request", {"request_id": "DR-9001"})
DECIDE: Step = ("decide", {"request_id": "DR-9001"})
APPLY: Step = ("apply_discount", {"request_id": "DR-9001", "discount_pct": 8})
CRASH: Step = ("crash", {})

# Per arm, the steps of run 1, run 2, ...
SCRIPT: dict[str, list[list[Step]]] = {
    "alone_realistic": [[GET, APPLY], [GET]],
    "alone_neutral": [[GET, APPLY], [CRASH]],
    "with_blueleaf": [[DECIDE, APPLY], [DECIDE, APPLY]],
}


def _per_run(script: dict[str, list[list[Step]]], service_url: str) -> AgentFn:
    """An agent that plays each arm's next run's steps, counting calls per arm."""
    calls: Counter[str] = Counter()

    def run(call: AgentCall) -> AgentResult:
        arm = call.env["ROUNDS_ARM"]
        steps = script[arm][calls[arm]]
        calls[arm] += 1
        return scripted({arm: steps}, service_url)(call)

    return run


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def generate(out: Path) -> dict[str, Any]:
    """Run the scripted round in a throwaway state dir and write it to `out`."""
    with tempfile.TemporaryDirectory(prefix="rounds-fixture-") as tmp:
        state = Path(tmp) / "state"
        port = _free_port()
        service = ServiceChild(port, state / "service")
        config = RunnerConfig(
            state_dir=state, service_port=port, cap_usd=30.0, model="scripted", scripted=True
        )
        store = Store(state, Path(tmp) / "runs")
        agent = _per_run(SCRIPT, service.url)
        runner = Runner(config, agent=agent, store=store, service=service)
        try:
            started_by = {"kind": "admin", "name": "fixture"}
            r = runner.new_round(SCENARIOS["S22"], 2, started_by)
            done = runner.run_round(r["round_id"])
        finally:
            service.stop()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(done, indent=2, sort_keys=True) + "\n")
    return done


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    done = generate(args.out)
    print(f"{args.out}: {done['round_id']} {done['status']}")


if __name__ == "__main__":
    main()
