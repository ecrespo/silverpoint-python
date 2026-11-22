from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = "example-only"
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INSTALLED_APPS = ["django.contrib.staticfiles", "silverpoint.contrib.django"]
MIDDLEWARE = ["chartsite.views.csp"]
ROOT_URLCONF = "chartsite.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"]}]
STATIC_URL = "/static/"
