"""The app's screens: the main view, a check's details, the accept-drift dialog and the spend view.

Screens only show what the engine produced; the app owns the workers and every engine call.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import ClassVar

from pydantic import JsonValue
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Input, Static
from textual.worker import get_current_worker

from preflight.baseline import baseline_values
from preflight.checks.agent_context import CHECKED
from preflight.config import CheckName
from preflight.engine import Evaluation, Event, describe_exc, repo_relative
from preflight.labels import LABEL, MARK
from preflight.record import (
    Accepted,
    CheckResult,
    Value,
    amendment_line,
    drift_text,
    fmt_value,
    record_name,
)
from preflight.spend import spend_view

RUNNING = "◌"
STYLE = {"✔": "bold green", "✖": "bold red", RUNNING: "yellow", "·": "dim"}
ACCEPTED = "✔"  # accepted drift: a pass mark, in the warning colour
ACCEPTED_STYLE = "bold yellow"
SHORT = 18  # longer values are cut in the main table; `enter` shows them whole
SHORT_SOURCE = 30
SPEND_SECONDS = 3
FINGERPRINT_COLUMNS = (
    ("mark", ""),
    ("label", "Fingerprint"),
    ("baseline", "baseline"),
    ("now", "now"),
    ("source", "read from"),
)


def _mark(mark: str, style: str | None = None) -> Text:
    return Text(mark, style=STYLE.get(mark, "") if style is None else style)


def _cut(text: str, width: int | None) -> Text:
    return Text(text if width is None or len(text) <= width else text[: width - 1] + "…")


def _cell(value: JsonValue, width: int | None = None) -> Text:
    return _cut("" if value is None else fmt_value(value), width)


def _value_mark(v: Value) -> str:
    """`✖` drifted, blank when it matches, `·` recorded but not compared."""
    if v.ok is False:
        return "✖"
    return " " if v.ok else "·"


class CheckTable(DataTable[Text]):
    """One row per check. `enter` opens the selected check's details."""

    BINDINGS: ClassVar[list[BindingType]] = [Binding("enter", "select_cursor", "details")]


class MainScreen(Screen[None]):
    """The header, the checks, the fingerprint table and the status line with the banner."""

    def __init__(self, run: Path, repo: Path, checks: list[CheckName]) -> None:
        super().__init__()
        self.run_dir = run
        self.repo = repo
        self.checks = checks
        self.results: dict[str, CheckResult] = {}

    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            run = repo_relative(self.run_dir, self.repo)
            yield Static(f"Pre-flight  {run}", id="run", markup=False)
            yield Static("baseline: …", id="baseline", markup=False)
        yield CheckTable(id="checks", cursor_type="row", show_header=False)
        yield DataTable[Text](id="fingerprint", cursor_type="row")
        with Horizontal(id="statusline"):
            yield Static("running…", id="status", markup=False)
            yield Static("", id="banner", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        checks = self.query_one("#checks", CheckTable)
        checks.add_column("", key="mark", width=1)
        checks.add_column("check", key="label", width=14)
        checks.add_column("summary", key="summary")
        for name in self.checks:
            checks.add_row(_mark(RUNNING), Text(LABEL[name]), Text("waiting"), key=name)
        fp = self.query_one("#fingerprint", DataTable)
        for key, label in FINGERPRINT_COLUMNS:
            fp.add_column(label, key=key)
        self.watch(self.app, "banner_text", self._show_banner)

    def _show_banner(self, text: str) -> None:
        banner = self.query_one("#banner", Static)
        banner.update(text)
        banner.set_class(text.startswith("✔"), "-pass")
        banner.set_class(text.startswith("✖"), "-fail")
        banner.set_class(text.startswith(RUNNING), "-running")

    def set_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)

    def reset(self) -> None:
        """A new evaluation: every check waits, the fingerprint table empties."""
        self.results.clear()
        checks = self.query_one("#checks", CheckTable)
        for name in self.checks:
            self._set_row(checks, name, RUNNING, "waiting")
        self.query_one("#fingerprint", DataTable).clear()
        self.query_one("#baseline", Static).update("baseline: …")  # an acceptance moves it
        self.set_status("running…")

    def _set_row(
        self, checks: CheckTable, name: str, mark: str, text: str, style: str | None = None
    ) -> None:
        checks.update_cell(name, "mark", _mark(mark, style))
        checks.update_cell(name, "summary", Text(text), update_width=True)

    def show_event(self, e: Event) -> None:
        if e.check not in self.checks:
            return
        checks = self.query_one("#checks", CheckTable)
        if e.kind == "done" and e.result is not None:
            self.results[e.check] = e.result
            self._set_row(checks, e.check, MARK[e.result.status], e.result.summary)
        else:
            self._set_row(checks, e.check, RUNNING, e.text)

    def show_evaluation(self, ev: Evaluation) -> None:
        """The baseline in the header and the fingerprint's compared fields in the table."""
        if ev.baseline is None:
            where = "none (this record sets it)"
        elif ev.baseline.same_run:
            where = f"preflight/{ev.baseline.path.name}"
        else:
            where = repo_relative(ev.baseline.path, self.repo)
        self.query_one("#baseline", Static).update(f"baseline: {where}")
        fp = self.results.get("fingerprint")
        if fp is None:
            return
        then = baseline_values(ev.baseline.record) if ev.baseline is not None else {}
        table = self.query_one("#fingerprint", DataTable)
        for v in fp.values:
            old: JsonValue = v.baseline  # set on compared fields; recorded ones come from `then`
            if old is None and v.field in then:
                old = then[v.field].value
            table.add_row(
                _mark(_value_mark(v)),
                Text(v.label),
                _cell(old, SHORT),
                _cell(v.value, SHORT),
                _cut(v.source, SHORT_SOURCE),
                key=v.field,
            )

    def show_accepted(self, accepted: Accepted) -> None:
        """The accepted record's fields stop reading as drift: marked accepted, with the reason."""
        accept = _mark(ACCEPTED, ACCEPTED_STYLE)
        table = self.query_one("#fingerprint", DataTable)
        for field in accepted.fields:
            if field in table.rows:
                table.update_cell(field, "mark", accept)
        fp = self.results.get("fingerprint")
        if fp is not None:
            checks = self.query_one("#checks", CheckTable)
            text = f"{fp.summary} · accepted: {accepted.reason}"
            self._set_row(checks, "fingerprint", ACCEPTED, text, ACCEPTED_STYLE)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        name = event.row_key.value if event.data_table.id == "checks" else "fingerprint"
        result = self.results.get(name or "")
        if result is None:
            self.app.notify("still running")
            return
        if result.name == "agent_context" and not result.values:
            # Its values are the reader's, which the fingerprint records (F-14).
            fp = self.results.get("fingerprint")
            reader = [v for v in fp.values if v.group == "reader"] if fp is not None else []
            if reader:
                note = "the reader's values, as the fingerprint recorded them"
                self.app.push_screen(DetailScreen(result, reader, note))
            else:
                self.app.push_screen(DetailScreen(result, [], f"checked: {', '.join(CHECKED)}"))
            return
        self.app.push_screen(DetailScreen(result))


