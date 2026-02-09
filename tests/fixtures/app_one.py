from __future__ import annotations

from celery import Celery

app = Celery(
    "fixture_one",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)


@app.task(name="fixture.add")
def add(a: int, b: int) -> int:
    return a + b
