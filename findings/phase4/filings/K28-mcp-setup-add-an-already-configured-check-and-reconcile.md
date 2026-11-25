---
id: K28
title: "mcp-setup: add an 'already configured?' check and reconcile the server-entry spelling"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P3
sample_count: 1
member_drafts:
  - 064-mcp-setup-skill-should-recognise-an-existing-documentdb-serv.md
open_questions: 1
---

# mcp-setup: add an "already configured?" check and reconcile the server-entry spelling

## What happens today

`skills/mcp-setup/SKILL.md` walks an agent through adding a DocumentDB MCP server entry to a client config. Step 4 says that if the config "already has other servers", the agent should add the `DocumentDB` entry inside the existing `mcpServers` object. Nothing tells the agent to check first whether a DocumentDB entry already exists, or what to do if one does.

The kit also describes the entry three ways (two keys, three launch targets):

| Where | Server key | Launch target |
|---|---|---|
| `mcp.json` (root), `gemini-extension.json` | `documentdb` | `npx -y documentdb-mcp-server` |
| `skills/mcp-setup/SKILL.md` Step 4 | `DocumentDB` | `npx -y github:microsoft/documentdb-mcp` |
| `install.sh` (`MCP_ENTRY="DocumentDB"`) | `DocumentDB` | `node <MCP_DIR>/dist/main.js` (local clone of microsoft/documentdb-mcp, built by the installer) |

All three start the same server. In microsoft/documentdb-mcp, `package.json` names the package `documentdb-mcp-server`, and its `bin` points to `dist/main.js`.

`install.sh` `merge_mcp_entry()` always assigns `node[p]["DocumentDB"] = {...}`, and the `jq` path always sets `.[top_key]["DocumentDB"]`. If the client already has the kit's `documentdb` entry, from the plugin manifest or from following the README, the installer adds a second entry beside it. Two server processes then run, each with its own `CONNECTION_PROFILES`, and the agent sees every DocumentDB tool twice. `remove_mcp_entry()` removes only the literal `DocumentDB` key.

## Why it matters

We ran gpt-5-mini on 100 sample apps, with this kit's skills and the DocumentDB, Azure and Learn MCP servers loaded. A readiness stage checked whether the kit's MCP entry was installed. All counts below come from that single run.

- In 1 of the 100 samples (the only direct finding), the `documentdb` server was present and working: 18 tools, and the build later called list_databases, create_index, list_indexes and find_documents. The readiness report still listed the kit's MCP entry as a missed accelerator and suggested installing the "GitHub repo variant" as well. Following that advice with the skill as written produces a duplicate entry.
- In two other samples, an existing entry was broken: one failed to start, and in the other `CONNECTION_PROFILES` was unresolved. Both times the agent sent the user to this skill, which covers only fresh installs, so the agent improvised its own repair steps.
- In another sample, the agent correctly answered "installed, no action required". When the agent thinks to check, the check is easy.

Only one sample triggered the duplicate-entry advice directly, so this is low priority. The fix is a few lines and removes a real trap for anyone who installed the plugin and then follows the skill or runs the installer.

## Proposed change

**File: `skills/mcp-setup/SKILL.md`**

1. Add this section before "Step 1: Confirm prerequisites":

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

2. In Step 4, either change the template to match the root `mcp.json` (key `"documentdb"`, args `["-y", "documentdb-mcp-server"]`), or keep the template and add this sentence under it:

   ```markdown
   The kit's `mcp.json` and Gemini extension register the same server as
   `documentdb` (`npx -y documentdb-mcp-server`). If that entry exists, do not add
   this one alongside it.
   ```

3. Add to Troubleshooting:

   ```markdown
   - **DocumentDB tools appear twice / two DocumentDB servers in the client**: the
     config has both a `documentdb` and a `DocumentDB` entry. Remove one (keep the
     one whose `CONNECTION_PROFILES` is filled in) and restart the client.
   ```

**File: `install.sh` (optional, same PR or a follow-up)**

- In `merge_mcp_entry()`, before assigning `node[p]["DocumentDB"]`, scan `node[p]` for an entry whose `args` reference `documentdb-mcp-server`, `github:microsoft/documentdb-mcp` or `documentdb-mcp/dist/main.js`. If one exists, update it in place and keep its key, instead of adding a sibling. Apply the same rule in the `jq` branch.
- Make `remove_mcp_entry()` delete entries by that same match, not only by the literal `DocumentDB` key.

## Evidence

Run folders from the experiment:

- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json`: `accelerators_missed[1]`. The server is present, but the kit entry is still reported missing.
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-inventory.json`: the `documentdb` server and all kit skills are installed.
- `runs/retail-semantic-search/20261115-153948/02-readiness.json`: the report says to repair the entry using this skill, but the skill has no repair path.
- `runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json`: an existing entry has unresolved `CONNECTION_PROFILES`, and the agent pointed the user to this skill.
- `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json`: the correct "already installed, no action" outcome.

Partly to blame: the experiment harness lists the toolkit as "Entry `documentdb` in `mcp.json`", so its readiness reports phrase the ask that way. The duplicate-entry risk itself comes from the kit's mismatched spellings.

## Open questions

1. Which key and launch target should be canonical: `documentdb` with the published npm package, or `DocumentDB` with the GitHub source or a local build? The answer decides between option A and option B in Step 4, and which key `install.sh` should write when no entry exists. This is a maintainer decision. No SME confirmation is needed.

A related consolidated PR (filing K25) adds kit-wide "am I installed?" self-identification, based on draft 057, and may also edit `skills/mcp-setup/SKILL.md`. Land the two PRs one after the other so they do not conflict in the same lines.

## Source drafts

- 064-mcp-setup-skill-should-recognise-an-existing-documentdb-serv.md
