# celery_cnc — Requirements, Tasks & Team Assignment

> Celery Command & Control: Multi-worker monitoring, management, and visualization.
> **Fresh build. Django SSR. PyPI wheel. Python 3.13. uv.**

---

## 0. Current To-Do (User)

- [ ] Record tracebacks reliably and persist them.
- [ ] Format JSON inputs/outputs cleanly in the UI (pretty + readable).
- [ ] Investigate why the `Schedule.JSON.Multitask` task did not start.
- [ ] Fix/verify task send from the WebUI.
- [ ] Add a delete-on-boot flag for DB cleanup on startup.
- [ ] Fix task search by task name.
- [ ] Replace filter Apply button with debounced on-change filtering.
- [ ] Fix the task graph (IDs showing, nodes don’t make sense).
- [ ] Ensure all components emit logs regularly so the Logs page is populated.
- [ ] Add a Settings page with theme selection (Monokai, Darkula, Generic, Dark, White, Solaris).
- [ ] Settings page: allow configuring the polling interval.
- [ ] Task start UI: use each task’s default queue (not a global/system default).
- [ ] Task start UI: searchable dropdown for task selection.
- [ ] Task start UI: provide a simple JSON editor for args/kwargs (“arcs/quarks”).
- [ ] Task detail layout: small cards (Execution flow, Relations) on top, big cards stacked for Overview/Result/Payload/Traceback.
- [ ] Improve top navbar secondary button contrast/visibility next to the primary button.
- [ ] Task list filters: quick time presets for last 5/10/30 minutes.
- [ ] Broker page: support multiple brokers/backends, show attached workers, add details for correct broker selection/purge.
- [ ] Beat schedule UI: quick select common intervals (hourly, every 10 min, daily, half-day, every 6h, every 3h, weekly); reduce manual cron typing.

## 1. Project Overview

celery_cnc replaces Celery Flower. It supports multiple Celery workers (different brokers/backends), has a proper database layer, multiprocessing architecture, and a Django-based web UI with real-time updates and task graph visualization.

### Design Principles

- **All config in Python** — the user controls how config gets there.
- **2-line startup** — `cnc = CeleryCnC(worker1, worker2, ...); cnc.run()`
- **Dev-friendly** — import workers by path without installing into the target project.
- **Django-aware** — support Django's way of doing things (custom backends, rate limiters, plugins).
- **Extensible** — ABC-based controllers for DB, logging, monitoring. User subclasses to customize.
- **Monitoring à la carte** — enable Prometheus, OpenTelemetry, or both at init time.

---

## 2. Tooling & Standards

| Concern | Tool / Standard |
|---------|----------------|
| Python version | **3.13** |
| Package manager | **uv** (all installs via `uv add`, sync via `uv sync`) |
| Build system | **uv build** (produces wheel) |
| Publishing | **uv publish** (to PyPI) |
| Project config | **pyproject.toml** only. No `requirements.txt`. No `setup.py`. |
| Linting | ruff |
| Type checking | mypy (strict) |
| Testing | pytest |
| Formatting | ruff format |

---

## 3. Architecture

### 3.1 Process Model

```
CeleryCnC.run()
       │
       ├── Process: EventListener(broker_1)  ──┐
       ├── Process: EventListener(broker_2)  ──┤
       ├── ...                                 ├──▶ IPC Queue ──▶ Process: DBManager
       ├── Process: EventListener(broker_n)  ──┘                       │
       │                                                               │
       ├── Process: PrometheusExporter (optional, if enabled)          │
       ├── Process: OTelExporter (optional, if enabled)                │
       │                                                               │
       └── Process: WebServer (Django)  ◀────────────────────── reads DB
```

- **One EventListener per unique broker** — subscribes to Celery events, pushes to shared queue.
- **One DBManager** — single writer to DB. Reads from event queue, writes to DB.
- **PrometheusExporter** (optional subprocess) — reads from DB, exposes `/metrics`. Enabled/disabled at init.
- **OTelExporter** (optional subprocess) — reads from DB, exports spans/metrics via OTLP. Enabled/disabled at init.
- **WebServer** — Django, reads DB, serves UI. Channels/SSE/polling for live updates.

