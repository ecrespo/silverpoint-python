# `silverpoint-python` — Technical design

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`). Since then: delta-001
> (Databricks; approved 2026-11-22) adds PY-DD-06 and a note to PY-DD-04.

## Design decisions

- **PY-DD-01 — The version mirrors the library's.** `silverpoint` X.Y.Z vendors
  `@silverpoint/embed` X.Y.Z. Python-only fixes are `X.Y.Z.postN`. This is the one host whose version
  is not its own (silverpoint DD-068): it is the standalone file's Python distribution, and "which
  silverpoint is this" must have one answer.
- **PY-DD-02 — Vendoring is a build step, checked in.** `scripts/vendor.py X.Y.Z` downloads the
  hosts kit of the GitHub release `vX.Y.Z` (or the npm tarball) —`silverpoint-embed.full.js`,
  `.full.mjs`, `host-catalog.json`, `conformance.json`, `integrity.json`, the HTML goldens and the
  table fixtures— verifies digests, and
  writes `src/silverpoint/_vendor/`. The files are committed, so an sdist builds offline and a
  reviewer sees the diff. CI re-runs it with `--check`.
- **PY-DD-03 — Builders are generated.** `scripts/make_builders.py` writes `_builders.py` and its
  `.pyi` from the host catalog (H-3): signatures, docstrings from `summary` and `doc`, snake-case
  names with the camel-case original kept in a table. CI: `--check`.
- **PY-DD-04 — An iframe in notebooks.** Front ends differ on whether a `<script>` in an output
  runs, and Databricks renders HTML in a frame of its own. A `srcdoc` frame with
  `sandbox="allow-scripts"` behaves the same everywhere and keeps the chart's stylesheet off the
  notebook's. Cost: the script travels with each chart unless PY-REQ-008 applies.
  In Databricks every output is its own frame, so PY-REQ-008 never applies there: `enable()` warns
  and changes nothing (delta-001).
- **PY-DD-05 — Flask and Django are sub-packages** (silverpoint D3), each importing its framework
  only inside its own module. Extras `silverpoint[flask]`, `silverpoint[django]` declare the
  frameworks' minimum versions and nothing else.
- **PY-DD-06 — A Spark table is read bounded, on the driver** (delta-001). pyspark is recognised by
  the module of the object's type, never imported (PY-Art. 2). `data.py` takes
  `limit(SPARK_ROW_LIMIT + 1)`, collects it through `toArrow` where it exists (Spark 4, Spark Connect)
  or `toPandas` otherwise, and refuses the table if the extra row came back: a chart never collects a
  large table, and an aggregation is asked for in Spark rather than done in Python (server-side
  aggregation stays out of scope). No extra: pyspark is the runtime's, and is tested in the `spark`
  dependency group.

## Structure

```
src/silverpoint/
  __init__.py  chart.py  data.py  spec.py  reshape.py  html.py  notebook.py  svg.py  errors.py
  _builders.py (generated)   _builders.pyi (generated)
  _vendor/  silverpoint-embed.full.js  silverpoint-embed.full.mjs  host-catalog.json
            conformance.json  integrity.json  html-goldens/  OFL.txt
  contrib/flask.py
  contrib/django/  __init__.py  apps.py  templatetags/silverpoint.py  static/silverpoint/ (symlinked or copied at build)
scripts/  vendor.py  make_builders.py  conformance.mjs
tests/    examples/ (notebooks: Jupyter, Databricks)   docs/
```
