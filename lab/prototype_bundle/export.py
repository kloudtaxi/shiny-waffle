"""The exporter (lab plan L1.1): writes the port bundle the prototype's builder reads (spec §11.4).

Only what `allowlist.yaml` names leaves the lab, and two checks in code stand behind it: each repo
may export only the files `PERMITTED` names, and the deny list wins over both. Paths must be plain
(no `./`, `..`, `//` or absolute paths). Every file is read from git (`git show <ref>:<path>`),
never from the working tree. The scrub (`scrub.yaml`, L1.2) is applied, then the private scan (L1.3)
runs over the staged bundle, with terms from the commit being exported; any hit means nothing is
written. The bundle is staged outside the folder it is handed over in, and an existing export is
never overwritten.

    PYTHONPATH=lab uv run python -m prototype_bundle.export --commit <sha> --out <dir> \\
      [--dataset-tag dataset-YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import errno
import fnmatch
import hashlib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from prototype_bundle.scan import REPO_ROOT, Hit, scan

HERE = Path(__file__).resolve().parent
EXPORT_REF = "@export"  # in allowlist.yaml: the lab repo at the commit being exported
STAGING = REPO_ROOT / ".bundle-staging"  # gitignored; never inside the handover folder

# What each repo may ever export, whatever the allowlist says. Changing the bundle means changing
# both this and allowlist.yaml, on purpose.
PERMITTED: Mapping[str, tuple[str, ...]] = {
    "lab": (
        "docs/superpowers/specs/2026-10-23-prototype-core-design.md",
        "docs/superpowers/specs/2026-10-23-prototype-core-rulings.md",
        "docs/superpowers/plans/2026-10-23-prototype-core.md",
        "lab/owm_kernel/*.py",
        "lab/owm_kernel/SPEC_FORMAT.md",
        "lab/owm_kernel/specs/discount.yaml",
        "lab/owm_kernel/specs/credit_v3.yaml",
        "lab/owm_register/registrar.py",
        "lab/owm_service/*.py",
        "lab/owm_service/contract/owm-decisions.ts",
        "lab/owm_service/contract/README.md",
        "lab/decision_engine/engine.py",
        "lab/rounds/tools_server.py",
        "dataset/evidence/documents/**",
        "dataset/evidence/structured/**",
    ),
    "glowing-garbanzo": (
        "owm/docs/foundation-contract-v0.2.md",
        "web-next/lib/contract/knowledge.ts",
    ),
    "sovera-owm": (
        "specs/001-identity-authz-ports/contracts/identity-provider.md",
        "specs/001-identity-authz-ports/contracts/authorization-provider.md",
    ),
}
# Never exported, even where PERMITTED would allow it: CLAUDE.md's never-load list and the lab's own
# plans, runs and tests (lab repo), and in any repo the manifest and worked examples.
DENY: Mapping[str, tuple[str, ...]] = {
    "lab": (
        "truth/**",
        "dataset/answer-key/**",
        "dataset/evaluation/**",
        "site/**",
        "owm/**",
        "runs/**",
        "tests/**",
        "docs/superpowers/plans/*lab-work*",
        "lab/owm_service/smoke.py",
    ),
    "*": ("**/MANIFEST.yaml", "**/*.example.*"),
}
# The org's own content: scanned for the lab's markers only (scan.LAB_MARKER_KINDS).
ORG_CONTENT = ("dataset/evidence/documents/**", "dataset/evidence/structured/**")

USE = """\
# The port bundle

This bundle is what the prototype's builder may read of the lab (spec §11.3 and §11.4): the spec,
its Appendix A and the builder's plan; the allowlisted lab source the prototype ports, scrubbed; the
contracts it starts from; and one org's documents and exported tables as that org's content.

Nothing else from the lab is the builder's to read or ask for: no scenario ids, expected outcomes,
acceptance suite, lab tests, runs, scorers or judge prompts, and nothing about a second org.
Gate results come back as counts and mechanism notes.

Comments in `source/` cite the lab service's own spec by § and its rulings by R-number. That spec
is not in this bundle; `docs/rulings.md` restates every ruling as a mechanism, and "§" in `docs/`
means `docs/spec.md`.
"""

ScanFn = Callable[[Path, Collection[str]], list[Hit]]


class BundleRefusedError(Exception):
    """The export would break the bundle's rules; nothing was written."""


@dataclass(frozen=True)
class ExportReport:
    files: int
    scrubbed_lines: int
    code_changes: list[str] = field(default_factory=list)
    scan_hits: list[Hit] = field(default_factory=list)


