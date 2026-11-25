---
title: "Cold-quiz belief that the OSS DocumentDB project is unrelated to Azure DocumentDB (model prior, no change needed)"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 14
findings: 14
bucket: confusion-Q14
verdicts:
  skipped: note-only
---

# Note only: "Azure DocumentDB is proprietary / unrelated to the open-source DocumentDB project" is a model prior

In 14 of 101 runs, the gpt-5-mini cold (ungrounded) answer to Q14 said the Azure service is unrelated to the open-source DocumentDB project, or that it is a proprietary Microsoft service. That is wrong. Azure DocumentDB is the managed Azure service built on the open-source, PostgreSQL-based DocumentDB engine (github.com/documentdb/documentdb). It was formerly called Azure Cosmos DB for MongoDB vCore. Only Amazon DocumentDB is unrelated.

In every affected run, the grounded answer got it right. No generated app, 05-audit.json or doc-gaps.md repeats the wrong claim. Microsoft Learn already covers the lineage: the overview's "Open source, with no SSPL" and "Naming and history" sections, and the FAQ. So does the Agent Kit (README.md line 12, AGENTS.md line 3, skills/azure-deployment/SKILL.md line 9). The findings propose adding a lineage paragraph, which would duplicate the existing "Naming and history" section.

Related nit: AGENTS.md and azure-deployment/SKILL.md link github.com/microsoft/documentdb instead of github.com/documentdb/documentdb. This nit is folded into the naming-theme Agent Kit PR.

## Skip reason

This is a model prior, and it only appears in the ungrounded cold-quiz stage. All 14 grounded answers corrected it, and the claim never reached a built sample or an audit. Learn and the Agent Kit already state the lineage. The skip reason is strong, so the status is drop.

## Verification

- skipped: note-only (the three checks were not run, per stage instructions)

## Finding ids

F0047, F0078, F0356, F0502, F0635, F0855, F1081, F1832, F2059, F2128, F2690, F3019, F3329, F3465
