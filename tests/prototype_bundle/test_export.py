"""The exporter (lab plan L1.1): the allowlist only, read from git, scanned, hashed, repeatable."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from prototype_bundle.export import BundleRefusedError, ExportReport, export
from prototype_bundle.scan import Hit


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    files = {
        "lab/owm_kernel/kernel.py": "def decide():\n    return 'route_to'\n",
        "lab/owm_kernel/notes.txt": "not allowlisted\n",
        "lab/owm_service/app.py": "APP = 1\n",
        "lab/owm_service/smoke.py": "SMOKE = 1\n",
        "lab/rounds/tools_server.py": "# prompt for one request\nPROMPT = 'decide request X'\n",
        "truth/organization.yaml": "name: secret\n",
        "dataset/evidence/MANIFEST.yaml": "hints: yes\n",
        "dataset/evidence/documents/policy.md": "# Policy\n",
        "dataset/evidence/structured/crm.csv": "id\n1\n",
        "docs/superpowers/plans/2026-10-23-prototype-lab-work.md": "lab only\n",
        "docs/spec.md": "# Spec\n",
    }
    for rel, text in files.items():
        p = r / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(r.parent, "init", "-q", str(r))
    _git(r, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
    _git(r, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "-m", "x")
    return r


ALLOWLIST = """
repos:
  lab: {path: ".", ref: "@export"}
files:
  - {repo: lab, from: lab/owm_kernel/kernel.py, to: source/lab/owm_kernel/kernel.py}
  - {repo: lab, glob: "lab/owm_service/*.py", exclude: [lab/owm_service/smoke.py],
     to: source/lab/owm_service/}
  - {repo: lab, from: lab/rounds/tools_server.py, to: source/lab/rounds/tools_server.py}
  - {repo: lab, glob: "dataset/evidence/**", to: inputs/northstar/}
  - {repo: lab, from: docs/spec.md, to: docs/spec.md}
"""

EMPTY_SCRUB = "replace: []\nkeep: []\n"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


def _no_hits(root: Path) -> list[Hit]:
    return []


def _run(
    repo: Path,
    tmp_path: Path,
    out: str = "out",
    *,
    allowlist: str = ALLOWLIST,
    scrub: str = EMPTY_SCRUB,
) -> tuple[Path, ExportReport]:
    dest = tmp_path / out
    report = export(
        _git(repo, "rev-parse", "HEAD"),
        dest,
        scrub=_write(tmp_path, f"{out}-scrub.yaml", scrub),
        allowlist=_write(tmp_path, f"{out}-allow.yaml", allowlist),
        repo=repo,
        scan_fn=_no_hits,
    )
    return dest, report


def _files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_only_allowlisted_files_are_copied(repo: Path, tmp_path: Path) -> None:
    dest, _ = _run(repo, tmp_path)
    assert _files(dest) == {
        "README.md",
        "FILES.sha256",
        "source/lab/owm_kernel/kernel.py",
        "source/lab/owm_service/app.py",
        "source/lab/rounds/tools_server.py",
        "inputs/northstar/documents/policy.md",
        "inputs/northstar/structured/crm.csv",
        "docs/spec.md",
    }


def test_manifest_yaml_is_never_copied(repo: Path, tmp_path: Path) -> None:
    dest, _ = _run(repo, tmp_path)
    assert not [p for p in _files(dest) if p.endswith("MANIFEST.yaml")]


@pytest.mark.parametrize(
    "denied",
    [
        "truth/organization.yaml",
        "docs/superpowers/plans/2026-10-23-prototype-lab-work.md",
        "dataset/evidence/MANIFEST.yaml",
    ],
)
def test_deny_list_wins_over_the_allowlist(repo: Path, tmp_path: Path, denied: str) -> None:
    allow = ALLOWLIST + f"  - {{repo: lab, from: {denied}, to: docs/x.md}}\n"
    with pytest.raises(BundleRefusedError, match="deny"):
        _run(repo, tmp_path, allowlist=allow)
    assert not (tmp_path / "out").exists()


def test_files_sha256_matches_the_copies(repo: Path, tmp_path: Path) -> None:
    dest, _ = _run(repo, tmp_path)
    lines = (dest / "FILES.sha256").read_text().splitlines()
    listed = {}
    for line in lines:
        digest, rel = line.split("  ", 1)
        listed[rel] = digest
    assert set(listed) == _files(dest) - {"FILES.sha256"}
    for rel, digest in listed.items():
        assert hashlib.sha256((dest / rel).read_bytes()).hexdigest() == digest


def test_export_is_reproducible(repo: Path, tmp_path: Path) -> None:
    a, _ = _run(repo, tmp_path, "a")
    b, _ = _run(repo, tmp_path, "b")
    assert _files(a) == _files(b)
    for rel in _files(a):
        assert (a / rel).read_bytes() == (b / rel).read_bytes(), rel


def test_working_tree_never_leaks(repo: Path, tmp_path: Path) -> None:
    (repo / "lab/owm_kernel/kernel.py").write_text("UNCOMMITTED = True\n")
    dest, _ = _run(repo, tmp_path)
    assert "UNCOMMITTED" not in (dest / "source/lab/owm_kernel/kernel.py").read_text()


def test_scan_hits_mean_nothing_is_written(repo: Path, tmp_path: Path) -> None:
    def one_hit(root: Path) -> list[Hit]:
        return [Hit(file="docs/spec.md", line=1, term_kind="person")]

    dest = tmp_path / "out"
    report = export(
        _git(repo, "rev-parse", "HEAD"),
        dest,
        scrub=_write(tmp_path, "s.yaml", EMPTY_SCRUB),
        allowlist=_write(tmp_path, "a.yaml", ALLOWLIST),
        repo=repo,
        scan_fn=one_hit,
    )
    assert report.scan_hits == [Hit(file="docs/spec.md", line=1, term_kind="person")]
    assert not dest.exists()


def test_scrub_is_applied_and_code_changes_listed(repo: Path, tmp_path: Path) -> None:
    scrub = """
