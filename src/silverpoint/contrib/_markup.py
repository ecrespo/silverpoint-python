"""What the Flask globals and the Django tags write: the same markup, with no inline script."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .. import html
from .._catalog import VENDOR

SCRIPT = "silverpoint-embed.full.js"


def integrity() -> str:
    return json.loads((VENDOR / "integrity.json").read_text(encoding="utf-8"))[SCRIPT]


def script(url: str) -> str:
    return html.script_tag(url, integrity())


def chart(chart_or_spec: Any) -> str:
    spec = chart_or_spec.spec if hasattr(chart_or_spec, "spec") else chart_or_spec
    if not isinstance(spec, Mapping) or "chart" not in spec:
        raise TypeError("silverpoint_chart takes a Chart or a spec dict with a `chart` key")
    return html.element(spec)
