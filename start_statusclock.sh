#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x ".venv/bin/python" ]; then
  PYTHON_EXE=".venv/bin/python"
else
  PYTHON_EXE="python3"
fi

if ! "$PYTHON_EXE" -c "import dotenv, PySide6, requests" >/dev/null 2>&1; then
  echo "Dependencias em falta."
  echo
  echo "Corre primeiro o setup nesta pasta:"
  echo "  $SCRIPT_DIR/setup_statusclock.sh"
  exit 1
fi

exec "$PYTHON_EXE" -m src.statusclock

