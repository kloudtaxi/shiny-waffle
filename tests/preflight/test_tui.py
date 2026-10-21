"""The Textual operator app (G-50 spike): headless Pilot tests, driven by `asyncio.run`.

No async pytest plugin: each test is a sync function that runs one coroutine (spike question 1).
"""

from __future__ import annotations

import asyncio
import os
import shlex
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from textual.pilot import Pilot
from textual.widgets import Button, DataTable, Input, Static

from preflight import cli
from preflight.config import AgentContextConfig, load_config
from preflight.engine import run_preflight
from preflight.markers import Markers
from preflight.observe.probe import ProbeObservation
from preflight.tui.app import PreflightApp
from preflight.tui.screens import AcceptDriftScreen, DetailScreen, MainScreen, SpendScreen
from tests.preflight.fakes import (
    AT,
    LOCAL_CFG,
    META,
    QUESTIONS,
    fake_deps,
    probe_with,
    write_config,
)

LATER = AT + timedelta(minutes=5)
REASON = "CLI auto-updated overnight"


def setup_run(run: Path) -> None:
    write_config(run, LOCAL_CFG)
    (run / "questions.tsv").write_text(QUESTIONS)


def app_with_drift(run: Path, repo: Path, meta: dict[str, Any] = META) -> PreflightApp:
    """A baseline record at claude 2.1.299, then the app with deps at 2.1.304."""
    setup_run(run)
    cfg = load_config(run, repo)
    run_preflight(run, repo, cfg, deps=fake_deps())
    return PreflightApp(run, repo, cfg, fake_deps("2.1.304", t0=LATER, probe=probe_with(meta)))


def app_with_slow_probe(run: Path, repo: Path, gate: threading.Event) -> PreflightApp:
    """An app whose probe blocks until `gate` is set (at most 30 s)."""
    setup_run(run)

    def slow(
        cfg: AgentContextConfig, run: Path, repo: Path, markers: Markers, started: datetime
    ) -> ProbeObservation:
        gate.wait(30)
        return probe_with()(cfg, run, repo, markers, started)

    return PreflightApp(run, repo, load_config(run, repo), fake_deps(probe=slow))


