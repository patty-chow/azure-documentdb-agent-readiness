---
id: K13
title: "Add a 'Which DocumentDB is this?' naming block, state the vCore plus storage billing model (no request units), and retire stale 'Cosmos DB for MongoDB vCore' strings"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 96
member_drafts:
  - 015-believes-capacity-is-ru-s-like-azure-cosmos-db-for-mongodb-r.md
  - 110-believes-azure-documentdb-is-the-2014-2017-documentdb-that-b.md
merged_from:
  - K13
  - K14
open_questions: 4
---

# Add a "Which DocumentDB is this?" naming block, state the vCore plus storage billing model (no request units), and retire stale "Cosmos DB for MongoDB vCore" strings

One PR. Both member filings edit the same lines (the `AGENTS.md` intro, the head of `skills/azure-deployment/SKILL.md`, line 7 of `model-embed-vs-reference.md` and `model-16mb-limit.md`, line 39 of `model-denormalize-reads.md`), so they are filed together. The sample count of 96 is the number of distinct samples flagged on either quiz question in one experiment run (88 + 82, with 74 samples flagged on both); it is indicative, not exact.

## What happens today

The kit never tells an agent what Azure DocumentDB used to be called, which similarly named products it is *not*, or how it is billed (all checked at commit `4f41c15`).

- **No naming or lineage statement.** `README.md`, `AGENTS.md` and `skills/azure-deployment/SKILL.md` say only that the service is built on the open-source DocumentDB project. No file in the kit (CHANGELOG aside) contains "vCore-based", "formerly", "databaseAccounts", "request unit" or "Amazon DocumentDB".
- **No billing statement.** A search for `request unit`, `RU/s`, `RUs` or `autoscale` across the repository returns nothing.
  - `AGENTS.md` line 3 lists "cluster M-tiers" only as a differentiator.
  - `skills/azure-deployment/SKILL.md` Step 0.5 (lines 53-66) asks the agent to choose M10/M20 versus M30, and the parameter table at line 153 lists tiers (`M10`, `M20`, `M30`, `M40`, `M50`, `M60`, `M80`, `M200`; no `M25`), but neither says that the tier is the compute billing unit or that storage is billed separately.
  - The only billing sentence in the kit is in `skills/high-availability/ha-cross-region-replica.md` line 184 (replicas pay for provisioned vCores and GiB/month of storage), which agents load only for replica work.
- **Stale pre-rename name and legacy Learn paths** in content files and the Codex plugin manifest:
  - `skills/data-modeling/model-embed-vs-reference.md` lines 7 and 49
  - `skills/data-modeling/model-16mb-limit.md` lines 7 and 45
  - `skills/data-modeling/model-denormalize-reads.md` lines 7 ("in vCore") and 39
  - `CONTRIBUTING.md` lines 19 and 21
  - `.codex-plugin/plugin.json` lines 31 (`websiteURL`) and 38 ("Azure DocumentDB (MongoDB vCore)")

  The `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/...` links still resolve, but only through an HTTP 302 redirect to `/azure/documentdb/...`. This is naming hygiene rather than a broken-link fix, but the old strings teach the old name, rely on a redirect Learn does not promise to keep, and reinforce the idea that the service is a Cosmos DB RU product.
- **Non-canonical engine links.** Four links point at `github.com/microsoft/documentdb` instead of the canonical `github.com/documentdb/documentdb` that `README.md` and Learn use: `AGENTS.md` line 3, `skills/azure-deployment/SKILL.md` line 9, `skills/local-deployment/local-choose-deployment-method.md` line 45 and `skills/local-deployment/local-docker-compose-setup.md` line 73. (Links to `microsoft/documentdb-mcp` are correct and are not touched.)

## Why it matters

In one 100-sample agent-readiness run (gpt-5-mini building Azure DocumentDB sample apps with this kit plus the DocumentDB, Azure and Learn MCP servers), each run first answered cold quiz questions. Two of them failed in almost every sample, and both failures trace to the same missing statement of identity:

