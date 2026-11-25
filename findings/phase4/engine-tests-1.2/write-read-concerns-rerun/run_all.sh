#!/bin/sh
# Reproduce stage for write-read-concerns: rerun the tester's script (copy, database t_concern_rerun), compare, extra probes, report.
set -e
cd "$(dirname "$0")"
PY=/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python
$PY -I preflight.py
$PY -I run.py > run.log 2>&1
$PY -I compare.py > compare.log 2>&1
$PY -I extra_probes.py > extra.log 2>&1
$PY -I finalize.py
