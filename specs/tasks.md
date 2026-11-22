# `silverpoint-python` — Tasks

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`), content unchanged.

## Tasks

- [x] **PY-T-01** Split this pack into `specs/`; `CLAUDE.md`; `uv` project, `ruff`, `pytest`, CI skeleton. Stop for review. *H-7*
- [x] **PY-T-02** *Withdrawn (user decision, 2026-11-20):* no placeholder release; the name `silverpoint` on PyPI is reserved by the first real upload in PY-T-13, whose Trusted Publisher is set up as a pending publisher before that release. *PY-REQ-016*
- [x] **PY-T-03** `scripts/vendor.py` and its `--check`; integrity verification. *PY-REQ-015, PY-REQ-016, H-2*
- [x] **PY-T-04** `spec.py`, `errors.py`: validation against the catalog. *PY-REQ-001, PY-REQ-004*
- [x] **PY-T-05** `data.py`: every input kind, with and without pandas/polars installed (tox-style matrix). *PY-REQ-002*
- [x] **PY-T-06** `reshape.py` against the library's table fixtures. *PY-REQ-005*
- [x] **PY-T-07** `scripts/make_builders.py`, `_builders.py`, stubs, `--check`. *PY-REQ-003, H-3*
- [x] **PY-T-08** `html.py` against the goldens and the hostile corpus. *PY-REQ-006, PY-REQ-014*
- [x] **PY-T-09** `notebook.py`; a Playwright test that opens an executed notebook's HTML export and reads the chart by keyboard. *PY-REQ-007, PY-REQ-008, H-5*
- [x] **PY-T-10** `svg.py` and `scripts/conformance.mjs`; the kit in CI. *PY-REQ-009, PY-REQ-015, H-4*
- [x] **PY-T-11** `contrib/flask.py` with an example app and the CSP browser test. *PY-REQ-011, PY-REQ-013*
- [x] **PY-T-12** `contrib/django` with an example project and the CSP browser test. *PY-REQ-012, PY-REQ-013*
- [ ] **PY-T-13** `catalog`, versions, `static_path`; README with one example per host (Jupyter, Databricks `displayHTML(chart.to_html())`, Flask, Django); release `0.11.0`. *PY-REQ-010*

## Open questions

- **PY-OQ-1** Databricks: does `displayHTML` accept the document size of the `full` file per cell
  without truncation? Measure in PY-T-09 on Free Edition; the fallback is the script served from a
  workspace file.
- **PY-OQ-2** An optional extra with an embedded JavaScript engine for `to_svg` without Node: only
  if users ask.

## Bootstrap prompt

````text
This repository will publish `silverpoint` on PyPI: silverpoint charts from Python. Its design is in specs/spec-pack.md, written in the silverpoint repository (~/WebstormProjects/silverpoint/changes/feature-007-bi-hosts). Read the pack, then that folder's README.md, api-delta.md and repositories/README.md §3.

Do PY-T-01 only: split the pack into specs/constitution.md, specs/prd.md, specs/technical-design.md and specs/tasks.md without changing its content; write CLAUDE.md pointing at the constitution and listing PY-Art. 1..3; set up the uv project, ruff, pytest and a CI workflow that runs them. Write no package code. Show me the tree and the output of `uv run pytest` and `uv run ruff check .`, then stop.
````

## Implementation ledger (2026-11-20)

Built test-first against silverpoint `0.10.1`'s local build (`scripts/vendor.py --from`), which carries
the 0.11.0 API; `vendor.py 0.11.0` replaces the files once the release attaches its hosts kit. Every
task's tests were written and run red before the code. `uv run pytest`: 100 passed (Python 3.13, Node
22, the Playwright Chromium build 1243 through `SP_CHROMIUM`); the bare install (no pandas/polars/pyarrow/Flask/Django): 81
passed, 4 skipped. `ruff check`, `ruff format --check`, `vendor.py --check`, `make_builders.py --check`
clean; `node scripts/conformance.mjs`: 76 passed, 0 failed.

| Task | Tests | Mutation check |
|---|---|---|
| PY-T-03 | `test_vendor.py` (digests, `--check`, wheel contents) | — |
| PY-T-04, -06 | `test_spec.py`: 15 table fixtures + 8 error fixtures equal `specFromTable`; three edges taken from Node | `__values` → `values`: survived the library's fixtures, so the edge test was added; then red |
| PY-T-05 | `test_data.py`, plus the import probe of PY-Art. 2 | — |
| PY-T-07 | `test_builders.py` (56 builders, signature, `--check`) | — |
| PY-T-08 | `test_html.py`: the 9 goldens byte for byte (Node), the 10 hostile specs, `JSON.stringify` numbers | dropping the `&` escape → red |
| PY-T-09 | `test_notebook.py`; `test_browser.py` opens the output in Chromium and reads it by keyboard | — |
| PY-T-10 | `test_svg.py`, `test_vendor.py::test_conformance_kit` | — |
| PY-T-11, -12 | `test_flask.py`, `test_django.py`; `test_browser.py` under `script-src 'self'; style-src 'self'` | an inline script instead of `src` → red |

### Deviations — to review

- **PY-D1 — byte-identical HTML needs Node.** PY-REQ-006's golden holds the server-drawn chart root,
  and PY-Art. 1 forbids drawing in Python. `to_html` takes `render="auto" | "server" | "client"`:
  `server` runs the library's `renderToHTML` in Node (byte-identical; tested on the 9 goldens),
  `client` writes the same envelope with only the spec, which the inlined script mounts on load
  (silverpoint DD-070 as implemented). `auto` picks `server` when Node is on PATH. Notebooks always
  use `client`, so they need no Node.
- **PY-D2 — `SpecError.kind == "value"`** for an option or appearance value outside its `values`:
  the library reports these as diagnostics at render time; PY-REQ-004 asks for an error before HTML.
- **PY-D3 — the Django static file is a copy**, not a symlink (a symlink breaks on Windows checkouts
  and in some wheels); `vendor.py` writes it and `--check` compares it with the vendored script.
- **PY-D4 — the hosts kit is a zip** (silverpoint TD delta §6), not the tarball the pack's PY-DD-02
  mentions. silverpoint's `release.yml` now builds and attaches it (`tools/release/hosts-kit.mjs`).

### Open

- PY-T-13: the release itself — the pending trusted publisher on PyPI, then tag `v0.11.0` on `main`.
  Everything before it is done (2026-11-22, below).
- PY-OQ-1: partly answered from Databricks' documented limits (delta-001); the measurement in a
  workspace (Free Edition) is still open.
- delta-001 (Databricks: PY-T-14..16) implemented 2026-11-21; to review, then fold into `specs/`.


## Ledger (2026-11-22) — PY-T-13 up to the release

- `vendor.py 0.11.0` from silverpoint's `v0.11.0` hosts kit (the release also has `v0.11.1`, "no
  changes"; 0.11.0 matches PY-T-13 and `reflex-silverpoint-react` 0.11.0). Builders regenerated: no change
  to the 56 builders. `pyproject.toml` and `__version__` are `0.11.0`.
- Fixed in `vendor.py`: `verify()` checked the pyproject mirror on the staging folder too, so the
  documented order (`vendor.py X.Y.Z`, then the version) always refused to write. The mirror is now
  checked only on the checked-in folder, and covers `silverpoint.__version__` as well. Tests first:
  `test_vendor.py::test_staging_of_a_new_version_does_not_need_pyproject_bumped_first` (red, then
  green) and `::test_package_version_mirrors_pyproject`.
- `uv run pytest`: 112 passed, none skipped (Python 3.13, Node 22, Playwright Chromium 1255, pyspark with
  Java 21); the bare install on Python 3.10: 85 passed, 4 skipped; `node scripts/conformance.mjs`:
  0.11.0, 76 passed, 0 failed; `ruff`, `vendor.py --check`, `make_builders.py --check`, `uv lock --check`
  clean.
- Cross-check with `reflex-silverpoint-react` 0.11.0 (`reflex-catalog.json`): the same 60 charts; every
  Python builder has the Reflex builder's name; the four without one (`orbit-chart`, `sparkline-rows`,
  `treemap-chart`, `volvelle-chart`) have `binding: none`.
