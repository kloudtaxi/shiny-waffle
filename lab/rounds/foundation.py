"""Thin helpers over the knowledge foundation's REST API, for the `kb` read tools of a round.

Everything goes through `lab/utopia/utopia.py` and `blind_reader` (the run scripts' own client).
Importing this module touches neither the network nor any credential; they are read on first use.

Every helper fails the same way, `RuntimeError("foundation error")`, with no detail: the client
raises SystemExit on any HTTP error, and its text could carry a URL or a response body.
"""

from __future__ import annotations

import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypeVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "utopia"))

import blind_reader  # noqa: E402

import utopia  # noqa: E402

PAGE = 200  # the documents route clamps `limit` to 1..200
T = TypeVar("T")


def _guarded(fn: Callable[[], T]) -> T:
    try:
        return fn()
    except (Exception, SystemExit):
        raise RuntimeError("foundation error") from None


def mint(kb: str) -> tuple[str, str]:
    """A read-only token for one KB: `(token, token_id)`. The token lives in process env only."""
    name = f"northstar-rounds-{time.strftime('%Y%m%d-%H%M%S')}"
    token, token_id = _guarded(lambda: blind_reader.mint_token(name, [kb]))
    return str(token), str(token_id)


def revoke(token_id: str) -> None:
    _guarded(lambda: blind_reader.revoke(token_id))


def mcp_url(kb: str) -> str:
    return f"{utopia.API}/kbs/{kb}/mcp"


def kb_tools(token: str, kb: str) -> list[str]:
    return _guarded(lambda: [str(t["name"]) for t in blind_reader.mcp_tools(token, kb)])


def fingerprint(kb: str) -> dict[str, Any]:
    """The base's document counts and newest update, to show it did not change during a round.

    `GET /kbs/{id}/documents` answers a `DocumentPage` (`docs`, `total`, `ready`, `done`,
    `deleted`, ...), newest `created_at` first. It is paged to the end, because an old document
    can carry the newest `updated_at`."""
    head = page = _page(kb, 0)
    docs: list[Any] = list(page["docs"])
    while page["docs"] and len(docs) < head["total"]:
        page = _page(kb, len(docs))
        docs += page["docs"]
    stamps = [str(s) for d in docs if isinstance(d, dict)
              if (s := d.get("updated_at") or d.get("created_at"))]  # fmt: skip
    return {
        "documents": head["total"], "deleted": head.get("deleted"), "ready": head.get("ready"),
        "done": head.get("done"), "latest": max(stamps, key=_when, default=None),
    }  # fmt: skip


def _page(kb: str, offset: int) -> dict[str, Any]:
    path = f"/kbs/{kb}/documents?limit={PAGE}&offset={offset}"
    page = _guarded(lambda: utopia.jcall("GET", path))
    if not (isinstance(page, dict) and isinstance(page.get("docs"), list)
            and isinstance(page.get("total"), int)):  # fmt: skip
        raise RuntimeError("foundation error")
    return page


def _when(stamp: str) -> datetime:
    """A timestamp as a time, not a string: "…00.5Z" is later than "…00Z"."""
    try:
        when = datetime.fromisoformat(re.sub(r"(\.\d{6})\d+", r"\1", stamp))
    except ValueError:
        raise RuntimeError("foundation error") from None
    return when if when.tzinfo else when.replace(tzinfo=UTC)
