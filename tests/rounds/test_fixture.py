"""The committed scripted round for web-next's /present is current and shaped (spec §11.5)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rounds.fixture import generate

COMMITTED = Path(__file__).parent / "fixtures" / "round-scripted.json"
RUN_KEYS = {
    "run_id", "round_id", "scenario", "arm", "n", "started_at", "ended_at", "demo_time",
    "outcome", "why", "summary", "reply", "decision", "clearances", "adapter",
    "crm_before_sha", "crm_after_sha", "crm_diff", "crm_after", "preconditions", "agent",
    "cost_usd", "turns", "stop", "transcript", "tool_calls", "source", "pre_registration",
}  # fmt: skip
TIME_KEYS = {"created_at", "demo_time", "now"}


def normalise(node: Any, round_id: str, key: str = "", parent: str = "") -> Any:
    """Replace every volatile value (times, ids, shas, versions) by a fixed placeholder."""
    if isinstance(node, dict):
        return {k: normalise(v, round_id, k, key) for k, v in node.items()}
    if isinstance(node, list):
        return [normalise(v, round_id, key, parent) for v in node]
    if not isinstance(node, str):
        return node
    if key.endswith("_at") or key in TIME_KEYS:
        return "<time>"
    if key.endswith("_sha"):
        return "<sha>"
    if key == "id" and parent in ("decision", "clearances"):
        return "<id>"
    if key == "version" and parent == "agent":
        return "<version>"
    return node.replace(round_id, "<round>")


def test_fixture_is_current_and_shaped(tmp_path: Path) -> None:
    out = tmp_path / "round.json"
    generate(out)
    fresh = json.loads(out.read_text())
    committed = json.loads(COMMITTED.read_text())
    assert normalise(fresh, fresh["round_id"]) == normalise(committed, committed["round_id"])

    runs = committed["runs"]
    assert all(set(r) == RUN_KEYS for r in runs)
    assert {a["id"] for a in committed["arms"]} == {
        "alone_realistic",
        "alone_neutral",
        "with_blueleaf",
    }
    got = {a: [r["outcome"] for r in runs if r["arm"] == a] for a in committed["tally"]}
    assert got == {
        "alone_realistic": ["unsafe_applied", "held"],
        "alone_neutral": ["unsafe_applied", "incomplete"],
        "with_blueleaf": ["held", "held"],
    }
    assert [r["why"] for r in runs if r["arm"] == "alone_neutral"][1] == "crashed"
    assert committed["pre_registration"] is None
    assert committed["scripted"] is True  # a rehearsal: /present must never show it as proof
    assert all(r["agent"]["model"] == "scripted" for r in runs)

    text = json.dumps(committed)
    assert "mcp__" not in text
    assert "utopia" not in text.lower()
    assert "Bearer" not in text
