"""Guard 3: before any reader batch, check the adapter against today's foundation's own answers.

    uv run python lab/exam/parity.py --run runs/<exam> --app http://127.0.0.1:3200 \
        --person sarah.chen@northstar.example

The reference check (2026-10-16) covered facts and identity. What's new since then is the adapter's
search (K10, glowing-garbanzo 320cb83), so this compares it with today's own search
(`POST /api/v1/kbs/:id/search`) on each of the three fresh bases:
- **The queries** are every document's file name, with `_` as spaces and no extension. They come
  from the corpus's own file list, the same for every base, and are chosen by no one.
- **A hit matches** when the adapter's passage is in a chunk's document and has its words
  (whitespace aside), among today's results for the same query. A CSV chunk is today's rendered
  table and its passage the raw row, so every cell of the row must be in the chunk. Today's chunks
  that make no passage
  are dropped by design (K0's K10 note). They're counted. Every adapter hit must match a chunk;
  the rank agreement is reported, not required, since today's order varies where scores tie.
- **An empty answer isn't a pass:** every query today answers must get at least one adapter hit
  (seen 2026-10-17: the adapter answered 200 with no hits on every query, and the first version of
  this check passed it).
- **Also:** K2 lists as many documents as today's own documents route does.

Prints and writes `parity.json` in the run folder: counts only, no text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

LAB = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(LAB / "lab")]

from contract_reader.client import adapter  # noqa: E402

VIEWER = LAB / "_owm-local/exam-1526-viewer.json"


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


class Today:
    def __init__(self) -> None:
        creds = json.loads(VIEWER.read_text())
        self.base = creds["base"].rstrip("/") + "/api/v1"
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        self.call("POST", "/auth/login", {"email": creds["email"], "password": creds["password"]})

    def call(self, method: str, path: str, body: Any = None) -> Any:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            self.base + path, data=data, method=method, headers={"content-type": "application/json"}
        )
        with self.opener.open(req, timeout=300) as r:
            text = r.read().decode()
        return json.loads(text) if text else None


def queries(filenames: list[str]) -> list[str]:
    return sorted(
        {re.sub(r"\.(md|csv)$", "", f.rsplit("/", 1)[-1]).replace("_", " ") for f in filenames}
    )


def same(chunk: dict[str, Any], passage: dict[str, Any]) -> bool:
    """A passage is its chunk: the same document, and the same words. A CSV's chunk is today's
    rendered table and its passage the raw row, so there every cell of the row must be in the
    chunk."""
    if passage.get("doc_id") != chunk.get("document_id"):
        return False
    a, b = _ws(chunk.get("text", "")), _ws(passage.get("text", ""))
    if a and b and (a in b or b in a):
        return True
    cells = [c.strip().strip('"') for c in re.split(r"[,\n]", passage.get("text", "")) if c.strip()]
    return bool(cells) and all(c in a for c in cells)


def compare(
    today_hits: list[dict[str, Any]], adapter_hits: list[dict[str, Any]], limit: int
) -> dict[str, int]:
    """Each adapter hit against today's chunks for the same query, as a set. Today's own order
    isn't stable where scores tie (seen 2026-10-17: one query's order changed between three
    identical calls), so rank agreement is counted, not required, and today is read twice as deep
    as the adapter, so a hit a tie pushed past the cut-off still finds its chunk. `dropped` is
    today's top `limit` chunks that no hit matched."""
    used: set[int] = set()
    matched = in_order = 0
    for rank, hit in enumerate(adapter_hits):
        k = next(
            (k for k, ch in enumerate(today_hits) if k not in used and same(ch, hit["passage"])),
            None,
        )
        if k is None:
            continue
        used.add(k)
        matched += 1
        in_order += k == rank
    return {
        "today": min(len(today_hits), limit),
        "adapter": len(adapter_hits),
        "matched": matched,
        "same_rank": in_order,
        "dropped": sum(1 for k in range(min(len(today_hits), limit)) if k not in used),
        "unmatched_adapter_hits": len(adapter_hits) - matched,
        "empty": int(bool(today_hits) and not adapter_hits),
    }


def main() -> None:
    ap = argparse.ArgumentParser(prog="exam-parity")
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--app", required=True)
    ap.add_argument("--person", required=True)
    ap.add_argument("--limit", type=int, default=10)
    a = ap.parse_args()
    bases = json.loads((a.run / "today-bases.json").read_text())["kbs"]
    today, c = Today(), adapter(a.app, a.person)
    report: dict[str, Any] = {}
    for corpus, kb in bases.items():
        native = today.call("GET", f"/kbs/{kb}/documents")["total"]
        k2 = c.pages(f"/kbs/{kb}/documents", {"limit": 100})
        per_query: list[dict[str, Any]] = []
        for q in queries([d["filename"] for d in k2]):
            t = today.call("POST", f"/kbs/{kb}/search", {"q": q, "top_k": 2 * a.limit})
            ad = c.request("POST", f"/kbs/{kb}/search", body={"q": q, "limit": a.limit})
            hits = ad.body.get("hits", []) if ad.status == 200 and isinstance(ad.body, dict) else []
            per_query.append(
                {"q": q, "status": ad.status, **compare(t.get("results", []), hits, a.limit)}
            )
        keys = (
            "today",
            "adapter",
            "matched",
            "same_rank",
            "dropped",
            "unmatched_adapter_hits",
            "empty",
        )
        totals = {k: sum(r[k] for r in per_query) for k in keys}
        report[corpus] = {
            "documents": {"today": native, "k2": len(k2)},
            "queries": len(per_query),
            "search": totals,
            "non_200": sum(r["status"] != 200 for r in per_query),
            "pass": totals["unmatched_adapter_hits"] == 0
            and totals["empty"] == 0
            and all(r["status"] == 200 for r in per_query)
            and native == len(k2),
        }
    (a.run / "parity.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
