"""The library's own renderers, run in Node from the vendored module build (PY-REQ-009)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from ._catalog import VENDOR
from .errors import RuntimeUnavailable, SpecError

_RUNNER = """
import * as sp from %s;
let input = '';
for await (const chunk of process.stdin) input += chunk;
const { fn, args } = JSON.parse(input);
const result = sp[fn](...args);
process.stdout.write(JSON.stringify(result));
"""

HOW = (
    "to_svg and server-side rendering run the library in Node 20+, which is not on PATH. "
    "Install Node, or use to_html(render='client'), which needs no Node and draws in the browser."
)


def node() -> str:
    """Node 20+: ``SILVERPOINT_NODE`` when set (a host's preference), otherwise ``node`` on PATH."""
    configured = os.environ.get("SILVERPOINT_NODE")
    if configured:
        if not os.path.isfile(configured) or not os.access(configured, os.X_OK):
            raise RuntimeUnavailable(f"SILVERPOINT_NODE is {configured!r}, which is not an executable file.")
        return configured
    path = shutil.which("node")
    if path is None:
        raise RuntimeUnavailable(HOW)
    return path


def call(fn: str, *args: Any, timeout: float = 60) -> Any:
    """``Silverpoint[fn](...args)`` in a Node subprocess; the arguments go in on standard input as JSON."""
    module = (VENDOR / "silverpoint-embed.full.mjs").as_uri()
    code = _RUNNER % json.dumps(module)
    proc = subprocess.run(
        [node(), "--input-type=module", "-e", code],
        input=json.dumps({"fn": fn, "args": list(args)}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"silverpoint's {fn} failed in Node: {proc.stderr.strip()}")
    result = json.loads(proc.stdout)
    if isinstance(result, dict) and result.get("ok") is False:
        error = result["error"]
        raise SpecError(
            error.get("kind", "shape"),
            error.get("message") or json.dumps(error),
            **{k: v for k, v in error.items() if k not in ("kind", "message")},
        )
    return result["value"] if isinstance(result, dict) and "value" in result else result
