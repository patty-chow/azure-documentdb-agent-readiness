---
id: K22
title: "Fix 404 compatibility links and list commands not exposed on Azure DocumentDB"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 16
member_drafts:
  - 028-believes-full-mongodb-atlas-parity-including-admin-and-diagn.md
open_questions: 1
---

# Fix 404 compatibility links and list commands not exposed on Azure DocumentDB

## What happens today

- `skills/natural-language-querying/SKILL.md:261` and `compat/QUICKSTART.md:103` link to `https://learn.microsoft.com/azure/documentdb/compatibility`, which returns HTTP 404 (checked 2026-11-25). Every other compatibility citation in the kit (six links in five files: `skills/query-optimizer/references/core-indexing-principles.md:7` and `:208`, `skills/monitoring/monitoring-slow-query-log.md:42`, `skills/full-text-search/fts-create-search-index.md:66`, `skills/indexing/index-single-field.md:89`) already uses the working path `/azure/documentdb/compatibility-query-language`.
- The "Azure DocumentDB Compatibility Notes" section of `skills/natural-language-querying/SKILL.md` (lines 240-261) lists only what is supported. Its "Check Documentation For" bullets say some advanced operators "may have partial support" and then point at the dead link. No skill in the kit names the command families a managed cluster does not expose (grep for `serverStatus`, `planCache`, `connPoolStats`, `killAllSessions` under `skills/`, `knowledge-base/` and `compat/` finds nothing).

## Why it matters

In one 100-sample agent-readiness run (an agent given this kit plus the DocumentDB, Azure and Microsoft Learn MCP servers), 16 of 100 samples answered the question "which server versions are supported and which commonly used MongoDB features are not?" partly wrong. Counts are from that single run. The agent treated Azure DocumentDB as a plain `mongod` or an Atlas cluster: some answers fell back to old request-unit-era Cosmos DB limits ("transactions and change streams may be limited"), others assumed full admin parity or Atlas-only features. Several agents asked the kit for a short list of unsupported admin commands (server-side JS, cluster admin commands, plan-cache introspection). The agent recovered only by searching Learn directly; the kit's own pointer would have 404'd. No generated app called a restricted command, so this is a trust and readiness gap rather than a build break, but it was the most repeated confusion on this question and the dead link is a plain bug.

Learn's `compatibility-query-language` page already has the per-version (5.0-8.0) table, and the Learn FAQ (updated 2026-11-07) states the headline facts outright ("Azure DocumentDB supports MongoDB wire protocol versions 5.0, 6.0, 7.0, and 8.0, and 99.03% of MongoDB query, projection, update, and aggregation operators"), so the fix belongs in the kit. Two rows of the compatibility table are themselves stale or inconsistent (see "Resolved" and "Open questions"), so the kit's list below deliberately departs from the table on `$listSearchIndexes` and footnotes `bulkWrite`.

## Proposed change

### 1. `skills/natural-language-querying/SKILL.md` and `compat/QUICKSTART.md`: fix the dead link

```diff
-https://learn.microsoft.com/azure/documentdb/compatibility
+https://learn.microsoft.com/azure/documentdb/compatibility-query-language
```

