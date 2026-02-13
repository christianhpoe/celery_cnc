"""ASGI config for the Celery Root Django app."""

from __future__ import annotations

import os

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "celery_root.components.web.settings")

django_application = get_asgi_application()
application = ASGIStaticFilesHandler(django_application)
