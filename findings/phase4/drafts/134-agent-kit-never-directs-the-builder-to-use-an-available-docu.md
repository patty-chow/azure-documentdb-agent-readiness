---
title: "Build-time skills (driver, connection, indexing, vector-search) never tell the agent to use the DocumentDB MCP server when it is connected"
repo: Azure/documentdb-agent-kit
type: issue
status: ready_with_edits
priority: P1
sample_count: 12
findings: 13
bucket: kit-mcp-unused
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Build-time skills never tell the agent to use a connected DocumentDB MCP server

## What happens today
Two kit skills already use the DocumentDB MCP tools: `skills/query-optimizer/SKILL.md` and `skills/natural-language-querying/SKILL.md`. Both declare `allowed-tools: mcp__documentdb__*`. query-optimizer says "Use DocumentDB MCP when available" and lists the MCP tools. natural-language-querying says it "Requires DocumentDB MCP server". However, both skills are scoped to *query* work: optimizing an existing query, or generating a read-only query on request. The skills an agent loads while *writing* an app say nothing about MCP: `documentdb-driver` (`skills/driver/`), `documentdb-connection` (`skills/connection/`), `documentdb-indexing` (`skills/indexing/`) and `documentdb-vector-search` (`skills/vector-search/`). In `AGENTS.md`, the task routing mentions MCP only for setup (`documentdb-mcp-setup`).

We ran 100 Azure DocumentDB sample prompts through an agent pipeline with gpt-5-mini. The pipeline connected the kit skills and the DocumentDB MCP server to a live vCore cluster. In most build runs the agent used the MCP tools on its own (`list_indexes`, `list_databases`, `create_index`, `find_documents`, ...). In **13 build runs across 12 distinct samples** it made **zero** `documentdb_*` calls during the build stage. Those runs covered vector search, RAG, ledgers, risk screeners, multi-agent systems, PO management and recommendations. In the build stage, those runs loaded only the MCP-silent skills listed above. For example, sample 01 loaded `documentdb-vector-search`, sample 15 loaded `documentdb-driver`, `documentdb-connection` and `documentdb-indexing`, and sample 11 loaded `documentdb-vector-search`, `documentdb-driver` and `documentdb-connection`. Here is what the agent did instead:
- It wrote index and query code without checking it. For example, in sample 01 the `cosmosSearch` vector index was never created or listed.
- It reported data loading as "not verified" because no DocumentDB local gateway or cluster "was started in this session", even though the cluster was reachable through MCP (sample 01, `03-build.md`).
- It pointed the app at a local `documentdb-local` Docker container by default (sample 01 README).
- In sample 15, the seed script failed. The agent then marked collections and indexes as unverified, when `list_databases` / `list_indexes` through MCP would have answered that question directly.

## Why it matters
The MCP server is the one tool that lets an agent confirm that collections, `cosmosSearch` / text indexes and aggregation shapes actually work on Azure DocumentDB. The plugin installs that server (`mcp.json`, `documentdb-mcp-server`) for exactly this purpose. If the build-time skills don't mention it, a weaker model has nothing that prompts it to use the tool, and it ships code nobody has checked against the cluster.

## Proposed change
1. Add a short rule, worded the same way in each file, to `skills/driver/SKILL.md`, `skills/connection/SKILL.md`, `skills/indexing/SKILL.md` and `skills/vector-search/SKILL.md`:

   > **Live cluster via MCP.** If `mcp__documentdb__*` tools are available, they are connected to the target cluster. Before declaring collections, indexes or queries unverified, or before starting a local container: call `list_databases` (pass a database name to list its collections) and `list_indexes` to check what exists, and run `explain_operation` (or `aggregate`) on one representative query. `create_index` is a *management* tool and works only when the server runs with `ENABLE_MANAGEMENT_TOOLS=true`. If that call is refused, put the index definitions in a setup script and say so. Follow query-optimizer's rule: do not create or drop indexes through MCP without the user's approval.

