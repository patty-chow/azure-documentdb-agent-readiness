---
title: "Note only: 'Azure DocumentDB' mapped to legacy Cosmos DB databaseAccounts in cold quiz; already corrected by the Agent Kit azure-deployment skill"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 2
findings: 2
bucket: confusion-Q03
verdicts:
  skipped: note-only
---

# Note only: cold-quiz name collision "Azure DocumentDB" -> Cosmos DB databaseAccounts

In 2 of 100 runs, the cold answer to Q03 (Bicep/Terraform resource types) was `Microsoft.DocumentDB/databaseAccounts` + `azurerm_cosmosdb_account`, because the model resolved "Azure DocumentDB" to the original Cosmos DB DocumentDB (NoSQL) API. Correct: Azure DocumentDB (formerly Azure Cosmos DB for MongoDB vCore) deploys as `Microsoft.DocumentDB/mongoClusters` (Terraform `azurerm_mongo_cluster`).

## Skip reason
Model prior already corrected by the Agent Kit: `skills/azure-deployment/SKILL.md` and its Bicep/Terraform reference templates use only mongoClusters / azurerm_mongo_cluster. Both runs produced the correct grounded answer and generated no IaC, so the wrong type never reached a deliverable. The Learn asks in the findings would not fix a pre-retrieval recall error, and a deprecation note on databaseAccounts would be factually wrong (it still backs Cosmos DB RU accounts).

## Verification
- skipped: note-only (checks not run per stage instructions; skip reason judged strong).

## Finding ids
- F2241
- F2386
