SHELL := /bin/sh

BROKER1_URL ?= amqp://guest:guest@localhost:5672//
BACKEND1_URL ?= redis://localhost:6379/0
BROKER2_URL ?= amqp://guest:guest@localhost:5673//
BACKEND2_URL ?= redis://localhost:6380/0
BROKER3_URL ?= redis://localhost:6381/0
BACKEND3_URL ?= db+postgresql://postgres:postgres@localhost:5432/postgres

CELERY_CNC_DB_PATH ?= celery_cnc.db
CELERY_CNC_WORKERS ?= demo.worker_math:app,demo.worker_text:app,demo.worker_sleep:app
CELERY_CNC_WEB_HOST ?= 127.0.0.1
CELERY_CNC_WEB_PORT ?= 8000

export BROKER_URL
export BACKEND_URL
export CELERY_CNC_DB_PATH
export CELERY_CNC_WORKERS
export CELERY_CNC_WEB_HOST
export CELERY_CNC_WEB_PORT

.PHONY: build build_frontend \
 		install \
 		lint

build_frontend:
	npm --prefix frontend/graph-ui run build

build: build_frontend

install:
	uv sync --all-extras --dev --frozen
	uv run pre-commit install

lint:
	CELERY_CNC_WORKERS= uv run pre-commit run --all-files

demo_stop_infra:
	docker compose -p celery_cnc_demo -f demo/infra.docker-compose.yml down --volumes --remove-orphans

demo_start_infra:
	docker compose -p celery_cnc_demo -f demo/infra.docker-compose.yml up -d

demo_worker_math: demo_start_infra
	uv run celery -A demo.worker_math worker -n math@%h -l INFO

demo_worker_text: demo_start_infra
	uv run celery -A demo.worker_text worker -n text@%h -l INFO

demo_worker_sleep: demo_start_infra
	BROKER3_URL=$(BROKER3_URL) BACKEND3_URL=$(BACKEND3_URL) uv run celery -A demo.worker_sleep worker -n sleep@%h -l INFO

demo_tasks:
	uv run python demo/schedule_demo_tasks.py

demo_graph_tasks:
	uv run python demo/schedule_demo_tasks.py

demo_cnc: build
	uv run python celery_cnc/web/manage.py migrate
	uv run python demo/main.py
