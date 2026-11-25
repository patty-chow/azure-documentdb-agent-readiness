---
title: "mcp-setup: add an \"already configured?\" check and reconcile the documentdb / DocumentDB server-entry spellings"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P3
sample_count: 1
findings: 1
bucket: kit-accelerator-missed
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# mcp-setup: add an "already configured?" check and reconcile the `documentdb` / `DocumentDB` entry spellings

## What happens today

`skills/mcp-setup/SKILL.md` walks an agent through adding a DocumentDB MCP server entry to a client config. Step 4 says "If it already has other servers, add the `DocumentDB` entry inside the existing `mcpServers` object", but nothing tells the agent to check whether a DocumentDB server entry is already present, or what to do if it is.

The kit also describes the entry two different ways:

| Where | Server key | Launch target |
|---|---|---|
| `mcp.json` (root), `gemini-extension.json` | `documentdb` | `npx -y documentdb-mcp-server` |
| `skills/mcp-setup/SKILL.md` Step 4 | `DocumentDB` | `npx -y github:microsoft/documentdb-mcp` |
| `install.sh` (`MCP_ENTRY="DocumentDB"`) | `DocumentDB` | `node <MCP_DIR>/dist/main.js` (local clone of `microsoft/documentdb-mcp`, built by the installer) |

All three launch the same server: `microsoft/documentdb-mcp`'s `package.json` names the package `documentdb-mcp-server` with `bin` `dist/main.js`.

`install.sh` `merge_mcp_entry()` unconditionally assigns `node[p]["DocumentDB"] = {...}` (and the `jq` path sets `.[top_key]["DocumentDB"]`). A client that already has the kit's own `documentdb` entry (from the plugin manifest, or configured by hand following the README) therefore ends up with two server processes for the same package, each with its own `CONNECTION_PROFILES`, and the agent sees the DocumentDB tool set twice.

## Why it matters

