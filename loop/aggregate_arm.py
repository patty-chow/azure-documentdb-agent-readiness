"""Run the pipeline's `aggregate` over one experiment arm only.

`main.py aggregate` takes the newest run folder of every sample, whatever produced it. Once the
control arm has run, the newest folder of ten samples is a control run, which would put no-kit,
no-MCP results into runs/gallery-insights.md. This builds runs/_aggregate/ (ignored by git) with a
symlink to the run folder the loop's state records as each sample's best run for the arm, plus any
run folders the loop never made (the repository's own sample), and aggregates that.

    python loop/aggregate_arm.py [--arm default] [--out runs/gallery-insights.md]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
RUNS = PROJECT / "runs"
STATE = RUNS / "loop-state.json"
VIEW = RUNS / "_aggregate"
STAGE_ORDER = {"review": 1, "readiness": 2, "build": 3, None: 4}


def best_run(entries: list[dict]) -> str | None:
    """Furthest-reaching finished run (exit 0 or 4), newest first on ties; else the newest attempt."""
    with_dir = [e for e in entries if e.get("run_dir") and (PROJECT / e["run_dir"]).is_dir()]
    if not with_dir:
        return None
    finished = [e for e in with_dir if e.get("exit_code") in (0, 4)]
    pool = finished or with_dir
    pool.sort(key=lambda e: (STAGE_ORDER.get(e.get("stop_after"), 0), e.get("started", "")))
    return pool[-1]["run_dir"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arm", default="default")
    ap.add_argument("--out", default=str(RUNS / "gallery-insights.md"))
    args = ap.parse_args()

    state = json.loads(STATE.read_text(encoding="utf-8"))["runs"]
    by_sample: dict[str, list[dict]] = {}
    for e in state:
        if e.get("arm") == args.arm:
            by_sample.setdefault(e["id"], []).append(e)

    if VIEW.exists():
        shutil.rmtree(VIEW)
    VIEW.mkdir()
    linked: set[str] = set()
    for sid, entries in sorted(by_sample.items()):
        run_dir = best_run(entries)
        if not run_dir:
            continue
        src = PROJECT / run_dir
        slug = src.parent.name
        (VIEW / slug).mkdir(exist_ok=True)
        os.symlink(src, VIEW / slug / src.name)
        linked.add(slug)
    # Sample folders the loop never wrote (e.g. the repository's own sample): take them as they are.
    loop_slugs = {Path(e["run_dir"]).parent.name for e in state if e.get("run_dir")}
    for p in sorted(RUNS.iterdir()):
        if p.is_dir() and not p.name.startswith("_") and p.name not in loop_slugs:
            os.symlink(p, VIEW / p.name)
            linked.add(p.name)

    rc = subprocess.call([sys.executable, str(PROJECT / "main.py"), "aggregate", "--runs", str(VIEW)],
                         cwd=PROJECT, stdout=subprocess.DEVNULL)
    if rc:
        return rc
    produced = VIEW / "gallery-insights.md"
    text = produced.read_text(encoding="utf-8").replace("latest run of each", f"best {args.arm}-arm run of each")
    Path(args.out).write_text(text, encoding="utf-8")
    print(f"{len(linked)} samples, arm={args.arm} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
