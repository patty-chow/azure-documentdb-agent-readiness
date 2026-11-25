---
title: "Cold-quiz Q01: model assumes Microsoft.DocumentDB/databaseAccounts for a DocumentDB cluster — corrected by kit and Learn, no change needed"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 88
findings: 93
bucket: confusion-Q01
verdicts:
  skipped: note-only
---

# Note (no issue filed): Q01 resource-type confusion is a corrected model prior

Cold, gpt-5-mini named `Microsoft.DocumentDB/databaseAccounts` (the RU-based Azure Cosmos DB account) instead of `Microsoft.DocumentDB/mongoClusters` in 93 of 102 Q01 answers. Every grounded answer corrected it to `mongoClusters` from Learn or the kit's azure-deployment skill, and no generated app or audit check carried `databaseAccounts` or `az cosmosdb`. The correct CLI is `az documentdb mongocluster`. Some proposed_change strings in this bucket recommend `az cosmosdb mongocluster`, which does not exist; do not carry that text forward.

Optional, low value: one negative sentence in the intro of `skills/azure-deployment/SKILL.md` in Azure/documentdb-agent-kit ("not Microsoft.DocumentDB/databaseAccounts; not managed with az cosmosdb").

## Skip reason
Model prior already corrected: all 93 grounded answers named Microsoft.DocumentDB/mongoClusters (48 on the first Learn read, 28 via the kit's documentdb-azure-deployment skill), zero of 117 generated apps or any audit check contained databaseAccounts or az cosmosdb, and both Learn (mongoClusters templates reference, Bicep/Terraform quickstarts) and the kit (skills/azure-deployment/SKILL.md lines 3, 9, 42-47, 227, 243, 252, 325; examples/azure-deployment/main.bicep line 53) already state the correct type. The proposed Learn banner targets databaseAccounts pages that belong to the Cosmos DB docset, and several proposed_change strings recommend the nonexistent 'az cosmosdb mongocluster'.

## Verification
- skipped: note-only (checks not run per stage instructions; skip reason judged strong, so status is drop).

## Finding ids
F0068, F0104, F0144, F0254, F0283, F0311, F0345, F0385, F0452, F0521, F0553, F0593, F0657, F0722, F0760, F0789, F0820, F0843, F0884, F0913, F0939, F0965, F0996, F1036, F1070, F1098, F1127, F1156, F1194, F1220, F1255, F1294, F1365, F1397, F1430, F1483, F1518, F1553, F1586, F1620, F1652, F1679, F1713, F1749, F1785, F1822, F1856, F1886, F1918, F1947, F1978, F2013, F2048, F2079, F2117, F2149, F2181, F2239, F2284, F2321, F2354, F2384, F2422, F2455, F2482, F2513, F2547, F2586, F2616, F2644, F2679, F2708, F2742, F2774, F2801, F2871, F2904, F2937, F2971, F3009, F3037, F3068, F3106, F3172, F3222, F3253, F3293, F3320, F3356, F3389, F3421, F3455, F3494
