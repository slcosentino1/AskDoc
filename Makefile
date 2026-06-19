.PHONY: install-dev check compile lint fix format format-check dev docker-up docker-down worker start stop

VENV_PYTHON := $(wildcard .venv/bin/python)
PYTHON ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),python3)
RUFF ?= $(PYTHON) -m ruff
UVICORN ?= $(PYTHON) -m uvicorn
CELERY ?= $(PYTHON) -m celery

CELERY_APP := askdoc.messaging.celery_app
CELERY_QUEUES := document-ingestion,document-chunks

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

check: compile lint format-check

compile:
	$(PYTHON) -m compileall src

lint:
	$(RUFF) check src

fix:
	$(RUFF) check src --fix
	$(RUFF) format src

format:
	$(RUFF) format src

format-check:
	$(RUFF) format --check src

dev:
	$(UVICORN) askdoc.main:app --reload

docker-up:
	docker compose up -d

docker-down:
	docker compose stop

worker:
	$(CELERY) -A $(CELERY_APP) worker --loglevel=info -Q $(CELERY_QUEUES)

start:
	@chmod +x scripts/dev.sh
	@./scripts/dev.sh

stop:
	@chmod +x scripts/stop-dev.sh
	@./scripts/stop-dev.sh
