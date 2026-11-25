---
title: "full-text-search skill: document the preview-enablement prerequisite and the CommandNotSupported fail-fast"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 2
findings: 2
bucket: confusion-Q09
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# full-text-search skill: document the preview-enablement prerequisite and the `CommandNotSupported` fail-fast

## What happens today

`skills/full-text-search/SKILL.md` and `skills/full-text-search/fts-create-search-index.md` show how to run `createSearchIndexes` and `$search`, but nothing in the skill (grep for `preview`, `enable`, `prerequisite` across `skills/full-text-search/` returns only the unrelated `dynamic: true` warning) says that:

- Azure DocumentDB full-text search is a **preview** feature that is **off by default** and must be enabled per cluster before `createSearchIndexes` or `$search` will work.
- After enabling, the service needs **about 10 minutes** before index creation or queries succeed.
- A cluster without the feature returns `{ ok: 0, code: 115, codeName: "CommandNotSupported", errmsg: "Search index creation is not supported yet" }`.

Microsoft Learn already documents the prerequisite (overview page, section "Enable full-text search": portal Settings > Features > Full-text search > Enable; `az rest` PATCH of `Microsoft.DocumentDB/mongoClusters` `properties.previewFeatures` to include `FullTextSearch`, api-version `2024-07-01`; AzAPI and Bicep variants; "wait 10 minutes before creating a search index or running a query"). The skill does not surface any of it, so an agent that relies on the kit alone never learns the gate exists.

## Why it matters

In a 100-sample run of gpt-5-mini building Azure DocumentDB samples with this kit:

- 2 samples (`12-abandoned-cart-recovery-orchestration`, `15-financial-advisor-chatbot-rag`) flagged this in the readiness stage: the cold answer still believed full-text search needs an external search service, and the grounded answer added that a sample assuming integrated search "will fail if the target cluster lacks the required tier/preview flags" and asked for the enablement step to be documented. Sample 15's worry about *tier* is not supported by the docs (Learn lists no tier restriction for full-text search, only the preview flag), which is itself a sign the skill should state the actual gate.
- 1 sample (`11-correspondent-banking-risk-screener`) hit the real error on the live cluster: the seed script's `createSearchIndexes` call returned code 115 `CommandNotSupported`, the script printed "command may not be available" and continued, and the audit recorded the build as partly met with a note to "add a clear README note about feature-gating".
- 1 sample (`07-voice-of-customer-sentiment-hub`) handled the same `CommandNotSupported` by silently falling back to `create_index([("text","text")])`, i.e. the legacy `$text` path the skill explicitly says is *not* the DocumentDB search path, and logged a high-priority doc gap asking for "which cluster types/tiers support createSearchIndexes" and "expected errors when unsupported".
- 1 sample (`04-natural-language-product-search`) shipped a `createSearchIndexes` JSON template and README instruction with no enablement step, so a user following the README on a fresh cluster gets the 115 error with no explanation.

Without the prerequisite in the skill, the agent cannot give a useful error or setup step, and its fallbacks (swallow the error, or downgrade to `$text`) contradict the rest of the skill.

## Proposed change

### 1. `skills/full-text-search/SKILL.md`

Insert after the intro paragraph (before "Key syntax points"):

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

Add a `## Prerequisite` block before `## Incorrect`:

```markdown
## Prerequisite

Full-text search is in preview and must be enabled on the cluster first (portal: Settings > Features > Full-text search > Enable, or `previewFeatures: ["FullTextSearch"]` via ARM). Allow ~10 minutes after enabling. See https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search. On a cluster without the flag, `createSearchIndexes` returns `code 115 CommandNotSupported: "Search index creation is not supported yet"`.
```

Extend the `## Correct` section with a fail-fast example (Node.js driver shown; same shape applies in pymongo via `OperationFailure.code`):

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

Add to the guidelines list: "**Check the preview flag before you debug index syntax.** `CommandNotSupported` means the feature is off (or still activating), not that the index definition is wrong."

Add to `## References`: `[Full-text search overview: enable full-text search](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#enable-full-text-search)` and `[Full-text search limitations (preview)](https://learn.microsoft.com/azure/documentdb/limitations#full-text-search-limitations-preview)`.

### Out of scope

Several samples also used `createSearchIndexes` to create *vector* indexes (which belong to `createIndexes` + `cosmosSearch`); that is a separate vector-search skill issue and is not addressed here. No new Learn content is proposed; Learn already documents the enablement steps. Separately, `SKILL.md` says "No `compound` operator yet", but the current Learn overview (updated 2026-11-17) lists `compound` with `equals`/`range`/`exists`/`in` as available; that drift should be a separate issue.

