# Changelog

## 0.11.0 (unreleased)

First release, vendoring `@silverpoint/embed` 0.11.0 from the hosts kit attached to silverpoint's
`v0.11.0` release (built test-first against 0.10.1's local build, which carries the same API).

- `Chart`, one builder per bindable chart, `SpecError` with "did you mean".
- `to_html` (server-drawn in Node or client-drawn), `to_svg`, notebook frames, `notebook.enable()`.
- `silverpoint.contrib.flask` and `silverpoint.contrib.django`, CSP-safe.
- Databricks (delta-001): Spark and pandas-on-Spark DataFrames and Spark `Row`s as data, read
  through `limit` up to `SPARK_ROW_LIMIT` (10,000); `notebook.enable()` warns there; an example
  notebook in Databricks source format.
- `scripts/vendor.py`, `scripts/make_builders.py`, `scripts/conformance.mjs`. `vendor.py X.Y.Z`
  verifies the kit before the version is moved; `--check` then requires `pyproject.toml` and
  `silverpoint.__version__` to mirror it (PY-DD-01).
