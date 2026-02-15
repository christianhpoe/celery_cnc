# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

"""Optional dependency helpers for feature scopes."""

from __future__ import annotations

from importlib.util import find_spec

_SCOPE_DEPENDENCIES: dict[str, tuple[str, ...]] = {
    "web": ("django",),
    "prometheus": ("prometheus_client",),
    "otel": ("opentelemetry.sdk", "opentelemetry.exporter.otlp"),
    "mcp": ("fastmcp", "uvicorn", "django"),
}


def require_optional_scope(scope: str) -> None:
    """Ensure optional dependencies for a scope are installed."""
    dependencies = _SCOPE_DEPENDENCIES.get(scope)
    if dependencies is None:
        message = f"Unknown optional dependency scope: {scope}"
        raise ValueError(message)
    missing = [name for name in dependencies if find_spec(name) is None]
    if not missing:
        return
    missing_list = ", ".join(missing)
    message = (
        f"Optional dependency scope '{scope}' is required but not installed. "
        f"Missing packages: {missing_list}. "
        f"Install with `pip install celery_root[{scope}]`."
    )
    raise RuntimeError(message)


__all__ = ["require_optional_scope"]
