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


def test_p2_and_p4_items_and_the_judges_reading() -> None:
    from exam.judge import majority, readings, render
    from exam.part1 import items

    its = items()
    assert [i["id"] for i in its["p2"]] == [f"F{n:02d}" for n in range(1, 27)]
    assert [i["id"] for i in its["p4"]] == ["P4a", "P4b", "P4c", "P4d"]
    for it in its["p2"] + its["p4"]:
        assert it["anchors"] and "CUST-" not in it["statement"] and "MSA-" not in it["statement"]
    snap = {
        "anchors": {"Acme Manufacturing": ["e1"]},
        "entities": {
            "e1": {
                "name": "Acme Manufacturing",
                "kind": {"key": "organization"},
                "names": [{"name": "Acme Mfg. Holdings"}],
                "identifiers": [{"system": "CRM", "id": "CRM-2048"}],
                "facts": [
                    {
                        "fact_id": "f1",
                        "subject": {"name": "Acme Manufacturing"},
                        "predicate": {"label": "credit limit"},
                        "object": {
                            "kind": "value",
                            "value": "250000",
                            "unit": "USD",
                            "datatype": "money_usd",
                        },
                        "valid": {"from": {"value": "2026-01-01"}, "to": {"value": None}},
                        "status": "current",
                    }
                ],
            }
        },
        "x_holds": {"e1": [{"fact_id": "f1", "from": "2026-02-01", "to": None}]},
    }
    item = {"anchors": ["Acme Manufacturing", "Nobody"]}
    stated = render(snap, item, holds=False)
    assert stated.splitlines() == [
        "1. E1 · Acme Manufacturing [organization] · also named: Acme Mfg. Holdings"
        " · identifiers: CRM: CRM-2048",
        "2. Acme Manufacturing — credit limit — 250000 USD (money_usd) · valid 2026-01-01 → …",
    ]
    assert render(snap, item, holds=True).endswith("· holds 2026-02-01 → …")
    assert render(snap, {"anchors": ["Nobody"]}, holds=False) == "(no facts found)"
    assert majority(["stated", "stated", "partly"]) == "stated"
    assert majority(["stated", "partly", "not_stated"]) == "partly"
    assert majority([None, None, None]) == "no answer"
    rs = readings(snap | {"anchors": {}})
    assert len(rs) == 26 + 4 + sum(1 for i in its["p2"] + its["p4"] if i.get("dated"))


def test_todays_loader_checks_every_corpus_against_the_hash_list() -> None:
    from exam import today

    counts = {c: len(today.corpus_files(c)) for c in today.NAMES}
    assert counts == {"base": 38, "missing-contract-evidence": 35, "missing-guarantee-evidence": 37}
    names = [rel for rel, _ in today.corpus_files("base")]
    assert not any("MANIFEST" in n for n in names)
    with pytest.raises(SystemExit):
        today.psql("SELECT 1", db="utopia")  # the live database is never touched


def test_parity_matches_hits_as_a_set_and_csv_rows_by_their_cells() -> None:
    from exam.parity import compare, queries

    today = [
        {"document_id": "d1", "text": "doc_id: X\ntitle:  Pricing"},
        {"document_id": "d2", "text": "| id | customer |\n| INV-1 | C-1044 |"},
        {"document_id": "d3", "text": "tie at the cut-off"},
        {"document_id": "d4", "text": "past the cut-off"},
    ]
    hits = [
        {"passage": {"doc_id": "d2", "text": "INV-1,C-1044"}},
        {"passage": {"doc_id": "d1", "text": "doc_id: X title: Pricing"}},
        {"passage": {"doc_id": "d4", "text": "past the cut-off"}},
    ]
    assert compare(today, hits, 3) == {
        "today": 3,
        "adapter": 3,
        "matched": 3,
        "same_rank": 0,
        "dropped": 1,
        "unmatched_adapter_hits": 0,
        "empty": 0,
    }
    wrong = [{"passage": {"doc_id": "d9", "text": "doc_id: X title: Pricing"}}]
    assert compare(today, wrong, 3)["unmatched_adapter_hits"] == 1
    # no hits where today answered isn't a pass, and no hits where today answered nothing is fine
    assert compare(today, [], 3)["empty"] == 1
    assert compare([], [], 3)["empty"] == 0
    assert queries(["acme_pricing_exception_2023.md", "erp_invoices.csv"]) == [
        "acme pricing exception 2023",
        "erp invoices",
    ]


