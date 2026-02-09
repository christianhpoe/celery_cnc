"""Logging setup helpers for subprocesses."""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

from celery_cnc.config import get_settings
from celery_cnc.logging.utils import LOG_FORMAT, log_file_path, resolve_log_level

if TYPE_CHECKING:
    from celery_cnc.config import CeleryCnCConfig


def _find_handler(logger: logging.Logger, log_file: Path) -> TimedRotatingFileHandler | None:
    log_path = str(log_file.resolve())
    for handler in logger.handlers:
        if not isinstance(handler, TimedRotatingFileHandler):
            continue
        base = getattr(handler, "baseFilename", None)
        if base is not None and str(base) == log_path:
            return handler
    return None


def configure_process_logging(config: CeleryCnCConfig | None = None, *, component: str | None = None) -> None:
    """Ensure log handlers are configured for the current process."""
    resolved = config or get_settings()
    log_dir = Path(resolved.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_file_path(log_dir, component)
    rotation_hours = int(resolved.log_rotation_hours)
    log_level = resolve_log_level(resolved.log_level)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    handler = _find_handler(root_logger, log_file)
    if handler is None:
        handler = TimedRotatingFileHandler(
            log_file,
            when="h",
            interval=rotation_hours,
            backupCount=7,
        )
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        root_logger.addHandler(handler)
    handler.setLevel(log_level)
