---
title: "Q03 model prior: vCore cluster assumed to be Microsoft.DocumentDB/databaseAccounts / azurerm_cosmosdb_account (already corrected; no fix)"
repo: Azure/documentdb-agent-kit
type: note-only
status: drop
priority: P3
sample_count: 93
findings: 97
bucket: confusion-Q03
verdicts:
  skipped: note-only
---

# Note: Q03 databaseAccounts prior is already corrected by Learn and the Agent Kit

Cold, gpt-5-mini answered the Bicep/Terraform question with the RU-based Cosmos DB account resource (`Microsoft.DocumentDB/databaseAccounts`, `azurerm_cosmosdb_account`) in 93 of 100 samples. The correct type is `Microsoft.DocumentDB/mongoClusters` (Terraform `azurerm_mongo_cluster` or azapi). This is a training-data prior from the former name "Azure Cosmos DB for MongoDB vCore" and the shared provider namespace.

## Skip reason

Every grounded answer landed on `Microsoft.DocumentDB/mongoClusters` (via Learn MCP, the `documentdb-azure-deployment` skill, or the ARM template reference), and no build stage wrote IaC with the wrong type. Learn quickstarts and the Agent Kit skill already state the correct type. Optional hardening only: a one-line negative contrast in skills/azure-deployment/SKILL.md. Pipeline note: the 9 could_not_verify outcomes come from the 2026-11-25 06:xx rerun batch that ran without skills/MCP.

## Verification

Skipped: note-only. The skip reason is strong (zero downstream failures, existing coverage), so status is drop.

## Finding ids

F0002, F0038, F0070, F0106, F0146, F0213, F0256, F0285, F0313, F0347, F0387, F0454, F0523, F0555, F0595, F0627, F0659, F0724, F0762, F0791, F0822, F0845, F0886, F0915, F0941, F0967, F0998, F1038, F1072, F1100, F1129, F1158, F1196, F1222, F1257, F1296, F1367, F1399, F1432, F1485, F1520, F1555, F1588, F1622, F1654, F1681, F1715, F1751, F1787, F1824, F1858, F1888, F1920, F1949, F1980, F2015, F2050, F2081, F2119, F2151, F2183, F2215, F2286, F2323, F2356, F2424, F2457, F2484, F2515, F2549, F2588, F2618, F2646, F2681, F2710, F2744, F2776, F2803, F2873, F2906, F2939, F2973, F3011, F3039, F3070, F3108, F3142, F3174, F3224, F3255, F3295, F3322, F3358, F3391, F3423, F3457, F3496
