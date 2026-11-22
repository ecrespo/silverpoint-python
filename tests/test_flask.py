"""PY-REQ-011: the Flask extension serves the script and writes CSP-safe markup."""

import pytest

flask = pytest.importorskip("flask")

from silverpoint import Chart  # noqa: E402
from silverpoint.contrib.flask import Silverpoint  # noqa: E402


@pytest.fixture
def app():
    app = flask.Flask(__name__)
    Silverpoint(app)

    @app.route("/")
    def index():
        chart = Chart("bar-chart", [{"a": "<x>", "b": 1}], roles={"x": "a", "value": "b"})
        return flask.render_template_string(
            "{{ silverpoint_script() }}{{ silverpoint_chart(chart) }}", chart=chart
        )

    return app


def test_script_route(app):
    response = app.test_client().get("/_silverpoint/silverpoint-embed.full.js")
    assert response.status_code == 200
    assert response.mimetype == "text/javascript"
    assert "immutable" in response.headers["Cache-Control"]
    assert "max-age=31536000" in response.headers["Cache-Control"]


def test_globals(app):
    body = app.test_client().get("/").get_data(as_text=True)
    assert '<script src="/_silverpoint/silverpoint-embed.full.js" integrity="sha384-' in body
    assert '<silverpoint-chart><script type="application/json">' in body
    assert "\\u003cx\\u003e" in body
    assert "<script>" not in body


def test_chart_takes_a_spec(app):
    with app.app_context():
        from silverpoint.contrib.flask import silverpoint_chart

        markup = str(silverpoint_chart({"chart": "orbit-chart"}))
    assert (
        markup
        == '<silverpoint-chart><script type="application/json">{"chart":"orbit-chart"}</script></silverpoint-chart>'
    )