class DetailScreen(Screen[None]):
    """Every value of one check, with its source and state, and its problems.

    `values` and `note` let a check show values another check recorded (agent context's are
    the fingerprint's reader values) and say so.
    """

    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape", "app.pop_screen", "back")]

    def __init__(
        self, check: CheckResult, values: list[Value] | None = None, note: str | None = None
    ) -> None:
        super().__init__()
        self.check = check
        self.values = check.values if values is None else values
        self.note = note

    def compose(self) -> ComposeResult:
        c = self.check
        yield Static(f"{MARK[c.status]} {LABEL[c.name]}  {c.summary}", id="title", markup=False)
        none = "no problems" if self.values or self.note else "no values recorded"
        if self.note:
            none += f" · {self.note}"
        problems = "\n".join(f"- {p}" for p in c.problems) or none
        yield Static(problems, id="problems", markup=False)
        yield DataTable[Text](id="values", cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#values", DataTable)
        for label in ("", "field", "compared with", "now", "state", "read from"):
            table.add_column(label)
        for v in self.values:
            table.add_row(
                _mark(_value_mark(v)),
                Text(v.label),
                _cell(v.baseline),
                _cell(v.value),
                Text(v.state),
                Text(v.source),
            )


class AcceptDriftScreen(ModalScreen[str | None]):
    """Lists the drift, previews the amendment line, and returns the reason (None: cancelled)."""

    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape", "cancel", "cancel")]

    def __init__(self, drift: list[Value], at: datetime) -> None:
        """`at` is fixed when the dialog opens and is the time `finish` writes at (T12-a)."""
        super().__init__()
        self.drift = drift
        self.at = at

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Accept drift", id="dialog-title")
            drifted = "\n".join(f"✖ {drift_text(v)}" for v in self.drift)
            yield Static(drifted, id="drifted", markup=False)
            yield Input(placeholder="why this drift is acceptable (required)", id="reason")
            yield Static("appended to notes.md:", classes="hint")
            yield Static(self._preview(""), id="preview", markup=False)
            with Horizontal(id="buttons"):
                yield Button("Accept drift", id="confirm", variant="warning", disabled=True)
                yield Button("Cancel", id="cancel")

    def _preview(self, reason: str) -> str:
        shown = " ".join(reason.split()) or "<reason>"  # as finish() will write it
        return amendment_line(self.at, self.drift, shown, f"preflight/{record_name(self.at)}")

    def on_input_changed(self, event: Input.Changed) -> None:
        self.query_one("#confirm", Button).disabled = not event.value.strip()
        self.query_one("#preview", Static).update(self._preview(event.value))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.value.strip():
            self.dismiss(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm":
            self.dismiss(self.query_one("#reason", Input).value)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class SpendScreen(Screen[None]):
    """The run folder's spend, re-read every few seconds in a thread worker (F-11).

    The scan walks the whole run folder, so it never runs on the UI thread.
    """

    BINDINGS: ClassVar[list[BindingType]] = [Binding("escape", "app.pop_screen", "back")]

    def __init__(self, run: Path) -> None:
        super().__init__()
        self.run_dir = run

    def compose(self) -> ComposeResult:
        yield Static(f"Spend  {self.run_dir.name}", id="title", markup=False)
        yield Static("reading the run folder's spend…", id="spend", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self._read()
        self.set_interval(SPEND_SECONDS, self._read)

    def _view(self) -> str:
        try:
            return spend_view(self.run_dir)
        except Exception as exc:  # a worker that raises would end the app
            return f"spend unreadable: {describe_exc(exc)}"

    @work(thread=True, exclusive=True, group="spend")
    def _read(self) -> None:
        worker = get_current_worker()
        text = self._view()
        if not worker.is_cancelled:
            self.app.call_from_thread(self._show, text)

    def _show(self, text: str) -> None:
        try:
            self.query_one("#spend", Static).update(text)
        except NoMatches:  # the screen closed while the worker read
            pass
