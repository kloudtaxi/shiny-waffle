"""Isolation (B-06 Task 7; constraints): nothing in `lab/owm_service/` imports the truth model or
the admission gate, names the lab's answer side, or opens it at run time.

The static half reads the service's source. The runtime half runs a decision in a fresh
interpreter with an audit hook that records every path opened or listed, so a read through any
module the service pulls in counts too."""

from __future__ import annotations

import ast
import importlib
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

LAB = Path(__file__).resolve().parents[2]
SERVICE = LAB / "lab/owm_service"
FORBIDDEN_TEXT = ("truth/", "answer-key", "dataset/evaluation", "site/")
FORBIDDEN_DIRS = [LAB / "truth", LAB / "dataset/answer-key", LAB / "dataset/evaluation",
                  LAB / "site"]  # fmt: skip


def _forbidden_module(name: str) -> bool:
    parts = name.split(".")
    return parts[0] == "northstar" or "admit" in parts or "spec_admission" in parts


def violations(source: str) -> list[str]:
    """Forbidden imports, and string constants that name the answer side or load a forbidden
    module by name (`importlib.import_module("admit")`), in one module's source."""
    out = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out += [f"import {a.name}" for a in node.names if _forbidden_module(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module, *(f"{node.module}.{a.name}" for a in node.names)]
            if any(_forbidden_module(n) for n in names):
                out.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value
            if any(t in text for t in FORBIDDEN_TEXT):
                out.append(f"string {text[:60]!r}")
            elif text in ("admit", "admit.py") or any(
                m in text for m in ("spec_admission", "northstar.model")
            ):
                out.append(f"module name {text[:60]!r}")
    return out


@pytest.mark.parametrize(
    "source",
    ["import northstar.model", "from northstar import model", "import admit",
     "from spec_admission import admit", "import importlib\nimportlib.import_module('admit')",
     "P = 'truth/scenarios'", "P = 'dataset/answer-key/x.yaml'",
     "P = LAB / 'dataset/evaluation'", "P = 'site/index.html'"],
)  # fmt: skip
def test_the_scan_catches_what_it_looks_for(source: str) -> None:
    assert violations(source)


def test_no_forbidden_imports_or_paths() -> None:
    files = sorted(SERVICE.glob("*.py"))
    assert SERVICE / "_lab.py" in files
    found = {f.name: v for f in files if (v := violations(f.read_text()))}
    assert found == {}


# -- the runtime half ---------------------------------------------------------------------------
AUDIT = """
import json, os, sys
OPENED = []
CWD = os.getcwd()

def _hook(event, args):
    if event in ("open", "os.listdir", "os.scandir") and args:
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)):
            OPENED.append(os.fsdecode(p))

sys.addaudithook(_hook)
"""

REPORT = """
print(json.dumps({"opened": OPENED, "cwd": CWD, "outcome": r.record["gated_outcome"],
                  "approver": r.approval_roles[0]["person_id"],
                  "northstar_model": "northstar.model" in sys.modules}))
"""

# `_lab.decide` on S01 as the service will make it: the DR-9001 row read from the CSV, as_of
# 2026-09-23, the bootstrap register and procedures, a replay-only engine. No test harness.
LAB_DECIDE = """
import csv
from datetime import date
from pathlib import Path
from owm_service import _lab

tmp = Path(sys.argv[1])
root = _lab.corpus_root("base")
with (root / "structured/discount_requests.csv").open() as f:
    row = next(r for r in csv.DictReader(f) if r["request_id"] == "DR-9001")
state = _lab.register_bootstrap("base")
register = _lab.kernel_register(state, tmp / "register")
terms = {e["doc_id"]: e.get("terms") for e in state.entries}
entries, store = _lab.procedures_bootstrap()
engine = _lab.ReplayEngine(_lab.replay_files(_lab.LAB_ROOT), tmp / "calls.jsonl", live=False,
                           cap=0)
r = _lab.decide("discount", evidence=_lab.make_evidence(root, lambda name, rows: rows),
                inputs={"sid": "DEC-0001", "record": row, "as_of": date(2026, 9, 23)},
                at=date(2026, 9, 23), register=register, entries=entries, store=store,
                engine=engine, staff=_lab.staff(root), requested_by=row["requested_by"],
                policy_terms=terms.get, route_mode=False)
assert not (tmp / "calls.jsonl").exists()
"""

# The same through an `Org` (Task 8): its systems of record, register, procedures and engine.
ORG_DECIDE = """
from datetime import date
from pathlib import Path
from owm_service import _lab
from owm_service.config import load_settings
from owm_service.org import Org

tmp = Path(sys.argv[1])
org = Org(load_settings({"OWM_STATE_DIR": str(tmp / "state")}))
row = org.sor.row("discount_requests", "DR-9001")
entries, store = org.procedures()
r = _lab.decide("discount", evidence=org.evidence,
                inputs={"sid": "DEC-0001", "record": row, "as_of": date(2026, 9, 23)},
                at=date(2026, 9, 23), register=org.kernel_register(), entries=entries,
                store=store, engine=org.engine, staff=org.evidence.table("employees"),
                requested_by=row["requested_by"], policy_terms=org.policy_terms,
                route_mode=org.on_mismatch() == "route")
"""


def audited(script: str, tmp: Path) -> dict[str, Any]:
    """Run `script` in a fresh interpreter under the audit hook; what it opened, and its result."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("TYPESAFE_")}
    env["PYTHONPATH"] = str(LAB / "lab")
    code = AUDIT + textwrap.dedent(script) + REPORT
    proc = subprocess.run(
        [sys.executable, "-c", code, str(tmp)], cwd=tmp, env=env, capture_output=True,
        text=True, timeout=600, check=False,
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr[-4000:]
    out: dict[str, Any] = json.loads(proc.stdout.splitlines()[-1])
    return out


def assert_isolated(out: dict[str, Any]) -> None:
    opened = [(Path(out["cwd"]) / p).resolve() for p in out["opened"]]
    assert any(p.is_relative_to(LAB / "dataset/evidence") for p in opened)  # the hook saw reads
    bad = sorted({str(p) for p in opened if any(p.is_relative_to(d) for d in FORBIDDEN_DIRS)})
    assert bad == []
    assert out["northstar_model"] is False
    assert (out["outcome"], out["approver"]) == ("APPROVE_WITH_AUTHORIZATION", "EMP-200")


def test_lab_decide_never_opens_truth(tmp_path: Path) -> None:
    assert_isolated(audited(LAB_DECIDE, tmp_path))


@pytest.mark.xfail(strict=True, raises=ModuleNotFoundError, reason="needs Task 8 (Org)")
def test_runtime_never_opens_truth(tmp_path: Path) -> None:
    importlib.import_module("owm_service.org")  # fails here, for the right reason, until Task 8
    assert_isolated(audited(ORG_DECIDE, tmp_path))
