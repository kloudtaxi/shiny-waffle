"""One organisation: settings, event log, clock, systems of record, people, the Jev replay engine,
the overlay evidence, the register and the procedures (spec §2)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from . import _lab
from .clock import Clock
from .config import Settings
from .events import EventLog
from .people import People
from .sor import SystemsOfRecord


class Org:
    def __init__(
        self, settings: Settings, *, org_id: str = "northstar", corpus: str | None = None
    ) -> None:
        self.settings, self.org_id = settings, org_id
        self.corpus = corpus or settings.corpus
        self.dir = settings.state_dir / org_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log = EventLog(self.dir / "events.sqlite")
        self.clock = Clock(self.log, org_id, settings.clock)
        self.clock.now()  # start it now: a first read inside a write transaction would deadlock
        root = _lab.corpus_root(self.corpus)
        self.sor = SystemsOfRecord(self.log, org_id, root)
        self.people = People(_lab.staff(root))
        self.engine = _lab.ReplayEngine(
            _lab.replay_files(_lab.LAB_ROOT),
            self.dir / "jev-calls.jsonl",
            live=settings.jev == "live",
            cap=settings.jev_cap,
        )
        self.evidence = _lab.make_evidence(root, self._overlay)
        self._state: Any = _lab.register_bootstrap(self.corpus)
        self._kernel_register: tuple[int, Any] | None = None

    def _overlay(self, name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        """The kernel's view of a table: the systems of record's (base rows, inserts, edits)."""
        return self.sor.table(name)

    def register_state(self) -> Any:
        return self._state

    def kernel_register(self) -> Any:
        state = self.register_state()
        if self._kernel_register is None or self._kernel_register[0] != state.version:
            self._kernel_register = (
                state.version,
                _lab.kernel_register(state, self.dir / "store"),
            )
        return self._kernel_register[1]

    def procedures(self) -> tuple[list[dict[str, Any]], Path]:
        return _lab.procedures_bootstrap()

    def on_mismatch(self) -> Literal["use_registered", "route"]:
        return "use_registered"

    def policy_terms(self, doc_id: str) -> dict[str, Any] | None:
        for e in self.register_state().entries:
            if e["doc_id"] == doc_id:
                terms: dict[str, Any] | None = e.get("terms")
                return terms
        return None
