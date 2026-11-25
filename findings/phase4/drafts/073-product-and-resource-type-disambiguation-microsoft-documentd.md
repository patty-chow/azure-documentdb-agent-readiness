---
title: "Learn: add a shared \"Which product and resource type is this?\" include (mongoClusters / az documentdb / vCore billing / SRV host) to the Azure DocumentDB Overview and quickstarts, and cross-link the legacy databaseAccounts and az cosmosdb mongocluster references"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 49
findings: 57
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a shared "Which product and resource type is this?" include to the Azure DocumentDB Overview and quickstarts, and cross-link the legacy `databaseAccounts` / `az cosmosdb mongocluster` references

**Pages (MicrosoftDocs/nosql-docs-pr, `azure/documentdb/`):** `overview.md`, `quickstart-portal.md`, `quickstart-cli.md`, `quickstart-bicep.md`, `quickstart-terraform.md`, and the language quickstarts `quickstart-nodejs.md` (JS/TS pivots), `quickstart-python.md`, `quickstart-dotnet.md`, `quickstart-java.md`, `quickstart-go.md`, `quickstart-rust.md`.
**Related pages owned elsewhere (filed separately, see section 3):** `azure/templates/microsoft.documentdb/databaseaccounts` and `.../mongoclusters` (ARM schema reference), `cli/azure/cosmosdb/mongocluster` (generated from the `cosmosdb-preview` extension).

## What happens today

An agent (or a developer) whose prior knowledge of "Azure DocumentDB" predates the rename reaches for the Cosmos DB control plane, and Learn does not stop it:

- The Overview's **Naming and history** section is the *last* section on the page. It says the service was previously named vCore-based Azure Cosmos DB for MongoDB, is not Amazon DocumentDB, is not the 2014-2017 Azure DocumentDB that became Cosmos DB, and is a different service from Azure Cosmos DB for MongoDB (RU). It never names the resource type, the CLI group, the Terraform resource, the billing unit or the host suffix, so it does not correct the mistakes that actually get made.
- None of the quickstarts carry a disambiguation note. `quickstart-cli` installs the `documentdb` extension and `quickstart-bicep` declares `Microsoft.DocumentDB/mongoClusters@2026-06-01`, but neither says "not `az cosmosdb`" or "not `databaseAccounts`", so a reader who arrived with the wrong model has nothing to collide with.
- `azure/templates/microsoft.documentdb/databaseaccounts` contains no mention of `mongoClusters`, vCore or Azure DocumentDB, and its `kind` enum offers `'GlobalDocumentDB' 'MongoDB' 'Parse'`, which reads as "this is how you make a MongoDB cluster".
- `az cosmosdb mongocluster` (`cosmosdb-preview` extension, preview) is still a live reference page with no deprecation notice and no pointer to `az documentdb mongocluster`. Learn search for "mongocluster CLI" returns both.

## Why it matters

We ran a five-stage agent-readiness pipeline over 100 Azure DocumentDB sample prompts with gpt-5-mini. Before any docs or skills were loaded, each run answered a short cold quiz. The same four questions came up in 118 runs across 101 samples. Not every run was scored on every question, so the rows below do not each add up to 118:

| Cold-quiz question | wrong | partly wrong | correct |
| --- | --- | --- | --- |
| Resource provider namespace and resource type of a cluster | 86 | 15 | 5 |
| Which Azure CLI command group creates and manages a cluster | 59 | 45 | 1 |
| How capacity is provisioned and billed | 78 | 16 | 15 |
| What a connection string looks like (scheme, host suffix, port, options) | 34 | 71 | 1 |

Typical wrong cold answers were `Microsoft.DocumentDB/databaseAccounts` with `mongodbDatabases` children, `az cosmosdb create` or `az cosmosdb mongocluster create`, request units, and `<account>.mongo.cosmos.azure.com:10255` with `replicaSet=globaldb`. 105 cold connection-string answers used the legacy host or port. In 369 of 418 scored confusions the model mixed this service up with Azure Cosmos DB for MongoDB (RU). Each of the 101 samples got at least one of the four facts wrong cold.

