"""A Flask page with one chart, under a strict CSP: ``uv run flask --app examples/flask/app.py run``."""

from flask import Flask, render_template_string

import silverpoint
from silverpoint.contrib.flask import Silverpoint

app = Flask(__name__)
Silverpoint(app)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Wins</title>{{ silverpoint_script() }}</head>
<body><h1>Wins per team</h1>{{ silverpoint_chart(chart) }}</body></html>"""


@app.after_request
def csp(response):
    response.headers["Content-Security-Policy"] = "script-src 'self'; style-src 'self'"
    return response


@app.route("/")
def index():
    rows = [{"team": "A", "wins": 12}, {"team": "B", "wins": 9}, {"team": "C", "wins": 15}]
    chart = silverpoint.bar_chart(rows, x="team", value="wins", title="Wins", orientation="rows")
    return render_template_string(PAGE, chart=chart)