In `skills/natural-language-querying/SKILL.md:261-262`, which calls the dead URL "the authoritative list of supported features", also link the companion page `https://learn.microsoft.com/azure/documentdb/compatibility-features` (the feature-level view; the two pages together are the live replacement for the 404'd `/compatibility`). The dead URL and the live pair are recorded in DECISIONS.md (topic 9, Learn fixes and kit errors).

### 2. `skills/natural-language-querying/SKILL.md`: replace the "Check Documentation For" bullets in "Azure DocumentDB Compatibility Notes"

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
- The `bulkWrite` *command*, i.e. the MongoDB 8.0 database-level command
  behind client-level `MongoClient.bulkWrite()` (the service returns code 59
  CommandNotFound); collection-level `collection.bulkWrite()` maps to
  insert/update/delete and works
- `compact`, `convertToCapped`, `setDefaultRWConcern`
- Replication, role-management and shard-balancer commands (Azure and
  Microsoft Entra ID manage these)
- `$where`, `$function`, `$accumulator` (deprecated in MongoDB 8.0; `$where`
  also cannot use indexes)
- Atlas-only features: this is not an Atlas cluster, so there is no Atlas
  Search (Lucene) service and no `$vectorSearch` stage. For full-text search
  the GA path is a classic text index with `$text`; the `$search` stage with
  a search index (`createSearchIndexes`, `$listSearchIndexes`) is a preview
  feature that must first be enabled on the cluster (portal Settings >
  Features > Full-text search, then wait about 10 minutes; until then
  `createSearchIndexes` fails with code 115 "Search index creation is not
  supported yet") - see the full-text-search skill. For vector search use
  `$search` with `cosmosSearch` (vector-ivf / vector-hnsw / vector-diskann)
  over number[] embeddings (see the vector-search skill)

If a prompt asks for one of these, say it is not available on Azure
DocumentDB and offer the closest supported alternative (for example,
`explain("executionStats")` and the slow-query log instead of
`serverStatus`/plan-cache introspection; Azure Monitor metrics instead
of `top`/`connPoolStats`).

For the authoritative per-version table, refer to:
https://learn.microsoft.com/azure/documentdb/compatibility-query-language
```

### 3. (Optional) `skills/query-optimizer/references/core-indexing-principles.md`

Add a short "Service-managed commands" subsection just above `## References` (line 202) with the same bullets; this file already carries the correct link and the kit's `$where` guidance (line 142).

Corrections from draft verification already applied: "six links in five files" (not six files); `$search` with a search index is supported (as a preview feature), so the list says "no Atlas Search service and no `$vectorSearch`" rather than "no `$search`"; the unsupported `bulkWrite` is the MongoDB 8.0 database-level command behind client-level `MongoClient.bulkWrite()`, not `collection.bulkWrite()`; the list says role-management, not user-management, because `createUser` is supported; `$listSearchIndexes` is no longer in the "not exposed" list because it is supported (the full-text-search keyword and structured pages, the limitations page and the 2026-11-17 DocumentDB blog post all use it to wait for `status: "READY"`), and the compatibility table's row marking it unsupported is stale.

## Evidence

Q10 entries in `02-readiness.json`:

- `runs/15-prescription-refill-agent/20261124-195253/02-readiness.json` (assumes full admin parity with plain mongod)
- `runs/14-dynamic-pricing-engine/20261124-184622/02-readiness.json` (asks for a checklist covering server-side JS, cluster admin commands, plan-cache introspection)
- `runs/19-care-coordination-multi-agent/20261124-195730/02-readiness.json` (assumes every MongoDB feature is present)
- `runs/15-digital-onboarding-orchestration/20261124-202211/02-readiness.json` (asks for a small list of unsupported admin commands)
- `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json` (request-unit-era confusion)

Other affected samples: 11-care-gap-identification-pipeline, 11-preference-center-consent-store, 12-cross-border-payment-audit-trail, 14-telehealth-session-summarizer, 15-cohort-analysis-backend, 15-financial-advisor-chatbot-rag, 16-atm-network-status-monitor, 17-ai-survey-response-analyzer, 17-seasonal-trend-spotter-agent, 18-returns-refund-workflow-orchestration, 19-insider-threat-detection-pipeline.

## Resolved

- Supported versions and the 99.03% figure: settled. Azure DocumentDB supports MongoDB wire protocol versions 5.0, 6.0, 7.0 and 8.0 and 99.03% of query, projection, update and aggregation operators; any wire-protocol driver connects. Sources: Learn FAQ (https://learn.microsoft.com/en-us/azure/documentdb/faq, ms.date 2026-11-06, updated 2026-11-07, "Which MongoDB versions and features does Azure DocumentDB support?"); compatibility page (https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language, ms.date 2025-11-05, updated 2026-06-13).
- `$listSearchIndexes`: settled as supported, so it is removed from the kit's "not exposed" list; the compatibility table row marking it unsupported is stale. Sources: https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-keyword; https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-structured; https://learn.microsoft.com/en-us/azure/documentdb/limitations ("Search-index management supports creation and listing"); DocumentDB blog post 2026-11-17 (https://devblogs.microsoft.com/documentdb/?p=259).
- Full-text search GA status and which path to recommend first: settled. Full-text search via `$search` with a search index "remains in preview" while `$text` and classic text indexes are GA; enablement is self-serve (portal Settings > Features > Full-text search, Azure CLI PATCH of `properties.previewFeatures` adding `FullTextSearch`, Bicep or Terraform), followed by a ten-minute wait, and `createSearchIndexes` on a cluster without the preview enabled returns code 115 "Search index creation is not supported yet". The kit therefore names the text index as the GA path and `$search` as the opt-in preview. Sources: https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview (dated 2026-11-04, updated 2026-11-17); https://devblogs.microsoft.com/documentdb/?p=259 (2026-11-17); runs/07-voice-of-customer-sentiment-hub/20261124-204049 (code 115 observation).
- `bulkWrite` distinction: settled. The compatibility page's `bulkWrite: No` is the MongoDB 8.0 database-level command (multi-namespace, used by `MongoClient.bulkWrite()`, which the Node driver scopes to server 8.0+ and driver 6.10+); the page states that client-side wrappers relying on supported server commands are compatible, and `insert`, `update`, `delete` and `findAndModify` are Yes, so collection-level `db.collection.bulkWrite()` works. The engine's `bulk_write.c` is a stub and the gateway returns 59 CommandNotFound for the 8.0 command; a run executed collection-level `bulkWrite(ops, { ordered: false })` against the Azure cluster with `ok: 1`. Sources: https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language (Database commands table and the note above it); https://www.mongodb.com/docs/manual/reference/command/bulkWrite/; https://www.mongodb.com/docs/drivers/node/current/crud/bulk-write/; https://github.com/documentdb/documentdb/blob/main/pg_documentdb/src/commands/bulk_write.c; https://github.com/documentdb/documentdb/issues/770; https://github.com/documentdb/documentdb/issues/108; runs/02-real-time-event-stream-ingestion/20261124-203233/events.jsonl.

## Open questions

1. [needs SME confirmation] The remaining "not exposed" command list (`serverStatus`, `top`, `connPoolStats`, `dataSize`, `dbHash`, `lockInfo`, `$listSessions`, `killAllSessions`, `$planCacheStats` and plan-cache commands, `compact`, `convertToCapped`, `setDefaultRWConcern`, and the replication, role-management and balancer rows) is taken from the Learn compatibility table as fetched on 2026-11-25 (ms.date 2025-11-05, updated 2026-06-13), which is already stale on `$listSearchIndexes` and disagrees with `compatibility-features` on the session commands (`killSessions` Yes vs listed as restricted; `killAllSessions` No) and on `getShardMap`/`balancerStart`/`balancerStatus`/`balancerStop` (N/A vs "retain control over"). Please confirm the list matches current gateway behavior on managed clusters before a skill tells agents never to call these commands.

## Source drafts

- 028-believes-full-mongodb-atlas-parity-including-admin-and-diagn.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
