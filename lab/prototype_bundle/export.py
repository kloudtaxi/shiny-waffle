"""The exporter (lab plan L1.1): writes the port bundle the prototype's builder reads (spec §11.4).

Only what `allowlist.yaml` names leaves the lab, and the deny list wins over it. Every file is read
from git (`git show <ref>:<path>`), never from the working tree. The scrub (`scrub.yaml`, L1.2) is
applied, then the private scan (L1.3) runs over the staged bundle; any hit means nothing is written.
An existing export is never overwritten.

    PYTHONPATH=lab uv run python -m prototype_bundle.export --commit <sha> --out <dir>
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from prototype_bundle.scan import REPO_ROOT, Hit, scan

HERE = Path(__file__).resolve().parent
EXPORT_REF = "@export"  # in allowlist.yaml: the lab repo at the commit being exported

# Never copied from the lab repo, whatever the allowlist says (CLAUDE.md's never-load list, plus the
# lab's own plans, runs and tests).
DENY_PREFIXES = (
    "truth/",
    "dataset/answer-key/",
    "dataset/evaluation/",
    "site/",
    "owm/",
    "runs/",
    "tests/",
)
DENY_GLOBS = ("docs/superpowers/plans/*lab-work*",)
DENY_NAMES = ("MANIFEST.yaml",)

USE = """\
# The port bundle

This bundle is what the prototype's builder may read of the lab (spec §11.3 and §11.4): the spec,
its Appendix A and the builder's plan; the allowlisted lab source the prototype ports, scrubbed; the
contracts it starts from; and one org's documents and exported tables as that org's content.

Nothing else from the lab is the builder's to read or ask for: no scenario ids, expected outcomes,
acceptance suite, lab tests, runs, scorers or judge prompts, and nothing about a second org.
Gate results come back as counts and mechanism notes.
"""


class BundleRefusedError(Exception):
    """The export would break the bundle's rules; nothing was written."""


@dataclass(frozen=True)
class ExportReport:
    files: int
    scrubbed_lines: int
    code_changes: list[str] = field(default_factory=list)
    scan_hits: list[Hit] = field(default_factory=list)


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout


def _denied(path: str) -> bool:
    return (
        path.startswith(DENY_PREFIXES)
        or Path(path).name in DENY_NAMES
        or any(fnmatch.fnmatchcase(path, g) for g in DENY_GLOBS)
    )


def _match(pattern: str, path: str) -> bool:
    """Segment-wise glob: `*` stays inside one segment, `**` spans any number of segments."""

    def go(ps: list[str], xs: list[str]) -> bool:
        if not ps:
            return not xs
        if ps[0] == "**":
            return any(go(ps[1:], xs[i:]) for i in range(len(xs) + 1))
        return bool(xs) and fnmatch.fnmatchcase(xs[0], ps[0]) and go(ps[1:], xs[1:])

    return go(pattern.split("/"), path.split("/"))


def _static_prefix(pattern: str) -> str:
    parts = []
    for seg in pattern.split("/"):
        if any(c in seg for c in "*?["):
            break
        parts.append(seg)
    return "/".join(parts) + "/" if parts else ""


def _collect(
    allow: Mapping[str, Any], commit: str, repo: Path
) -> tuple[dict[str, bytes], dict[str, str]]:
    files: dict[str, bytes] = {}
    shas: dict[str, str] = {}
    for entry in allow["files"]:
        name = entry["repo"]
        spec = allow["repos"][name]
        root = (repo / spec["path"]).resolve()
        is_lab = spec["ref"] == EXPORT_REF
        ref = commit if is_lab else str(spec["ref"])
        sha = _git(root, "rev-parse", f"{ref}^{{commit}}").decode().strip()
        shas[name] = sha
        if "from" in entry:
            pairs = [(str(entry["from"]), str(entry["to"]))]
            if is_lab and _denied(pairs[0][0]):
                raise BundleRefusedError(f"deny list: {pairs[0][0]} is never exported")
        else:
            pattern, exclude = str(entry["glob"]), set(entry.get("exclude", []))
            listed = _git(root, "ls-tree", "-r", "--name-only", sha).decode().splitlines()
            names = [
                n
                for n in listed
                if _match(pattern, n) and n not in exclude and not (is_lab and _denied(n))
            ]
            if not names:
                raise BundleRefusedError(f"allowlist: {pattern} matches nothing at {sha[:12]}")
            prefix = _static_prefix(pattern)
            pairs = [(n, str(entry["to"]) + n[len(prefix) :]) for n in names]
        for src, dest in pairs:
            if dest in files:
                raise BundleRefusedError(f"allowlist: two sources map to {dest}")
            files[dest] = _git(root, "show", f"{sha}:{src}")
    return files, shas


