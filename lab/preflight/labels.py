"""How both front ends name the checks and mark their status (the CLI and the app)."""

from __future__ import annotations

from preflight.config import CheckName

MARK = {"pass": "✔", "fail": "✖", "n/a": "·"}
LABEL: dict[CheckName, str] = {
    "inputs": "Inputs",
    "fingerprint": "Fingerprint",
    "settled": "Settled",
    "agent_context": "Agent context",
}
