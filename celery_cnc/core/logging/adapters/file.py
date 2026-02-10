"""File-based logging controller."""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler

from celery_cnc.config import CeleryCnCConfig, LoggingConfigFile
from celery_cnc.core.logging.adapters.base import BaseLogController
from celery_cnc.core.logging.utils import LOG_FORMAT, log_file_path, resolve_log_level

_NOT_CONFIGURED_ERROR = "FileLogController.configure() must be called first"


class FileLogController(BaseLogController):
    """File-based log controller with daily rotation."""

    def __init__(self) -> None:
        """Initialize an unconfigured file log controller."""
        self._configured = False
        self._config: LoggingConfigFile | None = None
        self._handlers: dict[str, logging.Handler] = {}
        self._log_level = logging.INFO

    def configure(self, config: CeleryCnCConfig | LoggingConfigFile) -> None:
        """Configure log handlers based on the provided config."""
        log_config = config.logging if isinstance(config, CeleryCnCConfig) else config
        log_dir = log_config.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_level = resolve_log_level(log_config.log_level)

        self._config = log_config
        self._configured = True

    def get_logger(self, name: str) -> logging.Logger:
        """Return a configured logger instance."""
        if not self._configured or self._config is None:
            raise RuntimeError(_NOT_CONFIGURED_ERROR)
        logger = logging.getLogger(name)
        logger.setLevel(self._log_level)
        self._attach_handlers(logger)
        return logger

    def shutdown(self) -> None:
        """Flush and close all handlers."""
        for handler in self._handlers.values():
            handler.flush()
            handler.close()

    def _attach_handlers(self, logger: logging.Logger) -> None:
        if self._config is None:
            return
        handler = self._handlers.get(logger.name)
        if handler is None:
            log_file = log_file_path(self._config.log_dir, logger.name)
            handler = TimedRotatingFileHandler(
                log_file,
                when="h",
                interval=self._config.log_rotation_hours,
                backupCount=7,
            )
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
            handler.setLevel(self._log_level)
            self._handlers[logger.name] = handler
        if handler not in logger.handlers:
            logger.addHandler(handler)
