---
title: "State the vCore + storage billing model (no RUs) in AGENTS.md and azure-deployment; drop remaining \"Cosmos DB for MongoDB vCore\" names/links"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 88
findings: 92
bucket: confusion-Q05
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# State the vCore + storage billing model (no RUs) in AGENTS.md and azure-deployment; drop remaining "Cosmos DB for MongoDB vCore" names/links

## What happens today

The kit never says how Azure DocumentDB is billed. `grep -rniE 'request unit|\bRU/s\b|\bRUs\b|autoscale'` over the repo (commit 4f41c15) returns nothing. `AGENTS.md` line 3 mentions "cluster M-tiers" only in a list of differentiators; `skills/azure-deployment/SKILL.md` Step 0.5 (lines 53-66) tells the agent to pick M10/M20 vs M30, and the parameter table at line 153 lists the tiers, but neither ever says that the tier *is* the compute billing unit and that storage is billed separately. The only billing sentence in the kit is in `skills/high-availability/ha-cross-region-replica.md` line 184 (replicas "pay for its provisioned vCores and GiB/month of storage"), which agents only load for replica work. The Bicep/Terraform references expose `computeTier` + `storageSizeGb` with no RU field, so a builder following the deployment skill cannot mis-provision - but only samples that create a cluster ever load that skill.

At the same time, four content files plus the Codex plugin manifest still use the pre-rename product name or link into the old Cosmos DB doc path, which reinforces the "this is a Cosmos DB product" association. (The old `cosmos-db/mongodb/vcore/` URLs still resolve: they redirect to `learn.microsoft.com/azure/documentdb/` and `/documentdb/limitations`, so this is a naming fix, not a broken-link fix.)

- `skills/data-modeling/model-embed-vs-reference.md` line 7 ("Cosmos DB for MongoDB vCore rewards designs...") and line 49 (link to `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`)
- `skills/data-modeling/model-16mb-limit.md` line 7 and line 45 (link to `.../cosmos-db/mongodb/vcore/limits`)
- `skills/data-modeling/model-denormalize-reads.md` line 39 (link to `.../cosmos-db/mongodb/vcore/`)
- `CONTRIBUTING.md` line 19 ("...unless it materially applies to Cosmos DB for MongoDB vCore")
- `.codex-plugin/plugin.json` line 31 (`websiteURL` points at `.../cosmos-db/mongodb/vcore/`)

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini, this kit + DocumentDB/Azure/Learn MCP servers), the cold-quiz question "How is capacity provisioned and billed?" was answered wrong or partly wrong in **92 of 92 recorded answers across 88 samples**. Every one asserted RU/s provisioning with autoscale/manual throughput and, in a minority, a serverless RU mode; 87 conflated the service with Azure Cosmos DB for MongoDB (RU), 5 with Cosmos DB for NoSQL. The grounded answer was correct every time once the agent read `learn.microsoft.com/azure/documentdb/pricing-explained`, so the Learn docs are not the gap.

The prior did not stay in the quiz. The audit stage, which loads the kit, imported RU/autoscale "best practices" in **46 of 221 audits** (sourced from `learn.microsoft.com/azure/cosmos-db/...` pages or labelled `prior_knowledge`) and marked **32 checks as "violated"** for things like not logging `requestCharge`, not "documenting recommended RU provisioning for bulk ingestion", or lacking "client-side rate limiting to avoid RU spikes". Those are false findings for a mongoClusters resource; a human reviewer would have to recognise and discard each one. Build-stage events contain no RU text in generated code, so the damage today is wrong advice and wrong audit verdicts, not broken deployments.

The fix is cheap because the agent already reads AGENTS.md on every task and Step 0.5 on every deployment; one sentence in each gives the model something concrete to override its prior with.

## Proposed change

**1. `AGENTS.md`, intro paragraph (after the sentence listing differentiators):**

