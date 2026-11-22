# silverpoint

silverpoint charts from Python — in notebooks, Flask, Django and static HTML. No picture is made in
Python: the package builds a chart spec and the markup that carries it, and the library's own
standalone script (`@silverpoint/embed`, vendored version for version) draws it.

```sh
pip install silverpoint            # no dependencies
pip install "silverpoint[flask]"   # or [django]
```

`silverpoint` X.Y.Z vendors `@silverpoint/embed` X.Y.Z (`silverpoint.SILVERPOINT_VERSION`).

## A chart

```python
import pandas as pd
import silverpoint

df = pd.DataFrame({"team": ["A", "B", "C"], "wins": [12, 9, 15]})
chart = silverpoint.bar_chart(df, x="team", value="wins", orientation="rows", title="Wins")

chart.spec  # the ChartSpec, a dict
chart.to_html()  # a complete, self-contained page (the script inlined; no network)
chart.to_svg()  # the library's renderToSVG bytes (needs Node 20+ on PATH)
```

There is one builder per chart a table can feed — `silverpoint.line_chart`, `heatmap_chart`,
`sankey_chart`, … — with one keyword per role (a column name) and per option, generated from the
host catalog. `silverpoint.Chart("bar-chart", df, roles={...}, options={...})` is the same thing by
name, and `silverpoint.catalog` is the catalog itself. Data can be rows, a mapping of columns, a pandas
or polars DataFrame or a pyarrow Table; dates become ISO strings and NaN/NaT become `None`.

A role, column, option or value the catalog does not know raises `SpecError` naming the closest valid
names, before any HTML is written.

## Jupyter, JupyterLab, VS Code

A chart as a cell's value draws itself: each one is a sandboxed `<iframe srcdoc>` holding the inline
page, so it needs no trusted notebook. `silverpoint.notebook.enable()` shows the script once and writes
later charts as `<silverpoint-chart>` elements, for front ends that run scripts in outputs.

## Databricks

A Spark DataFrame goes straight into a builder, and a chart as a cell's value draws itself:

```python
from pyspark.sql import functions as F

import silverpoint

by_hour = (
    spark.read.table("samples.nyctaxi.trips")
    .groupBy(F.hour("tpep_pickup_datetime").alias("hour"))
    .agg(F.count("*").alias("trips"))
    .orderBy("hour")
)
silverpoint.line_chart(by_hour, x="hour", value="trips", title="Trips per pickup hour")
```

`displayHTML(chart.to_html(render="client"))` draws a chart anywhere in a cell, so one cell can draw
several. pandas-on-Spark DataFrames and the `Row`s of `collect()` work too.

- **Rows.** At most `silverpoint.data.SPARK_ROW_LIMIT` (10,000) rows are read, through `limit`, so a
  large table never reaches the driver; a bigger DataFrame raises `ValueError`. Aggregate in Spark
  first.
- **Size.** Each chart carries its own copy of the script (about 0.5 MB; 1.1 MB with 10,000 rows).
  One cell's output may be 10 MB by default on Runtime 17+ (`%set_cell_max_output_size_in_mb`
  sets 1–20 MB), and a notebook keeps about fifteen charts before Databricks stops saving its
  revision snapshots (10 MB).
- `silverpoint.notebook.enable()` has no effect there: each output is its own frame.

[`examples/notebooks/databricks.py`](examples/notebooks/databricks.py) is a notebook to import
(Databricks source format) that runs on `samples.nyctaxi.trips`.

## Flask

```python
from silverpoint.contrib.flask import Silverpoint

Silverpoint(app)  # serves the script at /_silverpoint/, immutable, with its integrity
```

```jinja
<head>{{ silverpoint_script() }}</head>
<body>{{ silverpoint_chart(chart) }}</body>
```

## Django

Add `"silverpoint.contrib.django"` to `INSTALLED_APPS` (with `django.contrib.staticfiles`), then:

```django
{% load silverpoint %}
<head>{% silverpoint_script %}</head>
<body>{% silverpoint_chart chart %}</body>
```

The Flask and Django markup has no inline script or style: it renders under
`Content-Security-Policy: script-src 'self'; style-src 'self'`.

## HTML

`to_html(full_document=True, script="inline", render="auto")`:

- `script`: `"inline"` (the vendored file in the page), `"none"` (the page loads it) or a URL your
  application serves. A CDN URL is never written.
- `render`: `"server"` draws the chart in Node with the library's `renderToHTML` (byte-identical to
  its goldens; the script then adopts it); `"client"` writes only the spec and the script draws it;
  `"auto"` picks `server` when Node is on PATH.

`silverpoint.static_path()` is the folder holding `silverpoint-embed.full.js`, for any framework.

## Development

```sh
uv sync
uv run pytest                                   # browser tests: uv run playwright install chromium
uv run ruff check . && uv run ruff format --check .
uv run python scripts/vendor.py --check         # the vendored files against integrity.json
uv run python scripts/make_builders.py --check  # the generated builders are current
node scripts/conformance.mjs                    # the library's conformance kit, in Node
```

A new silverpoint version: `uv run python scripts/vendor.py X.Y.Z` (the release's hosts kit), then
`uv run python scripts/make_builders.py`, and set `version` in `pyproject.toml` to X.Y.Z.

Licence: MIT. The vendored script embeds EB Garamond (SIL OFL 1.1, `_vendor/OFL.txt`).
