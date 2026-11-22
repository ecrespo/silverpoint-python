"""PY-REQ-007, PY-REQ-013 (PY-T-09, PY-T-11, PY-T-12): real Chromium.

- the Flask and Django markup draws under ``script-src 'self'; style-src 'self'`` with no violation;
- a notebook output (the sandboxed srcdoc frame) draws, and the chart reads by keyboard.

Skipped when Playwright's Chromium is not installed (``uv run playwright install chromium``); a
browser elsewhere is used through ``SP_CHROMIUM=/path/to/chrome``.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sync_api = pytest.importorskip("playwright.sync_api")

from silverpoint import Chart  # noqa: E402
from silverpoint.contrib import _markup  # noqa: E402
from silverpoint.html import script_text  # noqa: E402

pytestmark = pytest.mark.browser
CSP = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:"
ROWS = [{"team": "A", "wins": 12}, {"team": "B", "wins": 9}, {"team": "C", "wins": 15}]


@pytest.fixture(scope="module")
def browser() -> Iterator:
    with sync_api.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(executable_path=os.environ.get("SP_CHROMIUM") or None)
        except Exception as error:
            pytest.skip(f"no Chromium: {str(error).splitlines()[0]}")
        yield browser
        browser.close()


def serve(pages: dict[str, tuple[str, str]], csp: str | None = CSP) -> tuple[ThreadingHTTPServer, str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = self.path.split("?")[0]
            if path == "/favicon.ico":
                self.send_response(204)
                self.end_headers()
                return
            if path not in pages:
                self.send_error(404)
                return
            kind, body = pages[path]
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", kind)
            if csp:
                self.send_header("Content-Security-Policy", csp)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def framework_page(script_url: str) -> str:
    chart = Chart("bar-chart", ROWS, roles={"x": "team", "value": "wins"}, options={"title": "Wins"}, id="w")
    head = _markup.script(script_url)
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>t</title>{head}</head><body>{_markup.chart(chart)}</body></html>"


def watch(page) -> list[str]:
    problems: list[str] = []
    page.on(
        "console",
        lambda m: (
            problems.append(m.text) if m.type == "error" or "Content Security Policy" in m.text else None
        ),
    )
    page.on("pageerror", lambda e: problems.append(str(e)))
    return problems


@pytest.mark.parametrize("framework", ["flask", "django"])
def test_markup_draws_under_a_strict_csp(browser, framework):
    url = (
        "/_silverpoint/silverpoint-embed.full.js"
        if framework == "flask"
        else "/static/silverpoint/silverpoint-embed.full.js"
    )
    server, base = serve({"/": ("text/html", framework_page(url)), url: ("text/javascript", script_text())})
    try:
        page = browser.new_page()
        problems = watch(page)
        page.goto(base + "/")
        page.wait_for_selector("silverpoint-chart .sp-root svg.sp-chart", timeout=10_000)
        assert page.locator("silverpoint-chart svg.sp-chart").count() == 1
        assert problems == []
        page.close()
    finally:
        server.shutdown()


def test_notebook_frame_draws_and_reads_by_keyboard(browser):
    from silverpoint import notebook

    notebook.disable()
    chart = Chart(
        "bar-chart",
        ROWS,
        roles={"x": "team", "value": "wins"},
        options={"title": "Wins"},
        width=480,
        height=260,
    )
    output = chart._repr_mimebundle_()["text/html"]
    # A notebook's own page: the output cell's HTML placed as the front end places it. A srcdoc frame
    # inherits its parent's CSP, and notebook front ends set none that forbids inline script.
    page_html = f"<!doctype html><html lang='en'><head><title>nb</title></head><body>{output}</body></html>"
    server, base = serve({"/": ("text/html", page_html)}, csp=None)
    try:
        page = browser.new_page()
        problems = watch(page)
        page.goto(base + "/")
        frame = page.frame_locator("iframe")
        root = frame.locator(".sp-root")
        root.locator("svg.sp-chart").wait_for(timeout=10_000)
        root.focus()
        live = frame.locator(".sp-live")
        sync_api.expect(live).not_to_have_text("")
        first = live.text_content()
        page.keyboard.press("ArrowRight")
        sync_api.expect(live).not_to_have_text(first or "")
        assert problems == []
        page.close()
    finally:
        server.shutdown()
