---
title: "local-deployment: add a gateway quick start and surface it from AGENTS.md and mcp-setup prerequisites"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 15
findings: 15
bucket: kit-accelerator-missed
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# local-deployment: add a gateway quick start and surface it from AGENTS.md and mcp-setup prerequisites

## What happens today

`skills/local-deployment/SKILL.md` names the Gateway image (`ghcr.io/documentdb/documentdb/documentdb-local`, MongoDB wire protocol on port 10260) and then links seven rule files. The runnable pieces are split across them:

- `docker run` lives in `local-choose-deployment-method.md` ("Correct" section) and `local-ports-and-bindings.md`
- the `mongosh` / driver connection examples live in `local-connection-config.md`
- teardown exists only as `docker compose down` in `local-docker-compose-setup.md`

Nothing at the kit's entry points tells an agent to *detect Docker and offer the local gateway as a dev loop*:

- `AGENTS.md` "Routing hints" routes to the skill only on "Running DocumentDB locally", so an agent building a sample against a provisioned Azure cluster never routes there. (The only other `docker run` pointer in `AGENTS.md` is for Route A, the diagnostic toolbox, via `docs/DIAGNOSTICS.md`.)
- `skills/mcp-setup/SKILL.md` Step 1 ("Confirm prerequisites") checks only `node --version` and `git --version`.
- `skills/mcp-setup/SKILL.md` Step 2 row B ("Local MongoDB / DocumentDB") gives `mongodb://localhost:27017`. That is correct for a community MongoDB container but not for the DocumentDB local gateway, which listens on 10260 by default and needs `tls=true&tlsAllowInvalidCertificates=true` plus SCRAM credentials (self-signed cert).
- `skills/connection/SKILL.md` has no mention of a local target.

## Why it matters

In a 100-sample agent-readiness experiment (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers, 120 run logs including reruns):

