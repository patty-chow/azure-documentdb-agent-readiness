#!/usr/bin/env bash
# Phase 3: clean-up and comparison, run after phase 2 (build + audit for every sample) is complete.
#   0. Resume runs that ended in a model failure (exit 7) once phase 2 is over.
#   1. Rerun the samples whose phase-2 result was tainted by a harness defect fixed since.
#   2. Control arm (no Agent Kit skills, no MCP servers) on two samples per vertical.
#   3. Roll everything up: the pipeline's aggregate command, the phase report, the findings triage.
# Usage: loop/phase3.sh [parallel]      (idempotent: finished runs are skipped by the loop's state)
set -uo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
PAR="${1:-3}"
RERUN_IDS="retail-07 retail-09 retail-13 retail-19 retail-12"
CONTROL_IDS="retail-01 retail-11 fintech-01 fintech-11 healthcare-01 healthcare-11 banking-01 banking-11 customer-360-01 customer-360-11"

echo "== phase 3.0: resume partial default-arm runs (rate-limit casualties) =="
# Without --ids the queue covers every sample; complete ones are skipped, partial ones (exit 7 after the
# retries ran out) are resumed from their run folder. Parallel 2 for this step: these fail on 429s.
$PY loop/run_loop.py --parallel 2
echo "== phase 3.1: reruns ($RERUN_IDS) =="
# --rerun starts fresh runs; the tainted ones are already marked complete in state, so without it they would be skipped.
# Only runs that have not yet been redone since the fixes are rerun: a sample whose latest default-arm run started
# after the fixes (2026-11-24 23:30 local) is left alone.
$PY - <<'EOF'
import json, subprocess, sys
state = json.load(open("runs/loop-state.json"))["runs"]
cutoff = "2026-11-25T07:30:00+00:00"   # 23:30 PST on the 24th
todo = []
for sid in "retail-07 retail-09 retail-13 retail-19 retail-12".split():
    runs = [r for r in state if r["id"] == sid and r["arm"] == "default" and r.get("stop_after") is None]
    if not any(r["started"] >= cutoff and r.get("exit_code") in (0, 4) for r in runs):
        todo.append(sid)
print("reruns needed:", todo or "none")
if todo:
    sys.exit(subprocess.call([".venv/bin/python", "loop/run_loop.py", "--rerun", "--parallel", sys.argv[1] if len(sys.argv) > 1 else "3", "--ids", *todo]))
EOF
echo "== phase 3.2: control arm (no skills, no MCP servers) =="
$PY loop/run_loop.py --arm control --parallel "$PAR" --ids $CONTROL_IDS
echo "== phase 3.3: roll-up =="
$PY loop/aggregate_arm.py --arm default                       # default-arm runs only (see the script's docstring)
$PY loop/phase_report.py --arm control && mv findings/PHASE-REPORT.md findings/PHASE-REPORT-control.md
$PY loop/phase_report.py --arm default
$PY loop/run_loop.py --triage-only
git add runs/gallery-insights.md findings runs/loop-state.json && git commit -q -m "Phase 3: reruns, control arm, aggregate roll-up and reports" && git push -q && echo "roll-up committed and pushed"
echo "PHASE 3 DONE"
