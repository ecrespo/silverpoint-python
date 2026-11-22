"""PY-REQ-003: one builder per bindable chart, generated from the host catalog (PY-DD-03)."""

import inspect
import subprocess
import sys
from pathlib import Path

import silverpoint
from silverpoint import _builders

ROOT = Path(__file__).resolve().parents[1]


def test_one_builder_per_bindable_chart():
    bindable = [c["slug"] for c in silverpoint.catalog["charts"] if c["binding"] != "none"]
    names = [slug.replace("-", "_") for slug in bindable]
    assert sorted(_builders.__all__) == sorted(names)
    for name in names:
        assert callable(getattr(silverpoint, name))


def test_builder_signature_has_roles_and_options():
    params = inspect.signature(silverpoint.bar_chart).parameters
    assert next(iter(params)) == "data"
    for name in ("x", "value", "orientation", "title", "ground", "palette", "width", "id"):
        assert params[name].kind is inspect.Parameter.KEYWORD_ONLY


def test_builder_equals_chart():
    rows = [{"team": "A", "wins": 12}, {"team": "B", "wins": 9}]
    built = silverpoint.bar_chart(rows, x="team", value="wins", orientation="rows", title="Wins")
    assert (
        built.spec
        == silverpoint.Chart(
            "bar-chart",
            rows,
            roles={"x": "team", "value": "wins"},
            options={"orientation": "rows", "title": "Wins"},
        ).spec
    )


def test_snake_case_option():
    built = silverpoint.line_chart([{"h": "a", "v": 1}], x="h", value="v", connect_nulls=True)
    assert built.spec["props"]["connectNulls"] is True


def test_docstring_from_summary():
    assert silverpoint.bar_chart.__doc__.splitlines()[0].strip()


def test_generated_files_are_current():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "make_builders.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
