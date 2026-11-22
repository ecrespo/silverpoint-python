"""PY-REQ-001, PY-REQ-004, PY-REQ-005: specs equal `specFromTable`'s over the library's table fixtures."""

import pytest
from conftest import VENDOR, load

import silverpoint
from silverpoint import Chart, SpecError

TABLES = sorted((VENDOR / "tables").glob("*.json"))
CASES = [(p.stem, c) for p in TABLES if p.stem != "errors" for c in load(p)]
ERRORS = load(VENDOR / "tables" / "errors.json")


def from_binding(binding):
    table = binding["table"]
    data = table.get("rows", table)
    if "columns" in table:
        data = {"columns": table["columns"], "values": table["values"]}
    return Chart(
        binding["chart"],
        data,
        roles=binding.get("roles"),
        options=binding.get("options"),
        id=binding.get("id"),
        **binding.get("appearance", {}),
        **binding.get("size", {}),
    )


@pytest.mark.parametrize(("file", "case"), CASES, ids=[f"{f}:{c['name']}" for f, c in CASES])
def test_spec_equals_spec_from_table(file, case):
    assert from_binding(case["binding"]).spec == case["expect"]


@pytest.mark.parametrize("case", ERRORS, ids=[c["name"] for c in ERRORS])
def test_errors_match_spec_from_table(case):
    with pytest.raises(SpecError) as raised:
        from_binding(case["binding"])
    error = raised.value
    if "error" in case:
        expected = case["error"]
        assert error.kind == expected["kind"]
        for key, value in expected.items():
            if key != "kind":
                assert getattr(error, key) == value, key
    else:
        assert error.kind == case["errorKind"]


def test_unknown_chart_names_the_closest():
    with pytest.raises(SpecError, match='Did you mean "bar-chart"'):
        Chart("bar-chrt", [])


def test_option_value_outside_its_values():
    with pytest.raises(SpecError) as raised:
        Chart(
            "bar-chart",
            [{"a": "x", "b": 1}],
            roles={"x": "a", "value": "b"},
            options={"orientation": "diagonal"},
        )
    assert raised.value.kind == "value"
    assert "orientation" in str(raised.value)
    assert '"rows"' in str(raised.value)


def test_unknown_option_suggests():
    with pytest.raises(SpecError, match='Did you mean "orientation"'):
        Chart(
            "bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"}, options={"orientaton": "rows"}
        )


def test_unknown_appearance_value():
    with pytest.raises(SpecError, match="ground"):
        Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"}, ground="charcoal")


def test_unbindable_chart_takes_options():
    chart = Chart("orbit-chart", options={"title": "Orbits"})
    assert chart.spec == {"chart": "orbit-chart", "props": {"title": "Orbits"}}


def test_snake_case_options_are_accepted():
    chart = Chart(
        "line-chart", [{"h": "a", "v": 1}], roles={"x": "h", "value": "v"}, options={"connect_nulls": True}
    )
    assert chart.spec["props"]["connectNulls"] is True


def test_appearance_and_size_in_spec_order():
    chart = Chart(
        "bar-chart",
        [{"a": "x", "b": 1}],
        roles={"x": "a", "value": "b"},
        ground="cyanotype",
        mode="precision",
        palette="sepia",
        width=640,
        height=300,
        id="w",
    )
    assert list(chart.spec) == [
        "chart",
        "data",
        "props",
        "ground",
        "mode",
        "palette",
        "width",
        "height",
        "id",
    ]


def test_catalog_and_versions():
    assert silverpoint.catalog["version"] == silverpoint.SILVERPOINT_VERSION
    assert silverpoint.__version__.startswith(silverpoint.SILVERPOINT_VERSION)
    assert (silverpoint.static_path() / "silverpoint-embed.full.js").is_file()


