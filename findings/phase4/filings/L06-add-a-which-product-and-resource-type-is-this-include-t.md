---
id: L06
title: "Add a 'Which product and resource type is this?' include to the Azure DocumentDB overview and quickstarts"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 49
member_drafts:
  - 073-product-and-resource-type-disambiguation-microsoft-documentd.md
open_questions: 3
---

# Add a "Which product and resource type is this?" include to the Azure DocumentDB overview and quickstarts

**Pages (MicrosoftDocs/nosql-docs-pr, `azure/documentdb/`):** `overview.md`, `quickstart-portal.md`, `quickstart-cli.md`, `quickstart-bicep.md`, `quickstart-terraform.md`, and the language quickstarts (`quickstart-nodejs.md`, `quickstart-python.md`, `quickstart-dotnet.md`, `quickstart-java.md`, `quickstart-go.md`, `quickstart-rust.md`).

Out of scope for this Learn item: the `az cosmosdb mongocluster` reference (generated from `Azure/azure-cli-extensions`, `cosmosdb-preview`; filed as X01) and the ARM schema reference / Azure Verified Module labels, which have their own source repositories. The ARM and AVM changes are listed under "Related changes in other repositories" below and still need to be filed with those owners.

## What happens today

A reader, human or AI agent, whose idea of "Azure DocumentDB" predates the rename tends to use the Azure Cosmos DB control plane. Learn doesn't correct them where they land:

- The overview's **Naming and history** section is the last section on the page. It correctly says the service was previously vCore-based Azure Cosmos DB for MongoDB and is a different service from Azure Cosmos DB for MongoDB (RU). It doesn't name the resource type, CLI group, Terraform resource, billing model or host suffix, and those are the details people get wrong.
- No quickstart carries a disambiguation note. `quickstart-cli` installs the `documentdb` extension and `quickstart-bicep` declares `Microsoft.DocumentDB/mongoClusters`, but neither says "not `az cosmosdb`" or "not `databaseAccounts`". A reader who arrives with the wrong mental model has nothing on the page that contradicts it.

The provisioning content itself is fine. The Bicep, Terraform and CLI quickstarts already show how to create and delete a cluster, so no new page is needed. What's missing is a note that tells readers which product they're on.

## Why it matters

We ran an agent-readiness experiment: an AI coding agent (gpt-5-mini) built 100 Azure DocumentDB sample apps. Before it loaded any docs, each run answered a short quiz from prior knowledge. The four questions below were asked in 118 runs (some samples ran more than once), and not every run was scored on every question, so the rows don't each add up to 118. Most answers were wrong or partly wrong:

| Question (answered from prior knowledge) | wrong | partly wrong | correct |
| --- | --- | --- | --- |
| Resource provider namespace and resource type | 86 | 15 | 5 |
| Azure CLI command group | 59 | 45 | 1 |
| How capacity is provisioned and billed | 78 | 16 | 15 |
| Connection string shape (scheme, host suffix, port, options) | 34 | 71 | 1 |

Typical wrong answers were `Microsoft.DocumentDB/databaseAccounts` with `mongodbDatabases` children, `az cosmosdb create`, request units, and the legacy `<account>.mongo.cosmos.azure.com:10255` host with `replicaSet=globaldb`. In most scored confusions the model mixed this service up with Azure Cosmos DB for MongoDB (RU). These numbers describe the model's prior knowledge rather than a product defect. That's why the correction belongs on Learn: Learn feeds both model training data and the Learn MCP server.

Later in the build, the audit stage logged 57 doc-gap findings on this theme across **49 of the 100 samples**. Auditors noted that authors avoided infrastructure-as-code rather than risk using the wrong resource type, and one sample shipped a `.env.example` with a Cosmos DB account host pattern. All counts come from a single run of the experiment and may shift on a re-run.

## Proposed change

### 1. New include: `includes/which-product-is-this.md`

Insert it directly under the H1 intro paragraph of every page listed above. Suggested text:

> **Which product and resource type is this?**
> Azure DocumentDB (with MongoDB compatibility) was previously named *vCore-based Azure Cosmos DB for MongoDB*. It runs on the open-source, PostgreSQL-based DocumentDB engine. It is **not** Azure Cosmos DB for MongoDB (RU), **not** Amazon DocumentDB, and **not** the 2014-2017 Azure DocumentDB that became Azure Cosmos DB. Examples written for those products use a different control plane and don't work here.
>
> | | Azure DocumentDB (this service) | Azure Cosmos DB for MongoDB (RU) |
> | --- | --- | --- |
> | ARM / Bicep resource type | `Microsoft.DocumentDB/mongoClusters` | `Microsoft.DocumentDB/databaseAccounts` with `kind: 'MongoDB'` |
> | Azure CLI | `az documentdb mongocluster ...` (`documentdb` extension) | `az cosmosdb ...` |
> | Terraform | `azurerm_mongo_cluster` (azurerm 4.x) or AzAPI `Microsoft.DocumentDB/mongoClusters` | `azurerm_cosmosdb_account` |
> | Capacity and billing | Compute tier (for example M10, M30, M40; each tier maps to a vCore and memory size) plus storage, scaled independently | Request units per second (RU/s) |
> | Host and connection | `mongodb+srv://` to `<cluster>.mongocluster.cosmos.azure.com`, no explicit port | `<account>.mongo.cosmos.azure.com:10255` with `replicaSet=globaldb` |
> | Authentication | Native (SCRAM-SHA-256) users or Microsoft Entra ID | Account keys or Entra ID |
>
> Copy your connection string from **Connection strings** in the portal, or from `az documentdb mongocluster list-connection-strings`, and pass it to your MongoDB driver unchanged. It uses the `mongodb+srv` scheme and includes `tls=true`, `authMechanism=SCRAM-SHA-256`, `retrywrites=false` and `maxIdleTimeMS=120000`. Don't split out the host and port, and don't add `replicaSet`.
>
> Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys).

