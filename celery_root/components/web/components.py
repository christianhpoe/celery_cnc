# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

"""Component metadata helpers for the web UI."""

from __future__ import annotations

from dataclasses import dataclass

from celery_root.config import get_settings


@dataclass(slots=True)
class ComponentInfo:
    """Summary metadata for a runtime component."""

    key: str
    display_name: str
    enabled: bool
    url: str | None = None
    config: dict[str, object] | None = None


def component_snapshot() -> dict[str, ComponentInfo]:
    """Return component metadata for UI rendering."""
    config = get_settings()
    prometheus = config.prometheus
    otel = config.open_telemetry
    beat = config.beat
    frontend = config.frontend
    mcp = config.mcp

    snapshot: dict[str, ComponentInfo] = {
        "prometheus": ComponentInfo(
            key="prometheus",
            display_name="Prometheus",
            enabled=prometheus is not None,
            url=_metrics_url() if prometheus is not None else None,
            config=({"port": prometheus.port, "path": prometheus.prometheus_path} if prometheus is not None else None),
        ),
        "open_telemetry": ComponentInfo(
            key="open_telemetry",
            display_name="OpenTelemetry",
            enabled=otel is not None,
            config=({"endpoint": otel.endpoint, "service_name": otel.service_name} if otel is not None else None),
        ),
        "beat": ComponentInfo(
            key="beat",
            display_name="Beat",
            enabled=beat is not None,
            config=({"db_refresh_seconds": beat.db_refresh_seconds} if beat is not None else None),
        ),
        "frontend": ComponentInfo(
            key="frontend",
            display_name="Web",
            enabled=frontend is not None,
            url=_frontend_url() if frontend is not None else None,
            config=({"host": frontend.host, "port": frontend.port} if frontend is not None else None),
        ),
        "mcp": ComponentInfo(
            key="mcp",
            display_name="MCP",
            enabled=mcp is not None,
            url=_mcp_url() if mcp is not None else None,
            config=(
                {
                    "host": mcp.host,
                    "port": mcp.port,
                    "path": mcp.path,
                    "auth_configured": bool(mcp.auth_key),
                }
                if mcp is not None
                else None
            ),
        ),
    }
    return snapshot


def _metrics_url() -> str:
    config = get_settings()
    frontend = config.frontend
    host = frontend.host if frontend is not None else "127.0.0.1"
    if host in {"0.0.0.0", "::"}:  # noqa: S104
        host = "127.0.0.1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    prometheus = config.prometheus
    path = "/metrics" if prometheus is None else prometheus.prometheus_path
    port = 8001 if prometheus is None else prometheus.port
    return f"http://{host}:{port}{path}"


def _frontend_url() -> str:
    config = get_settings()
    frontend = config.frontend
    if frontend is None:
        return ""
    host = frontend.host
    if host in {"0.0.0.0", "::"}:  # noqa: S104
        host = "127.0.0.1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    return f"http://{host}:{frontend.port}/"


def _mcp_url() -> str:
    config = get_settings()
    mcp = config.mcp
    if mcp is None:
        return ""
    host = mcp.host
    if host in {"0.0.0.0", "::"}:  # noqa: S104
        host = "127.0.0.1"
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    path = mcp.path or "/mcp/"
    if not path.startswith("/"):
        path = f"/{path}"
    path = f"{path.rstrip('/')}/"
    return f"http://{host}:{mcp.port}{path}"