Init-time control:
```python
cnc = CeleryCnC(
    worker1, worker2,
    prometheus=True,       # spawn PrometheusExporter process
    opentelemetry=True,    # spawn OTelExporter process
    db_controller=MyCustomDB(),      # optional ABC subclass
    log_controller=MyCustomLog(),    # optional ABC subclass
)
cnc.run()
```

### 3.2 Multi-Worker Registry

`CeleryCnC` accepts multiple Celery app instances or import paths. Each registration extracts broker URL, result backend, serializers, registered tasks, custom config. Workers sharing a broker share one EventListener.

### 3.3 Database Layer

**ABC: `BaseDBController`** — user can subclass for custom backends.

Implementations shipped:
- **SQLiteController** (default) — file-based, survives restarts.
- **MemoryController** — dict-based, for testing/ephemeral.

**Migration hooks:** `BaseDBController` defines `get_schema_version() -> int` and `migrate(from_version, to_version)`. Implementations handle their own schema migrations. SQLiteController uses a `schema_version` table. Not needed for v1 but the interface is there from day one.

Models: `Task`, `Worker`, `WorkerEvent`, `Schedule` (beat), `TaskRelation` (parent/child for chains/chords).

### 3.4 Logging Layer

**ABC: `BaseLogController`** — user can subclass.

Default implementation: file-based, new file every 24h, configurable path and rotation.

### 3.5 Monitoring Layer

**ABC: `BaseMonitoringExporter`** — defines `on_task_event()`, `on_worker_event()`, `update_stats()`, `serve()` (for HTTP exporters like Prometheus).

Each exporter runs as its own subprocess. Enabled/disabled independently at init time.

### 3.6 Web Layer

- Django with SSR (Django templates).
- Django Channels or SSE or polling for real-time (start with polling, Channels as upgrade path).
- Chart.js for charts. cytoscape.js or dagre-d3 for DAG visualization.
- No auth. Single user.

---

## 4. Functional Requirements

> Everything is a Must. No priority tiers.

### 4.1 Monitoring

| ID | Requirement |
|----|-------------|
| MON-1 | Running tasks per worker (live) |
| MON-2 | Total task count (all-time, per worker, per task type) |
| MON-3 | Runtime stats: min, max, avg, mean, p50/p95/p99 |
| MON-4 | CPU and memory per task (best-effort via worker stats / billiard rusage) |
| MON-5 | Prometheus metrics endpoint in dedicated subprocess |
| MON-6 | OpenTelemetry export (traces + metrics) in dedicated subprocess |
| MON-7 | Task state distribution (pending, started, success, failure, retry, revoked) |
| MON-8 | Task throughput over time |
| MON-9 | Worker online/offline status with history |
| MON-10 | Enable/disable Prometheus and OTel independently at init |

### 4.2 Command & Control

| ID | Requirement |
|----|-------------|
| CNC-1 | Broker inspection (queue lengths, consumers) |
| CNC-2 | Backend inspection (stored results) |
| CNC-3 | Start/send tasks (args, kwargs, ETA, countdown) |
| CNC-4 | Clear broker queues (all, specific task, task group) |
| CNC-5 | Clear backend results (all, specific task, task group) |
| CNC-6 | Stop/revoke running tasks (terminate with signal) |
| CNC-7 | Retry failed tasks (bypass max_retries — schedule as new) |
| CNC-8 | Retry entire chains/chords/starmap patterns |
| CNC-9 | Live pool management: grow, shrink, autoscale |
| CNC-10 | General worker stats (registered tasks, active queues, prefetch count, conf) |
| CNC-11 | Beat integration: read/add/edit/delete schedules on the fly |
| CNC-12 | Health checks (broker, backend, worker heartbeats) |

### 4.3 Search & Filtering

| ID | Requirement |
|----|-------------|
| SRC-1 | Filter tasks by state, worker, task name, date range |
| SRC-2 | Fuzzy search on task args and kwargs |
| SRC-3 | Filter by task group / chain / chord ID |
| SRC-4 | Combined filters (state + worker + name + fuzzy args) |

