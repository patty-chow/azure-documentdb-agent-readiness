---
title: "Run-environment note and inventory should state a pinning policy, env-var presence and cluster shard count so readiness stops scoring them as doc gaps"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P2
sample_count: 8
findings: 9
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Run-environment note and inventory should state a pinning policy, env-var presence and cluster shard count

## What happens today

Stage 2 hands the readiness agent two things it is told to treat as fact: `loop/run-environment.md` (filled in by `loop/run_loop.py`, which replaces `{database}` and `{mcp_line}`) and the inventory built by `factory/agents/readiness.py::collect_inventory()` from `factory/tools/environment.py`.

Some of the facts are already there:

- `run-environment.md` states the cluster is compute tier M30 with the MongoDB 7.0 wire protocol and DiskANN/HNSW/IVF vector indexes, that Node.js 24 is available, and that `python`/`pip` resolve to a per-run venv.
- `probe_clis()` records interpreter versions in `02-inventory.json` under `command_line_tools` (for example `python` -> `Python 3.13.13`, `node` -> `v24.21.0`).

What is **not** there:

- any instruction to *target* those interpreter versions, or a dependency-pinning policy (exact pins vs caret ranges vs floors in `requirements.txt` / `package.json`, lockfile, README record);
- whether `DOCUMENTDB_URI` is actually present in the process environment (the note asserts it; `probe_clis()` and `probe_azure_login()` never check, and no MCP tool exposes env vars);
- the cluster's shard count, HA mode and auth modes, even though `loop/provision.sh` creates it with `--tier M30 --shard-count 1 --high-availability Disabled`, and `az documentdb mongocluster show -n <cluster> -g <rg>` returns all of them from the control plane.

So the readiness agent files these as `information_gaps` against the docs and skills, and the builder decides versions from model prior.

## Why it matters

- The 9 findings in this theme come from 8 samples. A rough keyword scan of all `02-readiness.json` files suggests around half of the samples raise an information gap of a similar shape (Python version, Mongoose/pymongo/Beanie/Motor pins, `DOCUMENTDB_URI` presence, shard topology); that is harness noise inside the "learn-docs information gap" signal and dilutes the findings the Learn and Agent Kit teams should act on.
- Build effect: `runs/09-trade-settlement-tracker/20261124-201323/doc-gaps.md` records that the builder chose Mongoose 7.x by model default and ended with a caret range `^7.9.0`, although the Learn Mongoose quickstart it read lists Mongoose 9.12.1 / driver 7.8.0 as tested. `runs/16-subscription-billing-engine/20261124-192251/app/package.json` declares `mongoose ^7.7.0` (its `package-lock.json` resolves the `mongodb` driver to 5.9.2). `runs/17-stress-testing-multi-agent-runner/20261124-202407/app/requirements.txt` ships floor pins (`pymongo>=4.5.0`, `langchain>=0.0.350`), so the build is not reproducible.
- 09-trade-settlement-tracker and 12-hospital-bed-occupancy-tracker each spend an information gap on "is `DOCUMENTDB_URI` really set?", and 09 on "is the cluster multishard? (decides whether multishard change streams must be enabled)". Both are one probe away from being facts.

## Proposed change (PR)

### 1. `loop/run-environment.md` - add two bullets

```
- Runtime and dependency policy: target the interpreter versions reported in the machine inventory (`command_line_tools` -> python, node). Pin dependencies to the exact versions pip/npm resolve in this environment (`==` in requirements.txt, exact versions in package.json), commit the lockfile (package-lock.json; `pip freeze` output or a lock tool of your choice), and list the pinned driver/ODM versions in the README. Prefer the driver/ODM versions a Learn quickstart states it tested when they install on this runtime.
- Target cluster: tier {tier}, {shard_count} shard(s), server version {server_version}, high availability {ha_mode}, authentication: {auth_modes}. Treat these as facts; do not spend readiness effort re-deriving them.
```

The existing "compute tier M30, MongoDB 7.0 wire protocol" text can then be replaced by the placeholders. In `loop/run_loop.py`, fill the new placeholders the same way `{database}` and `{mcp_line}` are filled, from the probe below, falling back to the `--tier`/`--shard-count` values used in `loop/provision.sh` when `az` is unavailable.

### 2. `factory/tools/environment.py` - two new probes

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

(Property paths follow the `Microsoft.DocumentDB/mongoClusters` resource schema; confirm them against the output of `az documentdb mongocluster show` on the installed `documentdb` extension. `Settings` has no cluster fields today: add `cluster_name` and `resource_group`, read from the same `FACTORY_CLUSTER` / `FACTORY_RG` variables `loop/provision.sh` uses.)

### 3. `factory/agents/readiness.py::collect_inventory()` - two new keys

```python
"environment_variables": environment.probe_env_vars(),
"target_cluster": environment.probe_cluster(ctx.settings.cluster_name, ctx.settings.resource_group),
```

Interpreter versions are already recorded in `command_line_tools`; no new key is needed for them, only the run-environment instruction in step 1 to target them.

### 4. Prompts

