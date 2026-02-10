"""Shared runtime context passed to components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import logging
    from collections.abc import Callable

    from celery_cnc.config import CeleryCnCConfig
    from celery_cnc.core.db.adapters.base import BaseDBController
    from celery_cnc.core.registry import WorkerRegistry


@dataclass(slots=True)
class ComponentContext:
    """Runtime context shared with components."""

    config: CeleryCnCConfig
    registry: WorkerRegistry
    db_factory: Callable[[], BaseDBController]
    logger: logging.Logger
