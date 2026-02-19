# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from datetime import UTC, datetime

from celery import Celery

from celery_root.components.beat import BeatController
from celery_root.core.db.adapters.base import BaseDBController
from celery_root.core.db.models import (
    BrokerQueueEvent,
    Schedule,
    Task,
    TaskEvent,
    TaskFilter,
    TaskRelation,
    TaskStats,
    ThroughputBucket,
    TimeRange,
    Worker,
    WorkerEvent,
)


class FakeDB(BaseDBController):
    def __init__(self) -> None:
        self.stored: list[Schedule] = []

    def initialize(self) -> None: ...

    def get_schema_version(self) -> int:
        return 1

    def ensure_schema(self) -> None: ...

    def migrate(self, _from_version: int, _to_version: int) -> None: ...

    def store_task_event(self, _event: TaskEvent) -> None: ...

    def get_tasks(self, _filters: TaskFilter | None = None) -> list[Task]:
        return []

    def get_tasks_page(
        self,
        _filters: TaskFilter | None,
        *,
        sort_key: str | None,
        sort_dir: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        _ = (sort_key, sort_dir, limit, offset)
        return [], 0

    def list_task_names(self) -> list[str]:
        return []

    def get_task(self, _task_id: str) -> Task | None:
        return None

    def store_task_relation(self, _relation: TaskRelation) -> None: ...

    def get_task_relations(self, _root_id: str) -> list[TaskRelation]:
        return []

    def store_worker_event(self, _event: WorkerEvent) -> None: ...

    def store_broker_queue_event(self, _event: BrokerQueueEvent) -> None: ...

    def get_broker_queue_snapshot(self, _broker_url: str) -> list[BrokerQueueEvent]:
        return []

    def get_workers(self) -> list[Worker]:
        return []

    def get_worker(self, _hostname: str) -> Worker | None:
        return None

    def get_worker_event_snapshot(self, _hostname: str) -> WorkerEvent | None:
        return None

    def get_task_stats(self, _task_name: str | None, _time_range: TimeRange | None) -> TaskStats:
        return TaskStats()

    def get_throughput(self, _time_range: TimeRange, _bucket_seconds: int) -> list[ThroughputBucket]:
        return []

    def get_state_distribution(self) -> dict[str, int]:
        return {}

    def get_heatmap(self, _time_range: TimeRange | None) -> list[list[int]]:
        return []

    def get_schedules(self) -> list[Schedule]:
        return list(self.stored)

    def store_schedule(self, schedule: Schedule) -> None:
        self.stored = [item for item in self.stored if item.schedule_id != schedule.schedule_id]
        self.stored.append(schedule)

    def delete_schedule(self, schedule_id: str) -> None:
        self.stored = [s for s in self.stored if s.schedule_id != schedule_id]

    def cleanup(self, _older_than_days: int) -> int:
        return 0

    def close(self) -> None: ...


def test_db_backend_list_save_delete() -> None:
    app = Celery("beat-tests", broker="memory://", backend="cache+memory://")
    app.conf.beat_scheduler = "celery_root.components.beat.db_scheduler:DatabaseScheduler"
    db = FakeDB()
    controller = BeatController(app, db)

    assert controller.list_schedules() == []

    new_schedule = Schedule(
        schedule_id="heartbeat",
        name="heartbeat",
        task="tasks.heartbeat",
        schedule="interval:30",
        args="[]",
        kwargs_="{}",
        enabled=True,
        last_run_at=datetime.now(UTC),
        total_run_count=0,
    )
    controller.save_schedule(new_schedule)

    updated = controller.list_schedules()
    assert any(entry.schedule_id == "heartbeat" for entry in updated)
    assert db.get_schedules()[0].app == "beat-tests"

    controller.delete_schedule("heartbeat")
    final = controller.list_schedules()
    assert not any(entry.schedule_id == "heartbeat" for entry in final)
