"""The service's errors. Each message is one plain sentence (spec §7); the servers turn a
`ServiceError` into an MCP tool error with that sentence, and keep running."""

from __future__ import annotations


class ServiceError(Exception):
    """A failure the user can act on, stated in one plain sentence."""


class UnknownSandboxError(ServiceError):
    """No sandbox has that name."""


class UnknownFileError(ServiceError):
    """The file isn't in the sandbox, or an edit's text wasn't found in it."""


class AmbiguousEditError(ServiceError):
    """An edit's text matches more than once, so the edit can't tell which to change."""


class InvalidSpecError(ServiceError):
    """A procedure spec failed validation; the message names the line."""


class SealedError(ServiceError):
    """A subject session is open, so the experimenter's tools are off until it ends."""


class JevCapError(ServiceError):
    """The live Jev cap for this session is reached. The message contains "live Jev cap", which
    the admission gate reads (plan, task 9)."""


class SealMismatchError(ServiceError):
    """An attack set's files no longer match its seal."""


class RefusedError(ServiceError):
    """A wall refused the request: a file outside the question's documents, or output that would
    have carried the TypeSafe key."""


class NoSessionError(ServiceError):
    """No subject session is open."""
