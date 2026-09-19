#!/bin/bash
set -euo pipefail
AUDIT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOOK_DIR="$(cd "$AUDIT_DIR/../../../.." && pwd)"
AUDIT_PYTHON="${AUDIT_PYTHON:-$BOOK_DIR/.venv/bin/python}"
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTHONHASHSEED=0
export TZ=UTC
"$AUDIT_PYTHON" -B "$AUDIT_DIR/bootstrap.py"
export PYTHONPATH="$AUDIT_DIR/deps"
exec "$AUDIT_PYTHON" -B "$AUDIT_DIR/run_all.py" "$@"
