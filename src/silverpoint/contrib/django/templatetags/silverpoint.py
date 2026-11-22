from __future__ import annotations

from typing import Any

from django import template
from django.templatetags.static import static
from django.utils.safestring import SafeString, mark_safe

from ... import _markup

register = template.Library()


@register.simple_tag
def silverpoint_script() -> SafeString:
    return mark_safe(_markup.script(static(f"silverpoint/{_markup.SCRIPT}")))


@register.simple_tag
def silverpoint_chart(chart: Any) -> SafeString:
    return mark_safe(_markup.chart(chart))
