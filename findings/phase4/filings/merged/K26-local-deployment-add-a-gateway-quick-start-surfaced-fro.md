---
id: K26
title: "local-deployment: add a gateway quick start surfaced from AGENTS.md and mcp-setup"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 15
member_drafts:
  - 059-local-documentdb-gateway-container-is-never-started-surface-.md
open_questions: 2
---

# local-deployment: add a gateway quick start surfaced from AGENTS.md and mcp-setup

## What happens today

`skills/local-deployment/SKILL.md` names the Gateway image (`ghcr.io/documentdb/documentdb/documentdb-local`, MongoDB wire protocol on port 10260) and then only links seven rule files. The runnable pieces are scattered:

- `docker run` is in `local-choose-deployment-method.md` ("Correct" section) and `local-ports-and-bindings.md`.
- The `mongosh` / driver connection examples are in `local-connection-config.md`.
- Teardown exists only as `docker compose down` in `local-docker-compose-setup.md` and in the integration-test example in `local-prod-parity.md`.

Nothing at the kit's entry points tells an agent to detect Docker and offer the local gateway as a dev loop:

- `AGENTS.md` "Routing hints" routes to the skill only on "Running DocumentDB locally", so an agent building a sample against a provisioned Azure cluster never gets there. (The only other `docker run` pointer in `AGENTS.md` is the Route A diagnostic toolbox via `docs/DIAGNOSTICS.md`.)
- `skills/mcp-setup/SKILL.md` Step 1 ("Confirm prerequisites") checks only `node --version` and `git --version`.
- `skills/mcp-setup/SKILL.md` Step 2 row B ("Local MongoDB / DocumentDB") gives `mongodb://localhost:27017`. That is right for a community MongoDB container but not for the DocumentDB local gateway, which listens on 10260 and needs TLS (self-signed cert) plus SCRAM credentials.
- `skills/connection/SKILL.md` never mentions a local target.

Microsoft Learn has no local/emulator page for Azure DocumentDB (it links the open-source project), so the kit is the right home for this.

## Why it matters

We ran a coding agent (gpt-5-mini with this kit and the DocumentDB, Azure and Learn MCP servers) on 100 sample app prompts; counts below are from that one experiment run (120 run logs including reruns).

- In 15 of the 100 samples, the readiness review flagged "local DocumentDB gateway not running" as a missed accelerator. This count is indicative only: the reviewer notes that documentdb-local "missed accelerator" results are partly a harness artifact (see Open questions).
- The agent loaded `documentdb-local-deployment` during several builds and still never started the container. Across all 120 `events.jsonl` logs, no command the agent ran invoked `docker`.
- When agents wrote a local command into their reports, they improvised: several suggested a community `mongo:6.0` / `mongo:7` container on 27017 (which does not exercise the DocumentDB engine), and the one that used the gateway image omitted credentials (the image requires `PASSWORD`).

Result: every integration test and index-iteration cycle ran against the shared Azure cluster.

## Proposed change

### 1. `skills/local-deployment/SKILL.md`: add above the "Image choices:" list

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

**Parity caveats vs Azure DocumentDB:** the local gateway speaks the same wire protocol, so the same driver code should work by swapping `DOCUMENTDB_URI` between this and the cluster's `mongodb+srv://...mongocluster.cosmos.azure.com` string. It is a single-container dev engine: one SCRAM admin user, no Microsoft Entra ID auth, no vCore tier sizing, HA/replication, firewall, `az documentdb mongocluster` or portal features. Re-run `cosmosSearch` vector-index and text-index (full-text) tests against the Azure cluster before shipping; treat local results for those as a smoke test. See [local-prod-parity](local-prod-parity.md).
````

Keep the existing "## Rules" list (which links `local-docker-compose-setup.md`) unchanged: compose stays the recommended committed form; the quick start is the one-shot an agent runs at setup time.

### 2. `skills/mcp-setup/SKILL.md`

Step 1, after the `git --version` line:

```bash
docker --version  # optional: if present, start a local gateway for the dev loop
                  # (skills/local-deployment/SKILL.md -> Quick start) and add it
                  # as a second CONNECTION_PROFILES entry, e.g. "local"
```

Step 2: replace row B with two rows so the targets are not conflated:

| Option | When to use | Example URI |
|---|---|---|
| **B1. Local DocumentDB gateway (Docker)** | Local dev against the DocumentDB engine | `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256` |
| **B2. Local community MongoDB** | Generic MongoDB testing only | `mongodb://localhost:27017` |

### 3. `AGENTS.md`, "Routing hints for agents"

Add next to the existing local-deployment hint:

```markdown
- **Starting a new sample or integration tests and `docker` is on PATH** → `documentdb-local-deployment` (run its Quick start first; point tests at the local gateway, then switch `DOCUMENTDB_URI` to the Azure cluster)
```

Sources for the commands: https://documentdb.io/docs/documentdb-local/ (port 10260 default, `PASSWORD` required, `--username/--password` supported, no replication or failover) and the github.com/documentdb/documentdb README; the kit's own `local-prod-parity.md` already says to version-pin the image.

## Evidence

Run folders from the experiment:

- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/` (`02-readiness.json` accelerators_missed; `events.jsonl`: skill loaded, no docker command run)
- `runs/13-chronic-disease-risk-predictor/20261124-194916/02-readiness.json` (improvised gateway `docker run` with no credentials; also suggested community `mongo:7` on 27017)
- `runs/10-expense-report-auto-categorizer/20261124-191257/02-readiness.json` (image available but gateway not running)
- `runs/04-natural-language-product-search/20261124-183232/02-readiness.json` (local container would speed iterative index builds)
- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/02-readiness.json` (Docker installed, no container started)

## Open questions

1. Part of the "missed accelerator" signal may come from the experiment harness (local tools such as documentdb-local were reported as missed even where the harness did not let the agent use them). The doc gap stands on the file evidence above, but the sample count of 15 should be treated as indicative until a rerun after the harness fixes.
2. Maintainers: is `AGENTS.md` routing on "docker is on PATH" the trigger you want, or would you prefer the hint only in `mcp-setup` so agents do not start containers unasked?

## Source drafts

- 059-local-documentdb-gateway-container-is-never-started-surface-.md
