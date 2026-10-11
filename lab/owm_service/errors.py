"""Errors the service raises; the HTTP layer maps each to its status (spec §3.4)."""

from __future__ import annotations

from .models import Refusal


class Refused(Exception):
    """A rule refused the request. `status` is 403, 409 or 422, whichever the rule maps to."""

    def __init__(self, status: int, refusals: list[Refusal]) -> None:
        super().__init__("; ".join(f"{r.rule}: {r.detail}" for r in refusals))
        self.status = status
        self.refusals = refusals


class NotFound(Exception):
    """An unknown id (404)."""

    def __init__(self, what: str) -> None:
        super().__init__(what)
        self.what = what


class Unauthenticated(Exception):
    """No valid session (401)."""

    def __init__(self) -> None:
        super().__init__("unauthenticated")


class CannotDecide(Exception):
    """The kernel can't decide (Jev unavailable or a kernel error); nothing is written (503)."""

    status = 503

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail
