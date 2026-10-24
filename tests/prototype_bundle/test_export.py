"""The exporter (lab plan L1.1): the allowlist only, read from git, scanned, hashed, repeatable."""

from __future__ import annotations

import hashlib
import subprocess
from collections.abc import Collection
from pathlib import Path

import pytest

from prototype_bundle.export import BundleRefusedError, ExportReport, export
from prototype_bundle.scan import Hit

SPEC = "docs/superpowers/specs/2026-10-23-prototype-core-design.md"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(r: Path) -> None:
    _git(r, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "add", "-A")
    _git(r, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-q", "-m", "x")


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
        SPEC: "# Spec\n",
    }
    for rel, text in files.items():
        p = r / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(r.parent, "init", "-q", str(r))
    _commit(r)
    return r


ALLOWLIST = f"""
repos:
  lab: {{path: ".", ref: "@export"}}
files:
  - {{repo: lab, from: lab/owm_kernel/kernel.py, to: source/lab/owm_kernel/kernel.py}}
  - {{repo: lab, glob: "lab/owm_service/*.py", exclude: [lab/owm_service/smoke.py],
     to: source/lab/owm_service/}}
  - {{repo: lab, from: lab/rounds/tools_server.py, to: source/lab/rounds/tools_server.py}}
  - {{repo: lab, glob: "dataset/evidence/documents/**", to: inputs/northstar/documents/}}
  - {{repo: lab, glob: "dataset/evidence/structured/**", to: inputs/northstar/structured/}}
  - {{repo: lab, from: {SPEC}, to: docs/spec.md}}
"""

EMPTY_SCRUB = "replace: []\nkeep: []\n"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


def _no_hits(root: Path, org: Collection[str]) -> list[Hit]:
    return []


def _run(
    repo: Path,
    tmp_path: Path,
    out: str = "out",
    *,
    allowlist: str = ALLOWLIST,
    scrub: str = EMPTY_SCRUB,
    dataset_tag: str | None = None,
) -> tuple[Path, ExportReport]:
    dest = tmp_path / out
    report = export(
        _git(repo, "rev-parse", "HEAD"),
        dest,
        scrub=_write(tmp_path, f"{out}-scrub.yaml", scrub),
        allowlist=_write(tmp_path, f"{out}-allow.yaml", allowlist),
        repo=repo,
        scan_fn=_no_hits,
        staging=tmp_path / "staging",
        dataset_tag=dataset_tag,
    )
    return dest, report