`prompts/readiness_checker.md`, under **Information gaps**, add:

> Do not list as an information gap anything the machine inventory or run environment already states: interpreter versions, the dependency-pinning policy, whether a required environment variable is present, or the target cluster's tier, shard count and server version. If the inventory says a variable is missing or the cluster topology could not be read, that is a `blocker`, not a documentation gap.

`prompts/builder.md`, next to the existing "language, framework, driver, and each pinned version" line, add:

> Pin to the exact versions that resolve on the inventory's Python/Node versions and commit the lockfile. Where a Learn quickstart states the driver/ODM versions it tested, prefer those when they install cleanly here; otherwise use the latest stable that installs, and record the choice in the README.

## Out of scope

This does not touch the Agent Kit or Learn: the Learn quickstarts already publish tested driver/ODM versions (for example the Node.js/Mongoose quickstart), and "is the env var set" / "is it multishard" are answerable only by whoever controls the run environment.

## Evidence

- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` (information_gaps: multishard?, `DOCUMENTDB_URI` availability, Mongoose pin)
- `runs/09-trade-settlement-tracker/20261124-201323/doc-gaps.md` (builder chose Mongoose 7.x by default; docs tested 9.12.1)
- `runs/09-trade-settlement-tracker/20261124-201323/02-inventory.json` (already reports `Python 3.13.13`, `v24.21.0`; no env-var or cluster keys)
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` and `app/package.json` (`mongoose ^7.7.0`; lockfile resolves `mongodb` 5.9.2)
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/02-readiness.json` and `app/requirements.txt` (floor pins)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json` (presence of `DOCUMENTDB_URI`)
- `runs/18-adverse-event-reporting-pipeline/20261124-195726/02-readiness.json` (exact Beanie/pymongo/motor pins for Python 3.13)

## Verification

### 1. Already covered? partially_covered

The target is the pipeline itself, so I read its source.
- `loop/run-environment.md` already says: "compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes" and "Node.js 24 with npm and npx is available". So the tier and server/wire version are covered; shard count, HA and auth modes are not.
- `factory/tools/environment.py::probe_clis()` runs `python --version` and `node --version`, and `runs/09-trade-settlement-tracker/20261124-201323/02-inventory.json` shows `Python 3.13.13` and `v24.21.0`. Runtime versions are therefore already in the inventory. What is missing is an instruction to target them, plus any pinning policy. I removed the draft's proposed `runtime_versions` key and its claim that versions are absent.
- Nothing in `factory/tools/environment.py`, `factory/agents/readiness.py` (keys: command_line_tools, azure_sign_in, skill_folders_searched, installed_skills, mcp_servers, run_policy) or the prompts checks env-var presence or cluster topology. `prompts/builder.md` only asks the build report to list "each pinned version" and sets no pinning policy.
- `loop/provision.sh` creates the cluster with `--tier M30 ... --shard-count 1 --high-availability Disabled`.

### 2. Premise true? confirmed (with factual corrections applied)

- `az documentdb mongocluster show` exists (documentdb extension). It takes `--cluster-name/-n` and `--resource-group/-g`, which I checked against the local `--help`. The resource type is Microsoft.DocumentDB/mongoClusters. The host suffix `.mongocluster.cosmos.azure.com` matches the service's connection-string format.
- Evidence checked: sample 16 `package.json` has `"mongoose": "^7.7.0"`. The `mongodb 5.9.2` comes from `package-lock.json`, not `package.json`, so I corrected the text. Sample 17 `requirements.txt` has `pymongo>=4.5.0` and `langchain>=0.0.350`. Sample 09 `doc-gaps.md` records Mongoose 7.x by default, the caret range `^7.9.0` and tested Mongoose 9.12.1 / driver 7.8.0.
- Corrected: the draft said the env note and inventory do not state Python/Node versions or the server version. They do: the inventory reports the interpreter versions and the note states MongoDB 7.0 wire protocol. Only the target and pinning policy, env-var presence and shard count/HA/auth are missing.
- Softened: the draft gave "roughly 45 of 100 samples". My own keyword scan of the `02-readiness.json` information_gaps gave a different count (about 55 sample folders with a loose pattern), so the body now says "around half" and calls it a rough scan.
- `Settings` (`factory/config.py`) has no cluster or resource-group fields. I made the draft say to add them, read from `FACTORY_CLUSTER`/`FACTORY_RG` as in `provision.sh`.

### 3. Maintainer skeptic: confirmed

The change is right for this repository. It names exact files (`loop/run-environment.md`, `loop/run_loop.py`, `factory/tools/environment.py`, `factory/agents/readiness.py`, `factory/config.py`, `prompts/readiness_checker.md`, `prompts/builder.md`) and gives concrete code and prompt text. It has a DocumentDB angle: the mongocluster control-plane probe, the multishard change-stream question, and driver pins against the Learn-tested versions. The env-var probe never records the value. I would accept it after the edits above.

## Finding ids

- F1568
- F1569
- F2063
- F2721
- F2754
- F2787
- F2920
- F2949
- F3023
