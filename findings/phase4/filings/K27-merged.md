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
open_questions: 8
---

# mcp-setup skill: name the documentdb MCP server as the data-plane server, stop defaulting to a localhost URI, add an "already configured?" check, and document mongosh as optional with an MCP-tool fallback

One documentation PR centred on `skills/mcp-setup/SKILL.md`. It also touches `AGENTS.md`, `README.md`, `GEMINI.md`, `docs/installation/macos.md`, `install.sh`, `install.ps1`, `skills/local-deployment/local-connection-config.md` and `skills/query-optimizer/SKILL.md`. No runtime behavior changes, except an optional de-duplication fix in `install.sh`.

## What happens today

`skills/mcp-setup/SKILL.md` is the skill an agent loads to wire up and use the `documentdb` MCP server (`microsoft/documentdb-mcp`). It has four gaps, each of which pushes agents toward a wrong prior.

1. **It never says which MCP server does DocumentDB data-plane work.** Neither the skill nor `AGENTS.md` says that `documentdb` is the server for queries, aggregate, explain, indexes, statistics and sample documents. Neither mentions the general Azure MCP Server, whose `cosmos` tools target Azure Cosmos DB accounts, databases and containers (NoSQL API) and cannot reach a `Microsoft.DocumentDB/mongoClusters` cluster. The skill only says to "list available DocumentDB tools"; it does not list them or their capability gates. `AGENTS.md` routes "Setting up the DocumentDB MCP server" to `documentdb-mcp-setup` but has no routing hint for querying or explaining against a live cluster. A grep of `skills/`, `knowledge-base/`, `AGENTS.md`, `README.md` and `mcp.json` for "Azure MCP", "azmcp", "data plane" and "control plane" finds nothing about server choice.

2. **It presents a localhost URI on 27017 without TLS as the local default.** Nine lines in six files give `mongodb://localhost:27017` as the local DocumentDB connection string:

   | File | Line(s) | Current text |
   |---|---|---|
   | `skills/mcp-setup/SKILL.md` | 88 | Step 2 table, row **B. Local MongoDB / DocumentDB**: `mongodb://localhost:27017` |
   | `README.md` | 160 | `export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'` |
   | `GEMINI.md` | 27 | same export |
   | `docs/installation/macos.md` | 21 | `**Local DocumentDB / MongoDB:** mongodb://localhost:27017` |
   | `install.sh` | 8, 522, 527 | usage comment, `for local dev:` hint, `Local:` example |
   | `install.ps1` | 46, 491 | `.EXAMPLE` block, `Local:` example |

   The local DocumentDB gateway container (`ghcr.io/documentdb/documentdb/documentdb-local`) listens on **10260** and requires **TLS** (self-signed certificate) and **SCRAM-SHA-256**. The kit says so correctly in `skills/local-deployment/` (`SKILL.md:11`, `local-env-driven-config.md:61`) and in the README Quickstart (`-p 10260:10260` at `README.md:49`), so the README starts the container on 10260 and 110 lines later tells the MCP server to connect on 27017. An MCP profile pointed at 27017 without TLS cannot reach that container. The Learn tutorial `azure/documentdb/development-loop` uses the same 10260 + TLS endpoint.

3. **It has no "already configured?" check, and the kit spells the server entry three ways.** Step 4 says to add the `DocumentDB` entry inside an existing `mcpServers` object but never says to check whether a DocumentDB entry already exists, or how to repair a broken one.

   | Where | Server key | Launch target |
   |---|---|---|
   | `mcp.json` (root), `gemini-extension.json` | `documentdb` | `npx -y documentdb-mcp-server` |
   | `skills/mcp-setup/SKILL.md` Step 4 | `DocumentDB` | `npx -y github:microsoft/documentdb-mcp` |
   | `install.sh` (`MCP_ENTRY="DocumentDB"`) | `DocumentDB` | `node <MCP_DIR>/dist/main.js` (local clone built by the installer) |

   All three start the same server (`package.json` in microsoft/documentdb-mcp names the package `documentdb-mcp-server`, `bin` points to `dist/main.js`). `install.sh` `merge_mcp_entry()` always assigns `node[p]["DocumentDB"]` (and the `jq` path always sets `.[top_key]["DocumentDB"]`), so if the client already has the kit's `documentdb` entry the installer adds a second one: two processes, two `CONNECTION_PROFILES`, every tool listed twice. `remove_mcp_entry()` removes only the literal `DocumentDB` key.

