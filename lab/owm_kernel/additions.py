"""Kernel additions for the OWM service (B-06, `docs/superpowers/plans/2026-10-11-owm-service.md`,
Task 1; contract v1.2 §12.1 items 4 and 5).

New functions only. Nothing here changes a record the kernel returns: the service calls them beside
`governed.decide`, so every record the lab's harnesses produce stays byte-identical.
- `capture` and `judgment_about`: what each judgment is about (a document, a role, or the
  decision's subject), recorded beside the judgment by `kernel.judge` and never sent to Jev;
- `flag_items`: each flag string as `{code, text, routes}`, by the contract's §5.5 table.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

import kernel


@dataclass
class Capture:
    """What each judgment made during a capture is about, keyed by the judgment's `id()`."""

    about: dict[int, str | None] = field(default_factory=dict)


@contextmanager
def capture(subject: str | None = None) -> Iterator[Capture]:
    """Record what each judgment is about while the block runs. `subject` (the request id or the
    ticket) is what a judgment is about when it reads neither a document nor a role."""
    cap = Capture()
    judged = kernel.JUDGED.set(cap.about)
    subj = kernel.SUBJECT.set(subject)
    read = kernel.LAST_READ.set(None)  # nothing read before the capture counts
    try:
        yield cap
    finally:
        kernel.LAST_READ.reset(read)
        kernel.SUBJECT.reset(subj)
        kernel.JUDGED.reset(judged)


def judgment_about(record: dict[str, Any], cap: Capture) -> list[str | None]:
    """One entry per `record["judgments"]` item, in order. `record` must be the one the kernel
    returned inside the capture (a copy's judgments are other objects, and come out as None)."""
    return [cap.about.get(id(j)) for j in record.get("judgments") or []]


# the contract's §5.5 table, in order, first match wins: (regex, code, when the flag routes).
# Rules: "always", "never", "routed" (if the decision routed), "route_mode" (if on_mismatch: route)
FLAG_CODES: tuple[tuple[str, str, str], ...] = (
    (r"^routed:", "routed", "always"),
    (r"^withheld:", "withheld", "routed"),
    (r"^incident", "incident", "never"),
    (r"^conflict: (?:policies|registered [A-Z]|exceptions)", "conflict", "never"),
    (r"^conflict:|; terms not confirmed", "conflict", "always"),
    (r"^tamper signs in", "tamper", "always"),
    (r"document on file is (?:mismatch|missing) against registered version", "mismatch",
     "route_mode"),
    (r"; set aside", "set_aside", "never"),
    (r"not on file", "not_on_file", "routed"),
    # SLA: word-bounded prefixes, so sla.yaml's "cannot decide restoration: …" counts (ruling R9)
    (r"^cannot decide\b", "cannot_decide", "routed"),
    (r"^out of scope\b", "out_of_scope", "routed"),
    (r"^no claim yet\b", "note", "routed"),
)  # fmt: skip
OTHER = ("note", "never")


def flag_items(flags: list[str], *, route_mode: bool, routed: bool) -> list[dict[str, Any]]:
    """Each flag as `{code, text, routes}`, in order, with `text` the flag string unchanged.
    `route_mode`: the procedure routes on a mismatch; `routed`: the decision went to route_to."""
    when = {"always": True, "never": False, "routed": routed, "route_mode": route_mode}
    out = []
    for text in flags:
        code, rule = next(((c, r) for p, c, r in FLAG_CODES if re.search(p, text)), OTHER)
        out.append({"code": code, "text": text, "routes": when[rule]})
    return out
