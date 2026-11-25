---
title: "documentdb-mcp: gated write/management tools are listed but fail at call time; make the opt-in (ENABLE_WRITE_TOOLS / ENABLE_MANAGEMENT_TOOLS) and the driver fallback visible to agents"
repo: microsoft/documentdb-mcp
type: pr
status: ready_with_edits
priority: P1
sample_count: 8
findings: 8
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Make write/management opt-in visible to agents: README section, tool descriptions, error text, driver fallback

## What happens today

`create_index`, `insert_documents` and the other `management`/`write` tools are always registered (`src/tools/registry.ts`, `registerToolDefinitions` loops over every definition), so they appear in `tools/list` even when `ENABLE_MANAGEMENT_TOOLS` / `ENABLE_WRITE_TOOLS` are unset. The gate only fires at call time (`src/security/authorization.ts`, `assertCapabilityEnabled`), returning:

```
Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.
```

An agent (or a human following the quickstart) therefore sees the tool, calls it, and fails. The README does mention the flags, but in scattered places an agent skimming the quickstart does not connect to the Tools table: one sentence after the VS Code config block (line 122: "By default only read tools are exposed."), the `.env` sample under Configuration (lines 147-149), one sentence under Authentication And Authorization (line 167: write and management tools "also require explicit capability flags"), the write-tool example (line 301) and the Security Checks list (line 324). Line 122 is not accurate: the tools are exposed in `tools/list`, they are denied at call time. The Tools table (line 240) has a Role column but never says that `management` and `write` map to those env vars; tool descriptions (`'Create an index on a collection'`) say nothing about the gate; and the error names the env var but offers no alternative path.

## Why it matters

