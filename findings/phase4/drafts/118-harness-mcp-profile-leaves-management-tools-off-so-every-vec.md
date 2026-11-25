---
title: "Harness mcp.json leaves documentdb-mcp management/write tools off, so vector-index requirements are scored tool_unavailable and misattributed to documentdb-mcp"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P0
sample_count: 7
findings: 15
bucket: mcp-server
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Harness mcp.json leaves documentdb-mcp management/write tools off, so vector-index requirements are scored `tool_unavailable` and blamed on documentdb-mcp

## What happens today

`mcp.json` starts `github:microsoft/documentdb-mcp` with `TRANSPORT`, `AUTH_REQUIRED`, `ALLOW_UNAUTHENTICATED_STDIO` and `CONNECTION_PROFILES` only. documentdb-mcp defaults both opt-in flags to false (`src/config.ts:212-213`) and refuses with:

```
Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.
```

(`src/security/authorization.ts:47-50`; the README, line 122, and the kit's `skills/mcp-setup/SKILL.md`, lines 154-155, both document the flags.)

Result across the 221 run folders in `runs/`:

- **58 of 58** `documentdb_create_index` calls failed with that message; **0** succeeded. 32 of the 104 sample folders in `runs/` hit it.
- 13 samples also hit `Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in.` on `documentdb_insert_documents`.
- The audit scored 88 `requirement_results` in 29 samples as `not_met`/`partly_met` with `cause: tool_unavailable` (all causes of `tool_unavailable`, not only this refusal), most of them the four vector-index requirements: index created in code, dimensions match the embedding model, seed creates the index idempotently, `$search`/`cosmosSearch` retrieval.
- `loop/findings.py:169-171` maps every `tool_unavailable` requirement to target `documentdb-mcp`, so these 88 results appear in the findings as MCP-server defects.

## Why it matters

The experiment is meant to measure the Agent Kit and the MCP servers, but these scores measure the harness profile. Two concrete distortions:

1. Builders that did the right thing with the tool (correct `cosmosSearchOptions`, correct `{"field": "cosmosSearch"}` key form, dimensions = 1536 matching `text-embedding-3-small`; e.g. `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl` lines 50-51) still lose the requirement.
2. Some builders silently degraded: `14-hyper-personalized-content-engine` and `15-financial-advisor-chatbot-rag` fetch the whole collection and rank by cosine in the app instead of issuing `$search`, because no index existed. That is a real readiness signal (the builder should have fallen back to driver `createIndex`, which `node`, `python` and `mongosh` on `DEFAULT_ALLOWED_COMMANDS` permit), but today it is recorded as an MCP outage rather than as builder behaviour.

## Proposed change

**1. `mcp.json`** – enable the tools the build stage needs:

```json
"env": {
  "TRANSPORT": "stdio",
  "AUTH_REQUIRED": "false",
  "ALLOW_UNAUTHENTICATED_STDIO": "true",
  "ENABLE_MANAGEMENT_TOOLS": "true",
  "ENABLE_WRITE_TOOLS": "true",
  "CONNECTION_PROFILES": "{\"default\":{\"authMode\":\"connectionString\",\"uri\":\"${DOCUMENTDB_URI}\"}}"
}
```

Add one sentence to the `_comment` noting that the two flags are opt-ins in documentdb-mcp and are on here because the build stage is expected to create indexes and seed data against the experiment cluster.

**2. `loop/findings.py`** (around line 169) – stop attributing harness-caused refusals to the MCP server:

```python
HARNESS_REFUSALS = ("Set ENABLE_MANAGEMENT_TOOLS=true", "Set ENABLE_WRITE_TOOLS=true")
...
if r.get("cause") == "tool_unavailable" and any(s in r.get("evidence", "") for s in HARNESS_REFUSALS):
    target = "pipeline"
elif r["cause"] == "skill_silent":
    target = "agent-kit"
else:
    target = "documentdb-mcp"
```

**3. `prompts/auditor.md`** (cause list, line 30) – extend `tool_unavailable`: when the refusal is the MCP server's own opt-in message, say so in `evidence`, and additionally judge whether the builder fell back to a driver-based `createIndex`/`createIndexes` (the shell allows `node`, `python`, `mongosh`). A builder that neither created the index nor fell back and shipped client-side ranking should be `builder_error`, not `tool_unavailable`.

**4. Re-run** the 32 affected samples in the `default` and `mcps-only` arms (`ARMS_WITH_DOCUMENTDB_MCP`) so readiness scores reflect the kit and the server, not the profile. If the intent is instead to keep management tools off and measure fallback behaviour, skip step 1 and keep steps 2-4.

## Evidence

- `runs/13-product-q-a-chatbot-rag/20261125-055422/events.jsonl` line 72 (vector-hnsw, 1536 dims, refused; note this call also used the plain `{"embedding": 1}` key rather than `{"embedding": "cosmosSearch"}`, so it would have needed correcting even with the tool enabled); `05-audit.json` requirement_results
- `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl` lines 50-52 (two refusals, then log_decision to stop); `05-audit.json`
- `runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json` (client-side cosine ranking, no `$search`)
- `runs/14-hyper-personalized-content-engine/20261124-205043/05-audit.json` (same degradation)
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/events.jsonl` line 123

Scope of this draft: 15 findings across 7 samples (F2213, F2318-F2320, F2420-F2421, F2582-F2585, F2836-F2837, F2869-F2870, F3008); the counts above come from a grep of all 221 run folders (58 `documentdb_create_index` calls, all with outcome `exception`).

## Verification

### 1. Already covered? confirmed (not there)
The pipeline's `mcp.json` (documentdb server `env`) sets only `TRANSPORT`, `AUTH_REQUIRED`, `ALLOW_UNAUTHENTICATED_STDIO` and `CONNECTION_PROFILES`; neither `ENABLE_MANAGEMENT_TOOLS` nor `ENABLE_WRITE_TOOLS` is present. `loop/findings.py` (requirement_results loop, about lines 169-176) still maps any `tool_unavailable` to `"documentdb-mcp"` (`"agent-kit" if r["cause"] == "skill_silent" else "documentdb-mcp"`). `prompts/auditor.md` line 30 defines `tool_unavailable` only as "a missing or refused tool prevented it", with no harness-profile distinction. Nothing in the harness implements the fix.

### 2. Premise true? confirmed (counts corrected)
- `documentdb-mcp/src/config.ts` lines 212-213: `writeTools: parseBoolean(process.env.ENABLE_WRITE_TOOLS, false)` and `managementTools: parseBoolean(process.env.ENABLE_MANAGEMENT_TOOLS, false)`.
- `documentdb-mcp/src/security/authorization.ts` lines 44-50: throws "Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in." and "Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in."
- `documentdb-mcp/README.md` line 122 and lines 148-149 document both flags as off by default; `documentdb-agent-kit/skills/mcp-setup/SKILL.md` line 155 tells users to add `"ENABLE_MANAGEMENT_TOOLS": "true"` to `env`.
- Grep of `runs/*/*/events.jsonl`: 58 `documentdb_create_index` calls, 58 with outcome `exception`; 32 sample folders hit the management refusal, 13 hit the write refusal; 221 run folders, 104 sample folders.
- `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl` lines 50-52: two create_index calls with `{"rationale_embedding": "cosmosSearch"}`, `vector-hnsw`, 1536 dims, COS, then a `log_decision` to stop retrying. Consistent with Azure DocumentDB vector index syntax (cosmosSearch, vector-hnsw).
- `factory/config.py` line 15-16: `DEFAULT_ALLOWED_COMMANDS` includes python, node and mongosh, so a driver fallback was possible. `loop/run_loop.py` line 71: `ARMS_WITH_DOCUMENTDB_MCP = {"default", "mcps-only"}`.
- Correction applied: the draft said 90 requirement_results in 30 samples; a recount of `05-audit.json` gives 88 in 29 samples, and that count covers every `tool_unavailable` cause, not only this refusal. Also noted that the sample-13 call at line 72 used a plain `{"embedding": 1}` key, so not every refused call was otherwise correct.

### 3. Maintainer skeptic: confirmed
As harness maintainer I would accept this. It names exact files (`mcp.json`, `loop/findings.py`, `prompts/auditor.md`), gives concrete diffs, is backed by run evidence, and fixes a measurement defect that misattributes harness failures to microsoft/documentdb-mcp. It belongs in this repository: documentdb-mcp's opt-in defaults are intentional and documented, so nothing goes upstream.

## Finding ids

- F2213
- F2318
- F2319
- F2320
- F2420
- F2421
- F2582
- F2583
- F2584
- F2585
- F2836
- F2837
- F2869
- F2870
- F3008
