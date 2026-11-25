---
title: "No action: 'mongodbClusters' is a cold-recall near-miss already corrected by Learn and the Agent Kit"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 4
findings: 4
bucket: confusion-Q01
verdicts:
  skipped: note-only
---

# No action: 'mongodbClusters' is a cold-recall near-miss

In the cold quiz (no skills, docs or MCP), gpt-5-mini sometimes named the cluster resource type `Microsoft.DocumentDB/mongodbClusters` (one answer also invented `@2024-01-01`). The real token is `Microsoft.DocumentDB/mongoClusters`; the Agent Kit pins API `2025-09-01`. Every grounded answer corrected it, and no build, audit or doc-gaps artifact in the four runs contains the misspelling.

## Skip reason
Model-prior near-miss, not a documentation or kit gap. Learn pages already use `mongoClusters` and no Learn page with `mongodbClusters` was found; the Agent Kit azure-deployment SKILL.md, bicep-cluster-template.md, main.bicep, deploy.sh and the storage/HA skills all pin `Microsoft.DocumentDB/mongoClusters@2025-09-01`. The proposed alias/deprecation notes would document a token that was never valid.

## Verification
- skipped: note-only (checks not run per stage instructions; skip reason judged strong).

## Finding ids
- F0211
- F0492
- F0625
- F2838