### 4.4 Web Frontend

| ID | Requirement |
|----|-------------|
| WEB-1 | Dashboard overview (worker count, task counts, throughput) |
| WEB-2 | Real-time updates (WS / SSE / polling) |
| WEB-3 | Task chain/chord/starmap DAG visualization (self-loops × N for retries) |
| WEB-4 | Line charts (throughput over time, runtimes) |
| WEB-5 | Pie/donut charts (state distribution, task type distribution) |
| WEB-6 | Heatmaps (tasks per time-of-day / day-of-week) |
| WEB-7 | Worker detail view (stats, running tasks, pool, queues) |
| WEB-8 | Task detail view (args, kwargs, result, traceback, runtime, retries, parent chain) |
| WEB-9 | Beat schedule management UI |
| WEB-10 | No auth, single user |

### 4.5 Database

| ID | Requirement |
|----|-------------|
| DB-1 | SQLite default (file-based, persistent) |
| DB-2 | In-memory implementation |
| DB-3 | ABC `BaseDBController` for extensibility |
| DB-4 | Store task events with full args/kwargs/result/traceback |
| DB-5 | Store task relationships (parent → children, chord → callbacks) |
| DB-6 | Store worker events and stats history |
| DB-7 | Auto-cleanup of old data (configurable retention) |
| DB-8 | Migration hooks: `get_schema_version()` + `migrate()` on ABC |

### 4.6 Logging

| ID | Requirement |
|----|-------------|
| LOG-1 | ABC `BaseLogController` |
| LOG-2 | Default: file, 24h rotation |
| LOG-3 | Configurable path and rotation |
| LOG-4 | User-extensible via init |

### 4.7 Packaging

| ID | Requirement |
|----|-------------|
| PKG-1 | PyPI wheel with all frontend assets bundled |
| PKG-2 | 2-line startup |
| PKG-3 | Dev mode: workers by import path |
| PKG-4 | `pyproject.toml`, uv build, uv publish |
| PKG-5 | Works alongside existing Django projects |

---

## 5. Project Structure

```
celery-cnc/
├── pyproject.toml
├── uv.lock
├── README.md
├── LICENSE                          # BSD-3-Clause
│
├── src/
│   └── celery_cnc/
│       ├── __init__.py              # CeleryCnC class, public API
│       ├── config.py                # CnCConfig dataclass
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── registry.py          # WorkerRegistry
│       │   ├── event_listener.py    # EventListener(Process)
│       │   ├── inspector.py         # Inspector wrapper
│       │   ├── control.py           # Control wrapper
│       │   ├── beat.py              # Beat schedule read/write
│       │   └── process_manager.py   # Orchestrates all subprocesses
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── abc.py               # BaseDBController(ABC)
│       │   ├── models.py            # Dataclasses
│       │   ├── sqlite.py            # SQLiteController
│       │   ├── memory.py            # MemoryController
│       │   └── manager.py           # DBManager(Process)
│       │
│       ├── monitoring/
│       │   ├── __init__.py
│       │   ├── abc.py               # BaseMonitoringExporter(ABC)
│       │   ├── prometheus.py        # PrometheusExporter(Process)
│       │   ├── otel.py              # OTelExporter(Process)
│       │   └── stats.py             # Aggregation functions
│       │
│       ├── cnc/
│       │   ├── __init__.py
│       │   ├── tasks.py
│       │   ├── workers.py
│       │   ├── broker.py
│       │   ├── backend.py
│       │   └── health.py
│       │
│       ├── logging/
│       │   ├── __init__.py
│       │   ├── abc.py               # BaseLogController(ABC)
│       │   └── file_handler.py      # FileLogController
│       │
│       └── web/
│           ├── manage.py
│           ├── settings.py
│           ├── urls.py
│           ├── asgi.py
│           ├── wsgi.py
│           ├── views/
│           │   ├── dashboard.py
│           │   ├── tasks.py
│           │   ├── workers.py
│           │   ├── broker.py
│           │   ├── beat.py
│           │   ├── graphs.py
│           │   └── api.py
│           ├── consumers.py
│           ├── templates/
│           │   ├── base.html
│           │   ├── dashboard.html
│           │   ├── tasks/
│           │   │   ├── list.html
│           │   │   ├── detail.html
│           │   │   └── graph.html
│           │   ├── workers/
│           │   │   ├── list.html
│           │   │   └── detail.html
│           │   ├── broker.html
│           │   └── beat.html
│           └── static/
│               ├── css/
│               ├── js/
│               │   ├── charts.js
│               │   ├── dag.js
│               │   ├── realtime.js
│               │   └── search.js
│               └── vendor/
│
└── tests/
    ├── conftest.py
    ├── fixtures/
    ├── test_registry.py
    ├── test_event_listener.py
    ├── test_db_controllers.py
    ├── test_cnc_tasks.py
    ├── test_cnc_workers.py
    └── test_web_views.py
```

