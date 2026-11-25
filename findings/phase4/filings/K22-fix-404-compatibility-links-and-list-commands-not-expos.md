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
open_questions: 3
---

# Fix 404 compatibility links and list commands not exposed on Azure DocumentDB

## What happens today

- `skills/natural-language-querying/SKILL.md:261` and `compat/QUICKSTART.md:103` link to `https://learn.microsoft.com/azure/documentdb/compatibility`, which returns HTTP 404 (checked 2026-11-25). Every other compatibility citation in the kit (six links in five files: `skills/query-optimizer/references/core-indexing-principles.md:7` and `:208`, `skills/monitoring/monitoring-slow-query-log.md:42`, `skills/full-text-search/fts-create-search-index.md:66`, `skills/indexing/index-single-field.md:89`) already uses the working path `/azure/documentdb/compatibility-query-language`.
- The "Azure DocumentDB Compatibility Notes" section of `skills/natural-language-querying/SKILL.md` (lines 240-261) lists only what is supported. Its "Check Documentation For" bullets say some advanced operators "may have partial support" and then point at the dead link. No skill in the kit names the command families a managed cluster does not expose (grep for `serverStatus`, `planCache`, `connPoolStats`, `killAllSessions` under `skills/`, `knowledge-base/` and `compat/` finds nothing).

## Why it matters

In one 100-sample agent-readiness run (an agent given this kit plus the DocumentDB, Azure and Microsoft Learn MCP servers), 16 of 100 samples answered the question "which server versions are supported and which commonly used MongoDB features are not?" partly wrong. Counts are from that single run. The agent treated Azure DocumentDB as a plain `mongod` or an Atlas cluster: some answers fell back to old request-unit-era Cosmos DB limits ("transactions and change streams may be limited"), others assumed full admin parity or Atlas-only features. Several agents asked the kit for a short list of unsupported admin commands (server-side JS, cluster admin commands, plan-cache introspection). The agent recovered only by searching Learn directly; the kit's own pointer would have 404'd. No generated app called a restricted command, so this is a trust and readiness gap rather than a build break, but it was the most repeated confusion on this question and the dead link is a plain bug.

Learn's `compatibility-query-language` page already has the per-version (5.0-8.0) table, so the fix belongs in the kit.

## Proposed change

### 1. `skills/natural-language-querying/SKILL.md` and `compat/QUICKSTART.md`: fix the dead link

```diff
-https://learn.microsoft.com/azure/documentdb/compatibility
+https://learn.microsoft.com/azure/documentdb/compatibility-query-language
```

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
- The `bulkWrite` *command*, i.e. MongoDB 8.0 client-level
  `MongoClient.bulkWrite()`; collection-level `collection.bulkWrite()` is fine
- `compact`, `convertToCapped`, `setDefaultRWConcern`, `$listSearchIndexes`
- Replication, role-management and shard-balancer commands (Azure and
  Microsoft Entra ID manage these)
- `$where`, `$function`, `$accumulator` (deprecated in MongoDB 8.0; `$where`
  also cannot use indexes)
- Atlas-only features: this is not an Atlas cluster, so there is no Atlas
  Search (Lucene) service and no `$vectorSearch` stage. For full-text search
  use a text index or the `$search` stage with a search index (see the
  full-text-search skill); for vector search use `$search` with
  `cosmosSearch` (vector-ivf / vector-hnsw / vector-diskann) over number[]
  embeddings (see the vector-search skill)

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

Corrections from draft verification already applied: "six links in five files" (not six files); `$search` with a search index is supported, so the list says "no Atlas Search service and no `$vectorSearch`" rather than "no `$search`"; the unsupported `bulkWrite` is the server command behind client-level `MongoClient.bulkWrite()`, not `collection.bulkWrite()`; the list says role-management, not user-management, because `createUser` is supported.

## Evidence

Q10 entries in `02-readiness.json`:

- `runs/15-prescription-refill-agent/20261124-195253/02-readiness.json` (assumes full admin parity with plain mongod)
- `runs/14-dynamic-pricing-engine/20261124-184622/02-readiness.json` (asks for a checklist covering server-side JS, cluster admin commands, plan-cache introspection)
- `runs/19-care-coordination-multi-agent/20261124-195730/02-readiness.json` (assumes every MongoDB feature is present)
- `runs/15-digital-onboarding-orchestration/20261124-202211/02-readiness.json` (asks for a small list of unsupported admin commands)
- `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json` (request-unit-era confusion)

Other affected samples: 11-care-gap-identification-pipeline, 11-preference-center-consent-store, 12-cross-border-payment-audit-trail, 14-telehealth-session-summarizer, 15-cohort-analysis-backend, 15-financial-advisor-chatbot-rag, 16-atm-network-status-monitor, 17-ai-survey-response-analyzer, 17-seasonal-trend-spotter-agent, 18-returns-refund-workflow-orchestration, 19-insider-threat-detection-pipeline.

## Open questions

1. [needs SME confirmation] The command list and compatibility figures (99.03%, 58/60 stages, 44/45 query operators; `serverStatus`, `top`, `connPoolStats`, `$planCacheStats`, `compact` and the rest "not supported" in 5.0-8.0) are taken from the Learn page as fetched on 2026-11-25. Please confirm they match current engineering behavior before a skill tells agents never to call them.
2. [needs SME confirmation] Full-text search via `$search` with a search index: some Learn pages still label full-text search as preview. Confirm its GA status, and whether the kit should recommend `$search` or a classic text index first (the kit's indexing skill expresses its own preference here).
3. [needs SME confirmation] The `bulkWrite` distinction: confirm that only the MongoDB 8.0 server-level `bulkWrite` command (client-level `MongoClient.bulkWrite()`) is unsupported, and that collection-level `bulkWrite()` maps to supported insert/update/delete commands in all current drivers.

## Source drafts

- 028-believes-full-mongodb-atlas-parity-including-admin-and-diagn.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
