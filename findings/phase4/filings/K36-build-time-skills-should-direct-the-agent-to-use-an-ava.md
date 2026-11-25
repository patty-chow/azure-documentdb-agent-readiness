---
id: K36
title: "Build-time skills should direct the agent to use an available DocumentDB MCP server"
repo: Azure/documentdb-agent-kit
type: issue
status: ready
priority: P1
sample_count: 12
member_drafts:
  - 134-agent-kit-never-directs-the-builder-to-use-an-available-docu.md
open_questions: 3
---

# Build-time skills should direct the agent to use an available DocumentDB MCP server

## What happens today

Two kit skills already tell the agent to use the DocumentDB MCP tools: `skills/query-optimizer/SKILL.md` ("Use DocumentDB MCP when available", plus an "MCP Tools Available" section) and `skills/natural-language-querying/SKILL.md` ("Requires DocumentDB MCP server"). Both declare `allowed-tools: mcp__documentdb__*`. Both are scoped to query work: optimizing an existing query or generating a read-only query on request.

The skills an agent loads while writing an application say nothing about MCP. A case-insensitive search for "mcp" finds no match in `skills/driver/` (`documentdb-driver`), `skills/connection/` (`documentdb-connection`), `skills/indexing/` (`documentdb-indexing`), `skills/vector-search/` (`documentdb-vector-search`) or `knowledge-base/`. In `AGENTS.md`, MCP appears only in the public-preview status note, the skills-table row and routing entry for `documentdb-mcp-setup`, and the installation notes.

So when an agent is building an app with the kit installed and the bundled MCP server connected to a live cluster, nothing in the skills it actually loads tells it that it can check its work against that cluster.

## Why it matters

We ran 100 Azure DocumentDB sample prompts through an agent pipeline (gpt-5-mini) with the kit skills and the DocumentDB MCP server connected to a live cluster. In most build runs the agent used the MCP tools on its own (`list_databases`, `list_indexes`, `find_documents`, ...). In 13 build runs across 12 distinct samples it made no DocumentDB MCP calls during the build stage. Those runs loaded only the four MCP-silent skills above (for example, one loaded only `documentdb-vector-search`; another loaded `documentdb-driver`, `documentdb-connection` and `documentdb-indexing`). The samples covered vector search, RAG, ledgers, risk screening, multi-agent systems, purchase-order management and recommendations. Counts are from one experiment run and should be re-checked after the harness MCP-configuration fix (recount, not an engineering question); 5 of the 13 runs stopped before writing any files and are weaker evidence, while the other 8 produced complete apps without one MCP call.

What the agent did instead:
- Wrote index and query code without checking it. In one vector-search sample the `cosmosSearch` vector index was never created or listed.
- Reported data loading as "not verified" because no local gateway or cluster "was started in this session", although the cluster was reachable through MCP.
- Pointed the app at a local `documentdb-local` Docker container by default.
- After a seed script failed, marked collections and indexes as unverified, when `list_databases` and `list_indexes` would have answered the question directly.

The MCP server is the one tool that lets an agent confirm that collections, `cosmosSearch` and text indexes, and aggregation shapes work on Azure DocumentDB, and the plugin installs it (`mcp.json`) for that purpose. If the build-time skills do not mention it, a smaller model has nothing prompting it to use the server, and it ships unchecked code.

## Proposed change

1. Add the same short rule to `skills/driver/SKILL.md`, `skills/connection/SKILL.md`, `skills/indexing/SKILL.md` and `skills/vector-search/SKILL.md`:

   > **Live cluster via MCP.** If `mcp__documentdb__*` tools are available, they are connected to the target cluster. Before declaring collections, indexes or queries unverified, or before starting a local container: call `list_databases` (pass a database name to list its collections) and `list_indexes` to check what exists, and run `explain_operation` (or `aggregate`) on one representative query. `create_index` is a *management* tool and works only when the server runs with `ENABLE_MANAGEMENT_TOOLS=true`; if that call is refused, put the index definitions in a setup script and say so. As in `documentdb-query-optimizer`, do not create or drop indexes through MCP without the user's approval.

2. Add `allowed-tools: mcp__documentdb__*` to the frontmatter of those four skills, matching `query-optimizer` and `natural-language-querying`.

3. In `AGENTS.md`, after the task-routing list, add one line: "If DocumentDB MCP tools are present, verify schema, index and query work against the cluster with them (see `documentdb-query-optimizer` for tool names)."

The tool names and gating above were checked against the documentdb-mcp README and `src/security/authorization.ts` (`create_index` is gated by `ENABLE_MANAGEMENT_TOOLS`, not `ENABLE_WRITE_TOOLS`). An optional companion change to tool descriptions in microsoft/documentdb-mcp could be filed separately.

## Evidence

- `runs/01-product-catalog-with-vector-search/20261124-175429` (`03-build.md` "Not verified" section; `events.jsonl` has no DocumentDB MCP calls)
- `runs/15-supplier-po-management/20261124-184929` (no DocumentDB MCP calls)
- `runs/11-correspondent-banking-risk-screener/20261124-201541` (no DocumentDB MCP calls)
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049` (one `list_databases` call during readiness, none during build)
- `runs/19-cross-sell-recommendation-beanie/20261125-055705` (no DocumentDB MCP calls during build)

## Open questions

1. The experiment harness had MCP configuration problems in other runs (some tools left off or gated). The runs cited here had MCP available and used it in other stages, but the 12-sample count should be re-checked after the harness fix before it is quoted externally.
2. Should the build-time rule stop at read-only checks (`list_*`, `explain_operation`), leaving index creation entirely to app setup scripts, or is calling `create_index` with user approval the preferred kit pattern?
3. Is adding `allowed-tools: mcp__documentdb__*` to general-purpose skills acceptable to maintainers, given that these skills are also loaded in sessions with no MCP server configured?

## Source drafts

- 134-agent-kit-never-directs-the-builder-to-use-an-available-docu.md