replace:
  - file: source/lab/rounds/tools_server.py
    match: "# prompt for one request\\nPROMPT = 'decide request X'\\n"
    replace: "PROMPT = ''  # the builder supplies its own prompt\\n"
    kind: code
    why: a prompt fixed to one request is removed
keep: []
"""
    dest, report = _run(repo, tmp_path, scrub=scrub)
    text = (dest / "source/lab/rounds/tools_server.py").read_text()
    assert text == "PROMPT = ''  # the builder supplies its own prompt\n"
    assert report.scrubbed_lines == 2
    assert report.code_changes == [
        "source/lab/rounds/tools_server.py: a prompt fixed to one request is removed"
    ]
    assert "a prompt fixed to one request is removed" in (dest / "README.md").read_text()


def test_scrub_entry_that_no_longer_matches_refuses(repo: Path, tmp_path: Path) -> None:
    scrub = """
replace:
  - {file: source/lab/owm_kernel/kernel.py, match: "not in the file", replace: "", kind: comment}
keep: []
"""
    with pytest.raises(BundleRefusedError, match="scrub"):
        _run(repo, tmp_path, scrub=scrub)


def test_existing_output_is_never_overwritten(repo: Path, tmp_path: Path) -> None:
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "keep.txt").write_text("earlier export\n")
    with pytest.raises(BundleRefusedError, match="exists"):
        _run(repo, tmp_path)
    assert (tmp_path / "out" / "keep.txt").read_text() == "earlier export\n"


def test_deny_list_scopes_to_the_lab_repo(repo: Path, tmp_path: Path) -> None:
    # The KF contract lives under owm/docs/ in another repo; the lab's own owm/ stays denied.
    other = tmp_path / "other"
    (other / "owm/docs").mkdir(parents=True)
    (other / "owm/docs/foundation-contract-v0.2.md").write_text("# KF v0.2\n")
    _git(tmp_path, "init", "-q", str(other))
    _git(other, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
    _git(
        other, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "-m", "x"
    )
    sha = _git(other, "rev-parse", "HEAD")
    allow = ALLOWLIST.replace("files:\n", f"  kf: {{path: ../other, ref: {sha}}}\nfiles:\n") + (
        "  - {repo: kf, from: owm/docs/foundation-contract-v0.2.md,"
        " to: contracts/kf-foundation-contract-v0.2.md}\n"
    )
    dest, _ = _run(repo, tmp_path, allowlist=allow)
    assert (dest / "contracts/kf-foundation-contract-v0.2.md").read_text() == "# KF v0.2\n"
    assert f"`{sha}`" in (dest / "README.md").read_text()
