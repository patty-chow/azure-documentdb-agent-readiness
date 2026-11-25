---
id: M01
title: "Gated write/management tools: say so in tool descriptions and make the refusal actionable (opt-in location and driver fallback)"
repo: microsoft/documentdb-mcp
type: pr
status: ready
priority: P0
sample_count: 36
member_drafts:
  - 108-documentdb-mcp-create-index-refused-with-management-tools-ar.md
  - 084-documentdb-mcp-server-document-that-management-and-write-too.md
  - 112-documentdb-create-index-and-other-management-write-tools-are.md
open_questions: 3
---

# Gated write/management tools: say so in tool descriptions and make the refusal actionable (opt-in location and driver fallback)

This is a usability change, not a bug report. The secure default (write and management tools off) stays as it is. The PR makes the gate visible to an agent before it calls a tool, and makes the refusal tell the agent what it can do next.

## What happens today

- `ENABLE_WRITE_TOOLS` and `ENABLE_MANAGEMENT_TOOLS` default to false (`src/config.ts:212-213`).
- `registerToolDefinitions` (`src/tools/registry.ts`) registers every tool unconditionally and forwards only `title`, `description` and `inputSchema`, so `requiredRole` never reaches the client. `create_index` is described only as `'Create an index on a collection'` (`src/tools/index-tools.ts:19`).
- The gate fires only at call time, in `withDbGuard` (`src/tools/utils/dbGuard.ts:96`) -> `assertCapabilityEnabled` (`src/security/authorization.ts:42-52`):
  `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.` (and the equivalent `Write tools ...` text).
- The message does not say the flag is server configuration (the `env` block of the MCP client config, plus a restart), not a tool argument. It names no tool, gives no reason, and names no fallback: the same operation through a MongoDB driver (`createIndexes`, `insertMany`) is not covered by the gate, and read tools (`list_indexes`, `get_statistics`, `explain`) still work for verification.
- `README.md:122` says "By default only read tools are exposed". In fact the gated tools are listed and then refused. The flags are mentioned in several places (lines 122, 147-149, 167, 301, 324; `tool_list.md:8-9`), but the Tools table (lines 240-263) has a `Role` column that is never mapped to a flag. The one-click VS Code and Cursor install badges (`README.md:1-2`) leave both flags off, and so do the Agent Kit's shipped `mcp.json:12-13` and `gemini-extension.json:15-16`, so a default install cannot create an index through MCP.

## Why it matters

These counts come from a single experiment run: an agent (gpt-5-mini, with the Azure DocumentDB Agent Kit skills) built 100 Azure DocumentDB sample apps, using this server with its default configuration over stdio.

- **36 of the 100 samples** were refused at least once. In 32 samples the management gate refused `create_index` (surfaced to the client as `documentdb_create_index`) every time it was called (58 calls). In 13 samples the write gate refused `insert_documents` or a similar tool. (32 + 13 overlap in 9 samples, giving 36 distinct.)
- The agent read the refusal as an input error. In 17 of the 58 calls it immediately re-issued the same call with `keys`/`options` re-serialized as JSON strings; other samples retried two to four times with different `cosmosSearchOptions` spellings (`kind` vs `type`).
- In 17 of the 32 samples no driver-side index was added afterwards. At least 3 samples shipped with `explain` showing `COLLSCAN` on the query the index was designed for. One RAG sample shipped with no vector index at all (`list_indexes` showed only `_id`), and another fell back to ranking in the client.
- Even trivial steps are blocked: a plain unique index on `chunk_id` is management-tier.
- One agent wrongly concluded that cosmosSearch indexes cannot be created through the standard driver `createIndexes`. In the traced case where an agent fell back to the driver (run 08), the index was created on the first try.

The experiment harness did not set the flags (that is being fixed separately), so part of the hit rate is the harness's choice. The README quickstarts produce the same configuration, so any agent following them hits the same dead end. These counts come from one run and will be re-baselined after the harness fix; see Open question 3.

## Proposed change

### 1. `src/security/authorization.ts`: actionable refusals

The existing prefixes are kept, so `test/tools/dbGuard.test.ts:51`, `test/security/authorization.test.ts:81-82` and the prefix matches in `docs/permission-model.md:114` and `docs/e2e-testing-guide.md:130,237` still pass. Update the quoted deny text in `docs/permission-model.md:114` to the new message.