def _git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args], check=True, capture_output=True
        ).stdout
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
        raise BundleRefusedError(f"git {' '.join(args[:2])} in {repo}: {detail[0]}") from None


def _match(pattern: str, path: str) -> bool:
    """Segment-wise glob: `*` stays inside one segment, `**` spans any number of segments."""

    def go(ps: list[str], xs: list[str]) -> bool:
        if not ps:
            return not xs
        if ps[0] == "**":
            return any(go(ps[1:], xs[i:]) for i in range(len(xs) + 1))
        return bool(xs) and fnmatch.fnmatchcase(xs[0], ps[0]) and go(ps[1:], xs[1:])

    return go(pattern.split("/"), path.split("/"))


def _plain(path: str, *, folder: bool = False) -> str:
    """A path inside its repo or bundle: relative, no empty, `.` or `..` segments, no backslash."""
    body = path[:-1] if folder and path.endswith("/") else path
    if folder and not path.endswith("/"):
        raise BundleRefusedError(f"path: a glob's destination must end in '/': {path!r}")
    if (
        not body
        or body.startswith("/")
        or "\\" in body
        or any(seg in ("", ".", "..") for seg in body.split("/"))
    ):
        raise BundleRefusedError(f"path: {path!r} must be a plain relative path")
    return path


def _allowed(repo_name: str, path: str) -> None:
    deny = (*DENY.get(repo_name, ()), *DENY["*"])
    if any(_match(g, path) for g in deny):
        raise BundleRefusedError(f"deny list: {repo_name}:{path} is never exported")
    if not any(_match(g, path) for g in PERMITTED.get(repo_name, ())):
        raise BundleRefusedError(f"deny list: {repo_name}:{path} is not permitted to leave")


def _static_prefix(pattern: str) -> str:
    parts = []
    for seg in pattern.split("/"):
        if any(c in seg for c in "*?["):
            break
        parts.append(seg)
    return "/".join(parts) + "/" if parts else ""


def _collect(
    allow: Mapping[str, Any], commit: str, repo: Path
) -> tuple[dict[str, bytes], dict[str, str], set[str]]:
    """The bundle's files by bundle path, each repo's resolved sha, and which files are org
    content (by their source)."""
    files: dict[str, bytes] = {}
    shas: dict[str, str] = {}
    org: set[str] = set()
    for entry in allow["files"]:
        name = str(entry["repo"])
        spec = allow["repos"][name]
        root = (repo / spec["path"]).resolve()
        is_lab = spec["ref"] == EXPORT_REF
        ref = commit if is_lab else str(spec["ref"])
        sha = _git(root, "rev-parse", f"{ref}^{{commit}}").decode().strip()
        shas[name] = sha
        if "from" in entry:
            src, dest = _plain(str(entry["from"])), _plain(str(entry["to"]))
            _allowed(name, src)
            pairs = [(src, dest)]
        else:
            if not is_lab:
                raise BundleRefusedError(f"allowlist: {name} may export named files only, no glob")
            pattern, exclude = _plain(str(entry["glob"])), set(entry.get("exclude", []))
            to = _plain(str(entry["to"]), folder=True)
            listed = _git(root, "ls-tree", "-r", "--name-only", sha).decode().splitlines()
            names = [n for n in listed if _match(pattern, n) and n not in exclude]
            names = [n for n in names if not any(_match(g, n) for g in (*DENY["lab"], *DENY["*"]))]
            for n in names:
                _allowed(name, n)
            if not names:
                raise BundleRefusedError(f"allowlist: {pattern} matches nothing at {sha[:12]}")
            prefix = _static_prefix(pattern)
            pairs = [(n, to + n[len(prefix) :]) for n in names]
        for src, dest in pairs:
            if dest in files:
                raise BundleRefusedError(f"allowlist: two sources map to {dest}")
            files[dest] = _git(root, "show", f"{sha}:{src}")
            if is_lab and any(_match(g, src) for g in ORG_CONTENT):
                org.add(dest)
    return files, shas, org


def _scrub(files: dict[str, bytes], doc: Mapping[str, Any]) -> tuple[int, list[str]]:
    lines, changes = 0, []
    for e in doc.get("replace") or []:
        path, match, count = str(e["file"]), str(e["match"]), int(e.get("count", 1))
        if path not in files:
            raise BundleRefusedError(f"scrub: {path} is not in the bundle")
        if e.get("kind") not in ("comment", "code", "doc"):
            raise BundleRefusedError(f"scrub: {path}: kind must be comment, code or doc")
        try:
            text = files[path].decode("utf-8")
        except UnicodeDecodeError:
            raise BundleRefusedError(f"scrub: {path} is not UTF-8 text") from None
        found = text.count(match)
        if found != count:
            raise BundleRefusedError(f"scrub: {path}: expected {count} match(es), found {found}")
        files[path] = text.replace(match, str(e["replace"])).encode("utf-8")
        lines += max(1, len(match.splitlines())) * count
        if e["kind"] in ("code", "doc"):  # listed in the README; a comment rewrite isn't
            changes.append(f"{path}: {e['why']}")
    return lines, changes


