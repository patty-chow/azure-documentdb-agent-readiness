---
title: "Note: 'Azure DocumentDB has no native vector indexing' is a model prior already corrected by the kit and Learn — no issue filed"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 28
findings: 28
bucket: confusion-Q08
verdicts:
  skipped: note-only
---

# Note (no action): "Azure DocumentDB has no native vector indexing" is a model prior

In 28 of 100 samples the cold Q08 answer was wrong (26) or partly wrong (2): gpt-5-mini identified the service as the RU-based Cosmos DB for MongoDB API or Cosmos DB for NoSQL and said no server-side vector index exists. Azure DocumentDB (vCore, Microsoft.DocumentDB/mongoClusters) ships native cosmosSearch indexes (vector-ivf, vector-hnsw, vector-diskann). All 28 grounded answers were correct, citing the Learn vector-search page or the Agent Kit vector-search skill, and the vector-bearing builds used cosmosSearch. Optional nit (F2085): a one-line vector-search item in the Learn overview feature list; not filed.

## Skip reason

Model prior rooted in the "Azure Cosmos DB for MongoDB vCore" rename, not a doc or kit gap. The correction already exists where the pipeline grounds: the Learn vector-search page (cited in 20 of 28 grounded answers) and the Agent Kit's skills/vector-search/SKILL.md (cited in 7), whose first line states the cosmosSearch fact and whose description triggers on RAG / vector-index tasks. All 28 grounded answers were correct and the four vector-bearing builds loaded the skill and used cosmosSearch, so no sample was harmed by the prior. The one suggestion with some merit (an overview-page callout, F2085) would not change a cold answer and is recorded as a low-priority nit rather than an issue.

## Verification

- skipped: note-only. Checks not run per stage instructions; skip reason is well supported (correction already exists in Learn and the kit, all grounded answers correct), so status is drop.

## Finding ids

- F0110
- F0260
- F0351
- F0458
- F0599
- F0849
- F0890
- F0919
- F0945
- F1042
- F1076
- F1104
- F1226
- F1261
- F1403
- F1626
- F1755
- F2054
- F2085
- F2123
- F2245
- F2360
- F2553
- F2685
- F2808
- F2977
- F3178
- F3299
