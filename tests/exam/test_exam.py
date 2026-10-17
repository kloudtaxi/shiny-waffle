"""The exam's harness: its questions, the reader's controls, and Part 2's scoring."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from contract_reader.tools import TEXT_TOOLS
from exam import questions as q
from exam import reader
from exam.score_part2 import Scorers, table

SYSTEM_PROMPT = vars(reader)["SYSTEM_PROMPT"]  # the blind reader's, imported by reader
RUN = Path(__file__).resolve().parents[2] / "runs" / "2026-10-17-b20-northstar-exam"


def test_the_committed_questions_are_what_the_builder_builds() -> None:
    rows = q.build()
    assert len(rows) == 47
    committed = (RUN / "questions.tsv").read_text()
    assert committed == "id\tcorpus\tprocess\tquestion\n" + "".join(
        "\t".join(r) + "\n" for r in rows
    )


def test_earlier_texts_are_kept_byte_for_byte_and_no_gold_evidence_rides_along() -> None:
    rows = {sid: (corpus, proc, text) for sid, corpus, proc, text in q.build()}
    assert rows["S01"][2] == q._texts(q.PROCEDURE)["S01"]
    assert rows["S06b"][2] == q._texts(q.BASELINE)["S06b"]
    assert rows["S23"][2] == q._texts(q.SUBMITTED)["S23"]
    assert (
        rows["S05"][0] == "missing-contract-evidence"
        and rows["S33"][0] == "missing-guarantee-evidence"
    )
    assert {p for _, p, _ in rows.values()} == {"discount", "credit", "sla"}
    for _, _, text in rows.values():
        assert "The organization's documents and records" not in text and "=== " not in text


def stream(tools: list[str], connected: bool = True, denied: bool = False) -> str:
    evs: list[dict[str, Any]] = [
        {
            "type": "system",
            "subtype": "init",
            "tools": tools,
            "mcp_servers": [
                {"name": "foundation", "status": "connected" if connected else "failed"}
            ],
        },
        {"type": "result", "result": "ok", "total_cost_usd": 0.01},
    ]
    if denied:
        evs.insert(1, {"type": "system", "subtype": "permission_denied"})
    return "\n".join(json.dumps(e) for e in evs)


def test_the_probe_checks() -> None:
    c1 = [f"mcp__foundation__{t}" for t in reader.ALL_TOOLS]
    c2 = [t for t in c1 if t.split("__")[-1] not in TEXT_TOOLS]
    assert reader.check_probe(stream(c1), "C1") == []
    assert reader.check_probe(stream(c2), "C2") == []
    assert reader.check_probe(stream(c1), "C2")  # a text tool visible in C2
    assert reader.check_probe(stream(c1, connected=False), "C1")
    assert reader.check_probe(stream(c1, denied=True), "C1")
    assert reader.check_probe(stream([*c1, "Bash"]), "C1")


def test_the_reader_runs_blind_with_the_fixed_prompt_and_hides_c2s_text_tools(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    seen: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        seen["cmd"], seen["cwd"] = cmd, kw["cwd"]
        return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    cfg = {"mode": "bearer", "url": "http://x", "token_file": "_owm-local/t.token", "kbs": {}}
    env = reader.server_env(cfg, "kb1", tmp_path / "log.jsonl")
    sysprompt, rec = reader.system_prompt("credit")
    assert sysprompt.startswith(SYSTEM_PROMPT + "\n\n") and rec["path"].endswith("credit-limit.md")
    reader.ask("question?", sysprompt, env, "C2", "claude-opus-5-5")
    cmd = seen["cmd"]
    assert not Path(seen["cwd"]).resolve().is_relative_to(reader.LAB)
    for flag in ("--strict-mcp-config", "--no-session-persistence"):
        assert flag in cmd
    assert (
        cmd[cmd.index("--tools") + 1] == "" and cmd[cmd.index("--setting-sources") + 1] == "project"
    )
    hidden = next(c for c in cmd if c.startswith("--disallowedTools="))
    assert all(f"mcp__foundation__{t}" in hidden for t in TEXT_TOOLS)
    allowed = cmd[cmd.index("--allowedTools") + 1]
    assert not any(f"mcp__foundation__{t}" in allowed for t in TEXT_TOOLS)
    config = json.loads(cmd[cmd.index("--mcp-config") + 1])["mcpServers"]["foundation"]
    assert config["type"] == "stdio" and config["env"]["CONTRACT_READER_KB"] == "kb1"
    assert config["env"]["CONTRACT_READER_TOKEN_FILE"].endswith("_owm-local/t.token")


def test_part2_grades_with_each_process_scorer() -> None:
    s = Scorers()
    e = s.expected["S01"]
    decision = {
        "outcome": e["outcome"],
        "commercial_eligibility": {"status": e["eligibility"]},
        "authority": {
            "requestor_authorized": e["authorized"],
            "approver": e["approver"],
            "required_role": e["required_role"],
        },
    }
    assert s.grade("S01", "```json\n" + json.dumps(decision) + "\n```")["grade"] == "pass"
    assert s.grade("S01", "no decision")["grade"] == "fail"
    approve_s05 = {"outcome": "APPROVE"}
    assert s.grade("S05", "```json\n" + json.dumps(approve_s05) + "\n```")["safety"] == "unsafe"
    assert s.grade("S07", "anything")["grade"] == "hand"
    assert s.grade("S36", "nothing")["grade"] == "fail"
    md = table(
        [
            {"arm": "a", "variant": "C1", "rep": "r1", "scenario": "S01", "grade": "pass",
             "safety": "held", "cost_usd": 0.5},
            {"arm": "a", "variant": "C1", "rep": "r1", "scenario": "S36", "grade": "core",
             "safety": "held", "cost_usd": 0.25},
        ]
    )  # fmt: skip
    assert "| a | C1 | r1 | 1 / 0 / 0 | 0 / 0 / 0 | 0 / 1 / 0 | 0 | 0 | 0.75 |" in md
