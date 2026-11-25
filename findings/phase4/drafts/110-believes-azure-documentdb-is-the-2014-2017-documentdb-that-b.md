---
title: "Add a \"Which DocumentDB is this?\" naming block and retire stale \"Cosmos DB for MongoDB vCore\" strings in the Agent Kit"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 68
findings: 72
bucket: confusion-Q14
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add a "Which DocumentDB is this?" naming block; retire stale "Cosmos DB for MongoDB vCore" strings

## What happens today

The kit never tells an agent what this product used to be called or which neighbouring products it is *not*. `README.md` (line 12) and `AGENTS.md` (line 3) say only that Azure DocumentDB is "built on the open-source DocumentDB project". `skills/azure-deployment/SKILL.md` (line 9) says the same. Nowhere in the kit do the strings "vCore-based Azure Cosmos DB for MongoDB", "databaseAccounts", "request unit" or "Amazon DocumentDB" appear.

At the same time, several files still use the pre-rename framing:

- `skills/data-modeling/model-embed-vs-reference.md` line 7 opens "Cosmos DB for MongoDB vCore rewards designs ..."; line 49 links `https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`.
- `skills/data-modeling/model-16mb-limit.md` line 7 opens "BSON documents in Cosmos DB for MongoDB vCore have ..."; line 45 links `https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/limits`.
- `skills/data-modeling/model-denormalize-reads.md` line 7 says "`$lookup` across sharded collections in vCore ..."; line 39 links `https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`.
- `CONTRIBUTING.md` lines 19 and 21: "avoid generic MongoDB advice unless it materially applies to Cosmos DB for MongoDB vCore" / "Mark vCore-specific behavior explicitly".

Those `cosmos-db/mongodb/vcore/` URLs are legacy paths: they currently redirect (HTTP 302) and serve pages whose canonical URL is `learn.microsoft.com/azure/documentdb/` and `.../documentdb/limitations`. They still resolve today, but they teach agents the old product name and depend on a redirect Microsoft Learn does not promise to keep.

Separately, `AGENTS.md` line 3, `skills/azure-deployment/SKILL.md` line 9, `skills/local-deployment/local-choose-deployment-method.md` line 45 and `skills/local-deployment/local-docker-compose-setup.md` line 73 link the engine as `https://github.com/microsoft/documentdb`, while `README.md` and Microsoft Learn use the canonical `https://github.com/documentdb/documentdb`.

## Why it matters

In an agent-readiness experiment (100 Azure DocumentDB sample prompts, gpt-5-mini, this kit installed plus the DocumentDB/Azure/Learn MCP servers), the cold-quiz question "What was this service called before, and how does it relate to Azure Cosmos DB and to the open-source DocumentDB project?" was answered wrongly in 93 of 118 attempts, hitting **68 of the 100 samples**. The model's prior in nearly every case: Microsoft's 2014-2017 DocumentDB was rebranded Azure Cosmos DB, and "Azure DocumentDB" today is "the MongoDB-compatible API/compatibility layer on top of Cosmos DB" (the RU-based `databaseAccounts` product). **0 of 118 cold answers produced "vCore-based"**, and only 4 mentioned "Azure Cosmos DB for MongoDB vCore" at all.

The grounded re-answers recovered the correct lineage only when they reached the Learn overview's "Naming and history" section (54 grounded answers say "vCore-based"). The 10 answers that grounded on *this kit's* `azure-deployment` skill still described the service as "the precursor to Cosmos DB" and cited `microsoft/documentdb`, because the kit gives them nothing better. The audits list the resulting build risk repeatedly: builders reaching for `az cosmosdb`, `Microsoft.DocumentDB/databaseAccounts`, RU throughput settings and Cosmos DB RU quickstarts instead of `az documentdb mongocluster` / `Microsoft.DocumentDB/mongoClusters` and M-tier vCore sizing.

The kit is the one artifact that is loaded *before* the agent writes anything, so it is the right place to pre-empt the prior. Learn already has the content; the kit just needs to carry it.

## Proposed change (one PR)

### 1. `README.md` — insert after the intro paragraph (line 12)

```markdown
### Which DocumentDB is this?

- **Formerly:** *vCore-based Azure Cosmos DB for MongoDB*. Existing clusters, connection strings and APIs did not change with the rename.
- **Resource type:** `Microsoft.DocumentDB/mongoClusters`, billed by vCore tier (M-series) and storage. It is **not** *Azure Cosmos DB for MongoDB (RU)*, which is a different service on `Microsoft.DocumentDB/databaseAccounts` with request-unit billing — `az cosmosdb` account commands and RU/throughput guidance do not apply here; use `az documentdb mongocluster`.
- **Not Amazon DocumentDB**, which is an unrelated AWS service.
- **Not the original Azure DocumentDB (2014–2017)**, which became Azure Cosmos DB. Today's Azure DocumentDB is built on the open-source, PostgreSQL-based [DocumentDB](https://github.com/documentdb/documentdb) engine.

See [Naming and history](https://learn.microsoft.com/azure/documentdb/overview#naming-and-history) on Microsoft Learn.
```

