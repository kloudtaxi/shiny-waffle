"""BlueLeaf lab MCP server, task B-02: the walls, tested before they are built (spec §9 T1, T2, T4,
T6 and T7; plan, task 2).

Each test is a strict xfail that names the task that builds its wall, and accepts only the
failure a missing wall gives (a module that doesn't exist yet, or a helper that says which task
fills it in). Any other failure is a broken test and shows as one. A wall that starts passing
early fails the run (strict), and its task removes the marker.

The modules under test are imported with `importlib` inside each test, so this file collects and
type-checks before they exist.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from blueleaf_helpers import open_session, scripted_session

LAB = Path(__file__).resolve().parents[1]
PACKAGE = LAB / "lab/blueleaf_mcp"


def not_built(task: int) -> pytest.MarkDecorator:
    return pytest.mark.xfail(
        strict=True,
        raises=(ModuleNotFoundError, NotImplementedError),
        reason=f"wall not built: task {task}",
    )


# -- T1: the import wall ----------------------------------------------------------------------
ARMS = {
    "plain": ["list_documents", "read_document", "get_procedure", "submit_decision"],
    "register": ["list_documents", "read_document", "get_procedure", "get_register",
                 "submit_decision"],
    "owm": ["list_documents", "read_document", "get_procedure", "get_register", "decide",
            "submit_decision"],
}  # fmt: skip
# One ordinary call per subject tool (spec §4.2). `submit_decision` goes last: the seal lifts
# after the last answer.
CALLS: dict[str, dict[str, Any]] = {
    "list_documents": {"question": "Q1"},
    "read_document": {"question": "Q1", "file": "structured/employees.csv"},
    "get_procedure": {"decision_type": "credit"},
    "get_register": {"decision_type": "credit"},
    "decide": {"question": "Q1"},
    "submit_decision": {"question": "Q1", "decision": {"outcome": "REVIEW_REQUIRED"}},
}
AUDIT = """
import json, os, sys
opened = []

def hook(event, args):
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        opened.append(os.fsdecode(args[0]))

sys.addaudithook(hook)
sys.path.insert(0, {package!r})
import anyio
from mcp.client import Client
import subject_server

CALLS = json.loads({calls!r})

async def main():
    called = []
    async with Client(subject_server.build({arm!r})) as client:
        listed = [t.name for t in (await client.list_tools()).tools]
        for name in sorted(listed, key=lambda n: n == "submit_decision"):
            await client.call_tool(name, CALLS[name])
            called.append(name)
    return listed, called

listed, called = anyio.run(main)
mods = {{n: getattr(m, "__file__", None) for n, m in list(sys.modules.items())}}
print("AUDIT " + json.dumps({{"listed": listed, "called": called, "modules": mods,
                              "opened": opened}}))
