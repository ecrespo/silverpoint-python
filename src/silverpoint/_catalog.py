"""The pinned host catalog (silverpoint Data Model §2.39), read once from the vendored file."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

VENDOR = Path(__file__).resolve().parent / "_vendor"


@lru_cache(maxsize=1)
def host_catalog() -> dict[str, Any]:
    return json.loads((VENDOR / "host-catalog.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def charts() -> dict[str, dict[str, Any]]:
    return {chart["slug"]: chart for chart in host_catalog()["charts"]}


def snake(name: str) -> str:
    """``connectNulls`` → ``connect_nulls``; ``footerLeft`` → ``footer_left``."""
    out = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def options_of(chart: dict[str, Any]) -> list[dict[str, Any]]:
    """The chart's own options, then the common ones it does not redeclare."""
    own = list(chart["options"])
    names = {o["name"] for o in own}
    return own + [o for o in host_catalog()["common"] if o["name"] not in names]
