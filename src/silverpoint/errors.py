"""The two errors the package raises: a spec it refuses, and a missing runtime."""

from __future__ import annotations


class SpecError(ValueError):
    """A chart, role, column, option or value the pinned catalog does not know (PY-REQ-004).

    ``kind`` is the library's error kind (``chart``, ``role``, ``prop``, ``shape``) or ``value`` for an
    option value outside the option's ``values``; the other attributes follow the kind.
    """

    def __init__(self, kind: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.kind = kind
        self.details = details
        for key, value in details.items():
            setattr(self, key, value)


class RuntimeUnavailable(RuntimeError):
    """Raised by ``to_svg`` and server-side rendering when Node 20+ is not on ``PATH`` (PY-REQ-009)."""