"""
FORBIDDEN_MODULES = ("scoring", "build_register", "score")
FORBIDDEN_DIRS = ("truth", "dataset/answer-key", "dataset/evaluation", "site", "runs")


def under(path: Path, rel: str) -> bool:
    return path.is_relative_to((LAB / rel).resolve())


@not_built(20)
@pytest.mark.parametrize("arm", sorted(ARMS))
def test_import_wall(arm: str, tmp_path: Path) -> None:
    pytest.importorskip("mcp")
    home = tmp_path / "home"
    open_session(home, arm, ["S26"])
    env = {k: v for k, v in os.environ.items() if not k.startswith("TYPESAFE_API_KEY")}
    env["BLUELEAF_HOME"] = str(home)
    script = AUDIT.format(package=str(PACKAGE), calls=json.dumps(CALLS), arm=arm)
    proc = subprocess.run([sys.executable, "-c", script], cwd=LAB, env=env, capture_output=True,
                          text=True, timeout=600)  # fmt: skip
    assert proc.returncode == 0, proc.stderr[-2000:]
    line = next(x for x in reversed(proc.stdout.splitlines()) if x.startswith("AUDIT "))
    audit = json.loads(line.removeprefix("AUDIT "))
    assert sorted(audit["listed"]) == sorted(ARMS[arm])  # every tool of the arm is called once
    assert sorted(audit["called"]) == sorted(audit["listed"])
    for name, file in audit["modules"].items():
        assert name not in FORBIDDEN_MODULES and not name.startswith("northstar"), name
        if file:
            path = Path(file).resolve()
            assert not under(path, "runs") and not under(path, "truth"), (name, file)
    for raw in audit["opened"]:
        path = (LAB / raw).resolve() if not os.path.isabs(raw) else Path(raw).resolve()
        assert not any(under(path, d) for d in FORBIDDEN_DIRS), raw
        assert not path.name.endswith("-key.json"), raw


# -- T2: the file wall ------------------------------------------------------------------------
REFUSED = [
    "../x",
    "/etc/hosts",
    "documents/../../truth/x",
    "MANIFEST.yaml",
    "answer-key/S01.json",
    "documents/linked_outside.md",  # a symlink out of the corpus
    "documents/linked_manifest.md",  # a symlink to a file in the corpus but outside the pattern
    "documents/notes.txt",
    "structured/accounts.json",
]
ALLOWED = ["documents/acme_parent_guarantee.md", "structured/crm_accounts.csv"]


def small_corpus(tmp: Path) -> Path:
    root = tmp / "corpus"
    for rel, text in {
        "documents/acme_parent_guarantee.md": "---\ndoc_id: GRT-X\n---\nA guarantee.\n",
        "structured/crm_accounts.csv": "account_id,account_name\nCRM-1,Acme\n",
        "MANIFEST.yaml": "traps: []\n",
        "answer-key/S01.json": "{}\n",
        "documents/notes.txt": "notes\n",
        "structured/accounts.json": "{}\n",
    }.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    (tmp / "truth").mkdir()
    (tmp / "truth/x").write_text("truth\n")
    (tmp / "outside.md").write_text("outside\n")
    (root / "documents/linked_outside.md").symlink_to(tmp / "outside.md")
    (root / "documents/linked_manifest.md").symlink_to(root / "MANIFEST.yaml")
    return root


@not_built(3)
@pytest.mark.parametrize("rel", REFUSED)
def test_file_wall_refuses(rel: str, tmp_path: Path) -> None:
    walls = importlib.import_module("service.walls")
    errors = importlib.import_module("service.errors")
    root = small_corpus(tmp_path)
    with pytest.raises(errors.RefusedError, match="not one of this question's documents"):
        walls.subject_path(root, rel)


@not_built(3)
@pytest.mark.parametrize("rel", ALLOWED)
def test_file_wall_allows(rel: str, tmp_path: Path) -> None:
    walls = importlib.import_module("service.walls")
    root = small_corpus(tmp_path)
    assert Path(walls.subject_path(root, rel)) == (root / rel).resolve()


# -- T4: subject.json carries no answer -------------------------------------------------------
FORBIDDEN_KEYS = {"outcome", "expected", "decision", "approver", "approvers", "class", "safety",
                  "scenario", "scenario_id", "key", "attack"}  # fmt: skip
INPUTS = {"discount": {"record", "as_of"}, "credit": {"record", "as_of"},
          "sla": {"ticket_id", "decided_at"}}  # fmt: skip


def outcome_codes() -> set[str]:
    """The ten outcome codes: discount and credit share five, SLA has five."""
    specs = LAB / "lab/owm_kernel/specs"
    return {str(o) for f in ("discount.yaml", "sla_agent.yaml")
            for o in yaml.safe_load((specs / f).read_text())["outcomes"]}  # fmt: skip


def walk(node: Any, path: str = "") -> list[tuple[str, str | None, Any]]:
    """Every value in a JSON document, at any depth: (where, the key it sits under, value)."""
    if isinstance(node, dict):
        return [x for k, v in node.items()
                for x in [(f"{path}.{k}", str(k), v), *walk(v, f"{path}.{k}")]]  # fmt: skip
    if isinstance(node, list):
        return [x for i, v in enumerate(node)
                for x in [(f"{path}[{i}]", None, v), *walk(v, f"{path}[{i}]")]]  # fmt: skip
    return []


@not_built(19)
def test_subject_json_schema(tmp_path: Path) -> None:
    # One scenario of each type: a discount, a credit and an SLA question.
    path = open_session(tmp_path / "home", "plain", ["S01", "S26", "S36"])
    data = json.loads(path.read_text())
    assert set(data) == {"session", "arm", "created", "live_jev", "questions"}
    questions = data["questions"]
    assert list(questions) == [f"Q{i}" for i in range(1, len(questions) + 1)]
    assert {q["decision_type"] for q in questions.values()} == set(INPUTS)
    for q in questions.values():
        assert set(q) == {"corpus", "decision_type", "as_of", "inputs", "root"}
        assert set(q["inputs"]) == INPUTS[q["decision_type"]]
    codes = outcome_codes()
    assert len(codes) == 10
    for where, key, value in walk(data):
        assert key not in FORBIDDEN_KEYS, where
        if isinstance(value, str):
            assert value not in codes, where
            assert not re.search(r"\bS\d{2}\b", value), where


# -- T6: dataset/ is never written --------------------------------------------------------------
@not_built(23)
def test_dataset_untouched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    walls = importlib.import_module("service.walls")
    monkeypatch.setenv("BLUELEAF_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("BLUELEAF_RUNS", str(tmp_path / "runs"))
    before = walls.tree_digest(LAB / "dataset")
    scripted_session(tmp_path / "home", tmp_path / "runs")
    assert walls.tree_digest(LAB / "dataset") == before


# -- T7: the secret guard (unit) --------------------------------------------------------------
DUMMY_KEY = "ts-dummy-" + "5e1f" * 8  # never a real key


@not_built(3)
def test_secret_guard_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key_file = tmp_path / "typesafe.key"
    key_file.write_text(DUMMY_KEY + "\n")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.setenv("TYPESAFE_API_KEY_FILE", str(key_file))
    # The guard reads the key once; reload so it reads this test's dummy key.
    guard = importlib.reload(importlib.import_module("service.guard"))
    errors = importlib.import_module("service.errors")
    with pytest.raises(errors.RefusedError, match="output withheld"):
        guard.scrub(f"the reply was {DUMMY_KEY}.")
    with pytest.raises(errors.RefusedError):
        guard.check_log_line(json.dumps({"tool": "read_document", "result": DUMMY_KEY}))
    clean = "nothing secret here"
    assert guard.scrub(clean) == clean
