"""PY-REQ-012: the Django app's template tags equal the Flask globals."""

import pytest

django = pytest.importorskip("django")
from django.conf import settings  # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=["django.contrib.staticfiles", "silverpoint.contrib.django"],
        STATIC_URL="/static/",
        TEMPLATES=[{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}],
    )
    django.setup()

from django.contrib.staticfiles import finders  # noqa: E402
from django.template import engines  # noqa: E402

from silverpoint import Chart  # noqa: E402


def render(source, **context):
    return engines["django"].from_string(source).render(context)


def test_staticfiles_finds_the_script():
    assert finders.find("silverpoint/silverpoint-embed.full.js")


def test_tags():
    chart = Chart("bar-chart", [{"a": "<x>", "b": 1}], roles={"x": "a", "value": "b"})
    out = render("{% load silverpoint %}{% silverpoint_script %}{% silverpoint_chart chart %}", chart=chart)
    assert '<script src="/static/silverpoint/silverpoint-embed.full.js" integrity="sha384-' in out
    assert '<silverpoint-chart><script type="application/json">' in out
    assert "\\u003cx\\u003e" in out
    assert "<script>" not in out
