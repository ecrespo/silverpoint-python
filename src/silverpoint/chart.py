"""``Chart``: a spec and the ways out of Python — HTML, SVG, notebooks (PY-REQ-001, -006, -007, -009)."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from typing import Any

from . import html, notebook, svg
from ._catalog import charts
from .spec import APPEARANCE, build_spec

_DEFAULT_SIZE = (640, 360)


class Chart:
    """One chart: ``Chart("bar-chart", df, roles={"x": "team", "value": "wins"}, options={...})``.

    ``spec`` is the ``ChartSpec`` (silverpoint Data Model §2.38) as a dict; it is built and validated
    against the pinned host catalog when the chart is made, so an error is raised before any HTML.
    """

    def __init__(
        self,
        chart: str,
        data: Any = None,
        *,
        roles: Mapping[str, str | Sequence[str]] | None = None,
        options: Mapping[str, Any] | None = None,
        ground: str | None = None,
        substrate: str | None = None,
        mode: str | None = None,
        palette: str | None = None,
        width: float | None = None,
        height: float | None = None,
        id: str | None = None,
    ) -> None:
        appearance = {"ground": ground, "substrate": substrate, "mode": mode, "palette": palette}
        self._spec = build_spec(
            chart,
            data,
            roles=roles,
            options=options,
            appearance=appearance,
            width=width,
            height=height,
            id=id,
        )

    @classmethod
    def from_spec(cls, spec: Mapping[str, Any]) -> Chart:
        """A chart over a spec already written (for instance, by the MCP's ``generate_code``)."""
        chart = cls.__new__(cls)
        chart._spec = json.loads(json.dumps(dict(spec)))
        return chart

    @property
    def spec(self) -> dict[str, Any]:
        return self._spec

    @property
    def name(self) -> str:
        props = self._spec.get("props") or {}
        entry = charts().get(self._spec["chart"], {})
        return str(props.get("label") or props.get("title") or entry.get("title") or self._spec["chart"])

    @property
    def size(self) -> tuple[float, float]:
        return (self._spec.get("width", _DEFAULT_SIZE[0]), self._spec.get("height", _DEFAULT_SIZE[1]))

    def to_json(self) -> str:
        return html.js_json(self._spec)

    def to_svg(self, *, embed_fonts: bool = False) -> str:
        """The library's ``renderToSVG`` bytes, run in Node (PY-REQ-009)."""
        options = {"embedFonts": True} if embed_fonts else {}
        return svg.call("renderToSVG", self._spec, options)["svg"]

    def render_html(self, **options: Any) -> str:
        """The library's ``renderToHTML(spec, options)`` in Node: server-drawn, byte-identical."""
        return svg.call("renderToHTML", self._spec, options)["html"]

    def to_html(
        self,
        full_document: bool = True,
        script: str = "inline",
        *,
        render: str = "auto",
        title: str | None = None,
        lang: str = "en",
        integrity: str | None = None,
    ) -> str:
        """Interactive HTML for this chart (PY-REQ-006).

        ``script``: ``"inline"`` (the vendored file, so the page needs no network), ``"none"`` (the page
        loads it) or a URL the application serves. ``render``: ``"server"`` draws the chart in Node with
        the library's ``renderToHTML`` (byte-identical to its goldens; the script then adopts it);
        ``"client"`` writes only the spec and lets the script draw; ``"auto"`` is ``server`` when Node is
        on PATH and ``client`` otherwise.
        """
        if render == "auto":
            render = "server" if shutil.which("node") else "client"
        if render == "server":
            options: dict[str, Any] = {
                "as": "document" if full_document else "fragment",
                "interactive": True,
                "lang": lang,
            }
            if title is not None:
                options["title"] = title
            if full_document and script != "none":
                options["script"] = (
                    {"inline": html.script_text()}
                    if script == "inline"
                    else {"src": script, **({"integrity": integrity} if integrity else {})}
                )
            return self.render_html(**options)
        if render != "client":
            raise ValueError('render must be "auto", "server" or "client"')
        box = html.embed_box(self._spec)
        if not full_document:
            return box
        return html.document(
            box, title=title or self.name, lang=lang, script=html.script_tag(script, integrity)
        )

    def _repr_mimebundle_(self, include: Any = None, exclude: Any = None) -> dict[str, Any]:
        return {"text/html": notebook.markup(self), "application/json": self._spec}

    def __repr__(self) -> str:
        look = {k: self._spec[k] for k in APPEARANCE if k in self._spec}
        return f"Chart({self._spec['chart']!r}{''.join(f', {k}={v!r}' for k, v in look.items())})"
