from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import django
import pytest
from django.test import Client

from celery_cnc.config import reset_settings
from celery_cnc.db.models import Schedule, TaskEvent, WorkerEvent
from celery_cnc.db.sqlite import SQLiteController


@pytest.fixture(scope="session")
def web_client(tmp_path_factory: pytest.TempPathFactory) -> Client:
    db_path = tmp_path_factory.mktemp("celery_cnc") / "celery_cnc.db"
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "celery_cnc.web.settings")
    os.environ["CELERY_CNC_DB_PATH"] = str(db_path)
    reset_settings()

    if not django.apps.apps.ready:
        django.setup()

    _seed_db(db_path)
    return Client()


if TYPE_CHECKING:
    from pathlib import Path


def _seed_db(path: Path) -> None:
    db = SQLiteController(path)
    db.initialize()
    now = datetime.now(UTC)
    db.store_task_event(
        TaskEvent(
            task_id="task-0001",
            name="demo.task",
            state="SUCCESS",
            timestamp=now,
            worker="alpha",
            args="[]",
            kwargs="{}",
            result="ok",
        ),
    )
    db.store_worker_event(
        WorkerEvent(
            hostname="alpha",
            event="worker-online",
            timestamp=now,
            info={"pool": {"max-concurrency": 4}, "active": []},
        ),
    )
    db.store_schedule(
        Schedule(
            schedule_id="sched-1",
            name="demo schedule",
            task="demo.task",
            schedule="*/5 * * * *",
            args="[]",
            kwargs="{}",
            enabled=True,
            last_run_at=now,
            total_run_count=1,
        ),
    )
    db.close()


def test_dashboard_renders(web_client: Client) -> None:
    response = web_client.get("/")
    assert response.status_code == 200
    assert b"Dashboard" in response.content


def test_tasks_list_renders(web_client: Client) -> None:
    response = web_client.get("/tasks/")
    assert response.status_code == 200
    assert b"Task queue" in response.content


def test_task_detail_renders(web_client: Client) -> None:
    response = web_client.get("/tasks/task-0001/")
    assert response.status_code == 200
    assert b"Task lookup" in response.content


def test_task_graph_renders(web_client: Client) -> None:
    response = web_client.get("/tasks/task-0001/graph/")
    assert response.status_code == 200
    assert b"Task graph" in response.content


def test_workers_list_renders(web_client: Client) -> None:
    response = web_client.get("/workers/")
    assert response.status_code == 200
    assert b"Brokers & workers" in response.content


def test_worker_detail_renders(web_client: Client) -> None:
    response = web_client.get("/workers/alpha/")
    assert response.status_code == 200
    assert b"Worker detail" in response.content


def test_broker_page_renders(web_client: Client) -> None:
    response = web_client.get("/broker/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/workers/"


def test_beat_page_renders(web_client: Client) -> None:
    response = web_client.get("/beat/")
    assert response.status_code == 200
    assert b"Periodic tasks" in response.content


def test_api_tasks_list(web_client: Client) -> None:
    response = web_client.get("/api/tasks/")
    assert response.status_code == 200
    assert response.json()["tasks"]


def test_api_task_detail(web_client: Client) -> None:
    response = web_client.get("/api/tasks/task-0001/")
    assert response.status_code == 200
    assert response.json()["task_id"] == "task-0001"


def test_api_task_relations(web_client: Client) -> None:
    response = web_client.get("/api/tasks/task-0001/relations/")
    assert response.status_code == 200
    assert "relations" in response.json()


def test_api_task_graph_snapshot(web_client: Client) -> None:
    response = web_client.get("/api/tasks/task-0001/graph/")
    assert response.status_code == 200
    payload = response.json()
    assert "meta" in payload
    assert "nodes" in payload
    assert "edges" in payload


def test_api_task_graph_updates(web_client: Client) -> None:
    response = web_client.get("/api/tasks/task-0001/graph/updates/")
    assert response.status_code == 200
    payload = response.json()
    assert "generated_at" in payload
    assert "node_updates" in payload
    assert "meta_counts" in payload


def test_api_workers(web_client: Client) -> None:
    response = web_client.get("/api/workers/")
    assert response.status_code == 200
    assert response.json()["workers"]