2. Add `allowed-tools: mcp__documentdb__*` to the frontmatter of those four skills, matching `query-optimizer` and `natural-language-querying`.
3. In `AGENTS.md`, after the task-routing list, add one line: "If DocumentDB MCP tools are present, verify schema/index/query work against the cluster with them (see `documentdb-query-optimizer` for tool names)."

## Evidence (run folders)
- runs/01-product-catalog-with-vector-search/20261124-175429 (`03-build.md` "Not verified" section; `events.jsonl` has no `documentdb_*` calls)
- runs/15-supplier-po-management/20261124-184929 (`events.jsonl` has no `documentdb_*` calls)
- runs/11-correspondent-banking-risk-screener/20261124-201541 (`events.jsonl` has no `documentdb_*` calls)
- runs/07-voice-of-customer-sentiment-hub/20261124-204049 (one `documentdb_list_databases` call during readiness, none during build)
- runs/19-cross-sell-recommendation-beanie/20261125-055705 (no `documentdb_*` calls during build)

Note: 5 of the 13 runs stopped early, before writing any files. Those runs are weaker evidence that the agent ignored the tools. The other 8 wrote complete apps without making a single MCP call.

## Verification

### 1. Already covered? partially_covered
The kit already tells agents to use MCP, but only in query-focused skills that build agents did not load. `skills/query-optimizer/SKILL.md` has `allowed-tools: mcp__documentdb__*` at line 10, and its line 9 says "Use DocumentDB MCP when available". It also has an "MCP Tools Available" section. `skills/natural-language-querying/SKILL.md` has `allowed-tools: mcp__documentdb__*` at line 4, and its description says "Requires DocumentDB MCP server". A grep for "mcp" (case-insensitive) finds no match in `skills/driver`, `skills/connection`, `skills/indexing`, `skills/vector-search` or `knowledge-base/`. In `AGENTS.md`, MCP appears only in the routing for `documentdb-mcp-setup` (line 96) and in the installation notes (lines 105-123). The original draft listed `documentdb-natural-language-querying` as MCP-silent. That was wrong, and the body above now names it as one of the two skills that already cover MCP.

### 2. Premise true? confirmed (with corrections applied)
- The MCP tool names `list_databases`, `list_indexes`, `explain_operation`, `aggregate` and `create_index` all exist (documentdb-mcp `README.md` lines 246-263, `src/tools`). `list_databases` also lists collections when given a database name (README line 246).
- The original draft said `create_index` works "when write tools are enabled". That was wrong. The MCP README (line 253) classifies `create_index` as a **management** tool, and `src/security/authorization.ts` lines 47-50 gate write tools behind `ENABLE_WRITE_TOOLS` and management tools behind `ENABLE_MANAGEMENT_TOOLS`. The proposed rule now names the correct setting. It also adds query-optimizer's existing rule against creating or dropping indexes without approval (`skills/query-optimizer/SKILL.md` line 267).
- The run evidence was checked. During the build stage, runs 01, 15, 11, 07 and 19 made no `documentdb_*` calls. Run 07's one call came during readiness. Build-stage `load_skill` events show only vector-search, driver, connection and indexing. Run 01's `03-build.md` line 47 says data loading was not run because no local gateway or cluster was started.
- The description of the service (vCore, `cosmosSearch`) is consistent with the facts the task states.

### 3. Maintainer skeptic: confirmed
The issue names specific files and frontmatter keys, gives exact rule text, and has a clear Azure DocumentDB angle: verifying `cosmosSearch` and text indexes on a live cluster through the kit's own bundled MCP server. It extends a pattern two kit skills already use, which keeps the change small and consistent. It belongs in this repository because the change is to the guidance in the skills. A related change to tool descriptions in microsoft/documentdb-mcp could be filed separately, but it is optional.

## Finding ids
F0129, F0333, F0676, F1021, F1145, F1180, F1449, F1809, F2166, F2262, F2632, F3192, F3241