Downstream effect: the audit stage logged 57 doc-gap findings on this theme across 49 of the 100 samples. 78 samples shipped no infrastructure-as-code at all. The run policy forbade provisioning, but auditors repeatedly noted that authors also avoided IaC rather than risk using the wrong resource type. One sample (14-customer-complaint-classifier) shipped a `.env.example` with a Cosmos account host pattern. The Agent Kit's `azure-deployment` skill corrects all of this once it is installed. Learn, though, is part of the model's training data and is what the Learn MCP server returns, so Learn is where the wrong prior has to be contradicted.

## Proposed change

**Do not add a new "provision a cluster as code" page.** `quickstart-bicep` (M10 template, firewall rule, `az group delete`), `quickstart-terraform` (`azurerm_mongo_cluster`, `terraform destroy`) and `quickstart-cli` (`az extension add --name documentdb --upgrade`, `create --tier M30`, `list-connection-strings`, `delete`) already cover it. The gap is disambiguation, not provisioning.

### 1. New include: `includes/which-product-is-this.md`

Insert it directly under the H1 intro paragraph of `overview.md`, `quickstart-portal.md`, `quickstart-cli.md`, `quickstart-bicep.md`, `quickstart-terraform.md` and each language quickstart listed above. Suggested text:

> **Which product and resource type is this?**
> Azure DocumentDB (with MongoDB compatibility) was previously named *vCore-based Azure Cosmos DB for MongoDB*. It is **not** Azure Cosmos DB for MongoDB (RU), **not** Amazon DocumentDB, and **not** the 2014-2017 Azure DocumentDB that became Azure Cosmos DB. Examples written for those products use a different control plane and don't work here.
>
> | | Azure DocumentDB (this service) | Azure Cosmos DB for MongoDB (RU) |
> | --- | --- | --- |
> | ARM / Bicep resource type | `Microsoft.DocumentDB/mongoClusters` (latest stable API `2026-06-01`) | `Microsoft.DocumentDB/databaseAccounts` with `kind: 'MongoDB'` |
> | Azure CLI | `az documentdb mongocluster ...` (`documentdb` extension) | `az cosmosdb ...` |
> | Terraform | `azurerm_mongo_cluster` (azurerm 4.x) or AzAPI `Microsoft.DocumentDB/mongoClusters` | `azurerm_cosmosdb_account` |
> | Capacity and billing | Compute tier (M-series, for example M10, M30, M40; each tier maps to vCores and memory) plus storage, scaled independently. Monitor CPU, memory, IOPS and connections. | Request units per second (RU/s) |
> | Host and port | `<cluster>.mongocluster.cosmos.azure.com` with `mongodb+srv://` and no explicit port. A cluster that has replicas also has a global read-write host, `<cluster>.global.mongocluster.cosmos.azure.com`. | `<account>.mongo.cosmos.azure.com:10255` with `replicaSet=globaldb` |
>
> Connection strings have the following shape. Copy yours from **Connection strings** in the portal, or from `az documentdb mongocluster list-connection-strings`, and pass it to your MongoDB driver unchanged. Don't split the host and port, and don't add `replicaSet`.
>
> `mongodb+srv://<user>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`

### 2. Overview: move "Naming and history" up

Move the existing **Naming and history** section so it comes directly after the intro paragraph, and replace its four bullets with the include above. Its current content is correct, but readers don't see it at the bottom of the page.

### 3. One-line cross-links on the legacy pages (other repositories)

These pages aren't in nosql-docs-pr. File the changes with their owners:

