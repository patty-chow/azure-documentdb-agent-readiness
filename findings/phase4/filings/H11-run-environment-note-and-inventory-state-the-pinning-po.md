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
open_questions: 2
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
- the cluster's shard count, HA mode and auth modes, although `loop/provision.sh` creates it with `--tier M30 --shard-count 1 --high-availability Disabled` and `az documentdb mongocluster show` returns them from the control plane as `properties.compute.tier`, `properties.sharding.shardCount`, `properties.serverVersion`, `properties.authConfig.allowedModes` (array) and `properties.highAvailability.targetMode`. The live output observed on 2026-11-25 (DECISIONS.md, topic 11) reported tier M30, 1 shard, HA Disabled, NativeAuth and server version 8.0, so the note's hard-coded "MongoDB 7.0 wire protocol" already disagrees with the control plane, and with the data plane: an 8.0 cluster reports wire version 25 in `hello` and 8.0.0 in `buildInfo` (managed-service test of 2026-11-25 on a separate 8.0 cluster; ENGINE-TESTS.md, Managed service).

The readiness agent therefore files these as documentation `information_gaps`, and the builder picks versions from model prior.

## Why it matters

- In one experiment run of 100 samples, 9 findings from 8 distinct samples trace to this theme (counts are from that single run). A rough keyword scan suggests around half of all samples (unstable count; see open question 2) raise a similar-shaped gap (Python version, ODM/driver pins, `DOCUMENTDB_URI` presence, shard topology). That is harness noise inside the "Learn docs information gap" signal the product teams are meant to act on.
- What the agent did wrong: sample 09 chose Mongoose 7.x by default and shipped a caret range `^7.9.0`, a caret on a version that does not exist (npm's `7x` tag is 7.8.14); its run is one of 13 in the experiment that failed with `npm ERR! notarget` on nonexistent `mongodb`/`mongoose` versions (DECISIONS.md, topic 4, item 4.8). The Learn Mongoose quickstart it read states that it was tested with the MongoDB Node.js driver 7.8.0 as a dependency of Mongoose 9.12.1 and installs `mongoose@9.12.1` (quickstart-nodejs-mongoose, ms.date 2026-11-17, and tutorial-nodejs-mongoose, ms.date 2026-11-16, both updated 2026-11-24; re-read 2026-11-25, see Resolved). Sample 16 declared `mongoose ^7.7.0` (its lockfile resolves the `mongodb` driver to 5.9.2); Mongoose's own compatibility table lists only `^8.7.0` or `^9.0.0` for MongoDB 8.x, the server version the cluster reports. Sample 17 shipped floor pins (`pymongo>=4.5.0`, `langchain>=0.0.350`), so the build is not reproducible.
- Samples 09 and 12 each spent a gap on "is `DOCUMENTDB_URI` really set?", and 09 on "is the cluster multishard?". Shard count decides whether the portal-only "Change streams for multishard clusters" toggle must be enabled: multishard change streams are still preview on the Learn change-streams page (2026-11-16), while single-shard clusters need no enablement step, which the experiment observed working in run 07-lab-results-aggregator (DECISIONS.md, topic 8). Both gaps are one probe away from being facts.

## Proposed change

### 1. `loop/run-environment.md`: add two bullets

```
- Runtime and dependency policy: target the interpreter versions reported in the machine inventory (`command_line_tools` -> python, node). Pin dependencies to the exact versions pip/npm resolve in this environment (`==` in requirements.txt, exact versions in package.json), commit the lockfile (package-lock.json; `pip freeze` output or a lock tool of your choice), and list the pinned driver/ODM versions in the README. Where a Learn page states a tested version (today the Beanie and Django quickstarts, Beanie 2.2.0 and Django MongoDB Backend 6.1.0 with PyMongo 4.19.0 on Python 3.13.x, and the Mongoose quickstart and tutorial, Mongoose 9.12.1 with its bundled Node driver 7.8.0 on Node 22.x), prefer it when it installs on this runtime; otherwise resolve the current stable release and pin it exactly. Never pin a version you have not seen resolve. On Node 24 use the `mongodb` 7.x driver line (MongoDB's compatibility table marks 6.x untested on Node 24), and on a server-version 8.0 cluster use Mongoose `^8.7.0` or 9.x, not 7.x.
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

The `show` output is the unflattened ARM resource body, so the `properties` lookup above is required; the five paths match the extension's generated schema and the live output observed on 2026-11-25 (DECISIONS.md, topic 11). The command needs the `documentdb` extension and Azure CLI 2.75.0 or later; `loop/provision.sh` already installs the extension, and without a TTY the Azure CLI installs it on first use without prompting and re-runs the command (`dynamic_install.py`; observed in the managed-service test of 2026-11-25, which installed the stable 1.0.0; with a TTY the CLI stops at a "(Y/n)" prompt instead), so the probe, which runs with `stdin` set to `/dev/null`, cannot hang on a prompt.

### 5. `factory/agents/readiness.py::collect_inventory()`: two new keys

```python
"environment_variables": environment.probe_env_vars(),
"target_cluster": environment.probe_cluster(ctx.settings.cluster_name, ctx.settings.resource_group),
```

Interpreter versions are already in `command_line_tools`; no new key is needed for them.

### 6. `prompts/readiness_checker.md`, under **Information gaps**, add

> Do not list as an information gap anything the machine inventory or run environment already states: interpreter versions, the dependency-pinning policy, whether a required environment variable is present, or the target cluster's tier, shard count and server version. If the inventory says a variable is missing or the cluster topology could not be read, that is a `blocker`, not a documentation gap.

### 7. `prompts/builder.md`, next to the "language, framework, driver, and each pinned version" line, add

> Pin to the exact versions that resolve on the inventory's Python/Node versions and commit the lockfile. Where a Learn page states the driver/ODM versions it tested (today the Beanie, Django and Mongoose pages), prefer those when they install cleanly here; otherwise use the latest stable that installs, and record the choice in the README. Do not write a version you have not seen resolve: on Node 24 use the `mongodb` 7.x line, and on a server-version 8.0 cluster use Mongoose `^8.7.0` or 9.x.

Out of scope: no change to the Agent Kit or Learn here; the unpinned Learn quickstarts and the kit's missing version guidance are filed as K07/L01 (DECISIONS.md, topic 4). Env-var presence and topology are only answerable by whoever controls the run environment.

## Evidence

- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` and `doc-gaps.md` (multishard?, `DOCUMENTDB_URI` availability, Mongoose 7.x chosen vs tested 9.12.1)
- `runs/09-trade-settlement-tracker/20261124-201323/02-inventory.json` (interpreter versions present; no env-var or cluster keys)
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` and `app/package.json` (`mongoose ^7.7.0`; `package-lock.json` resolves `mongodb` 5.9.2)
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/02-readiness.json` and `app/requirements.txt` (floor pins)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json` (`DOCUMENTDB_URI` presence)
- `runs/18-adverse-event-reporting-pipeline/20261124-195726/02-readiness.json` (Beanie/pymongo/motor pins for Python 3.13)

## Resolved

- `probe_cluster()` JSON paths: confirmed. `az documentdb mongocluster show` returns the unflattened ARM body, and `properties.compute.tier`, `properties.sharding.shardCount`, `properties.serverVersion`, `properties.authConfig.allowedModes` (array) and `properties.highAvailability.targetMode` match both the extension's generated `_show.py` schema and live output observed on 2026-11-25. Sources: Azure/azure-cli-extensions `src/documentdb/azext_documentdb/aaz/latest/documentdb/mongocluster/_show.py` (lines 172, 269-270, 281-282, 294-295, 322-323, 414-416); local `az documentdb mongocluster list -o json` with documentdb extension 1.0.0 / azure-cli 2.89.1 (DECISIONS.md, topic 11).
- Multishard change streams: still preview, portal-only enablement; single-shard clusters need no enablement step. Sources: Learn change-streams page (ms.date 2026-11-16); run 07-lab-results-aggregator/20261124-194018 build log (DECISIONS.md, topic 8). The managed-service test of 2026-11-25 confirmed the single-shard case on a new cluster with no feature enabled (collection streams work with no enablement step); multi-shard clusters were not tested (ENGINE-TESTS.md, Managed service).
- Learn-stated Mongoose versions: confirmed. Both Learn Mongoose pages carry a "Tested driver version" section naming MongoDB Node.js driver 7.8.0 as a dependency of Mongoose 9.12.1, install `mongoose@9.12.1`, and require Node.js 22.12.0 or later in the 22.x line. Sources: Learn quickstart-nodejs-mongoose (ms.date 2026-11-17, updated 2026-11-24) and tutorial-nodejs-mongoose (ms.date 2026-11-16, updated 2026-11-24), both re-read 2026-11-25. Not yet in DECISIONS.md: topic 4, item 4.10 lists tested pins only for the Beanie and Django pages and should be amended to add these two.

## Open questions

1. [needs SME confirmation] Does Microsoft maintain Azure DocumentDB-specific tested driver/ODM versions that the builder text should prefer, and which? Learn states tested pins for the Beanie and Django quickstarts (Beanie 2.2.0 / Django MongoDB Backend 6.1.0 with PyMongo 4.19.0 on Python 3.13.x) and for the Mongoose quickstart and tutorial (Mongoose 9.12.1 with Node driver 7.8.0, on Node 22.x; see Resolved); the Node driver, .NET, Go, Rust and LlamaIndex quickstarts install unpinned, the two Java pages disagree (5.2.0 vs 5.4.0), and whether Node 24 was tested, and with which driver line, is unstated: the Mongoose pages name Node 22.x and the Node driver quickstart says 22 or newer (DECISIONS.md, topic 4, open items 4.8, 4.9 and 4.10). Until answered, the proposed text uses the best guess: prefer a Learn-stated tested pin where one exists, otherwise resolve the current stable release and pin exactly; mongodb 7.x on Node 24, Mongoose ^8.7/9.x on server version 8.0.
2. Counts are unstable: "around half of samples" comes from a loose keyword scan (another scan gave a different number), and every count in this filing is from one run of 100 prompts with known harness defects. Re-run after the other harness fixes before quoting it externally. (Harness matter, not an SME question.)

## Source drafts

- 055-run-environment-inventory-handed-to-the-readiness-build-stag.md
