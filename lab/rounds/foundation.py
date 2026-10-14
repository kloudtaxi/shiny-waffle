"""Thin helpers over the knowledge foundation's REST API, for the `kb` read tools of a round.

Everything goes through `lab/utopia/utopia.py` and `blind_reader` (the run scripts' own client).
Importing this module touches neither the network nor any credential; they are read on first use.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "utopia"))

import blind_reader  # noqa: E402

import utopia  # noqa: E402


def mint(kb: str) -> tuple[str, str]:
    """A read-only token for one KB: `(token, token_id)`. The token lives in process env only."""
    token, token_id = blind_reader.mint_token(
        f"northstar-rounds-{time.strftime('%Y%m%d-%H%M%S')}", [kb]
    )
    return str(token), str(token_id)


def revoke(token_id: str) -> None:
    blind_reader.revoke(token_id)


def mcp_url(kb: str) -> str:
    return f"{utopia.API}/kbs/{kb}/mcp"


def kb_tools(token: str, kb: str) -> list[str]:
    return [str(t["name"]) for t in blind_reader.mcp_tools(token, kb)]


def fingerprint(kb: str) -> dict[str, Any]:
    """Document count and the newest timestamp, to show the KB did not change between rounds."""
    resp = utopia.jcall("GET", f"/kbs/{kb}/documents")
    if isinstance(resp, dict):
        docs = resp.get("items") or resp.get("documents") or []
    else:
        docs = resp
    stamps = [str(d.get("updated_at") or d.get("created_at") or "") for d in docs]
    return {"documents": len(docs), "latest": max(stamps, default=None)}