> Azure DocumentDB is billed for **compute (cluster tier: vCores + memory, per shard) plus provisioned storage (GiB per month, per shard)**, scaled independently; tiers are Free, burstable M10/M20/M25, and M30 through M200. It has **no request units (RU/s), no autoscale RU, no provisioned-throughput API and no serverless capacity mode** - those belong to the separate Azure Cosmos DB for MongoDB (RU) and Azure Cosmos DB for NoSQL services. Do not carry over `Microsoft.DocumentDB/databaseAccounts` throughput settings, `requestCharge` instrumentation or 429/RU budgeting advice; the resource type here is `Microsoft.DocumentDB/mongoClusters`.

**2. `skills/azure-deployment/SKILL.md`, Step 0.5, after "Ask the user before anything else in Step 1...":**

> The tier you choose is the compute billing unit (vCores + RAM, billed per hour for each shard); storage (GiB per shard) is billed separately, scaled independently, and can be increased but not decreased. There is no RU/s, autoscale RU or serverless option to configure - if the user asks for "throughput" or "RUs", explain that capacity is the M-tier (plus shards and storage) and point them to [Compute and storage](https://learn.microsoft.com/azure/documentdb/compute-storage) and [Pricing explained](https://learn.microsoft.com/azure/documentdb/pricing-explained).

Optionally also add `M25` to the tier list in the line-153 parameter table, since `compute-storage` lists it as a burstable tier.

**3. Rename and relink (text-only):**

| File | Line | Change |
|---|---|---|
| `skills/data-modeling/model-embed-vs-reference.md` | 7 | "Cosmos DB for MongoDB vCore rewards..." -> "Azure DocumentDB rewards..." |
| same | 49 | link -> `https://learn.microsoft.com/azure/documentdb/` (title "Azure DocumentDB documentation") |
| `skills/data-modeling/model-16mb-limit.md` | 7 | "BSON documents in Cosmos DB for MongoDB vCore have..." -> "BSON documents in Azure DocumentDB have..." |
| same | 45 | link -> `https://learn.microsoft.com/azure/documentdb/limitations` (title "Azure DocumentDB service limits and quotas") |
| `skills/data-modeling/model-denormalize-reads.md` | 39 | link -> `https://learn.microsoft.com/azure/documentdb/` |
| `CONTRIBUTING.md` | 19 | "...applies to Cosmos DB for MongoDB vCore." -> "...applies to Azure DocumentDB." |
| `.codex-plugin/plugin.json` | 31 | `websiteURL` -> `https://learn.microsoft.com/azure/documentdb/` |

Optionally, in `skills/connection/SKILL.md` line 91, retitle "Scenario: Serverless Environments (Azure Functions, AWS Lambda)" to "Scenario: Serverless *app hosts* (Azure Functions, AWS Lambda)" so "serverless" is not read as a database capacity mode. Not required.

No Learn-docs change is requested: `overview` already says "Pricing is based on vCores and storage, which you scale independently" and that Azure DocumentDB and Azure Cosmos DB for MongoDB (RU) are different services; `pricing-explained` says the service "doesn't charge request units"; `compute-storage` lists the M-tier table.

## Evidence (run folders under azure-documentdb-agent-readiness/runs/)

- `02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` - confusions[Q05]: cold answer asserts manual/autoscale RU and serverless; grounded answer corrects via pricing-explained.
- `01-fraud-detection-with-vector-similarity/20261124-185817/02-readiness.json` - confusions[Q05], confused_with azure_cosmos_db_for_mongodb_ru.
- `01-patient-record-summarizer-rag/20261124-192917/02-readiness.json` and `05-audit.json` - Q05 confused with Cosmos DB for NoSQL; audit imports "RU monitoring / autoscale throughput" practice from a cosmos-db page.
- `01-unified-customer-profile-store/20261124-203120/05-audit.json` - check "RequestCharge monitoring" marked violated.
- `01-anti-money-laundering-pattern-detector/20261124-200112/05-audit.json` - check "Client-side rate limiting ... avoid RU spikes" marked violated, sourced from a cosmos-db vector-search page.

## Verification

### 1. Already covered? - confirmed (not covered in the target)

The kit clone (Azure/documentdb-agent-kit, commit 4f41c15, 2026-11-23) has no occurrence of "request unit", "RU/s", "RUs" or "autoscale" in any file. `AGENTS.md` line 3 only lists "cluster M-tiers" as a differentiator. `skills/azure-deployment/SKILL.md` Step 0.5 (lines 53-66) and line 153 list tiers without a billing statement. The only billing text is `skills/high-availability/ha-cross-region-replica.md:184` ("you pay for its provisioned vCores and GiB/month of storage"), scoped to replicas. The knowledge-base (`knowledge-base/kb.json`) has no pricing/billing entry. microsoft/documentdb-mcp has no pricing/RU text (not the right home anyway). The five stale name/link sites were confirmed by grep, plus a sixth (`.codex-plugin/plugin.json:31`) the draft missed; `CHANGELOG.md:220` is history and correctly left alone. Learn already covers the fact (see check 2), and the draft correctly asks for no Learn change.

### 2. Is the premise true? - confirmed, with corrections applied

- https://learn.microsoft.com/en-us/azure/documentdb/pricing-explained: "pricing has only two parts: compute and storage... Azure DocumentDB doesn't charge request units". Compute is billed "Per hour, by cluster tier (vCores and memory), for each shard"; storage "Per GiB per month, for the storage you provision on each shard". Storage can be increased, not decreased. A Free tier exists.
- https://learn.microsoft.com/en-us/azure/documentdb/compute-storage: tier table M10, M20, M25 (burstable), M30, M40, M50, M60, M80, M200; "You can select the compute and storage settings independently. The selected compute and storage values apply to each shard."
- https://learn.microsoft.com/en-us/azure/documentdb/overview: "Pricing is based on vCores and storage, which you scale independently"; "Azure DocumentDB (with MongoDB compatibility) and Azure Cosmos DB for MongoDB (RU) are different services"; formerly "vCore-based Azure Cosmos DB for MongoDB".
- Corrections applied: (a) the draft's proposed link `learn.microsoft.com/azure/documentdb/limits` returns 404; the limits page is `/azure/documentdb/limitations` ("Service limits and Quotas Reference", "16 MB per document") - fixed in the table. (b) The draft called the old Cosmos path "retired"; the old `cosmos-db/mongodb/vcore/` and `.../vcore/limits` URLs actually 302-redirect to the DocumentDB pages, so the change is reframed as naming hygiene, not a broken link. (c) The AGENTS.md sentence said "M10-M200", omitting M25 and Free; now lists Free, burstable M10/M20/M25 and M30-M200, and adds per-hour/per-shard billing and storage-can't-shrink. (d) Added the missed `.codex-plugin/plugin.json` websiteURL. (e) Replaced the non-existent link title "Data modeling in Azure DocumentDB" with a neutral title for the documentation landing page.

### 3. Maintainer skeptic - confirmed

As kit maintainer I would accept this: it names exact files and lines, gives the exact sentences to add, is DocumentDB-specific (the RU vs vCore confusion with sibling Cosmos DB services is the product's best-known naming trap), and is backed by a large, consistent failure signal (92/92 cold answers, 32 false "violated" audit checks). The text edits are small and low-risk. Learn already states the fact, so the kit is the right repository; the MCP server is not.

## Finding ids

- F0004
- F0040
- F0072
- F0108
- F0148
- F0179
- F0258
- F0287
- F0315
- F0349
- F0421
- F0456
- F0525
- F0557
- F0597
- F0726
- F0764
- F0793
- F0824
- F0847
- F0888
- F0917
- F0943
- F0969
- F1000
- F1040
- F1074
- F1102
- F1131
- F1160
- F1198
- F1224
- F1259
- F1298
- F1338
- F1369
- F1401
- F1434
- F1487
- F1522
- F1557
- F1624
- F1656
- F1683
- F1717
- F1753
- F1789
- F1826
- F1951
- F1982
- F2017
- F2052
- F2083
- F2121
- F2153
- F2185
- F2243
- F2288
- F2325
- F2358
- F2426
- F2459
- F2486
- F2517
- F2551
- F2590
- F2620
- F2648
- F2683
- F2712
- F2746
- F2778
- F2805
- F2875
- F2908
- F2975
- F3013
- F3041
- F3110
- F3176
- F3226
- F3257
- F3297
- F3360
- F3393
- F1860
- F1890
- F2388
- F3072
- F3144
- F3425
- F3498
