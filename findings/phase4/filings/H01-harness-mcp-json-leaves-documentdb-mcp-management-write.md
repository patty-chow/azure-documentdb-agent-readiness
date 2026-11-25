---
id: H01
title: "Harness mcp.json leaves documentdb-mcp management/write tools off, so vector-index requirements are scored as tool_unavailable"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: needs_sme
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P0
sample_count: 36
member_drafts:
  - 118-harness-mcp-profile-leaves-management-tools-off-so-every-vec.md
open_questions: 3
---

# Harness mcp.json leaves documentdb-mcp management/write tools off, so vector-index requirements are scored as `tool_unavailable`

> This repository belongs to a colleague (abinav2307). Coordinate with them before opening this PR.

## What happens today

The harness `mcp.json` starts `github:microsoft/documentdb-mcp` with only `TRANSPORT`, `AUTH_REQUIRED`, `ALLOW_UNAUTHENTICATED_STDIO` and `CONNECTION_PROFILES` in `env`. documentdb-mcp ships its write and management tools turned off by default (`src/config.ts` lines 212-213), which is intentional and documented (its README, and `skills/mcp-setup/SKILL.md` in the Agent Kit). So every builder call to `documentdb_create_index` is refused with:

```
Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.
```

and `documentdb_insert_documents` with the matching `ENABLE_WRITE_TOOLS` message (`src/security/authorization.ts` lines 44-50).

The scoring pipeline then misreads these refusals:

- `prompts/auditor.md` (line 30) defines `tool_unavailable` only as "a missing or refused tool prevented it", with no way to say the refusal came from the harness profile.
- `loop/findings.py` (about lines 169-176) maps every `tool_unavailable` requirement to target `documentdb-mcp`, so the refusals surface in the findings as MCP-server defects.

## Why it matters

Across the 221 run folders (104 sample folders) under `runs/` from one experiment of 100 samples (counts are from that single experiment and will change on a re-run):

- **36 of the 104 sample folders** hit at least one opt-in refusal: 32 the management refusal, 13 the write refusal.
- **All 58** `documentdb_create_index` calls failed; none succeeded.
- The audit recorded 88 requirement results in 29 samples as `not_met`/`partly_met` with `cause: tool_unavailable`, mostly the four vector-index requirements (index created in code, dimensions match the embedding model, seed creates the index idempotently, retrieval uses `$search` with `cosmosSearch`). That 88 covers every `tool_unavailable` cause, not only this refusal.

Two distortions follow:

1. Builders that called the tool correctly still lose the requirement. In `17-esg-scoring-pipeline` the builder asked for a `{"rationale_embedding": "cosmosSearch"}` key, `vector-hnsw`, 1536 dimensions to match `text-embedding-3-small`, cosine similarity, was refused twice and stopped.
2. Some builders silently degraded: `14-hyper-personalized-content-engine` and `15-financial-advisor-chatbot-rag` load the whole collection and rank by cosine in application code instead of issuing a `$search` query. That is a real readiness signal (they could have fallen back to a driver `createIndexes` call, since `node`, `python` and `mongosh` are on `DEFAULT_ALLOWED_COMMANDS` in `factory/config.py`), but today it is recorded as an MCP outage instead of as builder behaviour.

The scores therefore measure the harness profile, not the Agent Kit or the MCP server. documentdb-mcp is behaving as designed; nothing needs to go upstream.

This is also the root cause behind drafts 108 and 112 (documentdb-mcp items); those should be framed as UX improvements to the server, not bugs, and filed after this PR.

## Proposed change

**1. `mcp.json`**: enable the tools the build stage needs (the URI stays an environment placeholder):

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

Add one sentence to `_comment`: "ENABLE_MANAGEMENT_TOOLS and ENABLE_WRITE_TOOLS are opt-ins in documentdb-mcp; they are on here because the build stage is expected to create indexes and seed data against the experiment cluster."

**2. `loop/findings.py`** (around line 169): stop attributing harness-caused refusals to the MCP server:

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

**3. `prompts/auditor.md`** (cause list, line 30): extend the `tool_unavailable` definition with: "When the refusal is the MCP server's own opt-in message (ENABLE_MANAGEMENT_TOOLS / ENABLE_WRITE_TOOLS), quote it in `evidence`. Also judge whether the builder fell back to a driver `createIndex`/`createIndexes` call (the shell allows `node`, `python`, `mongosh`). A builder that neither created the index nor fell back, and shipped client-side ranking, is `builder_error`, not `tool_unavailable`."

**4. Re-run** the affected samples in the arms that load documentdb-mcp (`ARMS_WITH_DOCUMENTDB_MCP = {"default", "mcps-only"}` in `loop/run_loop.py`) so readiness scores reflect the kit and the server. If the intent is instead to keep these tools off and measure fallback behaviour, skip step 1 and keep steps 2 to 4.

## Evidence

- `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl` lines 50-52 (two refusals, then a decision to stop); `05-audit.json`
- `runs/13-product-q-a-chatbot-rag/20261125-055422/events.jsonl` line 72 (vector-hnsw, 1536 dims, refused; this call used a plain `{"embedding": 1}` key instead of `{"embedding": "cosmosSearch"}`, so it would have needed correcting even with the tool on)
- `runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json` (client-side cosine ranking, no `$search`)
- `runs/14-hyper-personalized-content-engine/20261124-205043/05-audit.json` (same degradation)
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/events.jsonl` line 123

## Open questions

1. Intent of the experiment (for the harness owner): should the build stage have management and write tools (step 1), or are they deliberately off to measure driver fallback? The rest of the PR applies either way.
2. Is turning on write and management tools against the shared experiment cluster acceptable to whoever owns that cluster?
3. Every `documentdb_create_index` call was refused before validation, so it is untested whether the tool accepts a `cosmosSearch` vector index (`vector-ivf`, `vector-hnsw`, `vector-diskann`) end to end. [needs SME confirmation] Can a documentdb-mcp maintainer confirm, so the re-run is not blocked by a second failure?

None of the reviewer's SME-flagged claims (change-stream limits, `$jsonSchema` enum support, 16500/429 behaviour, driver version floors, HNSW/IVF limits) appear in this PR. The retryWrites question is answered (2026-11-25, see findings/phase4/DECISIONS.md: retryable writes are not supported and `retrywrites=false` is required) and does not touch this PR.

## Source drafts

- 118-harness-mcp-profile-leaves-management-tools-off-so-every-vec.md (15 findings across 7 samples: F2213, F2318-F2320, F2420-F2421, F2582-F2585, F2836-F2837, F2869-F2870, F3008; the 36-sample figure above is a grep of all run folders, not a count of these finding ids)
