"""Django settings for the Celery CnC web app."""

from __future__ import annotations

import os
from pathlib import Path

from celery_cnc.config import get_settings

BASE_DIR = Path(__file__).resolve().parent
CONFIG = get_settings()

SECRET_KEY = CONFIG.secret_key
DEBUG = CONFIG.web_debug
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
]

ROOT_URLCONF = "celery_cnc.web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "celery_cnc.web.wsgi.application"
ASGI_APPLICATION = "celery_cnc.web.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "db.sqlite3"),
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [str(BASE_DIR / "static")]

CELERY_CNC_DB_PATH = Path(CONFIG.db_path)
CELERY_CNC_LOG_DIR = Path(CONFIG.log_dir)
CELERY_CNC_RETENTION_DAYS = int(CONFIG.retention_days)


def _parse_worker_paths(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


CELERY_CNC_WORKERS = _parse_worker_paths(os.getenv("CELERY_CNC_WORKERS"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
