---
id: K14
title: "Add a 'Which DocumentDB is this?' naming block and retire stale 'Cosmos DB for MongoDB vCore' strings"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 82
member_drafts:
  - 110-believes-azure-documentdb-is-the-2014-2017-documentdb-that-b.md
open_questions: 2
---

# Add a "Which DocumentDB is this?" naming block and retire stale "Cosmos DB for MongoDB vCore" strings

## What happens today

The kit never tells an agent what Azure DocumentDB used to be called or which similarly named products it is *not*. `README.md`, `AGENTS.md` and `skills/azure-deployment/SKILL.md` say only that it is built on the open-source DocumentDB project. No file in the kit (CHANGELOG aside) contains "vCore-based", "formerly", "databaseAccounts", "request unit" or "Amazon DocumentDB".

Meanwhile several files still use the pre-rename name or legacy Learn paths (checked at commit `4f41c15`):

- `skills/data-modeling/model-embed-vs-reference.md` lines 7 and 49
- `skills/data-modeling/model-16mb-limit.md` lines 7 and 45
- `skills/data-modeling/model-denormalize-reads.md` lines 7 and 39
- `CONTRIBUTING.md` lines 19 and 21
- `.codex-plugin/plugin.json` lines 31 (`websiteURL`) and 38 ("Azure DocumentDB (MongoDB vCore)")

The `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/...` links still resolve, but only through an HTTP 302 redirect to `/azure/documentdb/...`. They teach the old name and rely on a redirect Learn does not promise to keep.

Separately, four links point the engine at `github.com/microsoft/documentdb` instead of the canonical `github.com/documentdb/documentdb` that `README.md` and Learn use: `AGENTS.md` line 3, `skills/azure-deployment/SKILL.md` line 9, `skills/local-deployment/local-choose-deployment-method.md` line 45 and `skills/local-deployment/local-docker-compose-setup.md` line 73. (Links to `microsoft/documentdb-mcp` are correct and are not touched.)

## Why it matters

We ran an agent-readiness experiment: 100 Azure DocumentDB sample apps built by an agent (gpt-5-mini) with this kit plus the DocumentDB, Azure and Learn MCP servers installed. Before building, each run answered a cold quiz question: "What was this service called before, and how does it relate to Azure Cosmos DB and to the open-source DocumentDB project?" The answer was flagged in 93 runs covering **82 distinct samples** (89 partly wrong, 1 wrong, 3 not verifiable). Counts come from one experiment run and are indicative, not exact.

The typical wrong answer: the 2014-2017 Azure DocumentDB became Azure Cosmos DB, so "Azure DocumentDB" today must be the MongoDB compatibility layer on the RU-based Cosmos DB account. Of the 93 flags, 77 were confusion with the legacy vCore naming, 14 with the open-source project, and 2 were unclassified. Agents that grounded on this kit's `azure-deployment` skill still called the service "the precursor to Cosmos DB" and cited `microsoft/documentdb`, because the kit gives them nothing better. The build risk recorded in the runs: reaching for `az cosmosdb`, `Microsoft.DocumentDB/databaseAccounts`, RU throughput settings and RU quickstarts instead of `az documentdb mongocluster`, `Microsoft.DocumentDB/mongoClusters` and vCore tier sizing.

Learn's overview already has a "Naming and history" section that answers this correctly. The kit is loaded before the agent writes anything, so it is the right place to carry that answer.

## Proposed change (one PR)

### 1. `README.md`: insert after the intro paragraph (line 12)

```markdown
### Which DocumentDB is this?

- **Formerly:** *vCore-based Azure Cosmos DB for MongoDB*. Existing clusters, connection strings and APIs did not change with the rename.
- **Resource type:** `Microsoft.DocumentDB/mongoClusters`, billed by vCore tier and storage, not request units. It is **not** *Azure Cosmos DB for MongoDB (RU)*, a different service on `Microsoft.DocumentDB/databaseAccounts`. `az cosmosdb` account commands and RU/throughput guidance do not apply here; use `az documentdb mongocluster` (documentdb CLI extension).
- **Not Amazon DocumentDB**, an unrelated AWS service.
- **Not the original Azure DocumentDB (2014-2017)**, which became Azure Cosmos DB. Today's Azure DocumentDB is built on the open-source, PostgreSQL-based [DocumentDB](https://github.com/documentdb/documentdb) engine.

See [Naming and history](https://learn.microsoft.com/azure/documentdb/overview#naming-and-history) on Microsoft Learn.
```

