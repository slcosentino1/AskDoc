# AskDoc

Mini RAG service built with FastAPI.

## Prerequisites

- Python 3.11+
- Docker (for RabbitMQ)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
make install-dev
cp .env.example .env
```

## Running locally

### All-in-one (recommended)

Starts RabbitMQ in Docker, the Celery worker in the background, and the API in the foreground:

```bash
make start
```

Press `Ctrl+C` to stop the API and worker. RabbitMQ keeps running in Docker until you run `make stop`.

To stop everything (API, worker, and RabbitMQ):

```bash
make stop
```

### Separate terminals

Useful when you want isolated logs for each process:

```bash
make docker-up   # terminal 1 — RabbitMQ
make dev         # terminal 2 — FastAPI on http://127.0.0.1:8000
make worker      # terminal 3 — Celery (document-ingestion + document-chunks)
```

Stop RabbitMQ with `make docker-down`.

## Test the API

```bash
curl -X POST http://127.0.0.1:8000/api/askdoc/documents \
  -H "Content-Type: application/json" \
  -d '{"file_name":"test.txt","content":"Hello from AskDoc."}'
```

RabbitMQ management UI: http://localhost:15672 (guest / guest).

## Makefile commands

| Command | Description |
|---------|-------------|
| `make install-dev` | Install the package in editable mode with dev dependencies |
| `make start` | Start RabbitMQ, worker, and API (`scripts/dev.sh`) |
| `make stop` | Stop RabbitMQ and local Celery workers |
| `make dev` | Run the FastAPI app with reload |
| `make worker` | Run the Celery worker |
| `make docker-up` | Start RabbitMQ in Docker (detached) |
| `make docker-down` | Stop RabbitMQ |
| `make check` | Compile, lint, and format-check |
| `make fix` | Auto-fix lint issues and format code |
| `make format` | Format code with ruff |

The Makefile uses `.venv/bin/python` automatically when the virtualenv exists.
