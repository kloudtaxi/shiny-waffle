"""HTTP access to a foundation that serves the contract (v0.2), reads only.

Two ways in, one interface:
- `bearer`: a foundation that takes `Authorization: Bearer <token>` (B-20). The token is read from a
  file and kept in memory.
- `adapter`: web-next's adapter over today's foundation. It signs in to web-next as a BlueLeaf
  person (`POST /api/v1/auth/login {"email"}`) and sends the session cookie.

An HTTP error is an answer, not an exception: `request` returns its status and body, so a tool can
pass the contract's `Problem` to the reader. Only an unreachable foundation raises, and its message
never carries a URL, a token or a cookie.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any

PREFIX = "/api/knowledge/v1"
TIMEOUT = 300


class UnreachableError(Exception):
    """The foundation didn't answer. Deliberately without detail."""


@dataclass
class Answer:
    status: int
    body: Any  # parsed JSON, or the text when it isn't JSON


@dataclass
class Contract:
    root: str  # the base URL, without the contract's prefix
    headers: dict[str, str] = field(default_factory=dict)
    opener: urllib.request.OpenerDirector = field(default_factory=urllib.request.build_opener)

    def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> Answer:
        status, raw = self.raw(method, path, params, body)
        return Answer(status, _parse(raw))

    def raw(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        body: Mapping[str, Any] | None = None,
    ) -> tuple[int, bytes]:
        """The status and the body's bytes, unparsed: a version's text (K7) is counted in bytes."""
        query = urllib.parse.urlencode(
            {k: v for k, v in (params or {}).items() if v is not None and v != ""}
        )
        url = self.root.rstrip("/") + PREFIX + path + (f"?{query}" if query else "")
        headers = dict(self.headers)
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["content-type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=TIMEOUT) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            raise UnreachableError("the foundation didn't answer") from None

    def pages(self, path: str, params: Mapping[str, Any] | None = None) -> list[Any]:
        """Every item of a paged list (`items`, `next_cursor`). Raises on an HTTP error."""
        out: list[Any] = []
        cursor = None
        while True:
            a = self.request("GET", path, {**(params or {}), "cursor": cursor})
            if a.status != 200 or not isinstance(a.body, dict):
                raise RuntimeError(f"GET {path} answered {a.status}")
            out.extend(a.body.get("items") or [])
            cursor = a.body.get("next_cursor")
            if not cursor:
                return out


def _parse(raw: bytes) -> Any:
    text = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def bearer(root: str, token_file: Path) -> Contract:
    token = token_file.read_text().strip()
    if not token:
        raise ValueError("the token file is empty")
    return Contract(root, {"Authorization": f"Bearer {token}"})


def adapter(app_url: str, person: str) -> Contract:
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    login = urllib.request.Request(
        app_url.rstrip("/") + "/api/v1/auth/login",
        data=json.dumps({"email": person}).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(login, timeout=60) as r:
            r.read()
    except urllib.error.HTTPError as e:
        raise PermissionError(f"web-next refused the sign-in ({e.code})") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        raise UnreachableError("web-next didn't answer") from None
    return Contract(app_url, {}, opener)
