# TODO: CeleryCnC Modular Refactor

Goal: Refactor the project into a modular component system with a clean public API:
- `CeleryCnC(...)` orchestrates enabled components on boot.
- `CeleryCnCConfig(...)` configures logging/db + optional components (beat, prometheus, otel, frontend).
- Components are started only if enabled (config is not `None` / enabled flag).
- Shared services (logging + DB controller) are handed to all components.
- Web frontend adapts UI based on enabled components (sidebar entries, status, links, basic usage/config).

---

## 0) Repo / Structure Work

- [ ] Create / confirm package layout exactly like:

  - [ ] `celery_cnc/components/`
    - [ ] `metrics/opentelemetry/`
    - [ ] `metrics/prometheus/`
    - [ ] `web/`
    - [ ] `beat/`
  - [ ] `celery_cnc/core/`
    - [ ] `db/models/`
    - [ ] `db/manager.py`
    - [ ] `db/adapters/base.py`
    - [ ] `db/adapters/memory/`
    - [ ] `db/adapters/sqlite/`
    - [ ] `logging/adapters/base.py`
    - [ ] `logging/adapters/file.py`
    - [ ] `engine/backend.py`
    - [ ] `engine/workers.py`
    - [ ] `engine/brokers/base.py`
    - [ ] `engine/brokers/rabbitmq/`
    - [ ] `engine/brokers/redis/`
    - [ ] `engine/backends/base.py`
    - [ ] `engine/backends/sqlalchemy/`
    - [ ] `engine/backends/redis/`

- [ ] Add/verify `__init__.py` exports for the new public API:
  - [ ] `CeleryCnC`
  - [ ] `CeleryCnCConfig`
  - [ ] `LoggingConfigFile`
  - [ ] `DatabaseConfigSqlite`
  - [ ] `BeatConfig`
  - [ ] `PrometheusConfig`
  - [ ] `OpenTelemetryConfig`
  - [ ] `FrontendConfig`

- [ ] Ensure imports match the desired usage example (no deep-path imports needed).

---

## 1) Public API + Configuration Objects

### 1.1 CeleryCnCConfig and component configs
- [ ] Implement / refactor config dataclasses (or pydantic models) for:
  - [ ] `CeleryCnCConfig(logging=..., database=..., beat=..., prometheus=..., open_telemetry=..., frontend=...)`
  - [ ] `LoggingConfigFile(...)` with sensible defaults (file logging on by default per request)
  - [ ] `DatabaseConfigSqlite(db_path=..., purge_db=...)` (defaults to sqlite)
  - [ ] `BeatConfig(schedule_path=..., delete_schedules_on_boot=...)` (default: `None` to disable)
  - [ ] `PrometheusConfig(port=8001, prometheus=True, prometheus_path="/metrics", ...)` (default: `None` to disable)
  - [ ] `OpenTelemetryConfig(...)` (default: `None` to disable)
  - [ ] `FrontendConfig(host="127.0.0.1", port=8000, ...)` (default behavior TBD)

- [ ] Define consistent “enabled” semantics:
  - [ ] If config is `None` → component disabled, not started.
  - [ ] If config exists → component enabled (or has explicit `enabled: bool`).

- [ ] Validate config invariants early:
  - [ ] Paths exist / are creatable (log_dir, schedule_path, db_path parent)
  - [ ] Mutually exclusive / required fields
  - [ ] Reasonable defaults (so minimal config works)

### 1.2 CeleryCnC class shape
- [ ] Implement / refactor `CeleryCnC(*celery_apps, config=CeleryCnCConfig(...))`
  - [ ] Accept multiple Celery apps and register them internally
  - [ ] Provide `.run()` which:
    - [ ] builds shared services (logging + DB controller)
    - [ ] boots enabled components in correct order
    - [ ] starts the runtime (web server, workers, beat, metrics) as required

- [ ] Keep boot flow “roughly like demo/main.py” but routed through component manager.

---

## 2) Component System / Lifecycle

### 2.1 Common component interface
- [ ] Define a base component interface, e.g. `BaseComponent`:
  - [ ] `name: str`
  - [ ] `enabled: bool`
  - [ ] `start(ctx) -> None`
  - [ ] `stop(ctx) -> None` (graceful shutdown)
  - [ ] `status() -> ComponentStatus` (for UI: up/down + metadata)
  - [ ] `get_ui_schema()` or similar (optional: for frontend adaptation)

