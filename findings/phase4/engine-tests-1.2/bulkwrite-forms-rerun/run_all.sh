#!/bin/bash
# bulkwrite-forms REPRODUCTION on engine 1.2.0, database t_bulk_rerun only.
# preflight -> tester's run.py (copied, database renamed) -> tester's inspect_container.py (unchanged copy)
# -> extra probes -> source files at the image revision -> finalize (comparison, verdicts, report.json)
set -euo pipefail
cd "$(dirname "$0")"
PY=/Users/julietai/claude/azure-documentdb-agent-readiness/.venv/bin/python
"$PY" preflight.py
"$PY" run.py 2> run.stderr.log
mv report.json raw_run.json
"$PY" inspect_container.py > inspect.stdout.log 2> inspect.stderr.log
"$PY" extra_probes.py 2> extra.stderr.log
./fetch_source.sh > fetch_source.log 2>&1
"$PY" finalize_rerun.py
