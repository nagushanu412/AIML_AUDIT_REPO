#!/usr/bin/env bash
set -euo pipefail
alembic upgrade head
PORT="${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
