"""The private scan (lab plan L1.3): finds truth-derived terms in a bundle before it leaves the lab.

The term list is built at run time from `truth/` (every id-like value in it, its people, customers,
contracts and corpus variants), the README's trap table, the register attack cases, CLAUDE.md's
reserved names and the lab plan's file name. It is never written to disk, and a `Hit` carries the
kind of term only, never the term, so a scan report can be shown or relayed without leaking what it
looked for. Given a commit, the terms come from that commit, not the working tree.

It fails closed: a file it can't decode is a hit (`unscannable`), and a term source that has moved
or emptied stops the scan (`ScanError`) rather than letting that kind go unchecked.

The org's own content may name its people, customers and requests: the builder reads it as one
org's evidence (spec §11.3). There, only the lab's own markers are looked for. The caller names
which files are org content; without that, files under `inputs/` are.

    PYTHONPATH=lab uv run python -m prototype_bundle.scan PATH [PATH ...]   # counts, never terms
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from collections.abc import Collection, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACK_CASES = "runs/2026-10-08-register-attacks/sealed/cases"
LAB_PLAN_NAMES = ("2026-10-23-prototype-lab-work", "prototype-lab-work")
# CLAUDE.md's RESERVED_TOKENS, without the org's own name, which the spec uses openly.
RESERVED_NAMES = ("acme", "blueriver", "cedar")

# Trap names that are also the spec's own design vocabulary. The spec designs for the property
# openly (§6.4), so the phrase alone carries no trap mechanics; the people, ids and figures that
# make up the trap are caught under their own kinds. Add a phrase only when a real doc needs it.
GENERIC_TRAP_NAMES = frozenset({"separation of duties"})

# The order kinds are claimed in: a term belongs to the first kind that has it.
KIND_ORDER = (
    "scenario_id",
    "request_id",
    "fact_id",
    "attack_id",
    "corpus_name",
    "person",
    "entity_name",
    "reserved_name",
    "entity_id",
    "truth_id",
    "trap_name",
    "plan_name",
)
# Kinds looked for inside the org's own content: the lab's own ids and variant names. Never the
# org's names, and never trap labels, which were named after phrases the org's documents use.
LAB_MARKER_KINDS = frozenset({"scenario_id", "fact_id", "attack_id", "corpus_name", "plan_name"})
ORG_CONTENT = "inputs/"
# Ids match in any case, and beside `_` (test_s22, S22_EXAMPLE); names match as written. Attack
# ids are the exception: the lab writes them upper case, and the service's condition ids are c1.
# Their edges still allow `_`.
CASELESS = frozenset(
    {
        "scenario_id",
        "request_id",
        "fact_id",
        "corpus_name",
        "reserved_name",
        "entity_id",
        "truth_id",
        "trap_name",
        "plan_name",
    }
)
_ID_EDGES = (r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])")
_NAME_EDGES = (r"(?<![A-Za-z0-9_])", r"(?![A-Za-z0-9_])")
_ID_TOKEN = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+\b")
_NAME_KEYS = frozenset(
    {
        "name",
        "canonical_name",
        "aliases",
        "preferred_name",
        "erp_name",
        "title",
        "guarantor",
        "legal_name",
        "display_name",
    }
)
_NAME_FILES = ("truth/entities.yaml", "truth/support.yaml", "truth/policies.yaml")


class ScanError(Exception):
    """The scan couldn't build a kind's terms, so it can't vouch for anything."""


@dataclass(frozen=True)
class Hit:
    """One line that holds a term. Carries the kind only, never the term."""

    file: str
    line: int
    term_kind: str


class _Source:
    """The lab repo's files, at a commit or in the working tree."""

    def __init__(self, repo: Path, commit: str | None) -> None:
        self.repo, self.commit = repo, commit

    def _git(self, *args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True
        ).stdout

    def names(self, folder: str) -> list[str]:
        if self.commit:
            return self._git("ls-tree", "-r", "--name-only", self.commit, "--", folder).split()
        base = self.repo / folder
        return sorted(p.relative_to(self.repo).as_posix() for p in base.rglob("*") if p.is_file())

    def text(self, rel: str) -> str:
        if self.commit:
            return self._git("show", f"{self.commit}:{rel}")
        return (self.repo / rel).read_text()


def _strings(node: Any, key: str | None = None) -> Iterator[tuple[str | None, str]]:
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _strings(v, str(k))
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v, key)
    elif isinstance(node, str):
        yield key, node


