---
title: "No kit change needed: mongosh/Bicep \"optional tooling\" asks are induced by the harness inventory, and the kit already documents the MCP and az fallbacks"
repo: abinav2307/azure-documentdb-agent-readiness
type: note-only
status: drop
priority: P3
sample_count: 11
findings: 11
bucket: other-inventory
verdicts:
  skipped: note-only
---

# Note: "state mongosh/Bicep are optional" asks are harness-induced; kit already documents the fallbacks

Eleven readiness findings asked the DocumentDB Agent Kit to declare mongosh and the Bicep CLI optional and to document the DocumentDB MCP tools and `az deployment group create --template-file main.bicep` as fallbacks. No kit change is warranted.

## Skip reason
- The harness inventory lists mongosh and bicep (factory/tools/environment.py) and prompts/readiness_checker.md forces one inventory recommendation per unavailable tool; 114 of 120 readiness reports recommended mongosh regardless of need.
- No build was blocked: all 11 runs are ready_with_gaps with zero blockers; builders verified via documentdb MCP tools (list_indexes, list_databases, explain_operation) and Python.
- The kit already covers the ask: skills/query-optimizer/SKILL.md pairs each MCP tool with its mongosh equivalent and says to use mongosh when MCP is unavailable; skills/azure-deployment/SKILL.md deploys Bicep through `az deployment group create` with only the Azure CLI as prerequisite; skills/mcp-setup/SKILL.md needs only node and git.
- F1603 misnames `list-connection-strings` (an `az documentdb mongocluster` subcommand) as an MCP tool.

Optional follow-up (harness, not kit): mark mongosh/bicep as optional in the inventory and relax the readiness prompt so unavailable optional tools do not force a recommendation.

## Verification
- skipped: note-only. The skip reason is specific and evidence-backed (harness inventory cause, zero blockers, existing kit coverage), so the theme is dropped without running the covered / premise / maintainer checks.

## Finding ids
F1087, F1351, F1603, F1699, F2165, F1537, F2438, F2664, F2758, F2921, F3473
