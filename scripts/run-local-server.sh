#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_DIR="$ROOT_DIR/testrun/amm"

mkdir -p \
  "$BASE_DIR/import" \
  "$BASE_DIR/process" \
  "$BASE_DIR/export" \
  "$BASE_DIR/music" \
  "$BASE_DIR/art"

# Prefer project venv if present, unless caller explicitly sets PYTHON_BIN.
if [[ -z "${PYTHON_BIN:-}" ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
if [[ -z "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="sqlite+aiosqlite:///$ROOT_DIR/amm.db"
fi

export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

exec "$PYTHON_BIN" -m uvicorn main:app --app-dir "$ROOT_DIR/src" --host "$HOST" --port "$PORT" --reload