---

## 6. Flower Patterns to Adapt

BSD-3-Clause. Copy with attribution.

| Pattern | Source | Use |
|---------|--------|-----|
| Event consumption | `flower/events.py` — `EventsState(State)` | Adapt for EventListener |
| Control API calls | `flower/api/tasks.py`, `workers.py` | Reference for `cnc/tasks.py`, `cnc/workers.py` |
| Broker queue inspection | `flower/utils/broker.py` | Adapt for `cnc/broker.py` |
| Prometheus metrics | `flower/events.py` — metric names | Reference for `monitoring/prometheus.py` |

---

## 7. Agent Roles

Work is split by agent role. Each agent owns its area; ABCs and models are the contract. Mark tasks complete by changing the task row’s `[ ]` to `[x]` in the Done column.

| Role | Profile | Owns |
|------|---------|------|
| **Gandalf** | Architecture, systems, infra. | `core/`, `db/`, repo setup |
| **Lisa** | Backend, CnC, monitoring, logging, beat. | `cnc/`, `monitoring/`, `logging/`, beat logic |
| **Tom** | Frontend, views, templates, JS, charts, DAG. | `web/` — views, templates, JS, charts, DAG |

---

## 8. Phase 0 — Gandalf Bootstraps (Solo, ~2 days)

Gandalf sets up the repo and defines all interfaces so the three can work in parallel without blocking.

| Done | # | Task | Description |
|------|---|------|-------------|
| [x] | 0.1 | **Repo init** | `uv init celery-cnc`, `src/` layout, `pyproject.toml` (Python ≥3.13), `.gitignore`, `LICENSE` (BSD-3). |
| [x] | 0.2 | **Dependencies** | `uv add django celery sqlalchemy prometheus-client opentelemetry-sdk opentelemetry-exporter-otlp`. `uv add --dev pytest ruff mypy`. |
| [x] | 0.3 | **Directory structure** | Every dir + `__init__.py` from Section 5. Empty stubs everywhere. |
| [x] | 0.4 | **CnCConfig** | `config.py` — dataclass with all config fields, defaults, types, validation. |
| [x] | 0.5 | **Data models** | `db/models.py` — `Task`, `Worker`, `WorkerEvent`, `TaskEvent`, `Schedule`, `TaskRelation`, `TaskFilter`, `TaskStats`, `WorkerStats`, `ThroughputBucket`, `TimeRange`. Fully typed. |
| [x] | 0.6 | **BaseDBController ABC** | `db/abc.py` — full abstract interface (see Section 11). |
| [x] | 0.7 | **BaseLogController ABC** | `logging/abc.py` — `configure()`, `get_logger()`, `shutdown()`. |
| [x] | 0.8 | **BaseMonitoringExporter ABC** | `monitoring/abc.py` — `on_task_event()`, `on_worker_event()`, `update_stats()`, `serve()`, `shutdown()`. |
| [x] | 0.9 | **CeleryCnC stub** | `__init__.py` — constructor accepts workers + config, `run()` prints config and exits. |
| [x] | 0.10 | **WorkerRegistry** | `core/registry.py` — register by app or import path, group by broker, `get_apps()`, `get_brokers()`. Import-by-path logic working. |
| [x] | 0.11 | **Django scaffold** | Self-contained `web/settings.py`, `urls.py`, `wsgi.py`, `asgi.py`. `base.html` with nav skeleton. One placeholder view. Verify: Django starts on configured port. |
| [x] | 0.12 | **Test fixtures** | `docker-compose.yml` with Redis. Two mock Celery apps with dummy tasks. `conftest.py`. |
| [x] | 0.13 | **CI** | GitHub Actions: `uv sync`, `ruff check`, `mypy`, `pytest`. |