def _readme(
    shas: Mapping[str, str], allow: Mapping[str, Any], report: ExportReport, dataset_tag: str | None
) -> str:
    out = [USE, "## Source commits", ""]
    out += [
        f"- `{name}` ({allow['repos'][name]['path']}): `{sha}`"
        for name, sha in sorted(shas.items())
    ]
    dataset = (
        f"the tag `{dataset_tag}`, which names the `lab` commit above"
        if dataset_tag
        else "the `lab` commit above (no dataset tag was given)"
    )
    out += ["", f"The org's documents and exported tables in `inputs/` are {dataset}."]
    out += ["", "## Changed from source", ""]
    out += [f"- {c}" for c in report.code_changes] or ["- nothing beyond comments"]
    out += [
        "",
        f"The scrub rewrote {report.scrubbed_lines} lines in all (comments, code and "
        f"documents). `FILES.sha256` lists the bundle's other {report.files - 1} files with "
        "their hashes.",
        "",
    ]
    return "\n".join(out)


def _place(stage: Path, out: Path) -> None:
    try:
        stage.rename(out)
    except OSError as e:
        if e.errno != errno.EXDEV:
            raise
        shutil.copytree(stage, out)  # staging is on another filesystem
        shutil.rmtree(stage)


def export(
    commit: str,
    out: Path,
    *,
    scrub: Path,
    allowlist: Path,
    repo: Path = REPO_ROOT,
    scan_fn: ScanFn | None = None,
    staging: Path = STAGING,
    dataset_tag: str | None = None,
) -> ExportReport:
    """Write the bundle for `commit` to `out`, or write nothing and say why."""
    if out.exists():
        raise BundleRefusedError(f"{out} exists; an export is never overwritten")
    allow = yaml.safe_load(allowlist.read_text())
    files, shas, org = _collect(allow, commit, repo)
    lab = next(n for n, s in allow["repos"].items() if s["ref"] == EXPORT_REF)
    if dataset_tag is not None:
        tagged = _git(repo, "rev-parse", f"{dataset_tag}^{{commit}}").decode().strip()
        if tagged != shas[lab]:
            raise BundleRefusedError(
                f"dataset tag {dataset_tag} is at {tagged[:12]}, not the "
                f"export commit {shas[lab][:12]}"
            )
    scrubbed, changes = _scrub(files, yaml.safe_load(scrub.read_text()) or {})
    report = ExportReport(files=len(files) + 2, scrubbed_lines=scrubbed, code_changes=changes)
    files["README.md"] = _readme(shas, allow, report, dataset_tag).encode("utf-8")
    run_scan = scan_fn or (lambda root, o: scan(root, o, repo=repo, commit=shas[lab]))
    staging.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="bundle-", dir=staging))
    try:
        for rel, data in sorted(files.items()):
            p = stage / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        hits = run_scan(stage, frozenset(org))
        if hits:
            return ExportReport(report.files, report.scrubbed_lines, report.code_changes, hits)
        sums = [f"{hashlib.sha256(data).hexdigest()}  {rel}" for rel, data in sorted(files.items())]
        (stage / "FILES.sha256").write_text("\n".join(sums) + "\n")
        out.parent.mkdir(parents=True, exist_ok=True)
        _place(stage, out)
        return report
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--dataset-tag")
    ap.add_argument("--scrub", type=Path, default=HERE / "scrub.yaml")
    ap.add_argument("--allowlist", type=Path, default=HERE / "allowlist.yaml")
    args = ap.parse_args(argv)
    try:
        report = export(
            args.commit,
            args.out,
            scrub=args.scrub,
            allowlist=args.allowlist,
            dataset_tag=args.dataset_tag,
        )
    except BundleRefusedError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    if report.scan_hits:
        print(f"refused: {len(report.scan_hits)} scan hits; nothing written", file=sys.stderr)
        for h in report.scan_hits:
            print(f"  {h.file}:{h.line} {h.term_kind}", file=sys.stderr)
        return 1
    print(
        f"wrote {args.out}: {report.files} files, {report.scrubbed_lines} scrubbed lines, "
        f"{len(report.code_changes)} listed changes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
