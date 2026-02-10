"""OpenTelemetry exporter for Celery CnC events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from celery_cnc.components.metrics.base import BaseMonitoringExporter

if TYPE_CHECKING:
    from celery_cnc.core.db.models import TaskEvent, TaskStats, WorkerEvent

__all__ = ["OTelExporter"]


class OTelExporter(BaseMonitoringExporter):
    """OpenTelemetry exporter that records spans for task and worker events."""

    def __init__(self, *, service_name: str = "celery-cnc", endpoint: str | None = None) -> None:
        """Initialize the tracer provider and exporter."""
        self._endpoint = endpoint
        resource = Resource.create({"service.name": service_name})
        self._span_exporter = InMemorySpanExporter()
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(SimpleSpanProcessor(self._span_exporter))
        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer("celery_cnc.otel")

    @property
    def exporter(self) -> InMemorySpanExporter:
        """Expose the in-memory span exporter."""
        return self._span_exporter

    def on_task_event(self, event: TaskEvent) -> None:
        """Record a span for a task event."""
        with self._tracer.start_as_current_span(
            "task.event",
            attributes={
                "celery.task_id": event.task_id,
                "celery.task_name": event.name or "unknown",
                "celery.state": event.state,
                "celery.worker": event.worker or "unknown",
            },
        ) as span:
            if event.runtime is not None:
                span.set_attribute("celery.runtime", event.runtime)

    def on_worker_event(self, event: WorkerEvent) -> None:
        """Record a span for a worker event."""
        with self._tracer.start_as_current_span(
            "worker.event",
            attributes={
                "celery.worker": event.hostname,
                "celery.event": event.event,
            },
        ):
            return

    def update_stats(self, stats: TaskStats) -> None:
        """Record a span with task statistics."""
        with self._tracer.start_as_current_span("task.stats") as span:
            if stats.count is not None:
                span.set_attribute("celery.stats.count", stats.count)
            if stats.min_runtime is not None:
                span.set_attribute("celery.stats.min", stats.min_runtime)
            if stats.max_runtime is not None:
                span.set_attribute("celery.stats.max", stats.max_runtime)
            if stats.avg_runtime is not None:
                span.set_attribute("celery.stats.avg", stats.avg_runtime)
            if stats.p95 is not None:
                span.set_attribute("celery.stats.p95", stats.p95)
            if stats.p99 is not None:
                span.set_attribute("celery.stats.p99", stats.p99)

    def serve(self) -> None:
        """Serve exporter data (noop for in-memory exporter)."""
        return

    def shutdown(self) -> None:
        """Clear recorded spans."""
        self._span_exporter.clear()
