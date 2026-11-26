#!/bin/bash
# m-hosts runner: loads ../managed.env into the environment (never echoes it) and runs run.py.
# Usage: bash run.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
set -a
# shellcheck disable=SC1091
. "$HERE/../managed.env"
set +a
exec /Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python "$HERE/run.py"