# Edges the library's fixtures leave out, with expectations taken from `specFromTable` in Node 0.10.1.
EDGES = [
    (
        Chart(
            "heatmap-chart",
            [{"values": "a", "c": "x", "v": 1}, {"values": "b", "c": "y", "v": 2}],
            roles={"row": "values", "column": "c", "value": "v"},
        ),
        {
            "chart": "heatmap-chart",
            "data": [{"values": "a", "__values": [1, None]}, {"values": "b", "__values": [None, 2]}],
            "props": {"labelKey": "values", "valuesKey": "__values", "columnLabels": ["x", "y"]},
        },
    ),
    (
        Chart("gauge-arc", [{"p": None}], roles={"percent": "p"}),
        {"chart": "gauge-arc", "props": {"percent": 0}},
    ),
    (
        Chart("gauge-arc", [{"p": " 42 "}], roles={"percent": "p"}),
        {"chart": "gauge-arc", "props": {"percent": 42}},
    ),
]


@pytest.mark.parametrize(
    ("chart", "expected"), EDGES, ids=["matrix-values-column", "first-row-null", "first-row-text"]
)
def test_edges_equal_spec_from_table(chart, expected):
    assert chart.spec == expected


# Issue #2: the catalog's demos pass `demo.options`, and `specFromTable` takes every prop the engine
# knows for the chart, not only the declared options (`names`, `nodes`).
DEMOS = [c for c in silverpoint.catalog["charts"] if c["binding"] != "none"]


def from_demo(chart):
    demo = chart["demo"]
    return Chart(chart["slug"], demo["rows"], roles=demo["roles"], options=demo.get("options"))


@pytest.mark.parametrize("chart", DEMOS, ids=[c["slug"] for c in DEMOS])
def test_every_demo_builds_with_its_options(chart):
    """PY-REQ-001, PY-REQ-004: a demo with `demo.options` is a valid binding."""
    props = from_demo(chart).spec["props"]
    for name, value in (chart["demo"].get("options") or {}).items():
        assert props[name] == value


@pytest.mark.parametrize("slug", ["dumbbell-chart", "slope-chart", "network-chart"])
def test_unknown_prop_is_still_refused(slug):
    """PY-REQ-004: a prop the engine does not know is refused as `specFromTable` refuses it."""
    demo = next(c for c in DEMOS if c["slug"] == slug)["demo"]
    with pytest.raises(SpecError) as raised:
        Chart(slug, demo["rows"], roles=demo["roles"], options={"bogus": 1})
    assert raised.value.kind == "prop"
    assert raised.value.props == ["bogus"]


def test_engine_props_beyond_the_declared_options():
    """PY-REQ-001: undeclared props `specFromTable` accepts (`seed`, `numberFormat`) pass through."""
    chart = Chart(
        "bar-chart",
        [{"a": "x", "b": 1}],
        roles={"x": "a", "value": "b"},
        options={"seed": 3, "number_format": "0.0"},
    )
    assert chart.spec["props"]["seed"] == 3
    assert chart.spec["props"]["numberFormat"] == "0.0"


SPEC_FROM_TABLE = """
const sp = await import(process.argv[1]);
let input = '';
for await (const chunk of process.stdin) input += chunk;
const out = JSON.parse(input).map((b) => sp.specFromTable(b));
process.stdout.write(JSON.stringify(out));
"""


@pytest.mark.node
def test_every_demo_equals_spec_from_table():
    """PY-REQ-001: each demo's spec, with `demo.options`, is the one `specFromTable` returns in Node."""
    import json
    import shutil
    import subprocess

    bindings = [
        {
            "chart": c["slug"],
            "table": {"rows": c["demo"]["rows"]},
            "roles": c["demo"]["roles"],
            "options": c["demo"].get("options") or {},
        }
        for c in DEMOS
    ]
    result = subprocess.run(
        [
            shutil.which("node"),
            "--input-type=module",
            "-e",
            SPEC_FROM_TABLE,
            (VENDOR / "silverpoint-embed.full.mjs").as_uri(),
        ],
        input=json.dumps(bindings),
        capture_output=True,
        text=True,
        check=True,
    )
    for chart, expected in zip(DEMOS, json.loads(result.stdout), strict=True):
        assert expected["ok"], (chart["slug"], expected)
        assert from_demo(chart).spec == expected["value"], chart["slug"]
