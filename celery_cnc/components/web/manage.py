"""Django management entrypoint for Celery CnC."""

from __future__ import annotations

import importlib
import os
import sys


def main() -> None:
    """Run Django management commands."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "celery_cnc.components.web.settings")
    management = importlib.import_module("django.core.management")
    execute_from_command_line = management.execute_from_command_line
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
