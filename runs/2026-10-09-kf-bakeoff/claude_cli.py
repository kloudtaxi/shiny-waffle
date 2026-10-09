"""One model for every pipeline: Claude (Haiku 4.5 by default) through the `claude` CLI.

Every call runs blind (a fresh temporary directory outside the repo, no tools, no MCP, no session
persistence), is cached by sha256(model, system, prompt) in `calls.jsonl` so a re-run replays
without spend, and records its cost. Adapters wrap `complete()` for langextract and Semantica.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
CALLS = HERE / "calls.jsonl"
MODEL = os.environ.get("BAKEOFF_MODEL", "claude-haiku-4-5-20251001")
SYSTEM = (
    "You extract structured facts from documents exactly as instructed. Return only what "
    "the instructions ask for."
)
_lock = threading.Lock()
_cache: dict[str, dict[str, Any]] | None = None


def _load() -> dict[str, dict[str, Any]]:
    global _cache
    if _cache is None:
        _cache = {}
        if CALLS.exists():
            for line in CALLS.read_text().splitlines():
                rec = json.loads(line)
                _cache[rec["key"]] = rec
    return _cache


def key(model: str, system: str, prompt: str) -> str:
    return hashlib.sha256(json.dumps([model, system, prompt]).encode()).hexdigest()


def complete(prompt: str, system: str = SYSTEM, model: str = MODEL, tag: str = "") -> str:
    k = key(model, system, prompt)
    with _lock:
        hit = _load().get(k)
    if hit is not None:
        return str(hit["text"])
    blind = Path(tempfile.mkdtemp(prefix="northstar-blind-"))
    if blind.resolve().is_relative_to(LAB):
        raise RuntimeError(f"blind directory {blind} is inside the repo")
    cmd = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--system-prompt",
        system,
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers": {}}',
        "--tools",
        "",
        "--setting-sources",
        "project",
        "--no-session-persistence",
        "--max-turns",
        "2",
    ]
    try:
        proc = subprocess.run(cmd, cwd=blind, capture_output=True, text=True, timeout=600)
    finally:
        shutil.rmtree(blind, ignore_errors=True)
    res = json.loads(proc.stdout) if proc.stdout.strip() else {}
    text = str(res.get("result") or "")
    rec = {
        "key": k,
        "tag": tag,
        "model": model,
        "text": text,
        "usd": float(res.get("total_cost_usd") or 0),
        "error": bool(res.get("is_error")),
    }
    with _lock:
        _load()[k] = rec
        with CALLS.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    return text


def spend(tag_prefix: str = "") -> float:
    return sum(r["usd"] for r in _load().values() if str(r.get("tag", "")).startswith(tag_prefix))
