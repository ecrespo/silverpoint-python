# `silverpoint-python` — Constitution

> Split from `specs/spec-pack.md` (silverpoint feature-007, `repositories/`), content unchanged.

## Constitution

H-1..H-8 ([`README.md`](README.md) §3), and:

- **PY-Art. 1 — No picture is made in Python.** THE PACKAGE SHALL build a chart spec and the markup
  that carries it, and nothing else. It SHALL hold no geometry, no scale, no colour and no layout.
- **PY-Art. 2 — No required dependency.** THE BASE INSTALL SHALL depend on nothing but the standard
  library. pandas, polars, pyarrow, pyspark (delta-001), Flask and Django are detected, never imported
  at module load.
- **PY-Art. 3 — Self-contained output.** HTML THE PACKAGE WRITES SHALL work with no network: the
  script is inlined or served by the application itself. It SHALL never write a CDN URL.

Stack: Python ≥ 3.10; `uv`; `hatchling`; `ruff`; `pytest`; Node 20+ **in CI only** (the conformance
kit and `to_svg` tests); PyPI Trusted Publishing from a tag.

## Identity

| Field | Value |
|---|---|
| **Repository** | `github.com/ecrespo/silverpoint-python` |
| **Published as** | PyPI `silverpoint` (import name `silverpoint`) |
| **Licence** | MIT |
| **Description** | Silverpoint charts from Python: a chart from a DataFrame as self-contained HTML, for notebooks, Databricks, Flask and Django. |
| **Draws with** | `silverpoint-embed.full.js`, vendored from the silverpoint release it mirrors |
| **Wave** | 1 (the PyPI name is taken by the first real upload, PY-T-13) |
| **Ids** | `PY-REQ-nnn`, `PY-DD-nn`, `PY-T-nn` |
| **Status** | `APPROVED` gate-1 pack, 2026-11-20 (user decision); re-read against the released API in T-328 |
