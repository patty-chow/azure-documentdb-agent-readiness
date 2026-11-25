---
id: K27
title: "Document mongosh as an optional tool with an MCP-tool fallback"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 16
member_drafts:
  - 060-mongosh-is-never-installed-kit-setup-and-connection-skills-s.md
open_questions: 3
---

# Document mongosh as an optional tool with an MCP-tool fallback

## What happens today

Several kit skills assume `mongosh` is on PATH. No skill introduces it, says how to install it, or says what to do when it is missing.

- `skills/query-optimizer/SKILL.md` (lines 33-51) pairs every MCP tool with a mongosh equivalent (`getIndexes()`, `.explain("executionStats")`, `db.currentOp()`). The section "Local mongosh Commands (No MCP Required)" (line 69) and the line "If MCP is not available, use mongosh directly" (line 227) treat mongosh as the fallback when MCP is missing. Nothing covers the more common case: the MCP server is configured and mongosh is not installed.
- `skills/local-deployment/local-connection-config.md` uses `mongosh localhost:10260 ...` for its canonical examples. `local-prod-parity.md` (line 58), `local-sample-data-management.md`, `local-ports-and-bindings.md` and `local-choose-deployment-method.md` also reference mongosh with no install guidance.
- `skills/mcp-setup/SKILL.md`, Step 1 "Confirm prerequisites", lists only `node --version` and `git --version`.

An agent that reads these skills learns that mongosh is expected, finds it absent, and has to decide on its own whether that matters. The Learn page "Connect using MongoDB Shell" (https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell) already covers the connection, but the kit never links to it.

## Why it matters

In an agent-readiness experiment, an agent (gpt-5-mini with the kit skills and the DocumentDB, Azure and Learn MCP servers) ran a readiness check and then a build for each of 100 Azure DocumentDB sample prompts. In 16 of the 100 samples, the readiness check listed mongosh as a missed accelerator ("missing from PATH; installing mongosh speeds manual verification"). Three samples worked out that the DocumentDB MCP server offers the same operations. The other 13 recorded it only as a gap. Counts come from a single experiment run.

On scope: none of the 16 builds was blocked. The build agents never tried to run mongosh, and the MCP tools `list_indexes`, `find_documents` and `explain_operation` did the verification work. The experiment harness also runs `mongosh --version` during its environment inventory, which makes the readiness agent more likely to notice that the shell is missing. So the count overstates the impact. This is a cheap consistency fix, not a correctness bug. The skills should say what they assume and send the agent to the MCP tools when the shell is missing. Otherwise the agent spends a turn deciding what to do, or recommends an install the user did not ask for.

## Proposed change (one PR, three files, additive documentation only)

### 1. `skills/mcp-setup/SKILL.md`, Step 1 "Confirm prerequisites" (after the node/git block)

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

For more, see https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell.

If `mongosh` is not installed, do not treat that as a blocker. These DocumentDB MCP
server tools cover the same checks: `list_databases` (pass `db_name` to list that
database's collections), `list_indexes`, `find_documents`, `sample_documents`,
`aggregate`, `explain_operation`, `get_statistics` and `current_ops`.
````

### 2. `skills/local-deployment/local-connection-config.md` (immediately before the first `mongosh localhost:10260` example)

```markdown
> `mongosh` is optional. Install it with `npm install -g mongosh` (or Homebrew, or the MongoDB download; see
> the mcp-setup skill, Step 1). Without it, use the DocumentDB MCP server tools or the driver examples below.
```

### 3. `skills/query-optimizer/SKILL.md`, section "Local mongosh Commands (No MCP Required)" (after the first paragraph)

```markdown
**If mongosh is not installed** and the DocumentDB MCP server is configured, use the MCP
equivalents instead of installing the shell: `list_indexes` for `getIndexes()`,
`explain_operation` for `.explain("executionStats")`, `find_documents` (limit 1) or
`sample_documents` for `findOne()`, `list_databases` with `db_name` for `show collections`,
`get_statistics` (scope `collection` / `index`) for `stats()` / `$indexStats`, and
`current_ops` for `db.currentOp()`. Install mongosh only when the user asks for an
interactive shell (`npm install -g mongosh`).
```

Review corrections already applied: the MCP server has no `list_collections` tool (`list_databases` with `db_name` returns collections, per `src/tools/database-tools.ts`); the unverified winget id is removed in favor of the documented MSI; the connection template matches Learn. The query-optimizer skill keeps its MCP-first order. The PR changes no code or behavior.

## Evidence

Each path is a run folder from the experiment; see `accelerators_missed` in `02-readiness.json`:

- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/02-readiness.json`
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json`
- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json`
- `runs/11-correspondent-banking-risk-screener/20261124-201541/02-readiness.json`

## Open questions

1. The connection template uses `retrywrites=false`, as the Learn connection string does. Our source drafts disagree on what that setting means. One position is that Learn does not say retryable writes are unsupported, so the option is a recommendation. The other is that retryable writes are not supported and cause write errors if enabled. This PR adds no rationale. Can engineering confirm the actual behavior so that any wording the kit adds later is accurate? [needs SME confirmation]
2. Before this is quoted externally, should the sample count be taken from a clean re-run? The 16 comes from the extracted finding ids. A recount over all run folders, including runs finished after extraction, finds mongosh flagged in 19 samples, and the harness's `mongosh --version` probe inflates the number. [needs SME confirmation]
3. The npm `mongosh` package lists `engines.node >=16.15.0`. Does the kit need to state that floor, or is the MCP server's Node 20+ requirement enough? [needs SME confirmation]

## Source drafts

- 060-mongosh-is-never-installed-kit-setup-and-connection-skills-s.md
