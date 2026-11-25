---
title: "Readiness inventory: mark mongosh optional (DocumentDB MCP is the substitute) so 100+ runs stop recommending it"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 84
findings: 89
bucket: other-inventory
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Readiness inventory: treat `mongosh` as optional with the DocumentDB MCP server as the sanctioned substitute

## What happens today

`factory/tools/environment.py` probes `mongosh` as one of eleven CLIs (`CLI_PROBES`, purpose "Check connectivity and indexes by hand"). The runner image does not have it, so every `02-inventory.json` reports `mongosh: not found on PATH`. `prompts/readiness_checker.md` (the "Inventory recommendations" paragraph) then tells the readiness agent to write an `inventory_recommendations` entry for *every* unavailable item, and gpt-5-mini almost always decides it is `worth_adding: true`.

Result across the 120 readiness reports in `runs/`:

- 117 reports carry a mongosh `inventory_recommendations` entry; 114 of them (98 distinct samples) set `worth_adding: true`. This theme alone collected 89 findings over 84 distinct samples.
- 100 reports also list mongosh as an unavailable `tools` entry, so every report reads as if a tool is missing.
- 0 reports ever saw mongosh available, and no build ever ran it. `mongosh` is mentioned in 72 of 120 `events.jsonl` files, but none of those mentions is a `mongosh` command: most are Learn search queries in the readiness/discovery/audit stages, and the build-stage `run_command` hits are only the allowed-command list echoed in refusal messages (`mongosh` is in `DEFAULT_ALLOWED_COMMANDS` in `factory/config.py`). In the build stage it appears 3 times in `log_decision` only as an unchosen alternative, and 6 generated READMEs mention it as an optional way to inspect or clean up data. The builder did its connectivity, index, explain and aggregation checks through the DocumentDB MCP tools (`documentdb_find_documents`, `documentdb_list_indexes`, `documentdb_explain_operation`, `documentdb_aggregate`, `documentdb_sample_documents`) or short pymongo/Node scripts, which is exactly what we want it to do.

Because the prompt asks for "the simplest way to make it available", the model fills the gap with install text that is wrong or out of context:

- `npm install -g @mongosh/mongosh` (runs/03-next-best-action-multi-agent/20261124-203319) and `npm i -g @mongosh/cli` (runs/11-market-news-sentiment-orchestration/20261124-191425): neither is the published package; the npm package is `mongosh`.
- `--tlsAllowInvalidCertificates` appears in 48 of 120 readiness reports (for example runs/04-earnings-call-rag-assistant/20261124-190247 and runs/14-telehealth-session-summarizer/20261124-195137). For the local DocumentDB gateway this is the Agent Kit's documented local-only setting (the gateway ships a self-signed certificate; see `skills/local-deployment/local-connection-config.md`), so it is not wrong in itself, but it has no place in an install recommendation for a cloud M30 run and must never carry over to a managed Azure DocumentDB cluster.

The generated apps' READMEs (outside `node_modules`) contain neither the invented package names nor the TLS flag, so the damage is confined to the readiness reports and the findings they feed. It still costs reviewer time (89 near-identical findings in one bucket) and makes `ready_with_gaps` less meaningful.

## Why it matters

The readiness stage is supposed to surface gaps in the docs, the Agent Kit and the MCP server. A tool the harness itself chose not to install, for which the harness already provides a sanctioned substitute, is not such a gap. Fixing it in the harness removes about 100 noise rows per full run and stops the model from writing install instructions. Nothing here needs a change in Learn docs, Azure/documentdb-agent-kit or microsoft/documentdb-mcp.

## Proposed change (one PR)

1. **`factory/tools/environment.py`**: add `optional: bool = False` and `substitute: str = ""` to the `CliStatus` dataclass. Keep `CLI_PROBES` as `dict[str, tuple[list[str], str]]` (so the `for name, (args, purpose) in CLI_PROBES.items()` loop in `probe_clis()` does not change shape) and add a separate table:
   ```python
   OPTIONAL_CLIS: dict[str, str] = {
       "mongosh": "DocumentDB MCP server tools: documentdb_find_documents, documentdb_list_indexes, "
                  "documentdb_explain_operation, documentdb_aggregate, documentdb_sample_documents",
   }
   ```
   `probe_clis()` sets `optional=name in OPTIONAL_CLIS` and `substitute=OPTIONAL_CLIS.get(name, "")` on each `CliStatus`; `as_dicts()` already serialises dataclass fields, so `02-inventory.json` carries `optional` and `substitute`.

2. **`prompts/readiness_checker.md`**, "Inventory recommendations" paragraph, add one sentence:
   > If the inventory marks an unavailable item `optional` and names a `substitute` that is available, set `worth_adding` to false, name the substitute as the way to do that work, and do not write installation commands for it.

3. **`factory/reports.py`**, machine-inventory table (the `for c in inventory.get("command_line_tools", [])` loop and the `recommendation()` helper): when `c.get("optional")` and not available, print `optional` instead of `**no**` and `Use <substitute>` in the recommendation column, so the Markdown report does not read as a missing tool.

4. **`loop/README.md`**, "One-time setup": add an optional step after step 4, `npm install -g mongosh`, for anyone who wants the shell on the runner, with a note that the pipeline does not require it. (Alternatively, preinstall it in the runner image; either closes the theme, but marking it optional is the smaller change and keeps the substitute explicit.)