- [ ] Define an app “context” object passed to components:
  - [ ] `logger` / logging service
  - [ ] `db: BaseDBController`
  - [ ] `config: CeleryCnCConfig` (or component-specific configs)
  - [ ] `celery_apps` registry
  - [ ] any shared runtime handles (threads/processes, event loop, etc.)

### 2.2 Component manager / orchestrator
- [ ] Implement component registry + boot:
  - [ ] Determine components to start based on config
  - [ ] Start components in dependency order:
    - [ ] logging (first)
    - [ ] db (early)
    - [ ] metrics (prometheus/otel)
    - [ ] beat (if enabled)
    - [ ] web frontend (after registry exists so it can reflect loaded components)
  - [ ] Stop components in reverse order on shutdown

- [ ] Ensure components not enabled are not imported/started (avoid side effects).

---

## 3) Logging Service Refactor

- [ ] Define `core/logging/adapters/base.py` interface:
  - [ ] `configure(config) -> LoggerLike`
  - [ ] optional: structured logging hooks for components

- [ ] Implement `core/logging/adapters/file.py`:
  - [ ] Creates log directory
  - [ ] Rotating files (if desired)
  - [ ] Per-component logger namespace (e.g. `celery_cnc.component.beat`)

- [ ] Make logging available everywhere via context injection, not global imports.

---

## 4) Database Controller Refactor (Critical)

### 4.1 Base DB controller interface
- [ ] Define `BaseDBController` in `core/db/adapters/base.py` with a high-level API:
  - [ ] `init()`, `close()`
  - [ ] `migrate()` (optional)
  - [ ] `purge()` (for `purge_db=True`)
  - [ ] `transaction()` context manager (if supported)
  - [ ] “high level” CRUD methods used by components (define the minimal set)
  - [ ] Concurrency contract documented (thread-safe? process-safe?).

### 4.2 DB manager
- [ ] Refactor `core/db/manager.py` to:
  - [ ] choose the adapter based on config
  - [ ] produce a `BaseDBController` instance for the app context
  - [ ] handle purge/migrate on boot based on config
  - [ ] expose health/status for UI

### 4.3 SQLite + Memory adapters
- [ ] Implement/confirm `sqlite` adapter:
  - [ ] Safe concurrent access strategy for multi-component parallelism
  - [ ] If multiple processes are involved, define how writes are handled:
    - [ ] option A: single DB process/worker with IPC (queue-based)
    - [ ] option B: file-lock + WAL + retry/backoff
    - [ ] option C: restrict sqlite usage to a single process, and route all DB ops through it
  - [ ] Document limitations and behavior (so later postgres/mongo can differ safely)

- [ ] Implement/confirm `memory` adapter:
  - [ ] thread-safe data structures and clear lifecycle
  - [ ] intended for tests/dev only

- [ ] Add adapter stubs for future DBs:
  - [ ] `postgres` (likely via sqlalchemy)
  - [ ] `mongo`
  - [ ] Ensure components stay adapter-agnostic.

---

## 5) Engine Integration (Workers/Brokers/Backends)

- [ ] Confirm core engine pieces exist and refactor to fit the new modular architecture:
  - [ ] `core/engine/workers.py` consumes provided Celery apps registry
  - [ ] `core/engine/backend.py` uses backend adapters (sqlalchemy/redis/etc.)
  - [ ] `core/engine/brokers/*` aligned with config + selection

- [ ] Ensure `CeleryCnC.run()` uses the engine consistently:
  - [ ] Start workers if that’s part of `run()` (or expose separate `run_workers()`).

---

## 6) Beat Component

- [ ] Move/refactor beat integration into `components/beat/`:
  - [ ] Uses `BeatConfig(schedule_path, delete_schedules_on_boot)`
  - [ ] Deletes schedules on boot if configured
  - [ ] Starts celery beat (or custom scheduler) cleanly
  - [ ] Exposes status (up/down) and schedule metadata for UI

- [ ] Ensure disabled when `config.beat is None`.

> Note: Remove stray import like `from celery.apps.beat import Beat` from random places; keep beat-specific imports inside the beat component.

---

## 7) Metrics Components