### 2. `AGENTS.md` — insert the same block (headed `## Which DocumentDB is this?`) directly after the first paragraph, and add one line to the routing guidance

```markdown
When a user or an older document says "Cosmos DB for MongoDB vCore", treat it as Azure DocumentDB. When they say "Cosmos DB for MongoDB" with request units, `databaseAccounts`, or `az cosmosdb`, that is a different service this kit does not cover — say so.
```

### 3. `skills/azure-deployment/SKILL.md` — extend the intro sentence (line 9)

Replace:

> Azure DocumentDB is the managed Azure service built on the open-source [`microsoft/documentdb`](https://github.com/microsoft/documentdb) engine.

with:

> Azure DocumentDB (formerly *vCore-based Azure Cosmos DB for MongoDB*) is the managed Azure service built on the open-source [`documentdb/documentdb`](https://github.com/documentdb/documentdb) engine. It is **not** the RU-based *Azure Cosmos DB for MongoDB* `Microsoft.DocumentDB/databaseAccounts` resource — do not use `az cosmosdb` account commands or request-unit settings here.

### 4. Retarget stale strings and links

| File | Change |
|---|---|
| `skills/data-modeling/model-embed-vs-reference.md` | line 7: "Cosmos DB for MongoDB vCore rewards" -> "Azure DocumentDB rewards"; line 49: link text "Data modeling in Azure DocumentDB", URL `https://learn.microsoft.com/azure/documentdb/` |
| `skills/data-modeling/model-16mb-limit.md` | line 7: "BSON documents in Cosmos DB for MongoDB vCore" -> "BSON documents in Azure DocumentDB"; line 45: link text "Azure DocumentDB limits", URL `https://learn.microsoft.com/azure/documentdb/limitations` |
| `skills/data-modeling/model-denormalize-reads.md` | line 7: "across sharded collections in vCore" -> "across sharded collections in Azure DocumentDB"; line 39: URL `https://learn.microsoft.com/azure/documentdb/` |
| `CONTRIBUTING.md` | line 19: "Cosmos DB for MongoDB vCore" -> "Azure DocumentDB"; line 21: "Mark vCore-specific behavior" -> "Mark Azure DocumentDB-specific behavior" |

### 5. Cosmetic: canonical engine repo URL

Change `https://github.com/microsoft/documentdb` to `https://github.com/documentdb/documentdb` in `AGENTS.md` (line 3), `skills/azure-deployment/SKILL.md` (line 9, covered above), `skills/local-deployment/local-choose-deployment-method.md` (line 45) and `skills/local-deployment/local-docker-compose-setup.md` (line 73; that link is labelled "DocumentDB local image on GHCR", so it can alternatively point at the `ghcr.io/documentdb/documentdb/documentdb-local` package page the kit's other local-deployment rules already use). `README.md` already uses the canonical URL. (`CHANGELOG.md` line 220 is historical and should stay as is.)

Add a CHANGELOG entry per CONTRIBUTING.md.

## Evidence (run folders from the experiment)

- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json` — `confusions[Q14]`: cold answer "DocumentDB ... was rebranded and expanded into Azure Cosmos DB"; grounded on `skills/azure-deployment/SKILL.md`, still no former name, cites `microsoft/documentdb`.
- `runs/09-lead-scoring-agent/20261124-204408/02-readiness.json` — `confusions[Q14]`: cold answer "The Cosmos MongoDB API is a compatibility layer ... on top of Cosmos storage"; build risk "pick RU-based practices and APIs".
- `runs/11-correspondent-banking-risk-screener/20261125-064705/02-readiness.json` — `confusions[Q14]`: even the grounded answer says "Historically 'DocumentDB' was the precursor to Cosmos DB" because the kit gives nothing else.
- `runs/02-ai-powered-product-recommendations/20261124-181835/02-readiness.json` — `confusions[Q14]`: wrong lineage; build risk "referencing the wrong templates, CLI commands or API shapes".
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json` — `confusions[Q14]`: build risk "follows older 'DocumentDB' docs that actually describe the pre-2017 service or Cosmos DB RU-mode".

Facts cross-checked against the Learn overview "Naming and history" section (https://learn.microsoft.com/azure/documentdb/overview) and FAQ (https://learn.microsoft.com/azure/documentdb/faq), and the kit clone at commit `4f41c15`.

## Verification

### 1. Already covered? -- confirmed (not in the target)

The fix target is the Agent Kit, not Learn. Learn already has the content: https://learn.microsoft.com/en-us/azure/documentdb/overview, section "Naming and history", says the service "was previously named vCore-based Azure Cosmos DB for MongoDB", "isn't Amazon DocumentDB", "isn't the original Azure DocumentDB service from 2014–2017" and that it "and Azure Cosmos DB for MongoDB (RU) are different services". So a Learn change is not needed, and this PR mirrors that section.

The kit clone at commit `4f41c15` has none of it. Grepping all `*.md` files (CHANGELOG excluded) for `vCore-based`, `formerly`, `databaseAccounts`, `request unit` and `Amazon DocumentDB` finds no matches. The kit only gets part of the way there: `skills/azure-deployment/SKILL.md` line 9 names the resource type `Microsoft.DocumentDB/mongoClusters`, but it gives no former name and no contrast with the RU-based service. The stale strings the draft lists are there as described:
- `CONTRIBUTING.md:19` "Cosmos DB for MongoDB vCore"
- `skills/data-modeling/model-embed-vs-reference.md:7,49`
- `skills/data-modeling/model-16mb-limit.md:7,45`
- `skills/data-modeling/model-denormalize-reads.md:7,39`

The non-canonical engine links are also there:
- `AGENTS.md:3`
- `skills/azure-deployment/SKILL.md:9`
- `skills/local-deployment/local-choose-deployment-method.md:45`
- `skills/local-deployment/local-docker-compose-setup.md:73`

`README.md:12` already uses `https://github.com/documentdb/documentdb`.

### 2. Is the premise true? -- confirmed, with two small corrections applied

Each naming claim matches the Learn overview "Naming and history" section quoted above, and the overview's "Open source, with no SSPL" section links the canonical engine repo https://github.com/documentdb/documentdb. The other claims match the facts given for this run: resource type `Microsoft.DocumentDB/mongoClusters`, CLI group `az documentdb mongocluster`, M-tier vCore billing with no request units, and the PostgreSQL-based open-source engine.

Corrections applied to the body:
- **Redirect type.** The draft said the legacy `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/` URLs "301-redirect". `curl -I` shows they return HTTP 302 and then serve pages whose canonical URL is `/azure/documentdb/` or `/azure/documentdb/limitations`. That page also returns 200. The body now says the links still resolve but rely on a legacy redirect.
- **Scope of the `az cosmosdb` warning.** The wording now says `az cosmosdb` *account* commands and RU/throughput guidance do not apply, so the warning is not over-broad.

I also added an option for the GHCR-labelled link in `local-docker-compose-setup.md`. This is not a premise correction.

I could not independently recount the per-sample numbers (68 samples, 93 of 118 cold answers wrong). The findings records do not carry `fid`, so the ids cannot be joined back to samples. The numbers are kept from the clustered Q14 analysis.

### 3. Maintainer skeptic -- confirmed

As maintainer of the Agent Kit I would accept this PR:
- It names exact files and lines and gives the replacement text.
- The text mirrors official Learn wording.
- It removes the legacy product name from rules and from contributor guidance.
- The naming block is an Azure DocumentDB fix, not generic hygiene. The kit is the context an agent loads before acting, and the experiment shows agents that grounded on the kit still got the lineage wrong.

The canonical-URL change is a small, safe cleanup that fits in the same PR. It belongs in this repository: Learn already covers the content, and the MCP server is not the right place for product-naming guidance.

## Finding ids

- F0116
- F0155
- F0186
- F0265
- F0321
- F0392
- F0428
- F0463
- F0532
- F0604
- F0732
- F0770
- F0800
- F0924
- F0950
- F0976
- F1007
- F1047
- F1110
- F1138
- F1168
- F1205
- F1231
- F1267
- F1305
- F1377
- F1408
- F1494
- F1529
- F1563
- F1595
- F1662
- F1689
- F1724
- F1760
- F1796
- F1867
- F1896
- F1927
- F1958
- F1989
- F2024
- F2091
- F2158
- F2192
- F2223
- F2250
- F2295
- F2332
- F2395
- F2431
- F2466
- F2524
- F2558
- F2597
- F2625
- F2655
- F2717
- F2784
- F2813
- F2915
- F2946
- F2982
- F3078
- F3116
- F3183
- F3232
- F3264
- F3366
- F3399
- F3432
- F3505