- **ARM schema reference** (`MicrosoftDocs/azure-resource-manager-schema-reference-pr`, `arm-schema-ref/Microsoft.DocumentDB/databaseAccounts.md`), add a note at the top: "To deploy an **Azure DocumentDB (with MongoDB compatibility)** cluster, use [`Microsoft.DocumentDB/mongoClusters`](mongoclusters) instead. `databaseAccounts` with `kind: 'MongoDB'` creates an Azure Cosmos DB for MongoDB (RU) account."
- **`az cosmosdb mongocluster`** reference: this page is generated from the `cosmosdb-preview` extension's help text, so the change belongs in `Azure/azure-cli-extensions` (`src/cosmosdb-preview`). Add a group summary or a deprecation note: "For Azure DocumentDB clusters, use `az documentdb mongocluster` (`documentdb` extension)."
- **`Microsoft.DocumentDB/mongoClusters` reference**: the Azure Verified Module rows (Bicep `avm/res/document-db/mongo-cluster`, Terraform `terraform-azurerm-avm-res-documentdb-mongocluster`) and the AzAPI sample caption still say "Cosmos DB for MongoDB (vCore)". Rename them to "Azure DocumentDB (formerly Cosmos DB for MongoDB vCore)". The text comes from the AVM module metadata and the schema-reference sample sources.

### 4. `quickstart-bicep` and `quickstart-terraform` only: "Coming from a Cosmos DB template?"

After the template, add a short section with this mapping and a note on development defaults:

| Cosmos DB (RU) field | Azure DocumentDB equivalent |
| --- | --- |
| `Microsoft.DocumentDB/databaseAccounts`, `kind: 'MongoDB'` | `Microsoft.DocumentDB/mongoClusters` |
| `databaseAccounts/mongodbDatabases`, `.../collections` | No ARM child resource. Create databases and collections from the driver or `mongosh`. |
| `options.throughput` / `autoscaleSettings.maxThroughput` | `properties.compute.tier` (M10 ...) and `properties.storage.sizeGb` |
| `apiProperties.serverVersion` | `properties.serverVersion` (for example `'8.0'`) |
| `ipRules` | `Microsoft.DocumentDB/mongoClusters/firewallRules` child resource |
| `azurerm_cosmosdb_account` | `azurerm_mongo_cluster` |

"For development and samples, the template above uses a low-cost configuration: `M10`, 32 GiB storage, `shardCount: 1` and `highAvailability.targetMode: 'Disabled'`. For production, use a higher tier and set `targetMode` to `'ZoneRedundantPreferred'`."

## Evidence (run folders under `runs/`)

- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json`: cold answer `databaseAccounts` for Q01 and `az cosmosdb` for Q02. Its `doc-gaps.md` has an "Infra-as-code ambiguity" item.
- `runs/13-product-q-a-chatbot-rag/20261124-184527/02-readiness.json`: Q02 names `az cosmosdb mongocluster` as the source of the confusion, and the improvement asks for a cross-link on the `databaseAccounts` reference.
- `runs/19-care-coordination-multi-agent/20261124-195730/02-readiness.json` and `doc-gaps.md`: the legacy `mongo.cosmos.azure.com` / `replicaSet=globaldb` / port 10255 connection-string confusion.
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/doc-gaps.md`: resource type and CLI group disambiguation, rated high priority.
- `runs/14-customer-complaint-classifier/20261124-201931/doc-gaps.md`: the `.env.example` shipped with a Cosmos account host pattern.

## Verification

### 1. Already covered? partially_covered

The facts are on Learn, but they're spread out and nothing contrasts them with the RU control plane where an agent looks first.

