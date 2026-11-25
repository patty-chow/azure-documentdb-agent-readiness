---
id: K19
title: "full-text-search skill: document the preview-enablement prerequisite and CommandNotSupported fail-fast"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P2
sample_count: 2
member_drafts:
  - 025-skill-gap-full-text-search-is-a-preview-feature-that-must-be.md
open_questions: 3
---

# full-text-search skill: document the preview-enablement prerequisite and `CommandNotSupported` fail-fast

## What happens today

`skills/full-text-search/SKILL.md` and `skills/full-text-search/fts-create-search-index.md` show how to call `createSearchIndexes` and `$search`. Nothing in the skill says that:

- Azure DocumentDB full-text search is a **preview** feature, **off by default**, and must be enabled on each cluster before `createSearchIndexes` or `$search` will work. [needs SME confirmation: current preview/GA status]
- After enabling, Learn says to wait **about 10 minutes** before creating an index or running a query.
- On a cluster without the feature, `createSearchIndexes` returns `{ ok: 0, code: 115, codeName: "CommandNotSupported", errmsg: "Search index creation is not supported yet" }` (seen in run logs; Learn does not document this string). [needs SME confirmation]

A grep for `preview`, `enable`, `FullTextSearch`, `CommandNotSupported` or `prerequisite` over `skills/full-text-search/` and `knowledge-base/` finds only the unrelated `dynamic: true` guideline. Microsoft Learn already documents the steps ([Enable full-text search](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search): portal Settings > Features > Full-text search > Enable; an `az rest` PATCH adding `FullTextSearch` to `properties.previewFeatures` on `Microsoft.DocumentDB/mongoClusters`, api-version `2024-07-01`; AzAPI and Bicep variants). An agent relying on the kit alone never learns the gate exists.

## Why it matters

In one experiment run, an agent (gpt-5-mini with this kit loaded) built 100 Azure DocumentDB sample apps. Counts below come from that single run and may change on a re-run.

2 samples are backed by finding ids (the two readiness flags below); 3 more were found in run artifacts while verifying, so 5 of the 100 samples show the problem in total:

- 2 samples flagged the gap during a readiness check. One still believed full-text search needs an external search service; the other warned a sample "will fail" if the cluster lacks "tier/preview flags". Learn lists no tier restriction, only the preview flag, so the skill should state the actual gate.
- 1 sample hit code 115 on a live cluster. Its seed script printed "command may not be available" and continued, leaving search broken.
- 1 sample caught the same error and silently fell back to a legacy `{ text: "text" }` index (`$text`), which the skill itself says is not the DocumentDB search path.
- 1 sample shipped a `createSearchIndexes` template and README with no enablement step, so a user on a fresh cluster gets code 115 with no explanation.

Without the prerequisite, the agent cannot give a useful setup step or error message, and its workarounds (swallow the error, or downgrade to `$text`) contradict the rest of the skill.

## Proposed change

### 1. `skills/full-text-search/SKILL.md`

Insert after the intro paragraph, before "Key syntax points":

```markdown
## Prerequisite: enable the full-text search preview on the cluster

Full-text search (`createSearchIndexes` + `$search`) is a **preview** feature and is **off by default**. Enable it once per cluster before creating a search index or running `$search`:

- **Azure portal:** open the cluster > **Settings** > **Features** > **Full-text search** > **Enable**.
- **ARM / CLI / IaC:** add `"FullTextSearch"` to `properties.previewFeatures` on the `Microsoft.DocumentDB/mongoClusters` resource (api-version `2024-07-01`), preserving any other preview features already listed. Exact `az rest`, Terraform (AzAPI) and Bicep snippets: https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search
- **Wait ~10 minutes** after enabling. Seeing `FullTextSearch` in the resource configuration does not mean activation has finished.

Learn documents no cluster-tier restriction for full-text search (unlike HNSW/DiskANN vector indexes); the preview flag is the documented prerequisite. The GA `$text` operator and `{ field: "text" }` indexes are unaffected by the flag and are **not** a substitute.

**In generated samples:** do not assume the flag is on. Treat `createSearchIndexes` failing with `code: 115` / `codeName: "CommandNotSupported"` (errmsg `Search index creation is not supported yet`) as "feature not enabled yet": fail fast with a message that names the portal path and the Learn anchor above, and do not silently fall back to a `{ field: "text" }` index.
```

### 2. `skills/full-text-search/fts-create-search-index.md`

a. Add before `## Incorrect`:

```markdown
## Prerequisite

Full-text search is in preview and must be enabled on the cluster first (portal: Settings > Features > Full-text search > Enable, or `previewFeatures: ["FullTextSearch"]` via ARM). Allow ~10 minutes after enabling. See https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search. On a cluster without the flag, `createSearchIndexes` returns `code 115 CommandNotSupported: "Search index creation is not supported yet"`.
```

b. Append to `## Correct` (Node.js shown; in pymongo check `OperationFailure.code`):

```javascript
try {
  await db.command({ createSearchIndexes: "products_10M", indexes: [/* ... */] });
} catch (err) {
  if (err.code === 115 /* CommandNotSupported */) {
    throw new Error(
      "Full-text search is not enabled on this Azure DocumentDB cluster. " +
      "Enable it (portal: Settings > Features > Full-text search > Enable, or add " +
      "\"FullTextSearch\" to previewFeatures), wait ~10 minutes, then rerun. " +
      "https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search"
    );
  }
  throw err;
}
```

c. Add to the guidelines list: "**Check the preview flag before you debug index syntax.** `CommandNotSupported` means the feature is off (or still activating), not that the index definition is wrong."

d. Add to `## References`:
- `[Full-text search overview: enable full-text search](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search)`
- `[Full-text search limitations (preview)](https://learn.microsoft.com/azure/documentdb/limitations#full-text-search-limitations-preview)`

**Out of scope:** samples that used `createSearchIndexes` for vector indexes (those belong to `createIndexes` + `cosmosSearch`; separate vector-search item). Also separate: `SKILL.md` says "No `compound` operator yet", while the current Learn overview lists `compound` as available.

## Evidence

Run folders in the experiment repository:

1. `runs/12-abandoned-cart-recovery-orchestration/20261125-054042/02-readiness.json` (readiness answer asks for the enablement step)
2. `runs/15-financial-advisor-chatbot-rag/20261124-192021/02-readiness.json` (build-risk note about missing preview flag)
3. `runs/11-correspondent-banking-risk-screener/20261124-201541/` (`events.jsonl`, `04-decisions.md`: live code 115 from `createSearchIndexes`)
4. `runs/07-voice-of-customer-sentiment-hub/20261124-204049/` (`doc-gaps.md`, `app/src/ingest.py`: error swallowed, fallback to `$text` index)
5. `runs/04-natural-language-product-search/20261124-183232/app/indexes/README.md` (template with no enablement step)

## Open questions

1. [needs SME confirmation] Is full-text search still in preview, or has it reached GA (or a GA date been set)? If GA, the prerequisite text should change to whatever enablement, if any, remains, and the "preview" wording should be dropped.
2. [needs SME confirmation] Is `code 115 CommandNotSupported` / "Search index creation is not supported yet" the stable, intended error for a cluster without the feature, and also during the ~10-minute activation window? It was observed in run logs only; Learn does not document it.
3. [needs SME confirmation] Is there truly no tier or SKU restriction on full-text search? Learn's limitations page lists none; the proposed text says only that Learn documents none.

## Source drafts

- `025-skill-gap-full-text-search-is-a-preview-feature-that-must-be.md`
