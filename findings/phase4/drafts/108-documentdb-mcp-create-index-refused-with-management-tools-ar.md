---
title: "create_index/insert refusals (\"Management tools are disabled by default\") are not actionable for agents: gated tools are still listed, message omits that the flag is operator-side and names no fallback"
repo: microsoft/documentdb-mcp
type: pr
status: ready_with_edits
priority: P0
sample_count: 32
findings: 4
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Make the "Management tools are disabled by default" refusal actionable for agents (and stop listing tools that cannot be called)

## What happens today

With the default env (no `ENABLE_MANAGEMENT_TOOLS`), `registerToolDefinitions` in `src/tools/registry.ts` still registers all 18 tools, so an MCP client sees `create_index` in the tool list. The call is only refused inside `withDbGuard` → `assertCapabilityEnabled` (`src/security/authorization.ts:49-51`):

```
Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.
```

Three things make this a dead end for an automated caller:

1. The flag is a **server-process env var** (the `env` block of the MCP client config). The message does not say so, so an agent cannot tell whether this is something it can fix, an input problem, or operator policy.
2. It names **no fallback**. The obvious one, create the index from application code with the driver's `createIndex`/`createIndexes` and await the build, is never mentioned, nor that `list_indexes`, `get_statistics` and `explain` (read tier) still work for verification.
3. The README (line 122) says "By default only read tools are exposed", but gated tools *are* exposed; they just fail when called. `tool_list.md` documents the flag; the tool descriptions themselves do not.

The `write` tier has the identical shape (`insert_documents` → "Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in.").

## Why it matters

In an experiment that had gpt-5-mini build 100 Azure DocumentDB sample apps with this server (stdio, defaults, plus the DocumentDB Agent Kit skills):

- **32 of 100 builds** hit the refusal: 58 `documentdb_create_index` calls, every one rejected; write-tier calls (`insert_documents`) were rejected in 13 builds.
- In **17 of those 58 calls** the model immediately re-issued the same `create_index` with `keys`/`options` re-serialized as JSON strings, i.e. it read the error as an argument-parsing problem, not policy.
- In 17 of the 32 builds no driver-side `createIndex` was added afterwards. At least 3 shipped with `documentdb_explain_operation` showing a `COLLSCAN` on the query the index was designed for; the RAG build shipped with `list_indexes` showing only `_id` and no vector index at all.
- The index designs were correct (ESR compound `{paymentReference:1, stageTimestamp:1}`, `cosmosSearchOptions` `vector-hnsw` dimensions 1536, `vector-diskann`, unique `chunk_id`). The defect is purely operational: the server advertised a tool, refused it, and gave the agent nothing to act on.

## Proposed change

### 1. `src/security/authorization.ts`: actionable messages

Keep the existing prefixes (tests in `test/security/authorization.test.ts:81-82` and `test/tools/dbGuard.test.ts:51` match on them) and extend:

```ts
export function assertCapabilityEnabled(requiredRole: ToolRole, toolName?: string): void {
    const tool = toolName ? `'${toolName}' ` : '';
    ...
    if (requiredRole === 'management' && !config.capabilities.managementTools) {
        throw new Error(
            `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in. ` +
            `${tool}is a 'management' tool; this flag is server configuration set in the env block of the MCP client config ` +
            `by whoever launched the server, not a tool argument, so retrying with different arguments will not help. ` +
            `Either ask the operator to set ENABLE_MANAGEMENT_TOOLS=true and restart the server, or perform the operation ` +
            `from application code with the DocumentDB/MongoDB driver (for indexes: createIndex/createIndexes, then wait for ` +
            `the build). Read tools such as list_indexes, get_statistics and explain remain available to verify the result.`,
        );
    }
}
```

Same treatment for the write branch (fallback: driver `insertMany`/`updateOne`). In `src/tools/utils/dbGuard.ts` (the `assertCapabilityEnabled(policy.requiredRole)` call, around line 96) pass `policy.toolName`; `registerToolDefinitions` already threads `toolName` into the policy.

### 2. `src/tools/registry.ts`: make the tool list match the README

`config.capabilities` is process-global and known at startup, so either:

- **Preferred:** skip `server.registerTool` for a definition whose tier is disabled (`write` when `!writeTools`, `management` when `!managementTools`). This makes "only read tools are exposed" true and the agent plans around the driver from the start. Add a startup log line listing the skipped tools.
- **Minimal:** keep registering but append to `description`: `"DISABLED on this server: requires ENABLE_MANAGEMENT_TOOLS=true (server env). Use the driver's createIndex instead."`

### 3. `README.md`

