---
title: "dotnet listed as a missed accelerator for a Python-only sample (model speculation; no action)"
repo: none
type: note-only
status: drop
priority: P3
sample_count: 1
findings: 1
bucket: kit-accelerator-missed
verdicts:
  skipped: note-only
---

# Note: `dotnet` reported as a missed accelerator for a Python-only sample

**Status: note-only, no issue or PR.**

In run `17-stress-testing-multi-agent-runner/20261124-202407` the readiness stage listed `dotnet` in `accelerators_missed`. The prompt asked for a Python LangChain multi-agent system and the built app is Python only. The model's own inventory recommendation in the same file says dotnet is not needed for this sample. The model repeated the unavailable tools from the harness inventory without checking whether this sample needed them. The readiness prompt already says not to list tools the sample has no use for.

Optional low-value harness guard: drop any `accelerators_missed` entry whose `inventory_recommendations` row says the tool is not needed.

## Skip reason

This happened in 1 of 120 run folders. The model's own inventory row says dotnet is not needed for this Python sample. Nothing in the prompt, the Agent Kit or the pipeline requires .NET, and the kit has no toolchain setup skill to amend. The cause is the model speculating about a toolchain. It is not a gap in the Agent Kit, the MCP server or the Learn docs.

## Verification

- skipped: note-only. The drafter found that no action is warranted, so the coverage, premise and maintainer checks were not run. The skip reason is strong because the same run's evidence contradicts itself (`02-readiness.json` accelerators_missed vs its inventory recommendation for dotnet).

## Finding ids

- F2958