**After 0.13: "Repo is live. ABCs defined. Models defined. Django runs. Go."**

---

## 9. Parallel Task Lists

### File Ownership

```
Gandalf:  celery_cnc/core/*, celery_cnc/db/*
          celery_cnc/__init__.py, celery_cnc/config.py
          tests/test_registry.py, test_event_listener.py, test_db_*.py
          pyproject.toml, docker-compose.yml

Lisa:     celery_cnc/cnc/*, celery_cnc/monitoring/*, celery_cnc/logging/*
          tests/test_cnc_*.py, test_monitoring_*.py

Tom:      celery_cnc/web/*
          tests/test_web_*.py
```

No file is touched by two people. The ABCs + models are the contract between them.

---

### 9.1 Gandalf — Core Infrastructure & DB

| Done | # | Task | Size | Description |
|------|---|------|------|-------------|
| [x] | G1 | **SQLiteController** | L | Full `BaseDBController` impl. Schema creation with `schema_version` table. All CRUD. Filtered queries (state, worker, name, date range, fuzzy args via `LIKE`). Stats aggregation via SQL window functions (min/max/avg/percentiles). `migrate()` is a no-op for v1 but the version check exists. |
| [x] | G2 | **MemoryController** | M | Dict-based `BaseDBController`. Same interface, in-memory. For tests and ephemeral mode. |
| [x] | G3 | **DB tests** | M | Parametrized test suite covering both controllers against all ABC methods. Edge cases: large datasets, cleanup, concurrent reads. |
| [x] | G4 | **EventListener** | L | `multiprocessing.Process` per broker. Celery `Receiver`, event normalization into data model classes, push to `mp.Queue`. Reconnection logic, heartbeat handling, clean shutdown via SIGTERM. Adapt Flower's pattern (attributed). |
| [x] | G5 | **DBManager** | M | `multiprocessing.Process`. Reads from event queue, calls `db_controller.store_*()`. Batch inserts (configurable batch size / flush interval). Backpressure handling. Calls `migrate()` on startup. |
| [x] | G6 | **Task relationship tracking** | M | In DBManager: parse `parent_id`, `group_id`, `chord_id`, `root_id` from events. Build `TaskRelation` records. Expose via `get_task_relations(root_id)` — returns adjacency list for chain/chord/starmap DAGs. |
| [x] | G7 | **ProcessManager** | L | Start/stop all subprocesses based on config: N EventListeners + DBManager + optional PrometheusExporter + optional OTelExporter + WebServer. Start order, signal handling, clean shutdown (drain queues, flush DB, stop web). Child process health monitoring (restart crashed). |
| [x] | G8 | **CeleryCnC.run() real** | M | Wire config → WorkerRegistry → DBController → ProcessManager → block until shutdown. 2-line startup works end-to-end. |
| [x] | G9 | **Integration test** | L | Docker-compose: Redis + Celery workers from fixtures. Start CeleryCnC, send tasks, verify full pipeline: events → listener → queue → DB → query back. Test with 2 brokers. |
| [x] | G10 | **Dev mode** | S | Import-by-path resolution for workers. Test with fixture apps outside celery_cnc package tree. |

---

### 9.2 Lisa — CnC Operations, Monitoring, Logging

Agents in this role code against the ABCs and `WorkerRegistry`. Use `MemoryController` or mocked data until integration.