- Tools table (lines 245-262): the table already has a `Role` column (`read` / `write` / `management`), but nothing ties a role to its flag. Add one line above the table mapping `write` -> `ENABLE_WRITE_TOOLS=true` and `management` -> `ENABLE_MANAGEMENT_TOOLS=true` (or rename the column to `Role (enable flag)`).
- Replace line 122's "By default only read tools are exposed" with the real behaviour chosen in (2), show the exact refusal text, and add two sentences on the recommended agent fallback (driver `createIndex` + `list_indexes`/`explain` to verify).
- In the stdio quickstart JSON, show `"ENABLE_MANAGEMENT_TOOLS": "true"` as the local-dev example, with a comment that it stays off for shared/HTTP deployments.

### 4. Default

Leaving management off by default is consistent with `docs/design-doc.md` and `docs/permission-model.md`; this PR does not propose flipping it. The quickstart example in (3) covers the dev case, where index creation is the main reason to run the server.

## Evidence (run folders from the experiment; no connection data)

- `runs/12-cross-border-payment-audit-trail/20261124-201744/events.jsonl` lines 33, 35 (ESR compound refused twice; line 34 decision "retry without connection_profile"), line 43 (`explain` → COLLSCAN, shipped)
- `runs/13-product-q-a-chatbot-rag/20261125-055422/events.jsonl` line 71 (`list_indexes` → only `_id`), line 72 (`vector-hnsw`, 1536 dims refused; no index ever created)
- `runs/01-fraud-detection-with-vector-similarity/20261124-185817/events.jsonl` lines 34, 36 (`vector-ivf` refused, retried with stringified `keys`/`options`), followed by `insert_documents` write-tier refusals
- `runs/13-household-grouping-linkage/20261124-204947/events.jsonl` lines 40, 42 (compound index refused twice, later `explain` COLLSCAN)
- `runs/15-financial-advisor-chatbot-rag/20261124-192021/events.jsonl` lines 67-68 (`vector-diskann` refused, retried as strings)

Companion changes outside this repo: the Agent Kit `indexing` and `vector-search` skills should tell agents to fall back to the driver and await completion when the MCP tool is unavailable (`skills/mcp-setup/SKILL.md:154-155` already documents the flags), and harnesses that build apps should set `ENABLE_MANAGEMENT_TOOLS=true` in their `mcp.json` `env`.

## Verification

### 1. Already covered? partially_covered
The flag is named and documented, but the actionable parts the draft asks for are not there.
- `src/security/authorization.ts` `assertCapabilityEnabled` throws exactly "Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in." (and the Write equivalent). It names the flag but not that it is server-side configuration, names no tool, and suggests no driver fallback or read-tier verification.
- `README.md:122` says to set the flags in the `env` block and claims "By default only read tools are exposed"; `README.md:149` shows `ENABLE_MANAGEMENT_TOOLS=false`; the tools table (245-262) has a `Role` column but no flag mapping. `tool_list.md:13` lists `create_index (management)`.
- `src/tools/registry.ts` `registerToolDefinitions` calls `server.registerTool` for every definition unconditionally, so gated tools are listed; descriptions carry no gate notice.
- Agent kit: `skills/mcp-setup/SKILL.md:155` documents adding `"ENABLE_MANAGEMENT_TOOLS": "true"` to `env`; no skill tells the agent what to do on the refusal at runtime (companion change, out of this repo).

### 2. Premise true? confirmed
- The draft correctly corrects the theme summary: the refusal does name ENABLE_MANAGEMENT_TOOLS (source quoted above).
- README "only read tools are exposed" vs. unconditional registration is a real mismatch (registry.ts lines 69-94).
- Capability check runs in `withDbGuard` before authorization (`src/tools/utils/dbGuard.ts`, ~line 96); `policy.toolName` is available there.
- Run counts re-checked over `runs/*/*/events.jsonl`: 32 run folders contain the management refusal, 58 occurrences; 13 run folders contain the write-tier refusal (draft said "18 more" insert rejections; replaced with the verified 13-builds figure).
- Corrections applied: README tools table already has a Role column (changed "add a Requires column" to "map Role to flag"); table line range corrected to 245-262; test references corrected to `test/security/authorization.test.ts:81-82` and `test/tools/dbGuard.test.ts:51` (no `scripts/e2e-tests` match found).
- Nothing in the draft contradicts Azure DocumentDB facts (cosmosSearchOptions vector-hnsw/vector-diskann/vector-ivf, driver createIndexes).

### 3. Maintainer skeptic: confirmed
Names concrete files and functions (authorization.ts, dbGuard.ts, registry.ts, README.md), keeps the secure default and the test-matched prefixes, and offers a minimal option. The behaviour/README mismatch is a genuine bug a maintainer would accept. Scope is right: this is the documentdb-mcp repo; agent-kit and harness changes are listed as companions only.

Priority P0: the refusal blocked index creation in 32 of 100 builds and shows a real defect (tool advertised but refused, README mismatch) in the MCP server.

## Finding ids

- F2041
- F2042
- F2312
- F2314
