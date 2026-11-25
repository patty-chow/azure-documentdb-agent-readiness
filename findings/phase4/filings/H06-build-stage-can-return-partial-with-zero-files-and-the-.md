---
id: H06
title: "Build stage can return partial with zero files and the audit still grades the empty tree"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready
priority: P0
sample_count: 5
member_drafts:
  - 106-pipeline-audit-runs-the-practice-checklist-against-failed-or.md
  - 116-build-stage-wrote-no-files-to-the-workspace-so-the-audit-emi.md
open_questions: 3
---

# Build stage can return "partial" with zero files and the audit still grades the empty tree

> This repository belongs to a colleague; please coordinate this filing with them before opening it.

## What happens today

In a 100-sample run of the pipeline with gpt-5-mini as the builder (2026-11-24), five builds wrote nothing to `app/`, reported `status: "partial"` with `files_created: []`, and were then audited as if they were real apps.

**Likely trigger: `log_decision` rejections switch the builder's tools off.** `reason_source` on the `log_decision` tool is annotated with the closed `ReasonSource` `Literal` (`factory/models.py`, used in `factory/decision_log.py` `tool_for`). Agent Framework validates arguments against that type before the function body runs, so a value such as `documentdb-vector-search`, `skill_md` or `run_policy` fails with `_FunctionArgumentValidationError` (logged in `events.jsonl`). The model writes the source's name instead of the category and retries unchanged. With the framework's default `max_consecutive_errors_per_request` of 3, three rejections in a row end tool use for the request. In all five empty runs, the build-stage trace holds only `log_decision` / `load_skill` calls and these validation errors: no `write_file`, no `run_command`. The BuildReport says things like "I cannot run workspace actions right now". Across the whole run (120 run folders), 66 runs from 60 of the 100 samples had at least one rejected `log_decision` call. That is the wider effect; only five builds ended up empty.

**The gate trusts the builder's self-report.** `factory/pipeline.py` (around line 223) skips the audit only when `build.status == "failed"`. A "partial" build with an empty tree goes to the audit, which:
- marks practice checks `violated` with evidence "no code present" (29 checks across the five runs; 13-product-q-a alone has 14: singleton client, vector index, `number[]` embeddings, TLS, secrets, retries and more);
- marks requirements `not_met` with cause `tool_unavailable` (09-inventory-reorder: 17 not_met, 1 partly_met; 19-cross-sell: 20 of 20 not_met).

The run then exits 4 (`EXIT_AUDIT_FAILED`), which `finished()` in `loop/run_loop.py` counts as complete. `loop/findings.py` (around line 169) harvests `tool_unavailable` results as findings and routes them to `documentdb-mcp`. That produced 38 "MCP server" findings about a missing README, seed script, tests and IaC, none of which say anything about the MCP server.

**This is not an outage.** Empty builds are interleaved with successful ones, every run registers the same tools (`factory/agents/builder.py`), and re-runs of 09-inventory-reorder, 13-product-q-a and 19-cross-sell on 2026-11-25 wrote 8 to 11 files each (19-cross-sell 8, 09-inventory-reorder 10, 13-product-q-a 11). The 07-customer-review re-run wrote 14.

**`files_created` is not a reliable signal either.** 14-loan-origination reports `files_created: []` but has 10 files on disk and a valid `pass_with_findings` audit.

**Side effect in runs that did produce code:** rejected index-shape and provisioning decisions never reach `decisions.jsonl`, so the auditor then flags "audit trail: index decision" as violated (for example 04-customer-journey-mapper).

## Why it matters

5 of the 100 samples got a spurious `fail` verdict, and the two member drafts carry 67 findings (29 from the practice-violation bucket, 38 requirement findings) and an inflated not_met count attributed to the MCP server. A reader of `05-audit.md` for 13-product-q-a would conclude the agent does not know `cosmosSearch` indexes or `number[]` embeddings, when it never wrote any code. The 60-sample rejection rate also makes decision-log statistics (`model_default` share, audit-trail completeness) unreliable. These counts come from one experiment run.

## Proposed change

1. **`factory/pipeline.py`: gate on the disk, not the self-report.** After `build = await build_app(...)`:
   ```python
   written = [p for p in ctx.app_dir.rglob("*") if p.is_file()]
   if not written:
       ctx.log.add("build", "The builder wrote no files to the workspace",
                   f"status={build.status}, files_created={len(build.files_created)}, on_disk=0",
                   "tool_unavailable", ["Retry the build", "Mark the run infrastructure-failed"], build.summary)
       build = await build_app(ctx, review, readiness)   # one retry
       if not any(p.is_file() for p in ctx.app_dir.rglob("*")):
           build.status = "failed"
   ```
   The existing `failed` gate then returns `EXIT_BUILD_FAILED`; record the verdict as `build_incomplete`. (Equivalent: have `factory/agents/builder.py` coerce `status` to `"failed"` when `ctx.app_dir` holds no files after the agent returns.) Also log build-stage tool-call counts so an empty tree with zero `write_file` calls is visible in `events.jsonl`. Do not key on `files_created == []` (see 14-loan-origination). A stricter optional variant from draft 106 also treats a `partial` build whose source files never reference the database client (no `MongoClient` or `DOCUMENTDB_URI` in any `.py`/`.js`/`.ts`/`.java`/`.cs`/`.go` file) as `build_incomplete`; that heuristic needs a maintainer decision, since it could also drop legitimate partial builds.

