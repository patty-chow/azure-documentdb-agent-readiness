---
title: "Note only: $text / Atlas Search prior for full-text search is already corrected by Learn and the Agent Kit; no build leaked it"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 18
findings: 18
bucket: confusion-Q09
verdicts:
  skipped: note-only
---

# Note only: MongoDB `$text` / Atlas Search prior for full-text search, already corrected

In the cold quiz (Q09, no docs or skills), gpt-5-mini answered from its MongoDB/Atlas prior in 18 of 100 samples: `createIndex({field:'text'})` + `{$text:{$search:...}}`, Atlas `$vectorSearch` / compound syntax, and hybrid search as `$text` plus a client-side merge. 7 were graded `wrong` and 11 `partly_wrong`.

On Azure DocumentDB, full-text search uses `$search`-style text search indexes (created with `createSearchIndexes`) with BM25 scoring. It does not use Atlas Search. Vector queries use `cosmosSearch`.

**Skip reason:** The Learn full-text-search overview, keyword and hybrid pages already correct this. The Agent Kit corrects it in skills/full-text-search/SKILL.md, skills/indexing/index-text-prefer-textsearch.md, skills/query-optimizer/references/core-indexing-principles.md and skills/vector-search/vector-knn-query.md. None of the 18 affected builds used `$text`, `{field:'text'}` or `$vectorSearch`, and the grounded readiness answers were correct. This is a baseline model prior, not a gap in the docs or the kit. The RRF/`$unionWith` asks (F3260, F3300, F3326) moved to the hybrid-fusion theme.

## Verification
- skipped: note-only (drafter decided no action; the three checks were not run per stage instructions). Skip reason is strong: backed by kit file citations and run-artifact greps.

## Finding ids
F0007, F0631, F1560, F1659, F1863, F1985, F2328, F2391, F2462, F2623, F2844, F2878, F2943, F3016, F3075, F3113, F3229, F3461
