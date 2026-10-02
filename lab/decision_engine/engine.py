"""A port for typed-decision engines (Choice, Score, Noul over a state): adapters and replay.

The lab reaches TypeSafe's Jev through this port. Engines can then be swapped without touching
the experiment: laya serves the same wire format. Every exchange is recorded, and scoring can
replay the recording instead of calling the engine again.

    from engine import Recorder, TypeSafe
    eng = Recorder(TypeSafe(model="jev-1.13.0"), run_dir / "engine-calls.jsonl")
    reply = eng.ask(state, {"basis": {"type": "choice", "instructions": ..., "criteria": {...}}})
    reply["answers"]["basis"]["choice"], reply["answers"]["basis"]["confidence"]

The API key is read from `TYPESAFE_API_KEY`, or from the file named by `TYPESAFE_API_KEY_FILE`
(keep it in `_owm-local/`, which is gitignored). It is never logged or recorded. Standard library
only.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Protocol

Json = dict[str, Any]


class Engine(Protocol):
    model: str

    def ask(self, state: Any, questions: Json) -> Json: ...


class HttpEngine:
    """POST {base_url}/v1/systemone, TypeSafe's wire format (laya serves the same one)."""

    def __init__(self, base_url: str, model: str, api_key: str | None, timeout: float = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._key = api_key
        self.timeout = timeout

    def ask(self, state: Any, questions: Json) -> Json:
        body = json.dumps({"model": self.model, "state": state, "questions": questions}).encode()
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        for attempt in range(6):
            req = urllib.request.Request(
                f"{self.base_url}/v1/systemone", data=body, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    reply: Json = json.loads(resp.read())
                    return reply
            except urllib.error.HTTPError as e:
                if e.code in (429, 529) and attempt < 5:
                    time.sleep(min(2**attempt, 30))
                    continue
                detail = e.read().decode(errors="replace")[:500]
                raise RuntimeError(f"engine HTTP {e.code}: {detail}") from None
        raise RuntimeError("engine: still rate limited after 6 attempts")


def _key_from_env() -> str:
    key = os.environ.get("TYPESAFE_API_KEY")
    path = os.environ.get("TYPESAFE_API_KEY_FILE")
    if not key and path:
        key = Path(path).expanduser().read_text().strip()
    if not key:
        raise RuntimeError("set TYPESAFE_API_KEY or TYPESAFE_API_KEY_FILE")
    return key


def TypeSafe(model: str = "jev-1.13.0") -> HttpEngine:  # noqa: N802 (reads as a constructor)
    """TypeSafe's hosted Jev. Pin a version: aliases like jev-latest move."""
    return HttpEngine("https://api.typesafe.ai", model, _key_from_env())


def Laya(base_url: str = "http://127.0.0.1:8000", model: str = "laya") -> HttpEngine:  # noqa: N802
    """A local laya server (Jev's wire format). Not used without the user's OK."""
    return HttpEngine(base_url, model, None)


def request_hash(model: str, state: Any, questions: Json) -> str:
    canon = json.dumps({"model": model, "state": state, "questions": questions}, sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


class Recorder:
    """Wraps an engine. Every call is appended to a JSONL file, and an identical request is
    answered from the file rather than sent again, so a re-run is free and reproducible."""

    def __init__(self, engine: Engine, path: Path) -> None:
        self.engine, self.path, self.model = engine, path, engine.model
        self._seen: dict[str, Json] = {}
        if path.exists():
            for line in path.read_text().splitlines():
                rec = json.loads(line)
                self._seen[rec["hash"]] = rec["response"]

    def ask(self, state: Any, questions: Json) -> Json:
        h = request_hash(self.model, state, questions)
        if h in self._seen:
            return self._seen[h]
        t0 = time.perf_counter()
        response = self.engine.ask(state, questions)
        ms = round((time.perf_counter() - t0) * 1000)
        rec = {"hash": h, "model": self.model, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "latency_ms": ms, "request": {"state": state, "questions": questions},
               "response": response}  # fmt: skip
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._seen[h] = response
        return response


class Replay:
    """Serves recorded responses only. Raises on any request that was never recorded."""

    def __init__(self, path: Path, model: str) -> None:
        self.model = model
        self._seen = {
            json.loads(line)["hash"]: json.loads(line)["response"]
            for line in path.read_text().splitlines()
        }

    def ask(self, state: Any, questions: Json) -> Json:
        h = request_hash(self.model, state, questions)
        if h not in self._seen:
            raise KeyError(f"not recorded: {h[:12]}")
        return self._seen[h]