In an automated run of 100 Azure DocumentDB sample builds (gpt-5-mini, this server launched from the README's stdio quickstart config with no `ENABLE_*` flags), **36 of the 100 samples hit one of these two errors** in their event logs (32 samples the management error, 13 the write error). Eight audit findings (eight distinct samples) called out the same gap. Observed consequences:

- Builders fell back to ad-hoc pymongo `runCommand` / Mongoose index declarations and never verified the server-side index; `explain()` showed `COLLSCAN` (12-cross-border-payment-audit-trail).
- Index creation was demoted to a manual README step instead of being part of `init_db()` (05-kyc-document-ingestion-pipeline).
- One builder over-generalized from the failure into a false belief that cosmosSearch options "aren't available via the standard MongoDB createIndex API" and that a management-plane/portal path is required (14-hyper-personalized-content-engine). That is wrong: `createIndexes` with `cosmosSearchOptions` via any MongoDB driver is the normal data-plane path. A one-line fallback in the error text would have prevented it.
- Several runs retried the same call twice before giving up (12-cross-border, 13-product-q-a-chatbot-rag).

## Proposed change (this PR)

### 1. `README.md`: add a section right after the Public Preview callout

```markdown
## Write and management tools are opt-in

By default the server only *succeeds* on `read` tools. `write` and `management`
tools are still listed in `tools/list` but every call is denied until you opt in:

| Env var | Tools it unlocks |
| --- | --- |
| `ENABLE_WRITE_TOOLS=true` | `insert_documents`, `update_documents`, `delete_documents`, `find_and_modify` |
| `ENABLE_MANAGEMENT_TOOLS=true` | `create_index`, `drop_index`, `drop_collection`, `rename_collection`, `drop_database`, `current_ops` |

They are off by default because an MCP client (or a prompt-injected agent) can
otherwise mutate or drop data through the server. Enable them only for a profile
that points at a dev/test cluster, and turn them back off afterwards. On HTTP/SSE
transports the caller also needs the matching Entra role (`write` or
`management`, see *Authentication And Authorization*); trusted local stdio
(`TRUST_LOCAL_STDIO=true`) skips the role check but not these flags.

Local/CI launch with both enabled (stdio):

    "env": {
      "TRANSPORT": "stdio",
      "TRUST_LOCAL_STDIO": "true",
      "ENABLE_WRITE_TOOLS": "true",
      "ENABLE_MANAGEMENT_TOOLS": "true",
      "CONNECTION_PROFILES": "{\"dev\":{\"authMode\":\"connectionString\",\"uri\":\"<dev cluster uri>\"}}"
    }

**If you cannot or do not want to enable them**, do the same operation from
application code with any MongoDB driver; this is the normal data-plane path and
does not need the MCP server or the Azure control plane:

    // Node.js driver — vector index on Azure DocumentDB
    await db.collection("docs").createIndexes([{
      name: "vec_idx",
      key: { embedding: "cosmosSearch" },
      cosmosSearchOptions: { kind: "vector-hnsw", m: 16, efConstruction: 64,
                             similarity: "COS", dimensions: 1536 }
    }]);
    await db.collection("docs").insertMany(seedDocs);

    # pymongo
    db.command({"createIndexes": "docs", "indexes": [{ ...same spec... }]})
```

Also: change line 122 from "By default only read tools are exposed." to "By default only read tools succeed; write/management calls are denied until enabled (see *Write and management tools are opt-in*)." and add above the Tools table: "Role `write` requires `ENABLE_WRITE_TOOLS=true`; role `management` requires `ENABLE_MANAGEMENT_TOOLS=true`."

### 2. `src/security/authorization.ts`: give the agent an exit

```ts
throw new Error('Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true on the MCP server to opt in, or perform the write from application code with a MongoDB driver (e.g. collection.insertMany).');
throw new Error('Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true on the MCP server to opt in, or create the index from application code with a MongoDB driver (collection.createIndexes / createIndexes command; cosmosSearchOptions are supported there).');
```

The existing assertion in `test/tools/dbGuard.test.ts` (line 51, `toContain('Write tools are disabled by default')`) still passes because the prefix is unchanged; add a matching assertion for the management message and the new fallback text.

### 3. Tool descriptions (`src/tools/index-tools.ts`: `create_index`, `drop_index`; `collection-tools.ts`: `drop_collection`, `rename_collection`, `current_ops`; `database-tools.ts`: `drop_database`; `document-tools.ts`: `insert_documents`, `update_documents`, `delete_documents`, `find_and_modify`)

Prefix each `management` tool description with `Requires ENABLE_MANAGEMENT_TOOLS=true on the server. ` and each `write` tool with `Requires ENABLE_WRITE_TOOLS=true on the server. `, e.g. `'Requires ENABLE_MANAGEMENT_TOOLS=true on the server. Create an index on a collection'`. Agents read descriptions before calling; this is the cheapest fix.

### 4. For maintainers to decide (not in this PR)

Should `registerToolDefinitions` skip definitions whose capability is disabled, so `tools/list` matches what will succeed? That is what the current README wording implies and what agents expect. It is a behavior change (clients that enable the flag later would need a reconnect), so I am only raising it.

## Mirror in Azure/documentdb-agent-kit

`skills/mcp-setup/SKILL.md` already documents the flags (lines 154-155). Add one Troubleshooting bullet (section at line 191) keyed on the exact error text: "**`Management tools are disabled by default` / `Write tools are disabled by default`**: the server is running read-only. Either add `ENABLE_MANAGEMENT_TOOLS`/`ENABLE_WRITE_TOOLS` to the server `env` and restart, or do the operation in app code with the driver (`createIndexes` with `cosmosSearchOptions` works there)." Sample READMEs can then point to that line.

## Evidence (run folders from the 100-sample experiment)

- `runs/14-hyper-personalized-content-engine/20261124-205043/doc-gaps.md` (opt-in error, then false belief that driver createIndex cannot carry cosmosSearch options)
- `runs/12-cross-border-payment-audit-trail/20261124-201744/doc-gaps.md` (two failed create_index calls, COLLSCAN in explain)
- `runs/05-kyc-document-ingestion-pipeline/20261124-190500/doc-gaps.md` (index creation demoted to manual step)
- `runs/13-product-q-a-chatbot-rag/20261125-055422/events.jsonl` (ToolExecutionException on create_index during vector-search verification)
- `runs/17-rare-disease-literature-search/20261124-195633/doc-gaps.md` (pymongo runCommand workaround)

Note for reviewers: the experiment harness launched the server without the flags, so part of the hit rate is the harness's choice. The documentation and error-message gap is real regardless: the README quickstarts produce the same configuration, and nothing visible to the caller before the error explains the gate or the fallback.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? partially_covered
The opt-in flags exist and are mentioned, but not where an agent looks and not completely.
- microsoft/documentdb-mcp `README.md` line 122: "To enable write or management tools, also set `ENABLE_WRITE_TOOLS` ... and/or `ENABLE_MANAGEMENT_TOOLS` ... By default only read tools are exposed." Lines 147-149 (`.env` sample, both false), line 167 ("Write and management tools also require explicit capability flags"), line 301, line 324 ("Default-off gates for write and management tools").
- Not covered: the Tools table (lines 240-264) shows Role only, no flag mapping; tool descriptions (`src/tools/index-tools.ts` line 19 "Create an index on a collection") do not mention the gate; the error text in `src/security/authorization.ts` lines 47/50 names the flag but no fallback; no statement that gated tools still appear in `tools/list`.
- Azure/documentdb-agent-kit `skills/mcp-setup/SKILL.md` lines 154-155 document the flags; the Troubleshooting section (line 191) has no entry for the deny error. No other mention in `skills/` or `knowledge-base/`.
- Learn is not the right home (server-specific config); the draft already targets the MCP repo.

### 2. Premise true? confirmed
- `src/tools/registry.ts` `registerToolDefinitions` loops over every definition and calls `server.registerTool`; the gate is applied at call time by `withDbGuard` -> `assertCapabilityEnabled` (`src/security/authorization.ts` lines 42-52). So gated tools are listed but denied, and README line 122 ("only read tools are exposed") is inaccurate.
- Error strings quoted in the draft match `authorization.ts` lines 47 and 50 exactly. Flags default false in `src/config.ts` lines 212-213.
- Tool-to-role mapping in the proposed table matches `requiredRole` in `src/tools/*.ts` and the README Tools table (management: drop_database, drop_collection, rename_collection, current_ops, create_index, drop_index; write: insert_documents, update_documents, delete_documents, find_and_modify).
- Trusted stdio bypasses the role check (`assertAuthorized`, line 33) but not the capability flags, so the stdio snippet works; HTTP/SSE callers also need the Entra role (added to the body).
- Driver fallback is correct for Azure DocumentDB: `createIndexes` with `key: {field: "cosmosSearch"}` and `cosmosSearchOptions` (kind `vector-hnsw`, `m`, `efConstruction`, `similarity`, `dimensions`) is the documented data-plane path (https://learn.microsoft.com/en-us/azure/documentdb/vector-search). The builder belief that a portal/management-plane path is required is false.
- Hit counts verified by grepping `runs/*/*/events.jsonl`: 36 sample folders contain a "tools are disabled by default. Set ENABLE_" error, 32 the management message, 13 the write message.
- Correction applied: the draft said assertions exist in both `test/tools/dbGuard.test.ts` and `test/security/authorization.test.ts`; only `dbGuard.test.ts` line 51 asserts the message text.

### 3. Maintainer skeptic: confirmed
Names exact files and lines (README.md 122/240, authorization.ts 47/50, the four tool files, dbGuard.test.ts), proposes concrete small text changes with a DocumentDB-specific fallback (cosmosSearch createIndexes), keeps the behavior change (filtering `tools/list`) as an open question rather than forcing it. Edits applied: acknowledge the existing README mentions so the new section consolidates rather than duplicates them, list the exact tools per file, note the Entra role requirement on HTTP/SSE, fix the test reference. The agent-kit mirror is a one-line follow-up in a separate repo (Azure/documentdb-agent-kit `skills/mcp-setup/SKILL.md`) and should be filed there separately.

## Finding ids
- F0516
- F0815
- F2002
- F2034
- F2306
- F2415
- F2898
- F2998
