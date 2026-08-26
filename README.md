# AskDoc

AskDoc is a small **RAG** (Retrieval-Augmented Generation) service: you ingest text documents asynchronously, store chunk embeddings in Postgres/pgvector, and ask questions that are answered from the retrieved context via an LLM.

It is designed as a learning / portfolio project with a clear split between a FastAPI edge and a two-stage Celery pipeline.

## Features

- **Async document ingestion** — `POST /documents` returns `202` after saving the file and enqueueing work
- **Two-stage pipeline** — chunking and embedding run on separate RabbitMQ queues so they can scale independently
- **Structure-aware chunking** — prefers paragraphs and sentences (with soft breaks on punctuation) over fixed character windows
- **Vector search** — cosine similarity over pgvector (HNSW)
- **RAG answers** — retrieve top-k chunks, then complete with an OpenAI-compatible LLM (Ollama by default)
- **Optional observability** — Langfuse tracing when enabled

## Architecture

```
POST /documents
  → save text to local storage
  → enqueue process_document  (queue: document-ingestion)
       → split into chunks
       → enqueue process_chunk per chunk  (queue: document-chunks)
            → embed + upsert into Postgres/pgvector

POST /query
  → embed question
  → similarity search
  → LLM completion with retrieved context
```

**Why two queues?** Chunking is mostly sequential file I/O; embedding is CPU-bound and parallelizable. Separate queues isolate failures (a failed embed retries one chunk, not the whole document) and allow different worker counts per stage.

## Tech stack

| Layer | Choice |
|-------|--------|
| API | FastAPI, Pydantic Settings, Uvicorn |
| Async jobs | Celery + RabbitMQ |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, 384-d) |
| Vector store | PostgreSQL 16 + pgvector |
| LLM | OpenAI SDK against Ollama / any OpenAI-compatible API |
| Observability | Langfuse (optional) |
| Quality | Ruff, pytest |

## Prerequisites

- Python **3.11+**
- Docker (RabbitMQ + Postgres via Compose)
- [Ollama](https://ollama.com/) with a chat model (default: `llama3.2`), or another OpenAI-compatible endpoint

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
make install-dev
cp .env.example .env
```

Defaults in `.env.example` match the Compose services (`guest`/`guest` for RabbitMQ, `askdoc`/`askdoc` for Postgres).

Pull an Ollama model if you use the defaults:

```bash
ollama pull llama3.2
```

## Running locally

### All-in-one (recommended)

Starts Postgres + RabbitMQ, a Celery worker (both queues), and the API:

```bash
make start
```

- API: http://127.0.0.1:8000
- RabbitMQ UI: http://localhost:15672 (`guest` / `guest`)

`Ctrl+C` stops the API and worker. Docker services keep running until:

```bash
make stop
```

### Separate terminals

```bash
make docker-up   # Postgres + RabbitMQ
make worker      # Celery: document-ingestion + document-chunks
make dev         # FastAPI with reload
```

## API usage

### Ingest a document

```bash
curl -X POST http://127.0.0.1:8000/api/askdoc/documents \
  -H "Content-Type: application/json" \
  -d '{"file_name":"notes.txt","content":"AskDoc stores embeddings in Postgres with pgvector.\n\nIngestion is asynchronous."}'
```

Example response (`202`):

```json
{"job_id":"...","status":"queued"}
```

Give the worker a moment to chunk and embed before querying.

### Query

```bash
curl -X POST http://127.0.0.1:8000/api/askdoc/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Where are embeddings stored?","top_k":5}'
```

Response includes `answer` plus the retrieved `matches` (chunk text + score).

## Tests and checks

```bash
make test    # pytest
make check   # compile + ruff + format check + tests
make fix     # auto-fix lint/format
```

Tests mirror `src/askdoc/` (`tests/processing`, `tests/use_cases`, `tests/messaging`, …). They cover chunking, use cases, Celery task bodies (broker mocked via `send_task` / `.run()`), and HTTP routes with dependency overrides. No live RabbitMQ/Postgres required for `make test`.

## Makefile reference

| Command | Description |
|---------|-------------|
| `make install-dev` | Editable install with `[dev]` extras |
| `make start` / `make stop` | Local stack via `scripts/dev.sh` / `scripts/stop-dev.sh` |
| `make docker-up` / `make docker-down` | Start/stop Compose services |
| `make worker` | Celery worker (`solo` pool, concurrency 1) |
| `make dev` | API with reload |
| `make test` | Run pytest |
| `make check` / `make fix` / `make format` | Quality gates |

The Makefile prefers `.venv/bin/python` when the virtualenv exists.

## Configuration

Settings use the `ASKDOC_` prefix (see `.env.example`), including:

- `ASKDOC_DOCUMENT_CHUNK_SIZE` / `ASKDOC_DOCUMENT_CHUNK_OVERLAP` — max chunk size and overlap (characters)
- `ASKDOC_EMBEDDING_MODEL_NAME` — must match for ingest and query
- `ASKDOC_LLM_*` — provider endpoint and model
- `ASKDOC_LANGFUSE_*` — set `ASKDOC_LANGFUSE_ENABLED=true` plus keys to enable tracing

## Project layout

```
src/askdoc/
  api/           # FastAPI routes
  use_cases/     # ingest + query orchestration
  messaging/     # Celery app, tasks, dispatcher
  processing/    # chunking + embeddings
  storage/       # local files + pgvector store
  generation/    # LLM client + RAG prompts
tests/
  processing/    # chunking
  use_cases/     # ingest + query
  messaging/     # Celery tasks
  generation/    # RAG prompts
  api/           # route-level tests
```
