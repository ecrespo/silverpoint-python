# delta-001 — Databricks

| | |
|---|---|
| **Status** | Approved and folded into `specs/` 2026-11-22 (user decision); implemented 2026-11-21, released in `0.11.0` |
| **Amends** | PY-REQ-002, PY-REQ-008; adds PY-REQ-017, PY-REQ-018; answers part of PY-OQ-1 |
| **Release** | `0.11.0` (the first release; nothing is published yet, so no version moves) |

## Why

The pack names Databricks as a host (PY-REQ-007, the README, `examples/notebooks`) but three things
were missing for it:

1. A Databricks table is a **Spark DataFrame**. PY-REQ-002 reads pandas, polars and pyarrow, so
   `silverpoint.bar_chart(spark.table(...), ...)` raised `TypeError`, and so did `df.collect()` (a list
   of Spark `Row`s, which are tuples, not mappings). Collecting a Spark DataFrame also moves it to the
   driver, so the read has to be bounded.
2. `notebook.enable()` shares one script across outputs, but Databricks renders each cell's HTML in
   its own frame (PY-DD-04): there, a shared script reaches no chart.
3. The technical design lists a Databricks example notebook beside the Jupyter one; there was none.

## Changes

### PY-REQ-002 (amended)

| Id | Requirement | Priority |
|---|---|---|
| PY-REQ-002 | THE PACKAGE SHALL accept as `data` a list of mappings, a mapping of columns, a pandas or polars DataFrame, a pyarrow Table, **a Spark DataFrame (classic or Spark Connect), a pandas-on-Spark DataFrame, a list of Spark `Row`s**, or any object with `to_dict("records")` or `to_dicts()`, converting dates to ISO strings, NaN and NaT to `None`, and numpy scalars to Python numbers. pyspark SHALL be detected by module name, never imported (PY-Art. 2). | MUST |

### New requirements

| Id | Requirement | Priority |
|---|---|---|
| PY-REQ-017 | WHEN `data` is a Spark or pandas-on-Spark DataFrame, THE PACKAGE SHALL collect at most `silverpoint.data.SPARK_ROW_LIMIT` (10,000) rows through `limit(SPARK_ROW_LIMIT + 1)` (Arrow when the DataFrame has `toArrow`, pandas otherwise), and IF the DataFrame holds more, THEN SHALL raise `ValueError` that names the limit and asks for an aggregation in Spark, before any row reaches the spec. | MUST |
| PY-REQ-018 | A chart's notebook output (PY-REQ-007's frame) SHALL stay under 1 MB for a table of up to 100 rows —the smallest cell-output limit Databricks can be set to (`%set_cell_max_output_size_in_mb 1`)— and under 10 MB, Databricks' default on Runtime 17+, at `SPARK_ROW_LIMIT` rows. | SHOULD |

### PY-REQ-008 (amended)

`notebook.enable()` SHALL leave notebooks on one frame per chart, and warn (`RuntimeWarning`), WHEN
it runs in Databricks (`DATABRICKS_RUNTIME_VERSION` is set): there each output is its own frame, so
a shared script would reach no chart.

### PY-OQ-1 (partly answered from Databricks' documentation, 2026-11-21)

- One cell's output may be 10 MB by default on Runtime 17+ and serverless environment 3 (1–20 MB with
  `%set_cell_max_output_size_in_mb`); a cell holds at most 16 MB with its contents. A chart's frame is
  about 0.58 MB with a small table (the script is 509 KB) and about 1.1 MB at 10,000 rows, so one
  chart per cell fits every setting of the default and every chart of up to 100 rows fits even 1 MB.
- A notebook's revision snapshots, import and export stop at 10 MB on AWS, so a notebook keeps
  about fifteen inline charts before that applies. The fallback stays the one PY-OQ-1 names: the
  script served from a workspace file (`to_html(script=<url>)`, PY-REQ-006), never a CDN (PY-Art. 3).
- **Still open:** the same in a workspace (Free Edition), with the 16.4-and-older runtimes.

## Tasks

- [x] **PY-T-14** Spark inputs and the row limit, tested against a local Spark session (pyspark in
  the `spark` dependency group, CI job `spark`). *PY-REQ-002, PY-REQ-017*
- [x] **PY-T-15** `enable()` in Databricks; the size bounds. *PY-REQ-008, PY-REQ-018*
- [x] **PY-T-16** `examples/notebooks/databricks.py` (Databricks source format), executed by a test
  with Databricks' globals stubbed; README section. *PY-REQ-007, PY-REQ-017*

## Evidence (2026-11-21)

- `uv run --group spark pytest`: 110 passed (Python 3.13, pyspark 4.3.0 on a local session, Java
  21); the bare install's subset: 85 passed, 4 skipped, and the Spark tests skip there.
- Written red first: `test_data.py` (Spark Connect and pandas-on-Spark surfaces, Arrow and pandas,
  the cap, `Row`s), `test_spark.py` (a real local Spark session), `test_notebook.py` (`enable()` in
  Databricks, the size bounds). `test_examples.py` was written after the notebook.
- Mutation checks: `limit(limit + 1)` → `limit(limit)` → the two cap tests red; dropping the
  Databricks check in `enable()` → red; dropping the hour formatting in the notebook → the example's
  test red.
- `ruff check`, `ruff format --check`, `vendor.py --check`, `make_builders.py --check` clean;
  `uv lock --check` passes; `node scripts/conformance.mjs`: 76 passed, 0 failed.