| Done | # | Task | Size | Description |
|------|---|------|------|-------------|
| [x] | L1 | **cnc/tasks.py** | M | `send_task(worker, name, args, kwargs, eta, countdown)`. `revoke(task_id, terminate, signal)`. `rate_limit(worker, task_name, rate)`. `time_limit(worker, task_name, soft, hard)`. All via `registry.get_app(name).control.*`. |
| [x] | L2 | **cnc/workers.py** | M | `pool_grow()`, `pool_shrink()`, `autoscale()`, `shutdown()`, `restart()`. Queue consumer: `add_consumer()`, `remove_consumer()`. Stats via inspector. |
| [x] | L3 | **cnc/broker.py** | M | Queue list + counts (RabbitMQ mgmt API / Redis `LLEN`). Purge queue (all, by name pattern). Adapt Flower's `utils/broker.py`. |
| [x] | L4 | **cnc/backend.py** | M | List stored results. Clear by task ID, name pattern, or all. |
| [x] | L5 | **Smart retry** | L | Retry single task (new send, bypass max_retries). Retry chain: walk `TaskRelation` from failure, re-send rest. Retry chord: re-send members + callback. Retry starmap: re-send failed items. |
| [x] | L6 | **cnc/health.py** | S | Broker ping, backend ping, heartbeat check. Structured health dict. |
| [x] | L7 | **Beat integration** | L | `core/beat.py`. Detect beat backend (file-based / django-celery-beat). Read schedules, CRUD periodic tasks (crontab + interval). Hot-reload. |
| [x] | L8 | **Stats aggregation** | M | `monitoring/stats.py`. `task_runtime_stats() → {min, max, avg, p50, p95, p99}`. `throughput()`. `state_distribution()`. `heatmap_data()`. Reads from DB controller. |
| [x] | L9 | **PrometheusExporter** | M | `monitoring/prometheus.py`. `BaseMonitoringExporter` subclass. Own `Process`. `prometheus_client` HTTP server on separate port. Gauges, counters, histograms. Reads from DB periodically. Metric names: `celery_cnc_*` with optional `flower_*` aliases. |
| [x] | L10 | **OTelExporter** | M | `monitoring/otel.py`. `BaseMonitoringExporter` subclass. Own `Process`. `TracerProvider` + `MeterProvider`. Spans for task lifecycle. Metrics mirror Prometheus. OTLP exporter to configurable endpoint. |
| [x] | L11 | **FileLogController** | S | `logging/file_handler.py`. `BaseLogController` subclass. `TimedRotatingFileHandler`, 24h, configurable dir. |
| [x] | L12 | **Logging integration** | S | Each process uses `log_controller.get_logger(process_name)`. Consistent format: `[timestamp] [process] [level] message`. |
| [x] | L13 | **Tests: CnC ops** | M | Mock Celery app, verify correct `control.*` calls. Test smart retry chain reconstruction. |
| [x] | L14 | **Tests: monitoring** | M | Prometheus metrics update correctly. OTel spans created. Enable/disable independently. |

---

### 9.3 Tom — Web Layer

Agents in this role own `web/`. Read from the DB controller (read-only); call CnC modules for actions. Mock CnC until available.

