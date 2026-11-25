---
id: K27
title: "mcp-setup skill: name the documentdb MCP server as the data-plane server, stop defaulting to a localhost URI, add an 'already configured?' check, and document mongosh as optional with an MCP-tool fallback"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 27
member_drafts:
  - 060-mongosh-is-never-installed-kit-setup-and-connection-skills-s.md
  - 132-believes-the-general-azure-mcp-server-s-cosmos-db-tools-cove.md
  - 133-believes-no-dedicated-data-plane-mcp-server-exists-for-azure.md
  - 031-agent-kit-itself-reinforces-the-27017-prior-mcp-setup-skill-.md
  - 064-mcp-setup-skill-should-recognise-an-existing-documentdb-serv.md
merged_from:
  - K27
  - K12
  - K24
  - K28
open_questions: 7
---

# mcp-setup skill: name the documentdb MCP server as the data-plane server, stop defaulting to a localhost URI, add an "already configured?" check, and document mongosh as optional with an MCP-tool fallback

One documentation PR centred on `skills/mcp-setup/SKILL.md`. It also touches `AGENTS.md`, `README.md`, `GEMINI.md`, `docs/installation/macos.md`, `install.sh`, `install.ps1`, `skills/local-deployment/local-connection-config.md`, `skills/query-optimizer/SKILL.md`, and the launch target in `mcp.json` and `gemini-extension.json`. No code changes except that launch target (one line in each manifest, see section 10) and an optional de-duplication fix in `install.sh`.

## What happens today

`skills/mcp-setup/SKILL.md` is the skill an agent loads to wire up and use the `documentdb` MCP server (`microsoft/documentdb-mcp`, the Azure DocumentDB MCP Toolkit on Microsoft Learn, public preview). It has four gaps, each of which pushes agents toward a wrong prior.

