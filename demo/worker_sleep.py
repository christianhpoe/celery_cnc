"""Celery worker with a random sleep task."""

from __future__ import annotations

import random
import time

from .common import create_celery_app

app = create_celery_app(
    "demo_sleep",
    queue="sleep",
    broker_url="redis://localhost:6381/0",
    backend_url="db+postgresql://postgres:postgres@localhost:5432/postgres",
)


@app.task(name="sleep.hello", rate_limit="1/m")
def sleep_then_hello(min_seconds: float = 0.5, max_seconds: float = 2.0) -> str:
    """Sleep for a random duration and return hello world."""
    if min_seconds < 0 or max_seconds < 0:
        message = "sleep bounds must be non-negative"
        raise ValueError(message)
    if max_seconds < min_seconds:
        message = "max_seconds must be >= min_seconds"
        raise ValueError(message)
    duration = random.uniform(min_seconds, max_seconds)  # noqa: S311
    time.sleep(duration)
    return "hello world"