## Evidence (run folders under `/Users/julietai/claude/azure-documentdb-agent-readiness/`)

1. `runs/12-abandoned-cart-recovery-orchestration/20261125-054042/02-readiness.json` — `confusions[Q09].improvements[1]`: "Document that full-text search is a (preview) feature that may need enabling on a cluster prior to index creation and show the enablement step."
2. `runs/15-financial-advisor-chatbot-rag/20261124-192021/02-readiness.json` — `confusions[Q09].build_risk`: sample "will fail" if the cluster "lacks the required tier/preview flags".
3. `runs/11-correspondent-banking-risk-screener/20261124-201541/events.jsonl` (seed run output) and `04-decisions.md` line 143 — live `code 115 CommandNotSupported: Search index creation is not supported yet` from `createSearchIndexes`.
4. `runs/07-voice-of-customer-sentiment-hub/20261124-204049/doc-gaps.md` ("createSearchIndexes availability and fallback recipe") and `app/src/ingest.py` `create_search_indexes()` — `CommandNotSupported` swallowed and downgraded to a `{text: "text"}` index.
5. `runs/04-natural-language-product-search/20261124-183232/app/indexes/README.md` — `createSearchIndexes` template shipped with no enablement prerequisite.

Verified against Learn on 2026-11-25: `full-text-search-overview#enable-full-text-search` (portal, `az rest`, AzAPI, Bicep; 10-minute wait) and `limitations#full-text-search-limitations-preview` (no tier restriction listed). The exact `code 115` error text is taken from the run logs; Learn does not currently document the error string.


## Verification

### 1. Already covered? partially_covered
Microsoft Learn covers the prerequisite fully; the target (Agent Kit) does not.
- Learn, https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview#enable-full-text-search (updated 2026-11-17): "Enable full-text search on your Azure DocumentDB cluster before creating search indexes or running `$search` queries." It gives the portal steps (Settings > Features > Full-text search, status Off > Enable), an `az rest` PATCH of `Microsoft.DocumentDB/mongoClusters` with api-version 2024-07-01 that adds `FullTextSearch` to `properties.previewFeatures`, plus AzAPI and Bicep variants, and says to "wait 10 minutes before creating a search index or running a query".
- Agent Kit: `grep -rniE "preview|enable|FullTextSearch|CommandNotSupported|prerequisite"` over `skills/full-text-search/` and `knowledge-base/` finds only the unrelated `dynamic: true` guideline in `skills/full-text-search/fts-create-search-index.md` line 58. `SKILL.md` goes from the intro straight to "Key syntax points" and "## Rules". `fts-create-search-index.md` References list only the overview and MQL compatibility pages.
- documentdb-mcp: no full-text-search or enablement content.
So the docs exist, but not in the skill the agent reads. The gap is real for the kit.

### 2. Premise true? confirmed (one claim softened)
- Preview and off by default: confirmed. The overview says the status is initially "Off", and "Full-text search uses separate search indexes and `$search` queries and remains in preview", while `$text` and `{ field: "text" }` indexes are GA and the flag does not affect them.
- `previewFeatures: FullTextSearch`, api-version 2024-07-01, 10-minute wait: confirmed on the overview page.
- Tier: https://learn.microsoft.com/en-us/azure/documentdb/limitations#full-text-search-limitations-preview lists no tier, free-tier or SKU restriction for full-text search. The tier restrictions on that page are for HNSW/DiskANN vector indexes. Edit made: the draft stated "There is no cluster-tier gate" as fact; it now says Learn documents none.
- Error code 115 `CommandNotSupported` / "Search index creation is not supported yet": not on Learn. It appears in the run logs (8 occurrences in `events.jsonl` across runs 07 and 11; `runs/11-correspondent-banking-risk-screener/20261124-201541/04-decisions.md` line 143 records "createSearchIndexes returned CommandNotSupported"). The draft already labels this as observed behaviour from the logs.
- The other evidence paths exist: `runs/07-voice-of-customer-sentiment-hub/20261124-204049/doc-gaps.md` and `runs/04-natural-language-product-search/20261124-183232/app/indexes/README.md`.

### 3. Maintainer skeptic: confirmed
The draft names exact files and insertion points (`skills/full-text-search/SKILL.md` after the intro; `fts-create-search-index.md` before `## Incorrect`, in `## Correct`, in the guidelines and in `## References`). It supplies ready-to-paste text that matches Learn, the change is specific to Azure DocumentDB, and the failure it prevents (code 115 swallowed, or a fallback to `$text`) was seen on live clusters. I would accept it with the small edits above. Added the limitations page to References. Noted the separate `compound` drift as out of scope.

## Finding ids

- F1954
- F2554
