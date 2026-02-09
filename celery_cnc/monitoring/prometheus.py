"""Prometheus exporter for Celery CnC metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, start_http_server

from .abc import BaseMonitoringExporter

if TYPE_CHECKING:
    from celery_cnc.db.models import TaskEvent, TaskStats, WorkerEvent

__all__ = ["PrometheusExporter"]


class PrometheusExporter(BaseMonitoringExporter):
    """Prometheus exporter capturing task and worker metrics."""

    def __init__(self, *, port: int | None = None, registry: CollectorRegistry | None = None) -> None:
        """Initialize metrics and optionally start the HTTP server."""
        self.registry = registry or CollectorRegistry()
        self._task_counter = Counter(
            "celery_cnc_tasks_total",
            "Total tasks by state, worker, and name",
            ("state", "worker", "name"),
            registry=self.registry,
        )
        self._runtime = Histogram(
            "celery_cnc_task_runtime_seconds",
            "Observed task runtimes",
            registry=self.registry,
            buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
        )
        self._worker_gauge = Gauge(
            "celery_cnc_workers",
            "Worker online/offline counts",
            ("state",),
            registry=self.registry,
        )
        self._runtime_min = Gauge("celery_cnc_task_runtime_min_seconds", "Min runtime", registry=self.registry)
        self._runtime_max = Gauge("celery_cnc_task_runtime_max_seconds", "Max runtime", registry=self.registry)
        self._runtime_avg = Gauge("celery_cnc_task_runtime_avg_seconds", "Avg runtime", registry=self.registry)
        self._runtime_p95 = Gauge("celery_cnc_task_runtime_p95_seconds", "p95 runtime", registry=self.registry)
        self._runtime_p99 = Gauge("celery_cnc_task_runtime_p99_seconds", "p99 runtime", registry=self.registry)

        self._started_server = False
        if port is not None:
            start_http_server(port, registry=self.registry)
            self._started_server = True

    def on_task_event(self, event: TaskEvent) -> None:
        """Update metrics for a task event."""
        worker = event.worker or "unknown"
        name = event.name or "unknown"
        self._task_counter.labels(event.state, worker, name).inc()
        if event.runtime is not None:
            self._runtime.observe(event.runtime)

    def on_worker_event(self, event: WorkerEvent) -> None:
        """Update metrics for a worker event."""
        state = event.event
        if state not in {"online", "offline"}:
            state = "other"
        self._worker_gauge.labels(state).inc()

    def update_stats(self, stats: TaskStats) -> None:
        """Update runtime gauges from task statistics."""
        if stats.min_runtime is not None:
            self._runtime_min.set(stats.min_runtime)
        if stats.max_runtime is not None:
            self._runtime_max.set(stats.max_runtime)
        if stats.avg_runtime is not None:
            self._runtime_avg.set(stats.avg_runtime)
        if stats.p95 is not None:
            self._runtime_p95.set(stats.p95)
        if stats.p99 is not None:
            self._runtime_p99.set(stats.p99)

    def serve(self) -> None:
        """Start the HTTP server if not already running."""
        if not self._started_server:
            start_http_server(8001, registry=self.registry)
            self._started_server = True

    def shutdown(self) -> None:
        """Shutdown hook for API parity (noop)."""
        return
