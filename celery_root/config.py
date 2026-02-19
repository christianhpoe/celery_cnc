# SPDX-FileCopyrightText: 2026 Christian-Hauke Poensgen
# SPDX-FileCopyrightText: 2026 Maximilian Dolling
# SPDX-FileContributor: AUTHORS.md
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration settings for Celery Root."""

from __future__ import annotations

import hashlib
import secrets
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_PORT = 65_535


def _default_rpc_socket_path() -> Path:
    root = Path.cwd().resolve()
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:8]
    return Path(tempfile.gettempdir()) / f"celery_root_{digest}.sock"


class DatabaseConfigBase(BaseModel):
    """Base database configuration."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    rpc_host: str = "127.0.0.1"
    rpc_port: int = Field(default=8765, ge=1, le=MAX_PORT)
    rpc_auth_key: str = ""
    rpc_socket_path: Path = Field(default_factory=_default_rpc_socket_path)
    rpc_max_message_bytes: int = Field(default=4_194_304, gt=0)
    rpc_max_inflight: int = Field(default=64, gt=0)
    rpc_timeout_seconds: float = Field(default=5.0, gt=0)

    @field_validator("rpc_socket_path", mode="after")
    @classmethod
    def _expand_rpc_socket_path(cls, value: Path) -> Path:
        expanded = value.expanduser()
        expanded.parent.mkdir(parents=True, exist_ok=True)
        return expanded

    def rpc_address(self) -> str:
        """Return the address for RPC connections."""
        return str(self.rpc_socket_path)


class DatabaseConfigSqlite(DatabaseConfigBase):
    """SQLite database configuration (in-memory when db_path is None)."""

    db_path: Path | None = None
    retention_days: int = Field(default=7, gt=0)
    batch_size: int = Field(default=500, gt=0)
    flush_interval: float = Field(default=1.0, gt=0)
    purge_db: bool = False

    @field_validator("db_path", mode="after")
    @classmethod
    def _expand_db_path(cls, value: Path | None) -> Path | None:
        if value is None:
            return None
        return value.expanduser()

    @model_validator(mode="after")
    def _ensure_db_parent(self) -> DatabaseConfigSqlite:
        if self.db_path is not None:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return self


class BeatConfig(BaseModel):
    """Beat scheduler configuration."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    db_refresh_seconds: float | None = Field(default=None, gt=0)


class PrometheusConfig(BaseModel):
    """Prometheus exporter configuration."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    port: int = Field(default=8001, ge=1, le=MAX_PORT)
    prometheus_path: str = "/metrics"
    flower_comatibility: bool = False

    @field_validator("prometheus_path", mode="after")
    @classmethod
    def _normalize_path(cls, value: str) -> str:
        if not value:
            return "/metrics"
        return value if value.startswith("/") else f"/{value}"

    @property
    def flower_compatibility(self) -> bool:
        """Return whether to use Flower metric naming."""
        return self.flower_comatibility


class OpenTelemetryConfig(BaseModel):
    """OpenTelemetry exporter configuration."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    endpoint: str = "http://localhost:4317"
    service_name: str = "celery_root"


class FrontendConfig(BaseModel):
    """Web frontend configuration."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    host: str = "127.0.0.1"
    port: int = Field(default=5555, ge=1, le=MAX_PORT)
    debug: bool = True
    poll_interval: float = Field(default=2.0, gt=0)
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    basic_auth: str | None = None
    auth_provider: str | None = None
    auth: str | None = None
    oauth2_key: str | None = None
    oauth2_secret: str | None = None
    oauth2_redirect_uri: str | None = None
    oauth2_okta_base_url: str | None = None
    gitlab_allowed_groups: str | None = None
    gitlab_min_access_level: int | None = Field(default=None, ge=1)
    gitlab_oauth_domain: str | None = None


class McpConfig(BaseModel):
    """MCP server configuration."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    host: str = "127.0.0.1"
    port: int = Field(default=5557, ge=1, le=MAX_PORT)
    path: str = "/mcp/"
    auth_key: str | None = None
    readonly_db_url: str | None = None

    @field_validator("path", mode="after")
    @classmethod
    def _normalize_path(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return "/mcp/"
        if not cleaned.startswith("/"):
            cleaned = f"/{cleaned}"
        return cleaned


class CeleryRootConfig(BaseModel):
    """Central configuration for Celery Root."""

    model_config = ConfigDict(validate_assignment=True, extra="ignore")

    database: DatabaseConfigSqlite = Field(default_factory=DatabaseConfigSqlite)
    beat: BeatConfig | None = None
    prometheus: PrometheusConfig | None = None
    open_telemetry: OpenTelemetryConfig | None = None
    frontend: FrontendConfig | None = Field(default_factory=FrontendConfig)
    mcp: McpConfig | None = None

    worker_import_paths: list[str] = Field(default_factory=list)
    event_queue_maxsize: int = Field(default=32_767, gt=0, le=32_767)
    integration: bool = False

    @field_validator("database", mode="before")
    @classmethod
    def _coerce_database(cls, value: object) -> object:
        if isinstance(value, DatabaseConfigSqlite):
            return value
        if isinstance(value, dict):
            return DatabaseConfigSqlite(**value)
        return value


@dataclass
class _SettingsState:
    cache: CeleryRootConfig | None = None
    runtime: CeleryRootConfig | None = None


_STATE = _SettingsState()


def get_settings() -> CeleryRootConfig:
    """Return the active configuration, reading defaults if needed."""
    if _STATE.runtime is not None:
        return _STATE.runtime
    if _STATE.cache is None:
        _STATE.cache = CeleryRootConfig()
    return _STATE.cache


def set_settings(config: CeleryRootConfig) -> None:
    """Override the global settings for the current process."""
    _STATE.runtime = config


def reset_settings() -> None:
    """Clear cached settings."""
    _STATE.cache = None
    _STATE.runtime = None


__all__ = [
    "MAX_PORT",
    "BeatConfig",
    "CeleryRootConfig",
    "DatabaseConfigBase",
    "DatabaseConfigSqlite",
    "FrontendConfig",
    "McpConfig",
    "OpenTelemetryConfig",
    "PrometheusConfig",
    "get_settings",
    "reset_settings",
    "set_settings",
]
