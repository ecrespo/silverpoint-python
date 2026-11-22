"""silverpoint charts from Python: notebooks, Flask, Django and static HTML (PY-REQ-010).

No picture is made in Python (PY-Art. 1): the package builds a spec and the markup that carries it, and
the library's own standalone script — vendored, version for version — draws it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import notebook
from ._builders import *  # noqa: F403
from ._builders import __all__ as _builders_all
from ._catalog import VENDOR, host_catalog
from .chart import Chart
from .errors import RuntimeUnavailable, SpecError

__version__ = "0.11.0.post1"
SILVERPOINT_VERSION: str = host_catalog()["version"]


def static_path() -> Path:
    """The folder holding the vendored ``silverpoint-embed.full.js`` (and its module build)."""
    return VENDOR


def __getattr__(name: str) -> Any:
    if name == "catalog":
        return host_catalog()
    raise AttributeError(f"module 'silverpoint' has no attribute {name!r}")


__all__ = [
    "SILVERPOINT_VERSION",
    "Chart",
    "RuntimeUnavailable",
    "SpecError",
    "__version__",
    "catalog",  # noqa: F405 - resolved by the module __getattr__
    "notebook",
    "static_path",
    *_builders_all,
]
