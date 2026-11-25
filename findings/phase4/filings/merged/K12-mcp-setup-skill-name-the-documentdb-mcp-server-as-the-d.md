---
id: K12
title: "mcp-setup skill: name the documentdb MCP server as the data-plane server and say what the Azure MCP Server covers"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P2
sample_count: 6
member_drafts:
  - 132-believes-the-general-azure-mcp-server-s-cosmos-db-tools-cove.md
  - 133-believes-no-dedicated-data-plane-mcp-server-exists-for-azure.md
open_questions: 4
---

# mcp-setup skill: name the documentdb MCP server as the data-plane server and say what the Azure MCP Server covers

## What happens today

The kit ships `microsoft/documentdb-mcp` as the `documentdb` server in `mcp.json`, and `skills/mcp-setup/SKILL.md` explains how to install it. But neither that skill nor `AGENTS.md`:

- says that `documentdb` is the MCP server for data-plane work (queries, aggregate, explain, indexes, statistics, sample documents);
- mentions the general Azure MCP Server, or says that its `cosmos` tools work on Azure Cosmos DB accounts, databases and containers (Cosmos DB SQL / NoSQL API queries) and cannot reach a `Microsoft.DocumentDB/mongoClusters` cluster;
- lists the tools the server exposes and which capability gate each needs (the skill only says to "list available DocumentDB tools").

`AGENTS.md` routes "Setting up the DocumentDB MCP server" to `documentdb-mcp-setup` but has no hint about which server to use when querying or explaining against a live cluster. A grep of `skills/`, `knowledge-base/`, `AGENTS.md`, `README.md` and `mcp.json` for "Azure MCP", "azmcp", "data plane" and "control plane" finds nothing about MCP server choice.

## Why it matters

We ran an agent-readiness experiment: 100 Azure DocumentDB sample prompts, gpt-5-mini, this kit plus the DocumentDB, Azure and Learn MCP servers. Before grounding, the model was asked: "Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it?"

In **6 of the 100 samples** it answered wrongly in one of two ways (counts are from one experiment run and may move on a re-run):

- **2 samples:** the general Azure MCP Server or its Cosmos DB tools cover DocumentDB's data plane, confusing Azure DocumentDB with the request-unit Azure Cosmos DB for MongoDB API (once with Azure Cosmos DB for NoSQL). The prior comes from the service's former name, "Azure Cosmos DB for MongoDB vCore".
- **4 samples:** no DocumentDB-specific MCP server exists, so the Azure MCP Server (or plain drivers) is the way to inspect data.

After grounding the model got it right, but only from the live tool inventory or a list of known accelerators, never from anything the kit says. An agent that follows its prior either calls `cosmos` tools that cannot reach the cluster, or skips `explain_operation`, `sample_documents`, `aggregate` and `get_statistics` and writes ad-hoc driver scripts, which makes skipped index and query-plan checks more likely. Builds in this run still called `documentdb_*` tools once exposed, so impact was small; the risk is in clients where the agent picks a server from what it has read. The fix is a few lines.

## Proposed change

### 1. `skills/mcp-setup/SKILL.md`

Add this section after the intro and before `## Safety: never receive credentials in chat`:

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

### 2. `AGENTS.md`

In "Routing hints for agents", next to "Setting up the DocumentDB MCP server -> `documentdb-mcp-setup`" (around line 96), add:

```markdown
- **Querying / inspecting / explaining against a live cluster** -> the `documentdb` MCP server tools (see `documentdb-mcp-setup`). The Azure MCP Server has no DocumentDB data-plane tools; its Cosmos DB tools are for Azure Cosmos DB (NoSQL) accounts, not DocumentDB clusters.
```

Reviewer corrections already applied: the Azure MCP Server is not described as DocumentDB's control plane (no `mongoClusters` tools are listed for it); `create_index` and `current_ops` are management-gated, not default; no npm package name is stated as fact.

## Evidence

- runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json (Q13 wrong; confused with Cosmos DB for MongoDB RU)
- runs/07-customer-review-sentiment-pipeline/20261125-054042/02-readiness.json (Q13 partly_wrong; confused with Cosmos DB for MongoDB RU)
- runs/06-collateral-management-store/20261124-200922/02-readiness.json (Q13 partly_wrong; "no dedicated server")
- runs/07-mortgage-application-multi-agent/20261124-201025/02-readiness.json (Q13 partly_wrong)
- runs/08-interest-rate-scenario-modeler/20261124-201113/02-readiness.json (Q13 partly_wrong)
- runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json (Q13 partly_wrong)
- runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json (Q13 wrong; confused with Cosmos DB for NoSQL; a second run of sample 01, not counted separately in the 6)
- runs/11-market-news-sentiment-orchestration/20261125-062725/02-readiness.json (Q13 wrong; grounded only from the known-accelerators list; cited by draft 132 as supporting context, not counted in the 6)

## Open questions

1. [needs SME confirmation] The Azure MCP Server has no Azure DocumentDB / `mongoClusters` namespace today (per its Learn tools page, updated 2026-10). Is one planned? If so, the "no DocumentDB tools" wording needs a date or a softer phrasing. A separate note to microsoft/mcp pointing to the dedicated server is a possible follow-up; no draft targets it yet.
2. [needs SME confirmation] The read / write / management split and tool names come from `documentdb-mcp/tool_list.md` and the README. Confirm they are stable enough to list in a skill, or whether the skill should link to `tool_list.md` instead.
3. [needs SME confirmation] Distribution: the Learn MCP Toolkit page says there is no published npm package yet, while the kit's `mcp.json` runs `npx -y documentdb-mcp-server`. Which is current? The proposed text avoids naming a package, but `mcp.json` and `AGENTS.md` (line 105 says the plugin bundles "`documentdb-mcp-server` on npm") may need a follow-up.
4. [needs SME confirmation] Is "Azure DocumentDB MCP Toolkit" the canonical product name to use alongside `microsoft/documentdb-mcp`?

## Source drafts

- 132-believes-the-general-azure-mcp-server-s-cosmos-db-tools-cove.md
- 133-believes-no-dedicated-data-plane-mcp-server-exists-for-azure.md
