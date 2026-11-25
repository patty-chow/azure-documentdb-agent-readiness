#!/bin/bash
# Rerun bulkwrite-forms (engine 1.2.0) end to end: wire steps, read-only container checks, finalize.
# Owns database t_bulk only; run.py drops it at the start and at the end.
set -euo pipefail
cd "$(dirname "$0")"
PY=/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python
"$PY" run.py 2> run.stderr.log
"$PY" inspect_container.py > inspect.stdout.log
"$PY" finalize.py
