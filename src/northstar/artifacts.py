"""An evidence artifact and the provenance tags that make the corpus auditable."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Artifact:
    """One file of evidence.

    ``supports``  — truth keys this artifact is *authoritative* evidence for. The
                    reference oracle reasons only from these.
    ``asserts``   — fact ids (truth/facts.yaml) the artifact states outright.
    ``mentions``  — truth keys it refers to without establishing them (hearsay,
                    precedent, second-hand claims). A trap for scenario 5 and 7.
    """

    id: str
    path: str
    source_system: str
    description: str
    content: str
    supports: tuple[str, ...] = ()
    asserts: tuple[str, ...] = ()
    mentions: tuple[str, ...] = ()
