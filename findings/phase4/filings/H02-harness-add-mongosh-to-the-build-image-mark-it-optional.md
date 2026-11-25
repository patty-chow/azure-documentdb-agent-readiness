---
id: H02
title: "Harness: add mongosh to the build image, mark it optional in the readiness inventory, and ask for a 'Verify by hand' README section"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 98
member_drafts:
  - 066-harness-build-image-lacks-mongosh-readiness-stage-flags-it-i.md
  - 062-mongosh-missing-from-the-pipeline-build-environment.md
  - 069-generated-sample-readmes-should-include-mongosh-install-conn.md
open_questions: 1
---

# Harness: add mongosh to the build image, mark it optional in the readiness inventory, and ask for a "Verify by hand" README section

> This repository belongs to a colleague (abinav2307); please coordinate with them before opening this PR.

## What happens today

The harness expects the MongoDB Shell but never provides it:

- `factory/tools/environment.py` probes `mongosh` ("Check connectivity and indexes by hand"), and `factory/config.py` / `.env.example` list it in the allowed commands. The setup steps in `loop/README.md` (az login, provision, `npx skills add`, `pip install`, `python main.py check`) never install it, and the repo has no Dockerfile, so the "build image" is the operator's runner host. `main.py check` prints `NO` for it with no install hint.
- So every `02-inventory.json` (120 of 120 runs) reports `mongosh: not found on PATH`.
- `prompts/readiness_checker.md` ("Inventory recommendations") asks for a recommendation for *every* unavailable tool, with no carve-out for tools that have a substitute. Result: 117 of 120 readiness reports carry a mongosh `inventory_recommendations` entry, 114 with `worth_adding: true`; 19 also list it under `accelerators_missed`. `factory/reports.py` renders it as `**no**`, so every report reads as if a tool is missing.
- Asked for "the simplest way to make it available", the model writes install text that is wrong or out of context: invented npm packages `@mongosh/mongosh` and `@mongosh/cli` (one report each; the published package is `mongosh`); the TLS setting `tlsAllowInvalidCertificates` inside the mongosh recommendation itself in 3 reports (it appears somewhere in 48 of 120 readiness reports, 7 of them as the `--tlsAllowInvalidCertificates` flag; it is a local-gateway-only setting: the Agent Kit's local-deployment skill and the Learn development-loop tutorial (`https://learn.microsoft.com/en-us/azure/documentdb/development-loop`) show it only in the `localhost:10260` connection string of the `documentdb-local` container, which serves a self-signed certificate; it is out of place for a cloud cluster run); and one invented Learn URL (`learn.microsoft.com/mongodb/mongodb-shell/install`, 404). The URL rule at `prompts/readiness_checker.md` line 39 sits after the per-confusion field list, so it reads as scoped to confusions, not to recommendation prose.
- The builder never ran `mongosh`. It did its connectivity, index and explain checks through DocumentDB MCP tools (`documentdb_find_documents`, `documentdb_list_indexes`, `documentdb_explain_operation`, `documentdb_aggregate`, `documentdb_sample_documents`) or short PyMongo/Node scripts. One build report (19-proactive-outreach-orchestration, `03-build.md` line 44) told users to install mongosh locally or use the DocumentDB MCP tools; that run's `app/README.md` does not mention mongosh.
- `prompts/builder.md` step 3 asks for a README with "what the sample shows, prerequisites, setup, how to run, and how to clean up". Nothing asks for a manual-verification path; only 11 of 112 generated `app/README.md` files mention mongosh, mostly as "see mongosh/portal" for clean-up. Twelve readiness reports asked for exactly that README step.

## Why it matters

- **98 distinct samples** (of the 100 in the sweep) produced a mongosh `worth_adding: true` recommendation; the 19 `accelerators_missed` samples are a subset. Counts are from one experiment run (2026-11-24/25) and were recounted from the run folders; the member drafts reported 84, 19 and 4 because each counted a different slice of findings (96 finding ids in all). Counts from this harness are unstable and partly harness artifacts; re-run after the harness fixes (118, 058, 106, 117) before quoting them outside the team.
- This is harness noise, not a gap in Learn, the Agent Kit or the DocumentDB MCP server: about 100 near-identical rows per full run, an inflated `accelerators_missed` metric, and a weaker `ready_with_gaps` verdict.
- Without the shell, the experiment can only test the MCP half of the Agent Kit's `query-optimizer` skill, which pairs every MCP tool with a mongosh command and has a "Local mongosh Commands (No MCP Required)" section.
- Generated samples leave a developer with no quick "connect and look" step before debugging app code.

## Proposed change (one PR)

1. **`loop/README.md`**, "One-time setup", new step after the skills install (step 3), renumbering the later steps:
   > 4. Optional but recommended: install the MongoDB Shell so the builder and you can inspect collections and indexes by hand: `npm install -g mongosh` (or `brew install mongosh`). The pipeline does not require it; the DocumentDB MCP server covers the same checks.

   Amend the `python main.py check` line to: "should show `az login` ok, `mongosh` ok or optional, 17 skills, and all three MCP servers ok." If a container image is added later, the same `npm install -g mongosh` belongs there.

2. **`factory/tools/environment.py`**: add `optional: bool = False` and `substitute: str = ""` to `CliStatus`. Keep `CLI_PROBES` unchanged (so `for name, (args, purpose) in CLI_PROBES.items()` in `probe_clis()` keeps its shape) and add:
   ```python
   OPTIONAL_CLIS: dict[str, str] = {
       "mongosh": "DocumentDB MCP server tools: documentdb_find_documents, documentdb_list_indexes, "
                  "documentdb_explain_operation, documentdb_aggregate, documentdb_sample_documents",
   }
   ```
   `probe_clis()` sets `optional=name in OPTIONAL_CLIS` and `substitute=OPTIONAL_CLIS.get(name, "")`; `as_dicts()` already serialises dataclass fields, so `02-inventory.json` carries both.

3. **`main.py` `check`** (around line 120): when a CLI is unavailable and `c.optional`, print `optional (install with: npm install -g mongosh)` instead of `NO`.

4. **`factory/reports.py`**, machine-inventory table (`for c in inventory.get("command_line_tools", [])` and `recommendation()`): for an unavailable optional CLI print `optional` instead of `**no**` and `Use <substitute>` in the recommendation column.

5. **`prompts/readiness_checker.md`**:
   - Move "Never construct or recall a URL. If you do not have one from a tool result or skill text, leave it empty." from the end of the per-confusion field list to a top-level rule covering every output field, prose included.
   - In "Inventory recommendations" add:
     > If the inventory marks an unavailable item `optional` and names a `substitute` that is available, set `worth_adding` to false, name the substitute as the way to do that work, and do not write installation commands for it. Put any URL in the entry's `references`, copied from a tool result; do not write URLs in `recommendation` text.

6. **`prompts/builder.md`**, step 3, replace the README sentence with:
   > Include a README with what the sample shows, prerequisites, setup, how to run, a short **Verify by hand** section, and how to clean up. The Verify by hand section shows one `mongosh "$DOCUMENTDB_CONNECTION_STRING"` command (connection string read from an environment variable, never written out) followed by one or two one-line checks such as `db.runCommand({ ping: 1 })` and `db.<collection>.getIndexes()`. If the sample also runs against the local Docker DocumentDB gateway, say that `--tlsAllowInvalidCertificates` is for that local gateway only (its self-signed certificate; the Learn development-loop tutorial shows the local string as `localhost:10260` with `tls=true&tlsAllowInvalidCertificates=true`) and never for the Azure cluster. Link only to pages you obtained from a tool result, such as the Learn page "Connect using MongoDB Shell - Azure DocumentDB" (`https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell`) and the mongosh install page (`https://www.mongodb.com/docs/mongodb-shell/install/`). Do not invent a Learn path for mongosh installation.

7. **`tests/test_pipeline_offline.py`**: add an inventory fixture row `{"name": "mongosh", "available": False, "optional": True, ...}`; assert the rendered inventory row contains `optional` and that the verdict logic ignores it.

Optional follow-up (not in this PR): after each stage, HEAD-check every `http(s)://` string in the stage JSON and record a `dead_url` warning on 404.

## Evidence

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-inventory.json` and `02-readiness.json`: typical case, not on PATH, `worth_adding: true`, MCP named as workaround.
- `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json`: invented package `@mongosh/mongosh`.
- `runs/11-market-news-sentiment-orchestration/20261124-191425/02-readiness.json`: invented package `@mongosh/cli`.
- `runs/04-earnings-call-rag-assistant/20261124-190247/02-readiness.json`, `runs/14-telehealth-session-summarizer/20261124-195137/02-readiness.json` and `runs/16-loyalty-points-ledger/20261124-184937/02-readiness.json`: `tlsAllowInvalidCertificates` inside the mongosh recommendation (local-gateway-only setting, out of context here).
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/02-readiness.json`: mongosh under `accelerators_missed`; builder used MCP `list_indexes` / `find_documents` instead.
- `runs/19-proactive-outreach-orchestration/20261124-205844/03-build.md` (line 44): build report tells users to install mongosh locally.
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` and `app/README.md`: fabricated Learn URL; README with no manual-verification section.

## Open questions

1. Should mongosh be installed on the runner (so the experiment also exercises the kit's mongosh path) or only marked optional? This PR does both: the README step installs it and the optional flag stops noise when it is absent. The harness owner may prefer one. (Maintainer decision; no claim here needs SME confirmation. The Learn page and npm package named above were checked and resolve.)

## Source drafts

- 066-harness-build-image-lacks-mongosh-readiness-stage-flags-it-i.md (lead)
- 062-mongosh-missing-from-the-pipeline-build-environment.md
- 069-generated-sample-readmes-should-include-mongosh-install-conn.md

Not in this PR: 062 notes a companion Agent Kit gap (the kit never lists mongosh as a tool in a setup skill), tracked separately under the agent-kit mongosh theme.