5. **`tests/test_pipeline_offline.py`**: the fixture already has `InventoryRecommendation(name="mongosh", worth_adding=False, ...)`; add an inventory fixture row `{"name": "mongosh", "available": False, "optional": True, ...}` and assert that the rendered inventory row contains `optional` and that the verdict logic ignores it.

## Evidence (run folders)

- runs/01-anti-money-laundering-pattern-detector/20261124-200112/02-inventory.json and 02-readiness.json: typical case, `mongosh` not on PATH, `worth_adding: true`, MCP named as workaround.
- runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json: invented package `@mongosh/mongosh`.
- runs/11-market-news-sentiment-orchestration/20261124-191425/02-readiness.json: invented package `@mongosh/cli`; its events.jsonl lists "mongosh scripts" only as a rejected alternative in `log_decision`.
- runs/04-earnings-call-rag-assistant/20261124-190247/02-readiness.json and runs/14-telehealth-session-summarizer/20261124-195137/02-readiness.json: `--tlsAllowInvalidCertificates` offered in a mongosh install recommendation (local-gateway-only setting, out of context here).

## Verification

### 1. Already covered? confirmed (not covered)

The target is the pipeline repo itself. `factory/tools/environment.py` line 27 probes `"mongosh": (["--version"], "Check connectivity and indexes by hand")` with no optional flag; `CliStatus` has only `name, purpose, available, detail`; grep for `optional` in that file finds nothing. `prompts/readiness_checker.md` line 45 requires "For every command-line tool or MCP server the inventory reports as unavailable, add one `inventory_recommendations` entry" with no carve-out for optional tools. `factory/reports.py` line 151 renders any unavailable CLI as `**no**`. `loop/README.md` "One-time setup" has no mongosh step. Nothing in Learn docs, Azure/documentdb-agent-kit or microsoft/documentdb-mcp is expected to address a harness runner-image property (the kit mentions mongosh in `skills/local-deployment/*` and `skills/query-optimizer/SKILL.md` only as a client to use, which is consistent with this draft).

### 2. Premise true? confirmed (secondary claims corrected)

Core premise verified from the run files: 117 of 120 `02-readiness.json` have a mongosh inventory recommendation, 114 with `worth_adding: true` across 98 samples; 100 list it as an unavailable tool. `@mongosh/mongosh` (1 report) and `@mongosh/cli` (2 mentions, 1 report) occur as stated; the published npm package is `mongosh` (MongoDB Shell install docs, `npm install -g mongosh`).
Corrections applied to the body:
- The draft said `mongosh` "appears in 1 of 120 events.jsonl". It appears in 72; none is an executed `mongosh` command. Build-stage hits are the allowed-command list echoed in `run_command` refusals, 3 `log_decision` alternatives and 6 README `write_file`s. The conclusion (the builder never needed or ran it) stands.
- The draft called `--tlsAllowInvalidCertificates` against the local gateway "an unsafe flag presented as routine setup" and cited 2 runs. It appears in 48 reports, and for the local DocumentDB gateway it is the Agent Kit's documented local-only setting (`skills/local-deployment/local-connection-config.md`: "`--tlsAllowInvalidCertificates` (for the self-signed local cert only)"; `local-env-driven-config.md` warns against it as a default for managed clusters). Reworded as out-of-context padding rather than an invented unsafe flag.
- The draft's code sketch turned the `CLI_PROBES` value into a 3-tuple with a dict, which breaks the declared type and the `for name, (args, purpose) in CLI_PROBES.items()` unpacking in `probe_clis()`. Replaced with a separate `OPTIONAL_CLIS` table.
No claim contradicts the Azure DocumentDB facts (mongosh is a supported client for Azure DocumentDB; the MCP tools named exist in the DocumentDB MCP server used by the runs).

### 3. Maintainer skeptic: confirmed

As maintainer of the harness I would accept this: it names exact files (`factory/tools/environment.py`, `prompts/readiness_checker.md`, `factory/reports.py`, `loop/README.md`, `tests/test_pipeline_offline.py`), a concrete small change, and a test. It has a DocumentDB angle (the DocumentDB MCP server is declared the substitute for an interactive shell) and removes ~100 noise rows per run. It belongs in this repo, not in the Agent Kit or MCP server.

## Finding ids

- F0017
- F0056
- F0091
- F0128
- F0161
- F0193
- F0230
- F0270
- F0295
- F0332
- F0364
- F0401
- F0437
- F0472
- F0511
- F0540
- F0571
- F0613
- F0645
- F0675
- F0711
- F0740
- F0777
- F0809
- F0834
- F0864
- F0900
- F0929
- F0956
- F0985
- F1020
- F1054
- F1117
- F1144
- F1179
- F1211
- F1239
- F1280
- F1311
- F1386
- F1416
- F1448
- F1502
- F1538
- F1572
- F1639
- F1668
- F1738
- F1769
- F1808
- F1843
- F1873
- F1906
- F1933
- F1965
- F1999
- F2032
- F2070
- F2099
- F2133
- F2204
- F2228
- F2261
- F2303
- F2341
- F2371
- F2407
- F2472
- F2500
- F2530
- F2604
- F2631
- F2728
- F2791
- F2825
- F2890
- F2959
- F3027
- F3053
- F3158
- F3191
- F3240
- F3275
- F3308
- F3338
- F3376
- F3405
- F3444
- F3511
