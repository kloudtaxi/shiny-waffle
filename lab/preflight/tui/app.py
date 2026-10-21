"""The pre-flight operator app: the engine's evaluation, live, with the accept-drift dialog.

The engine runs in a thread worker; its events reach the screen through `call_from_thread`, so
the settled window and the probe never freeze the keys. Records and amendments are written only
by `finish`, the same code the plain `check` uses.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App
from textual.binding import Binding, BindingType
from textual.reactive import reactive
from textual.worker import get_current_worker

from preflight.config import RunConfig
from preflight.engine import (
    ORDER,
    Deps,
    Evaluation,
    Event,
    Outcome,
    describe_exc,
    evaluate,
    finish,
    repo_relative,
)
from preflight.record import Value
from preflight.tui.screens import AcceptDriftScreen, MainScreen, SpendScreen

RUNNING = "◌ RUNNING"
BLOCKED_IN_DIALOG = frozenset({"rerun", "accept_drift", "spend"})


def banner(status: str, drift: list[Value]) -> str:
    """The status line's verdict for a written record."""
    if status == "pass":
        return "✔ PASS"
    if status == "accepted":
        return "✔ ACCEPTED"
    return f"✖ FAIL ({len(drift)} drift)" if drift else "✖ FAIL"


class PreflightApp(App[None]):
    """One run folder's pre-flight, evaluated on start and again on `r`."""

    CSS_PATH = "app.tcss"
    TITLE = "Pre-flight"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("r", "rerun", "re-run"),
        Binding("a", "accept_drift", "accept drift…"),
        Binding("s", "spend", "spend"),
        Binding("q", "quit", "quit"),
    ]

    banner_text: reactive[str] = reactive(RUNNING)

    def __init__(self, run: Path, repo: Path, cfg: RunConfig, deps: Deps) -> None:
        super().__init__()
        self.run_dir = run
        self.repo = repo
        self.cfg = cfg
        self.deps = deps
        self.evaluation: Evaluation | None = None
        self.outcome: Outcome | None = None
        self.error: str | None = None
        self.running = False
        self.main_screen = MainScreen(run, repo, [n for n in ORDER if n in cfg.checks])

    @property
    def exit_code(self) -> int:
        """As the plain `check`: 0 pass or accepted, 1 fail or no record, 2 an error."""
        if self.error is not None:
            return 2
        if self.outcome is None:
            return 1
        return 0 if self.outcome.record.status in ("pass", "accepted") else 1

    def get_default_screen(self) -> MainScreen:
        return self.main_screen

    def on_mount(self) -> None:
        # Queued behind the main screen's own mount, so its tables exist when events arrive.
        self.main_screen.call_later(self.action_rerun)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """The dialog has the keys while it is open."""
        return not (isinstance(self.screen, AcceptDriftScreen) and action in BLOCKED_IN_DIALOG)

    # --- evaluating ----------------------------------------------------------------------------

    def action_rerun(self) -> None:
        if self.running:
            self.notify("an evaluation is already running")
            return
        self.running = True
        self.evaluation = None
        self.outcome = None
        self.error = None
        self.banner_text = RUNNING
        self.main_screen.reset()
        self._evaluate()

    @work(thread=True, exclusive=True)
    def _evaluate(self) -> None:
        worker = get_current_worker()

        def on_event(e: Event) -> None:
            if not worker.is_cancelled:
                self.call_from_thread(self.main_screen.show_event, e)

        try:
            ev = evaluate(self.run_dir, self.repo, self.cfg, self.deps, on_event)
            if worker.is_cancelled:  # the app is closing: write nothing more
                return
            out = finish(self.run_dir, self.repo, ev, None, self.deps)
        except Exception as exc:
            if not worker.is_cancelled:
                self.call_from_thread(self._failed, describe_exc(exc))
            return
        if not worker.is_cancelled:
            self.call_from_thread(self._evaluated, ev, out)

    def _evaluated(self, ev: Evaluation, out: Outcome) -> None:
        self.running = False
        self.evaluation = ev
        self.outcome = out
        self.main_screen.show_evaluation(ev)
        self.main_screen.set_status(f"record: {repo_relative(out.path, self.repo)}")
        self.banner_text = banner(out.record.status, ev.drift)

    def _failed(self, message: str) -> None:
        self.running = False
        self.error = message
        self.main_screen.set_status(message)
        self.banner_text = "✖ ERROR"
        self.notify(message, severity="error")

    # --- accepting drift (P7: a second record from the same evaluation) ------------------------

    def action_accept_drift(self) -> None:
        if self.running:
            self.notify("still running")
            return
        ev = self.evaluation
        if ev is None or not ev.drift:
            self.notify("nothing to accept")
            return
        if self.outcome is not None and self.outcome.record.status == "accepted":
            self.notify("drift already accepted")
            return
        self.push_screen(AcceptDriftScreen(ev.drift, self.deps.now), self._accept)

    def _accept(self, reason: str | None) -> None:
        if reason is None or self.evaluation is None:
            return
        self.running = True
        self.main_screen.set_status("writing the accepted record…")
        self._finish_accepted(self.evaluation, reason)

    @work(thread=True, exclusive=True)
    def _finish_accepted(self, ev: Evaluation, reason: str) -> None:
        worker = get_current_worker()
        try:
            out = finish(self.run_dir, self.repo, ev, reason, self.deps)
        except Exception as exc:
            if not worker.is_cancelled:
                self.call_from_thread(self._failed, describe_exc(exc))
            return
        if not worker.is_cancelled:
            self.call_from_thread(self._accepted, ev, out)

    def _accepted(self, ev: Evaluation, out: Outcome) -> None:
        self.running = False
        self.outcome = out
        status = f"record: {repo_relative(out.path, self.repo)}"
        if out.record.status == "accepted":
            status += " · amendment appended to notes.md"
        elif out.note:
            status = out.note
            self.notify(out.note, severity="warning")
        self.main_screen.set_status(status)
        self.banner_text = banner(out.record.status, ev.drift)

    # --- spend ---------------------------------------------------------------------------------

    def action_spend(self) -> None:
        if isinstance(self.screen, SpendScreen):
            self.pop_screen()
        else:
            self.push_screen(SpendScreen(self.run_dir))


def run_app(run: Path, repo: Path, cfg: RunConfig, deps: Deps | None = None) -> int:
    """Run the app on this terminal; the exit code is the plain `check`'s."""
    app = PreflightApp(run, repo, cfg, deps or Deps())
    app.run()
    return app.exit_code
