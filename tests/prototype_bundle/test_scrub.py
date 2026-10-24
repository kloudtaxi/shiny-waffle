"""The scrub (lab plan L1.2): the exported source keeps its mechanisms and loses the lab's markers.

These run the real allowlist's source entries at HEAD through the real `scrub.yaml`.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from prototype_bundle.export import HERE, _collect, _scrub
from prototype_bundle.scan import REPO_ROOT, scan

PATTERN = re.compile(r"\bS[0-9]{1,2}\b|[Ss]cenario|[Tt]rap|[Tt]ruth|answer.key|MANIFEST")
# A pointer out of the bundle: to another repo's docs or worked examples, the lab's runs or tests,
# or the lab's corpus variants. Reviewed exceptions are `keep` entries.
POINTERS = re.compile(
    r"owm/docs/|web-next/|runs/20|tests/|github\.com|\.example\.|shiny-waffle|"
    r"evidence-variants|missing-contract|missing-guarantee|b18-"
)
LAB_READS = re.compile(
    r"runs/20|\"runs\"|truth/|answer-key|dataset/evaluation|spec_admission|"
    r"rounds\.scenarios|p2_items"
)


def _scrub_doc() -> dict[str, Any]:
    doc: dict[str, Any] = yaml.safe_load((HERE / "scrub.yaml").read_text())
    return doc


@pytest.fixture(scope="module")
def source() -> dict[str, str]:
    allow = yaml.safe_load((HERE / "allowlist.yaml").read_text())
    allow["files"] = [e for e in allow["files"] if str(e["to"]).startswith("source/")]
    files, _, _ = _collect(allow, "HEAD", REPO_ROOT)
    _scrub(
        files,
        {"replace": [e for e in _scrub_doc()["replace"] if str(e["file"]).startswith("source/")]},
    )
    return {rel: data.decode("utf-8") for rel, data in files.items()}


def _keeps_for(rel: str) -> list[str]:
    return [
        str(k["match"])
        for k in _scrub_doc().get("keep") or []
        if fnmatch.fnmatchcase(rel, str(k["file"]))
    ]


def test_scrub_leaves_no_pattern_hits(source: dict[str, str]) -> None:
    left = []
    for rel, text in source.items():
        keeps = _keeps_for(rel)
        for n, line in enumerate(text.splitlines(), start=1):
            rest = line
            for k in keeps:
                rest = rest.replace(k, "")
            if PATTERN.search(rest):
                left.append(f"{rel}:{n}: {line.strip()[:120]}")
    assert left == []


def test_scrub_leaves_no_scan_hits(source: dict[str, str], tmp_path: Path) -> None:
    for rel, text in source.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    assert [(h.file, h.line, h.term_kind) for h in scan(tmp_path)] == []


def test_scrub_leaves_no_reads_of_lab_paths(source: dict[str, str]) -> None:
    left = [
        f"{rel}:{n}"
        for rel, text in source.items()
        for n, line in enumerate(text.splitlines(), start=1)
        if LAB_READS.search(line)
    ]
    assert left == []


def test_scrubbed_python_still_compiles(source: dict[str, str]) -> None:
    for rel, text in source.items():
        if rel.endswith(".py"):
            compile(text, rel, "exec")


def test_every_keep_entry_still_matches(source: dict[str, str], contracts: dict[str, str]) -> None:
    bundle = {**source, **contracts}
    stale = [
        k
        for k in _scrub_doc().get("keep") or []
        if not any(
            str(k["match"]) in text
            for rel, text in bundle.items()
            if fnmatch.fnmatchcase(rel, str(k["file"]))
        )
    ]
    assert stale == []


def test_copied_contracts_leave_no_scan_hits(tmp_path: Path) -> None:
    # The contracts come from other repos; the bundle's copies are scrubbed like the source.
    allow = yaml.safe_load((HERE / "allowlist.yaml").read_text())
    allow["files"] = [e for e in allow["files"] if str(e["to"]).startswith("contracts/")]
    files, _, _ = _collect(allow, "HEAD", REPO_ROOT)
    _scrub(
        files,
        {
            "replace": [
                e for e in _scrub_doc()["replace"] if str(e["file"]).startswith("contracts/")
            ]
        },
    )
    for rel, data in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    assert [(h.file, h.line, h.term_kind) for h in scan(tmp_path)] == []


@pytest.fixture(scope="module")
def contracts() -> dict[str, str]:
    allow = yaml.safe_load((HERE / "allowlist.yaml").read_text())
    allow["files"] = [e for e in allow["files"] if str(e["to"]).startswith("contracts/")]
    files, _, _ = _collect(allow, "HEAD", REPO_ROOT)
    _scrub(
        files,
        {
            "replace": [
                e for e in _scrub_doc()["replace"] if str(e["file"]).startswith("contracts/")
            ]
        },
    )
    return {rel: data.decode("utf-8") for rel, data in files.items()}


def test_the_bundle_points_nowhere_outside_itself(
    source: dict[str, str], contracts: dict[str, str]
) -> None:
    left = []
    for rel, text in {**source, **contracts}.items():
        keeps = _keeps_for(rel)
        for n, line in enumerate(text.splitlines(), start=1):
            rest = line
            for k in keeps:
                rest = rest.replace(k, "")
            if POINTERS.search(rest):
                left.append(f"{rel}:{n}: {line.strip()[:120]}")
    assert left == []


def test_contracts_carry_no_reads_of_lab_paths(contracts: dict[str, str]) -> None:
    left = [
        f"{rel}:{n}"
        for rel, text in contracts.items()
        for n, line in enumerate(text.splitlines(), start=1)
        if LAB_READS.search(line)
    ]
    assert left == []