- The readiness stage flagged "local DocumentDB gateway container not running" as a missed accelerator in 15 distinct samples (this issue's findings).
- The agent loaded `documentdb-local-deployment` during several builds and still never started the container.
- Across all 120 `events.jsonl` logs, no `run_command` call ever invoked `docker`.
- When agents did write a local command into their reports, it was improvised rather than the kit's: several suggested a community `mongo:6.0` / `mongo:7` container on 27017 (which does not exercise the DocumentDB engine), and the one that used the gateway image omitted credentials (`PASSWORD` is required by the image).

Result: every integration test and every index-iteration cycle ran against the shared M30 cluster.

## Proposed change

### 1. `skills/local-deployment/SKILL.md`: add a quick start above "Image choices"

````markdown
## Quick start (local dev loop)

Use this when Docker is present and you are writing a sample, running integration tests, or iterating on indexes. It avoids round-trips to the Azure cluster until the code is stable.

```bash
# 1. run (loopback only, named so teardown is one command; pin a tag in CI, see local-prod-parity)
docker run --pull always -dt --name documentdb-local \
  -p 127.0.0.1:10260:10260 \
  -e USERNAME=docdbuser -e PASSWORD="${DOCUMENTDB_PASSWORD:?set DOCUMENTDB_PASSWORD}" \
  ghcr.io/documentdb/documentdb/documentdb-local:latest

# 2. verify (self-signed cert, so allow invalid certs locally only)
mongosh "mongodb://localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256" \
  -u docdbuser -p "$DOCUMENTDB_PASSWORD" --eval 'db.runCommand({ ping: 1 })'

# 3. connection string for the app (read from env, never hard-code)
export DOCUMENTDB_URI="mongodb://docdbuser:${DOCUMENTDB_PASSWORD}@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256"

# 4. teardown
docker rm -f documentdb-local
```

(`-e USERNAME/-e PASSWORD` and the `--username/--password` arguments after the image name are equivalent; the CLI arguments override the env vars.)

**Parity caveats vs Azure DocumentDB:** the local gateway speaks the same wire protocol, so the same driver code should work by swapping `DOCUMENTDB_URI` between this and the cluster's `mongodb+srv://...mongocluster.cosmos.azure.com` string. It is a single-container dev engine: one SCRAM admin user, no Microsoft Entra ID auth, no M-tier sizing, HA/replication, firewall, `az documentdb mongocluster` or portal features. Re-run `cosmosSearch` vector-index and text-index (full-text) tests against the Azure cluster before shipping; treat local results for those as a smoke test. See [local-prod-parity](local-prod-parity.md).
````

(`docker compose` remains the recommended committed form; the quick start is the one-shot an agent runs at environment-setup time, and `local-docker-compose-setup.md` is linked right below it.)

### 2. `skills/mcp-setup/SKILL.md`

Step 1, after the `git --version` line:

```bash
docker --version  # optional: if present, start a local gateway for the dev loop
                  # (skills/local-deployment/SKILL.md -> Quick start) and add it
                  # as a second CONNECTION_PROFILES entry, e.g. "local"
```

Step 2: split row B into two rows so the two targets are not conflated:

| Option | When to use | Example URI |
|---|---|---|
| **B1. Local DocumentDB gateway (Docker)** | Local dev against the DocumentDB engine | `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256` |
| **B2. Local community MongoDB** | Generic MongoDB testing only | `mongodb://localhost:27017` |

### 3. `AGENTS.md`: "Routing hints for agents"

Add one line next to the existing local-deployment hint:

```markdown
- **Starting a new sample or integration tests and `docker` is on PATH** → `documentdb-local-deployment` (run its Quick start first; point tests at the local gateway, then switch `DOCUMENTDB_URI` to the Azure cluster)
```

## Evidence (run folders from the experiment)

- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json` (accelerators_missed) and `.../events.jsonl`: skill loaded, no docker command ever run
- `runs/13-chronic-disease-risk-predictor/20261124-194916/02-readiness.json`: agent improvised a gateway `docker pull/run` with no credentials, and also suggested a community `mongo:7` container on 27017
- `runs/10-expense-report-auto-categorizer/20261124-191257/02-readiness.json`: "docker image available but gateway not running"
- `runs/04-natural-language-product-search/20261124-183232/02-readiness.json`: "starting the local dev container would speed iterative index builds"
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/02-readiness.json`: "docker is installed but no container is started"

## Verification

### 1. Already covered? partially_covered

The kit documents the local gateway thoroughly, but not where an agent looks at setup time, and not as one runnable sequence.
- `skills/local-deployment/SKILL.md` lists the image and port, then only links rule files; no command in SKILL.md itself.
- `skills/local-deployment/local-choose-deployment-method.md` "Correct" section contains `docker run --pull always -dt -p 10260:10260 -e USERNAME=docdbuser -e PASSWORD=... ghcr.io/documentdb/documentdb/documentdb-local:latest`; `local-connection-config.md` contains the `mongosh localhost:10260 ... --tls --tlsAllowInvalidCertificates` command; `local-prod-parity.md` contains a compose file.
- `AGENTS.md` line 98: "Running DocumentDB locally → `documentdb-local-deployment`" is the only routing hint; line 28 points to `docs/DIAGNOSTICS.md` for a `docker run` only for the Route A diagnostic toolbox.
- `skills/mcp-setup/SKILL.md` Step 1 checks only node and git; Step 2 row B: "Local MongoDB / DocumentDB | Local dev | `mongodb://localhost:27017`".
- Learn (https://learn.microsoft.com/en-us/azure/documentdb/) has no local/emulator page; it links the open-source project, so the kit is the right home.

### 2. Premise true? confirmed (one evidence claim corrected)

- Image, port 10260, TLS with self-signed cert and SCRAM: confirmed by https://documentdb.io/docs/documentdb-local/ (example `docker run -dt -p 127.0.0.1:10260:10260 ... -e USERNAME -e PASSWORD ghcr.io/documentdb/documentdb/documentdb-local:<tag>`; `DOCUMENTDB_PORT` default 10260, `PASSWORD` required) and https://github.com/documentdb/documentdb README (connection string `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`).
- Corrected: the draft said agents used "wrong flag names" (`--username/--password`) for this image. That is false: documentdb.io lists `--username`/`--password` as supported CLI options that override `USERNAME`/`PASSWORD`, and the upstream README uses them. The evidence paragraph now says what was actually wrong (community `mongo` images on 27017, missing credentials), and the quick start notes both forms are equivalent.
- Corrected: "`createSearchIndexes` full-text tests" replaced with "text-index (full-text) tests"; Azure DocumentDB full-text search uses text indexes, not Atlas Search index APIs.
- Corrected: row B at 27017 is not "wrong" for a community MongoDB, only for the DocumentDB gateway; the change now splits the row instead of replacing it.
- Corrected: dropped unverifiable counts (119/120 Docker detected, 23 runs, 14 builds). Spot check of the 120 `events.jsonl` files found zero `run_command` calls containing `docker`, which supports the core claim.
- Single-container, no replication: confirmed by documentdb.io ("no replication or failover"). Entra ID is supported on Azure (Learn hub links "Use Microsoft Entra ID and role-based access control"); the local image documents a single SCRAM admin user only.
- Version pinning: documentdb.io's example pins a tag and the kit's own `local-prod-parity.md` says "Version-pin the local image"; the quick start comment now says so.

### 3. Maintainer skeptic: confirmed

Names three exact files in Azure/documentdb-agent-kit and gives the literal text to add; it is specific to the DocumentDB local gateway (port, TLS, SCRAM, parity with vCore), reuses commands already in the kit's rule files, and fixes a misleading URI row in mcp-setup. Accept with the small edits applied above.

## Finding ids

F0088, F0229, F0399, F0644, F0899, F1447, F1638, F1737, F1931, F2065, F2164, F2202, F2260, F2339, F2498
