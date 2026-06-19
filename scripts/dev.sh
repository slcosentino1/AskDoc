#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"
CELERY="${ROOT}/.venv/bin/celery"

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing .venv. Run:"
  echo "  python3 -m venv .venv"
  echo "  source .venv/bin/activate"
  echo "  pip install -e '.[dev]'"
  exit 1
fi

WORKER_PID=""

cleanup() {
  if [[ -n "$WORKER_PID" ]] && kill -0 "$WORKER_PID" 2>/dev/null; then
    echo "Stopping Celery worker (pid $WORKER_PID)..."
    kill "$WORKER_PID" 2>/dev/null || true
    wait "$WORKER_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting RabbitMQ..."
docker compose up -d

echo "Waiting for RabbitMQ..."
for _ in $(seq 1 30); do
  if docker compose exec -T rabbitmq rabbitmq-diagnostics -q ping >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Starting Celery worker..."
"$CELERY" -A askdoc.messaging.celery_app worker \
  --loglevel=info \
  -Q document-ingestion,document-chunks &
WORKER_PID=$!

echo "Starting API on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop API and worker (RabbitMQ keeps running in Docker)."
"$PYTHON" -m uvicorn askdoc.main:app --reload
