---
id: H11
title: "Run-environment note and inventory: state the pinning policy, env-var presence and shard count"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: needs_sme
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P2
sample_count: 8
member_drafts:
  - 055-run-environment-inventory-handed-to-the-readiness-build-stag.md
open_questions: 3
---

# Run-environment note and inventory: state the pinning policy, env-var presence and shard count

> This repository belongs to a colleague (abinav2307); coordinate this PR with them before opening it.

## What happens today

The harness builds sample apps against an Azure DocumentDB cluster (`Microsoft.DocumentDB/mongoClusters`). Before building, a readiness agent receives two inputs it is told to treat as fact: `loop/run-environment.md` (filled in by `loop/run_loop.py`, which substitutes `{database}` and `{mcp_line}`) and an inventory built by `factory/agents/readiness.py::collect_inventory()` from `factory/tools/environment.py`.

Already present:

- `run-environment.md` states compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF vector indexes, Node.js 24, and a per-run Python venv.
- `probe_clis()` records interpreter versions in `02-inventory.json` under `command_line_tools` (e.g. `Python 3.13.13`, `v24.21.0`).

Missing:

- any instruction to target those interpreter versions, and any dependency-pinning policy (exact pins vs caret ranges vs floors, lockfile, README record);
- whether `DOCUMENTDB_URI` is actually set (the note asserts it; no probe checks it, and no MCP tool exposes env vars);
- the cluster's shard count, HA mode and auth modes, although `loop/provision.sh` creates it with `--tier M30 --shard-count 1 --high-availability Disabled` and `az documentdb mongocluster show` returns them from the control plane.

The readiness agent therefore files these as documentation `information_gaps`, and the builder picks versions from model prior.

## Why it matters

- In one experiment run of 100 samples, 9 findings from 8 distinct samples trace to this theme (counts are from that single run). A rough keyword scan suggests around half of all samples [needs SME confirmation] (unstable count; see open question 3) raise a similar-shaped gap (Python version, ODM/driver pins, `DOCUMENTDB_URI` presence, shard topology). That is harness noise inside the "Learn docs information gap" signal the product teams are meant to act on.
- What the agent did wrong: sample 09 chose Mongoose 7.x by default and shipped a caret range `^7.9.0`, though the Learn Mongoose quickstart it read lists Mongoose 9.12.1 / driver 7.8.0 as tested [needs SME confirmation]. Sample 16 declared `mongoose ^7.7.0` (its lockfile resolves the `mongodb` driver to 5.9.2). Sample 17 shipped floor pins (`pymongo>=4.5.0`, `langchain>=0.0.350`), so the build is not reproducible.
- Samples 09 and 12 each spent a gap on "is `DOCUMENTDB_URI` really set?", and 09 on "is the cluster multishard?" (which decides whether multishard change streams must be enabled [needs SME confirmation]: the reviewer notes Learn labels multishard change streams preview; confirm current GA status). Both are one probe away from being facts.

## Proposed change

### 1. `loop/run-environment.md`: add two bullets

```
- Runtime and dependency policy: target the interpreter versions reported in the machine inventory (`command_line_tools` -> python, node). Pin dependencies to the exact versions pip/npm resolve in this environment (`==` in requirements.txt, exact versions in package.json), commit the lockfile (package-lock.json; `pip freeze` output or a lock tool of your choice), and list the pinned driver/ODM versions in the README. Prefer the driver/ODM versions a Learn quickstart states it tested when they install on this runtime.
- Target cluster: tier {tier}, {shard_count} shard(s), server version {server_version}, high availability {ha_mode}, authentication: {auth_modes}. Treat these as facts; do not spend readiness effort re-deriving them.
```

Replace the existing hard-coded "compute tier M30, MongoDB 7.0 wire protocol" text with these placeholders.

### 2. `loop/run_loop.py`

Fill `{tier}`, `{shard_count}`, `{server_version}`, `{ha_mode}`, `{auth_modes}` the same way `{database}` and `{mcp_line}` are filled, from `probe_cluster()` below; fall back to the `--tier`/`--shard-count`/`--high-availability` values used in `loop/provision.sh` when `az` is unavailable.

### 3. `factory/config.py`

Add `cluster_name` and `resource_group` to `Settings`, read from the same `FACTORY_CLUSTER` / `FACTORY_RG` variables `loop/provision.sh` uses.

### 4. `factory/tools/environment.py`: two new probes

