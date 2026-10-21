"""The engine and the plain CLI: one evaluation, one record, the amendment and the exit code."""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from preflight import cli
from preflight.config import AgentContextConfig, FoundationConfig, load_config
from preflight.engine import Deps, Event, evaluate, finish, run_preflight
from preflight.foundations import Foundation, FoundationSnapshot
from preflight.markers import Markers
from preflight.observe.lab import LabObservation
from preflight.observe.probe import ProbeObservation
from preflight.record import CheckResult, latest_record
from preflight.spend import live_reservations
from tests.preflight.fakes import MARKERS as M
from tests.preflight.fakes import stream, write_config

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


@pytest.fixture(autouse=True)
def _questions(run_dir: Path) -> None:
    (run_dir / "questions.tsv").write_text(QUESTIONS)


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
    return Deps(
        observe_lab=lambda repo: LabObservation(commit="81f24e8", dirty_paths=[]),
        run_probe=probe or probe_with(),
        claude_version=lambda: version,
        markers=lambda repo, today: M,
        now=Clock(t0).now,
        sleep=lambda seconds: None,
    )


def check(checks: list[CheckResult], name: str) -> CheckResult:
    return next(c for c in checks if c.name == name)


# --- the brief's tests -------------------------------------------------------------------------


def test_first_run_passes_and_sets_the_baseline(run_dir: Path, repo: Path) -> None:
    write_config(run_dir, LOCAL_CFG)  # checks [inputs, fingerprint, settled, agent_context], local
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 0
    rec = latest_record(run_dir)[1]  # type: ignore[index]
    fp = next(c for c in rec.checks if c.name == "fingerprint")
    assert rec.status == "pass" and "baseline set by this record" in fp.summary
    assert next(c for c in rec.checks if c.name == "settled").status == "n/a"
    assert rec.probe is not None and rec.probe.cost_usd == 0.05


def test_drift_fails_then_a_reason_amends_once_and_moves_the_baseline(
    run_dir: Path, repo: Path
) -> None:
    write_config(run_dir, LOCAL_CFG)
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 0
    assert cli.main(["check", "--run", str(run_dir)], fake_deps("2.1.304")) == 1
    before = (run_dir / "notes.md").read_text()
    argv = ["check", "--run", str(run_dir), "--accept-drift", "CLI auto-updated overnight"]
    assert cli.main(argv, fake_deps("2.1.304")) == 0
    after = (run_dir / "notes.md").read_text()
    assert after.startswith(before)
    added = after[len(before) :].splitlines()
    assert len(added) == 1 and added[0].startswith("- **Amendment (pre-flight drift, ")
    assert "claude --version 2.1.299 → 2.1.304" in added[0]
    assert "Reason: CLI auto-updated overnight." in added[0]
    assert latest_record(run_dir)[1].status == "accepted"  # type: ignore[index]
    assert cli.main(["check", "--run", str(run_dir)], fake_deps("2.1.304")) == 0  # R1


