# `silverpoint-python` — Prd

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`). Since then:
> [delta-001](../changes/archive/delta-001-databricks.md) (Databricks; approved 2026-11-22) amends
> PY-REQ-002 and PY-REQ-008 and adds PY-REQ-017 and PY-REQ-018.

## Scope

**In:** `Chart`; one builder per chart; DataFrame inputs; `to_html`, `save`, notebook display;
`to_svg` where Node is available; `silverpoint.contrib.flask`; `silverpoint.contrib.django`; the host
catalog as Python data. **Out:** Reflex (that is `reflex-silverpoint-react`); dashboards, UI
components, decks; a pure-Python or embedded-engine SVG (silverpoint DD-069); server-side aggregation.

## Requirements

| ID | Requirement | Priority |
|---|---|---|
| PY-REQ-001 | THE PACKAGE SHALL expose `Chart(chart, data=None, *, roles=None, options=None, ground=None, substrate=None, mode=None, palette=None, width=None, height=None, id=None)` whose `spec` property is a `ChartSpec` as a `dict` (silverpoint Data Model §2.38). | MUST |
| PY-REQ-002 | THE PACKAGE SHALL accept as `data` a list of mappings, a mapping of columns, a pandas or polars DataFrame, a pyarrow Table, a Spark DataFrame (classic or Spark Connect), a pandas-on-Spark DataFrame, a list of Spark `Row`s, or any object with `to_dict("records")` or `to_dicts()`, converting dates to ISO strings, NaN and NaT to `None`, and numpy scalars to Python numbers. pyspark SHALL be detected by module name, never imported (PY-Art. 2). *(delta-001)* | MUST |
| PY-REQ-003 | THE PACKAGE SHALL provide one function per chart of the pinned host catalog whose `binding` is not `none` —`silverpoint.bar_chart(df, x="team", value="wins", orientation="rows")`— with one keyword per role and per option in snake case, generated from the host catalog. | MUST |
| PY-REQ-004 | IF a required role is missing, a column is not in the data, an option is unknown or a value is outside an option's `values`, THEN THE PACKAGE SHALL raise `SpecError` naming it, with the closest valid names, before any HTML is written. | MUST |
| PY-REQ-005 | THE PACKAGE SHALL apply, in Python, the reshapes the host catalog declares (`matrix`, `dimensions`, `first-row`), with results equal to `specFromTable`'s for the fixtures of `fixtures/embed/tables`. | MUST |
| PY-REQ-006 | WHEN `to_html(full_document=True, script="inline")` is called, THE PACKAGE SHALL return the interactive document of `renderToHTML` (silverpoint API §1.5), byte-identical to the library's golden for the same spec and options. `script` SHALL accept `"inline"`, `"none"` and a URL string the application serves. | MUST |
| PY-REQ-007 | WHEN a `Chart` is the value of a notebook cell, THE PACKAGE SHALL display it through `_repr_mimebundle_` as `text/html` holding a sandboxed `<iframe srcdoc>` of the inline document, sized to the chart, so that the chart draws in Jupyter, JupyterLab, VS Code and Databricks without trusting the notebook. | MUST |
| PY-REQ-008 | THE PACKAGE SHALL inline the script once per notebook where the front end allows shared output (`silverpoint.notebook.enable()`), and once per chart otherwise. WHEN `enable()` runs in Databricks (`DATABRICKS_RUNTIME_VERSION` is set), it SHALL leave notebooks on one frame per chart and warn (`RuntimeWarning`): there each output is its own frame, so a shared script would reach no chart. *(delta-001)* | SHOULD |
| PY-REQ-009 | WHERE Node 20+ is on `PATH`, `to_svg()` SHALL return the library's `renderToSVG` result by running the vendored module build in a subprocess with the spec on standard input; otherwise it SHALL raise `RuntimeUnavailable` saying how to get an SVG. | MUST |
| PY-REQ-010 | THE PACKAGE SHALL expose `silverpoint.catalog` (the pinned host catalog as data), `silverpoint.__version__` and `silverpoint.SILVERPOINT_VERSION`, and `silverpoint.static_path()` returning the folder of the vendored script. | MUST |
| PY-REQ-011 | `silverpoint.contrib.flask.Silverpoint(app)` SHALL register a route serving the vendored script with a long-lived immutable cache header and its integrity, and the Jinja globals `silverpoint_script()` and `silverpoint_chart(chart_or_spec)`, the latter writing a `<silverpoint-chart>` with the spec in a JSON child and no inline script. | MUST |
| PY-REQ-012 | `silverpoint.contrib.django` SHALL be an installable app providing the script through `staticfiles` and the template tags `{% silverpoint_script %}` and `{% silverpoint_chart chart %}`, equivalent to the Flask globals. | MUST |
| PY-REQ-013 | THE MARKUP OF PY-REQ-011 AND PY-REQ-012 SHALL render under `Content-Security-Policy: script-src 'self'; style-src 'self'`, verified by a browser test. | MUST |
| PY-REQ-014 | THE PACKAGE SHALL escape the spec for a script context exactly as the library does (`<`, `>`, `&`, U+2028, U+2029), verified over the library's hostile corpus. | MUST |
| PY-REQ-015 | CI SHALL run the conformance kit in Node against the vendored module build, and SHALL verify the vendored files against `integrity.json`. | MUST |
| PY-REQ-016 | THE WHEEL SHALL contain the vendored script, the host catalog, `integrity.json` and the licence of the embedded font, and SHALL be pure Python (`py3-none-any`). | MUST |
| PY-REQ-017 | WHEN `data` is a Spark or pandas-on-Spark DataFrame, THE PACKAGE SHALL collect at most `silverpoint.data.SPARK_ROW_LIMIT` (10,000) rows through `limit(SPARK_ROW_LIMIT + 1)` (Arrow when the DataFrame has `toArrow`, pandas otherwise), and IF the DataFrame holds more, THEN SHALL raise `ValueError` that names the limit and asks for an aggregation in Spark, before any row reaches the spec. *(delta-001)* | MUST |
| PY-REQ-018 | A chart's notebook output (PY-REQ-007's frame) SHALL stay under 1 MB for a table of up to 100 rows —the smallest cell-output limit Databricks can be set to (`%set_cell_max_output_size_in_mb 1`)— and under 10 MB, Databricks' default on Runtime 17+, at `SPARK_ROW_LIMIT` rows. *(delta-001)* | SHOULD |
