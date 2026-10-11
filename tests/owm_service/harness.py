"""The OWM service tests' window on the lab (test side only).

It loads the committed admission gate (`lab/spec_admission/admit.py`) by path, as
`runs/2026-10-06-procedures-governed/run_governed.py` does, and uses its scenario inputs, its
register and its clean corpora. Jev is replay only: the engine reads every recording under `runs/`
and never goes live, and its own calls file sits in a temp dir, so nothing is written under `runs/`.
The corpora are copied once per test session.
"""

from __future__ import annotations

import atexit
import functools
import importlib
import importlib.util
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

LAB = Path(__file__).resolve().parents[2]

# the 42 decision scenarios, by decision type
DECISIONS: dict[str, list[str]] = {
    "discount": [f"S{n:02d}" for n in (*range(1, 6), *range(9, 26))],
    "credit": [f"S{n}" for n in range(26, 36)],
    "sla": [f"S{n}" for n in range(36, 46)],
}
KIND_OF = {sid: kind for kind, sids in DECISIONS.items() for sid in sids}
ROUTE_TO = {"discount": "REQUEST_EVIDENCE", "credit": "REQUEST_EVIDENCE", "sla": "CANNOT_DECIDE"}


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@functools.cache
def admit() -> ModuleType:
    """The admission gate's module. Loading it puts the kernel on `sys.path`."""
    return _load("admit", LAB / "lab/spec_admission/admit.py")


def lab(name: str) -> ModuleType:
    """A kernel module (`kernel`, `flow`, `governed`, `additions`), as the gate imports it."""
    admit()
    return importlib.import_module(name)


@functools.cache
def _tmp() -> Path:
    d = tempfile.TemporaryDirectory(prefix="ns-owm-tests-")
    atexit.register(d.cleanup)
    return Path(d.name)


@functools.cache
def gate() -> Any:
    """The gate, on a replay-only engine (live off, cap 0)."""
    a = admit()
    return a.Gate(a.Layered(_tmp() / "none.jsonl", live=False, cap=0))


@functools.cache
def roots() -> dict[str, Path]:
    """The clean corpora, copied once: corpus name -> root."""
    return dict(gate().clean_roots(_tmp() / "clean"))


def doc_ids(corpus: str) -> set[str]:
    """The doc_id of every document in the corpus."""
    kernel = lab("kernel")
    return {kernel.parse_doc(p.name, p.read_text()).doc_id
            for p in (roots()[corpus] / "documents").glob("*.md")}  # fmt: skip


def inputs(sid: str) -> dict[str, Any]:
    return dict(gate().inputs(KIND_OF[sid], sid))


def corpus(sid: str) -> str:
    return str(gate().corpus(KIND_OF[sid], sid))


def at_of(sid: str) -> Any:
    """The decision's date, as the committed gate run chooses it."""
    inp = inputs(sid)
    return inp.get("as_of") or gate().scen[sid].as_of or inp.get("decided_at")


def subject_of(sid: str) -> str:
    """The request id (discount, credit) or the ticket (SLA)."""
    inp = inputs(sid)
    return str(inp["ticket_id"] if KIND_OF[sid] == "sla" else inp["record"]["request_id"])


@functools.cache
def attacked_roots(attack: str) -> dict[str, Path]:
    """Copies of the corpora with one of set F's sealed attacks in place (`run_set_f.build`, as
    `runs/2026-10-06-register-fixes/check_withhold.py` builds them), built once per attack."""
    setf = admit().setf
    setf.check_seal()
    manifest = yaml.safe_load((setf.SET / "manifest.yaml").read_text())
    at = next(x for x in manifest if x["id"] == attack)
    return dict(setf.build(at, _tmp() / f"set-f-{attack}"))


def entries(sid: str, route: bool = False) -> list[dict[str, Any]]:
    """The procedure register's entries. With `route`, every version of the scenario's decision
    type is deployed in G-32 route mode (`on_mismatch: route`), as run_all.py's `+R` engines are."""
    out = []
    for e in lab("governed").procedures():
        if route and e["decision_type"] == KIND_OF[sid]:
            e = dict(e, deployment={**(e.get("deployment") or {}), "on_mismatch": "route"})
        out.append(e)
    return out


def route_mode(sid: str, route: bool = False) -> bool:
    """Whether the procedure in force for the scenario routes on a mismatch (`on_mismatch`)."""
    governed, flow = lab("governed"), lab("flow")
    entry = governed.in_force(entries(sid, route), KIND_OF[sid], at_of(sid))
    spec = flow.loads((governed.STORE / f"{entry['sha256']}.yaml").read_text(), entry["file"])
    spec["documents"].update(entry.get("deployment") or {})
    return bool(spec["documents"].get("on_mismatch", "use_registered") == "route")


def decide(
    sid: str, trace: dict[str, Any] | None = None, *, attack: str | None = None,
    route: bool = False,
) -> dict[str, Any]:  # fmt: skip
    """`governed.decide` on the scenario's inputs, corpus and register; with `attack`, on that set F
    attack's corpus, and with `route`, under route mode (`entries`)."""
    a, governed, c = admit(), lab("governed"), corpus(sid)
    root = (attacked_roots(attack) if attack else roots())[c]
    kwargs = {} if trace is None else {"trace": trace}
    record: dict[str, Any] = governed.decide(
        KIND_OF[sid], gate().eng, a.Evidence(root), inputs(sid), at_of(sid), a.ra.REG[c],
        entries(sid, route), **kwargs,
    )  # fmt: skip
    return record


def decide_with_capture(sid: str) -> tuple[dict[str, Any], list[str | None]]:
    """The decision, made inside `additions.capture`, and what each of its judgments is about."""
    additions = lab("additions")
    with additions.capture(subject=subject_of(sid)) as cap:
        record = decide(sid)
    about: list[str | None] = additions.judgment_about(record, cap)
    return record, about