- **Billing (from K13): 88 of 100 samples.** "How is capacity provisioned and billed?" was answered wrong or partly wrong in every recorded answer. Each answer asserted RU/s provisioning with manual or autoscale throughput, and some added a serverless RU mode; most confused the service with Azure Cosmos DB for MongoDB (RU), a few with Azure Cosmos DB for NoSQL. Once the agent read `learn.microsoft.com/azure/documentdb/pricing-explained`, its answer was correct, so Learn is not the gap; the kit simply never states the fact.
  - The wrong belief leaked into the agent's code audits, which load the kit: RU and autoscale "best practices" appeared in roughly 46 of 221 audits, and about 32 checks were marked "violated" for things such as not logging `requestCharge` or lacking rate limiting "to avoid RU spikes". These are false findings for a `Microsoft.DocumentDB/mongoClusters` resource. The audit figures may be partly inflated by the experiment harness grading against RU-API practices (Open question 2) and are provisional until a re-run after that harness fix. [needs SME confirmation]
  - Generated code contained no RU settings, so today's damage is wrong advice and wrong audit verdicts rather than broken deployments.
- **Naming and lineage (from K14): 82 distinct samples** (93 flagged runs: 89 partly wrong, 1 wrong, 3 not verifiable). The question was "What was this service called before, and how does it relate to Azure Cosmos DB and to the open-source DocumentDB project?" The typical wrong answer: the 2014-2017 Azure DocumentDB became Azure Cosmos DB, so "Azure DocumentDB" today must be the MongoDB compatibility layer on the RU-based Cosmos DB account. Of the 93 flags, 77 were confusion with the legacy vCore naming, 14 with the open-source project, and 2 were unclassified.
  - Agents that grounded on this kit's `azure-deployment` skill still called the service "the precursor to Cosmos DB" and cited `microsoft/documentdb`, because the kit gives them nothing better.
  - Build risk recorded in the runs: reaching for `az cosmosdb`, `Microsoft.DocumentDB/databaseAccounts`, RU throughput settings and RU quickstarts instead of `az documentdb mongocluster`, `Microsoft.DocumentDB/mongoClusters` and vCore tier sizing.

