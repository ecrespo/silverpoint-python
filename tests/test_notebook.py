"""PY-REQ-007, PY-REQ-008: notebooks show a sandboxed frame, or a shared script once enabled."""

import html as htmllib
import re

from silverpoint import Chart, notebook


def chart():
    return Chart("bar-chart", [{"a": "x", "b": 1}], roles={"x": "a", "value": "b"}, width=500, height=280)


def test_mimebundle_is_a_sandboxed_srcdoc_frame():
    notebook.disable()
    bundle = chart()._repr_mimebundle_()
    frame = bundle["text/html"]
    assert frame.startswith("<iframe ")
    assert 'sandbox="allow-scripts"' in frame
    assert "allow-same-origin" not in frame
    src = re.search(r'srcdoc="([^"]*)"', frame).group(1)
    document = htmllib.unescape(src)
    assert document.startswith("<!doctype html>")
    assert "<script>" in document and "data-sp-embed" in document
    assert 'width="516"' in frame and 'height="296"' in frame
    assert bundle["application/json"] == chart().spec


def test_enable_shares_the_script():
    first = notebook.enable(display=False)
    assert first.startswith("<script>") and first.count("</script>") == 1
    bundle = chart()._repr_mimebundle_()
    assert bundle["text/html"].startswith("<silverpoint-chart")
    assert "<iframe" not in bundle["text/html"]
    notebook.disable()
    assert chart()._repr_mimebundle_()["text/html"].startswith("<iframe ")


def test_enable_in_databricks_warns_and_keeps_frames(monkeypatch):
    """PY-REQ-008 (delta-001): each Databricks output is its own frame, so nothing can be shared."""
    import pytest

    monkeypatch.setenv("DATABRICKS_RUNTIME_VERSION", "17.3")
    with pytest.warns(RuntimeWarning, match="Databricks"):
        notebook.enable(display=False)
    assert chart()._repr_mimebundle_()["text/html"].startswith("<iframe ")
    notebook.disable()


def test_frame_sizes_fit_databricks_cell_limits():
    """PY-REQ-018 (delta-001): under 1 MB at 100 rows, under 10 MB at SPARK_ROW_LIMIT rows."""
    from silverpoint.data import SPARK_ROW_LIMIT

    def size(n):
        rows = [{"x": i, "y": i * 0.731 + 0.123456789} for i in range(n)]
        return len(
            Chart("line-chart", rows, roles={"x": "x", "value": "y"})
            ._repr_mimebundle_()["text/html"]
            .encode()
        )

    assert size(100) < 1_000_000
    assert size(SPARK_ROW_LIMIT) < 10_000_000
