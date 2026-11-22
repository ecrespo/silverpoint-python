"""Charts in notebooks (PY-REQ-007, PY-REQ-008, PY-DD-04).

By default each chart is a sandboxed ``<iframe srcdoc>`` holding the inline document: it draws the same
in Jupyter, JupyterLab, VS Code and Databricks, needs no trusted notebook, and keeps the chart's
stylesheet off the notebook's. ``enable()`` instead shows the script once and writes each chart as a
``<silverpoint-chart>``, for front ends that run scripts in outputs and share one page.
"""

from __future__ import annotations

import html as _html
import os
import warnings
from typing import TYPE_CHECKING, Any

from . import html

if TYPE_CHECKING:
    from .chart import Chart

_state = {"shared": False}
_FRAME_PAD = 16  # the srcdoc body's default 8 px margin on each side


def enable(display: bool = True) -> str:
    """Show the script once in this notebook; later charts reuse it. Returns the markup shown.

    In Databricks each output is its own frame, so a shared script would reach no chart: there this
    warns and leaves one frame per chart (PY-REQ-008, delta-001).
    """
    markup = html.script_tag("inline")
    if os.environ.get("DATABRICKS_RUNTIME_VERSION"):
        warnings.warn(
            "silverpoint.notebook.enable() has no effect in Databricks: each output is its own frame, "
            "so every chart keeps its own copy of the script.",
            RuntimeWarning,
            stacklevel=2,
        )
        return markup
    _state["shared"] = True
    if display:
        try:
            from IPython.display import HTML
            from IPython.display import display as show
        except ImportError:  # pragma: no cover - only outside IPython
            pass
        else:
            show(HTML(markup))
    return markup


def disable() -> None:
    """Back to one sandboxed frame per chart."""
    _state["shared"] = False


def frame(chart: Chart) -> str:
    width, height = chart.size
    document = chart.to_html(full_document=True, script="inline", render="client")
    return (
        f'<iframe srcdoc="{_html.escape(document, quote=True)}" sandbox="allow-scripts" '
        f'width="{int(width) + _FRAME_PAD}" height="{int(height) + _FRAME_PAD}" '
        f'style="border:0;max-width:100%" title="{_html.escape(chart.name, quote=True)}" loading="lazy"></iframe>'
    )


def markup(chart: Chart) -> str:
    if _state["shared"]:
        return html.element(chart.spec)
    return frame(chart)


def display(chart: Chart, **kwargs: Any) -> None:  # pragma: no cover - IPython glue
    from IPython.display import HTML
    from IPython.display import display as show

    show(HTML(markup(chart)), **kwargs)
