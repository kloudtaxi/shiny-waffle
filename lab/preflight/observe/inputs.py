"""Observe a run's questions and the evidence handed to the reader."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from preflight.config import InputsConfig


@dataclass(frozen=True)
class Question:
    """One row of the questions file: the configured id, corpus and question columns."""

    id: str
    corpus: str
    text: str


@dataclass(frozen=True)
class InputsObservation:
    """What the questions file and the evidence trees hold."""

    questions_sha256: str
    header: list[str]  # the file's header; rows are read only when it has every configured column
    questions: list[Question]
    corpus_text: dict[str, str]
    tree_hash: dict[str, str]
    # Per question, in question order: the ids its text names, and those it supplies itself.
    ids: list[list[str]] = field(default_factory=list)
    supplied: list[dict[str, str]] = field(default_factory=list)
    file_counts: dict[str, int] = field(default_factory=dict)


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
    dec = json.JSONDecoder()
    pos = text.find("{")
    while pos != -1:
        try:
            rec, end = dec.raw_decode(text, pos)
        except ValueError:
            pos = text.find("{", pos + 1)
            continue
        if isinstance(rec, dict):
            for k in keys:
                v = rec.get(k)
                if isinstance(v, str):
                    out[v] = k
        pos = text.find("{", end)
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
    header = lines[0].split("\t") if lines else []
    cols = cfg.columns
    questions: list[Question] = []
    if all(c in header for c in cols.values()):
        for line in lines[1:]:
            if not line.strip():
                continue
            # Only the last column may hold tabs: it takes the rest of the line.
            parts = line.split("\t", len(header) - 1)
            parts += [""] * (len(header) - len(parts))
            row = dict(zip(header, parts, strict=True))
            questions.append(
                Question(id=row[cols["id"]], corpus=row[cols["corpus"]], text=row[cols["question"]])
            )
    corpus_text: dict[str, str] = {}
    tree_hash: dict[str, str] = {}
    file_counts: dict[str, int] = {}
    for corpus, rels in cfg.evidence.items():
        paths = [repo / r for r in rels]
        file_counts[corpus] = len(_files(paths))
        corpus_text[corpus] = "\n".join(
            f.read_bytes().decode("utf-8", errors="replace") for f in _files(paths)
        )
        tree_hash[corpus] = evidence_tree_hash(paths, repo)
    return InputsObservation(
        questions_sha256=hashlib.sha256(raw).hexdigest(),
        header=header,
        questions=questions,
        corpus_text=corpus_text,
        tree_hash=tree_hash,
        ids=[find_ids(q.text, cfg.id_patterns) for q in questions],
        supplied=[supplied_ids(q.text, cfg.supplied_keys) for q in questions],
        file_counts=file_counts,
    )
