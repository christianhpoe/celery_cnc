"""Public package entrypoints for Celery CnC."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import TYPE_CHECKING

from .config import CeleryCnCConfig, get_settings, set_settings
from .core.process_manager import ProcessManager
from .core.registry import WorkerRegistry
from .db.abc import BaseDBController
from .db.memory import MemoryController
from .db.sqlite import SQLiteController

if TYPE_CHECKING:
    from collections.abc import Callable

    from celery import Celery


_RETENTION_ARG_POSITIVE_ERROR = "retention_days must be positive"


class CeleryCnC:
    """Bootstrap class for Celery Command & Control."""

    def __init__(
        self,
        *workers: Celery | str,
        config: CeleryCnCConfig | None = None,
        db_controller: BaseDBController | Callable[[], BaseDBController] | None = None,
        purge_db: bool | None = None,
        retention_days: int | None = None,
    ) -> None:
        """Initialize the CnC service with worker targets and configuration."""
        if config is None:
            config = get_settings()
        if retention_days is not None:
            if retention_days <= 0:
                raise ValueError(_RETENTION_ARG_POSITIVE_ERROR)
            config = config.model_copy(update={"retention_days": retention_days})
        if purge_db is not None:
            config = config.model_copy(update={"purge_db": purge_db})

        set_settings(config)
        self.config = config
        self.registry = WorkerRegistry(workers)
        self._db_controller = db_controller
        self._process_manager: ProcessManager | None = None
        self._ensure_sqlite_db_path()
        if self.config.purge_db:
            self._purge_existing_db()

    def run(self) -> None:
        """Start all subprocesses and block until shutdown."""
        controller_factory = self._resolve_db_controller_factory()
        manager = ProcessManager(self.registry, self.config, controller_factory)
        self._process_manager = manager
        manager.run()

    def _resolve_db_controller_factory(self) -> Callable[[], BaseDBController]:
        if self._db_controller is not None and callable(self._db_controller):
            return self._db_controller
        if isinstance(self._db_controller, SQLiteController):
            path = getattr(self._db_controller, "_path", self.config.db_path)
            return functools.partial(_make_sqlite_controller, path)
        if isinstance(self._db_controller, MemoryController):
            return functools.partial(_return_controller, self._db_controller)
        if isinstance(self._db_controller, BaseDBController):
            controller = self._db_controller
            return functools.partial(_return_controller, controller)
        return functools.partial(_make_sqlite_controller, self.config.db_path)

    def _ensure_sqlite_db_path(self) -> None:
        controller = self._db_controller
        if controller is not None:
            if isinstance(controller, SQLiteController):
                raw_path = getattr(controller, "_path", None)
                if raw_path is not None:
                    self.config.db_path = Path(raw_path).expanduser().resolve()
                return
            if isinstance(controller, BaseDBController) or callable(controller):
                return

        path = Path(self.config.db_path).expanduser()
        path = (Path.cwd() / path).resolve() if not path.is_absolute() else path.resolve()
        self.config.db_path = path

    def _purge_existing_db(self) -> None:
        path = self._resolve_purge_path()
        if path is None:
            return
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            return
        if resolved.is_dir():
            msg = f"SQLite database path points to a directory: {resolved}"
            raise RuntimeError(msg)
        try:
            resolved.unlink()
        except OSError as exc:  # pragma: no cover - depends on OS permissions
            msg = f"Failed to purge SQLite database at {resolved}: {exc}"
            raise RuntimeError(msg) from exc

    def _resolve_purge_path(self) -> Path | None:
        controller = self._db_controller
        if controller is None:
            return self.config.db_path
        if isinstance(controller, SQLiteController):
            raw_path = getattr(controller, "_path", None)
            return Path(raw_path) if raw_path is not None else self.config.db_path
        return None


def _make_sqlite_controller(path: Path) -> BaseDBController:
    """Create a SQLite controller; multiprocessing-safe factory."""
    return SQLiteController(path)


def _return_controller(controller: BaseDBController) -> BaseDBController:
    """Return the provided controller instance."""
    return controller


__all__ = ["CeleryCnC", "CeleryCnCConfig", "CnCConfig"]
