---
title: "Gated write/management tools: say so in the tool description and make the refusal actionable (opt-in location, rationale, driver fallback)"
repo: microsoft/documentdb-mcp
type: pr
status: ready_with_edits
priority: P1
sample_count: 11
findings: 12
bucket: mcp-server
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Gated write/management tools: say so in the tool description and make the refusal actionable

## What happens today

Write and management tools are off by default (`ENABLE_WRITE_TOOLS` / `ENABLE_MANAGEMENT_TOOLS`, `src/config.ts:212-213`). That is a good default. The problem is that nothing the MCP client receives tells the model about it:

- Tool descriptions carry no tier information. `create_index` is registered as `'Create an index on a collection'` (`src/tools/index-tools.ts:19-21`); `registerToolDefinitions` forwards only `title`, `description`, `inputSchema` (`src/tools/registry.ts:75-88`). `requiredRole` never reaches the client.
- When the model calls the tool, `assertCapabilityEnabled` (`src/security/authorization.ts:44-51`) throws `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.` The message does not say *where* that is set (the operator's MCP-client `env` block, with a server restart, not a tool argument or connection-profile field), *why* the tier is off, *what* opting in exposes, or that the same operation can be run through a MongoDB driver (`db.command({createIndexes: ...})`), which the gate does not cover.
- README.md:122 and tool_list.md:8-9 do document the flag (as do the agent kit's README.md:168-169, GEMINI.md:35-36 and `skills/mcp-setup/SKILL.md:154-155`), but an agent never reads those at runtime. The README one-click VS Code install (line 1) and the agent kit's shipped `mcp.json` (lines 12-13) and `gemini-extension.json` (lines 15-16) all leave the flags off, so a default install cannot create an index through MCP.

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini, DocumentDB Agent Kit skills, this MCP server configured per its documented defaults):

- `create_index` (surfaced to the client as `documentdb_create_index`) was called in 32 of the 100 samples and was refused by the management-tier gate in every one of them. 13 samples hit the write-tier gate (`insert_documents` and friends); 36 distinct samples hit one gate or the other.
- The model typically retried the same call two to four times with different `cosmosSearchOptions` spellings (`kind` vs `type`, string vs object `keys`), reading the refusal as a syntax problem, because the message gives it nothing else to act on (e.g. `runs/13-chronic-disease-risk-predictor/20261124-194916/events.jsonl:108,139,142`).
- Only a minority worked out the driver fallback on their own. When one did (`runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl:66-67`, `pymongo db.command({'createIndexes': ...})` over the same connection string), it succeeded on the first try (exit code 0, index then visible via `list_indexes`), which shows the gate blocks only the MCP path, not the capability.
- Where the model gave up, the cosmosSearch vector index was never created and the sample silently degraded to client-side cosine ranking, turning a "DB-native vector search" demo into an in-process one (`runs/15-financial-advisor-chatbot-rag/20261124-192021/05-audit.json`: vector-index requirement `not_met`, cause `tool_unavailable`). Eleven samples in this theme alone were scored `partly_met`/`not_met` on their index requirements for this reason.
- Even trivial steps are blocked: a plain `{chunk_id: 1}` unique index is management-tier (`runs/04-earnings-call-rag-assistant/20261124-190247/events.jsonl:48-49`).

## Proposed change

### 1. Put the tier in the tool description (`src/tools/registry.ts`)

Append a note per `requiredRole` at registration time, and when the tier is off on *this* server, say so, so the model learns it at tool-discovery time instead of after a failed call:

```ts
import { config, type ToolRole } from '../config';

const TIER_NOTE: Record<ToolRole, string> = {
    read: '',
    write:
        ' Tier: write (off by default). Enabled only when the server is started with ENABLE_WRITE_TOOLS=true.',
    management:
        ' Tier: management (off by default). Enabled only when the server is started with ENABLE_MANAGEMENT_TOOLS=true.',
};

function tierEnabled(role: ToolRole): boolean {
    if (role === 'write') return config.capabilities.writeTools;
    if (role === 'management') return config.capabilities.managementTools;
    return config.capabilities.readTools;
}

function describeWithTier(def: ToolDefinition): string {
    let text = def.description + TIER_NOTE[def.requiredRole];
    if (def.requiredRole !== 'read' && !tierEnabled(def.requiredRole)) {
        text +=
            ' CURRENTLY DISABLED on this server: calls will be refused. Ask the operator to opt in,' +
            ' or run the equivalent command through a MongoDB driver (for indexes: createIndexes).';
    }
    return text;
}
// in registerToolDefinitions: description: describeWithTier(def),
```

Alternative if you prefer a smaller tool list: skip `server.registerTool` for tools whose tier is off. That stops the retries but also hides the capability; the description note keeps it discoverable, so it is the one proposed here.

### 2. Make the refusal self-sufficient (`src/security/authorization.ts`)

```ts
const OPT_IN_WHERE =
    'This gate is set by the server operator, not by the caller: add the flag to the server\'s "env" block ' +
    'in your MCP client configuration (for example ~/.claude.json, .vscode/mcp.json, ~/.cursor/mcp.json) and restart the server.';

export function assertCapabilityEnabled(requiredRole: ToolRole): void {
    if (requiredRole === 'read' && !config.capabilities.readTools) {
        throw new Error('Read tools are disabled by server configuration (ENABLE_READ_TOOLS=false).');
    }
    if (requiredRole === 'write' && !config.capabilities.writeTools) {
        throw new Error(
            'Write tools are disabled by default (ENABLE_WRITE_TOOLS=false) because they can mutate data. ' +
            'To opt in for a trusted run, set "ENABLE_WRITE_TOOLS": "true"; this exposes insert_documents, ' +
            'update_documents, delete_documents and find_and_modify. ' + OPT_IN_WHERE +
            ' Alternatively, perform the write through a MongoDB driver connected with your own credentials; ' +
            'that path is not subject to this gate.',
        );
    }
    if (requiredRole === 'management' && !config.capabilities.managementTools) {
        throw new Error(
            'Management tools are disabled by default (ENABLE_MANAGEMENT_TOOLS=false) because they can create, ' +
            'rename or drop indexes, collections and databases. To opt in for a trusted run, set ' +
            '"ENABLE_MANAGEMENT_TOOLS": "true"; this exposes create_index, drop_index, drop_collection, ' +
            'rename_collection, drop_database and current_ops. ' + OPT_IN_WHERE +
            ' Alternatively, run the equivalent command through a MongoDB driver, e.g. ' +
            'db.command({ createIndexes: "<collection>", indexes: [ ... ] }); that path is not subject to this gate.',
        );
    }
}
```

Update the matching expectation strings in `docs/permission-model.md:114` and `docs/e2e-testing-guide.md:130,237` (they match on the `Write tools are disabled` prefix, which is preserved).

### 3. README: "Tool tiers and opt-in" section

Add after the install snippets (around README.md:122) and link it from the one-click badge line:

- Table: tier, default, tools, flag (`read` on; `write` off: insert/update/delete/find_and_modify; `management` off: create_index/drop_index/drop_collection/rename_collection/drop_database/current_ops).
- The exact `env` block for a trusted local run, with the two flags set to `"true"`, and the note that a restart is required.
- Security rationale: tiers are off so a read-only agent cannot escalate; every allowed and denied call is written to the audit log (`src/security/audit.ts`), so enabling a tier for a build session leaves a trace; turn it back off afterwards.
- Fallback when you cannot change the server config: the driver path (`createIndexes` example with `cosmosSearchOptions`), noting that it uses the caller's own database credentials.

### 4. Question for maintainers: tier of `create_index`

`create_index` on an existing collection is the single most common step in sample building and is not destructive, yet it sits in the same tier as `drop_database`. Would you consider moving it to `write` (so a `["read","write"]` profile can build a vector index) and keeping `drop_index`/`drop_*`/`rename_collection`/`current_ops` in `management`? If not, the description note in (1) at least tells the model why it is refused.

### 5. Follow-up in Azure/documentdb-agent-kit (separate PR)

Mirror the same note in `skills/mcp-setup/SKILL.md` (currently one line at 154-155) with a "when the call is refused" paragraph that names the driver fallback, and add a `_comment` to the shipped `mcp.json` and `gemini-extension.json` explaining why `ENABLE_MANAGEMENT_TOOLS` is `"false"` and how to flip it for a build session.

## Evidence (run folders from the readiness experiment)

- `runs/13-chronic-disease-risk-predictor/20261124-194916/events.jsonl` lines 108, 139, 142: three `documentdb_create_index` attempts, varying `cosmosSearchOptions`, all refused with the same text; `doc-gaps.md` records the model searching the installed skills and Learn for how to enable management tools and finding nothing.
- `runs/15-financial-advisor-chatbot-rag/20261124-192021/events.jsonl` lines 68-69 and `05-audit.json`: index never created, requirement `not_met` (`tool_unavailable`), sample fell back to client-side ranking.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/events.jsonl` lines 26, 43, 66-67: two decisions to use the MCP tool, refusal, then a successful `pymongo` `createIndexes` fallback on the same connection.
- `runs/04-earnings-call-rag-assistant/20261124-190247/events.jsonl` lines 48-49: a plain unique index on `chunk_id` is gated too.
- `runs/02-clinical-trial-matching-orchestration/20261124-193208/05-audit.json`: three requirements `partly_met` with cause `tool_unavailable`.

## Verification

### 1. Already covered? partially_covered

The opt-in flags are documented, but only in places the agent does not read at runtime; neither the tool description nor the refusal carries the guidance the draft asks for.

- `src/security/authorization.ts:47-51` (clone of microsoft/documentdb-mcp): the refusals are only `Write tools are disabled by default. Set ENABLE_WRITE_TOOLS=true to opt in.` and `Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.` They give no location, rationale, list of exposed tools or driver fallback.
- `src/tools/index-tools.ts:17-20`: `create_index` has the description `'Create an index on a collection'` and `requiredRole: 'management'`. `src/tools/registry.ts:79-85` passes only `title`, `description` and `inputSchema` to `server.registerTool`, so the tier never reaches the client.
- README.md:122 says: "To enable write or management tools, also set `"ENABLE_WRITE_TOOLS": "true"` and/or `"ENABLE_MANAGEMENT_TOOLS": "true"` in the `env` block." README.md:147-149 and tool_list.md:8-9 list the defaults. There is no security rationale, no audit note and no driver fallback.
- Agent kit: `skills/mcp-setup/SKILL.md:154-155` has a one-line opt-in note. README.md:168-169 and GEMINI.md:35-36 show `export ENABLE_MANAGEMENT_TOOLS=true`. The shipped `mcp.json:12-13` and `gemini-extension.json:15-16` set both flags to `"false"`. None of these says what to do when a call is refused.

### 2. Premise true? confirmed (one count corrected)

- I checked every code reference against the clone. Defaults are at `src/config.ts:212-213` (`ENABLE_WRITE_TOOLS` and `ENABLE_MANAGEMENT_TOOLS` default false). The management tier holds create_index, drop_index, drop_collection, rename_collection, current_ops and drop_database (`requiredRole: 'management'` in index-tools.ts, collection-tools.ts and database-tools.ts). The write tier holds insert_documents, update_documents, delete_documents and find_and_modify (document-tools.ts). The audit log is `src/security/audit.ts` (`[MCP-AUDIT]` lines on stderr). `create_index` calls `collection.createIndex`, so the driver `createIndexes` command is the same operation. docs/permission-model.md:114 and docs/e2e-testing-guide.md:130,237 match on the `Write tools are disabled` prefix.
- I recounted from the runs' events.jsonl. 32 samples have a `documentdb_create_index` tool call, and 32 samples contain the management refusal. 13 samples contain the write refusal. 36 distinct samples hit either gate, not the 38 the draft stated; the body now says 36. The run 08 pymongo `createIndexes` fallback finished with exit code 0, and `list_indexes` ran after it.
- The fallback is consistent with the service facts: Azure DocumentDB creates cosmosSearch vector indexes (vector-ivf, vector-hnsw, vector-diskann) with the `createIndexes` command.
- Naming: the server registers the tool as `create_index`. `documentdb_create_index` is the client-side prefixed name. The body now says this.

### 3. Maintainer skeptic: confirmed

The draft names exact files and line ranges (authorization.ts, registry.ts, README.md, docs/*) and gives concrete code. It keeps the secure default and only makes the gate self-explaining, which is squarely in this repository's scope and specific to how DocumentDB samples are built (cosmosSearch vector indexes). Item 4, moving `create_index` to the write tier, is framed as a question, which is appropriate. Item 5 is correctly split out as a separate Azure/documentdb-agent-kit follow-up. The repo stays microsoft/documentdb-mcp.

### Edits applied

- Corrected "38 distinct samples" to 36, and clarified that the 32 create_index samples were all refused by the management gate.
- Noted the `create_index` / `documentdb_create_index` naming.
- Added the agent kit's existing opt-in mentions (README, GEMINI.md, SKILL.md) and `gemini-extension.json`, which also ships the flags off.
- Added the run 08 fallback evidence (exit code 0, then `list_indexes`).

## Finding ids

- F0168
- F0250
- F0439
- F0451
- F0513
- F0591
- F1363
- F2207
- F2408
- F2445
- F2569
- F2826
