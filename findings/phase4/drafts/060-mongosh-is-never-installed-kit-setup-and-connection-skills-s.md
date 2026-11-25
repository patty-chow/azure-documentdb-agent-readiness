---
title: "Document mongosh as an optional tool (install commands + MCP-tool fallback) in mcp-setup, local-deployment and query-optimizer skills"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 16
findings: 16
bucket: kit-accelerator-missed
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Document mongosh as an optional tool: install commands and MCP-tool fallback

## What happens today

Several skills assume `mongosh` is on PATH, but no skill introduces it, says how to install it, or says what to do when it is missing:

- `skills/query-optimizer/SKILL.md` lines 33-51 pair every MCP tool with a mongosh equivalent (`db.<coll>.getIndexes()`, `.explain("executionStats")`, `db.currentOp()`). The section "Local mongosh Commands (No MCP Required)" (line 69) and "If MCP is not available, use mongosh directly" (line 227) treat mongosh as the fallback. Nothing covers the more common case in which the MCP server is configured and mongosh is not.
- `skills/local-deployment/local-connection-config.md` uses `mongosh localhost:10260 ...` for its canonical incorrect and correct examples. `local-prod-parity.md` line 58 tells CI to run the index `.js` files "with `mongosh` against the cluster URI". `local-sample-data-management.md` says the image runs `.js` seed scripts through mongosh. `local-ports-and-bindings.md` lists mongosh as a client for port 10260.
- `skills/mcp-setup/SKILL.md` Step 1 "Confirm prerequisites" lists only `node --version` and `git --version`.

An agent that reads these skills learns that mongosh is expected, finds it absent, and has to decide on its own whether that matters.

## Why it matters

The experiment ran a readiness check and a build over 100 Azure DocumentDB sample prompts, using gpt-5-mini with the kit skills and the DocumentDB, Azure and Learn MCP servers. In 16 of the 100 runs, `02-readiness.json` listed mongosh under `accelerators_missed`. The entries said things like "missing from PATH; installing mongosh speeds manual verification of indexes and sample documents". Three runs (15-cohort-analysis-backend, 16-atm-network-status-monitor and 12-abandoned-cart-recovery-orchestration) worked out on their own that the DocumentDB MCP server offers the same operations. The other 13 only recorded it as a gap.

To be clear about scope: none of the 16 builds was blocked or measurably slowed. The build agents never tried to run mongosh, and the MCP server's `list_indexes`, `find_documents` and `explain_operation` tools did the verification work. The experiment harness also runs `mongosh --version` in its environment inventory, which makes the readiness agent more likely to notice that the shell is missing. This is a cheap consistency fix, not a correctness bug. The skills should state what they assume and send the agent to the MCP tools when the shell is missing. Otherwise the agent spends a turn deciding what to do, or recommends an install the user did not ask for.

## Proposed change (one PR, three files, additive text only)

### 1. `skills/mcp-setup/SKILL.md`, Step 1 "Confirm prerequisites"

Add this after the node/git block:

````markdown
**Optional: `mongosh`** (MongoDB Shell). The MCP server does not need it. It is
useful for ad-hoc checks and for running the `.js` index and seed scripts that the
local-deployment skill uses. Install it with one of:

```bash
npm install -g mongosh            # any platform with Node.js (the npm package needs Node >= 16.15; the MCP server already needs Node 20+)
brew install mongosh              # macOS (Homebrew)
# Windows: MSI installer from https://www.mongodb.com/try/download/shell
# Linux: MongoDB apt/yum repository, or download from https://www.mongodb.com/try/download/shell
```

Connect to Azure DocumentDB with the cluster's SRV string and its required options
(`tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`).
Leave the password out of the string so that mongosh prompts for it:

```bash
mongosh "mongodb+srv://<user>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000"
```

For more, see https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell.