2. **`factory/decision_log.py` / `factory/models.py`: stop hard-rejecting `reason_source`.** Annotate the tool parameter as `str`, normalize known variants (`skill_md`, `documentdb-*` to `skill`; `prompt_review`, `assumptions_from_prompt_review` to `readiness_report`; `run_policy`, `run_environment` to `operator`; `docs`, `learn` to `docs`), and for unmappable values return an explanatory string rather than raising, so a bad value never counts toward the error budget. Keep the original wording in a new `Decision.reason_source_raw: str = ""`, and keep `Decision.reason_source` typed as `ReasonSource` (the normalized value always fits it). Rewrite the Field description to say it is a category, not a document name, and define each value. Changing only the `ValueError` in `DecisionLog.add` is not enough: the framework rejects the call before the body runs.

3. **`factory/llm.py` `_make_client`: raise the error budget** to `"max_consecutive_errors_per_request": 10`. The experiment's fork already carries this; re-runs made with it produced code.

4. **`loop/run_loop.py`:** exit 6 is already outside `finished()`. Re-queue it (or retry it like `MODEL_FAILURE_EXIT` under `--auto-resume`) and record it as `infrastructure_failed` rather than skipping it silently.

5. **`loop/findings.py`:** skip `requirement_results` from any run whose `app/` holds no files on disk, so an empty tree can never produce kit, MCP or Learn findings. Do not key this on `files_created == []`.

6. **Optional auditor guard:** `prompts/auditor.md` already requires "cite the file and line" for `violated`; enforce it with a validator on `AuditCheck` that downgrades a `violated` check whose `evidence` holds no path-like token (for example `\w+\.(py|js|ts|json|md|yaml|txt)`) to `not_assessable`, with a note.

7. **Data clean-up for this experiment:** drop F1465-F1482 and F3202-F3221 (the 38 requirement findings) and the practice violations scored on the five empty runs from the roll-up, exclude those five runs from the scores, and re-run 07-multi-currency-ledger, the only affected sample with no later run.

8. **Follow-up, best filed as its own issue: post-build framework check** (from draft 106). Extract framework names from `prompt.md` (`langchain`, `langgraph`, `semantic kernel`, `autogen`, `beanie`, `motor`, `mongoose`, `spring data`, ...) and compare them with the manifest and the actual imports in `app/`. If a name is in the prompt but in no import, require a matching decision in `decisions.jsonl`; otherwise the pipeline appends an `audit trail` check itself (`availability: discovered_not_listed`) so the deviation is recorded. Evidence: 06-credit-risk-multi-agent-scorer pins `langchain` in `app/requirements.txt` but no `.py` file imports it and `decisions.jsonl` has no framework decision.

No change is needed in the kit, the MCP server or the Learn pages for this issue.

## Evidence

- `runs/13-product-q-a-chatbot-rag/20261124-184527/` (`events.jsonl` lines 19-21: three rejections with `reason_source=documentdb-vector-search`, then no further calls; `03-build.json` partial, no files; `05-audit.json` 14 violated). Re-run `runs/13-product-q-a-chatbot-rag/20261125-055422/`: 11 files, `pass_with_findings`.
- `runs/09-inventory-reorder-multi-agent-system/20261124-184020/` (`reason_source=run_policy` x3; "cannot run workspace actions right now"; 17 not_met, cause `tool_unavailable`).
- `runs/09-inventory-reorder-multi-agent-system/20261125-054042/` (same sample and tools: 10 `write_file` calls, 10 files).
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/` (no `write_file`; 20 of 20 not_met). Re-run `20261125-055705`: 8 files.
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/` and `runs/07-multi-currency-ledger/20261124-190814/` (the other two empty builds).
- `runs/14-loan-origination-workflow-orchestration/20261124-191837/` (`files_created: []` but 10 files on disk: why the gate must check the disk).
- `runs/04-customer-journey-mapper/20261124-203553/events.jsonl` lines 21-23 (decision rejected; code exists; audit-trail check still violated).
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/` (framework deviation, item 8).

## Open questions

1. Is the three-error tool cut-off the confirmed cause of every empty build? Draft 116 says the model "did not use the tools"; draft 106 links it to the consecutive-error limit. Both observations are in the traces. A maintainer check of the framework behavior would settle it.
2. Is the `max_consecutive_errors_per_request` change wanted upstream, or should it stay a fork-only setting?
3. Should `run_policy` become its own `ReasonSource` literal (10 rejections used exactly that word), or map to `operator`?

No Azure DocumentDB product claims in this issue need SME confirmation. The reviewer asks for a re-run after this fix before any sample count here is quoted externally.

## Source drafts

- 106-pipeline-audit-runs-the-practice-checklist-against-failed-or.md
- 116-build-stage-wrote-no-files-to-the-workspace-so-the-audit-emi.md
