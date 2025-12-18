#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN=${PYTHON:-python3}

cd "$ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
  echo "[setup] Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "[setup] Installing dependencies (this requires internet access the first time)"
pip install --upgrade pip
pip install -e ".[dev]"

if [ "${1:-}" = "--serve" ]; then
  echo "[run] Starting FastAPI dev server at http://localhost:8000"
  uvicorn src.server.main:app --reload
else
  echo "[test] Running pytest suite"
  pytest
fi