```python
EXPECTED_CLUSTER_SUFFIX = ".mongocluster.cosmos.azure.com"
REQUIRED_ENV_VARS = {"DOCUMENTDB_URI": "Connection string for the target cluster"}

def probe_env_vars() -> list[dict]:
    """Presence only. Never record or log the value."""
    out = []
    for name, purpose in REQUIRED_ENV_VARS.items():
        value = os.environ.get(name, "")
        detail = "not set"
        if value:
            host = urlsplit(value).hostname or ""
            detail = ("set; host matches expected domain" if host.endswith(EXPECTED_CLUSTER_SUFFIX)
                      else "set; host does NOT match *.mongocluster.cosmos.azure.com")
        out.append({"name": name, "purpose": purpose, "available": bool(value), "detail": detail})
    return out

def probe_cluster(name: str, resource_group: str) -> dict:
    """Topology from the control plane; no data-plane call, no secrets."""
    exe = shutil.which("az")
    if not exe:
        return {"available": False, "detail": "Azure CLI not installed"}
    done = subprocess.run([exe, "documentdb", "mongocluster", "show", "--cluster-name", name,
                           "--resource-group", resource_group, "--output", "json"],
                          capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        return {"available": False, "detail": " ".join((done.stderr or "").split())[:160]}
    props = json.loads(done.stdout).get("properties", {})
    return {"available": True,
            "tier": props.get("compute", {}).get("tier"),
            "shard_count": props.get("sharding", {}).get("shardCount"),
            "server_version": props.get("serverVersion"),
            "auth_modes": props.get("authConfig", {}).get("allowedModes"),
            "high_availability": props.get("highAvailability", {}).get("targetMode")}
```

(Add `os`, `json`, `shutil`, `subprocess` and `from urllib.parse import urlsplit` imports if not already present.)

### 5. `factory/agents/readiness.py::collect_inventory()`: two new keys

```python
"environment_variables": environment.probe_env_vars(),
"target_cluster": environment.probe_cluster(ctx.settings.cluster_name, ctx.settings.resource_group),
```

Interpreter versions are already in `command_line_tools`; no new key is needed for them.

### 6. `prompts/readiness_checker.md`, under **Information gaps**, add

> Do not list as an information gap anything the machine inventory or run environment already states: interpreter versions, the dependency-pinning policy, whether a required environment variable is present, or the target cluster's tier, shard count and server version. If the inventory says a variable is missing or the cluster topology could not be read, that is a `blocker`, not a documentation gap.

### 7. `prompts/builder.md`, next to the "language, framework, driver, and each pinned version" line, add

> Pin to the exact versions that resolve on the inventory's Python/Node versions and commit the lockfile. Where a Learn quickstart states the driver/ODM versions it tested, prefer those when they install cleanly here; otherwise use the latest stable that installs, and record the choice in the README.

Out of scope: no change to the Agent Kit or Learn; env-var presence and topology are only answerable by whoever controls the run environment.

## Evidence

- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` and `doc-gaps.md` (multishard?, `DOCUMENTDB_URI` availability, Mongoose 7.x chosen vs tested 9.12.1)
- `runs/09-trade-settlement-tracker/20261124-201323/02-inventory.json` (interpreter versions present; no env-var or cluster keys)
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` and `app/package.json` (`mongoose ^7.7.0`; `package-lock.json` resolves `mongodb` 5.9.2)
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/02-readiness.json` and `app/requirements.txt` (floor pins)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json` (`DOCUMENTDB_URI` presence)
- `runs/18-adverse-event-reporting-pipeline/20261124-195726/02-readiness.json` (Beanie/pymongo/motor pins for Python 3.13)

## Open questions

1. [needs SME confirmation] The JSON property paths in `probe_cluster()` (`compute.tier`, `sharding.shardCount`, `serverVersion`, `authConfig.allowedModes`, `highAvailability.targetMode`) follow the `Microsoft.DocumentDB/mongoClusters` schema but should be checked against actual `az documentdb mongocluster show` output from the installed `documentdb` extension.
2. [needs SME confirmation] The builder text tells agents to prefer Learn-quickstart tested driver/ODM versions. The reviewer flagged driver version floors as unverified in other drafts; confirm the Learn-stated versions (e.g. Mongoose 9.12.1 / Node driver 7.8.0) are the ones the service team wants recommended.
3. [needs SME confirmation] Counts are unstable: "around half of samples" comes from a loose keyword scan (another scan gave a different number). Re-run after the other harness fixes before quoting it externally.

## Source drafts

- 055-run-environment-inventory-handed-to-the-readiness-build-stag.md
