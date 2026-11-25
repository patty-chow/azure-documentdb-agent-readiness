---
title: "No action: stale mongodbClusters / azurerm_mongodb_cluster prior already corrected by the Agent Kit and Learn quickstarts"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 1
findings: 1
bucket: confusion-Q03
verdicts:
  skipped: note-only
---

# Note only: stale "mongodbClusters" / "azurerm_mongodb_cluster" prior already corrected

In 1 of 100 samples (17-esg-scoring-pipeline), the cold answer to Q03 recalled `Microsoft.DocumentDB/mongodbClusters` with an outdated preview API version and Terraform `azurerm_mongodb_cluster`, under legacy "Cosmos DB for MongoDB vCore" naming. Correct: `Microsoft.DocumentDB/mongoClusters` (current API 2025-09-01) and `azurerm_mongo_cluster` (AzureRM 4.x). After one Learn search the grounded answer was correct, and the build produced no IaC (run environment forbade provisioning), so nothing downstream was affected.

The Agent Kit already pins the type, API version and Terraform resource in skills/azure-deployment/SKILL.md, both reference templates and examples/azure-deployment/main.bicep; the Learn quickstarts and templates reference carry the same mapping.

Decision: no issue or PR.

## Verification

- skipped: note-only. Skip reason (strong): model prior already corrected by the kit and Learn; 1 sample; grounded answer correct; no IaC generated.
- Evidence: runs/17-esg-scoring-pipeline/20261124-192259/02-readiness.json (Q01, Q03); 05-audit.md line 134; 01-prompt-review.md lines 30, 60.

## Finding ids

- F2840