def test_an_api_error_is_not_an_answer() -> None:
    # Claude Code's session-limit refusal, as the exam recorded it on 2026-10-17
    limit = {
        "type": "result",
        "subtype": "success",
        "is_error": True,
        "num_turns": 1,
        "total_cost_usd": 0,
        "result": "You've hit your session limit · resets 2:40am (America/New_York)",
    }
    out_of_turns = {"type": "result", "subtype": "error_max_turns", "is_error": True}
    answered = {"type": "result", "subtype": "success", "is_error": False, "result": "Approve."}
    assert reader.infra(limit) and reader.infra({})
    assert not reader.infra(out_of_turns) and not reader.infra(answered)
    # the account's limit never counts toward a question's two infra errors
    assert reader.account_limit(limit)
    assert not reader.account_limit({**limit, "result": "API Error: 529 overloaded"})
    assert not reader.account_limit(answered)

    from exam.judge import hollow, is_infra

    assert is_infra(limit) and is_infra({}) and not is_infra({**answered, "total_cost_usd": 0.01})
    assert hollow({"verdict": None, "cost_usd": 0}) and hollow({"infra": True})
    # a judge that answered badly is still a judge's answer
    assert not hollow({"verdict": None, "cost_usd": 0.004})


def test_the_scorer_skips_infra_attempts(tmp_path: Path) -> None:
    from exam.score_part2 import score

    folder = tmp_path / "part2" / "b20" / "C1" / "r1"
    folder.mkdir(parents=True)
    (folder / "S99.infra-error-1.jsonl").write_text('{"type":"result","is_error":true}\n')
    (folder / "S99.infra-error-1.calls.jsonl").write_text("")

    class Never:
        def grade(self, sid: str, text: str) -> dict[str, Any]:
            raise AssertionError(f"graded {sid}")

    assert score(tmp_path / "part2", Never()) == []  # type: ignore[arg-type]


def test_the_probe_writes_its_stream_and_metadata_for_preflight(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREFLIGHT_PROBE_OUT", str(tmp_path))
    reader.write_probe_out("{}\n", {"runner": "exam-reader"})
    assert (tmp_path / "probe.jsonl").read_text() == "{}\n"
    assert json.loads((tmp_path / "probe.json").read_text())["runner"] == "exam-reader"


def test_the_probe_writes_nothing_without_the_variable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("PREFLIGHT_PROBE_OUT", raising=False)
    monkeypatch.chdir(tmp_path)
    reader.write_probe_out("{}\n", {})
    assert list(tmp_path.iterdir()) == []


def test_the_probe_prompt_asks_who_and_when() -> None:
    assert "(3) say who you work for, and today's date, if you know them." in reader.PROBE_PROMPT


def test_a_refused_reservation_skips_the_question(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = tmp_path / "runs" / "r"
    folder.mkdir(parents=True)
    (folder / "questions.tsv").write_text(
        "id\tcorpus\tprocess\tquestion\nS01\tbase\tdiscount\tq1\nS02\tbase\tdiscount\tq2\n"
    )
    arm = {"mode": "bearer", "url": "http://x", "token_file": "nope.token", "kbs": {"base": "k"}}
    (folder / "arms.json").write_text(json.dumps({"arms": {"a": arm}}))
    (folder / "S00.jsonl").write_text(json.dumps({"type": "result", "total_cost_usd": 10.0}) + "\n")
    calls: list[str] = []

    def fail_ask(*args: Any, **kwargs: Any) -> str:
        calls.append("ask")
        raise AssertionError("ask was called")

    monkeypatch.setattr(reader, "ask", fail_ask)
    monkeypatch.setattr(
        "sys.argv",
        ["reader", "run", "--run", str(folder), "--arm", "a", "--variant", "C1", "--rep", "1",
         "--cap-usd", "5"],
    )  # fmt: skip
    reader.main()
    out = capsys.readouterr().out
    assert "skipped: spend guard: $10.00 recorded" in out and calls == []
    assert out.count("skipped: spend guard") == 2
    setup = json.loads((folder / "part2/a/C1/r1/setup.json").read_text())
    assert setup["preflight"]["status"] == "missing"
    assert setup["flags"] == reader.FLAGS
