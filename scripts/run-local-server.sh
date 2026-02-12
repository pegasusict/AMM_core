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

PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

exec "$PYTHON_BIN" -m uvicorn main:app --app-dir "$ROOT_DIR/src" --host "$HOST" --port "$PORT" --reload