def _scrub(files: dict[str, bytes], doc: Mapping[str, Any]) -> tuple[int, list[str]]:
    lines, changes = 0, []
    for e in doc.get("replace") or []:
        path, match, count = str(e["file"]), str(e["match"]), int(e.get("count", 1))
        if path not in files:
            raise BundleRefusedError(f"scrub: {path} is not in the bundle")
        if e.get("kind") not in ("comment", "code", "doc"):
            raise BundleRefusedError(f"scrub: {path}: kind must be comment, code or doc")
        text = files[path].decode("utf-8")
        found = text.count(match)
        if found != count:
            raise BundleRefusedError(f"scrub: {path}: expected {count} match(es), found {found}")
        files[path] = text.replace(match, str(e["replace"])).encode("utf-8")
        lines += max(1, len(match.splitlines())) * count
        if e["kind"] in ("code", "doc"):  # listed in the README; a comment rewrite isn't
            changes.append(f"{path}: {e['why']}")
    return lines, changes


def _readme(shas: Mapping[str, str], allow: Mapping[str, Any], report: ExportReport) -> str:
    out = [USE, "## Source commits", ""]
    out += [
        f"- `{name}` ({allow['repos'][name]['path']}): `{sha}`"
        for name, sha in sorted(shas.items())
    ]
    out += ["", "## Changed from source", ""]
    out += [f"- {c}" for c in report.code_changes] or ["- nothing beyond comments"]
    out += [
        "",
        f"{report.scrubbed_lines} source lines were rewritten by the scrub. "
        f"`FILES.sha256` lists all {report.files} files with their hashes.",
        "",
    ]
    return "\n".join(out)


def export(
    commit: str,
    out: Path,
    *,
    scrub: Path,
    allowlist: Path,
    repo: Path = REPO_ROOT,
    scan_fn: Callable[[Path], list[Hit]] = scan,
) -> ExportReport:
    """Write the bundle for `commit` to `out`, or write nothing and say why."""
    if out.exists():
        raise BundleRefusedError(f"{out} exists; an export is never overwritten")
    allow = yaml.safe_load(allowlist.read_text())
    files, shas = _collect(allow, commit, repo)
    scrubbed, changes = _scrub(files, yaml.safe_load(scrub.read_text()) or {})
    report = ExportReport(files=len(files) + 2, scrubbed_lines=scrubbed, code_changes=changes)
    files["README.md"] = _readme(shas, allow, report).encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".bundle-", dir=out.parent))
    try:
        for rel, data in sorted(files.items()):
            p = stage / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        hits = scan_fn(stage)
        if hits:
            return ExportReport(report.files, report.scrubbed_lines, report.code_changes, hits)
        sums = [f"{hashlib.sha256(data).hexdigest()}  {rel}" for rel, data in sorted(files.items())]
        (stage / "FILES.sha256").write_text("\n".join(sums) + "\n")
        stage.rename(out)
        return report
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--scrub", type=Path, default=HERE / "scrub.yaml")
    ap.add_argument("--allowlist", type=Path, default=HERE / "allowlist.yaml")
    args = ap.parse_args(argv)
    try:
        report = export(args.commit, args.out, scrub=args.scrub, allowlist=args.allowlist)
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
        f"{len(report.code_changes)} code changes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
