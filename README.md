# AskDoc

AskDoc is a small **RAG** (Retrieval-Augmented Generation) service: you ingest text documents asynchronously, store chunk embeddings in Postgres/pgvector, and ask questions that are answered from the retrieved context via an LLM.

It is designed as a learning / portfolio project with a clear split between a FastAPI edge and a two-stage Celery pipeline.

## Features

- **Async document ingestion** — `POST /documents` returns `202` after saving the file and enqueueing work
- **Two-stage pipeline** — chunking and embedding run on separate RabbitMQ queues so they can scale independently
- **Structure-aware chunking** — prefers paragraphs and sentences (with soft breaks on punctuation) over fixed character windows
- **Vector search** — cosine similarity over pgvector (HNSW)
- **RAG answers** — `POST /query` retrieves top-k chunks, then completes with an OpenAI-compatible LLM (Ollama by default)
- **Retrieval for agents** — `POST /search-matches` returns similarity matches only (no LLM), for tools that generate their own answer
- **Optional observability** — Langfuse tracing when enabled

## Architecture

```
POST /documents
  → save text to local storage
  → enqueue process_document  (queue: document-ingestion)
       → split into chunks
       → enqueue process_chunk per chunk  (queue: document-chunks)
            → embed + upsert into Postgres/pgvector

POST /search-matches   (retrieval only — for agent tools)
  → embed question
  → similarity search
  → { query, matches }

POST /query            (full RAG — for humans / demos)
  → same retrieval as /search-matches
  → LLM completion with retrieved context
  → { query, answer, matches }
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

Give the worker a moment to chunk and embed before querying or searching.

### Query (RAG answer + matches)

Use when you want AskDoc to generate the final answer:

```bash
curl -X POST http://127.0.0.1:8000/api/askdoc/query \
  -H "Content-Type: application/json" \
  -d '{"query":"Where are embeddings stored?","top_k":5}'
```

Response: `{ "query", "answer", "matches" }`.

### Search matches (retrieval only)

Use when another service/agent (e.g. OpsDesk) will generate the answer:

```bash
curl -X POST http://127.0.0.1:8000/api/askdoc/search-matches \
  -H "Content-Type: application/json" \
  -d '{"query":"Where are embeddings stored?","top_k":5}'
```

Response: `{ "query", "matches" }` — no `answer`, no LLM call.

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
  use_cases/     # ingest + search-matches + query
  messaging/     # Celery app, tasks, dispatcher
  processing/    # chunking + embeddings
  storage/       # local files + pgvector store
  generation/    # LLM client + RAG prompts
tests/
  processing/    # chunking
  use_cases/     # ingest + search-matches + query
  messaging/     # Celery tasks
  generation/    # RAG prompts
  api/           # route-level tests
```

## GitHub Issue automation on a self-hosted Mac

The workflow in `.github/workflows/harness-issue.yml` imports an AskDoc Issue when the `agent:run` label is added. It checks out AskDoc and `slcosentino1/autonomous-engineering-harness` into separate directories, then calls the existing `github import` command with `--publish-pr`. The Harness creates a proposal and stops at `awaiting_approval`. The workflow never approves work, runs on pull request events, or merges pull requests.

### Runner setup

Register one dedicated, persistent macOS self-hosted runner for this repository. In GitHub, open Settings → Actions → Runners → New self-hosted runner, choose macOS and the machine architecture, and follow the displayed download and registration commands. The required labels are self-hosted, macOS, and askdoc-agent; GitHub adds the first two, and you add askdoc-agent. Use the repository URL https://github.com/slcosentino1/AskDoc. Keep the registration token private; GitHub's setup token is temporary and must not be committed.

Run the runner service as a dedicated macOS user. Install it as a service with the runner's `svc.sh` commands from GitHub's setup instructions, then start it and confirm that it is online with the askdoc-agent label. Keep this one runner and its `_work` directory persistent: the Harness stores its Issue-to-workflow registry under `.engineering/workflows` in the AskDoc checkout. The workflow disables checkout cleanup for AskDoc so repeat events can reuse that registry. Do not delete that directory while an Issue workflow is active.

The job explicitly adds /opt/homebrew/bin, /usr/local/bin, and the runner account's .local/bin to PATH. Install Python, Codex CLI, Aily CLI, and GitHub CLI (gh) in one of those directories, or set the repository Actions variables HARNESS_PYTHON, HARNESS_CODEX_CLI, and HARNESS_AILY_CLI to their executable paths. Set HARNESS_EXTRA_PATH to additional absolute runtime directories, separated by colons, such as the Node installation used by an NVM-installed Codex CLI. The runner service does not inherit an interactive terminal's PATH.

Use Python 3.11 or newer. Authenticate Codex and Aily under the same macOS account that runs the runner service, not only under an interactive account. Configure and verify Codex as that account:

    codex login
    codex login status

Set up the Aily/Claude credentials through the approved Aily login flow. For an Entra-backed setup, Aily provides:

    aily claude --entra --login