def _files(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def _other_repo(tmp_path: Path, name: str, files: dict[str, str]) -> str:
    other = tmp_path / name
    for rel, text in files.items():
        (other / rel).parent.mkdir(parents=True, exist_ok=True)
        (other / rel).write_text(text)
    _git(tmp_path, "init", "-q", str(other))
    _commit(other)
    return _git(other, "rev-parse", "HEAD")


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
    allow = ALLOWLIST + '  - {repo: lab, glob: "dataset/evidence/*", to: inputs/top/}\n'
    with pytest.raises(BundleRefusedError, match="matches nothing"):
        _run(repo, tmp_path, allowlist=allow)  # MANIFEST.yaml is the glob's only match
    dest, _ = _run(repo, tmp_path)
    assert not [p for p in _files(dest) if p.endswith("MANIFEST.yaml")]


@pytest.mark.parametrize(
    "denied",
    [
        # the plan's named deny list
        "truth/organization.yaml",
        "dataset/answer-key/answers.yaml",
        "dataset/evaluation/sheet.csv",
        "site/index.html",
        "owm/owm-spec.md",
        "runs/2026-10-08-register-attacks/plan.md",
        "tests/test_oracle.py",
        "docs/superpowers/plans/2026-10-23-prototype-lab-work.md",
        "dataset/evidence/MANIFEST.yaml",
        # and everything else that isn't on the code-level list of what may leave
        "README.md",
        "src/northstar/oracle.py",
        "dataset/evidence-variants/missing-contract-evidence/documents/a.md",
        "lab/rounds/scenarios.py",
        "lab/owm_service/contract/s22.example.ts",
        "lab/owm_register/base.yaml",
        "lab/prototype_bundle/scan.py",
        "docs/superpowers/specs/2026-10-10-owm-service-design.md",
    ],
)
def test_deny_list_wins_over_the_allowlist(repo: Path, tmp_path: Path, denied: str) -> None:
    allow = ALLOWLIST + f"  - {{repo: lab, from: {denied}, to: docs/x.md}}\n"
    with pytest.raises(BundleRefusedError, match="deny"):
        _run(repo, tmp_path, allowlist=allow)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize(
    ("src", "dest"),
    [
        ("./truth/organization.yaml", "docs/x.md"),
        ("lab/../truth/organization.yaml", "docs/x.md"),
        ("/etc/hosts", "docs/x.md"),
        ("lab/owm_kernel/kernel.py", "../escape.py"),
        ("lab/owm_kernel/kernel.py", "/tmp/escape.py"),
        ("lab//owm_kernel/kernel.py", "docs/x.py"),
    ],
)
def test_paths_must_be_plain(repo: Path, tmp_path: Path, src: str, dest: str) -> None:
    allow = ALLOWLIST + f'  - {{repo: lab, from: "{src}", to: "{dest}"}}\n'
    with pytest.raises(BundleRefusedError, match="path"):
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
    def one_hit(root: Path, org: Collection[str]) -> list[Hit]:
        return [Hit(file="docs/spec.md", line=1, term_kind="person")]

    dest = tmp_path / "handover" / "out"
    report = export(
        _git(repo, "rev-parse", "HEAD"),
        dest,
        scrub=_write(tmp_path, "s.yaml", EMPTY_SCRUB),
        allowlist=_write(tmp_path, "a.yaml", ALLOWLIST),
        repo=repo,
        scan_fn=one_hit,
        staging=tmp_path / "staging",
    )
    assert report.scan_hits == [Hit(file="docs/spec.md", line=1, term_kind="person")]
    assert not dest.exists()
    assert list((tmp_path / "staging").iterdir()) == []
    assert not (tmp_path / "handover").exists() or list((tmp_path / "handover").iterdir()) == []


def test_org_content_is_decided_by_source_not_destination(repo: Path, tmp_path: Path) -> None:
    seen: list[frozenset[str]] = []

    def record(root: Path, org: Collection[str]) -> list[Hit]:
        seen.append(frozenset(org))
        return []

    allow = ALLOWLIST + (
        "  - {repo: lab, from: lab/owm_kernel/kernel.py, to: inputs/northstar/documents/k.py}\n"
    )
    export(
        _git(repo, "rev-parse", "HEAD"),
        tmp_path / "out",
        scrub=_write(tmp_path, "s.yaml", EMPTY_SCRUB),
        allowlist=_write(tmp_path, "a.yaml", allow),
        repo=repo,
        scan_fn=record,
        staging=tmp_path / "staging",
    )
    assert seen == [
        frozenset({"inputs/northstar/documents/policy.md", "inputs/northstar/structured/crm.csv"})
    ]


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


def test_an_outside_repo_exports_only_its_named_files(repo: Path, tmp_path: Path) -> None:
    sha = _other_repo(
        tmp_path,
        "garbanzo",
        {
            "owm/docs/foundation-contract-v0.2.md": "# KF v0.2\n",
            "owm/docs/contract-v1.2.md": "# a lab-derived document\n",
        },
    )
    repos = f"  glowing-garbanzo: {{path: ../garbanzo, ref: {sha}}}\nfiles:\n"
    allow = ALLOWLIST.replace("files:\n", repos) + (
        "  - {repo: glowing-garbanzo, from: owm/docs/foundation-contract-v0.2.md,"
        " to: contracts/kf-foundation-contract-v0.2.md}\n"
    )
    dest, _ = _run(repo, tmp_path, allowlist=allow)
    assert (dest / "contracts/kf-foundation-contract-v0.2.md").read_text() == "# KF v0.2\n"
    assert f"`{sha}`" in (dest / "README.md").read_text()

    other_doc = allow + (
        "  - {repo: glowing-garbanzo, from: owm/docs/contract-v1.2.md, to: contracts/c.md}\n"
    )
    with pytest.raises(BundleRefusedError, match="deny"):
        _run(repo, tmp_path, "o2", allowlist=other_doc)
    a_glob = allow + ('  - {repo: glowing-garbanzo, glob: "owm/docs/*.md", to: contracts/all/}\n')
    with pytest.raises(BundleRefusedError, match="glob"):
        _run(repo, tmp_path, "o3", allowlist=a_glob)


def test_an_unknown_repo_is_refused(repo: Path, tmp_path: Path) -> None:
    sha = _other_repo(tmp_path, "elsewhere", {"x.md": "x\n"})
    allow = (
        ALLOWLIST.replace("files:\n", f"  elsewhere: {{path: ../elsewhere, ref: {sha}}}\nfiles:\n")
        + "  - {repo: elsewhere, from: x.md, to: docs/x.md}\n"
    )
    with pytest.raises(BundleRefusedError, match="deny"):
        _run(repo, tmp_path, allowlist=allow)


def test_the_dataset_tag_must_name_the_export_commit(repo: Path, tmp_path: Path) -> None:
    _git(repo, "tag", "dataset-test")
    dest, _ = _run(repo, tmp_path, dataset_tag="dataset-test")
    assert "`dataset-test`" in (dest / "README.md").read_text()

    (repo / "lab/owm_service/app.py").write_text("APP = 2\n")
    _commit(repo)
    with pytest.raises(BundleRefusedError, match="dataset-test"):
        _run(repo, tmp_path, "later", dataset_tag="dataset-test")


def test_doc_rewrites_are_listed_as_changes(repo: Path, tmp_path: Path) -> None:
    scrub = """
replace:
  - {file: docs/spec.md, match: "# Spec", replace: "# The spec", kind: doc,
     why: a heading in a copied document is reworded}
keep: []
"""
    dest, report = _run(repo, tmp_path, scrub=scrub)
    assert (dest / "docs/spec.md").read_text() == "# The spec\n"
    assert report.code_changes == ["docs/spec.md: a heading in a copied document is reworded"]


_SIBLINGS = [
    Path(__file__).resolve().parents[2] / p
    for p in ("../../glowing-garbanzo", "../../../Sandbox/sovera-owm")
]


@pytest.mark.skipif(not all(p.exists() for p in _SIBLINGS), reason="needs the sibling repos")
def test_the_real_export_at_head_is_clean(tmp_path: Path) -> None:
    from prototype_bundle.export import HERE
    from prototype_bundle.scan import REPO_ROOT

    head = _git(REPO_ROOT, "rev-parse", "HEAD")
    report = export(
        head,
        tmp_path / "bundle",
        scrub=HERE / "scrub.yaml",
        allowlist=HERE / "allowlist.yaml",
        staging=tmp_path / "staging",
    )
    assert report.scan_hits == []
    got = _files(tmp_path / "bundle")
    assert {
        "README.md",
        "FILES.sha256",
        "docs/spec.md",
        "docs/rulings.md",
        "docs/plan.md",
        "contracts/kf-foundation-contract-v0.2.md",
        "contracts/kf-knowledge.ts",
    } <= got
    assert not [p for p in got if p.endswith("MANIFEST.yaml") or ".example." in p]
