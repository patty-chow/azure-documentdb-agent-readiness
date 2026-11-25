"""Run the five-stage pipeline over every sample in samples/index.json, then triage the findings.

    python loop/run_loop.py --dry-run                      show the queue
    python loop/run_loop.py --parallel 3                   run everything not yet done, 3 at a time
    python loop/run_loop.py --vertical retail --limit 5    first five retail samples
    python loop/run_loop.py --ids retail-02 fintech-07     named samples
    python loop/run_loop.py --ids retail-02 --allow-azure-writes --cleanup
                                                           let the builder provision; delete what it made afterwards
    python loop/run_loop.py --arm control --ids retail-01  no skills, no MCP servers
    python loop/run_loop.py --triage-only                  rebuild findings/ from existing runs

State lives in runs/loop-state.json: one entry per sample and arm with the run
folder, exit code and verdicts. A sample is skipped when its latest entry
finished with exit code 0, unless --rerun is given. Each run's console output
goes to runs/_loop_logs/. After every run the findings are extracted and
findings/TRIAGE.md is regenerated. Nothing outside this repository is created,
except by the builder when --allow-azure-writes is on.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from loop.findings import write_triage  # noqa: E402

PYTHON = sys.executable
INDEX = PROJECT / "samples" / "index.json"
STATE = PROJECT / "runs" / "loop-state.json"
LOGS = PROJECT / "runs" / "_loop_logs"
ARMS_DIR = PROJECT / "loop" / "arms"

# An arm is one experimental condition: which skills and MCP servers the agents get.
ARMS: dict[str, dict[str, str]] = {
    "default": {},  # kit installed in .agents/skills plus mcp.json as committed
    "control": {"FACTORY_SKILL_PATHS": str(ARMS_DIR / "no-skills"), "FACTORY_MCP_CONFIG": str(ARMS_DIR / "mcp-none.json")},
    "kit-only": {"FACTORY_MCP_CONFIG": str(ARMS_DIR / "mcp-none.json")},
    "mcps-only": {"FACTORY_SKILL_PATHS": str(ARMS_DIR / "no-skills")},
}
# Never deleted by --cleanup, whatever the builder did.
PROTECTED_RESOURCE_TYPES = {"Microsoft.DocumentDB/mongoClusters", "Microsoft.CognitiveServices/accounts"}

_state_lock = threading.Lock()
_print_lock = threading.Lock()


def say(text: str) -> None:
    with _print_lock:
        print(text, flush=True)


def load_state() -> dict:
    if STATE.is_file():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"runs": []}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def record(entry: dict) -> None:
    with _state_lock:
        state = load_state()
        state["runs"] = [r for r in state["runs"] if not (r["id"] == entry["id"] and r["arm"] == entry["arm"] and r["started"] == entry["started"])]
        state["runs"].append(entry)
        save_state(state)


def latest(state: dict, sample_id: str, arm: str) -> dict | None:
    rows = [r for r in state["runs"] if r["id"] == sample_id and r["arm"] == arm]
    return max(rows, key=lambda r: r["started"]) if rows else None


def az_resource_ids(resource_group: str) -> set[str]:
    done = subprocess.run(["az", "resource", "list", "-g", resource_group, "--query", "[].{id:id,type:type}", "-o", "json"],
                          capture_output=True, text=True, timeout=120)
    if done.returncode != 0:
        say(f"      WARNING: could not list resources in {resource_group}: {done.stderr.strip()[:200]}")
        return set()
    return {r["id"] for r in json.loads(done.stdout or "[]") if r["type"] not in PROTECTED_RESOURCE_TYPES}


def cleanup_new_resources(resource_group: str, before: set[str]) -> list[str]:
    new = sorted(az_resource_ids(resource_group) - before)
    for rid in new:
        subprocess.run(["az", "resource", "delete", "--ids", rid, "--no-wait", "-o", "none"], capture_output=True, text=True, timeout=120)
    return new


def run_one(sample: dict, args: argparse.Namespace) -> dict:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{sample['id']}-{args.arm}-{stamp}.log"

    cmd = [PYTHON, str(PROJECT / "main.py"), "run", str(PROJECT / sample["prompt"]), "--yes"]
    if args.force:
        cmd.append("--force")
    if args.stop_after:
        cmd += ["--stop-after", args.stop_after]
    if args.allow_azure_writes:
        cmd.append("--allow-azure-writes")
    requirements = PROJECT / "requirements" / f"{Path(sample['prompt']).stem}.md"
    if requirements.is_file():
        cmd += ["--requirements", str(requirements)]
    env = {**os.environ, **ARMS[args.arm], "PYTHONUNBUFFERED": "1"}

    entry = {"id": sample["id"], "arm": args.arm, "title": sample["title"], "started": started, "finished": "",
             "exit_code": None, "run_dir": "", "verdicts": {}, "log": str(log_path.relative_to(PROJECT)),
             "azure_writes": bool(args.allow_azure_writes), "cleaned_up": []}
    record(entry)
    say(f"[{sample['id']}] start  {sample['title']}  (arm={args.arm}, log={entry['log']})")

    before = az_resource_ids(args.resource_group) if args.allow_azure_writes and args.cleanup else set()
    t0 = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        log.write(" ".join(cmd) + "\n\n")
        log.flush()
        done = subprocess.run(cmd, cwd=PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT, text=True)
    text = log_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^Run folder: (.+)$", text, re.M)
    run_dir = Path(m.group(1).strip()) if m else None

    entry["exit_code"] = done.returncode
    entry["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry["minutes"] = round((time.time() - t0) / 60, 1)
    if run_dir and run_dir.is_dir():
        entry["run_dir"] = str(run_dir.relative_to(PROJECT)) if run_dir.is_relative_to(PROJECT) else str(run_dir)
        run_json = run_dir / "run.json"
        if run_json.is_file():
            entry["verdicts"] = json.loads(run_json.read_text(encoding="utf-8")).get("verdicts", {})
    if args.allow_azure_writes and args.cleanup:
        entry["cleaned_up"] = cleanup_new_resources(args.resource_group, before)
        if entry["cleaned_up"]:
            say(f"[{sample['id']}] cleanup requested for {len(entry['cleaned_up'])} resource(s) the builder created")
    record(entry)
    verdicts = ", ".join(f"{k}={v}" for k, v in entry["verdicts"].items()) or "no run.json"
    say(f"[{sample['id']}] exit {done.returncode} after {entry['minutes']} min  {verdicts}")
    return entry


def build_queue(args: argparse.Namespace) -> list[dict]:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    state = load_state()
    queue = []
    for s in index:
        if args.vertical and s["vertical"] not in args.vertical:
            continue
        if args.ids and s["id"] not in args.ids:
            continue
        last = latest(state, s["id"], args.arm)
        if last and last.get("exit_code") == 0 and not args.rerun:
            continue
        if last and last.get("exit_code") is None and not args.rerun:
            # Started and never finished: a crash or an interrupted loop. Run it again.
            pass
        queue.append(s)
    if args.limit:
        queue = queue[: args.limit]
    return queue


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vertical", nargs="*", help="retail fintech healthcare banking customer-360")
    ap.add_argument("--ids", nargs="*", help="sample ids from samples/index.json")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--parallel", type=int, default=1, help="runs at a time (forced to 1 with --allow-azure-writes --cleanup)")
    ap.add_argument("--arm", choices=sorted(ARMS), default="default")
    ap.add_argument("--rerun", action="store_true", help="run samples that already finished")
    ap.add_argument("--force", action="store_true", help="pass --force to the pipeline (continue past an insufficient prompt)")
    ap.add_argument("--stop-after", choices=["review", "readiness", "build"])
    ap.add_argument("--allow-azure-writes", action="store_true", help="let the builder create Azure resources")
    ap.add_argument("--cleanup", action="store_true", help="after a write-enabled run, delete resources that appeared in the resource group")
    ap.add_argument("--resource-group", default=os.environ.get("FACTORY_RG", "documentdb-samples-rg"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--triage-only", action="store_true")
    args = ap.parse_args()

    if args.triage_only:
        n, r = write_triage(PROJECT / "runs")
        print(f"{n} findings from {r} runs -> findings/TRIAGE.md")
        return 0

    queue = build_queue(args)
    print(f"{len(queue)} sample(s) queued, arm={args.arm}, parallel={args.parallel}"
          + (", AZURE WRITES ON" if args.allow_azure_writes else ""))
    for s in queue:
        print(f"  {s['id']:<16} {s['title']}")
    if args.dry_run or not queue:
        return 0
    if args.allow_azure_writes and args.cleanup and args.parallel != 1:
        print("cleanup compares the resource group before and after each run, so write-enabled runs go one at a time")
        args.parallel = 1

    results = []
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futures = {pool.submit(run_one, s, args): s for s in queue}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:  # one broken run must not stop the loop
                say(f"[{futures[fut]['id']}] loop error: {exc!r}")
            n, r = write_triage(PROJECT / "runs")
            say(f"      triage: {n} findings from {r} runs -> findings/TRIAGE.md")

    ok = sum(1 for r in results if r.get("exit_code") == 0)
    print(f"\n{ok}/{len(queue)} runs finished with exit 0. State: runs/loop-state.json")
    return 0 if ok == len(queue) else 1


if __name__ == "__main__":
    sys.exit(main())