4. **It (and other skills) assume `mongosh` without introducing it.** Step 1 "Confirm prerequisites" lists only `node --version` and `git --version`. `skills/query-optimizer/SKILL.md` (lines 33-51) pairs every MCP tool with a mongosh equivalent; its section "Local mongosh Commands (No MCP Required)" (line 69) and "If MCP is not available, use mongosh directly" (line 227) treat mongosh as the fallback when MCP is missing, but nothing covers the more common case of MCP configured and mongosh absent. `skills/local-deployment/local-connection-config.md` (lines 22, 25, 44) uses `mongosh localhost:10260 ...` for its canonical examples; `local-prod-parity.md:58`, `local-sample-data-management.md:14,32`, `local-ports-and-bindings.md:11` and `local-choose-deployment-method.md:13,41` also reference mongosh with no install guidance. The Learn page "Connect using MongoDB Shell" (https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell) is never linked.

## Why it matters

In one run of an agent-readiness experiment, gpt-5-mini with this kit's skills and the DocumentDB, Azure and Learn MCP servers ran a cold quiz, a readiness check and a build for each of 100 Azure DocumentDB sample prompts. Across the four themes, **27 distinct samples of 100** produced a finding (figure from one run; sample 07-customer-review-sentiment-pipeline appears in both the mongosh and the MCP-server themes and is counted once):

- **mongosh missing (16 samples, from K27).** The readiness check listed mongosh as a missed accelerator ("missing from PATH; installing mongosh speeds manual verification"). Three samples worked out that the DocumentDB MCP server offers the same operations; 13 recorded it only as a gap. None of the 16 builds was blocked: the build agents never ran mongosh, and `list_indexes`, `find_documents` and `explain_operation` did the verification. The harness's own `mongosh --version` inventory probe makes the gap more visible, so the count overstates impact. This is a cheap consistency fix: skills should say what they assume and send the agent to the MCP tools, instead of the agent spending a turn deciding or recommending an install the user did not ask for.
- **Wrong MCP server for the data plane (6 samples, from K12).** Asked cold "Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it?":
  - 2 samples said the general Azure MCP Server or its Cosmos DB tools cover DocumentDB's data plane, confusing Azure DocumentDB with the RU-based Azure Cosmos DB for MongoDB API (once with Azure Cosmos DB for NoSQL); the prior comes from the former name "Azure Cosmos DB for MongoDB vCore".
  - 4 samples said no DocumentDB-specific MCP server exists, so the Azure MCP Server or plain drivers are the way to inspect data.

  After grounding the model got it right, but only from the live tool inventory or a known-accelerators list, never from the kit. An agent that follows its prior either calls `cosmos` tools that cannot reach the cluster or skips `explain_operation`, `sample_documents`, `aggregate` and `get_statistics` and writes ad-hoc driver scripts, making skipped index and query-plan checks more likely. Builds still called `documentdb_*` tools once exposed, so impact was small; the risk is in clients where the agent picks a server from what it has read.
- **27017 localhost prior (5 samples, from K24).** Asked cold how to run the database locally, the agent typically answered "`mongo:7` on 27017". The kit should correct that prior, but `mcp-setup` is often loaded before `local-deployment` and its row B confirms it. Generated apps then wired `.env.example`, seed scripts and integration tests to a stock `mongo` image on 27017 (other runs outside the five show the same: a test defaulting to `localhost:27017`, an `.env.example` hard-coding `:27017`). Against plain MongoDB, apps lose parity for `cosmosSearch` vector indexes (vector-ivf, vector-hnsw, vector-diskann), text search and TLS/SCRAM behavior, so tests pass or fail for the wrong reasons.
- **Duplicate MCP entry advice (1 sample, from K28).** The `documentdb` server was present and working (18 tools; the build later called `list_databases`, `create_index`, `list_indexes`, `find_documents`), yet the readiness report listed the kit's MCP entry as missing and suggested installing the "GitHub repo variant" as well. Following that advice with the skill as written produces a duplicate entry. In two other samples an existing entry was broken (one failed to start; one had unresolved `CONNECTION_PROFILES`) and the agent sent the user to this skill, which covers only fresh installs, so it improvised repair steps. In another sample the agent correctly answered "installed, no action required": when the agent thinks to check, the check is easy.

## Proposed change

Files are listed once each; edits within a file are in document order.

### 1. `skills/mcp-setup/SKILL.md`

**1a. New section after the intro and before `## Safety: never receive credentials in chat`** (from K12):

```markdown
## Which MCP server do I use?

- **Data plane of a live cluster: use `documentdb`** (this server, `microsoft/documentdb-mcp`,
  the "Azure DocumentDB MCP Toolkit" on Microsoft Learn). It is the MCP server with
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

Reviewer corrections already applied: the Azure MCP Server is not described as DocumentDB's control plane; `create_index` and `current_ops` are management-gated, not default; no npm package name is stated as fact in this section.

**1b. New section before "Step 1: Confirm prerequisites"** (from K28):

```markdown
## Step 0: Is it already configured?

