"""The one boundary between the BlueLeaf service and the lab's decision code (plan, task 1).

The lab modules (`lab/owm_kernel`, `lab/decision_engine`, `lab/owm_register`,
`lab/reader_inputs`) are scripts' siblings, not a package, so they are reached by putting their
directories on `sys.path`. This is the only file under `lab/blueleaf_mcp/` that does that (a test
holds it to that). mypy doesn't follow the lab modules (pyproject, the BlueLeaf MCP spec §11 B9),
so everything the service uses is re-exported here with a type: the Protocols say what the
service relies on, and the wrappers cast the lab's untyped returns to them.

Nothing here imports `build_register` or `northstar`: the service stays on the subject's side of
the answer-key wall (spec §2.1).
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol, cast

LAB = Path(__file__).resolve().parents[3]
PATHS = ("lab/owm_kernel", "lab/decision_engine", "lab/owm_register", "lab/reader_inputs")
for _rel in PATHS:
    if str(LAB / _rel) not in sys.path:
        sys.path.insert(0, str(LAB / _rel))

import credit  # noqa: E402
import engine  # noqa: E402
import flow  # noqa: E402
import governed  # noqa: E402
import kernel  # noqa: E402
import overlay as reader_overlay  # noqa: E402
import serve  # noqa: E402

Json = dict[str, Any]
MODEL = "jev-1.13.0"  # pinned: aliases like jev-latest move


# -- the types the service relies on ----------------------------------------------------------
class Engine(Protocol):
    """A typed-decision engine (Jev's wire format)."""

    model: str

    def ask(self, state: Any, questions: Json) -> Json: ...


class Doc(Protocol):
    """One document on file: YAML front matter, then the body."""

    filename: str
    doc_id: str
    title: str
    owner: str
    front: Json
    body: str
    raw: str


class Evidence(Protocol):
    """One corpus: its documents and its system-of-record tables."""

    root: Path

    def docs(self) -> list[Doc]: ...

    def table(self, name: str) -> list[dict[str, str]]: ...


class Register(Protocol):
    """A company's register of approved governing documents, with its content-addressed store."""

    entries: list[Json]
    store: Path | None

    def status(self, docs: list[Doc]) -> dict[str, str]: ...


SpecError = cast(type[ValueError], flow.SpecError)
NoProcedureError = cast(type[Exception], governed.NoProcedureError)
COVERAGE = cast(dict[str, dict[str, str]], serve.COVERAGE)


# -- the evidence port and the document register ----------------------------------------------
def evidence(root: Path) -> Evidence:
    """The corpus at `root` (its `documents/*.md` and `structured/*.csv`)."""
    return cast(Evidence, kernel.Evidence(root))


def load_register(path: Path) -> Register:
    """The register at `path`, with its store at `path.parent / "store"`."""
    return cast(Register, kernel.Register.load(path))


def fingerprint(text: str) -> str:
    """The register's normalized sha256 of a document's whole text."""
    return cast(str, kernel.fingerprint(text))


def served(corpus: str, decision: str, root: Path | None = None) -> str:
    """The register for one company and one decision type, as served to an agent. `root` (a
    sandbox's register directory) arrives with task 7; until then only the frozen one serves."""
    if root is None:
        return cast(str, serve.served(corpus, decision))
    return cast(str, serve.served(corpus, decision, root=root))


# -- specs and decisions ----------------------------------------------------------------------
def load_spec(path: Path) -> Json:
    """A spec from its file, validated (`SpecError` if malformed)."""
    return cast(Json, flow.load(path))


def loads_spec(text: str, name: str) -> Json:
    """A spec from its text; `name` is used in error messages only."""
    return cast(Json, flow.loads(text, name))


def run_spec(
    spec: Json, eng: Engine, ev: Evidence, inputs: Json,
    register: Register | None = None, trace: Json | None = None,
) -> Json:  # fmt: skip
    """One decision by a spec (the YAML runner)."""
    return cast(Json, flow.run(spec, eng, ev, inputs, register, trace))


def credit_decide(eng: Engine, ev: Evidence, as_of: date, record: dict[str, str], sid: str) -> Json:
    """One credit decision by the v1 python engine; `record` is the ERP credit request row."""
    return cast(Json, credit.decide(eng, ev, as_of, record, sid))


def procedure_entries(path: Path) -> list[Json]:
    """The entries of a procedure register (G-13)."""
    return cast(list[Json], governed.procedures(path))


def governed_decide(
    decision_type: str, eng: Engine, ev: Evidence, inputs: Json, at: date | datetime | str,
    register: Register | None, *, entries: list[Json], store: Path, specs: Path,
) -> Json:  # fmt: skip
    """One decision by the procedure version in force on `at`, run from its approved text, and
    stamped with that version (G-13). The register, store and specs are always the sandbox's, so
    none of them defaults to the frozen lab copy."""
    return cast(
        Json,
        governed.decide(decision_type, eng, ev, inputs, at, register, entries, store, specs),
    )


def overlay(src: Path, dst: Path, record: dict[str, str], kind: str) -> Path:
    """A copy of the corpus at `src`, at `dst`, whose export holds `record` and no alternative
    version of it (G-36)."""
    return cast(Path, reader_overlay.overlay(src, dst, record, kind))


# -- the Jev engine pieces --------------------------------------------------------------------
def request_hash(model: str, state: Any, questions: Json) -> str:
    """The key a recorded Jev exchange is filed under. Paths are never part of it."""
    return cast(str, engine.request_hash(model, state, questions))


def recorder(inner: Engine, path: Path) -> Engine:
    """`inner`, with every exchange appended to `path` and an identical request answered from it."""
    return cast(Engine, engine.Recorder(inner, path))


def typesafe(model: str = MODEL) -> Engine:
    """TypeSafe's hosted Jev. Reads the key from the environment when called, so call it only when
    a live call is actually needed (never in replay)."""
    return cast(Engine, engine.TypeSafe(model))