### 7.1 Prometheus component
- [ ] `components/metrics/prometheus/`:
  - [ ] Mount metrics endpoint at `prometheus_path` (e.g. `/metrics`)
  - [ ] Expose “status” (up/down) and config info for the UI
  - [ ] Ensure it can integrate with chosen web framework (see frontend tasks)

### 7.2 OpenTelemetry component
- [ ] `components/metrics/opentelemetry/`:
  - [ ] Initialize OTel SDK based on `OpenTelemetryConfig`
  - [ ] Set up exporters/resources
  - [ ] Provide status + minimal “how to use” config summary for UI

- [ ] Ensure both are optional and do nothing if disabled.

---

## 8) Web Frontend Component (Dynamic UI)

- [ ] Move/refactor into `components/web/`:
  - [ ] Start web server with `FrontendConfig(host, port)`
  - [ ] Load component registry from context to adapt navigation
  - [ ] Render conditional sidebar entries:
    - [ ] Prometheus entry only if enabled: show status up/down, basic config snippet, link
    - [ ] OTel entry only if enabled: show status + basic usage/config + link
    - [ ] Beat scheduler UI only if enabled (sidebar + page)
  - [ ] Components not enabled are invisible in UI.

- [ ] Define a simple contract for UI metadata per component:
  - [ ] `display_name`
  - [ ] `route`
  - [ ] `status`
  - [ ] `links` (e.g. prometheus scrape URL)
  - [ ] `config_summary` (safe to display)

- [ ] Add an endpoint for component health summary (JSON) used by UI.

---

## 9) Boot Flow & Process Model

- [ ] Decide and implement the runtime model in `CeleryCnC.run()`:
  - [ ] single process with threads?
  - [ ] multi-process? (web + beat + workers)
  - [ ] if multi-process: how shared DB controller is accessed safely
  - [ ] define shutdown signals handling (SIGINT/SIGTERM)

- [ ] Ensure “general things like db and logging can be handed over (and copied in the process?!)”:
  - [ ] If multi-process: implement a safe pattern (e.g., re-init controller per process or use an IPC proxy)
  - [ ] Clearly document which objects are process-local.

---

## 10) Demo parity + Migration

- [ ] Update `demo/main.py` (or equivalent) to match the target usage:

  - [ ] `config = CeleryCnCConfig(...)`
  - [ ] `cnc = CeleryCnC(math_app, text_app, sleep_app, config=config)`
  - [ ] `cnc.run()`

- [ ] Ensure existing demo workers run unchanged (only wiring changes).

---

## 11) Tests / Verification

- [ ] Add smoke tests:
  - [ ] Boot with minimal config (only logging + sqlite)
  - [ ] Boot with beat enabled
  - [ ] Boot with prometheus enabled
  - [ ] Boot with otel enabled
  - [ ] Boot with web frontend enabled and verify dynamic nav entries

- [ ] Add DB concurrency tests (especially sqlite):
  - [ ] Parallel reads/writes from multiple components (threads/processes depending on runtime model)
  - [ ] Validate no DB corruption / deadlocks

- [ ] Add graceful shutdown test:
  - [ ] stop order works and no resources leak

---

## 12) Documentation

- [ ] Document configuration defaults and “how to compose” features:
  - [ ] What happens when a config is `None`
  - [ ] Where logs go
  - [ ] DB adapter behavior and limitations (sqlite concurrency!)
  - [ ] How to access metrics endpoints
  - [ ] What the web frontend shows depending on enabled components

---

# Open Questions / Clarifications Needed

(Answering these will prevent rework; if unclear, implement a reasonable default and document it.)

- [x] **Runtime model:** Should `CeleryCnC.run()` start *everything* (web + beat + workers), or only “control plane” components and leave workers to be started separately? - only control plane
- [x] **Concurrency scope:** Will components run in:
  - [ ] same process (threads/async), or
  - [x] multiple processes (recommended for isolation)?
- [x] **SQLite strategy:** If multiple processes are used, which approach do you want?
  - [x] IPC-based single DB writer
  - [ ] SQLite WAL + retry/backoff + file locks
  - [ ] “SQLite only supported in single-process mode”
- [x] **Prometheus exposure:** Should prometheus endpoint be served by the web component, or by a standalone metrics server component? - standalone, can use a very slim django
- [x] **Component status:** How should “up/down” be determined: process alive

---
