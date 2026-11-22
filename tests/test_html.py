"""PY-REQ-006, PY-REQ-014: the markup and the escaping, against the library's goldens and hostile corpus."""

import json

import pytest
from conftest import FIXTURES, VENDOR, load

from silverpoint import Chart
from silverpoint.html import escape_json_for_script, js_json

HOSTILE = load(FIXTURES / "hostile-expected.json")
GOLDENS = load(VENDOR / "html-goldens" / "cases.json")


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_escape_matches_the_library_over_the_hostile_corpus(name):
    expected = HOSTILE[name]
    if isinstance(expected, dict):
        pytest.skip("the library refuses this spec")
    spec = load(FIXTURES / "hostile" / name)
    assert escape_json_for_script(spec) == expected


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (1.0, "1"),
        (2.5, "2.5"),
        (1e21, "1e+21"),
        (1e20, "100000000000000000000"),
        (1e-7, "1e-7"),
        (0.000001, "0.000001"),
        (-0.0, "0"),
        (float("nan"), "null"),
        (True, "true"),
        (None, "null"),
        ("é ", '"é "'),
        ("\x01\n", '"\\u0001\\n"'),
        (123456789012, "123456789012"),
        (0.1 + 0.2, "0.30000000000000004"),
    ],
)
def test_numbers_and_strings_as_json_stringify(value, text):
    assert js_json(value) == text


def test_spec_is_stringified_in_insertion_order():
    assert js_json({"b": 1, "a": [1, {"c": None}]}) == '{"b":1,"a":[1,{"c":null}]}'


@pytest.mark.node
@pytest.mark.parametrize("case", GOLDENS, ids=[c["file"] for c in GOLDENS])
def test_server_rendered_html_is_the_golden(case):
    chart = Chart.from_spec(case["spec"])
    options = case["options"]
    html = chart.render_html(**options)
    assert html == (VENDOR / "html-goldens" / case["file"]).read_text(encoding="utf-8")


def test_client_document_without_node():
    chart = Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"}, id="c1")
    html = chart.to_html(full_document=True, script="none", render="client")
    assert html.startswith('<!doctype html><html lang="en"><head><meta charset="utf-8">')
    assert '<div data-sp-embed><script type="application/json">' + escape_json_for_script(chart.spec) in html
    assert "<svg" not in html


def test_client_document_inlines_the_script_once():
    chart = Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"})
    html = chart.to_html(script="inline", render="client")
    code = (VENDOR / "silverpoint-embed.full.js").read_text(encoding="utf-8")
    assert html.count("</script>") == 2  # the JSON child and the one inline script; none inside the code
    assert len(html) > len(code)
    assert html.endswith("</script></body></html>")


def test_script_url_is_an_attribute():
    chart = Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"})
    html = chart.to_html(script='/static/sp.js?"x', render="client")
    assert '<script src="/static/sp.js?&quot;x"></script>' in html


def test_fragment_is_one_box():
    chart = Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"})
    html = chart.to_html(full_document=False, render="client")
    assert html.startswith("<div data-sp-embed>") and html.endswith("</div>")


def test_no_cdn_url_anywhere():
    chart = Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"})
    for script in ("inline", "none"):
        html = chart.to_html(script=script, render="client")
        assert 'src="http' not in html and "src='http" not in html and "//cdn" not in html


def test_to_json_round_trips():
    chart = Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"})
    assert json.loads(chart.to_json()) == chart.spec
