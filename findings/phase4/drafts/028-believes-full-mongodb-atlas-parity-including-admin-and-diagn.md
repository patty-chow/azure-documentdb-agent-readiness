---
title: "Fix 404 compatibility links and add a \"not exposed on Azure DocumentDB\" command list to natural-language-querying"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 16
findings: 16
bucket: confusion-Q10
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Fix 404 compatibility links and add a "not exposed on Azure DocumentDB" command list to natural-language-querying

## What happens today

- `skills/natural-language-querying/SKILL.md:261` and `compat/QUICKSTART.md:103` both point to `https://learn.microsoft.com/azure/documentdb/compatibility`, which returns **HTTP 404** (checked 2026-11-25). Every other compatibility citation in the kit (six links in five files: `skills/query-optimizer/references/core-indexing-principles.md:7` and `:208`, `skills/monitoring/monitoring-slow-query-log.md:42`, `skills/full-text-search/fts-create-search-index.md:66`, `skills/indexing/index-single-field.md:89`) uses the correct path `/azure/documentdb/compatibility-query-language`.
- The "Azure DocumentDB Compatibility Notes" section in `skills/natural-language-querying/SKILL.md` (lines 240-261) only lists what is **supported**. The "Check Documentation For" bullets say "some advanced aggregation operators may have partial support" and then send the reader to the dead link. No skill in the kit names the command families a managed cluster does not expose.

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini, this kit plus the DocumentDB, Azure and Learn MCP servers), **16 of 100 samples** answered the cold-quiz question "which wire/server versions are supported and which commonly used MongoDB features are not?" as `partly_wrong`. The failure mode was the same each time: the model treated Azure DocumentDB as a plain `mongod` or an Atlas cluster. Several answers hedged with old Cosmos DB RU-era limits (wire 3.6/4.x, "transactions and change streams may be limited"); the rest assumed full admin parity ("certain admin/diagnostic commands ... may be limited", with no idea which) or Atlas features. Several `build_risk` notes say the builder "must consult the compatibility matrix", and the agents' own `improvements` ask the kit for a short list of unsupported admin commands (e.g. `15-digital-onboarding-orchestration`, `15-prescription-refill-agent`, `14-dynamic-pricing-engine`, which names server-side JS, cluster admin commands and planCache introspection).

The grounded stage recovered every time, but only by falling back to Learn search; the kit's own pointer would have 404'd. None of the 100 generated apps ended up calling a restricted command, so this is a readiness/trust gap rather than a build breakage, but it is the most repeated Q10 confusion and the dead link is a plain bug.

Learn's `compatibility-query-language` page already carries the full per-version (5.0-8.0) table, marking `serverStatus`, `top`, `connPoolStats`, `dataSize`, `dbHash`, `lockInfo`, `$planCacheStats`, `$listSessions`, `$listSearchIndexes`, `killAllSessions`, `compact`, `convertToCapped`, `bulkWrite` and `setDefaultRWConcern` as not supported, and replication, role-management, plan-cache and shard-balancer commands as N/A (service-managed). So the fix belongs in the kit, not in Learn.

## Proposed change

### 1. Fix the two dead links

`skills/natural-language-querying/SKILL.md:261` and `compat/QUICKSTART.md:103`:

```diff
-https://learn.microsoft.com/azure/documentdb/compatibility
+https://learn.microsoft.com/azure/documentdb/compatibility-query-language
```

### 2. Replace the "Check Documentation For" bullets in `skills/natural-language-querying/SKILL.md` (section "Azure DocumentDB Compatibility Notes")

```markdown
**Not exposed on Azure DocumentDB (managed service):**
Azure DocumentDB supports MongoDB versions 5.0, 6.0, 7.0 and 8.0
(about 99% operator compatibility: 58/60 aggregation stages, all
aggregation and update operators, 44/45 query and projection operators),
including change streams and multi-document transactions. It is a
managed service, so do NOT generate code that calls:
- Server/diagnostic commands: `serverStatus`, `top`, `connPoolStats`,
  `dataSize`, `dbHash`, `lockInfo`, `$listSessions`, `killAllSessions`
- `$planCacheStats` and plan-cache commands (the engine manages plan caching)
- The `bulkWrite` *command*, i.e. MongoDB 8.0 client-level
  `MongoClient.bulkWrite()`; collection-level `collection.bulkWrite()` is fine
- `compact`, `convertToCapped`, `setDefaultRWConcern`, `$listSearchIndexes`
- Replication, role-management and shard-balancer commands (Azure and
  Microsoft Entra ID manage these)
- `$where`, `$function`, `$accumulator` (deprecated in MongoDB 8.0; `$where`
  also cannot use indexes)
- Atlas-only features: this is not an Atlas cluster, so there is no Atlas
  Search (Lucene) service and no `$vectorSearch` stage. Use a text index
  (`$text`) or the `$search` stage with a search index for full-text search
  (see the full-text-search skill), and `$search` with `cosmosSearch`
  (vector-ivf / vector-hnsw / vector-diskann) for vector search
  (see the vector-search skill)

If a prompt asks for one of these, say it is not available on Azure
DocumentDB and offer the closest supported alternative (for example,
`explain("executionStats")` and the slow-query log instead of
`serverStatus`/plan-cache introspection; Azure Monitor metrics instead
of `top`/`connPoolStats`).

For the authoritative per-version table, refer to:
https://learn.microsoft.com/azure/documentdb/compatibility-query-language
```

