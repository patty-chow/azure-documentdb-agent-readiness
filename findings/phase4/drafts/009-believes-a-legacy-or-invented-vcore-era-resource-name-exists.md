---
title: "Legacy/invented vCore IaC resource names (azurerm_documentdb_mongo_cluster, databaseAccounts) are a model prior already corrected by the azure-deployment skill"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 5
findings: 5
bucket: confusion-Q03
verdicts:
  skipped: note-only
---

# Note: invented vCore-era IaC resource names are a model prior the kit already corrects

In 5 of 100 samples, gpt-5-mini's cold answer to Q03 (Bicep/Terraform resource types) named a resource that does not exist or targets the RU-based Cosmos DB account: `azurerm_documentdb_mongo_cluster`, `azurerm_cosmosdb_mongo_cluster`, `Microsoft.DocumentDB/mongodbClusters`, or `Microsoft.DocumentDB/databaseAccounts` + `azurerm_cosmosdb_account`. The correct names are `Microsoft.DocumentDB/mongoClusters` (ARM/Bicep) and `azurerm_mongo_cluster` (AzureRM 4.x), with AzAPI as the escape hatch.

Secondary (pipeline): in two runs the grader's grounded answer also missed `azurerm_mongo_cluster`; grounding Q03 against the azure-deployment skill or the Learn quickstart-terraform page would fix that.

## Verification

- skipped: note-only. The three checks were not run, per stage instructions.
- Skip reason (accepted as strong): the Agent Kit `skills/azure-deployment/SKILL.md` (Steps 6a/6b/6c) and `references/terraform-cluster-template.md` already state the exact names, provider and API versions, and link the Learn Bicep/Terraform quickstarts. The invented names appear only in cold quiz answers; no generated app contains IaC or a wrong resource name. The findings' proposals duplicate existing skill content.

## Finding ids

- F0177
- F0419
- F0494
- F0694
- F1336
