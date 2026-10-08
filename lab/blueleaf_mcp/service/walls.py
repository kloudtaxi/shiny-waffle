"""The file wall, and the digest that proves `dataset/` is never written (spec §2.1; plan, task 3).

A blind subject reads exactly what the lab's reader arms read: `documents/*.md` and
`structured/*.csv` of its question's corpus, one level deep (D-3). Anything else is refused,
`MANIFEST.yaml` included, because it names the traps. A path is checked twice: as written, and
again after every symlink is resolved, so a link can lead neither out of the corpus nor to a file
outside the pattern.
"""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath

from service.errors import RefusedError

READABLE = {"documents": ".md", "structured": ".csv"}
REFUSAL = "that file is not one of this question's documents"


def _readable(rel: PurePosixPath) -> bool:
    return (
        len(rel.parts) == 2
        and READABLE.get(rel.parts[0]) == rel.suffix
        and not rel.name.startswith(".")
    )


def subject_path(corpus_root: Path, rel: str) -> Path:
    """The file `rel` of a question's corpus, resolved, if the subject may read it. Otherwise
    `RefusedError`, with the same sentence whatever the reason."""
    want = PurePosixPath(rel)
    if not rel or want.is_absolute() or ".." in want.parts or not _readable(want):
        raise RefusedError(REFUSAL)
    try:
        root = corpus_root.resolve(strict=True)
        got = (root / want).resolve(strict=True)
        inside = PurePosixPath(got.relative_to(root).as_posix())
    except (OSError, ValueError, RuntimeError):  # missing, outside the corpus, or a link loop
        raise RefusedError(REFUSAL) from None
    if not _readable(inside) or not got.is_file():
        raise RefusedError(REFUSAL)
    return got


def tree_digest(root: Path) -> str:
    """sha256 over every file under `root`, as sorted lines of relative path and content sha256.
    Equal digests mean the same names with the same bytes."""
    lines = sorted(
        f"{p.relative_to(root).as_posix()}\t{hashlib.sha256(p.read_bytes()).hexdigest()}\n"
        for p in root.rglob("*")
        if p.is_file()
    )
    return hashlib.sha256("".join(lines).encode()).hexdigest()
