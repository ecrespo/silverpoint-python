"""Flask: ``Silverpoint(app)`` serves the vendored script and adds two Jinja globals (PY-REQ-011).

    from silverpoint.contrib.flask import Silverpoint
    Silverpoint(app)                     # or Silverpoint().init_app(app)

    {{ silverpoint_script() }}            in the page's <head> or before </body>
    {{ silverpoint_chart(chart) }}        a <silverpoint-chart> with its spec in a JSON child

The markup has no inline script and no inline style, so it renders under
``Content-Security-Policy: script-src 'self'; style-src 'self'`` (PY-REQ-013).
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Flask, send_from_directory, url_for
from markupsafe import Markup

from .._catalog import VENDOR
from . import _markup

ONE_YEAR = 31_536_000


def silverpoint_script() -> Markup:
    return Markup(_markup.script(url_for("silverpoint.script", filename=_markup.SCRIPT)))


def silverpoint_chart(chart_or_spec: Any) -> Markup:
    return Markup(_markup.chart(chart_or_spec))


class Silverpoint:
    def __init__(self, app: Flask | None = None, url_prefix: str = "/_silverpoint") -> None:
        self.url_prefix = url_prefix
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        blueprint = Blueprint("silverpoint", __name__, url_prefix=self.url_prefix)

        @blueprint.route("/<path:filename>")
        def script(filename: str) -> Any:
            if filename not in (_markup.SCRIPT, "silverpoint-embed.full.mjs"):
                from flask import abort

                abort(404)
            response = send_from_directory(VENDOR, filename, mimetype="text/javascript", max_age=ONE_YEAR)
            response.cache_control.immutable = True
            response.cache_control.public = True
            return response

        app.register_blueprint(blueprint)
        app.jinja_env.globals.update(
            silverpoint_script=silverpoint_script, silverpoint_chart=silverpoint_chart
        )
        app.extensions["silverpoint"] = self