Together the two failures cover 96 distinct samples. Learn already answers both correctly (the overview's "Naming and history" section, `pricing-explained`, `compute-storage`), so no Learn change is requested. The agent reads `AGENTS.md` on every task and `azure-deployment` Step 0.5 on every deployment, and the kit is loaded before the agent writes anything, so one explicit statement in each gives the model something concrete to override its prior. Counts come from a single experiment run and should be read as indicative.

## Proposed change (one PR, file by file)

### `AGENTS.md`

1. **Line 3:** change `https://github.com/microsoft/documentdb` to `https://github.com/documentdb/documentdb`.
2. **Directly after the first paragraph (line 3), before the Public Preview callout,** insert the naming block and the billing paragraph:

```markdown
## Which DocumentDB is this?

- **Formerly:** *vCore-based Azure Cosmos DB for MongoDB*. Existing clusters, connection strings and APIs did not change with the rename.
- **Resource type:** `Microsoft.DocumentDB/mongoClusters`, billed by vCore tier and storage, not request units. It is **not** *Azure Cosmos DB for MongoDB (RU)*, a different service on `Microsoft.DocumentDB/databaseAccounts`. `az cosmosdb` account commands and RU/throughput guidance do not apply here; use `az documentdb mongocluster` (documentdb CLI extension).
- **Not Amazon DocumentDB**, an unrelated AWS service.
- **Not the original Azure DocumentDB (2014-2017)**, which became Azure Cosmos DB. Today's Azure DocumentDB is built on the open-source, PostgreSQL-based [DocumentDB](https://github.com/documentdb/documentdb) engine.

See [Naming and history](https://learn.microsoft.com/azure/documentdb/overview#naming-and-history) on Microsoft Learn.

When a user or an older document says "Cosmos DB for MongoDB vCore", treat it as Azure DocumentDB. When they say "Cosmos DB for MongoDB" together with request units, `databaseAccounts` or `az cosmosdb`, that is a different service this kit does not cover; say so.

### How it is billed

Azure DocumentDB is billed for **compute (cluster tier: vCores + memory, per shard) plus provisioned storage (GiB per month, per shard)**, scaled independently; tiers are Free, burstable M10/M20/M25, and M30 through M200. It has **no request units (RU/s), no autoscale RU, no provisioned-throughput API and no serverless capacity mode** - those belong to the separate Azure Cosmos DB for MongoDB (RU) and Azure Cosmos DB for NoSQL services. Do not carry over `Microsoft.DocumentDB/databaseAccounts` throughput settings, `requestCharge` instrumentation or 429/RU budgeting advice; the resource type here is `Microsoft.DocumentDB/mongoClusters`.
```

(The billing paragraph was proposed by K13 as an addition to the intro paragraph; placing it under the naming block keeps the intro sentence short and puts both identity facts in one place. The detailed billing facts are subject to Open question 1.)

### `README.md`

**Insert after the intro paragraph (line 12):**

```markdown
### Which DocumentDB is this?

- **Formerly:** *vCore-based Azure Cosmos DB for MongoDB*. Existing clusters, connection strings and APIs did not change with the rename.
- **Resource type:** `Microsoft.DocumentDB/mongoClusters`, billed by vCore tier and storage, not request units. It is **not** *Azure Cosmos DB for MongoDB (RU)*, a different service on `Microsoft.DocumentDB/databaseAccounts`. `az cosmosdb` account commands and RU/throughput guidance do not apply here; use `az documentdb mongocluster` (documentdb CLI extension).
- **Not Amazon DocumentDB**, an unrelated AWS service.
- **Not the original Azure DocumentDB (2014-2017)**, which became Azure Cosmos DB. Today's Azure DocumentDB is built on the open-source, PostgreSQL-based [DocumentDB](https://github.com/documentdb/documentdb) engine.

See [Naming and history](https://learn.microsoft.com/azure/documentdb/overview#naming-and-history) on Microsoft Learn.
```

### `skills/azure-deployment/SKILL.md`

1. **Line 9 (head of the skill):** replace the second sentence ("Azure DocumentDB is the managed Azure service built on the open-source [`microsoft/documentdb`](...) engine.") with:

   > Azure DocumentDB (formerly *vCore-based Azure Cosmos DB for MongoDB*) is the managed Azure service built on the open-source [`documentdb/documentdb`](https://github.com/documentdb/documentdb) engine. It is **not** the RU-based *Azure Cosmos DB for MongoDB* `Microsoft.DocumentDB/databaseAccounts` resource; do not use `az cosmosdb` account commands or request-unit settings here.

2. **Step 0.5, after "Ask the user **before** anything else in Step 1. The answer drives every default. Never assume." (line 55):** add

   > The tier you choose is the compute billing unit (vCores + RAM, billed per hour for each shard); storage (GiB per shard) is billed separately, scaled independently, and can be increased but not decreased. There is no RU/s, autoscale RU or serverless option to configure - if the user asks for "throughput" or "RUs", explain that capacity is the M-tier (plus shards and storage) and point them to [Compute and storage](https://learn.microsoft.com/azure/documentdb/compute-storage) and [Pricing explained](https://learn.microsoft.com/azure/documentdb/pricing-explained).

3. **Parameter table, line 153:** add `M25` to the full tier list (`M10`, `M20`, `M25`, `M30`, `M40`, `M50`, `M60`, `M80`, `M200`); `compute-storage` lists it as a burstable tier. [needs SME confirmation, see Open question 1]

### `skills/connection/SKILL.md`

**Optional, line 91:** retitle "Scenario: Serverless Environments (Azure Functions, AWS Lambda)" to "Scenario: Serverless app hosts (Azure Functions, AWS Lambda)" so "serverless" is not read as a database capacity mode.

### `skills/data-modeling/model-embed-vs-reference.md`

- **Line 7:** "Cosmos DB for MongoDB vCore rewards..." -> "Azure DocumentDB rewards..."
- **Line 49:** link URL -> `https://learn.microsoft.com/azure/documentdb/`, link text "Data modeling in Azure DocumentDB". (K13 proposed the title "Azure DocumentDB documentation"; either works, since the target is the documentation landing page. Use "Azure DocumentDB documentation" if the maintainers prefer the text to match the page.)

### `skills/data-modeling/model-16mb-limit.md`

- **Line 7:** "BSON documents in Cosmos DB for MongoDB vCore have..." -> "BSON documents in Azure DocumentDB have..."
- **Line 45:** link URL -> `https://learn.microsoft.com/azure/documentdb/limitations`, link text "Azure DocumentDB service limits and quotas" (K14 proposed "Azure DocumentDB limits"; same target). Note: `/azure/documentdb/limits` returns 404; the correct page is `/azure/documentdb/limitations`.

### `skills/data-modeling/model-denormalize-reads.md`

- **Line 7:** "`$lookup` across sharded collections in vCore can be expensive..." -> "`$lookup` across sharded collections in Azure DocumentDB can be expensive..."
- **Line 39:** link URL `https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/` -> `https://learn.microsoft.com/azure/documentdb/` (link text "Modeling for read-heavy workloads" unchanged).

### `skills/local-deployment/local-choose-deployment-method.md`

- **Line 45:** link URL `https://github.com/microsoft/documentdb` -> `https://github.com/documentdb/documentdb`.

### `skills/local-deployment/local-docker-compose-setup.md`

- **Line 73:** link URL -> `https://github.com/documentdb/documentdb`, or the `ghcr.io/documentdb/documentdb/documentdb-local` package page, since the link is labelled "GHCR" (Open question 4).

### `CONTRIBUTING.md`

- **Line 19:** "...applies to Cosmos DB for MongoDB vCore." -> "...applies to Azure DocumentDB."
- **Line 21:** "Mark vCore-specific behavior" -> "Mark Azure DocumentDB-specific behavior".

### `.codex-plugin/plugin.json`

- **Line 31:** `websiteURL` -> `https://learn.microsoft.com/azure/documentdb/`
- **Line 38:** "Azure DocumentDB (MongoDB vCore)" -> "Azure DocumentDB"

### `CHANGELOG.md`

Leave existing history (including line 220) as is; add a new entry for this PR per `CONTRIBUTING.md`.

No Learn change is requested: `overview`, `pricing-explained` and `compute-storage` already state the naming history, the vCore plus storage model, and that the service does not charge request units.

## Evidence

Run folders under `runs/` in the experiment repository:

- `runs/02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` - cold billing answer asserts manual/autoscale RU and serverless; grounded answer corrects it from `pricing-explained`.
- `runs/01-fraud-detection-with-vector-similarity/20261124-185817/02-readiness.json` - billing answer confuses the service with Azure Cosmos DB for MongoDB (RU).
- `runs/01-patient-record-summarizer-rag/20261124-192917/` (`02-readiness.json`, `05-audit.json`) - confused with Cosmos DB for NoSQL; audit imports RU monitoring and autoscale throughput from a Cosmos DB page.
- `runs/01-unified-customer-profile-store/20261124-203120/` (`02-readiness.json`, `05-audit.json`) - naming answer risks following pre-2017 or Cosmos DB RU docs; audit marks a "RequestCharge monitoring" check violated.
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/05-audit.json` - "client-side rate limiting to avoid RU spikes" marked violated.
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json` - cold naming answer says DocumentDB was rebranded into Cosmos DB; the answer grounded on `azure-deployment/SKILL.md` still gives no former name and cites `microsoft/documentdb`.
- `runs/11-correspondent-banking-risk-screener/20261125-064705/02-readiness.json` - even the grounded answer calls DocumentDB the precursor to Cosmos DB.
- `runs/09-lead-scoring-agent/20261124-204408/02-readiness.json` - describes the service as a compatibility layer on Cosmos storage; build risk "pick RU-based practices and APIs".
- `runs/02-ai-powered-product-recommendations/20261124-181835/02-readiness.json` - wrong lineage; risk of wrong templates, CLI commands and API shapes.

Naming facts are taken from the Learn overview's "Naming and history" section and the Azure DocumentDB FAQ; billing facts from `pricing-explained` and `compute-storage`.

## Open questions

1. The billing text adds details beyond "vCores plus storage, no RUs": billing per shard, per-hour compute, storage that can grow but not shrink, the Free tier and M25 as a burstable tier. These match the current Learn pages (`pricing-explained`, `compute-storage`), but please confirm they are current before merging, since the sentences will be read as authoritative by agents. [needs SME confirmation]
2. Part of the audit-stage noise (the roughly 32 false "violated" checks) may come from the experiment harness grading against RU-API practices, which is being fixed separately. The cold-answer failures (88 and 82 samples) stand on their own; the audit figures should not be quoted externally until a re-run after that harness fix. [needs SME confirmation]
3. Is `github.com/documentdb/documentdb` the link the team wants agents to use for the engine everywhere, with `microsoft/documentdb` treated as legacy?
4. For `local-docker-compose-setup.md` line 73, should the link go to the engine repository or to the GHCR `documentdb-local` package page?

The naming statements themselves (from K14) were not flagged as needing SME confirmation; each mirrors Learn.

Note on counts: K14's source draft quoted 68 samples from a clustered subset whose finding ids cannot be joined back to runs; 82 is a recount of all Q14 records in the experiment's findings file. The merged 96 is the union of Q05 (88) and Q14 (82) samples in that file, one run.

## Source drafts

- 015-believes-capacity-is-ru-s-like-azure-cosmos-db-for-mongodb-r.md
- 110-believes-azure-documentdb-is-the-2014-2017-documentdb-that-b.md

## Merged from

- K13 - State the vCore plus storage billing model (no request units) in AGENTS.md and azure-deployment (needs_sme, P1, 88 samples)
- K14 - Add a "Which DocumentDB is this?" naming block and retire stale "Cosmos DB for MongoDB vCore" strings (ready, P1, 82 samples)
