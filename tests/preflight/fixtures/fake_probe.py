"""A stand-in for a runner's `probe` command: writes a stream and its metadata."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--say", default="I don't know.")
    ap.add_argument("--sleep", type=float, default=0.0)
    ap.add_argument("--cost", type=float, default=0.0)
    args = ap.parse_args()
    time.sleep(args.sleep)
    out = Path(os.environ["PREFLIGHT_PROBE_OUT"])
    init = {
        "type": "system",
        "subtype": "init",
        "cwd": tempfile.mkdtemp(prefix="northstar-exam-blind-"),
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
    result = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": args.say,
        "total_cost_usd": args.cost,
    }
    (out / "probe.jsonl").write_text(json.dumps(init) + "\n" + json.dumps(result) + "\n")
    meta = {
        "runner": "exam-reader",
        "model": "claude-opus-5-5",
        "flags": "f",
        "expected_tools": ["mcp__foundation__find_entities"],
        "expected_servers": ["foundation"],
        "system_prompt_sha256": "s",
        "problems": [],
    }
    (out / "probe.json").write_text(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
