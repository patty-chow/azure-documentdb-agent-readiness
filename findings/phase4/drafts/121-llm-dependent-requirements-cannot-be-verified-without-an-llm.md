---
title: "Audit marks LLM-dependent requirements tool_unavailable / documentdb-mcp when the app runs without an LLM key"
repo: abinav2307/azure-documentdb-agent-readiness
type: note-only
status: drop
priority: P3
sample_count: 1
findings: 1
bucket: mcp-server
verdicts:
  skipped: note-only
---

# Audit marks LLM-dependent requirements as tool_unavailable when the app runs without an LLM key

**What happens today**
In `11-care-gap-identification-pipeline`, the audit scored "agent prioritises the patient list using the LLM" as `partly_met` with `cause: tool_unavailable`, and extraction targeted `documentdb-mcp`. The app calls the LLM through LangChain when `OPENAI_API_KEY` is set and otherwise uses a deterministic fallback. The audit environment had no model key, so the LLM path never ran.

**Why it is note-only**
1 of 100 samples. Not a gap in DocumentDB, the MCP server, the Agent Kit or Learn docs. The only cost is noise in the mcp-server "missing tool" counts.

**Optional harness tweak (target: pipeline)**
- Classify requirements blocked only by a missing model credential as `env_missing` / `not_applicable`, not `tool_unavailable`.
- Or pass the harness's Azure OpenAI settings to the app as env vars during verification (never written to the app folder).

**Evidence**
- runs/11-care-gap-identification-pipeline/20261124-194646/05-audit.json
- runs/11-care-gap-identification-pipeline/20261124-194646/05-audit.md
- runs/11-care-gap-identification-pipeline/20261124-194646/app/src/agent.py
- runs/11-care-gap-identification-pipeline/20261124-194646/app/.env.example

## Verification

Skipped: note-only. Skip reason: this is a harness classification artifact, not a product gap; the app's fallback worked as designed, so no issue for documentdb-mcp, Agent Kit or Learn docs is warranted. The reason is sound, so status is drop.

## Finding ids

- F1784
