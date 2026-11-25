---
id: K13
title: "State the vCore plus storage billing model (no request units) in AGENTS.md and azure-deployment"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 88
member_drafts:
  - 015-believes-capacity-is-ru-s-like-azure-cosmos-db-for-mongodb-r.md
open_questions: 2
---

# State the vCore plus storage billing model (no request units) in AGENTS.md and azure-deployment

## What happens today

The kit never says how Azure DocumentDB is billed. A search for `request unit`, `RU/s`, `RUs` or `autoscale` across the repository (commit 4f41c15) returns nothing.

- `AGENTS.md` line 3 lists "cluster M-tiers" only as a differentiator.
- `skills/azure-deployment/SKILL.md` Step 0.5 (lines 53-66) asks the agent to choose M10/M20 versus M30, and the parameter table near line 153 lists tiers, but neither says that the tier is the compute billing unit or that storage is billed separately.
- The only billing sentence in the kit is in `skills/high-availability/ha-cross-region-replica.md` line 184 (replicas pay for provisioned vCores and GiB/month of storage), which agents load only for replica work.

Separately, four content files and the Codex plugin manifest still use the pre-rename name "Cosmos DB for MongoDB vCore" or link into the old `cosmos-db/mongodb/vcore/` doc path. Those URLs still redirect to the Azure DocumentDB pages, so this is naming hygiene, not a broken-link fix, but it reinforces the idea that the service is a Cosmos DB RU product.

## Why it matters

In one 100-sample agent-readiness run (gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers), the cold question "How is capacity provisioned and billed?" was answered wrong or partly wrong in every recorded answer, across **88 of the 100 samples**. Each answer asserted RU/s provisioning with manual or autoscale throughput, and some added a serverless RU mode; most confused the service with Azure Cosmos DB for MongoDB (RU), a few with Azure Cosmos DB for NoSQL. Once the agent read `learn.microsoft.com/azure/documentdb/pricing-explained`, its answer was correct, so Learn is not the gap; the kit simply never states the fact.

The wrong belief leaked into the agent's code audits, which load the kit: RU and autoscale "best practices" appeared in roughly 46 of 221 audits, and about 32 checks were marked "violated" for things such as not logging `requestCharge` or lacking rate limiting "to avoid RU spikes". These are false findings for a `Microsoft.DocumentDB/mongoClusters` resource. The audit figures may be partly inflated by the experiment harness grading against RU-API practices (see Open question 2) and are provisional until a re-run after that harness fix. [needs SME confirmation] Generated code contained no RU settings, so today's damage is wrong advice and wrong audit verdicts rather than broken deployments. Counts come from a single experiment run and should be read as indicative.

The agent reads `AGENTS.md` on every task and Step 0.5 on every deployment, so one explicit statement in each gives the model something concrete to override its prior.

## Proposed change

**1. `AGENTS.md`, intro paragraph, after the sentence listing differentiators:**

> Azure DocumentDB is billed for **compute (cluster tier: vCores + memory, per shard) plus provisioned storage (GiB per month, per shard)**, scaled independently; tiers are Free, burstable M10/M20/M25, and M30 through M200. It has **no request units (RU/s), no autoscale RU, no provisioned-throughput API and no serverless capacity mode** - those belong to the separate Azure Cosmos DB for MongoDB (RU) and Azure Cosmos DB for NoSQL services. Do not carry over `Microsoft.DocumentDB/databaseAccounts` throughput settings, `requestCharge` instrumentation or 429/RU budgeting advice; the resource type here is `Microsoft.DocumentDB/mongoClusters`.

**2. `skills/azure-deployment/SKILL.md`, Step 0.5, after "Ask the user before anything else in Step 1...":**

> The tier you choose is the compute billing unit (vCores + RAM, billed per hour for each shard); storage (GiB per shard) is billed separately, scaled independently, and can be increased but not decreased. There is no RU/s, autoscale RU or serverless option to configure - if the user asks for "throughput" or "RUs", explain that capacity is the M-tier (plus shards and storage) and point them to [Compute and storage](https://learn.microsoft.com/azure/documentdb/compute-storage) and [Pricing explained](https://learn.microsoft.com/azure/documentdb/pricing-explained).

In the same file, add `M25` to the tier list in the parameter table (near line 153); `compute-storage` lists it as a burstable tier.

**3. Rename and relink (text only):**

| File | Line | Change |
|---|---|---|
| `skills/data-modeling/model-embed-vs-reference.md` | 7 | "Cosmos DB for MongoDB vCore rewards..." -> "Azure DocumentDB rewards..." |
| same | 49 | link -> `https://learn.microsoft.com/azure/documentdb/` (title "Azure DocumentDB documentation") |
| `skills/data-modeling/model-16mb-limit.md` | 7 | "BSON documents in Cosmos DB for MongoDB vCore have..." -> "BSON documents in Azure DocumentDB have..." |
| same | 45 | link -> `https://learn.microsoft.com/azure/documentdb/limitations` (title "Azure DocumentDB service limits and quotas") |
| `skills/data-modeling/model-denormalize-reads.md` | 39 | link -> `https://learn.microsoft.com/azure/documentdb/` |
| `CONTRIBUTING.md` | 19 | "...applies to Cosmos DB for MongoDB vCore." -> "...applies to Azure DocumentDB." |
| `.codex-plugin/plugin.json` | 31 | `websiteURL` -> `https://learn.microsoft.com/azure/documentdb/` |

Note: `/azure/documentdb/limits` returns 404; the correct page is `/azure/documentdb/limitations`. `CHANGELOG.md` line 220 is history and is left alone.

Optional: in `skills/connection/SKILL.md` line 91, retitle "Scenario: Serverless Environments (Azure Functions, AWS Lambda)" to "Scenario: Serverless app hosts (Azure Functions, AWS Lambda)" so "serverless" is not read as a database capacity mode.

No Learn change is requested: `overview`, `pricing-explained` and `compute-storage` already state the vCore plus storage model and that the service does not charge request units.

## Evidence

Run folders under `runs/` in the experiment repository:

- `02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` - cold answer asserts manual/autoscale RU and serverless; grounded answer corrects it from pricing-explained.
- `01-fraud-detection-with-vector-similarity/20261124-185817/02-readiness.json` - confused with Azure Cosmos DB for MongoDB (RU).
- `01-patient-record-summarizer-rag/20261124-192917/` (`02-readiness.json`, `05-audit.json`) - confused with Cosmos DB for NoSQL; audit imports RU monitoring and autoscale throughput from a Cosmos DB page.
- `01-unified-customer-profile-store/20261124-203120/05-audit.json` - "RequestCharge monitoring" check marked violated.
- `01-anti-money-laundering-pattern-detector/20261124-200112/05-audit.json` - "client-side rate limiting to avoid RU spikes" marked violated.

## Open questions

1. The proposed text adds details beyond "vCores plus storage, no RUs": billing per shard, per-hour compute, storage that can grow but not shrink, the Free tier and M25 as a burstable tier. These match the current Learn pages (`pricing-explained`, `compute-storage`), but please confirm they are current before merging, since the sentence will be read as authoritative by agents. [needs SME confirmation]
2. Part of the audit-stage noise (the roughly 32 false "violated" checks) may come from the experiment harness grading against RU-API practices, which is being fixed separately. The cold-answer failure (88 samples) stands on its own; the audit figures should not be quoted externally until a re-run after that harness fix. [needs SME confirmation]

## Source drafts

- 015-believes-capacity-is-ru-s-like-azure-cosmos-db-for-mongodb-r.md