class Said:
    """Stands in for `App.notify`, keeping each message."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def __call__(self, message: str, **kwargs: Any) -> None:
        self.messages.append(message)


def records(run: Path) -> list[Path]:
    return sorted((run / "preflight").glob("*Z.json"))


def text_of(widget: Static) -> str:
    return str(widget.content)


# --- the brief's tests -------------------------------------------------------------------------


def test_drift_shows_the_fail_banner(run_dir: Path, repo: Path) -> None:
    async def go() -> None:
        app = app_with_drift(run_dir, repo)  # a baseline record at 2.1.299, then deps at 2.1.304
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.banner_text == "✖ FAIL (1 drift)"
            assert app.outcome is not None and app.outcome.record.status == "fail"

    asyncio.run(go())


def test_accepting_drift_needs_a_reason_then_writes_once(run_dir: Path, repo: Path) -> None:
    async def go() -> None:
        app = app_with_drift(run_dir, repo)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("a")
            assert isinstance(app.screen, AcceptDriftScreen)
            assert app.screen.query_one("#confirm", Button).disabled
            app.screen.query_one(Input).value = "CLI auto-updated overnight"
            await pilot.pause()
            assert not app.screen.query_one("#confirm", Button).disabled
            await pilot.click("#confirm")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.banner_text == "✔ ACCEPTED"
        notes = (run_dir / "notes.md").read_text().splitlines()
        assert sum(line.startswith("- **Amendment (pre-flight drift,") for line in notes) == 1

    asyncio.run(go())


def test_keys_respond_while_the_probe_runs(run_dir: Path, repo: Path) -> None:
    async def go() -> None:
        gate = threading.Event()
        app = app_with_slow_probe(run_dir, repo, gate)  # run_probe blocks on gate.wait(30)
        async with app.run_test() as pilot:
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(app.screen, SpendScreen)
            gate.set()
            await app.workers.wait_for_complete()

    asyncio.run(go())


def test_nothing_outside_tui_imports_textual(repo: Path) -> None:
    for p in (repo / "lab/preflight").rglob("*.py"):
        if "tui" in p.parts:
            continue
        text = p.read_text()
        top = [ln for ln in text.splitlines() if ln.startswith(("import ", "from "))]
        assert not any("textual" in ln for ln in top), p


# --- the app's contract ------------------------------------------------------------------------


def test_the_dialog_previews_the_amendment_and_escape_writes_nothing(
    run_dir: Path, repo: Path
) -> None:
    async def go() -> None:
        app = app_with_drift(run_dir, repo)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            written = records(run_dir)
            await pilot.press("a")
            assert isinstance(app.screen, AcceptDriftScreen)
            preview = app.screen.query_one("#preview", Static)
            assert "claude --version 2.1.299 → 2.1.304. Reason: <reason>." in text_of(preview)
            assert text_of(preview).startswith("- **Amendment (pre-flight drift, 2026-10-21 ")
            app.screen.query_one(Input).value = REASON
            await pilot.pause()
            assert f"Reason: {REASON}. Record: preflight/2026-10-21T" in text_of(preview)
            await pilot.press("escape")
            assert isinstance(app.screen, MainScreen)
            assert app.banner_text == "✖ FAIL (1 drift)"
        assert records(run_dir) == written  # the baseline and the fail record, nothing more
        assert (run_dir / "notes.md").read_text() == "# Notes\n"

    asyncio.run(go())


def test_enter_shows_every_value_of_the_selected_check(run_dir: Path, repo: Path) -> None:
    async def go() -> None:
        app = app_with_drift(run_dir, repo)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.press("down")  # inputs, then fingerprint
            await pilot.press("enter")
            assert isinstance(app.screen, DetailScreen)
            assert app.screen.check.name == "fingerprint"
            table = app.screen.query_one(DataTable)
            assert table.row_count == len(app.screen.check.values) > 0
            await pilot.press("escape")
            assert isinstance(app.screen, MainScreen)

    asyncio.run(go())


def test_the_fingerprint_table_marks_the_drifted_row(run_dir: Path, repo: Path) -> None:
    async def go() -> None:
        app = app_with_drift(run_dir, repo)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            table = app.screen.query_one("#fingerprint", DataTable)
            rows = {
                str(table.get_row_at(i)[1]): table.get_row_at(i) for i in range(table.row_count)
            }
            mark, _, then, now, source = (str(c) for c in rows["claude --version"])
            assert (mark, then, now, source) == ("✖", "2.1.299", "2.1.304", "the probe")
            assert str(rows["Lab commit"][0]) == "·"  # recorded, not compared

    asyncio.run(go())


def test_with_nothing_drifted_a_says_so_s_toggles_and_r_reruns(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def go() -> None:
        setup_run(run_dir)
        app = PreflightApp(run_dir, repo, load_config(run_dir, repo), fake_deps())
        said = Said()
        monkeypatch.setattr(app, "notify", said)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.banner_text == "✔ PASS" and app.exit_code == 0
            await pilot.press("a")
            assert isinstance(app.screen, MainScreen) and said.messages == ["nothing to accept"]
            await pilot.press("s")
            assert isinstance(app.screen, SpendScreen)
            await app.workers.wait_for_complete()  # the spend view is read in a worker (F-11)
            await pilot.pause()
            assert text_of(app.screen.query_one("#spend", Static)).startswith("recorded: $")
            await pilot.press("s")
            assert isinstance(app.screen, MainScreen)
            await pilot.press("r")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.banner_text == "✔ PASS"
        assert len(records(run_dir)) == 2  # one record per evaluation

    asyncio.run(go())


def test_r_while_the_probe_runs_starts_no_second_probe(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def go() -> None:
        gate = threading.Event()
        app = app_with_slow_probe(run_dir, repo, gate)
        said = Said()
        monkeypatch.setattr(app, "notify", said)
        async with app.run_test() as pilot:
            assert app.running and app.banner_text == "◌ RUNNING"  # started before the pilot
            await pilot.press("r")
            await pilot.press("a")
            assert said.messages == ["an evaluation is already running", "still running"]
            gate.set()
            await app.workers.wait_for_complete()
            await pilot.pause()
        assert len(records(run_dir)) == 1

    asyncio.run(go())


def test_a_refused_acceptance_shows_the_engine_s_note(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # P5
    async def go() -> None:
        app = app_with_drift(run_dir, repo, {**META, "problems": ["the tool list is stale"]})
        said = Said()
        monkeypatch.setattr(app, "notify", said)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("a")
            app.screen.query_one(Input).value = REASON
            await pilot.pause()
            await pilot.click("#confirm")
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.banner_text == "✖ FAIL (1 drift)" and app.exit_code == 1
            assert said.messages[-1].startswith(
                "drift can be accepted only when the other checks pass"
            )
        assert (run_dir / "notes.md").read_text() == "# Notes\n"

    asyncio.run(go())


def test_an_engine_error_is_one_line_not_a_traceback(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def go() -> None:
        setup_run(run_dir)
        (run_dir / "preflight").mkdir()
        (run_dir / "preflight" / "2026-10-20T00-00-00Z.json").write_text("{not json")
        app = PreflightApp(run_dir, repo, load_config(run_dir, repo), fake_deps())
        said = Said()
        monkeypatch.setattr(app, "notify", said)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.banner_text == "✖ ERROR" and app.exit_code == 2
            assert len(said.messages) == 1 and said.messages[0].startswith(
                "RecordError: unreadable pre-flight record 2026-10-20T00-00-00Z.json: "
            )

    asyncio.run(go())


# --- fix round 1 (T12-a, T12-b, T12-d) ---------------------------------------------------------

QUITTING = "quitting once the probe finishes…"


def status_of(app: PreflightApp) -> str:
    return text_of(app.main_screen.query_one("#status", Static))


async def accept(app: PreflightApp, pilot: Pilot[None], reason: str) -> str:
    """Open the dialog, type `reason` and confirm; return the line the dialog previewed."""
    await pilot.press("a")
    assert isinstance(app.screen, AcceptDriftScreen)
    app.screen.query_one(Input).value = reason
    await pilot.pause()
    previewed = text_of(app.screen.query_one("#preview", Static))
    await pilot.click("#confirm")
    await app.workers.wait_for_complete()
    await pilot.pause()
    return previewed


def test_the_previewed_line_is_the_line_written(run_dir: Path, repo: Path) -> None:  # T12-a
    async def go() -> None:
        app = app_with_drift(run_dir, repo)  # its clock moves a second on every read
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            previewed = await accept(app, pilot, REASON)
            assert app.outcome is not None and app.outcome.record.accepted is not None
            assert previewed == app.outcome.record.accepted.amendment
        assert (run_dir / "notes.md").read_text().splitlines()[-1] == previewed

    asyncio.run(go())


def test_the_preview_skips_a_record_name_already_taken(run_dir: Path, repo: Path) -> None:
    async def go() -> None:  # T12-a: the fail record and the dialog fall in the same second
        app = app_with_drift(run_dir, repo)
        app.deps.now = lambda: LATER
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app.outcome is not None
            assert app.outcome.path.name == "2026-10-21T09-19-00Z.json"
            previewed = await accept(app, pilot, REASON)
            assert previewed.endswith("Record: preflight/2026-10-21T09-19-01Z.json.")
            assert app.outcome.record.accepted is not None
            assert previewed == app.outcome.record.accepted.amendment

    asyncio.run(go())


def test_q_while_the_probe_runs_quits_once_it_finishes(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # T12-b
    async def go() -> None:
        gate = threading.Event()
        app = app_with_slow_probe(run_dir, repo, gate)
        said = Said()
        monkeypatch.setattr(app, "notify", said)
        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.press("q")  # repeats the notice
            assert app.is_running and app.return_code is None
            assert status_of(app) == QUITTING and said.messages == [QUITTING, QUITTING]
            gate.set()
            await app.workers.wait_for_complete()
            for _ in range(300):
                if not app.is_running:
                    break
                await asyncio.sleep(0.01)
            assert not app.is_running and app.return_code == 0  # it left on its own
        assert len(records(run_dir)) == 1  # and the evaluation's record was still written

    asyncio.run(go())


def test_ctrl_q_while_the_probe_runs_leaves_now_and_says_why_it_waits(
    run_dir: Path, repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    async def go() -> None:
        gate = threading.Event()
        app = app_with_slow_probe(run_dir, repo, gate)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+q")
            assert app.return_code is not None
        gate.set()  # after the app has closed and cancelled its worker

    asyncio.run(go())
    assert "the probe is still running" in capsys.readouterr().err
    assert records(run_dir) == []  # a cancelled evaluation writes nothing


def test_an_acceptance_marks_the_accepted_rows(run_dir: Path, repo: Path) -> None:  # T12-d
    async def go() -> None:
        app = app_with_drift(run_dir, repo)
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            await accept(app, pilot, REASON)
            table = app.screen.query_one("#fingerprint", DataTable)
            rows = [table.get_row_at(i) for i in range(table.row_count)]
            marks = {str(r[1]): str(r[0]) for r in rows}
            assert marks["claude --version"] == "✔" and "✖" not in marks.values()
            checks = app.screen.query_one("#checks", DataTable)
            assert str(checks.get_cell("fingerprint", "mark")) == "✔"
            assert str(checks.get_cell("fingerprint", "summary")).endswith(f"accepted: {REASON}")

    asyncio.run(go())


def test_the_app_does_not_import_the_cli(repo: Path) -> None:  # T12-d
    for p in (repo / "lab/preflight/tui").glob("*.py"):
        assert "preflight.cli" not in p.read_text(), p


# --- the CLI's app paths -----------------------------------------------------------------------


def test_tui_loads_the_config_and_runs_the_app(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_run(run_dir)
    seen: list[tuple[Path, list[str]]] = []

    def fake_run_app(run: Path, repo: Path, cfg: Any, deps: Any = None) -> int:
        seen.append((run, list(cfg.checks)))
        return 1

    monkeypatch.setattr("preflight.tui.app.run_app", fake_run_app)
    assert cli.main(["tui", "--run", str(run_dir)]) == 1
    assert seen == [(run_dir, ["inputs", "fingerprint", "settled", "agent_context"])]


def test_no_subcommand_on_a_terminal_opens_the_app(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_run(run_dir)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr("preflight.tui.app.run_app", lambda run, repo, cfg, deps=None: 0)
    assert cli.main(["--run", str(run_dir)]) == 0
    assert not (run_dir / "preflight").exists()  # the (fake) app ran, not `check`


def without(monkeypatch: pytest.MonkeyPatch, module: str) -> None:
    """Make `module` unimportable, and the app import afresh so it meets that."""
    monkeypatch.delitem(sys.modules, "preflight.tui.app", raising=False)
    monkeypatch.setitem(sys.modules, module, None)  # importing it raises


def test_tui_without_textual_says_which_group_to_install(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    setup_run(run_dir)
    without(monkeypatch, "textual")
    assert cli.main(["tui", "--run", str(run_dir)]) == 2
    assert "uv sync --group tui" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["tui"], []], ids=["tui", "no subcommand"])
def test_a_broken_app_is_not_mistaken_for_a_missing_textual(
    run_dir: Path, monkeypatch: pytest.MonkeyPatch, argv: list[str]
) -> None:  # F-13
    setup_run(run_dir)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    without(monkeypatch, "preflight.tui.screens")  # textual is there; the app's own import fails
    with pytest.raises(ImportError) as e:
        cli.main([*argv, "--run", str(run_dir)])
    assert e.value.name == "preflight.tui.screens"
    assert not (run_dir / "preflight").exists()  # it didn't fall back to `check`


@pytest.mark.parametrize("cmd", [["tui"], ["serve"]])
def test_the_app_commands_refuse_a_bad_config(
    run_dir: Path, capsys: pytest.CaptureFixture[str], cmd: list[str]
) -> None:
    write_config(run_dir, "checks: [nope]\n")
    assert cli.main([*cmd, "--run", str(run_dir)]) == 2
    assert "preflight.yaml" in capsys.readouterr().err


def test_serve_runs_the_tui_command_on_localhost(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    setup_run(run_dir)
    made: list[tuple[str, str, int]] = []

    class FakeServer:
        def __init__(self, command: str, host: str = "", port: int = 0) -> None:
            made.append((command, host, port))

        def serve(self) -> None:
            made.append(("served", os.environ["PYTHONPATH"], 0))

    monkeypatch.setattr("textual_serve.server.Server", FakeServer)
    monkeypatch.setenv("PYTHONPATH", "/elsewhere")
    assert cli.main(["serve", "--run", str(run_dir), "--port", "9000"]) == 0
    command = f"{shlex.quote(sys.executable)} -m preflight tui --run {shlex.quote(str(run_dir))}"
    assert made == [
        (command, "localhost", 9000),
        ("served", f"{repo / 'lab'}{os.pathsep}/elsewhere", 0),
    ]


# --- final review (F-11, F-14) -----------------------------------------------------------------


def test_the_spend_screen_reads_the_folder_off_the_ui_thread(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def go() -> None:
        setup_run(run_dir)
        on_ui: list[bool] = []

        def view(run: Path) -> str:
            on_ui.append(threading.current_thread() is threading.main_thread())
            return "recorded: $1.23"

        monkeypatch.setattr("preflight.tui.screens.spend_view", view)
        monkeypatch.setattr("preflight.tui.screens.SPEND_SECONDS", 0.05)
        app = PreflightApp(run_dir, repo, load_config(run_dir, repo), fake_deps())
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("s")
            assert isinstance(app.screen, SpendScreen)
            for _ in range(200):  # the first read, then at least one refresh
                await pilot.pause(0.01)
                if len(on_ui) >= 2:
                    break
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert text_of(app.screen.query_one("#spend", Static)) == "recorded: $1.23"
            await pilot.press("escape")
            assert isinstance(app.screen, MainScreen)
        assert len(on_ui) >= 2 and not any(on_ui)

    asyncio.run(go())


def test_a_spend_view_that_raises_is_shown_not_fatal(
    run_dir: Path, repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def go() -> None:
        setup_run(run_dir)

        def broken(run: Path) -> str:
            raise OSError("folder went away")

        monkeypatch.setattr("preflight.tui.screens.spend_view", broken)
        app = PreflightApp(run_dir, repo, load_config(run_dir, repo), fake_deps())
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.press("s")
            await app.workers.wait_for_complete()
            await pilot.pause()
            spend = text_of(app.screen.query_one("#spend", Static))
            assert spend == "spend unreadable: OSError: folder went away" and app.is_running

    asyncio.run(go())


def test_agent_context_details_show_the_reader_values(run_dir: Path, repo: Path) -> None:  # F-14
    async def go() -> None:
        setup_run(run_dir)
        app = PreflightApp(run_dir, repo, load_config(run_dir, repo), fake_deps())
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            for _ in range(3):  # inputs, fingerprint, settled, then agent context
                await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, DetailScreen)
            assert app.screen.check.name == "agent_context" and app.screen.check.values == []
            fp = app.main_screen.results["fingerprint"]
            reader = [v for v in fp.values if v.group == "reader"]
            assert reader and app.screen.query_one(DataTable).row_count == len(reader)
            note = text_of(app.screen.query_one("#problems", Static))
            assert note == "no problems · the reader's values, as the fingerprint recorded them"

    asyncio.run(go())


def test_agent_context_details_without_a_fingerprint_list_what_was_checked(
    run_dir: Path, repo: Path
) -> None:  # F-14
    async def go() -> None:
        setup_run(run_dir)
        write_config(run_dir, LOCAL_CFG.replace("[inputs, fingerprint, settled, agent_context]",
                                                "[agent_context]"))  # fmt: skip
        app = PreflightApp(run_dir, repo, load_config(run_dir, repo), fake_deps())
        async with app.run_test() as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            await pilot.press("enter")
            assert isinstance(app.screen, DetailScreen)
            note = text_of(app.screen.query_one("#problems", Static))
            assert note.startswith("no problems · checked: cwd outside the repo")

    asyncio.run(go())