| Done | # | Task | Size | Description |
|------|---|------|------|-------------|
| [x] | T1 | **base.html + CSS** | M | Nav sidebar (Dashboard, Tasks, Workers, Broker, Beat). Pick CSS framework (Tailwind CDN or Pico CSS). Responsive. |
| [x] | T2 | **Dashboard view + template** | M | `views/dashboard.py` + `dashboard.html`. Worker count, task counts by state, latest 20 events feed, throughput number. Chart placeholders. |
| [x] | T3 | **Task list view** | L | `views/tasks.py` + `tasks/list.html`. Paginated table: name, state (color badge), worker, runtime, timestamp, args (truncated). Filter bar: state, worker, task name, date range, fuzzy search. Calls `db_controller.get_tasks(filters)`. |
| [x] | T4 | **Task detail view** | M | `tasks/detail.html`. Full info. Args/kwargs as formatted JSON. Traceback in collapsible block. Retry + Revoke buttons (POST to API). Link to chain graph. |
| [x] | T5 | **Worker list view** | M | `views/workers.py` + `workers/list.html`. Table: name, status badge, pool size, active tasks, registered tasks, queues. |
| [x] | T6 | **Worker detail view** | M | `workers/detail.html`. Stats, running tasks, pool info. Grow/Shrink/Shutdown buttons (POST). |
| [x] | T7 | **Charts: line + pie** | M | `static/js/charts.js` + Chart.js (vendored). JSON API endpoints in `views/api.py`: throughput timeseries, state distribution, task type distribution. Render on dashboard + task list. |
| [x] | T8 | **Charts: heatmap** | M | Tasks per hour × day-of-week. Chart.js matrix plugin. API endpoint for data. |
| [x] | T9 | **Task DAG visualization** | L | `views/graphs.py` + `tasks/graph.html` + `static/js/dag.js` + cytoscape.js (vendored). API returns `{nodes, edges}` from `db_controller.get_task_relations()`. Nodes colored by state. Self-loops for retries (×N). Zoom/pan. Click → task detail. |
| [x] | T10 | **Broker view** | M | `views/broker.py` + `broker.html`. Queue table: name, pending, consumers. Purge button (calls `cnc/broker.py`). Backend result count + clear. |
| [x] | T11 | **Beat schedule view** | L | `views/beat.py` + `beat.html`. Schedule table. Add/edit/delete forms. Crontab + interval. Enabled toggle. Calls `cnc/beat.py`. |
| [x] | T12 | **Real-time updates** | L | `static/js/realtime.js`. Polling first: `setInterval` fetching `/api/events/latest?since=<ts>`. Update dashboard counters, prepend events, flash updated rows. API endpoint in `views/api.py`. |
| [x] | T13 | **Fuzzy search UI** | M | `static/js/search.js`. Debounced input, form submit, highlight matches. |
| [x] | T14 | **JSON API layer** | M | `views/api.py` — all endpoints: `/api/tasks/`, `/api/tasks/<id>/`, `/api/tasks/<id>/relations/`, `/api/workers/`, `/api/stats/*`, `/api/events/latest/`, `/api/beat/schedules/`. POST endpoints for actions. |
| [x] | T15 | **Static bundling** | S | Vendor Chart.js, cytoscape into `static/vendor/`. `collectstatic` works. Assets in wheel. |
| [x] | T16 | **Tests** | M | Django test client. Pages render. API returns correct shapes. |

---

## 10. Phases

Work is organized in phases (not calendar weeks). Agents pick tasks from the phase that unblocks them; mark tasks done by setting the Done column to `[x]` in `TODO.md`.

```
Phase 0:    Gandalf bootstraps (solo) — Section 8
            ──────────────────────────────────────────────────

Phase 1:    Gandalf: G1 (SQLite) ───────▶ G4 (EventListener)
            Lisa:    L1 (tasks) ─▶ L2 (workers) ─▶ L3 (broker)
            Tom:     T1 (layout) ─▶ T2 (dashboard) ─▶ T3 (task list)

Phase 2:    Gandalf: G5 (DBManager) ─▶ G6 (relations) ─▶ G7 (ProcMgr)
            Lisa:    L4 (backend) ─▶ L5 (smart retry) ─▶ L7 (beat)
            Tom:     T4 (task detail) ─▶ T5+T6 (workers) ─▶ T7 (charts)

Phase 3:    Gandalf: G8 (run()) ──▶ G9 (integration test) ──▶ G10
            Lisa:    L8 (stats) ─▶ L9 (prometheus) ─▶ L10 (otel)
            Tom:     T8 (heatmap) ─▶ T9 (DAG) ─▶ T10 (broker)

Phase 4:    Gandalf: G2+G3 (MemoryCtrl + DB tests) ──▶ hardening
            Lisa:    L11+L12 (logging) ─▶ L13+L14 (tests)
            Tom:     T11 (beat) ─▶ T12 (realtime) ─▶ T13+T14 (search+API)

Phase 5:    All:     T15+T16 ──▶ wheel build ──▶ integration ──▶ README
```