- https://learn.microsoft.com/en-us/azure/documentdb/overview: "Naming and history" is the final section. It says the service "was previously named vCore-based Azure Cosmos DB for MongoDB" and that it and "Azure Cosmos DB for MongoDB (RU) are different services". It doesn't name `mongoClusters`, `az documentdb`, `azurerm_mongo_cluster`, vCore-versus-RU billing or the host suffix. The page does say "Pricing is based on vCores and storage".
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-bicep: uses `Microsoft.DocumentDB/mongoClusters@2026-06-01`, M10, 32 GB, `targetMode: 'Disabled'`, `serverVersion: '8.0'` and `az group delete`. It has no disambiguation note.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-cli: `az extension add --name documentdb --upgrade`, `az documentdb mongocluster create ... --tier M30`, `list-connection-strings`, `delete`. It has no "not az cosmosdb" note.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-terraform: `azurerm_mongo_cluster` (azurerm ~> 4.0), M10, `terraform destroy`. It has no note about `azurerm_cosmosdb_account`.
- https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/databaseaccounts: a grep of the fetched page found no occurrence of `mongoCluster`, vCore or "Azure DocumentDB". `kind` is `'GlobalDocumentDB''MongoDB''Parse'`.
- https://learn.microsoft.com/en-us/cli/azure/cosmosdb/mongocluster: live page, "part of the **cosmosdb-preview** extension", in preview, with no pointer to `az documentdb mongocluster`.
- The Agent Kit's `skills/azure-deployment/SKILL.md` and `references/bicep-cluster-template.md` / `terraform-cluster-template.md` have the correct identifiers. The kit isn't the target here, and it only helps after it's installed.
- This confirms the draft's point that a new provisioning page would duplicate what already exists. The proposed include, the relocation of the section and the cross-links aren't on Learn yet.

### 2. Is the premise true? confirmed (with corrections applied)

Checked against the pages above:
- `Microsoft.DocumentDB/mongoClusters`: the latest stable API is `2026-06-01` (newer ones are previews, `2026-06-15-preview`). `highAvailability.targetMode` takes `'Disabled' 'SameZone' 'ZoneRedundantPreferred'`. `storage.sizeGb` and `compute.tier` exist, and `firewallRules` is a child resource. Source: the mongoclusters template reference.
- The CLI group `az documentdb mongocluster` (documentdb extension), `azurerm_mongo_cluster` and wire-protocol versions 5.0 through 8.0 are all confirmed by the quickstarts and the Overview.
- Correction applied: the draft listed `<cluster>.global.mongocluster.cosmos.azure.com` as a general alternative host. It is the *global read-write* string that exists for clusters with replicas (Agent Kit `skills/high-availability/SKILL.md` line 34, `ha-cross-region-replica.md`, and Learn `how-to-cluster-replica`). The table now says so.
- Correction applied: the "Multi-document transactions" row (RU described as "Supported with RU limits") wasn't backed by a source and doesn't help with disambiguation, so it was removed. The table now has five rows.
- Correction applied: the tier list "M10, M20, M30 ... M200, vCores + RAM" was changed to the reference's own wording ("each tier maps to a virtual-core and memory size") with examples, so an unverified top tier isn't stated.
- Correction applied: the problem statement described wrong or partly-wrong counts as if they were counts of specific answers ("databaseAccounts in 101 of 118"). It now reports them as wrong or partly wrong with typical answers, and notes that not every run was scored on every question.
- Correction applied: the `cosmosdb-preview` CLI page and the AVM and AzAPI labels are owned outside nosql-docs-pr. The draft now names those repositories.
- The language quickstarts listed (nodejs JS/TS pivots, python, dotnet, java, go, rust) all exist in the documentdb TOC (https://learn.microsoft.com/en-us/azure/documentdb/toc.json).

### 3. Maintainer skeptic: confirmed

The draft names specific pages, a specific include file, the exact text and table, a section move and a mapping table, and the change is specific to Azure DocumentDB. A nosql-docs-pr maintainer would accept sections 1, 2 and 4 as written. Section 3 touches pages in other repositories: the ARM schema reference repo, `Azure/azure-cli-extensions` (`cosmosdb-preview`) and the AVM module metadata. The draft now marks those as separate filings, so the primary repository stays learn-docs and doesn't change.

## Finding ids

F0022, F0023, F0097, F0136, F0162, F0163, F0277, F0301, F0479, F0480, F0544, F0581, F0620, F0745, F0784, F0838, F0870, F0932, F0990, F1090, F1185, F1284, F1318, F1390, F1422, F1423, F1455, F1456, F1508, F1578, F1646, F1705, F1775, F1851, F1878, F1939, F2007, F2072, F2075, F2139, F2169, F2268, F2347, F2414, F2536, F2669, F2701, F2794, F2897, F2964, F3087, F3164, F3246, F3344, F3346, F3483, F3517
