# celery_cnc

Celery Command & Control (CnC) is a multi-worker monitoring, management, and visualization tool for Celery.
It ships with a Django-based UI, a lightweight event listener/collector, and helper utilities for inspecting
queues, tasks, workers, and beat schedules.

## Features

- Task list with filtering, sorting, and details (args/kwargs/result/traceback).
- Task relation graph visualization.
- Worker fleet overview and per-worker drill-down.
- Broker queue inspection and purge actions.
- Beat schedule overview and editor.
- Pluggable storage (SQLite by default).

## Quickstart (demo)

Requirements: Python >= 3.13, `uv`, and Docker (for the demo broker/redis).

```bash
make demo-infra
```

Start the demo workers in separate terminals:

```bash
make demo-worker-math
```

```bash
make demo-worker-text
```

Launch the CnC supervisor + web UI:

```bash
make demo-cnc
```

Then open `http://127.0.0.1:8000`.

To enqueue demo tasks:

```bash
make demo-tasks
```

## Running the web UI

If you already have Celery workers and a broker running, you can point the UI at your apps via
`CELERY_CNC_WORKERS` and run the web server:

```bash
export CELERY_CNC_WORKERS="your_app.celery:app,another_app.celery:app"
uv run python celery_cnc/web/manage.py migrate
uv run python -m celery_cnc.web.devserver --host 127.0.0.1 --port 8000
```

The UI reads task/worker data from the CnC SQLite store (see configuration below).

## Configuration

Environment variables used by the web app and supervisor:

- `CELERY_CNC_DB_PATH`: Path to the SQLite database (default: `celery_cnc.db`).
- `CELERY_CNC_WORKERS`: Comma-separated Celery app import paths.
- `CELERY_CNC_RETENTION_DAYS`: How many days of task/worker history to keep (default: `7`).
- `CELERY_CNC_WEB_HOST`: Host interface for the web UI (default: `127.0.0.1`).
- `CELERY_CNC_WEB_PORT`: Port for the web UI (default: `8000`).
- `CELERY_CNC_LOG_DIR`: Directory for logs (default: `./logs`).
- `CELERY_CNC_PURGE_DB`: Set to `true` to delete the SQLite DB on startup.
- `CELERY_CNC_SECRET_KEY`: Django secret key override for the web UI.

`BROKER_URL` and `BACKEND_URL` are standard Celery settings used by the demo math worker. The demo text and sleep
workers use `BROKER2_URL`/`BACKEND2_URL` and `BROKER3_URL`/`BACKEND3_URL` respectively.

## Library usage

For programmatic use, you can start the supervisor from Python:

```python
from celery_cnc import CeleryCnC

cnc = CeleryCnC("your_app.celery:app")
cnc.run()
```

## Development

Run checks locally:

```bash
uv run precommit
```

Run tests directly:

```bash
uv run pytest
```

Type checking:

```bash
uv run mypy
```

## Project structure

- `celery_cnc/`: core logic, DB controllers, web app.
- `celery_cnc/web/`: Django templates, static assets, and views.
- `demo/`: demo workers and task scripts.
- `tests/`: unit and integration tests.
