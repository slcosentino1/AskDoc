#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Stopping RabbitMQ..."
docker compose stop

echo "Stopping local Celery workers for askdoc.messaging.celery_app..."
pkill -f "celery -A askdoc.messaging.celery_app worker" 2>/dev/null || true

echo "Done."