In a 100-sample agent-readiness experiment (gpt-5-mini with the kit's skills and the DocumentDB, Azure and Learn MCP servers), the readiness stage is asked whether the kit's MCP entry is installed:

- In `runs/18-360-data-platform-cdp-orchestration/20261124-205822` the `documentdb` server was present and working (18 tools; the build later called `documentdb_list_databases`, `documentdb_create_index`, `documentdb_list_indexes`, `documentdb_find_documents`), yet `02-readiness.json` still listed "Azure DocumentDB MCP Toolkit entry in mcp.json" under `accelerators_missed`, reasoning that the kit's "accelerator variant (GitHub repo)" should be installed in addition. With the skill as written, following that advice adds a second entry.
- In `runs/retail-semantic-search/20261115-153948` the existing `documentdb` entry failed to start, and the readiness agent's remedy was "Repair the documentdb entry using documentdb-mcp-setup" with the `github:microsoft/documentdb-mcp` launch target and `TRUST_LOCAL_STDIO`. The skill has no repair/verify path for an existing entry, so the agent improvised one.
- In `runs/01-product-catalog-with-vector-search/20261124-174657` the entry existed but `CONNECTION_PROFILES` was unresolved; again the agent pointed at this skill, which only covers fresh installs.
- By contrast `runs/12-cross-border-payment-audit-trail/20261124-201744` correctly said "documentdb MCP is installed, so no action required", showing the check is cheap when the agent thinks of it.

Only one of the 100 samples produced the "add a duplicate" finding directly, so this is low priority, but the fix is a few lines and removes a real foot-gun for anyone who ran the plugin install and then follows the skill (or the installer) manually.

## Proposed change

**File:** `skills/mcp-setup/SKILL.md`

1. Add a new section before "Step 1: Confirm prerequisites":

   ```markdown
   ## Step 0: Is it already configured?

   Before adding anything, open the client's MCP config (table in Step 4) and look
   for an existing entry under `mcpServers` / `mcp.servers` whose `args` contain
   `documentdb-mcp-server`, `github:microsoft/documentdb-mcp`, or a path ending in
   `documentdb-mcp/dist/main.js` (the bundled installer's local build). The key may
   be `documentdb` (the kit's `mcp.json` / Gemini manifest) or `DocumentDB` (this
   skill and the bundled installer). All of these launch the same server; only one
   entry should exist.

   - **Entry present and the client lists DocumentDB tools** → nothing to add.
     Skip to Step 5 to verify (`list_databases` with the profile name defined in
     that entry's `CONNECTION_PROFILES`).
   - **Entry present but the server does not start or has no tools** → repair it
     in place rather than adding a second one. Check, in order: `TRANSPORT` is
     `stdio`; `AUTH_REQUIRED` is `"false"`; `TRUST_LOCAL_STDIO` is `"true"`
     (older builds: `ALLOW_UNAUTHENTICATED_STDIO`); `CONNECTION_PROFILES` is a
     JSON *string* and any `${VAR}` it references is set in the environment the
     client launches with. Then continue at Troubleshooting.
   - **No entry** → continue with Step 1.

   Never add a second DocumentDB entry: two entries start two server processes and
   the agent sees every tool twice.
   ```

2. In Step 4, either switch the template to the same key and launch target as the root `mcp.json` (`"documentdb"`, `["-y", "documentdb-mcp-server"]`), or keep the current template and add one sentence noting that `documentdb` / `documentdb-mcp-server` (used by `mcp.json` and the Gemini extension) is the same server and must not be added alongside.

3. Add to Troubleshooting:

   ```markdown
   - **DocumentDB tools appear twice / two DocumentDB servers in the client**: the
     config has both a `documentdb` and a `DocumentDB` entry. Remove one (keep the
     one whose `CONNECTION_PROFILES` is filled in) and restart the client.
   ```

**Optional, `install.sh`:** in `merge_mcp_entry()`, before assigning `node[p]["DocumentDB"]`, scan `node[p]` for any entry whose `args` reference `documentdb-mcp-server`, `github:microsoft/documentdb-mcp` or `documentdb-mcp/dist/main.js` and update that entry in place (keeping its key) instead of adding a sibling. `remove_mcp_entry()` should delete by the same match rather than only by the literal `DocumentDB` key.

## Evidence (run folders from the experiment)

- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json` — `accelerators_missed[1]`: server present, kit entry still reported missing
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-inventory.json` — inventory shows the `documentdb` server and all kit skills installed
- `runs/retail-semantic-search/20261115-153948/02-readiness.json` — "repair the documentdb entry using documentdb-mcp-setup" with no repair path in the skill
- `runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json` — existing entry with unresolved `CONNECTION_PROFILES`, agent pointed at this skill
- `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` — the correct "already installed, no action" outcome

Note for context: the experiment harness's own accelerator list describes the MCP toolkit as "Entry `documentdb` in `mcp.json`", which is why several readiness reports phrase the ask that way; the duplicate-entry risk itself comes from the kit's two spellings, not from the harness.

## Verification

### 1. Already covered? confirmed (not there)

Grepped `skills/`, `knowledge-base/`, `docs/` and `README.md` of Azure/documentdb-agent-kit for "already configured", "already installed", "existing ... entry", "duplicate" and `documentdb-mcp-server`. No hit relates to detecting an existing MCP server entry. The only nearby text is `skills/mcp-setup/SKILL.md` Step 4: "If it already has other servers, **add** the `DocumentDB` entry inside the existing `mcpServers` object", which covers other servers, not an existing DocumentDB one. Troubleshooting has no duplicate-entry bullet. `install.sh` `merge_mcp_entry()` writes `node[p]["DocumentDB"]` with no lookup for an existing entry, and `remove_mcp_entry()` pops only the literal `DocumentDB` key.

### 2. Premise true? confirmed (one detail corrected)

- `mcp.json` and `gemini-extension.json` (repo root) register `"documentdb"` with `"args": ["-y", "documentdb-mcp-server"]`: confirmed.
- `skills/mcp-setup/SKILL.md` Step 4 template registers `"DocumentDB"` with `"args": ["-y", "github:microsoft/documentdb-mcp"]`: confirmed.
- `install.sh` uses `MCP_ENTRY="DocumentDB"`: confirmed. **Corrected:** the draft said install.sh launches `github:microsoft/documentdb-mcp`. In fact `install_mcp_for_client()` sets `cmd="node"` and `args=["${MCP_DIR}/dist/main.js"]` after cloning and building the repo. The table, Step 0 match list and installer suggestion now include that launch form.
- `microsoft/documentdb-mcp/package.json`: `"name": "documentdb-mcp-server"`, `"bin": {"documentdb-mcp-server": "dist/main.js"}`. This confirms all three forms run the same server.
- `TRUST_LOCAL_STDIO` (formerly `ALLOW_UNAUTHENTICATED_STDIO`, microsoft/documentdb-mcp#83) and `AUTH_REQUIRED=false` for stdio match SKILL.md Step 3 and Troubleshooting.
- Evidence spot-checked: `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json` `accelerators_missed[1]` says "the documentdb MCP server is present, but if the agent kit accelerator variant (GitHub repo) were installed...". `runs/retail-semantic-search/20261115-153948/02-readiness.json` contains "Repair the documentdb entry using documentdb-mcp-setup". `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` says the MCP is installed, "so no action required".

### 3. Maintainer skeptic: confirmed

The draft names one file (`skills/mcp-setup/SKILL.md`) and gives concrete sections and text. It also includes an optional, specific change to `install.sh`. The ask is specific to the kit: the kit's own mismatch between `documentdb` and `DocumentDB` keys can register the same DocumentDB MCP server twice. It is small and in scope for Azure/documentdb-agent-kit. Only one sample showed it, so it is priority P3.

## Finding ids

- F2991
