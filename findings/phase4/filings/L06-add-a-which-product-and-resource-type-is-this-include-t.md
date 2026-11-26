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
open_questions: 1
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
> | Azure CLI | `az documentdb mongocluster ...` (`documentdb` extension, Azure CLI 2.75.0 or later; the older `az cosmosdb mongocluster` group manages the same resource type but is superseded) | `az cosmosdb ...` |
> | Terraform | `azurerm_mongo_cluster` (azurerm 4.x and later) or AzAPI `Microsoft.DocumentDB/mongoClusters` | `azurerm_cosmosdb_account` |
> | Capacity and billing | Compute tier (M10 to M200; M10, M20 and M25 are burstable dev/test tiers) plus storage, applied to every physical shard and scaled independently; storage can be increased but not decreased | Request units per second (RU/s) |
> | Host and connection | `mongodb+srv://` to `<cluster>.mongocluster.cosmos.azure.com` (the portal's **Self** string) or `<cluster>.global.mongocluster.cosmos.azure.com` (the **Global read-write** string), no explicit port | `<account>.mongo.cosmos.azure.com:10255` with `replicaSet=globaldb` |
> | Authentication | Native (SCRAM-SHA-256) users or Microsoft Entra ID | Account keys or Entra ID |
>
> Copy your connection string from **Connection strings** in the portal (Cluster > Settings > Connection strings), or from `az documentdb mongocluster list-connection-strings` (pick the entry by `name`; `GlobalReadWrite` is listed first and `Self` second), and pass it to your MongoDB driver unchanged. It uses the `mongodb+srv` scheme and includes `tls=true`, `authMechanism=SCRAM-SHA-256`, `retrywrites=false` and `maxIdleTimeMS=120000`; the Microsoft Entra ID strings, listed once Entra ID is enabled, use `authMechanism=MONGODB-OIDC` and carry no credentials. Don't split out the host and port, and don't add `replicaSet`: the cluster hosts are SRV names with no A record, so a `mongodb://` string with the cluster host fails. On a single cluster the Self string and the Global read-write string are interchangeable. If the cluster has or may get a cross-region replica, use the Global read-write string for writes so that a promotion needs no code change; the Self string of the old primary becomes read-only after promotion. Replica clusters expose only a Self string. Never construct the host from the cluster name; use the string the portal, CLI or REST API returns.
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

Then add: "This template uses a low-cost development configuration (`M10`, 32 GiB storage, `shardCount: 1`, high availability disabled). For production, choose `M30` or higher and set `properties.highAvailability.targetMode` to `'ZoneRedundantPreferred'`. M10, M20 and M25 are burstable dev/test tiers: they support one physical shard and no in-region high availability, and a cluster scaled to M30 or higher can't be scaled back down to them. `Disabled` is documented by the resource provider as not recommended for production."

Don't name `SameZone` in the note: it is in the API contract and accepted by the CLI, but the azurerm provider doesn't expose it and whether the control plane accepts an explicit request today is still an open engineering question (DECISIONS.md, topic 11).

### 4. Language quickstarts and `quickstart-portal`: agree on the host form

All six language quickstarts hard-code `<your-cluster-name>.global.mongocluster.cosmos.azure.com` while telling the reader to copy "the value from the Connection string field", and `quickstart-portal` says "the Connection string field" (singular) and shows only the plain host. The portal shows two fields, **Self (always this cluster)** and **Global read-write**, and neither page says so. Both forms are valid; this is an inconsistency of presentation, not of fact. Fix: either switch the quickstart samples to the plain (Self) host, which is what `how-to-connect-mongo-shell`, `how-to-connect-cloud-shell`, the Learn training unit and the REST API default string show, or keep `.global.` and add the one-sentence explanation from the include ("on a single cluster either string works; use the Global read-write string for writes when the cluster has a replica"). Either way, name both portal fields where the reader is told to copy the value, and link the connection-string reference once L07 lands.

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
- Global read-write host: answered 2026-11-25, see findings/phase4/DECISIONS.md (host forms, SME topic 3; settled from Learn, no SME needed). The portal offers two connection strings, **Self (always this cluster)** on `<cluster>.mongocluster.cosmos.azure.com` and **Global read-write** on `<cluster>.global.mongocluster.cosmos.azure.com`; on a single cluster either works, the global string exists only on the primary and keeps writes working across a replica promotion, replica clusters expose only a Self string, and the host must be taken from the returned connection string rather than built from the cluster name. The table now shows both; the earlier wording "for clusters with replicas" was imprecise because every primary cluster has a Global read-write string. Sources: Learn how-to-connect-role-based-access-control ("Get cluster credentials"), how-to-cluster-replica#use-connection-strings, how-to-private-link, how-to-cross-region-replica-portal, training unit create-configure-azure-documentdb-cluster/3-connect-to-cluster, tutorial-nodejs-mongoose. The managed test of 2026-11-25 confirmed this on one cluster with no replica: the `.global.` host resolves, authenticates and takes writes, data written through either host is visible through the other, both hosts are SRV-only (no A record), and `list-connection-strings` returns `GlobalReadWrite` first and `Self` second; a replica was not tested (ENGINE-TESTS.md, Managed service; DECISIONS.md topic 3).
- Production guidance in the Bicep/Terraform note: answered 2026-11-25, see findings/phase4/DECISIONS.md (CLI, IaC and server versions, SME topic 11). Enable HA with `highAvailability.targetMode: 'ZoneRedundantPreferred'`: the resource provider's HighAvailabilityMode contract documents `Disabled` as "not recommended for production" and `ZoneRedundantPreferred` as preferring zone redundancy and falling back to same-zone, and the azurerm provider exposes only those two values. Name M30 or higher as production tiers: M10, M20 and M25 are burstable dev/test tiers with one physical shard and no in-region HA, a cluster scaled to M30 or higher can't go back to them, and the FAQ calls M30 and larger the production tiers. Whether an explicit `SameZone` request is accepted today stays open, so the note doesn't name it. Sources: Azure/azure-rest-api-specs MongoCluster.tsp (HighAvailabilityMode) and stable/2026-09-01 mongoCluster.json; Learn compute-storage, limitations (Tier limits), high-availability, how-to-scale-cluster, faq; Azure DocumentDB pricing page; terraform-provider-azurerm mongo_cluster r_schema.go.

## Open questions

1. **Authentication row.** [needs SME confirmation] Confirm that the RU-column authentication summary (account keys or Entra ID) is accurate enough for a comparison table, or drop the row. (The Azure DocumentDB column is settled: native SCRAM-SHA-256 users, Microsoft Entra ID, or both; DECISIONS.md topic 5. The RU-based Azure Cosmos DB for MongoDB column is outside DECISIONS.md.)

## Source drafts

- `073-product-and-resource-type-disambiguation-microsoft-documentd.md`
