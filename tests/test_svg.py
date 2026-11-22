"""PY-REQ-009: `to_svg` runs the vendored module build in Node."""

import shutil

import pytest

from silverpoint import Chart, RuntimeUnavailable, svg


@pytest.mark.node
def test_to_svg_is_the_library_render():
    chart = Chart(
        "bar-chart", [{"a": "x", "b": 1}, {"a": "y", "b": 3}], roles={"x": "a", "value": "b"}, id="s1"
    )
    out = chart.to_svg()
    assert out.startswith("<svg") and out.rstrip().endswith("</svg>")
    assert out == svg.call("renderToSVG", chart.spec)["svg"]


def test_without_node(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(RuntimeUnavailable, match="Node"):
        Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"}).to_svg()


def test_configured_runtime(monkeypatch, tmp_path):
    monkeypatch.setenv("SILVERPOINT_NODE", str(tmp_path / "missing-node"))
    with pytest.raises(RuntimeUnavailable, match="SILVERPOINT_NODE"):
        svg.node()
    real = shutil.which("node")
    if real:
        monkeypatch.setenv("SILVERPOINT_NODE", real)
        assert svg.node() == real