def _terms(src: _Source) -> dict[str, set[str]]:
    t: dict[str, set[str]] = {k: set() for k in KIND_ORDER}
    truth = {
        rel: yaml.safe_load(src.text(rel)) for rel in src.names("truth") if rel.endswith(".yaml")
    }
    for rel, doc in truth.items():
        if rel.startswith("truth/scenarios/"):
            sid = str(doc["id"])
            t["scenario_id"].update({sid, f"Scenario {int(sid[1:])}"})
        for _, value in _strings(doc):
            t["truth_id"].update(m for m in _ID_TOKEN.findall(value) if any(c.isdigit() for c in m))
    t["fact_id"].update(str(r["id"]) for r in truth.get("truth/facts.yaml", {}).get("facts", []))
    for section, rows in (truth.get("truth/entities.yaml") or {}).items():
        for r in rows if isinstance(rows, list) else []:
            if not isinstance(r, dict):
                continue
            if section == "employees":
                name = str(r["name"])
                t["person"].update({name, *(p for p in name.split() if len(p) > 2)})
                t["person"].update(str(a) for a in r.get("aliases", []) if len(str(a)) > 3)
                if r.get("preferred_name"):
                    t["person"].add(str(r["preferred_name"]))
            kind = "request_id" if section.endswith("_requests") else "entity_id"
            t[kind].update(str(r[k]) for k in ("id", "sku") if k in r)
    for rel in _NAME_FILES:
        for key, value in _strings(truth.get(rel)):
            if key in _NAME_KEYS and len(value) > 3:
                t["entity_name"].add(value)
    corpora = (truth.get("truth/corpora.yaml") or {}).get("corpora", {})
    t["corpus_name"].update(k for k in corpora if k != "base")
    t["reserved_name"].update(RESERVED_NAMES)
    t["trap_name"].update(_trap_names(src.text("README.md")))
    t["attack_id"].update(
        Path(n).stem
        for n in src.names(ATTACK_CASES)
        if re.fullmatch(r"C[0-9]{2}\.yaml", Path(n).name)
    )
    t["plan_name"].update(LAB_PLAN_NAMES)
    claimed: set[str] = set()
    for kind in KIND_ORDER:
        t[kind] = {w for w in t[kind] if w.casefold() not in claimed}
        claimed |= {w.casefold() for w in t[kind]}
    empty = [k for k in KIND_ORDER if not t[k]]
    if empty:
        raise ScanError(f"no terms for {', '.join(empty)}: a term source moved or emptied")
    return t


def _trap_names(readme: str) -> set[str]:
    names: set[str] = set()
    in_table = False
    for line in readme.splitlines():
        if line.startswith("### Deliberate traps"):
            in_table = True
            continue
        if in_table and line.startswith("#"):
            break
        if in_table and line.startswith("| ") and not line.startswith(("| Trap ", "|---")):
            name = line.split("|")[1].strip()
            if name and name.lower() not in GENERIC_TRAP_NAMES:
                names.add(name)
    return names


def _patterns(terms: dict[str, set[str]]) -> dict[str, re.Pattern[str]]:
    pats: dict[str, re.Pattern[str]] = {}
    for kind, words in terms.items():
        left, right = _ID_EDGES if kind in CASELESS or kind == "attack_id" else _NAME_EDGES
        alt = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
        flags = re.IGNORECASE if kind in CASELESS else 0
        pats[kind] = re.compile(f"{left}(?:{alt}){right}", flags)
    return pats


def _files(root: Path) -> Iterator[Path]:
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            yield p


def scan(
    root: Path,
    org_content: Collection[str] | None = None,
    *,
    repo: Path = REPO_ROOT,
    commit: str | None = None,
) -> list[Hit]:
    """Every line under `root` that holds a truth-derived term, as (file, line, kind).

    `org_content` names the files (relative to `root`) that are the org's own content; when None,
    files under `inputs/` are. `commit` reads the terms from that commit of `repo`."""
    pats = _patterns(_terms(_Source(repo, commit)))
    hits: list[Hit] = []
    for path in _files(root):
        rel = path.name if root.is_file() else path.relative_to(root).as_posix()
        try:
            text = path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            hits.append(Hit(file=rel, line=0, term_kind="unscannable"))
            continue
        is_org = rel.startswith(ORG_CONTENT) if org_content is None else rel in org_content
        kinds = [k for k in KIND_ORDER if not is_org or k in LAB_MARKER_KINDS]
        for n, line in enumerate(text.splitlines(), start=1):
            hits.extend(Hit(file=rel, line=n, term_kind=k) for k in kinds if pats[k].search(line))
    return hits


def _summary(hits: Iterable[Hit]) -> str:
    hits = list(hits)
    by_kind = Counter(h.term_kind for h in hits)
    lines = [f"{len(hits)} hits"] + [f"  {k}: {n}" for k, n in sorted(by_kind.items())]
    lines += [f"  {h.file}:{h.line} {h.term_kind}" for h in hits]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    hits = [h for arg in argv for h in scan(Path(arg))]
    print(_summary(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
