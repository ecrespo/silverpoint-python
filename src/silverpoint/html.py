"""Markup that carries a spec (PY-REQ-006, PY-REQ-014): ``JSON.stringify`` in Python, the library's
escapes for a script context, and the documented ``renderToHTML`` envelope (silverpoint API §1.5)."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from decimal import Decimal
from typing import Any

from ._catalog import VENDOR

_SCRIPT_ESCAPES = {"<": "\\u003c", ">": "\\u003e", "&": "\\u0026", " ": "\\u2028", " ": "\\u2029"}
_HTML_ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}
_STRING = json.JSONEncoder(ensure_ascii=False).encode


def _number(value: float) -> str:
    """``String(number)`` / ``JSON.stringify(number)``: shortest round-trip digits, JS exponent rules."""
    if not math.isfinite(value):
        return "null"
    if value == 0:
        return "0"
    sign, raw, exp = Decimal(repr(value)).as_tuple()
    digits = "".join(map(str, raw)).lstrip("0")
    stripped = digits.rstrip("0")
    exp += len(digits) - len(stripped)
    digits, sign = stripped, "-" if sign else ""
    # ECMAScript Number::toString: k significant digits, the value is 0.digits × 10^n.
    k = len(digits)
    n = k + int(exp)
    if k <= n <= 21:
        return sign + digits + "0" * (n - k)
    if 0 < n <= 21:
        return sign + digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * (-n) + digits
    e = n - 1
    body = digits if k == 1 else digits[0] + "." + digits[1:]
    return f"{sign}{body}e{'+' if e > 0 else '-'}{abs(e)}"


def js_json(value: Any) -> str:
    """``JSON.stringify(value)`` with no spacing, keys in insertion order."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value) if abs(value) < 10**21 else _number(float(value))
    if isinstance(value, float):
        return _number(value)
    if isinstance(value, str):
        return _STRING(value)
    if isinstance(value, Mapping):
        return "{" + ",".join(f"{_STRING(str(k))}:{js_json(v)}" for k, v in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(js_json(v) for v in value) + "]"
    raise TypeError(f"{type(value).__name__} is not JSON")


def escape_json_for_script(value: Any) -> str:
    """JSON safe inside ``<script type="application/json">``: ``<``, ``>``, ``&``, U+2028, U+2029 as ``\\uXXXX``."""
    return re.sub("[<>&  ]", lambda m: _SCRIPT_ESCAPES[m.group(0)], js_json(value))


def escape_html(value: str) -> str:
    return re.sub('[&<>"]', lambda m: _HTML_ESCAPES[m.group(0)], value)


def escape_script_text(code: str) -> str:
    """A script's own text, with every ``</script`` broken so the element cannot close early."""
    return re.sub(r"</(script)", r"<\\/\1", code, flags=re.IGNORECASE)


def script_text() -> str:
    return (VENDOR / "silverpoint-embed.full.js").read_text(encoding="utf-8")


def embed_box(spec: Mapping[str, Any], inner: str = "") -> str:
    """The ``data-sp-embed`` box the standalone script mounts on load."""
    return f'<div data-sp-embed><script type="application/json">{escape_json_for_script(spec)}</script>{inner}</div>'


def element(spec: Mapping[str, Any]) -> str:
    """``<silverpoint-chart>`` with the spec in a JSON child: no inline script, upgraded whenever inserted."""
    return f'<silverpoint-chart><script type="application/json">{escape_json_for_script(spec)}</script></silverpoint-chart>'


def script_tag(script: str, integrity: str | None = None) -> str:
    """``inline`` → the vendored script inlined; ``none`` → nothing; any other string → ``src``."""
    if script == "none":
        return ""
    if script == "inline":
        return f"<script>{escape_script_text(script_text())}</script>"
    extra = f' integrity="{escape_html(integrity)}" crossorigin="anonymous"' if integrity else ""
    return f'<script src="{escape_html(script)}"{extra}></script>'


def document(body: str, *, title: str, lang: str = "en", script: str = "") -> str:
    """The envelope ``renderToHTML`` writes around its body."""
    return (
        f'<!doctype html><html lang="{escape_html(lang)}"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape_html(title)}</title>'
        f"</head><body>{body}{script}</body></html>"
    )