The last paragraph of the include is an explicit ask: explain why `retrywrites=false` is required, with the de-duplication reason. No Learn page (limitations, compatibility, connect, quickstarts) states the reason today, so keep this paragraph even if the comparison table is trimmed. Don't describe `retrywrites=false` as a recommendation or a sample choice, and don't claim that `retryWrites=true` causes connection errors; that isn't established.

### 2. Overview: move "Naming and history" up

Move the existing **Naming and history** section directly after the intro paragraph, and replace its bullets with the include above. The current content is accurate, but readers miss it at the bottom of the page.

### 3. `quickstart-bicep` and `quickstart-terraform` only: "Coming from a Cosmos DB template?"

Add this mapping after the template:

| Cosmos DB (RU) | Azure DocumentDB |
| --- | --- |
| `databaseAccounts`, `kind: 'MongoDB'` | `Microsoft.DocumentDB/mongoClusters` |
| `databaseAccounts/mongodbDatabases`, `.../collections` | No ARM child resource. Create databases and collections from the driver or `mongosh`. |
| `options.throughput` / `autoscaleSettings.maxThroughput` | `properties.compute.tier` and `properties.storage.sizeGb` |
| `apiProperties.serverVersion` | `properties.serverVersion` |
| `ipRules` | `Microsoft.DocumentDB/mongoClusters/firewallRules` child resource |
| `azurerm_cosmosdb_account` | `azurerm_mongo_cluster` |

Then add: "This template uses a low-cost development configuration (`M10`, 32 GiB storage, `shardCount: 1`, high availability disabled). For production, choose a higher tier and enable high availability."

## Related changes in other repositories (not yet filed)

These come from the same source draft. They aren't in nosql-docs-pr, so they need to be filed with their owners:

- **ARM schema reference** (`MicrosoftDocs/azure-resource-manager-schema-reference-pr`, the `Microsoft.DocumentDB/databaseAccounts` page): add a note at the top: "To deploy an **Azure DocumentDB (with MongoDB compatibility)** cluster, use `Microsoft.DocumentDB/mongoClusters` instead. `databaseAccounts` with `kind: 'MongoDB'` creates an Azure Cosmos DB for MongoDB (RU) account." Today the page doesn't mention `mongoClusters`, vCore or Azure DocumentDB.
- **`Microsoft.DocumentDB/mongoClusters` reference labels**: the Azure Verified Module rows (Bicep `avm/res/document-db/mongo-cluster`, Terraform `terraform-azurerm-avm-res-documentdb-mongocluster`) and the AzAPI sample caption still say "Cosmos DB for MongoDB (vCore)". Rename them to "Azure DocumentDB (formerly Cosmos DB for MongoDB vCore)". The text comes from the AVM module metadata and the schema-reference sample sources.
- **`az cosmosdb mongocluster` help text** (`Azure/azure-cli-extensions`, `src/cosmosdb-preview`): filed as X01.

## Evidence

Run folders from the experiment:

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/doc-gaps.md`: resource type and CLI group disambiguation, rated high priority
- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json`: answered `databaseAccounts` and `az cosmosdb` from prior knowledge
- `runs/13-product-q-a-chatbot-rag/20261124-184527/02-readiness.json`: names `az cosmosdb mongocluster` as the source of the confusion
- `runs/14-customer-complaint-classifier/20261124-201931/doc-gaps.md`: `.env.example` shipped with a Cosmos DB account host pattern
- `runs/19-care-coordination-multi-agent/20261124-195730/doc-gaps.md`: legacy host, port 10255 and `replicaSet=globaldb` confusion

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

## Open questions

1. **Global read-write host.** [needs SME confirmation] Clusters with replicas also expose `<cluster>.global.mongocluster.cosmos.azure.com`. Should the table mention it, and is the wording "global read-write host for clusters with replicas" correct?
2. **Production guidance in the Bicep/Terraform note.** [needs SME confirmation] Is "enable high availability" (for example `targetMode: 'ZoneRedundantPreferred'`) the recommended production default, and which tiers should be named as examples?
3. **Authentication row.** [needs SME confirmation] Confirm that the RU-column authentication summary (account keys or Entra ID) is accurate enough for a comparison table, or drop the row.

## Source drafts

- `073-product-and-resource-type-disambiguation-microsoft-documentd.md`
