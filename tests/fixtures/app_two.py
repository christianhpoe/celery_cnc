from __future__ import annotations

from celery import Celery

app = Celery(
    "fixture_two",
    broker="redis://localhost:6379/2",
    backend="redis://localhost:6379/3",
)


@app.task(name="fixture.mul")
def mul(a: int, b: int) -> int:
    return a * b