def test_acceptance_is_refused_when_another_check_fails(
    run_dir: Path, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:  # P5
    write_config(run_dir, LOCAL_CFG)
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 0
    capsys.readouterr()
    broken = probe_with({**META, "problems": ["the tool list is stale"]})
    argv = ["check", "--run", str(run_dir), "--accept-drift", "CLI auto-updated overnight"]
    code = cli.main(argv, fake_deps("2.1.304", probe=broken))
    out = capsys.readouterr().out
    assert code == 1 and "drift can be accepted only when the other checks pass" in out
    assert "    - runner: the tool list is stale" in out
    assert (run_dir / "notes.md").read_text() == "# Notes\n"


def test_an_empty_reason_or_a_bad_config_exits_2(
    run_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(run_dir, LOCAL_CFG)
    assert cli.main(["check", "--run", str(run_dir), "--accept-drift", "  "], fake_deps()) == 2
    assert "a reason is required" in capsys.readouterr().err
    write_config(run_dir, "checks: [nope]\n")
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 2
    err = capsys.readouterr().err
    assert "preflight.yaml" in err and "preflight.yaml: preflight.yaml" not in err
    assert not (run_dir / "preflight").exists()


def test_two_evaluations_in_one_second_write_two_records(run_dir: Path, repo: Path) -> None:
    write_config(run_dir, LOCAL_CFG)
    frozen = fake_deps()
    frozen.now = lambda: AT
    run_preflight(run_dir, repo, load_config(run_dir, repo), deps=frozen)
    run_preflight(run_dir, repo, load_config(run_dir, repo), deps=frozen)
    assert len(list((run_dir / "preflight").glob("*Z.json"))) == 2


def test_the_probe_reserves_spend_and_a_cap_refusal_fails_agent_context(
    run_dir: Path, repo: Path
) -> None:
    write_config(run_dir, LOCAL_CFG.replace("cap_usd: 5", "cap_usd: 0.1"))  # est 0.25 > cap
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 1
    found = latest_record(run_dir, frozenset({"fail"}))
    assert found is not None
    ac = check(found[1].checks, "agent_context")
    assert any(p.startswith("spend guard:") for p in ac.problems)
    assert ac.problems[0].startswith("spend guard:") and found[1].probe is None


def test_spend_prints_the_folder_total(run_dir: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (run_dir / "S01.jsonl").write_text(stream(cost=1.5))
    assert cli.main(["spend", "--run", str(run_dir)]) == 0
    assert "recorded: $1.50" in capsys.readouterr().out


def test_no_subcommand_off_a_terminal_runs_check(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_config(run_dir, LOCAL_CFG)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: False)
    assert cli.main(["--run", str(run_dir)], fake_deps()) == 0


# --- the engine's contract ---------------------------------------------------------------------


def test_the_check_lines_and_record_path_print_in_order(
    run_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(run_dir, LOCAL_CFG)
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("✔ Inputs         1 questions · 1 ids")
    assert lines[1] == "✔ Fingerprint    baseline set by this record"
    assert lines[2] == "· Settled        not applicable (local foundation)"
    assert lines[3].startswith("✔ Agent context  cwd outside repo")
    found = latest_record(run_dir)
    assert found is not None
    assert lines[4] == f"record: {found[0]}" and lines[5] == "status: pass" and len(lines) == 6


def test_one_evaluation_can_fail_then_be_accepted(run_dir: Path, repo: Path) -> None:  # P7, T2-a
    write_config(run_dir, LOCAL_CFG)
    cfg = load_config(run_dir, repo)
    run_preflight(run_dir, repo, cfg, deps=fake_deps())
    deps = fake_deps("2.1.304", t0=AT + timedelta(minutes=5))
    events: list[Event] = []
    ev = evaluate(run_dir, repo, cfg, deps, events.append)
    assert [v.field for v in ev.drift] == ["reader.claude_cli_version"]
    assert [c.name for c in ev.checks] == ["inputs", "fingerprint", "settled", "agent_context"]
    names = ["inputs", "fingerprint", "settled", "agent_context"]
    assert sorted(e.check for e in events if e.kind == "started") == sorted(names)
    done = [e for e in events if e.kind == "done"]
    assert sorted(e.check for e in done) == sorted(names) and done[-1].check == "fingerprint"
    assert all(e.result is not None and e.result.name == e.check for e in done)

    failed = finish(run_dir, repo, ev, None, deps)
    accepted = finish(run_dir, repo, ev, "CLI\n auto-updated   overnight ", deps)
    assert failed.record.status == "fail" and failed.note is None
    assert accepted.record.status == "accepted" and accepted.path != failed.path
    acc = accepted.record.accepted
    assert acc is not None and acc.reason == "CLI auto-updated overnight"
    assert acc.fields == ["reader.claude_cli_version"]
    notes = (run_dir / "notes.md").read_text().splitlines()
    amendments = [n for n in notes if n.startswith("- **Amendment (pre-flight drift,")]
    assert amendments == [acc.amendment]
    assert acc.amendment.endswith(f"Record: preflight/{accepted.path.name}.")


def test_a_reason_with_nothing_drifted_writes_no_amendment(
    run_dir: Path, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(run_dir, LOCAL_CFG)
    assert cli.main(["check", "--run", str(run_dir)], fake_deps()) == 0
    argv = ["check", "--run", str(run_dir), "--accept-drift", "just in case"]
    assert cli.main(argv, fake_deps()) == 0
    assert "nothing drifted; no amendment written" in capsys.readouterr().out
    assert (run_dir / "notes.md").read_text() == "# Notes\n"


def test_a_collector_that_raises_fails_only_its_own_check(run_dir: Path, repo: Path) -> None:
    write_config(run_dir, LOCAL_CFG)
    deps = fake_deps()

    def no_inputs(cfg: Any, run: Path, repo: Path) -> Any:
        raise OSError("disk went away\nand more")

    deps.observe_inputs = no_inputs
    out = run_preflight(run_dir, repo, load_config(run_dir, repo), deps=deps)
    inputs = check(out.record.checks, "inputs")
    assert inputs.status == "fail" and inputs.problems == [
        "could not read: OSError: disk went away"
    ]
    assert check(out.record.checks, "fingerprint").status == "pass"  # it still ran
    assert check(out.record.checks, "agent_context").status == "pass"
    assert out.record.status == "fail"


def test_an_unreadable_lab_fails_the_fingerprint_and_refuses_acceptance(
    run_dir: Path, repo: Path
) -> None:
    write_config(run_dir, LOCAL_CFG)
    run_preflight(run_dir, repo, load_config(run_dir, repo), deps=fake_deps())
    deps = fake_deps("2.1.304")

    def no_git(repo: Path) -> LabObservation:
        raise RuntimeError("git is gone")

    deps.observe_lab = no_git
    out = run_preflight(run_dir, repo, load_config(run_dir, repo), accept_reason="r", deps=deps)
    fp = check(out.record.checks, "fingerprint")
    assert fp.status == "fail" and fp.problems[0] == "could not read: RuntimeError: git is gone"
    assert out.record.lab.commit == "unread" and out.record.status == "fail"
    assert out.note is not None and "no amendment written" in out.note
    assert (run_dir / "notes.md").read_text() == "# Notes\n"


def test_the_probe_runs_inside_a_reservation_and_its_stream_is_cited(
    run_dir: Path, repo: Path
) -> None:
    write_config(run_dir, LOCAL_CFG)
    saved = run_dir / "preflight" / "2026-10-21T09-14-00Z.probe.jsonl"
    seen: list[tuple[str, str, float]] = []
    starts: list[datetime] = []

    def probe(
        cfg: AgentContextConfig, run: Path, repo: Path, markers: Markers, started: datetime
    ) -> ProbeObservation:
        seen.extend((r.label, r.item, r.est_usd) for r in live_reservations(run))
        starts.append(started)
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_text(stream(cost=0.05))
        return probe_with(saved=saved)(cfg, run, repo, markers, started)

    out = run_preflight(run_dir, repo, load_config(run_dir, repo), deps=fake_deps(probe=probe))
    assert seen == [("preflight", "probe", 0.25)] and live_reservations(run_dir) == []
    assert starts == [AT]  # the stream is named by the evaluation's start (P7)
    assert out.record.probe is not None and out.record.probe.stream == str(saved)


def test_a_missing_baseline_record_exits_2_before_any_probe(
    run_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:  # T7
    write_config(run_dir, LOCAL_CFG + "baseline: runs/nowhere/preflight/x.json\n")
    calls: list[datetime] = []

    def probe(
        cfg: AgentContextConfig, run: Path, repo: Path, markers: Markers, started: datetime
    ) -> ProbeObservation:
        calls.append(started)
        return probe_with()(cfg, run, repo, markers, started)

    assert cli.main(["check", "--run", str(run_dir)], fake_deps(probe=probe)) == 2
    assert "preflight.yaml: baseline record not found" in capsys.readouterr().err
    assert calls == [] and not (run_dir / "preflight").exists()


UTOPIA_CFG = r"""checks: [fingerprint, settled]
foundation:
  kind: utopia
  kbs: {base: 00000000-0000-0000-0000-000000000001}
  db_container: db
  binary: bin/utopia
  log: {docker: utopia}
settled: {window_seconds: 12}
"""


class FakeFoundation:
    kind = "utopia"

    def __init__(self, clock: Clock, facts: list[int]) -> None:
        self.clock = clock
        self.facts = facts
        self.since: list[datetime] = []
        self.taken: list[FoundationSnapshot] = []

    def snapshot(self, since: datetime) -> FoundationSnapshot:
        self.since.append(since)
        snap = FoundationSnapshot(
            at=self.clock.now(),
            counts={"base.facts": self.facts.pop(0)},
            settings={},
            binary_sha256="abc",
            jobs_active=0,
            jobs_failed_since=0,
            documents_unfinished=0,
            log_errors=[],
        )
        self.taken.append(snap)
        return snap


def utopia_deps(clock: Clock, foundation: FakeFoundation) -> Deps:
    def make(cfg: FoundationConfig, run: Path, repo: Path) -> Foundation:
        return foundation

    return Deps(
        observe_lab=lambda repo: LabObservation(commit="81f24e8", dirty_paths=[]),
        make_foundation=make,
        now=clock.now,
        sleep=clock.sleep,
    )


def test_settled_waits_out_the_window_then_reads_again(run_dir: Path, repo: Path) -> None:
    write_config(run_dir, UTOPIA_CFG)
    clock = Clock(AT)
    foundation = FakeFoundation(clock, [10, 10])
    events: list[Event] = []
    ev = evaluate(run_dir, repo, load_config(run_dir, repo), utopia_deps(clock, foundation),
                  events.append)  # fmt: skip
    first, second = foundation.taken
    assert foundation.since == [ev.started, first.at]
    assert (second.at - first.at).total_seconds() >= 12
    progress = [e.text for e in events if e.kind == "progress"]
    assert progress and all(e.check == "settled" for e in events if e.kind == "progress")
    assert all(t.startswith("counts stable ") and t.endswith(" of 12 s") for t in progress)
    settled = check(ev.checks, "settled")
    assert settled.status == "pass" and "counts stable 12 s" in settled.summary
    counts = [v for v in check(ev.checks, "fingerprint").values if v.field.startswith("found")]
    assert {v.field: v.value for v in counts}["foundation.counts.base.facts"] == 10


def test_counts_that_move_in_the_window_fail_settled(run_dir: Path, repo: Path) -> None:
    write_config(run_dir, UTOPIA_CFG)
    clock = Clock(AT)
    deps = utopia_deps(clock, FakeFoundation(clock, [10, 11]))
    out = run_preflight(run_dir, repo, load_config(run_dir, repo), deps=deps)
    settled = check(out.record.checks, "settled")
    assert settled.status == "fail" and "counts moved during the window" in settled.problems[0]


def test_no_subcommand_on_a_terminal_without_the_app_runs_check(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_config(run_dir, LOCAL_CFG)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setitem(sys.modules, "preflight.tui.app", None)  # importing it raises
    assert cli.main(["--run", str(run_dir)], fake_deps()) == 0


@pytest.mark.parametrize("cmd", [["tui"], ["serve", "--port", "9000"]])
def test_the_app_commands_wait_for_the_app(
    run_dir: Path, capsys: pytest.CaptureFixture[str], cmd: list[str]
) -> None:
    assert cli.main([*cmd, "--run", str(run_dir)]) == 2
    assert "the app isn't built yet" in capsys.readouterr().err
