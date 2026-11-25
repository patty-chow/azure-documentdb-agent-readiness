"""Run the five-stage pipeline over every sample in samples/index.json, then triage the findings.

    python loop/run_loop.py --dry-run                          show the queue
    python loop/run_loop.py --stop-after readiness --parallel 3
                                                               phase 1: review and readiness for every sample
    python loop/run_loop.py --parallel 3                       phase 2: resume each phase-1 run through build and audit
    python loop/run_loop.py --vertical retail --limit 5        first five retail samples
    python loop/run_loop.py --ids retail-02 fintech-07         named samples
    python loop/run_loop.py --ids retail-02 --allow-azure-writes --cleanup
                                                               let the builder provision; delete what it made afterwards
    python loop/run_loop.py --arm control --ids retail-01 retail-11
                                                               no skills, no MCP servers
    python loop/run_loop.py --triage-only                      rebuild findings/ from existing runs

State lives in runs/loop-state.json: one entry per run with the run folder, exit
code, how far it went (stop_after) and the verdicts. A sample is complete for a
requested stop point when an earlier run with exit code 0 reached at least that
far. A sample with a partial run is resumed from its run folder (the pipeline
skips finished stages), unless --rerun asks for a fresh run.

What the loop adds around each pipeline run:
- a virtual environment on PATH, so the builder's `pip install` works on a Mac
  whose system Python refuses it;
- an environment note (loop/run-environment.md) passed as the pipeline's shared
  context, telling the agents a live cluster is reachable through DOCUMENTDB_URI;
- the sample's databases are dropped from the shared cluster afterwards, so runs
  stay independent;
- one automatic --resume when the model call failed (exit code 7);
- the run folder, state and findings are committed and pushed after every run,
  after a scan that refuses to commit the cluster credentials;
- caffeinate keeps the Mac awake while the loop runs;
- the loop stops after three failures in a row and prints STUCK.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
from loop.findings import write_triage  # noqa: E402

PYTHON = sys.executable
INDEX = PROJECT / "samples" / "index.json"
STATE = PROJECT / "runs" / "loop-state.json"
LOGS = PROJECT / "runs" / "_loop_logs"
VENVS = PROJECT / "runs" / "_venvs"
ARMS_DIR = PROJECT / "loop" / "arms"
ENV_NOTE = PROJECT / "loop" / "run-environment.md"

# An arm is one experimental condition: which skills and MCP servers the agents get.
ARMS: dict[str, dict[str, str]] = {
    "default": {},  # kit installed in .agents/skills plus mcp.json as committed
    "control": {"FACTORY_SKILL_PATHS": str(ARMS_DIR / "no-skills"), "FACTORY_MCP_CONFIG": str(ARMS_DIR / "mcp-none.json")},
    "kit-only": {"FACTORY_MCP_CONFIG": str(ARMS_DIR / "mcp-none.json")},
    "mcps-only": {"FACTORY_SKILL_PATHS": str(ARMS_DIR / "no-skills")},
}
ARMS_WITH_DOCUMENTDB_MCP = {"default", "mcps-only"}
# Never deleted by --cleanup, whatever the builder did.
PROTECTED_RESOURCE_TYPES = {"Microsoft.DocumentDB/mongoClusters", "Microsoft.CognitiveServices/accounts"}
SYSTEM_DATABASES = {"admin", "config", "local"}
# How far a run went. None means the whole pipeline.
STAGE_ORDER = {"review": 1, "readiness": 2, "build": 3, None: 4}
MODEL_FAILURE_EXIT = 7
MAX_CONSECUTIVE_FAILURES = 3
MODEL_RETRIES = 2                 # resumes after a model failure (exit 7), on top of the SDK's own retries
RATE_LIMIT_BACKOFF_SECONDS = 90   # the deployment's limit is per minute, so wait out the window first

_state_lock = threading.Lock()
_print_lock = threading.Lock()
_git_lock = threading.Lock()


def say(text: str) -> None:
    with _print_lock:
        print(text, flush=True)


# ----------------------------------------------------------------- state --

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
        state["runs"] = [r for r in state["runs"]
                         if not (r["id"] == entry["id"] and r["arm"] == entry["arm"] and r["started"] == entry["started"])]
        state["runs"].append(entry)
        save_state(state)


def entries_for(state: dict, sample_id: str, arm: str) -> list[dict]:
    return sorted((r for r in state["runs"] if r["id"] == sample_id and r["arm"] == arm), key=lambda r: r["started"])


def reached(entry: dict) -> int:
    return STAGE_ORDER.get(entry.get("stop_after"), 4)


def complete_for(entry: dict, stop_after: str | None) -> bool:
    return entry.get("exit_code") == 0 and reached(entry) >= STAGE_ORDER[stop_after]


def resumable(entry: dict) -> bool:
    """A run folder with saved stages can be continued, whether the run stopped at a gate or failed."""
    run_dir = entry.get("run_dir")
    return bool(run_dir) and (PROJECT / run_dir).is_dir() and entry.get("exit_code") is not None


# ------------------------------------------------------------ environment --

def cluster_uri() -> str:
    return os.environ.get("DOCUMENTDB_URI", "").strip()


def cluster_credentials() -> list[str]:
    """The secret forms that must never land in git: the password as written and URL-decoded."""
    uri = cluster_uri()
    m = re.match(r"mongodb(?:\+srv)?://([^:/@]+):([^@]+)@", uri)
    if not m:
        return []
    raw = m.group(2)
    return sorted({raw, unquote(raw)} - {""})


def list_databases() -> set[str]:
    if not cluster_uri():
        return set()
    try:
        from pymongo import MongoClient
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = MongoClient(cluster_uri(), serverSelectionTimeoutMS=20000)
            return set(client.list_database_names())
    except Exception as exc:
        say(f"      WARNING: could not list cluster databases: {type(exc).__name__}: {exc}")
        return set()


def drop_new_databases(before: set[str]) -> list[str]:
    new = sorted(list_databases() - before - SYSTEM_DATABASES)
    if not new:
        return []
    try:
        from pymongo import MongoClient
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            client = MongoClient(cluster_uri(), serverSelectionTimeoutMS=20000)
            for name in new:
                client.drop_database(name)
    except Exception as exc:
        say(f"      WARNING: could not drop databases {new}: {type(exc).__name__}: {exc}")
    return new


def make_venv(tag: str) -> Path:
    path = VENVS / tag
    subprocess.run([PYTHON, "-m", "venv", str(path)], check=True, capture_output=True)
    subprocess.run([str(path / "bin" / "python"), "-m", "pip", "install", "-q", "--upgrade", "pip"], capture_output=True)
    return path


def render_env_note(sample: dict, arm: str, tag: str) -> Path:
    database = "sample_" + re.sub(r"[^a-z0-9]+", "_", sample["id"].lower()).strip("_")
    mcp_line = ("- The `documentdb` MCP server's connection profile `default` is connected to that same cluster. Use its tools "
                "to inspect collections, indexes and query plans and to verify what the app created.\n") if arm in ARMS_WITH_DOCUMENTDB_MCP else ""
    text = ENV_NOTE.read_text(encoding="utf-8").replace("{database}", database).replace("{mcp_line}", mcp_line)
    LOGS.mkdir(parents=True, exist_ok=True)
    path = LOGS / f"{tag}-env.md"
    path.write_text(text, encoding="utf-8")
    return path


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


# ------------------------------------------------------------------- git --

def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=PROJECT, capture_output=True, text=True)


def commit_run(entry: dict, push: bool) -> str:
    """Commit the run folder, state and findings. Files holding the cluster credentials are left out."""
    with _git_lock:
        paths = ["runs/loop-state.json", "findings"]
        if entry.get("run_dir"):
            paths.append(entry["run_dir"])
        git("add", "-A", "--", *paths)
        leaked = []
        for secret in cluster_credentials():
            # -z: NUL-separated paths. Secrets are matched as fixed strings against the staged content.
            found = subprocess.run(["git", "grep", "-z", "-l", "-F", "--cached", "-e", secret, "--", *paths],
                                   cwd=PROJECT, capture_output=True, text=True).stdout
            leaked += [p for p in found.split("\0") if p]
        for path in sorted(set(leaked)):
            git("rm", "-q", "--cached", "--", path)
        if leaked:
            say(f"[{entry['id']}] REFUSED to commit {len(set(leaked))} file(s) containing the cluster credentials: "
                + ", ".join(sorted(set(leaked))[:5]))
        if not git("diff", "--cached", "--quiet").returncode:
            return "nothing to commit"
        verdicts = ", ".join(f"{k}={v}" for k, v in entry.get("verdicts", {}).items())
        msg = f"Run {entry['id']} ({entry['arm']}): exit {entry.get('exit_code')}, {verdicts or 'no verdicts'}"
        done = git("commit", "-q", "-m", msg)
        if done.returncode:
            return f"commit failed: {done.stderr.strip()[:200]}"
        if push:
            pushed = git("push", "-q")
            if pushed.returncode:
                return f"committed, push failed: {pushed.stderr.strip()[:200]}"
            return "committed and pushed"
        return "committed"


# ------------------------------------------------------------------- run --

def run_pipeline(cmd: list[str], env: dict, log_path: Path) -> int:
    with log_path.open("a", encoding="utf-8") as log:
        log.write("\n$ " + " ".join(cmd) + "\n\n")
        log.flush()
        return subprocess.run(cmd, cwd=PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT, text=True).returncode


def run_one(sample: dict, args: argparse.Namespace, resume_from: str | None) -> dict:
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = f"{sample['id']}-{args.arm}-{stamp}"
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{tag}.log"

    entry = {"id": sample["id"], "arm": args.arm, "title": sample["title"], "started": started, "finished": "",
             "exit_code": None, "run_dir": resume_from or "", "resumed_from": resume_from or "", "stop_after": args.stop_after,
             "verdicts": {}, "log": str(log_path.relative_to(PROJECT)), "azure_writes": bool(args.allow_azure_writes),
             "dropped_databases": [], "cleaned_up": [], "retried": False, "git": ""}
    record(entry)
    say(f"[{sample['id']}] start  {sample['title']}  (arm={args.arm}"
        + (f", resume {resume_from}" if resume_from else "") + f", stop_after={args.stop_after or 'audit'})")

    cmd = [PYTHON, str(PROJECT / "main.py"), "run"]
    cmd += ["--resume", str(PROJECT / resume_from)] if resume_from else [str(PROJECT / sample["prompt"])]
    cmd.append("--yes")
    if args.force:
        cmd.append("--force")
    if args.stop_after:
        cmd += ["--stop-after", args.stop_after]
    if args.allow_azure_writes:
        cmd.append("--allow-azure-writes")
    # Passed on resume as well: the pipeline refreshes the run folder's copy, so a corrected
    # requirements file reaches the audit even when review and readiness already ran.
    requirements = PROJECT / "requirements" / f"{Path(sample['prompt']).stem}.md"
    if requirements.is_file():
        cmd += ["--requirements", str(requirements)]
    if args.env_note:
        cmd += ["--skill", str(render_env_note(sample, args.arm, tag))]

    env = {**os.environ, **ARMS[args.arm], "PYTHONUNBUFFERED": "1"}
    venv = None
    if args.venv:
        venv = make_venv(tag)
        env["PATH"] = f"{venv / 'bin'}{os.pathsep}{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(venv)
        env.pop("PYTHONHOME", None)

    dbs_before = list_databases() if args.drop_databases else set()
    resources_before = az_resource_ids(args.resource_group) if args.allow_azure_writes and args.cleanup else set()

    t0 = time.time()
    code = run_pipeline(cmd, env, log_path)
    text = log_path.read_text(encoding="utf-8", errors="replace")
    m = re.findall(r"^Run folder: (.+)$", text, re.M)
    run_dir = Path(m[-1].strip()) if m else (PROJECT / resume_from if resume_from else None)
    attempts = 0
    while code == MODEL_FAILURE_EXIT and args.auto_resume and attempts < MODEL_RETRIES and run_dir and run_dir.is_dir():
        attempts += 1
        entry["retried"] = True
        rate_limited = "429" in text[-3000:]
        wait = RATE_LIMIT_BACKOFF_SECONDS * attempts if rate_limited else 15
        say(f"[{sample['id']}] model call failed{' (rate limit)' if rate_limited else ''}; "
            f"waiting {wait}s then resuming {run_dir.name} (attempt {attempts}/{MODEL_RETRIES})")
        time.sleep(wait)
        retry = [c for c in cmd if c != str(PROJECT / sample["prompt"])]
        if "--resume" not in retry:
            retry = retry[:3] + ["--resume", str(run_dir)] + retry[3:]
        retry = [c for i, c in enumerate(retry) if not (c == "--requirements" or (i and retry[i - 1] == "--requirements"))]
        code = run_pipeline(retry, env, log_path)
        text = log_path.read_text(encoding="utf-8", errors="replace")

    entry["exit_code"] = code
    entry["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry["minutes"] = round((time.time() - t0) / 60, 1)
    if run_dir and run_dir.is_dir():
        entry["run_dir"] = str(run_dir.relative_to(PROJECT)) if run_dir.is_relative_to(PROJECT) else str(run_dir)
        run_json = run_dir / "run.json"
        if run_json.is_file():
            entry["verdicts"] = json.loads(run_json.read_text(encoding="utf-8")).get("verdicts", {})
    if args.drop_databases:
        entry["dropped_databases"] = drop_new_databases(dbs_before)
    if args.allow_azure_writes and args.cleanup:
        entry["cleaned_up"] = cleanup_new_resources(args.resource_group, resources_before)
        if entry["cleaned_up"]:
            say(f"[{sample['id']}] cleanup requested for {len(entry['cleaned_up'])} resource(s) the builder created")
    if venv:
        shutil.rmtree(venv, ignore_errors=True)
    record(entry)

    with _state_lock:  # the triage reads every run folder, so one writer at a time
        n, r = write_triage(PROJECT / "runs")
    if args.commit:
        entry["git"] = commit_run(entry, push=args.push)
        record(entry)
    verdicts = ", ".join(f"{k}={v}" for k, v in entry["verdicts"].items()) or "no run.json"
    say(f"[{sample['id']}] exit {code} after {entry['minutes']} min  {verdicts}"
        + (f"  dropped {entry['dropped_databases']}" if entry["dropped_databases"] else "")
        + (f"  git: {entry['git']}" if entry["git"] else "")
        + f"  triage: {n} findings / {r} runs")
    return entry


# ----------------------------------------------------------------- queue --

def build_queue(args: argparse.Namespace) -> list[tuple[dict, str | None]]:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    state = load_state()
    queue: list[tuple[dict, str | None]] = []
    for s in index:
        if args.vertical and s["vertical"] not in args.vertical:
            continue
        if args.ids and s["id"] not in args.ids:
            continue
        history = entries_for(state, s["id"], args.arm)
        if not args.rerun and any(complete_for(e, args.stop_after) for e in history):
            continue
        resume_from = None
        if not args.rerun:
            partial = [e for e in history if resumable(e) and reached(e) < STAGE_ORDER[args.stop_after]]
            if partial:
                resume_from = partial[-1]["run_dir"]
        queue.append((s, resume_from))
    if args.limit:
        queue = queue[: args.limit]
    return queue


def keep_awake() -> subprocess.Popen | None:
    exe = shutil.which("caffeinate")
    if not exe:
        return None
    # -i: no idle sleep; -s: no system sleep on AC power; -w: only while this process lives.
    return subprocess.Popen([exe, "-i", "-s", "-w", str(os.getpid())])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vertical", nargs="*", help="retail fintech healthcare banking customer-360")
    ap.add_argument("--ids", nargs="*", help="sample ids from samples/index.json")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--parallel", type=int, default=1, help="runs at a time (forced to 1 with --allow-azure-writes --cleanup)")
    ap.add_argument("--arm", choices=sorted(ARMS), default="default")
    ap.add_argument("--stop-after", choices=["review", "readiness", "build"], help="omit to run through the audit")
    ap.add_argument("--rerun", action="store_true", help="start fresh runs even for samples that are complete or resumable")
    ap.add_argument("--no-force", dest="force", action="store_false", help="stop at an insufficient prompt instead of building on assumptions")
    ap.add_argument("--no-env-note", dest="env_note", action="store_false", help="do not pass loop/run-environment.md as shared context")
    ap.add_argument("--no-venv", dest="venv", action="store_false", help="do not give each run its own virtual environment")
    ap.add_argument("--keep-databases", dest="drop_databases", action="store_false", help="leave databases the run created on the cluster")
    ap.add_argument("--no-auto-resume", dest="auto_resume", action="store_false", help="do not retry a model failure once")
    ap.add_argument("--no-commit", dest="commit", action="store_false", help="do not commit after each run")
    ap.add_argument("--no-push", dest="push", action="store_false", help="commit but do not push")
    ap.add_argument("--allow-azure-writes", action="store_true", help="let the builder create Azure resources")
    ap.add_argument("--cleanup", action="store_true", help="after a write-enabled run, delete resources that appeared in the resource group")
    ap.add_argument("--resource-group", default=os.environ.get("FACTORY_RG", "documentdb-samples-rg"))
    ap.add_argument("--max-consecutive-failures", type=int, default=MAX_CONSECUTIVE_FAILURES)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--triage-only", action="store_true")
    args = ap.parse_args()

    from dotenv import load_dotenv
    load_dotenv(PROJECT / ".env")

    if args.triage_only:
        n, r = write_triage(PROJECT / "runs")
        print(f"{n} findings from {r} runs -> findings/TRIAGE.md")
        return 0

    queue = build_queue(args)
    print(f"{len(queue)} sample(s) queued, arm={args.arm}, stop_after={args.stop_after or 'audit'}, parallel={args.parallel}"
          + (", AZURE WRITES ON" if args.allow_azure_writes else "") + (", no env note" if not args.env_note else ""))
    for s, resume_from in queue:
        print(f"  {s['id']:<16} {s['title']}" + (f"   (resume {resume_from})" if resume_from else ""))
    if args.dry_run or not queue:
        return 0
    if args.allow_azure_writes and args.cleanup and args.parallel != 1:
        print("cleanup compares the resource group before and after each run, so write-enabled runs go one at a time")
        args.parallel = 1
    if args.drop_databases and not cluster_uri():
        print("DOCUMENTDB_URI is not set: nothing to drop, continuing")
        args.drop_databases = False

    awake = keep_awake()
    results: list[dict] = []
    consecutive_failures = 0
    stuck = False
    pool = ThreadPoolExecutor(max_workers=args.parallel)
    try:
        futures = {pool.submit(run_one, s, args, resume_from): s for s, resume_from in queue}
        for fut in as_completed(futures):
            try:
                entry = fut.result()
                results.append(entry)
                consecutive_failures = 0 if entry.get("exit_code") == 0 else consecutive_failures + 1
            except Exception as exc:  # one broken run must not stop the loop
                say(f"[{futures[fut]['id']}] loop error: {exc!r}")
                consecutive_failures += 1
            if args.max_consecutive_failures and consecutive_failures >= args.max_consecutive_failures:
                stuck = True
                say(f"STUCK: {consecutive_failures} runs failed in a row; cancelling the rest of the queue")
                pool.shutdown(wait=True, cancel_futures=True)
                break
    finally:
        pool.shutdown(wait=True)
        if awake:
            awake.terminate()

    ok = sum(1 for r in results if r.get("exit_code") == 0)
    if stuck:
        print(f"\nSTUCK after {len(results)} run(s), {ok} ok. State: runs/loop-state.json")
        return 2
    print(f"\nPHASE DONE: {ok}/{len(queue)} runs finished with exit 0 (arm={args.arm}, stop_after={args.stop_after or 'audit'}). "
          "State: runs/loop-state.json")
    return 0 if ok == len(queue) else 1


if __name__ == "__main__":
    sys.exit(main())
