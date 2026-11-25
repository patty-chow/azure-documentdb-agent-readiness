---
title: "No action: legacy \"Cosmos DB for MongoDB vCore\" framing of the cluster resource is a model prior already corrected by the kit and Learn"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 5
findings: 5
bucket: confusion-Q01
verdicts:
  skipped: note-only
---

# Note only: legacy vCore naming of the cluster resource (confusion Q01, legacy_vcore_naming)

In 5 of 100 samples, gpt-5-mini answered cold quiz Q01 with `Microsoft.DocumentDB/databaseAccounts` and described the cluster in "Azure Cosmos DB for MongoDB vCore" terms. In every one of those runs the grounded answer was correct (`Microsoft.DocumentDB/mongoClusters`). It came from `skills/azure-deployment/SKILL.md` or from the Learn mongoClusters template reference. No generated app used `databaseAccounts`.

## Skip reason
This is a model prior, not a gap in the docs or the kit. The azure-deployment skill gives the resource type `Microsoft.DocumentDB/mongoClusters` at the top. No kit skill mentions `databaseAccounts`. The Learn overview already gives the former product name. The rename changed only the product name and the CLI group (`az documentdb mongocluster`), not the resource type. The wrong prior never reached any build output.

## Verification
- skipped: note-only (the drafter decided no action is needed, so the three checks were not run). The skip reason is strong: in all five runs grounding fixed the answer, and the wrong value never reached code.

## Finding ids
- F0000
- F0036
- F0175
- F0417
- F1334