1. **It never says which MCP server does DocumentDB data-plane work.** Neither the skill nor `AGENTS.md` says that `documentdb` is the server for queries, aggregate, explain, indexes, statistics and sample documents. Neither mentions the general Azure MCP Server, whose `cosmos` tools target Azure Cosmos DB accounts, databases and containers (NoSQL API) and cannot reach a `Microsoft.DocumentDB/mongoClusters` cluster; the Azure MCP Server tools page (ms.date 2026-08-11, updated 2026-10-16) lists the Databases namespaces `cosmos`, `mysql`, `postgres`, `redis` and `sql` and no `documentdb` or `mongocluster` namespace, and the request for one (microsoft/mcp#774) was closed on 2026-04-27 as blocked. The skill only says to "list available DocumentDB tools"; it does not list them or their capability gates. `AGENTS.md` routes "Setting up the DocumentDB MCP server" to `documentdb-mcp-setup` but has no routing hint for querying or explaining against a live cluster. A grep of `skills/`, `knowledge-base/`, `AGENTS.md`, `README.md` and `mcp.json` for "Azure MCP", "azmcp", "data plane" and "control plane" finds nothing about server choice.

2. **It presents a localhost URI on 27017 with no credentials and no TLS as the local default.** Nine lines in six files give `mongodb://localhost:27017` as the local DocumentDB connection string:

   | File | Line(s) | Current text |
   |---|---|---|
   | `skills/mcp-setup/SKILL.md` | 88 | Step 2 table, row **B. Local MongoDB / DocumentDB**: `mongodb://localhost:27017` |
   | `README.md` | 160 | `export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'` |
   | `GEMINI.md` | 27 | same export |
   | `docs/installation/macos.md` | 21 | `**Local DocumentDB / MongoDB:** mongodb://localhost:27017` |
   | `install.sh` | 8, 522, 527 | usage comment, `for local dev:` hint, `Local:` example |
   | `install.ps1` | 46, 491 | `.EXAMPLE` block, `Local:` example |

   The local DocumentDB gateway container (`ghcr.io/documentdb/documentdb/documentdb-local`) listens on **10260** by default, requires a **username and password** (without one the container exits at startup) and presents a **self-signed TLS certificate**; its only authentication mechanism is SCRAM-SHA-256. Its default `--tlsMode allowTLS` accepts both plain and TLS connections, and the canonical connection string in the Learn `development-loop` tutorial and the engine README is `mongodb://<admin-username>:<admin-password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`. The kit's own local-deployment skill gives the same endpoint (10260, credentials, `tls=true&tlsAllowInvalidCertificates=true`; `skills/local-deployment/SKILL.md:11`, `local-env-driven-config.md:61`) and the README Quickstart starts the container with `-p 10260:10260` (`README.md:49`), then 110 lines later tells the MCP server to connect on 27017. An MCP profile pointed at 27017 with no credentials cannot reach that container (it only works if the operator remaps the port and still needs the credentials).

3. **It has no "already configured?" check, and the kit spells the server entry three ways, one of which now launches third-party code.** Step 4 says to add the `DocumentDB` entry inside an existing `mcpServers` object but never says to check whether a DocumentDB entry already exists, or how to repair a broken one.

   | Where | Server key | Launch target |
   |---|---|---|
   | `mcp.json` (root), `gemini-extension.json` | `documentdb` | `npx -y documentdb-mcp-server` |
   | `skills/mcp-setup/SKILL.md` Step 4 | `DocumentDB` | `npx -y github:microsoft/documentdb-mcp` |
   | `install.sh` (`MCP_ENTRY="DocumentDB"`) | `DocumentDB` | `node <MCP_DIR>/dist/main.js` (local clone built by the installer) |

   The second and third start the Microsoft server (`package.json` in microsoft/documentdb-mcp names the package `documentdb-mcp-server`, `bin` points to `dist/main.js`). The first does not: Microsoft has never published that npm package (Learn MCP Toolkit page, Limitations: "No published npm package yet. Install from source ... or run directly with `npx -y github:microsoft/documentdb-mcp`"; upstream README: "not yet published to a public package registry"; microsoft/documentdb-mcp#48, #49; Azure/documentdb-agent-kit#20 records `npm view documentdb-mcp-server` returning 404). Since 2026-11-24 the unscoped name `documentdb-mcp-server` is occupied on registry.npmjs.org by a 0.1.0 package from an account not identifiable as Microsoft (no repository or homepage field, no README, two files, bin `documentdb-mcp-local`) whose `index.js` reads `CONNECTION_PROFILES` and opens MongoDB connections. The kit's `npx -y documentdb-mcp-server` therefore no longer fails with a 404; it hands the cluster credentials to code that is not the Microsoft server. `AGENTS.md:105` and `:123`, `CHANGELOG.md:115,121`, `GEMINI.md:3`, `docs/installation/updating.md:24` and `.codex-plugin/plugin.json:27` repeat the claim that the plugin bundles "`documentdb-mcp-server` on npm". The skill's Step 4 already uses the GitHub form; its remark that the repository "may be private" is stale (the repo is public and Learn links it).

   `install.sh` `merge_mcp_entry()` always assigns `node[p]["DocumentDB"]` (and the `jq` path always sets `.[top_key]["DocumentDB"]`), so if the client already has the kit's `documentdb` entry the installer adds a second one: two processes, two `CONNECTION_PROFILES`, every tool listed twice. `remove_mcp_entry()` removes only the literal `DocumentDB` key.

4. **It (and other skills) assume `mongosh` without introducing it.** Step 1 "Confirm prerequisites" lists only `node --version` and `git --version`. `skills/query-optimizer/SKILL.md` (lines 33-51) pairs every MCP tool with a mongosh equivalent; its section "Local mongosh Commands (No MCP Required)" (line 69) and "If MCP is not available, use mongosh directly" (line 227) treat mongosh as the fallback when MCP is missing, but nothing covers the more common case of MCP configured and mongosh absent. `skills/local-deployment/local-connection-config.md` (lines 22, 25, 44) uses `mongosh localhost:10260 ...` for its canonical examples; `local-prod-parity.md:58`, `local-sample-data-management.md:14,32`, `local-ports-and-bindings.md:11` and `local-choose-deployment-method.md:13,41` also reference mongosh with no install guidance. The Learn page "Connect using MongoDB Shell" (https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell) is never linked.

## Why it matters

In one run of an agent-readiness experiment, gpt-5-mini with this kit's skills and the DocumentDB, Azure and Learn MCP servers ran a cold quiz, a readiness check and a build for each of 100 Azure DocumentDB sample prompts. Across the four themes, **27 distinct samples of 100** produced a finding (figure from one run; sample 07-customer-review-sentiment-pipeline appears in both the mongosh and the MCP-server themes and is counted once):

- **mongosh missing (16 samples, from K27).** The readiness check listed mongosh as a missed accelerator ("missing from PATH; installing mongosh speeds manual verification"). Three samples worked out that the DocumentDB MCP server offers the same operations; 13 recorded it only as a gap. None of the 16 builds was blocked: the build agents never ran mongosh, and `list_indexes`, `find_documents` and `explain_operation` did the verification. The harness's own `mongosh --version` inventory probe makes the gap more visible, so the count overstates impact. This is a cheap consistency fix: skills should say what they assume and send the agent to the MCP tools, instead of the agent spending a turn deciding or recommending an install the user did not ask for.
- **Wrong MCP server for the data plane (6 samples, from K12).** Asked cold "Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it?":
  - 2 samples said the general Azure MCP Server or its Cosmos DB tools cover DocumentDB's data plane, confusing Azure DocumentDB with the RU-based Azure Cosmos DB for MongoDB API (once with Azure Cosmos DB for NoSQL); the prior comes from the former name "Azure Cosmos DB for MongoDB vCore".
  - 4 samples said no DocumentDB-specific MCP server exists, so the Azure MCP Server or plain drivers are the way to inspect data.

  After grounding the model got it right, but only from the live tool inventory or a known-accelerators list, never from the kit. An agent that follows its prior either calls `cosmos` tools that cannot reach the cluster or skips `explain_operation`, `sample_documents`, `aggregate` and `get_statistics` and writes ad-hoc driver scripts, making skipped index and query-plan checks more likely. Builds still called `documentdb_*` tools once exposed, so impact was small; the risk is in clients where the agent picks a server from what it has read.
- **27017 localhost prior (5 samples, from K24).** Asked cold how to run the database locally, the agent typically answered "`mongo:7` on 27017". The kit should correct that prior, but `mcp-setup` is often loaded before `local-deployment` and its row B confirms it. Generated apps then wired `.env.example`, seed scripts and integration tests to a stock `mongo` image on 27017 (other runs outside the five show the same: a test defaulting to `localhost:27017`, an `.env.example` hard-coding `:27017`; in run 20-store-locator the `.env.example` used an RU-API style `host:27017/?ssl=true&replicaSet=...` URI). A plain `mongo` image has no `cosmosSearch` vector indexes at all (the local gateway supports `vector-ivf` and `vector-hnsw`; DiskANN, product quantization and full-text search are Azure-only) and does not reproduce the gateway's SCRAM/TLS behaviour, so tests pass or fail for the wrong reasons.
- **Duplicate MCP entry advice (1 sample, from K28).** The `documentdb` server was present and working (18 tools; the build later called `list_databases`, `create_index`, `list_indexes`, `find_documents`), yet the readiness report listed the kit's MCP entry as missing and suggested installing the "GitHub repo variant" as well. Following that advice with the skill as written produces a duplicate entry. In two other samples an existing entry was broken (one failed to start; one had unresolved `CONNECTION_PROFILES`) and the agent sent the user to this skill, which covers only fresh installs, so it improvised repair steps. In another sample the agent correctly answered "installed, no action required": when the agent thinks to check, the check is easy.
- **Credentials to a third-party package (no sample; found while checking the npm claim).** Any client that installs the kit's `mcp.json` or Gemini extension as shipped now runs the unscoped npm package of unknown provenance with the user's `CONNECTION_PROFILES`. This is security-relevant and should not wait for any SME answer.

## Proposed change

Files are listed once each; edits within a file are in document order.

### 1. `skills/mcp-setup/SKILL.md`

**1a. New section after the intro and before `## Safety: never receive credentials in chat`** (from K12):

```markdown
## Which MCP server do I use?

- **Data plane of a live cluster: use `documentdb`** (this server: the Azure DocumentDB MCP
  Toolkit, the `microsoft/documentdb-mcp` server, public preview). It is the MCP server with
  data-plane tools for Azure DocumentDB.
  - Read tools (on by default): `list_databases`, `find_documents`, `count_documents`,
    `aggregate`, `sample_documents`, `explain_operation`, `list_indexes`, `get_statistics`.
  - Write tools (`ENABLE_WRITE_TOOLS=true`): `insert_documents`, `update_documents`,
    `delete_documents`, `find_and_modify`.
  - Management tools (`ENABLE_MANAGEMENT_TOOLS=true`): `create_index`, `drop_index`,
    `current_ops`, `drop_collection`, `rename_collection`, `drop_database`.
  - The kit's `mcp.json` leaves write and management tools off.
- **Azure MCP Server: no Azure DocumentDB tools.** Its `cosmos` tools target Azure Cosmos DB
  accounts, databases and containers and run Cosmos DB SQL (NoSQL API) queries. They do not
  connect to DocumentDB clusters; do not use them to read or write DocumentDB data. Use its
  general tools (resource groups, Bicep schema, deploy, RBAC, Monitor) only for Azure
  resource work around the cluster.
- **Control plane (create, scale, firewall, replicas, Entra admin on a
  `Microsoft.DocumentDB/mongoClusters` cluster):** use `az documentdb mongocluster`,
  Bicep/ARM or Terraform (see the `documentdb-azure-deployment` skill).

Rule: documentdb MCP for data; Azure tooling for resources.
```

Reviewer corrections already applied: the Azure MCP Server is not described as DocumentDB's control plane; `create_index` and `current_ops` are management-gated, not default; no npm package name is stated anywhere in the skill (there is none, see Resolved). The product-name phrasing follows the Learn MCP Toolkit page ("The Azure DocumentDB MCP Toolkit is an open-source Model Context Protocol (MCP) server ... and ships from the microsoft/documentdb-mcp repository"); the repository's own README calls it "DocumentDB MCP Server". The 18 tools and their gates match the Learn page's tool list. The "no Azure DocumentDB tools" sentence describes today (Azure MCP Server tools page, updated 2026-10-16; microsoft/mcp#774 closed 2026-04-27); open question 4 covers whether to soften it.

**1b. New section before "Step 1: Confirm prerequisites"** (from K28):

```markdown
## Step 0: Is it already configured?

Before adding anything, open the client's MCP config (table in Step 4) and look
for an existing entry under `mcpServers` / `mcp.servers` whose `args` contain
`github:microsoft/documentdb-mcp` or a path ending in `documentdb-mcp/dist/main.js`
(the bundled installer's local build). The key may be `documentdb` (the kit's
`mcp.json` / Gemini manifest) or `DocumentDB` (this skill and the bundled
installer). Both launch the same server; only one entry should exist.

- **Entry present and the client lists DocumentDB tools** → nothing to add.
  Skip to Step 5 to verify (`list_databases` with the profile name defined in
  that entry's `CONNECTION_PROFILES`).
- **Entry whose `args` contain the bare npm name `documentdb-mcp-server`** →
  replace the args with `["-y", "github:microsoft/documentdb-mcp"]` before
  anything else. Microsoft has not published an npm package; that name is
  taken by a third-party package, and the entry runs it with your credentials.
- **Entry present but the server does not start or has no tools** → repair it
  in place rather than adding a second one. Check, in order: `TRANSPORT` is
  `stdio`; `AUTH_REQUIRED` is `"false"`; `TRUST_LOCAL_STDIO` is `"true"`
  (`ALLOW_UNAUTHENTICATED_STDIO`, which the Learn MCP Toolkit page still shows,
  is the variable's pre-release name and is ignored by the current server);
  `CONNECTION_PROFILES` is a JSON *string* and any `${VAR}` it references is
  set in the environment the client launches with. Then continue at
  Troubleshooting.
- **No entry** → continue with Step 1.

Never add a second DocumentDB entry: two entries start two server processes and
the agent sees every tool twice.
```

(The `TRUST_LOCAL_STDIO` rename is settled: microsoft/documentdb-mcp PR #83, merged 2026-05-27, replaced `ALLOW_UNAUTHENTICATED_STDIO`; `src/config.ts:225` reads only the new name and `src/server.ts:37` exits when stdio is used without it. The Learn page (ms.date 2026-05-18) predates the rename; the Learn fix is tracked separately.)

**1c. Step 1 "Confirm prerequisites", after the node/git block** (from K27):

````markdown
**Optional: `mongosh`** (MongoDB Shell). The MCP server does not need it. It is
useful for ad-hoc checks and for running the `.js` index and seed scripts that the
local-deployment skill uses. Install it with one of:

```bash
npm install -g mongosh            # any platform with Node.js (the MCP server already needs Node 20+)
brew install mongosh              # macOS (Homebrew)
# Windows: MSI installer from https://www.mongodb.com/try/download/shell
# Linux: MongoDB apt/yum repository, or download from https://www.mongodb.com/try/download/shell
```

Connect to Azure DocumentDB with the cluster's SRV string and its required options
(`retrywrites=false` is required; the Step 2 note says why). Leave the password out of
the string so that mongosh prompts for it:

```bash
mongosh "mongodb+srv://<user>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
```

For the local gateway container, use the row B URI from Step 2 (port 10260, TLS).
For more, see https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell.

If `mongosh` is not installed, do not treat that as a blocker. These DocumentDB MCP
server tools cover the same checks: `list_databases` (pass `db_name` to list that
database's collections), `list_indexes`, `find_documents`, `sample_documents`,
`aggregate`, `explain_operation`, `get_statistics` and, when
`ENABLE_MANAGEMENT_TOOLS=true` (the kit's `mcp.json` leaves it off), `current_ops`.
````

(The one-line pointer to row B is added in the merge so the mongosh and Step 2 guidance agree on the local endpoint. Review corrections already applied: there is no `list_collections` tool, `list_databases` with `db_name` returns collections per `src/tools/database-tools.ts`; the unverified winget id is removed in favor of the documented MSI; the template matches Learn. Added in the merge: `current_ops` is marked as management-gated so 1c agrees with the tool list in 1a.)

**1d. Step 2 table (lines 85-89): replace the table and add a note under it** (from K24):

```markdown
| Option | When to use | Example URI |
|---|---|---|
| **A. Azure DocumentDB** | Production / cloud dev | `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` |
| **B. Local DocumentDB (gateway container)** | Local dev with feature parity | `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` |
| **C. Custom MongoDB-compatible** | Atlas, self-hosted, third-party | `mongodb://<user>:<pw>@host:port/?tls=true` |
| **D. Plain MongoDB (not DocumentDB)** | Driver-only smoke tests | `mongodb://localhost:27017` |

Row A: copy the string from the portal (Cluster > Settings > Connection strings) or
`az documentdb mongocluster list-connection-strings`. On a single cluster the Self string
(`<cluster>.mongocluster.cosmos.azure.com`) and the Global read-write string
(`<cluster>.global.mongocluster.cosmos.azure.com`) are interchangeable; on a cluster with a
replica, use the Global read-write string for writes.

Row B is the local string from the Learn `development-loop` tutorial. The local DocumentDB
gateway listens on **10260**, not 27017, needs the username and password the container was
started with, and presents a self-signed certificate; `tlsAllowInvalidCertificates=true` is
only for that local certificate. Never put it in a cloud profile. SCRAM-SHA-256 is the only
mechanism the gateway offers, so `authMechanism` need not be set. A plain `mongo` image on
27017 has no `cosmosSearch` vector indexes (the local gateway has `vector-ivf` and
`vector-hnsw`; DiskANN and full-text search exist only on Azure) and does not reproduce the
gateway's TLS/SCRAM behavior. See the `documentdb-local-deployment` skill for the container
and docker-compose setup.

Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support
retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a
non-idempotent write twice. Handle transient write failures in application code with idempotent
operations (upserts, deterministic keys).
```

Row A now uses the full Azure portal connection-string format, including `retrywrites=false&maxIdleTimeMS=120000` (the existing row leaves those out), matching the mongosh template in 1c; the Self/Global sentence follows the Learn RBAC page ("In a single-cluster configuration, you can use either connection string indiscriminately"). `retrywrites=false` is required, not a sample choice (see Resolved), so the note under the table carries the kit's canonical rationale sentence. Row B is the canonical local URI: the Learn `development-loop` form, without `authMechanism` (not required; harmless if present, see Resolved). Whether the local string should also carry `retrywrites=false` is open question 1.

**1e. Step 4 template: keep the launch target, reconcile the entry spelling** (from K28). The template's `npx -y github:microsoft/documentdb-mcp` is the correct launch target and stays (it is what Learn and the upstream README prescribe; no npm package exists, see Resolved). Delete the sentence that the repository "may be private". Add under the template:

```markdown
The kit's `mcp.json` and Gemini extension register the same server under the key
`documentdb`. If that entry exists, do not add this one alongside it; if its `args`
still name the npm package `documentdb-mcp-server`, replace them with
`["-y", "github:microsoft/documentdb-mcp"]` (Step 0).
```

Whether the skill's template should also switch its key to `documentdb` to match `mcp.json` is a maintainer decision (open question 6); the launch target no longer depends on it.

**1f. Troubleshooting: add** (from K28):

```markdown
- **DocumentDB tools appear twice / two DocumentDB servers in the client**: the
  config has both a `documentdb` and a `DocumentDB` entry. Remove one (keep the
  one whose `CONNECTION_PROFILES` is filled in) and restart the client.
- **Server exits with "stdio transport is disabled when AUTH_REQUIRED=true"**: the
  entry was copied from a snippet that sets `ALLOW_UNAUTHENTICATED_STDIO` (the
  Learn MCP Toolkit page still uses that pre-release name). Set
  `TRUST_LOCAL_STDIO` to `"true"` instead; the current server reads only that name.
- **Tools are missing or behave unexpectedly and `args` contain
  `documentdb-mcp-server`**: that is a third-party npm package, not the Microsoft
  server. Replace the args with `["-y", "github:microsoft/documentdb-mcp"]`.
```

### 2. `AGENTS.md`

**2a.** In "Routing hints for agents", next to "Setting up the DocumentDB MCP server -> `documentdb-mcp-setup`" (around line 96), add (from K12):

```markdown
- **Querying / inspecting / explaining against a live cluster** -> the `documentdb` MCP server tools (see `documentdb-mcp-setup`). The Azure MCP Server has no DocumentDB data-plane tools; its Cosmos DB tools are for Azure Cosmos DB (NoSQL) accounts, not DocumentDB clusters.
```

**2b.** Lines 105 and 123: replace "bundles the DocumentDB MCP server (`documentdb-mcp-server` on npm)" and "runs via `npx -y documentdb-mcp-server` and refreshes on every agent restart (subject to npm cache)" with "bundles the DocumentDB MCP server (`microsoft/documentdb-mcp`, run from GitHub with `npx -y github:microsoft/documentdb-mcp`; there is no published npm package yet)" and "runs via `npx -y github:microsoft/documentdb-mcp` and refreshes on every agent restart (subject to the npx cache)". Make the same replacement in `CHANGELOG.md:115,121`, `GEMINI.md:3`, `docs/installation/updating.md:24` and `.codex-plugin/plugin.json:27`.

### 3. `README.md` (line 160)

Replace the export (from K24):

```bash
export DOCUMENTDB_CONNECTION_PROFILES='{"local":{"uriEnv":"DOCUMENTDB_LOCAL_URI"}}'
# local gateway: port 10260, TLS with a self-signed cert (dev only)
export DOCUMENTDB_LOCAL_URI='mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true'
```

### 4. `GEMINI.md` (line 27)

Same replacement as `README.md` line 160 (from K24).

### 5. `docs/installation/macos.md` (line 21)

Replace with two bullets (from K24):

```markdown
- **Local DocumentDB (gateway container):** `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`
- **Plain MongoDB / Atlas / self-hosted:** your standard MongoDB URI (e.g. `mongodb://localhost:27017`).
```

### 6. `install.sh`

**6a. Printed strings, lines 8, 522, 527** (from K24; the installer only prints these, no code path changes):

```bash
#   curl -fsSL .../install.sh | bash -s -- --uri "mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true" --yes
...
    err "for local DocumentDB: --uri \"mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true\""
...
  log "  • Local DocumentDB: mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true"
  log "  • Plain MongoDB:    mongodb://localhost:27017"
```

**6b. Optional (same PR or a follow-up): stop writing a duplicate entry** (from K28):

- In `merge_mcp_entry()`, before assigning `node[p]["DocumentDB"]`, scan `node[p]` for an entry whose `args` reference `github:microsoft/documentdb-mcp`, `documentdb-mcp/dist/main.js` or the bare npm name `documentdb-mcp-server`. If one exists, update it in place (replacing an npm-name launch target with the GitHub one) and keep its key instead of adding a sibling. Apply the same rule in the `jq` branch.
- Make `remove_mcp_entry()` delete entries by that same match, not only by the literal `DocumentDB` key.

### 7. `install.ps1` (lines 46, 491)

From K24:

```powershell
    .\install.ps1 -Uri "mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true" -Yes
...
    Write-Host "  - Local DocumentDB: mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true"
    Write-Host "  - Plain MongoDB:    mongodb://localhost:27017"
```

### 8. `skills/local-deployment/local-connection-config.md`

Immediately before the first `mongosh localhost:10260` example (from K27):

```markdown
> `mongosh` is optional. Install it with `npm install -g mongosh` (or Homebrew, or the MongoDB download; see
> the mcp-setup skill, Step 1). Without it, use the DocumentDB MCP server tools or the driver examples below.
```

### 9. `skills/query-optimizer/SKILL.md`

In section "Local mongosh Commands (No MCP Required)", after the first paragraph (from K27); the skill keeps its MCP-first order:

```markdown
**If mongosh is not installed** and the DocumentDB MCP server is configured, use the MCP
equivalents instead of installing the shell: `list_indexes` for `getIndexes()`,
`explain_operation` for `.explain("executionStats")`, `find_documents` (limit 1) or
`sample_documents` for `findOne()`, `list_databases` with `db_name` for `show collections`,
`get_statistics` (scope `collection` / `index`) for `stats()` / `$indexStats`, and
`current_ops` for `db.currentOp()` (needs `ENABLE_MANAGEMENT_TOOLS=true`). Install mongosh only when the user asks for an
interactive shell (`npm install -g mongosh`).
```

### 10. `mcp.json` (lines 4-5) and `gemini-extension.json` (lines 7-8)

Change `"args": ["-y", "documentdb-mcp-server"]` to `"args": ["-y", "github:microsoft/documentdb-mcp"]` in both manifests, matching the skill's Step 4 template, the Learn MCP Toolkit page and the upstream README. Reason: Microsoft has not published an npm package, and since 2026-11-24 the unscoped name resolves to a third-party package that reads `CONNECTION_PROFILES`. This is security-relevant and should land even if the rest of the PR is still under review. The key stays `documentdb` for now (open question 6). When Microsoft publishes a scoped package (microsoft/documentdb-mcp#49 proposes `@azure/documentdb-mcp-server`; open question 5), switch to it in one place and update Step 0 and Step 4 together.

### Acceptance checks

- `grep -rn 27017` matches only lines explicitly labeled plain MongoDB.
- `grep -rn "documentdb-mcp-server"` matches no launch target and no "on npm" claim; the only remaining mentions tell the reader to replace it.
- `skills/mcp-setup/SKILL.md` names `documentdb` as the data-plane server, has a Step 0, lists mongosh as optional with the MCP fallback, and its Step 4 template launches `github:microsoft/documentdb-mcp` and agrees with (or explicitly defers to) the `mcp.json` entry.

### Out of scope / follow-ups

- `microsoft/documentdb-mcp` has the same 27017 pattern in its `README.md` (lines 73, 95, 115, 231, plus the VS Code install badge on line 1) and `.env.example:36`; the README never mentions the DocumentDB local image. Needs a separate issue there; no draft exists yet.
- `microsoft/documentdb-mcp` `package.json` still declares the unscoped name `documentdb-mcp-server` with no `repository` or `publishConfig`, while that name is now taken on npm by a third party (microsoft/documentdb-mcp#49 already proposes `@azure/documentdb-mcp-server`). Raise the squat with the repository owners in the kit PR; the rename is theirs.
- The Learn MCP Toolkit page (https://learn.microsoft.com/azure/documentdb/mcp-toolkit) still uses `ALLOW_UNAUTHENTICATED_STDIO` in its quickstart configurations and configuration table and `mongodb://localhost:27017` as its local example; both are Learn fixes, not kit changes.
- A note to microsoft/mcp pointing the Azure MCP Server docs at the dedicated server is a possible follow-up; no draft targets it yet.
- Filing K25 adds kit-wide "am I installed?" self-identification (draft 057) and may also edit `skills/mcp-setup/SKILL.md`. Land the two PRs one after the other so they do not conflict in the same lines.

## Evidence

Run folders from the experiment (single run):

- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json`: mongosh in `accelerators_missed`; the agent noted MCP tools cover the same checks
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json`: mongosh recorded only as a gap
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: Q13 wrong; confused with Cosmos DB for MongoDB RU
- `runs/06-collateral-management-store/20261124-200922/02-readiness.json`: Q13 partly_wrong; "no dedicated server"
- `runs/09-lead-scoring-agent/20261124-204408/` (`02-readiness.json`, `events.jsonl`): cold answer `mongo:7` on 27017, and the run loaded `documentdb-mcp-setup`
- `runs/13-chronic-disease-risk-predictor/20261124-194916/app/tests/test_seed.py`: shipped test defaults to `localhost:27017` (supporting, outside the 5 counted)
- `runs/20-store-locator-with-geospatial-search/20261124-185729/app/.env.example`: shipped URI in RU-API style on `:27017` (supporting, outside the 5 counted)
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json`: `accelerators_missed[1]`; server present but kit entry reported missing
- `runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json`: existing entry with unresolved `CONNECTION_PROFILES`, agent pointed the user to this skill (also a Q13 wrong answer confused with Cosmos DB for NoSQL; second run of sample 01, not counted separately)

Further run folders carried over from the member filings:

- mongosh (`accelerators_missed` in `02-readiness.json`): `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/`, `runs/16-atm-network-status-monitor/20261124-202405/`, `runs/11-correspondent-banking-risk-screener/20261124-201541/`
- MCP server choice (Q13 in `02-readiness.json`): `runs/07-customer-review-sentiment-pipeline/20261125-054042/` (partly_wrong; confused with Cosmos DB for MongoDB RU), `runs/07-mortgage-application-multi-agent/20261124-201025/`, `runs/08-interest-rate-scenario-modeler/20261124-201113/`, `runs/12-invoice-matching-reconciliation/20261124-191603/` (each partly_wrong); `runs/11-market-news-sentiment-orchestration/20261125-062725/` (wrong; grounded only from the known-accelerators list; supporting context, not counted in the 6)
- 27017 prior: `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json` (cold answer `mongo:7` on 27017), `runs/04-regulatory-reporting-orchestration/20261124-200545/02-readiness.json` (same), `runs/05-churn-prediction-pipeline/20261124-203754/02-readiness.json` (same; later grounded on the Learn `development-loop` page, 10260), `runs/12-cross-border-payment-audit-trail/20261124-201744/app/.env.example` (shipped URI uses `:27017`; supporting, outside the 5 counted)
- Existing entry: `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-inventory.json` (the `documentdb` server and all kit skills installed), `runs/retail-semantic-search/20261115-153948/02-readiness.json` (report says to repair the entry with this skill, which has no repair path), `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` (correct "already installed, no action" outcome)

Documentation and source evidence (via `findings/phase4/DECISIONS.md`, topics 12 and 13, researched 2026-11-25):

- Local gateway endpoint: https://learn.microsoft.com/en-us/azure/documentdb/development-loop (canonical local string); https://documentdb.io/docs/documentdb-local/ (port, credentials required, `--tlsMode allowTLS` default, self-signed certificate); engine `pg_documentdb_gw/documentdb_gateway_core/src/processor/ismaster.rs:118,193` and `src/auth/manager.rs:159-166` (SCRAM-SHA-256 only); `documentdb-local/scripts/documentdb_local_settings.sh:30,44`
- Local feature parity: engine `pg_documentdb/src/vector/vector_index_kind_impl.c:109-133` (only `vector-ivf` and `vector-hnsw`); `pg_documentdb_gw/documentdb_gateway_core/src/postgres/data_client.rs:528-548` (`createSearchIndexes` not supported locally); https://learn.microsoft.com/en-us/azure/documentdb/limitations
- npm status: https://learn.microsoft.com/en-us/azure/documentdb/mcp-toolkit (Limitations: "No published npm package yet"); https://github.com/microsoft/documentdb-mcp (README line 21); https://github.com/microsoft/documentdb-mcp/issues/49 and /issues/48; https://github.com/Azure/documentdb-agent-kit/issues/20; https://registry.npmjs.org/documentdb-mcp-server (observed 2026-11-25: version 0.1.0 published 2026-11-24, bin `documentdb-mcp-local`, no repository field); https://registry.npmjs.org/@azure%2Fdocumentdb-mcp-server and https://registry.npmjs.org/@microsoft%2Fdocumentdb-mcp-server (both 404 on 2026-11-25)
- Azure MCP Server: https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/ (no `documentdb` or `mongocluster` namespace); https://github.com/microsoft/mcp/issues/774 (closed 2026-04-27)
- Product name: https://learn.microsoft.com/en-us/azure/documentdb/mcp-toolkit (title and first sentence); https://devblogs.microsoft.com/documentdb/azure-documentdb-mcp-toolkit/ (supporting); upstream README H1 "DocumentDB MCP Server"
- `TRUST_LOCAL_STDIO`: https://github.com/microsoft/documentdb-mcp/pull/83 (merged 2026-05-27); upstream `src/config.ts:225`, `src/server.ts:37`
- Self vs Global host: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control ("In a single-cluster configuration, you can use either connection string indiscriminately")

Partly to blame for the duplicate-entry advice: the experiment harness lists the toolkit as "Entry `documentdb` in `mcp.json`", so its readiness reports phrase the ask that way. The duplicate-entry risk itself comes from the kit's mismatched spellings.

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

Canonical local URI and `authMechanism`: settled 2026-11-25 (DECISIONS.md, topic 12). The canonical local string is the Learn `development-loop` form, `mongodb://<admin-username>:<admin-password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`; `authMechanism=SCRAM-SHA-256` is not required (the gateway advertises and registers only SCRAM-SHA-256, so negotiation lands on it) and is harmless if present; the image default `--tlsMode allowTLS` accepts plain and TLS connections, and a username and password are mandatory. Sources: engine `pg_documentdb_gw/documentdb_gateway_core/src/processor/ismaster.rs:118,193` and `src/auth/manager.rs:159-166`; https://www.mongodb.com/docs/manual/reference/connection-string-options/; https://learn.microsoft.com/en-us/azure/documentdb/development-loop; https://github.com/documentdb/documentdb/blob/main/README.md; https://documentdb.io/docs/documentdb-local/; `documentdb-local/scripts/documentdb_local_settings.sh:44`.

npm distribution and launch target: settled 2026-11-25 (DECISIONS.md, topic 13). Microsoft has not published `documentdb-mcp-server` (or any scoped name) on npm; Learn and the upstream README prescribe `npx -y github:microsoft/documentdb-mcp` or a source build, and since 2026-11-24 the unscoped name is a third-party package of unknown provenance, so the kit's `mcp.json`/`gemini-extension.json` must switch to the GitHub launch target and the "on npm" claims in `AGENTS.md:105,123` and elsewhere are wrong. Sources: https://learn.microsoft.com/en-us/azure/documentdb/mcp-toolkit; https://github.com/microsoft/documentdb-mcp (README.md line 21, commit 2026-09-16); https://github.com/microsoft/documentdb-mcp/issues/49; https://github.com/microsoft/documentdb-mcp/issues/48; https://github.com/microsoft/documentdb-mcp/pull/34; https://github.com/Azure/documentdb-agent-kit/issues/20; https://registry.npmjs.org/documentdb-mcp-server (observed 2026-11-25).

Azure MCP Server today: settled 2026-11-25 (DECISIONS.md, topic 13). The Azure MCP Server has no `documentdb` or `mongocluster` namespace; its Databases namespaces are `cosmos`, `mysql`, `postgres`, `redis` and `sql`, and microsoft/mcp#774 was closed 2026-04-27 as blocked. Sources: https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/ (ms.date 2026-08-11, updated 2026-10-16); https://github.com/microsoft/mcp/issues/774.

Product name: settled 2026-11-25 (DECISIONS.md, topic 13). "Azure DocumentDB MCP Toolkit" is the Microsoft product name (Learn page title "MCP Toolkit - Azure DocumentDB"; the repository calls itself "DocumentDB MCP Server"; both mark it public preview), so the recommended phrasing is "the Azure DocumentDB MCP Toolkit (the microsoft/documentdb-mcp server)". Sources: https://learn.microsoft.com/en-us/azure/documentdb/mcp-toolkit; https://github.com/microsoft/documentdb-mcp (README.md H1; package.json); https://devblogs.microsoft.com/documentdb/azure-documentdb-mcp-toolkit/ (supporting).

## Open questions

1. **`retrywrites=false` in the local string.** The canonical local URI is settled (see Resolved) and, like the Learn `development-loop` string, omits `retrywrites=false`. Issue documentdb/documentdb#767 (gateway passes a NULL transaction id, so retried writes are not de-duplicated) is filed against the open-source gateway that the local image ships, so the same risk plausibly applies locally, but no source states a local requirement. Should row B and the kit's local exports also carry `retrywrites=false`? [needs SME confirmation]
2. **Sample count.** Before these figures are quoted externally, should they come from a clean re-run? The mongosh count (16) comes from extracted finding ids; a recount over all run folders, including runs finished after extraction, finds mongosh flagged in 19 samples, and the harness's `mongosh --version` probe inflates the number. The fifth K24 sample (a sample 06) is not named in its draft, so the merged 27 assumes it does not overlap another theme. (Project decision, not an SME question.)
3. **Node floor for mongosh.** The npm `mongosh` package lists `engines.node >=16.15.0`. Does the kit need to state that floor, or is the MCP server's Node 20+ requirement enough? Maintainer decision; DECISIONS.md's general position on version floors (topic 4, item 4.11) is to state them only where a feature is gated.
4. **Azure MCP Server roadmap.** Does the Azure MCP Server team plan a DocumentDB namespace, and when? The only public artefact, microsoft/mcp#774, was closed 2026-04-27 as "blocked due to AOT issues, team investigating alternative approach to ship"; no roadmap item, PR or Learn page has appeared since, and the MCP Toolkit Learn page does not mention the Azure MCP Server. Until answered, 1a describes the two as separate and does not promise an `azmcp` `documentdb` namespace; if one is planned, the "no DocumentDB tools" wording needs a date or softer phrasing. [needs SME confirmation]
5. **Official npm name and publisher.** Which npm name and publisher will the official package use (`@azure/documentdb-mcp-server` per microsoft/documentdb-mcp#49, or `@microsoft/...`), and will the team claim or report the unscoped `documentdb-mcp-server` name re-published by a third party on 2026-11-24? Both scoped names returned 404 on 2026-11-25. Until a scoped package ships, every kit config uses `npx -y github:microsoft/documentdb-mcp` (section 10) and no filing states an npm package name as fact. [needs SME confirmation]
6. **Canonical server key.** With the launch target settled, which key is canonical, `documentdb` (the kit's `mcp.json` and Gemini manifest) or `DocumentDB` (the skill's Step 4 template and `install.sh`)? This decides whether 1e also changes the template's key and which key `install.sh` writes when no entry exists. Maintainer decision.
7. **Tool list in the skill: inline or link.** The read / write / management split in 1a (18 tools) matches the Learn MCP Toolkit page and `documentdb-mcp/tool_list.md`. Should the skill carry the list inline, or link to `tool_list.md` so it cannot drift? Maintainer decision.

## Source drafts

- 060-mongosh-is-never-installed-kit-setup-and-connection-skills-s.md
- 132-believes-the-general-azure-mcp-server-s-cosmos-db-tools-cove.md
- 133-believes-no-dedicated-data-plane-mcp-server-exists-for-azure.md
- 031-agent-kit-itself-reinforces-the-27017-prior-mcp-setup-skill-.md
- 064-mcp-setup-skill-should-recognise-an-existing-documentdb-serv.md

## Merged from

- K27: Document mongosh as an optional tool with an MCP-tool fallback (P1, 16 samples)
- K12: mcp-setup skill: name the documentdb MCP server as the data-plane server and say what the Azure MCP Server covers (P2, 6 samples)
- K24: mcp-setup skill, README and installers: stop presenting a localhost URI as the default (P1, 5 samples)
- K28: mcp-setup: add an "already configured?" check and reconcile the server-entry spelling (P3, 1 sample)
