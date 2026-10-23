"""The private scan (lab plan L1.3): finds truth-derived terms in a bundle before it leaves the lab.

The term list is built at run time from `truth/`, the README's trap table, the register attack
cases and the lab plan's file name. It is never written to disk, and a `Hit` carries the kind of
term only, never the term, so a scan report can be shown or relayed without leaking what it looked
for.

The org's own content (`inputs/`) may name its people, customers and requests: the builder reads it
as one org's evidence (spec §11.3). There, only the lab's own markers are looked for.

    PYTHONPATH=lab uv run python -m prototype_bundle.scan PATH [PATH ...]   # counts, never terms
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
ATTACK_CASES = Path("runs/2026-10-08-register-attacks/sealed/cases")
LAB_PLAN_NAMES = ("2026-10-23-prototype-lab-work", "prototype-lab-work")

# Kinds looked for inside the org's own content (inputs/): the lab's own ids. Never the org's
# names, and never trap labels, which were named after phrases the org's documents use.
LAB_MARKER_KINDS = frozenset({"scenario_id", "fact_id", "attack_id", "plan_name"})
ORG_CONTENT = "inputs/"

# Trap names that are also the spec's own design vocabulary. The spec designs for the property
# openly (§6.4), so the phrase alone carries no trap mechanics; the people, ids and figures that
# make up the trap are caught under their own kinds. Add a phrase only when a real doc needs it.
GENERIC_TRAP_NAMES = frozenset({"separation of duties"})

_EDGE_L = r"(?<![A-Za-z0-9_])"
_EDGE_R = r"(?![A-Za-z0-9_])"


@dataclass(frozen=True)
class Hit:
    """One line that holds a term. Carries the kind only, never the term."""

    file: str
    line: int
    term_kind: str


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def _records(doc: Any) -> Iterator[dict[str, Any]]:
    if isinstance(doc, dict):
        for value in doc.values():
            if isinstance(value, list):
                yield from (r for r in value if isinstance(r, dict))


def _terms(repo: Path) -> dict[str, set[str]]:
    truth = repo / "truth"
    t: dict[str, set[str]] = {
        k: set()
        for k in (
            "scenario_id",
            "request_id",
            "person",
            "fact_id",
            "entity_id",
            "entity_name",
            "trap_name",
            "attack_id",
            "plan_name",
        )
    }
    for f in sorted((truth / "scenarios").glob("*.yaml")):
        t["scenario_id"].add(str(_load(f)["id"]))  # S01..S45 only; short forms are the scrub's
    t["fact_id"].update(str(r["id"]) for r in _records(_load(truth / "facts.yaml")) if "id" in r)
    entities = _load(truth / "entities.yaml")
    for section, rows in entities.items():
        for r in rows if isinstance(rows, list) else []:
            if not isinstance(r, dict):
                continue
            kind = "request_id" if section.endswith("_requests") else "entity_id"
            for key in ("id", "sku"):
                if key in r:
                    t[kind].add(str(r[key]))
            if section == "employees":
                name = str(r["name"])
                t["person"].update({name, *name.split()})
                t["person"].update(str(a) for a in r.get("aliases", []) if len(str(a)) > 3)
            else:
                for key in ("canonical_name", "name"):
                    if key in r:
                        t["entity_name"].add(str(r[key]))
    t["trap_name"].update(_trap_names(repo / "README.md"))
    cases = repo / ATTACK_CASES
    t["attack_id"].update(p.stem for p in cases.glob("C[0-9][0-9].yaml"))
    t["plan_name"].update(LAB_PLAN_NAMES)
    return t


def _trap_names(readme: Path) -> set[str]:
    names: set[str] = set()
    in_table = False
    for line in readme.read_text().splitlines():
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
        if not words:
            continue
        alt = "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))
        flags = re.IGNORECASE if kind == "trap_name" else 0
        pats[kind] = re.compile(f"{_EDGE_L}(?:{alt}){_EDGE_R}", flags)
    return pats


def _text_files(root: Path) -> Iterator[Path]:
    if root.is_file():
        yield root
        return
    for p in sorted(root.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            yield p


def scan(root: Path, *, repo: Path = REPO_ROOT) -> list[Hit]:
    """Every line under `root` that holds a truth-derived term, as (file, line, kind)."""
    pats = _patterns(_terms(repo))
    hits: list[Hit] = []
    for path in _text_files(root):
        rel = path.name if root.is_file() else path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        kinds = LAB_MARKER_KINDS if rel.startswith(ORG_CONTENT) else pats.keys()
        for n, line in enumerate(text.splitlines(), start=1):
            for kind in sorted(kinds):
                pat = pats.get(kind)
                if pat is not None and pat.search(line):
                    hits.append(Hit(file=rel, line=n, term_kind=kind))
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