```ts
const OPT_IN_WHERE =
    'This flag is server configuration set by whoever launched the server (the "env" block of the MCP client ' +
    'configuration, for example ~/.claude.json, .vscode/mcp.json or ~/.cursor/mcp.json, then a server restart). ' +
    'It is not a tool argument or connection-profile field, so retrying with different arguments will not help.';

export function assertCapabilityEnabled(requiredRole: ToolRole, toolName?: string): void {
    const tool = toolName ? `'${toolName}' ` : 'This tool ';
    if (requiredRole === 'read' && !config.capabilities.readTools) {
        throw new Error('Read tools are disabled by server configuration (ENABLE_READ_TOOLS=false).');
    }
    if (requiredRole === 'write' && !config.capabilities.writeTools) {
        throw new Error(
            'Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in. ' +
            `${tool}is a 'write' tool (off by default because it can mutate data). Opting in exposes ` +
            'insert_documents, update_documents, delete_documents and find_and_modify. ' + OPT_IN_WHERE +
            ' Alternatively, perform the write from application code with a MongoDB driver connected with your own ' +
            'credentials (e.g. collection.insertMany / updateOne); that path is not subject to this gate.',
        );
    }
    if (requiredRole === 'management' && !config.capabilities.managementTools) {
        throw new Error(
            'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in. ' +
            `${tool}is a 'management' tool (off by default because this tier can create, rename or drop ` +
            'indexes, collections and databases). Opting in exposes create_index, drop_index, drop_collection, ' +
            'rename_collection, drop_database and current_ops. ' + OPT_IN_WHERE +
            ' Alternatively, run the equivalent command from application code with a MongoDB driver connected with ' +
            'your own credentials ' +
            '(for indexes: createIndexes, including cosmosSearchOptions for vector indexes, then wait for the build; ' +
            'a new vector index can return empty results for 2 to 3 minutes while it builds). ' +
            'Read tools such as list_indexes, get_statistics and explain remain available to verify the result.',
        );
    }
}
```

In `src/tools/utils/dbGuard.ts:96`, pass `policy.toolName` to `assertCapabilityEnabled` (`registerToolDefinitions` already puts `toolName` in the policy). Add assertions for the management message and the new fallback text next to the existing one.

### 2. `src/tools/registry.ts`: put the tier in the description

```ts
// change the existing import to: import { config, type ToolRole } from '../config';
const TIER_NOTE: Record<ToolRole, string> = {
    read: '',
    write: ' Tier: write (off by default; requires ENABLE_WRITE_TOOLS=true on the server).',
    management: ' Tier: management (off by default; requires ENABLE_MANAGEMENT_TOOLS=true on the server).',
};

function tierEnabled(role: ToolRole): boolean {
    if (role === 'write') return config.capabilities.writeTools;
    if (role === 'management') return config.capabilities.managementTools;
    return config.capabilities.readTools;
}

function describeWithTier(def: ToolDefinition): string {
    let text = def.description + TIER_NOTE[def.requiredRole];
    if (def.requiredRole !== 'read' && !tierEnabled(def.requiredRole)) {
        text += ' CURRENTLY DISABLED on this server: calls will be refused. Ask the operator to opt in, ' +
            'or run the equivalent command through a MongoDB driver (for indexes: createIndexes).';
    }
    return text;
}
// in registerToolDefinitions: description: describeWithTier(def),
```

This approach keeps every tool discoverable and tells the agent about the gate before it makes a call. It needs no edits to the individual tool files.

### 3. `README.md`

- Replace line 122's "By default only read tools are exposed." with: "By default only read tools succeed. Write and management tools are listed but refused until enabled (see *Write and management tools are opt-in*)." Link the same section from the one-click install badge lines.
- Above the Tools table, add: "Role `write` requires `ENABLE_WRITE_TOOLS=true`; role `management` requires `ENABLE_MANAGEMENT_TOOLS=true`."
- Add a section *Write and management tools are opt-in* after the install snippets that covers:
  - A table of each tier with its flag and tools. `write`: `insert_documents`, `update_documents`, `delete_documents`, `find_and_modify`. `management`: `create_index`, `drop_index`, `drop_collection`, `rename_collection`, `drop_database`, `current_ops`.
  - Why the tiers are off by default (a client, or a prompt-injected agent, could otherwise change or drop data). A note that the audit log (`src/security/audit.ts`) records allowed and denied calls. A recommendation to enable the tiers only for a dev/test profile and turn them off afterwards.
  - A note that on HTTP/SSE the caller also needs the matching Entra role, and that `TRUST_LOCAL_STDIO=true` skips the role check but not these flags.
  - The exact refusal text an agent will see, so it can be matched when searching the docs.
  - An `env` fragment for a trusted local/dev run, `"ENABLE_WRITE_TOOLS": "true", "ENABLE_MANAGEMENT_TOOLS": "true"`, with a note that the server must be restarted and that the flags stay off for shared or HTTP deployments.
  - The driver fallback, noting that it uses the caller's own database credentials and is the normal data-plane path (no MCP server or Azure control plane needed), for example (an HNSW spec with only `similarity` and `dimensions` is valid; the build parameters fall back to the documented defaults `m` 16, `efConstruction` 64, `efSearch` 40, and 1,536 dimensions is within the 2,000 limit for an uncompressed index, 4,000 with `compression: "half"`):
    ```js
    await db.collection("docs").createIndexes([{
      name: "vec_idx",
      key: { embedding: "cosmosSearch" },
      cosmosSearchOptions: { kind: "vector-hnsw", similarity: "COS", dimensions: 1536 }
    }]);
    await db.collection("docs").insertMany(seedDocs);
    ```
    and in pymongo: `db.command({"createIndexes": "docs", "indexes": [ ...same spec... ]})`.

The default stays off, consistent with `docs/design-doc.md` and `docs/permission-model.md`.

### 4. Follow-ups in Azure/documentdb-agent-kit (separate PR, not part of this one)

- `skills/mcp-setup/SKILL.md`: the opt-in note is one line (154-155). Add a Troubleshooting bullet (section at line 191) keyed on the exact refusal text: add the flag to the server `env` and restart, or do the operation in app code with the driver (`createIndexes` with `cosmosSearchOptions` works there).
- The `indexing` and `vector-search` skills: when the MCP tool is unavailable, fall back to driver `createIndexes` and wait for the build (a new vector index can return empty results for 2 to 3 minutes), then verify with `list_indexes`/`explain`. Quote the documented HNSW parameters (`m` 2 to 100, default 16; `efConstruction` 4 to 1000 and at least 2m, default 64; `efSearch` default 40) and the dimension limits (2,000 uncompressed; 4,000 with `compression: "half"` on HNSW and IVF; 16,000 with product quantization on DiskANN).
- The shipped `mcp.json` and `gemini-extension.json`: add a `_comment` explaining why `ENABLE_MANAGEMENT_TOOLS` is `"false"` and how to turn it on for a build session.

## Evidence

Paths are run folders from the experiment.

- `runs/12-cross-border-payment-audit-trail/20261124-201744/events.jsonl`, lines 33 and 35: an ESR compound index refused twice. Line 43: `explain` shows `COLLSCAN`, and the sample shipped that way.
- `runs/13-product-q-a-chatbot-rag/20261125-055422/events.jsonl`, line 71: `list_indexes` shows only `_id`; line 72: a `vector-hnsw` index (1536 dimensions) refused. No vector index was ever created.
- `runs/13-chronic-disease-risk-predictor/20261124-194916/events.jsonl`, lines 108, 139 and 142: three retries with different `cosmosSearchOptions` spellings, all refused.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl`, lines 66-67: a pymongo `createIndexes` fallback succeeded on the first try (exit code 0, index then visible via `list_indexes`).
- `runs/04-earnings-call-rag-assistant/20261124-190247/events.jsonl`, lines 48-49: a plain unique index on `chunk_id` refused by the management gate.
- `runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json`: the vector-index requirement is `not_met` (`tool_unavailable`), and the sample fell back to client-side ranking.
- `runs/14-hyper-personalized-content-engine/20261124-205043/doc-gaps.md`: after the refusal, the agent wrongly concluded that the driver cannot carry `cosmosSearchOptions`.

## Resolved

- Vector-index facts: settled 2026-11-25 from the Learn vector-search, half-precision, product-quantization and limitations pages and engine issue documentdb/documentdb#109, see findings/phase4/DECISIONS.md.
  - The README driver-fallback example (`vector-hnsw` with only `similarity` and `dimensions`) is valid as written: `m`, `efConstruction` and `efSearch` are optional and default to 16, 64 and 40 (vector-search page, HNSW tab).
  - HNSW parameter limits: `m` 2 to 100, `efConstruction` 4 to 1000 and at least 2m (vector-search page, HNSW tab).
  - 1,536 dimensions is within the 2,000 limit for an uncompressed index; 4,000 with `compression: "half"` on HNSW or IVF; 16,000 with product quantization on DiskANN (vector-search "Features and limitations", half-precision, product-quantization and limitations pages).
  - "Wait for the build" in the fallback text: a new vector index can return empty results for 2 to 3 minutes while it builds (quickstart-nodejs-select-algorithm, Troubleshooting).

## Open questions

1. Maintainer decision: should `registerToolDefinitions` stop registering tools whose tier is off (with a startup log line listing the skipped tools), so that `tools/list` matches what will succeed? This PR adds a description note instead, because skipping registration hides the capability and would require clients to reconnect once a flag is enabled.
2. Maintainer decision: would you move `create_index` to the `write` tier? It is the most common step when building a sample and is not destructive, yet it currently sits in the same tier as `drop_database`. Moving it would let a `["read","write"]` profile build a vector index while `drop_index`, `drop_*`, `rename_collection` and `current_ops` stay in `management`.
3. Before filing: the sample counts (36, 32, 58, 13, 17) come from one run in which the harness left the flags off. The reviewer asks for a re-run after the harness fix before quoting counts externally; refresh or soften the numbers in *Why it matters* at that point.

## Source drafts

- 108-documentdb-mcp-create-index-refused-with-management-tools-ar.md
- 084-documentdb-mcp-server-document-that-management-and-write-too.md
- 112-documentdb-create-index-and-other-management-write-tools-are.md