**Marking tasks complete:** In `TODO.md`, find the task row (e.g. `| [x] | G1 |`) and change `[ ]` to `[x]` (e.g. `| [x] | G1 |`). Commit the change.

---

## 11. Interface Contracts

The exact ABCs Gandalf defines in Phase 0. Everyone codes against these.

### BaseDBController

```python
from abc import ABC, abstractmethod
from typing import Sequence

class BaseDBController(ABC):
    """Subclass to provide a custom storage backend."""

    @abstractmethod
    def initialize(self) -> None: ...

    # Migration
    @abstractmethod
    def get_schema_version(self) -> int: ...
    @abstractmethod
    def migrate(self, from_version: int, to_version: int) -> None: ...

    # Tasks
    @abstractmethod
    def store_task_event(self, event: TaskEvent) -> None: ...
    @abstractmethod
    def get_tasks(self, filters: TaskFilter | None = None) -> Sequence[Task]: ...
    @abstractmethod
    def get_task(self, task_id: str) -> Task | None: ...

    # Task relations
    @abstractmethod
    def store_task_relation(self, relation: TaskRelation) -> None: ...
    @abstractmethod
    def get_task_relations(self, root_id: str) -> Sequence[TaskRelation]: ...

    # Workers
    @abstractmethod
    def store_worker_event(self, event: WorkerEvent) -> None: ...
    @abstractmethod
    def get_workers(self) -> Sequence[Worker]: ...
    @abstractmethod
    def get_worker(self, hostname: str) -> Worker | None: ...

    # Stats
    @abstractmethod
    def get_task_stats(self, task_name: str | None, time_range: TimeRange | None) -> TaskStats: ...
    @abstractmethod
    def get_throughput(self, time_range: TimeRange, bucket_seconds: int) -> Sequence[ThroughputBucket]: ...
    @abstractmethod
    def get_state_distribution(self) -> dict[str, int]: ...
    @abstractmethod
    def get_heatmap(self, time_range: TimeRange | None) -> list[list[int]]: ...

    # Beat
    @abstractmethod
    def get_schedules(self) -> Sequence[Schedule]: ...
    @abstractmethod
    def store_schedule(self, schedule: Schedule) -> None: ...
    @abstractmethod
    def delete_schedule(self, schedule_id: str) -> None: ...

    # Maintenance
    @abstractmethod
    def cleanup(self, older_than_days: int) -> int: ...
    @abstractmethod
    def close(self) -> None: ...
```

### BaseLogController

```python
class BaseLogController(ABC):
    @abstractmethod
    def configure(self, config: CnCConfig) -> None: ...
    @abstractmethod
    def get_logger(self, name: str) -> logging.Logger: ...
    @abstractmethod
    def shutdown(self) -> None: ...
```

### BaseMonitoringExporter

```python
class BaseMonitoringExporter(ABC):
    """Subclass to create custom monitoring exporters.
    Each runs as its own subprocess."""

    @abstractmethod
    def on_task_event(self, event: TaskEvent) -> None: ...
    @abstractmethod
    def on_worker_event(self, event: WorkerEvent) -> None: ...
    @abstractmethod
    def update_stats(self, stats: TaskStats) -> None: ...
    @abstractmethod
    def serve(self) -> None:
        """Start serving (e.g. HTTP for Prometheus). Blocks."""
        ...
    @abstractmethod
    def shutdown(self) -> None: ...
```

---

## 12. Open Questions

| # | Question | Default |
|---|----------|---------|
| Q1 | Real-time: polling vs. Channels vs. SSE? | Polling first, Channels upgrade path. |
| Q2 | Beat backends: which to support? | File-based + django-celery-beat. |
| Q3 | Metric namespace: `celery_cnc_*` vs. `flower_*`? | `celery_cnc_*` with config flag for `flower_*`. |
| Q4 | Per-task CPU/memory: realistic? | Best-effort from `inspect().stats()`. |
| Q5 | SQLAlchemy Core vs. raw sqlite3? | SQLAlchemy Core. |
| Q6 | CSS framework? | Gandalf picks in Phase 0. Suggestion: Tailwind CDN or Pico. |
