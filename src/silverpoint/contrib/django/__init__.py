"""Django: add ``"silverpoint.contrib.django"`` to ``INSTALLED_APPS`` (PY-REQ-012).

    {% load silverpoint %}
    {% silverpoint_script %}              the vendored script through ``staticfiles``, with its integrity
    {% silverpoint_chart chart %}         a <silverpoint-chart> with its spec in a JSON child

``staticfiles`` serves the script from ``silverpoint/silverpoint-embed.full.js``; with a hashed storage
(``ManifestStaticFilesStorage``) the URL changes with each version, so it can be cached for good.
"""

default_app_config = "silverpoint.contrib.django.apps.SilverpointConfig"
