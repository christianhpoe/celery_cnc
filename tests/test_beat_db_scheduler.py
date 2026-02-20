# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from celery import Celery

from celery_root.components.beat.db_scheduler import DatabaseScheduler
from celery_root.core.db.models import Schedule


class _FakeDb:
    def __init__(self, schedules: list[Schedule]) -> None:
        self._schedules = schedules
        self.stored: list[Schedule] = []

    def get_schedules(self) -> list[Schedule]:
        return list(self._schedules)

    def store_schedule(self, schedule: Schedule) -> None:
        self.stored.append(schedule)

    def close(self) -> None:
        return None


def _make_app() -> Celery:
    app = Celery("beat-db-tests", broker="memory://", backend="cache+memory://")
    app.conf.timezone = "UTC"
    return app


def test_db_scheduler_filters_by_app() -> None:
    app = _make_app()
    schedules = [
        Schedule(
            schedule_id="s1",
            name="s1",
            task="tasks.a",
            schedule="interval:5",
            args=None,
            kwargs_=None,
            enabled=True,
            app="beat-db-tests",
        ),
        Schedule(
            schedule_id="s2",
            name="s2",
            task="tasks.b",
            schedule="interval:5",
            args=None,
            kwargs_=None,
            enabled=True,
            app="other-app",
        ),
    ]
    scheduler = DatabaseScheduler(app=app, db_client=_FakeDb(schedules))
    scheduler.setup_schedule()
    assert "s1" in scheduler.schedule
    assert "s2" not in scheduler.schedule


def test_db_scheduler_writeback_run_state() -> None:
    app = _make_app()
    schedule = Schedule(
        schedule_id="s1",
        name="s1",
        task="tasks.a",
        schedule="interval:5",
        args=None,
        kwargs_=None,
        enabled=True,
        app="beat-db-tests",
    )
    db = _FakeDb([schedule])
    scheduler = DatabaseScheduler(app=app, db_client=db)
    scheduler.setup_schedule()
    entry = cast("Any", scheduler.schedule["s1"])
    entry.last_run_at = datetime.now(UTC)
    entry.total_run_count = 2
    scheduler.sync()
    assert db.stored
    assert db.stored[-1].schedule_id == "s1"
    assert db.stored[-1].total_run_count == 2
