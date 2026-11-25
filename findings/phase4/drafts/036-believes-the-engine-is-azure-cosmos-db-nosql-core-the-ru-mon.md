---
title: "Q15 'engine is Cosmos DB' belief: model prior already corrected by Learn docs and Agent Kit; no action"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 70
findings: 71
bucket: confusion-Q15
verdicts:
  skipped: note-only
---

# Note: Q15 "engine underneath is Cosmos DB" is a model prior, not a doc gap

In 71 of 87 Q15 cold answers (70 samples), gpt-5-mini said Azure DocumentDB (vCore) runs on a Cosmos DB engine (NoSQL core, RU MongoDB-API translation layer, or a proprietary Cosmos engine). This is the pre-rename memory of the RU-based Azure Cosmos DB for MongoDB. The true engine is the open-source, PostgreSQL-based DocumentDB (github.com/documentdb/documentdb); apps use standard MongoDB drivers, capacity is M-series vCore tiers, resource type Microsoft.DocumentDB/mongoClusters.

No change to Learn docs, the Agent Kit or the MCP server. Adjacent naming hygiene (old "Cosmos DB for MongoDB vCore" wording and cosmos-db/mongodb/vcore links in skills/data-modeling/*.md and CONTRIBUTING.md of the Agent Kit) belongs to the naming bucket.

## Verification

Skipped: note-only. Skip reason (strong; status drop):

Model prior already corrected by both doc sources: the Learn overview's "Open source, with no SSPL" and "Naming and history" sections (verified live) and the Agent Kit's README.md:12, AGENTS.md:3 and skills/azure-deployment/SKILL.md:9 all state the open-source, Postgres-backed DocumentDB engine. The pipeline's grounding step cited those pages and corrected the answer in all 71 runs, and no build stage or generated app used a Cosmos SDK, databaseAccounts path or RU idiom (0 of 120 run folders). The one proposed kit edit (F1959) matches no text in the clone; the stale "Cosmos DB for MongoDB vCore" wording in skills/data-modeling belongs to the naming bucket.

## Finding ids

- F0011
- F0048
- F0079
- F0117
- F0156
- F0187
- F0266
- F0322
- F0357
- F0429
- F0464
- F0605
- F0636
- F0733
- F0771
- F0801
- F0830
- F0856
- F0925
- F0951
- F0977
- F1048
- F1082
- F1111
- F1139
- F1169
- F1232
- F1268
- F1306
- F1344
- F1409
- F1495
- F1530
- F1564
- F1631
- F1663
- F1690
- F1725
- F1761
- F1797
- F1833
- F1897
- F1959
- F1990
- F2025
- F2060
- F2092
- F2159
- F2193
- F2251
- F2296
- F2365
- F2467
- F2493
- F2525
- F2559
- F2626
- F2656
- F2691
- F2814
- F2882
- F2983
- F3020
- F3079
- F3117
- F3233
- F3265
- F3304
- F3433
- F3466
- F3506
