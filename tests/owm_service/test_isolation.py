"""Isolation (B-06 Task 7; constraints): nothing in `lab/owm_service/` imports the truth model or
the admission gate, names the lab's answer side, or opens it at run time.

The static half reads the service's source. The runtime half runs a decision in a fresh
interpreter with an audit hook that records every path opened or listed, so a read through any
module the service pulls in counts too."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path, PurePosixPath
from typing import Any

import pytest

LAB = Path(__file__).resolve().parents[2]
SERVICE = LAB / "lab/owm_service"
FORBIDDEN_TEXT = ("truth/", "answer-key", "dataset/evaluation", "site/")
# a path component on its own, as `LAB / "truth"` builds it, or inside a path string
FORBIDDEN_PARTS = frozenset({"truth", "answer-key", "answer_key", "evaluation", "site"})
# modules that load the truth model: the admission gate and the register's bootstrap builder
FORBIDDEN_MODULES = frozenset({"admit", "spec_admission", "build_register"})
IMPORT_CALLS = frozenset({"import_module", "__import__", "find_spec", "spec_from_file_location",
                          "run_module", "run_path"})  # fmt: skip
DOTTED = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
FORBIDDEN_DIRS = [LAB / "truth", LAB / "dataset/answer-key", LAB / "dataset/evaluation",
                  LAB / "site"]  # fmt: skip


def _forbidden_module(name: str) -> bool:
    parts = name.split(".")
    return parts[0] == "northstar" or bool(FORBIDDEN_MODULES & set(parts))


def _forbidden_string(text: str, imported: bool) -> str | None:
    """Why a string constant is forbidden, or None. `imported`: it is an import call's argument.
    A bare "northstar" elsewhere is a name (the org id), not a module; a dotted one is a module."""
    parts = PurePosixPath(text).parts
    if any(t in text for t in FORBIDDEN_TEXT) or FORBIDDEN_PARTS & set(parts):
        return "path"
    if any(PurePosixPath(p).stem in FORBIDDEN_MODULES for p in parts):
        return "module file"
    if DOTTED.fullmatch(text) and (
        FORBIDDEN_MODULES & set(text.split("."))
        or (text.split(".")[0] == "northstar" and ("." in text or imported))
    ):
        return "module name"
    return None


def _callee(node: ast.Call) -> str:
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def violations(source: str) -> list[str]:
    """Forbidden imports, and string constants that name the answer side (a path or a path
    component) or a forbidden module (`importlib.import_module("admit")`), in one module."""
    tree = ast.parse(source)
    imported = {id(a) for n in ast.walk(tree) if isinstance(n, ast.Call)
                and _callee(n) in IMPORT_CALLS for a in n.args}  # fmt: skip
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [f"import {a.name}" for a in node.names if _forbidden_module(a.name)]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module, *(f"{node.module}.{a.name}" for a in node.names)]
            if any(_forbidden_module(n) for n in names):
                out.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            why = _forbidden_string(node.value, id(node) in imported)
            if why:
                out.append(f"{why} {node.value[:60]!r}")
    return out


@pytest.mark.parametrize(
    "source",
    ["import northstar.model", "from northstar import model", "import admit",
     "from spec_admission import admit", "import importlib\nimportlib.import_module('admit')",
     "P = 'truth/scenarios'", "P = 'dataset/answer-key/x.yaml'",
     "P = LAB / 'dataset/evaluation'", "P = 'site/index.html'",
     # the codebase's own idiom (build_register.py reaches the truth as LAB / "truth")
     "P = LAB / 'truth'", "P = LAB / 'truth' / 'scenarios'", "P = LAB / 'site'",
     "P = LAB / 'dataset' / 'evaluation'", "P = 'dataset/answer_key'",
     "import importlib\nimportlib.import_module('northstar')",
     "import importlib\nimportlib.import_module('build_register')",
     "import northstar", "import build_register", "from build_register import REG",
     "M = 'northstar.build'", "P = 'lab/owm_register/build_register.py'",
     "P = LAB / 'lab/spec_admission/admit.py'"],
)  # fmt: skip
def test_the_scan_catches_what_it_looks_for(source: str) -> None:
    assert violations(source)


@pytest.mark.parametrize(
    "source",
    ["P = LAB / 'dataset/evidence'", "P = LAB / 'dataset' / 'evidence-variants' / corpus",
     "P = LAB / 'runs'", "D = 'lab/owm_kernel'", "from .errors import CannotDecide",
     "import importlib\nimportlib.import_module('kernel')",
     "ORG = 'northstar'",  # Task 8's default org id: a name, not a module or a path
     "E = 'sarah.chen@northstar.example'", "S = 'the truth of the matter'",
     "S = 'an evaluation of the request'", "S = 'a site visit'", "S = 'admitted'",
     "S = 'answer key'"],
)  # fmt: skip
def test_the_scan_passes_ordinary_code(source: str) -> None:
    assert violations(source) == []


def test_no_forbidden_imports_or_paths() -> None:
    files = sorted(SERVICE.rglob("*.py"))
    assert SERVICE / "_lab.py" in files
    found = {str(f.relative_to(SERVICE)): v for f in files if (v := violations(f.read_text()))}
    assert found == {}


# -- the image ----------------------------------------------------------------------------------
IMAGE_PACKAGES = {"lab/owm_service/", "lab/owm_kernel/", "lab/owm_register/",
                  "lab/decision_engine/"}  # fmt: skip


def test_the_image_copies_only_the_service_and_the_lab_packages_it_imports() -> None:
    """I-3: the Dockerfile copies the service and the three lab packages `_lab.py` puts on the
    path, never the rest of `lab/` (`lab/utopia`, `lab/spec_admission`), `src/` or the repo
    README, and installs the dependencies without the project. The README's `docker run …
    isolated` check proves the same in a built image."""
    text = (SERVICE / "Dockerfile").read_text()
    sources = {s for line in text.splitlines() if line.startswith("COPY ") and "--from" not in line
               for s in line.split()[1:-1]}  # fmt: skip
    assert {s for s in sources if s.startswith("lab")} == IMAGE_PACKAGES
    assert not sources & {"src/", "src", "README.md", "lab/", "lab", ".", "./"}
    assert "--no-install-project" in text
    on_path = set(re.findall(r'"(lab/\w+)"', (SERVICE / "_lab.py").read_text()))
    assert {f"{p}/" for p in on_path} | {"lab/owm_service/"} == IMAGE_PACKAGES


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


def test_runtime_never_opens_truth(tmp_path: Path) -> None:
    assert_isolated(audited(ORG_DECIDE, tmp_path))
