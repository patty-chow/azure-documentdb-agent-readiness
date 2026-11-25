---
title: "mcp-setup skill: say that the documentdb MCP server is the data-plane server, and that the Azure MCP Server has no Azure DocumentDB tools"
repo: Azure/documentdb-agent-kit
type: issue
status: ready_with_edits
priority: P2
sample_count: 4
findings: 4
bucket: confusion-Q13
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# mcp-setup skill: say that `documentdb` is the data-plane MCP server, and that the Azure MCP Server has no Azure DocumentDB tools

## What happens today
In an agent-readiness experiment (gpt-5-mini, 100 Azure DocumentDB sample prompts, kit skills plus the documentdb, Azure and Learn MCP servers), we asked the model cold, before grounding: "Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it?" In 4 of the 100 samples it said there is no DocumentDB-specific server and that the general Azure MCP Server covers data-plane inspection. All four were scored `partly_wrong`. The model only fixed its answer by reading the live tool list, not from anything the kit says.

The kit bundles `microsoft/documentdb-mcp` as the `documentdb` server in `mcp.json`, and `skills/mcp-setup/SKILL.md` explains how to install it. But neither that skill nor `AGENTS.md`:
- mentions the Azure MCP Server,
- says that `documentdb` is the server for data-plane work (queries, explain, indexes, stats), or
- lists the tools the server provides and which capability gate each one needs (the skill only says "Ask the agent to list available DocumentDB tools").

So an agent that has loaded the skill still has to guess which server to reach for.

## Why it matters
The Azure MCP Server has no Azure DocumentDB (`Microsoft.DocumentDB/mongoClusters`) namespace at all. Its `cosmos` namespace works with Azure Cosmos DB accounts, databases and containers, which is a different service. If an agent goes with its prior and uses only the Azure MCP Server, it has no `explain_operation`, `sample_documents`, `aggregate` or `get_statistics`. It ends up writing ad-hoc driver scripts to check indexes and query plans. That is slower, and it makes it more likely that index or explain checks get skipped. The builds in these runs did call `documentdb` tools once the environment exposed them, so the impact so far is small. The risk is in clients where the agent picks servers based on what it has read.

## Proposed change
1. In `skills/mcp-setup/SKILL.md`, add a section after the intro:

```markdown
## When to use which MCP server
- **`documentdb` (this server, microsoft/documentdb-mcp)**: the data plane of a live cluster.
  - Read tools (on by default): `list_databases`, `find_documents`, `count_documents`,
    `aggregate`, `sample_documents`, `explain_operation`, `list_indexes`, `get_statistics`.
  - Write tools (`ENABLE_WRITE_TOOLS=true`): `insert_documents`, `update_documents`,
    `delete_documents`, `find_and_modify`.
  - Management tools (`ENABLE_MANAGEMENT_TOOLS=true`): `create_index`, `drop_index`,
    `current_ops`, `drop_collection`, `rename_collection`, `drop_database`.
    The kit's `mcp.json` leaves write and management tools off.
- **Azure MCP Server**: it has no Azure DocumentDB tools. It has no query, explain or index
  tools for DocumentDB, and its `cosmos` namespace is for Azure Cosmos DB, not
  Azure DocumentDB. Use its general tools (resource groups, Bicep schema, deploy,
  RBAC, Monitor) only for Azure resource work around the cluster.
- **Provisioning / scaling / firewall / Entra admin on `Microsoft.DocumentDB/mongoClusters`**:
  use `az documentdb mongocluster`, Bicep or Terraform (see `documentdb-azure-deployment`).
Rule: documentdb MCP for data; Azure tooling for resources.
```

2. In the `AGENTS.md` "Routing hints for agents" list, add: `**Querying / inspecting / explaining against a live cluster** -> the documentdb MCP server tools (see documentdb-mcp-setup); the Azure MCP Server has no DocumentDB data-plane tools`.

## Evidence
- runs/06-collateral-management-store/20261124-200922/02-readiness.json (confusions, Q13)
- runs/07-mortgage-application-multi-agent/20261124-201025/02-readiness.json (confusions, Q13)
- runs/08-interest-rate-scenario-modeler/20261124-201113/02-readiness.json (confusions, Q13)
- runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json (confusions, Q13)

## Verification

### 1. Already covered? partially_covered
The kit ships the server and the skill installs it, but the split is never stated in words.
- `mcp.json` defines the `documentdb` server (`npx -y documentdb-mcp-server`, `ENABLE_READ_TOOLS=true`, `ENABLE_WRITE_TOOLS=false`, `ENABLE_MANAGEMENT_TOOLS=false`).
- `skills/mcp-setup/SKILL.md` says the skill "guides users through wiring the microsoft/documentdb-mcp server into an agentic client". It names no tools beyond telling the user to "list available DocumentDB tools" and to set `ENABLE_WRITE_TOOLS` / `ENABLE_MANAGEMENT_TOOLS`.
- `AGENTS.md` routing hints include "Setting up the DocumentDB MCP server -> documentdb-mcp-setup" but no hint about which server to use for querying or explaining.
- A grep of `skills/`, `knowledge-base/`, `AGENTS.md`, `README.md` and `mcp.json` for "Azure MCP", "azmcp", "data plane" and "control plane" finds no text about MCP server choice. The only matches are unrelated uses of "data plane" / "control plane" in security and HA skills.

### 2. Premise true? confirmed (details corrected)
The core premise holds: the kit does not say which MCP server handles data-plane work. Two technical details in the original draft were wrong and have been fixed in the body above:
- The draft listed `create_index` and `current_ops` as default data-plane tools and put only write tools behind a gate. Per `documentdb-mcp/tool_list.md`, `create_index`, `drop_index`, `current_ops`, `drop_collection`, `rename_collection` and `drop_database` are `management` tools that need `ENABLE_MANAGEMENT_TOOLS=true`. The kit's `mcp.json` turns that gate off. The tool list is now split into read, write and management.
- The draft said the Azure MCP Server is the control plane for `Microsoft.DocumentDB/mongoClusters` ("provision, scale, firewall, Entra"). The Azure MCP Server tools page (https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/, updated 2026-10) lists no Azure DocumentDB / mongoClusters namespace. Its Databases namespaces are `cosmos` (Azure Cosmos DB accounts, databases, containers, documents), `mysql`, `postgres`, `redis` and `sql`. The body now says the Azure MCP Server has no DocumentDB tools. It routes cluster provisioning and scaling to `az documentdb mongocluster`, Bicep or Terraform via the kit's `documentdb-azure-deployment` skill.
- Confirmed: `microsoft/documentdb-mcp` tool names (`documentdb-mcp/src`, `tool_list.md`); read tools on by default, write behind `ENABLE_WRITE_TOOLS`, management behind `ENABLE_MANAGEMENT_TOOLS` (`documentdb-mcp/README.md` line 122).

### 3. Maintainer skeptic: confirmed
The issue names two exact files (`skills/mcp-setup/SKILL.md`, `AGENTS.md`), gives paste-ready text, and is specific to Azure DocumentDB tool routing inside this kit. A kit maintainer would accept it with small edits. It belongs in Azure/documentdb-agent-kit, not microsoft/documentdb-mcp: the routing guidance is part of the kit's skills, and the MCP server README is not what the agent loads.

## Finding ids
- F0854
- F1109
- F1266
- F2090
