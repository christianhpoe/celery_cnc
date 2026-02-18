# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

"""Queue-based logging helpers for multiprocessing."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue

DEFAULT_LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"


@dataclass(frozen=True, slots=True)
class LogQueueConfig:
    """Configuration for log forwarding from subprocesses."""

    queue: Queue[object]
    level: int


@dataclass(slots=True)
class LogQueueRuntime:
    """Runtime logging state for the parent process."""

    logger: logging.Logger
    config: LogQueueConfig
    listener: QueueListener

    def start(self) -> None:
        """Start forwarding records from subprocesses."""
        self.listener.start()

    def stop(self) -> None:
        """Stop forwarding records from subprocesses."""
        self.listener.stop()


def create_log_runtime(logger: logging.Logger | None) -> LogQueueRuntime:
    """Configure the base logger and build a queue listener."""
    base_logger = _ensure_base_logger(logger)
    handlers = _collect_handlers(base_logger)
    if not handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
        base_logger.addHandler(handler)
        handlers = [handler]
    queue: Queue[object] = Queue()
    listener = QueueListener(queue, *handlers, respect_handler_level=True)
    level = base_logger.getEffectiveLevel()
    return LogQueueRuntime(base_logger, LogQueueConfig(queue=queue, level=level), listener)


def configure_subprocess_logging(config: LogQueueConfig | None) -> None:
    """Configure logging inside a subprocess to forward to the parent."""
    if config is None:
        return
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    root_logger.setLevel(config.level)
    root_logger.addHandler(QueueHandler(config.queue))

    celery_logger = logging.getLogger("celery_root")
    for handler in list(celery_logger.handlers):
        celery_logger.removeHandler(handler)
    celery_logger.setLevel(logging.NOTSET)
    celery_logger.propagate = True


def log_level_name(level: int | None) -> str:
    """Return a lowercase log level name suitable for external configs."""
    if level is None:
        return "info"
    name = logging.getLevelName(level)
    if isinstance(name, str) and name.isalpha():
        return name.lower()
    return "info"


def _ensure_base_logger(logger: logging.Logger | None) -> logging.Logger:
    if logger is None:
        base_logger = logging.getLogger("celery_root")
        if not base_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
            base_logger.addHandler(handler)
        if base_logger.level == logging.NOTSET:
            base_logger.setLevel(logging.INFO)
        base_logger.propagate = False
        return base_logger

    if logger.name.startswith("celery_root"):
        return logger

    base_logger = logging.getLogger("celery_root")
    handlers = _collect_handlers(logger)
    for attached_handler in handlers:
        if attached_handler not in base_logger.handlers:
            base_logger.addHandler(attached_handler)
    for filt in logger.filters:
        if filt not in base_logger.filters:
            base_logger.addFilter(filt)
    if base_logger.level == logging.NOTSET:
        base_logger.setLevel(logger.getEffectiveLevel())
    base_logger.propagate = False
    return base_logger


def _collect_handlers(logger: logging.Logger) -> list[logging.Handler]:
    handlers: list[logging.Handler] = []
    seen: set[int] = set()
    current: logging.Logger | None = logger
    while current is not None:
        for handler in current.handlers:
            if isinstance(handler, QueueHandler):
                continue
            handler_id = id(handler)
            if handler_id in seen:
                continue
            seen.add(handler_id)
            handlers.append(handler)
        if not current.propagate:
            break
        current = current.parent
    return handlers