### 2. `AGENTS.md`

- Line 3: change `https://github.com/microsoft/documentdb` to `https://github.com/documentdb/documentdb`.
- Directly after the first paragraph, insert the same block headed `## Which DocumentDB is this?`, followed by:

```markdown
When a user or an older document says "Cosmos DB for MongoDB vCore", treat it as Azure DocumentDB. When they say "Cosmos DB for MongoDB" together with request units, `databaseAccounts` or `az cosmosdb`, that is a different service this kit does not cover; say so.
```

### 3. `skills/azure-deployment/SKILL.md`, line 9

Replace the second sentence with:

> Azure DocumentDB (formerly *vCore-based Azure Cosmos DB for MongoDB*) is the managed Azure service built on the open-source [`documentdb/documentdb`](https://github.com/documentdb/documentdb) engine. It is **not** the RU-based *Azure Cosmos DB for MongoDB* `Microsoft.DocumentDB/databaseAccounts` resource; do not use `az cosmosdb` account commands or request-unit settings here.

### 4. Retarget stale strings and links

| File | Change |
|---|---|
| `skills/data-modeling/model-embed-vs-reference.md` | L7 "Cosmos DB for MongoDB vCore rewards" -> "Azure DocumentDB rewards"; L49 text "Data modeling in Azure DocumentDB", URL `https://learn.microsoft.com/azure/documentdb/` |
| `skills/data-modeling/model-16mb-limit.md` | L7 "in Cosmos DB for MongoDB vCore" -> "in Azure DocumentDB"; L45 text "Azure DocumentDB limits", URL `https://learn.microsoft.com/azure/documentdb/limitations` |
| `skills/data-modeling/model-denormalize-reads.md` | L7 "in vCore" -> "in Azure DocumentDB"; L39 URL `https://learn.microsoft.com/azure/documentdb/` |
| `CONTRIBUTING.md` | L19 "Cosmos DB for MongoDB vCore" -> "Azure DocumentDB"; L21 "Mark vCore-specific behavior" -> "Mark Azure DocumentDB-specific behavior" |
| `.codex-plugin/plugin.json` | L31 `websiteURL` -> `https://learn.microsoft.com/azure/documentdb/`; L38 "Azure DocumentDB (MongoDB vCore)" -> "Azure DocumentDB" |
| `skills/local-deployment/local-choose-deployment-method.md` | L45 URL -> `https://github.com/documentdb/documentdb` |
| `skills/local-deployment/local-docker-compose-setup.md` | L73 URL -> `https://github.com/documentdb/documentdb` (or the `ghcr.io/documentdb/documentdb/documentdb-local` package page, since the link is labelled "GHCR") |

Leave `CHANGELOG.md` history as is, and add a new CHANGELOG entry per `CONTRIBUTING.md`.

## Evidence

Run folders from the experiment (field `confusions[Q14]` in each file):

- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: cold answer says DocumentDB was rebranded into Cosmos DB; the answer grounded on `azure-deployment/SKILL.md` still gives no former name and cites `microsoft/documentdb`.
- `runs/09-lead-scoring-agent/20261124-204408/02-readiness.json`: describes the service as a compatibility layer on Cosmos storage; build risk "pick RU-based practices and APIs".
- `runs/11-correspondent-banking-risk-screener/20261125-064705/02-readiness.json`: even the grounded answer calls DocumentDB the precursor to Cosmos DB.
- `runs/02-ai-powered-product-recommendations/20261124-181835/02-readiness.json`: wrong lineage; risk of wrong templates, CLI commands and API shapes.
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json`: risk of following pre-2017 or Cosmos DB RU docs.

Naming facts are taken from the Learn overview's "Naming and history" section and the Azure DocumentDB FAQ.

## Open questions

No claim in this PR was flagged as needing SME confirmation; every naming statement mirrors Learn. Two maintainer questions remain:

1. Is `github.com/documentdb/documentdb` the link the team wants agents to use for the engine everywhere, with `microsoft/documentdb` treated as legacy?
2. For `local-docker-compose-setup.md` line 73, should the link go to the engine repository or to the GHCR `documentdb-local` package page?

Note on counts: the source draft quoted 68 samples from a clustered subset whose finding ids cannot be joined back to runs. The 82 above is a recount of all Q14 records in the experiment's findings file.

## Source drafts

- 110-believes-azure-documentdb-is-the-2014-2017-documentdb-that-b.md