The job checks codex login status and verifies that Aily exposes its claude command. Harness calls Aily for the actual plan review; authentication failures stop the import with a failed Harness status or a CLI error in the job log. Do not print or copy provider keys into workflow logs, Issue text, or repository files. In particular, do not call aily get-api-key in a workflow because it prints a provider key. If a provider needs environment variables, configure them for the runner service account and restart the service before testing.

### GitHub permissions and configuration

The workflow grants its GitHub Actions token only issues: read; repository contents permission is none. The import step receives this token as GH_TOKEN for Harness GitHub CLI operations. The Harness passes GitHub credentials only to its gh subprocesses and removes them from Codex and Aily environments.

Both checkout steps use the AskDoc repository secret ASKDOC_CHECKOUT_TOKEN, a fine-grained token with read-only Contents access to only slcosentino1/AskDoc and slcosentino1/autonomous-engineering-harness. This separate token is used by the checkout actions only. Checkout credentials are not persisted in either repository's Git configuration.

The default total Claude/Aily budget is USD 0.50 per imported workflow. Set the AskDoc repository Actions variable `HARNESS_GITHUB_BUDGET_USD` to a different conservative amount if needed. This is a variable, not a secret. The workflow token has no write permissions. For later local Pull Request publication, the operator's local gh authentication must have repository Contents and Pull Requests write access. Authenticate that local CLI separately, for example with:

    gh auth login --hostname github.com

This local credential is used only when the operator runs approve or resume; it is not the workflow token.

Before enabling the label, confirm that the runner has a clean AskDoc checkout apart from `.engineering/workflows`. Before checkout, the workflow fails if other tracked or untracked workspace changes remain; it does not clean or overwrite them. After a local approval changes tracked AskDoc files, finish publication and reconcile the runner worktree to the default branch before starting a different Issue workflow. The per-Issue Actions concurrency group serializes repeated runs for that Issue, and the Harness registry returns the existing workflow on a duplicate import. Keep one persistent runner for this target; separate runner machines do not share the local registry.

### Triggering and approving an Issue

Add the `agent:run` label to an Issue in slcosentino1/AskDoc. The workflow runs from the repository's default branch, checks out that branch, and ignores pull request issues and events from other repositories. Issue text is treated as untrusted task input by the Harness; the job does not execute code from an Issue branch.

The Actions job summary reports the workflow ID, status, and proposal path. The proposal is stored in the runner's AskDoc checkout at:

    $GITHUB_WORKSPACE/AskDoc/.engineering/workflows/WORKFLOW_ID/proposal.md

Copy the AskDoc target path and workflow ID from the job summary, then review the proposal on the Mac. From a terminal running as the same account as the runner:

    export HARNESS_GITHUB_ALLOWED_REPOSITORIES="slcosentino1/AskDoc"
    python3 /path/to/autonomous-engineering-harness/harness/orchestrator.py status \
      --target /absolute/path/to/runner/_work/AskDoc/AskDoc \
      --workflow-id WORKFLOW_ID

After reviewing the proposal, explicitly approve it:

    python3 /path/to/autonomous-engineering-harness/harness/orchestrator.py approve \
      --target /absolute/path/to/runner/_work/AskDoc/AskDoc \
      --workflow-id WORKFLOW_ID

If a saved stage failed, inspect status and retry only that stage with:

    python3 /path/to/autonomous-engineering-harness/harness/orchestrator.py resume \
      --target /absolute/path/to/runner/_work/AskDoc/AskDoc \
      --workflow-id WORKFLOW_ID

resume does not approve a proposal. The initial GitHub job stops at `awaiting_approval`; no automatic approval path is configured.

### Pull Request publication

`--publish-pr` records publication permission in the workflow authorization; it does not publish during Issue import. After local approval, implementation, code review, delivery verification, and the Harness commitment gate all pass, approve or resume can publish the reviewed change. Publication uses the locally authenticated gh account, requires its write access, a clean starting target, an unchanged default branch, and the matching AskDoc origin. The Harness creates a reviewed branch and Pull Request but never merges it. The GitHub Actions token only needs read access and cannot publish the Pull Request.

Manual setup still required: commit and push the workflow and documentation to AskDoc's default branch, register and label the Mac runner, install the CLIs and Python, configure Codex/Aily authentication for the runner service user, create the read-only ASKDOC_CHECKOUT_TOKEN secret, and optionally set the Actions variables for custom CLI paths, extra PATH entries, or budget. No GitHub workflow run or runner registration was performed as part of this repository change.

## Project ownership and permissions

Copyright © 2026 Sebastian Cosentino. All rights reserved.

This repository is public for viewing and evaluation. Unless you have separate, express written permission from the copyright holder, no license is granted to use, copy, modify, adapt, publish, distribute, sublicense, or create derivative works from this project's code or documentation. Public visibility on GitHub does not place this project in the public domain or make it open source.

The project may include references to and integrations with third-party tools. Their names and trademarks belong to their respective owners; this notice applies only to original material in this repository.
