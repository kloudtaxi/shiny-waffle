"""Observe a run's questions and the evidence handed to the reader."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from preflight.config import InputsConfig

HEADER = ["id", "corpus", "process", "question"]
_RECORD = re.compile(r"\{[^{}]*\}")


@dataclass(frozen=True)
class Question:
    """One row of the questions file."""

    id: str
    corpus: str
    text: str


@dataclass(frozen=True)
class InputsObservation:
    """What the questions file and the evidence trees hold."""

    questions_sha256: str
    header_ok: bool
    questions: list[Question]
    corpus_text: dict[str, str]
    tree_hash: dict[str, str]
    # Per question, in question order: the ids its text names, and those it supplies itself.
    ids: list[list[str]] = field(default_factory=list)
    supplied: list[dict[str, str]] = field(default_factory=list)


def find_ids(text: str, patterns: list[str]) -> list[str]:
    """Ids matched by any pattern, each once, in order of first appearance."""
    hits: list[tuple[int, str]] = []
    for p in patterns:
        hits.extend((m.start(), m.group(0)) for m in re.finditer(p, text))
    seen: list[str] = []
    for _, ident in sorted(hits):
        if ident not in seen:
            seen.append(ident)
    return seen


def appears(ident: str, text: str) -> bool:
    """Whether `ident` occurs in `text` as a whole token."""
    return (
        re.search(r"(?<![A-Za-z0-9-])" + re.escape(ident) + r"(?![A-Za-z0-9-])", text) is not None
    )


def supplied_ids(text: str, keys: list[str]) -> dict[str, str]:
    """Ids the question supplies itself: string values of `keys` in inline JSON records."""
    out: dict[str, str] = {}
    for m in _RECORD.finditer(text):
        try:
            rec = json.loads(m.group(0))
        except ValueError:
            continue
        if not isinstance(rec, dict):
            continue
        for k in keys:
            v = rec.get(k)
            if isinstance(v, str):
                out[v] = k
    return out


def _files(paths: list[Path]) -> list[Path]:
    found: dict[Path, None] = {}
    for p in paths:
        if p.is_file():
            cands = [p]
        else:
            cands = [f for f in p.rglob("*") if f.is_file()]
        for f in cands:
            rel = f.relative_to(p) if p.is_dir() else Path(f.name)
            if f.name == "MANIFEST.yaml" or any(part.startswith(".") for part in rel.parts):
                continue
            found[f] = None
    return sorted(found)


def _rel(f: Path, repo: Path) -> str:
    try:
        return f.relative_to(repo).as_posix()
    except ValueError:
        return f.as_posix()


def evidence_tree_hash(paths: list[Path], repo: Path) -> str:
    """sha256 over the sorted `relpath\\tsha256` lines of every evidence file."""
    lines = sorted(
        f"{_rel(f, repo)}\t{hashlib.sha256(f.read_bytes()).hexdigest()}\n" for f in _files(paths)
    )
    return hashlib.sha256("".join(lines).encode()).hexdigest()


def observe_inputs(cfg: InputsConfig, run: Path, repo: Path) -> InputsObservation:
    """Read the questions file and every configured evidence tree."""
    raw = (run / cfg.questions).read_bytes()
    lines = raw.decode("utf-8", errors="replace").splitlines()
    header_ok = bool(lines) and lines[0].split("\t") == HEADER
    questions: list[Question] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t", 3)
        if len(parts) < 4:
            parts += [""] * (4 - len(parts))
        questions.append(Question(id=parts[0], corpus=parts[1], text=parts[3]))
    corpus_text: dict[str, str] = {}
    tree_hash: dict[str, str] = {}
    for corpus, rels in cfg.evidence.items():
        paths = [repo / r for r in rels]
        corpus_text[corpus] = "\n".join(
            f.read_bytes().decode("utf-8", errors="replace") for f in _files(paths)
        )
        tree_hash[corpus] = evidence_tree_hash(paths, repo)
    return InputsObservation(
        questions_sha256=hashlib.sha256(raw).hexdigest(),
        header_ok=header_ok,
        questions=questions,
        corpus_text=corpus_text,
        tree_hash=tree_hash,
        ids=[find_ids(q.text, cfg.id_patterns) for q in questions],
        supplied=[supplied_ids(q.text, cfg.supplied_keys) for q in questions],
    )
