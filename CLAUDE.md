# silverpoint-python — context for agents

Before proposing or writing code, read [`specs/constitution.md`](specs/constitution.md). Its articles
are binding:

- **PY-Art. 1 — No picture is made in Python.** The package builds a spec and the markup that carries
  it. No geometry, no scale, no colour, no layout.
- **PY-Art. 2 — No required dependency.** The base install is the standard library. pandas, polars,
  pyarrow, pyspark (delta-001), Flask and Django are detected, never imported at module load (`tests/test_data.py` checks).
- **PY-Art. 3 — Self-contained output.** HTML the package writes works with no network. Never a CDN URL.

Specs: `specs/prd.md` (PY-REQ-001..016), `specs/technical-design.md` (PY-DD-01..05), `specs/tasks.md`
(PY-T-01..13 and the ledger). `specs/spec-pack.md` is the pack as written in silverpoint's
`changes/feature-007-bi-hosts/repositories/`; the four files are its split, unchanged.
`changes/delta-001-databricks.md` (Spark inputs, `enable()` in Databricks, the example notebook;
PY-REQ-017..018, PY-T-14..16) is implemented and waits for review before it is folded into `specs/`.

Working rules:

- Test-first; every test cites the PY-REQ it verifies.
- `src/silverpoint/_vendor/` is written only by `scripts/vendor.py` (the hosts kit of a silverpoint
  release, or `--from` a local checkout after `pnpm build`). `_builders.py` and `_builders.pyi` only by
  `scripts/make_builders.py`. Both have a `--check` that CI runs.
- The version mirrors the library's (PY-DD-01): X.Y.Z vendors `@silverpoint/embed` X.Y.Z; Python-only
  fixes are X.Y.Z.postN.
- Before committing: `uv run ruff check . && uv run ruff format --check . && uv run pytest`; the
  Spark tests run with `uv sync --group spark` and Java 17+ (CI job `spark`).
- Release by tag `vX.Y.Z` on `main`; PyPI through Trusted Publishing (`release.yml`, environment
  `pypi`). The name `silverpoint` is reserved by the first real upload (PY-T-02 withdrawn).