Before adding anything, open the client's MCP config (table in Step 4) and look
for an existing entry under `mcpServers` / `mcp.servers` whose `args` contain
`documentdb-mcp-server`, `github:microsoft/documentdb-mcp`, or a path ending in
`documentdb-mcp/dist/main.js` (the bundled installer's local build). The key may
be `documentdb` (the kit's `mcp.json` / Gemini manifest) or `DocumentDB` (this
skill and the bundled installer). All of these launch the same server; only one
entry should exist.

- **Entry present and the client lists DocumentDB tools** → nothing to add.
  Skip to Step 5 to verify (`list_databases` with the profile name defined in
  that entry's `CONNECTION_PROFILES`).
- **Entry present but the server does not start or has no tools** → repair it
  in place rather than adding a second one. Check, in order: `TRANSPORT` is
  `stdio`; `AUTH_REQUIRED` is `"false"`; `TRUST_LOCAL_STDIO` is `"true"`
  (older builds: `ALLOW_UNAUTHENTICATED_STDIO`); `CONNECTION_PROFILES` is a
  JSON *string* and any `${VAR}` it references is set in the environment the
  client launches with. Then continue at Troubleshooting.
- **No entry** → continue with Step 1.

Never add a second DocumentDB entry: two entries start two server processes and
the agent sees every tool twice.
```

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

Connect to Azure DocumentDB with the cluster's SRV string and its required options.
Leave the password out of the string so that mongosh prompts for it:

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

The local DocumentDB gateway listens on **10260**, not 27017. It uses a self-signed
TLS certificate and SCRAM-SHA-256. `tlsAllowInvalidCertificates=true` is only for that
local certificate. Never put it in a cloud profile. A plain `mongo` image on 27017
does not reproduce DocumentDB vector or text indexes, or its TLS/SCRAM behavior. See
the `documentdb-local-deployment` skill for the container and docker-compose setup.
```

Row A now uses the full Azure portal connection-string format, including `retrywrites=false&maxIdleTimeMS=120000` (the existing row leaves those out), matching the mongosh template in 1c.

**1e. Step 4 template: reconcile the server-entry spelling** (from K28). Either

- **Option A:** change the template to match the root `mcp.json` (key `"documentdb"`, args `["-y", "documentdb-mcp-server"]`), or
- **Option B:** keep the template and add this sentence under it:

```markdown
The kit's `mcp.json` and Gemini extension register the same server as
`documentdb` (`npx -y documentdb-mcp-server`). If that entry exists, do not add
this one alongside it.
```

The choice depends on open question 6.

**1f. Troubleshooting: add** (from K28):

```markdown
- **DocumentDB tools appear twice / two DocumentDB servers in the client**: the
  config has both a `documentdb` and a `DocumentDB` entry. Remove one (keep the
  one whose `CONNECTION_PROFILES` is filled in) and restart the client.
```

### 2. `AGENTS.md`

In "Routing hints for agents", next to "Setting up the DocumentDB MCP server -> `documentdb-mcp-setup`" (around line 96), add (from K12):

```markdown
- **Querying / inspecting / explaining against a live cluster** -> the `documentdb` MCP server tools (see `documentdb-mcp-setup`). The Azure MCP Server has no DocumentDB data-plane tools; its Cosmos DB tools are for Azure Cosmos DB (NoSQL) accounts, not DocumentDB clusters.
```

(Line 105, which says the plugin bundles "`documentdb-mcp-server` on npm", is left unchanged pending open question 6.)

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

- In `merge_mcp_entry()`, before assigning `node[p]["DocumentDB"]`, scan `node[p]` for an entry whose `args` reference `documentdb-mcp-server`, `github:microsoft/documentdb-mcp` or `documentdb-mcp/dist/main.js`. If one exists, update it in place and keep its key instead of adding a sibling. Apply the same rule in the `jq` branch.
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

### Not changed

- `mcp.json`: referenced by Step 0 and the Step 4 Option A template; no edit in this PR. Whether its `npx -y documentdb-mcp-server` launch target stays depends on open question 6.

### Acceptance checks

- `grep -rn 27017` matches only lines explicitly labeled plain MongoDB.
- `skills/mcp-setup/SKILL.md` names `documentdb` as the data-plane server, has a Step 0, lists mongosh as optional with the MCP fallback, and its Step 4 template agrees with (or explicitly defers to) the `mcp.json` entry.

### Out of scope / follow-ups

- `microsoft/documentdb-mcp` has the same 27017 pattern in its `README.md` (lines 73, 95, 115, 231, plus the VS Code install badge on line 1) and `.env.example:36`. Needs a separate issue there; no draft exists yet.
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
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json`: `accelerators_missed[1]`; server present but kit entry reported missing
- `runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json`: existing entry with unresolved `CONNECTION_PROFILES`, agent pointed the user to this skill (also a Q13 wrong answer confused with Cosmos DB for NoSQL; second run of sample 01, not counted separately)

Further run folders carried over from the member filings:

- mongosh (`accelerators_missed` in `02-readiness.json`): `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/`, `runs/16-atm-network-status-monitor/20261124-202405/`, `runs/11-correspondent-banking-risk-screener/20261124-201541/`
- MCP server choice (Q13 in `02-readiness.json`): `runs/07-customer-review-sentiment-pipeline/20261125-054042/` (partly_wrong; confused with Cosmos DB for MongoDB RU), `runs/07-mortgage-application-multi-agent/20261124-201025/`, `runs/08-interest-rate-scenario-modeler/20261124-201113/`, `runs/12-invoice-matching-reconciliation/20261124-191603/` (each partly_wrong); `runs/11-market-news-sentiment-orchestration/20261125-062725/` (wrong; grounded only from the known-accelerators list; supporting context, not counted in the 6)
- 27017 prior: `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json` (cold answer `mongo:7` on 27017), `runs/04-regulatory-reporting-orchestration/20261124-200545/02-readiness.json` (same), `runs/05-churn-prediction-pipeline/20261124-203754/02-readiness.json` (same; later grounded on the Learn `development-loop` page, 10260), `runs/12-cross-border-payment-audit-trail/20261124-201744/app/.env.example` (shipped URI uses `:27017`; supporting, outside the 5 counted)
- Existing entry: `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-inventory.json` (the `documentdb` server and all kit skills installed), `runs/retail-semantic-search/20261115-153948/02-readiness.json` (report says to repair the entry with this skill, which has no repair path), `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` (correct "already installed, no action" outcome)

Partly to blame for the duplicate-entry advice: the experiment harness lists the toolkit as "Entry `documentdb` in `mcp.json`", so its readiness reports phrase the ask that way. The duplicate-entry risk itself comes from the kit's mismatched spellings.

## Open questions

1. **`retrywrites=false`.** Row A and the mongosh template use `retrywrites=false`, as the Learn / Azure portal connection string does. Source drafts disagree on what it means: one position is that Learn does not say retryable writes are unsupported, so the option is a recommendation; the other is that retryable writes are unsupported and cause write errors if enabled. This PR adds no rationale. Can engineering confirm the actual behavior, and whether the local gateway URI (row B and the exports) also needs `retrywrites=false`? [needs SME confirmation]
2. **Canonical local URI.** Should the local gateway URI set `authMechanism=SCRAM-SHA-256` explicitly? `local-env-driven-config.md:61` sets it; the Learn `development-loop` tutorial and the strings above do not. Please name one canonical local URI so every file in the kit uses it. [needs SME confirmation]
3. **Sample count.** Before these figures are quoted externally, should they come from a clean re-run? The mongosh count (16) comes from extracted finding ids; a recount over all run folders, including runs finished after extraction, finds mongosh flagged in 19 samples, and the harness's `mongosh --version` probe inflates the number. The fifth K24 sample (a sample 06) is not named in its draft, so the merged 27 assumes it does not overlap another theme. [needs SME confirmation]
4. **Node floor for mongosh.** The npm `mongosh` package lists `engines.node >=16.15.0`. Does the kit need to state that floor, or is the MCP server's Node 20+ requirement enough? [needs SME confirmation]
5. **Azure MCP Server roadmap.** The Azure MCP Server has no Azure DocumentDB / `mongoClusters` namespace today (per its Learn tools page, updated 2026-10). Is one planned? If so, the "no DocumentDB tools" wording needs a date or softer phrasing. [needs SME confirmation]
6. **Distribution and canonical entry.** The Learn MCP Toolkit page says there is no published npm package yet, while the kit's `mcp.json` runs `npx -y documentdb-mcp-server` and `AGENTS.md` line 105 says the plugin bundles "`documentdb-mcp-server` on npm". Which is current? [needs SME confirmation] The answer feeds a maintainer decision: which key and launch target are canonical (`documentdb` with the npm package, or `DocumentDB` with the GitHub source or a local build), which decides Option A vs B in Step 4 and which key `install.sh` writes when no entry exists.
7. **Tool list stability.** The read / write / management split and tool names come from `documentdb-mcp/tool_list.md` and its README. Are they stable enough to list in a skill, or should the skill link to `tool_list.md` instead? [needs SME confirmation]
8. **Product name.** Is "Azure DocumentDB MCP Toolkit" the canonical product name to use alongside `microsoft/documentdb-mcp`? [needs SME confirmation]

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