### 3. (Optional) mirror the list in `skills/query-optimizer/references/core-indexing-principles.md`

Add a short "Service-managed commands" subsection just above `## References` (line 202) with the same bullets, since that file already carries the correct link and is where the kit's `$where` guidance (line 142) lives.

## Evidence (run folders, Q10 entries in `02-readiness.json`)

- `runs/15-prescription-refill-agent/20261124-195253/02-readiness.json` (confusions Q10, Q15: assuming full admin parity with plain mongod could cause runtime errors)
- `runs/14-dynamic-pricing-engine/20261124-184622/02-readiness.json` (Q10 improvement asks for a checklist covering server-side JS, cluster admin commands, planCache introspection)
- `runs/19-care-coordination-multi-agent/20261124-195730/02-readiness.json` (Q10: assumes every MongoDB feature is present; an administrative command may fail at runtime)
- `runs/15-digital-onboarding-orchestration/20261124-202211/02-readiness.json` (Q10 improvement: a small list of unsupported admin commands)
- `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json` (Q10: RU-era confusion; check the compatibility matrices before using advanced server commands)

Other affected samples: 11-care-gap-identification-pipeline, 11-preference-center-consent-store, 12-cross-border-payment-audit-trail, 14-telehealth-session-summarizer, 15-cohort-analysis-backend, 15-financial-advisor-chatbot-rag, 16-atm-network-status-monitor, 17-ai-survey-response-analyzer, 17-seasonal-trend-spotter-agent, 18-returns-refund-workflow-orchestration, 19-insider-threat-detection-pipeline.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? confirmed (not in the target)

- Grepped the kit clone (HEAD 4f41c15, 2026-11-23) for `serverStatus`, `planCache`, `connPoolStats`, `killAllSessions`, "not exposed", "unsupported command" under `skills/`, `knowledge-base/` and `compat/`: no list of restricted command families exists. The only hit for "not exposed" is unrelated (`skills/azure-deployment/SKILL.md:266`, Terraform HA mode).
- `skills/natural-language-querying/SKILL.md:240-261` lists only supported features; line 261 reads `https://learn.microsoft.com/azure/documentdb/compatibility`. `compat/QUICKSTART.md:103` links the same URL and says the test "does not imply that every MongoDB feature is supported" without naming which.
- `curl -L` on `https://learn.microsoft.com/azure/documentdb/compatibility` and the `/en-us/` variant returns 404; `https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language` returns 200.
- The information exists on Learn (compatibility-query-language page), so the Learn side is already covered; the kit side, which this PR targets, is not.

### 2. Premise true? confirmed (with corrections applied)

Checked against https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language (fetched 2026-11-25):
- "99.03% MongoDB compatibility"; aggregation stages 58/60, aggregation operators 181/181, query and projection 44/45, update 22/22; versions 5.0-8.0. Confirmed.
- `$changeStream` supported; `abortTransaction`/`commitTransaction` supported. Confirmed.
- `serverStatus`, `top`, `connPoolStats`, `dataSize`, `dbHash`, `lockInfo`, `bulkWrite`, `$planCacheStats`, `$listSearchIndexes`, `$listSessions`, `killAllSessions`, `setDefaultRWConcern`, `compact`, `convertToCapped`: all "No" in 5.0-8.0. Confirmed.
- Replication, role management (via Microsoft Entra ID), plan caching and shard balancing: N/A with footnotes saying Azure/the engine manages them. Confirmed. (`createUser` is supported, so the list says role-management, not user-management.)
- `$where`, `$function`, `$accumulator`: "Deprecated in Mongo version 8.0". Confirmed.
- Correction 1: the draft said "the six other skill files"; it is six links in five files (core-indexing-principles.md has two, lines 7 and 208). Fixed.
- Correction 2: the draft said "there is no Atlas Search or `$vectorSearch`; use `$text` with a text index". The `$search` and `$searchMeta` stages are listed as supported, and the kit's own full-text-search skill uses `$search` + `createSearchIndexes` for BM25 and `$search: { cosmosSearch: ... }` for vectors (`skills/full-text-search/fts-hybrid-search.md:7,71`). Reworded: no Atlas Search (Lucene) service and no `$vectorSearch` (not listed on the page), full-text via text index or `$search` with a search index, vector via `$search` + `cosmosSearch`.
- Correction 3: clarified that the unsupported `bulkWrite` is the server command used by MongoDB 8.0 client-level `MongoClient.bulkWrite()`; collection-level `bulkWrite()` maps to insert/update/delete commands and works.
- No contradiction with the given true facts (cosmosSearch index kinds, text-index full-text search, not Atlas).

### 3. Maintainer skeptic: confirmed

Names exact files and lines, fixes a verifiable broken link, and adds an Azure DocumentDB-specific, source-backed list to the skill an agent reads when writing queries. Small two-file PR with an optional third. I would accept it with the edits above.

## Finding ids

F1757, F1864, F2021, F2362, F2463, F2490, F2521, F2555, F2594, F2652, F2687, F2810, F2912, F3076, F3148, F3261
