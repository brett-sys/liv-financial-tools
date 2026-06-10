#!/bin/bash
# LIFI Agent Toolkit — start Flask on port 5055
# Paths are relative to this script (no hardcoded /Users/...).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${LIFI_PORT:-5055}"

# Virtualenv: prefer repo .venv, then ../venv next to repo, then venv inside repo
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/../venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/../venv/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/venv/bin/activate"
fi

PY="${PYTHON:-python3}"

# Kill any existing instance on this port (optional)
if command -v lsof >/dev/null 2>&1; then
  lsof -ti ":$PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo ""
echo "======================================"
echo "  LIFI Agent Toolkit"
echo "======================================"
echo "  App dir: $SCRIPT_DIR"
echo "  Local:   http://localhost:$PORT"
echo "  Public:  https://tools.livfinancialgroup.com"
echo ""
echo "  Brett:    https://tools.livfinancialgroup.com/brett"
echo "  Kevin:    https://tools.livfinancialgroup.com/kevin"
echo "  Easton:   https://tools.livfinancialgroup.com/easton"
echo "  Carmello: https://tools.livfinancialgroup.com/carmello"
echo "  Noah:     https://tools.livfinancialgroup.com/noah"
echo "  Mahan:    https://tools.livfinancialgroup.com/mahan"
echo "  Alex:     https://tools.livfinancialgroup.com/alex"
echo "  Kaiden:   https://tools.livfinancialgroup.com/kaiden"
echo "  Devon:    https://tools.livfinancialgroup.com/devon"
echo "  Nico:     https://tools.livfinancialgroup.com/nico"
echo "  Harlie:   https://tools.livfinancialgroup.com/harlie"
echo "  Joe:      https://tools.livfinancialgroup.com/joe"
echo "  Blake:    https://tools.livfinancialgroup.com/blake"
echo "  Alberto:  https://tools.livfinancialgroup.com/alberto"
echo "  JL:       https://tools.livfinancialgroup.com/jl"
echo "======================================"
echo ""

exec "$PY" -c "
from app import app
import scheduler
app.run(host='0.0.0.0', port=int('$PORT'), debug=False)
"
