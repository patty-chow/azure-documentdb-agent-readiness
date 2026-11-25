---
title: "mcp-setup skill: say which MCP server is DocumentDB's data plane and what the general Azure MCP Server covers"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P3
sample_count: 2
findings: 2
bucket: confusion-Q13
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# mcp-setup skill: say which MCP server is DocumentDB's data plane

## What happens today
We ran an agent-readiness experiment: 100 Azure DocumentDB sample prompts, gpt-5-mini, this kit plus the DocumentDB, Azure and Learn MCP servers. Question Q13 of the cold quiz (no tools, no docs) asked: "Which MCP server gives an agent data-plane tools for this service? Does the general Azure MCP Server cover it?"

- Of 115 Q13 cold answers, 8 were `wrong` or `partly_wrong`. This theme covers the 2 samples (01, 07) where the model said the general Azure MCP Server or generic Cosmos DB tooling covers DocumentDB's data plane, confusing DocumentDB with the RU-based Azure Cosmos DB for MongoDB API (and in one run with Azure Cosmos DB for NoSQL). Other answers said no service-specific MCP server exists and that "for data-plane you use standard MongoDB drivers."
- After grounding, the model gave the right answer, but it got there from the machine's MCP inventory (the `documentdb` server happened to be configured), from this skill's install instructions, or from a list of known accelerators. Nothing in the kit states the distinction directly.
  - `skills/mcp-setup/SKILL.md`, `AGENTS.md` and `mcp.json` explain how to install the `documentdb` server.
  - None of them mentions the general Azure MCP Server, or says that its Cosmos DB tools do not work against DocumentDB clusters.

## Why it matters
- The prior comes from the service's former name, "Azure Cosmos DB for MongoDB vCore".
- An agent that believes the Azure MCP Server covers DocumentDB may try its `cosmos` tools for collection-level work. Those tools take a Cosmos DB *account*, database and container and run Cosmos DB SQL (NoSQL API) queries, so they cannot reach a `Microsoft.DocumentDB/mongoClusters` cluster. Or the agent may assume no data-plane MCP server exists and skip checking indexes and documents with tools.
- Impact in this experiment was small: builds still called `documentdb_*` tools. The fix is cheap, though, and it protects setups where both servers are installed.

## Proposed change
1. `skills/mcp-setup/SKILL.md`: add this section after the intro and before `## Safety: never receive credentials in chat`:

```markdown
## Which MCP server do I use?

- **Data plane (databases, collections, documents, indexes, aggregate, explain, sample documents):**
  use the `documentdb` MCP server (`microsoft/documentdb-mcp`, the "Azure DocumentDB MCP Toolkit"
  on Microsoft Learn). It is the MCP server with data-plane tools for Azure DocumentDB.
- **Control plane (create/scale/configure a `Microsoft.DocumentDB/mongoClusters` cluster, firewall, replicas):**
  use `az documentdb mongocluster`, Bicep/ARM or Terraform (see the `documentdb-azure-deployment` skill).
- The general Azure MCP Server's Cosmos DB (`cosmos`) tools target Azure Cosmos DB accounts and run
  Cosmos DB SQL (NoSQL API) queries against containers. They do not connect to DocumentDB clusters;
  do not use them to read or write DocumentDB data.
```

2. `AGENTS.md`: in the routing list (next to "Setting up the DocumentDB MCP server -> `documentdb-mcp-setup`", line ~96), add:
   `- Data-plane work on a cluster -> the documentdb MCP server; the Azure MCP Server's Cosmos DB tools are for Cosmos DB (NoSQL) accounts, not DocumentDB clusters.`

## Evidence
- runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json (confusions, Q13: wrong, confused_with azure_cosmos_db_for_mongodb_ru)
- runs/07-customer-review-sentiment-pipeline/20261125-054042/02-readiness.json (confusions, Q13: partly_wrong, confused_with azure_cosmos_db_for_mongodb_ru)
- runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json (confusions, Q13: wrong, confused_with azure_cosmos_db_for_nosql)
- runs/11-market-news-sentiment-orchestration/20261125-062725/02-readiness.json (confusions, Q13: wrong, confused_with none; grounded only from the known-accelerators list)

## Verification

### 1. Already covered? -- confirmed (not there)
Grepped the agent-kit clone (`skills/`, `knowledge-base/`, `AGENTS.md`, `mcp.json`) for "azure mcp", "azmcp", "control plane", "data plane", "cosmos". No hit mentions the general Azure MCP Server or a data-plane vs control-plane split for MCP servers. `skills/mcp-setup/SKILL.md` only describes wiring `microsoft/documentdb-mcp`; `AGENTS.md` line 96 routes "Setting up the DocumentDB MCP server" to `documentdb-mcp-setup` with no comparison; `mcp.json` defines only the `documentdb` server. The Learn page https://learn.microsoft.com/en-us/azure/documentdb/mcp-toolkit describes the toolkit's 18 tools but also does not mention the Azure MCP Server. The microsoft/documentdb-mcp README has no mention either.

### 2. Is the premise true? -- confirmed, with corrections applied
- Confirmed: https://learn.microsoft.com/en-us/azure/documentdb/mcp-toolkit says the toolkit ships from `microsoft/documentdb-mcp` and lists data-plane tools (`list_databases`, `sample_documents`, `find_documents`, `aggregate`, `explain_operation`, `list_indexes`, `create_index`, ...).
- Confirmed: https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/azure-cosmos-db lists the Azure MCP Server's Cosmos DB tools (`azmcp cosmos list`, `... item query`, `... item get`, `text-search`, `vector-search`, `schema infer`); they take an account/database/container and the query "uses Azure Cosmos DB SQL API syntax". None targets mongoClusters.
- Corrected: the draft said the Cosmos DB tools target "NoSQL / RU-based APIs"; the Learn page shows they are NoSQL (SQL API) tools, so the text now says Cosmos DB (NoSQL API) accounts.
- Corrected: the draft told agents to use the Azure MCP Server for DocumentDB control plane. The Azure MCP Server's Cosmos DB tool page lists no mongoClusters tools, so that claim is unsupported; the section now points to `az documentdb mongocluster`, Bicep/ARM or Terraform and the kit's `documentdb-azure-deployment` skill.
- Corrected: the draft said "npm `documentdb-mcp-server`" as fact; the Learn page says "No published npm package yet" while the kit's `mcp.json` runs `npx -y documentdb-mcp-server`. The proposed text now names the repo and the Learn toolkit only, avoiding the conflict.
- Corrected evidence annotations: the 174657 and run 11 Q13 answers are `wrong` (not just confused/partly_wrong), and run 11 was grounded from the accelerators list, not the MCP inventory. The figure "8 of 115 Q13 answers wrong or partly wrong" was recomputed from all 02-readiness.json files (3 wrong, 5 partly_wrong, 99 correct, 8 could_not_verify).

### 3. Maintainer skeptic -- confirmed
Names exact files (`skills/mcp-setup/SKILL.md`, `AGENTS.md`), an insertion point, and ready-to-paste text with a DocumentDB-specific angle (renamed-service prior, tool-surface confusion). Small, low-risk docs change that fits the skill's purpose. I would accept it with the edits above. A matching note on the Learn MCP Toolkit page is a reasonable follow-up but is not part of this PR.

## Finding ids
- F0115
- F1046
