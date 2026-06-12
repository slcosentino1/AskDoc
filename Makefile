.PHONY: install-dev check compile lint fix format format-check dev

PYTHON ?= python3
RUFF ?= $(PYTHON) -m ruff
UVICORN ?= $(PYTHON) -m uvicorn

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