If `mongosh` is not installed, do not treat that as a blocker. These MCP server
tools cover the same checks: `list_databases` (pass `db_name` to list that
database's collections), `list_indexes`, `find_documents`, `sample_documents`,
`aggregate`, `explain_operation`, `get_statistics` and `current_ops`.
````

### 2. `skills/local-deployment/local-connection-config.md`

Add one line immediately before the first `mongosh localhost:10260 ...` example:

```markdown
> `mongosh` is optional. Install it with `npm install -g mongosh` (or Homebrew, or the MongoDB download; see
> the mcp-setup skill, Step 1). Without it, use the DocumentDB MCP server tools or the driver examples below.
```

### 3. `skills/query-optimizer/SKILL.md`, section "Local mongosh Commands (No MCP Required)"

Add this after the first paragraph:

```markdown
**If mongosh is not installed** and the DocumentDB MCP server is configured, use the MCP
equivalents instead of installing the shell: `list_indexes` for `getIndexes()`,
`explain_operation` for `.explain("executionStats")`, `find_documents` (limit 1) or
`sample_documents` for `findOne()`, `list_databases` with `db_name` for `show collections`,
`get_statistics` (scope `collection` / `index`) for `stats()` / `$indexStats`, and
`current_ops` for `db.currentOp()`. Install mongosh only when the user asks for an
interactive shell (`npm install -g mongosh`).
```

All three edits are documentation only, with no behavior or code changes. The query-optimizer skill keeps its existing MCP-first order.

## Evidence (run folders from the experiment: `02-readiness.json` -> `accelerators_missed`)

- `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/02-readiness.json`
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json`
- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json`
- `runs/11-correspondent-banking-risk-screener/20261124-201541/02-readiness.json`

Full list of affected samples (16): 03-medication-interaction-checker, 04-customer-journey-mapper, 05-kyc-document-ingestion-pipeline, 07-customer-review-sentiment-pipeline, 09-clinical-notes-de-identification, 10-support-ticket-rag-assistant, 10-wealth-management-rag-portal, 11-correspondent-banking-risk-screener, 11-visual-similarity-search-image-embeddings, 12-abandoned-cart-recovery-orchestration, 12-hospital-bed-occupancy-tracker, 14-customer-complaint-classifier, 14-hyper-personalized-content-engine, 15-cohort-analysis-backend, 16-atm-network-status-monitor, 16-multi-touch-attribution-model.

## Verification

### 1. Already covered? partially_covered

The kit uses mongosh in many places but never introduces it, never shows how to install it, and never maps a missing mongosh to the MCP tools. The only fallback it describes goes the other way, from missing MCP to mongosh.
- `skills/mcp-setup/SKILL.md` Step 1 shows only `node --version   # must be >= 20` and `git --version`. There is no mongosh line.
- `skills/query-optimizer/SKILL.md:71` says "All diagnostic operations can be performed directly via mongosh. Use these when MCP is not available". Line 227 says "**If MCP is not available**, use mongosh directly". There is no statement for the case where mongosh is missing.
- `skills/local-deployment/local-connection-config.md:22,25,44`, `local-prod-parity.md:58`, `local-sample-data-management.md:14,32`, `local-ports-and-bindings.md:11` and `local-choose-deployment-method.md:13,41` all reference mongosh without install guidance. A grep for `install` plus `mongosh` across `skills/` and `knowledge-base/` finds nothing.
- Learn already documents the connection: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell ("Connect Using MongoDB Shell") lists MongoDB Shell as a prerequisite and links https://www.mongodb.com/try/download/shell. The agent did not find that page through the kit. The draft now links it rather than restating it.

### 2. Premise true? confirmed (with corrections applied)

The core premise is true: the kit references mongosh without listing it as a prerequisite, and the MCP server provides equivalent read tools. I made these corrections to the original draft:
- **There is no `list_collections` tool.** The registered tool names in `documentdb-mcp/src/tools/*.ts` are list_databases, list_indexes, find_documents, count_documents, aggregate, explain_operation, sample_documents, get_statistics, current_ops, plus the write and management tools. `src/tools/database-tools.ts:17-20` says `list_databases` "If db_name is provided, return that database collections with estimated document counts". The draft now names `list_databases` with `db_name` in place of `list_collections`.
- **winget id removed.** The MongoDB install page (https://www.mongodb.com/docs/mongodb-shell/install/) documents the Windows MSI or .zip from the Download Center and `brew install mongosh` on macOS. It does not document a winget id, so the draft now points Windows users to the MSI.
- **The Node requirement is now accurate.** The npm registry metadata for `mongosh` (latest 2.14.3) has `engines.node >=16.15.0`, not ">= 20". The draft now says this and notes that the MCP server itself needs Node 20+ (`mcp-setup/SKILL.md` Step 1).
- **The connection template matches Learn.** It uses the SRV host `<cluster>.mongocluster.cosmos.azure.com` with `tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`, and connects with the username in the URI and no password so that mongosh prompts for it (Learn, "Connect with interactive password authentication").

### 3. Maintainer skeptic: confirmed

The PR names three exact files, gives the text to add, and is DocumentDB-specific: vCore connection options, mapping to the DocumentDB MCP tools, and the local Gateway on port 10260. It is additive documentation that fits the kit's MCP-first approach and closes a real inconsistency, since skills reference a tool they never introduce. It belongs in the kit rather than in documentdb-mcp, because the change is about how the agent chooses tools. With the tool-name corrections above, I would accept it.

## Finding ids

F0400, F0539, F0808, F1016, F1385, F1698, F1733, F1807, F1904, F1932, F2066, F2340, F2406, F2499, F2663, F2724
