---
title: "Build stage can return \"partial\" with zero files written; pipeline still audits the empty tree and counts the result"
repo: abinav2307/azure-documentdb-agent-readiness
type: issue
status: ready_with_edits
priority: P2
sample_count: 5
findings: 38
bucket: mcp-server
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Build stage can return "partial" with zero files written; the audit then runs on an empty tree and its results are counted

## What happens today

In 5 of the 100 sample runs from 2026-11-24 the builder agent (gpt-5-mini) never called `write_file` or `run_command`. Its build-stage trace in `events.jsonl` contains only `log_decision` (each run also logs `_FunctionArgumentValidationError` lines) and `load_skill`, and the BuildReport says things like "I cannot run workspace actions right now" with `status: "partial"` and `files_created: []`. The `app/` folder of each of these runs holds zero files.

The gate in `factory/pipeline.py` (around line 223) only stops on `build.status == "failed"`:

```python
if build.status == "failed" and not force:
    say("      The build failed, so there is nothing to audit.")
    return finish(EXIT_BUILD_FAILED, verdicts)
```

So the audit stage ran against an empty `app/` folder and marked every requirement with cause `tool_unavailable` (09-inventory-reorder: 17 not_met, 1 partly_met, 1 not_checkable; 19-cross-sell: 20 of 20 not_met). The run exited with code 4 (`EXIT_AUDIT_FAILED`), which `finished()` in `loop/run_loop.py` treats as a completed run (`exit_code in (0, AUDIT_FAIL_EXIT)`), and `loop/findings.py` (around line 169) harvests `not_met`/`partly_met` results with cause `tool_unavailable` as findings and routes them to target `documentdb-mcp`. The result: 38 "mcp-server" findings (F1465-F1482, F3202-F3221) that describe a missing README, requirements.txt, seed script, index script, tests and IaC, none of which say anything about the kit, the MCP server or the docs.

This is not an outage. The empty builds are interleaved with successful ones in the same batch (by run-folder timestamp: 08-personalized-email-campaign-builder at 18:37 and 10-multi-tenant-storefront-saas at 18:41 both wrote files; 09-inventory-reorder at 18:40 wrote nothing), and the builder registers the same tool list (`workspace.tools()` on a `Workspace(..., writable=True)`, `run_command_tool`, MCP tools) in every run (`factory/agents/builder.py`). The 2026-11-25 re-run of 09-inventory-reorder wrote 10 files with 10 `write_file` and 6 `run_command` calls. The model simply did not use the tools in those turns, and the harness did not notice.

Affected runs (empty `app/`, `files_created: []`, audit `fail`):
- `runs/07-customer-review-sentiment-pipeline/20261124-183656` (re-run `20261125-054042` succeeded)
- `runs/07-multi-currency-ledger/20261124-190814` (no later run)
- `runs/09-inventory-reorder-multi-agent-system/20261124-184020` (re-run `20261125-054042` succeeded)
- `runs/13-product-q-a-chatbot-rag/20261124-184527` (re-run `20261125-055422` wrote 11 files, build `partial`, audit `pass_with_findings`)
- `runs/19-cross-sell-recommendation-beanie/20261124-185532` (re-run `20261125-055705` succeeded)

Note that `files_created` alone is not a reliable signal: `runs/14-loan-origination-workflow-orchestration/20261124-191837` also reports `files_created: []` but has 10 files on disk and a `pass_with_findings` audit. The check must look at the workspace, not the self-report.

## Why it matters

- 5 of 100 samples (5 percent) produced a spurious "fail" verdict and roughly 20 spurious requirement findings each, which inflate the not_met count attributed to the MCP server (and potentially the kit).
- The audit stage spent its whole budget (practice discovery, Learn searches, requirement checks) on a tree it could have refused with one directory listing.
- The builder's self-reported `status` is the only signal the gate uses, and the model reports "partial" for "I wrote nothing".

## Proposed change

1. `factory/pipeline.py`, after `build = await build_app(ctx, review, readiness)`: add a workspace check that does not trust the self-report. Gate on files actually on disk, not on `files_created` (see the 14-loan-origination case above).

```python
written = [p for p in ctx.app_dir.rglob("*") if p.is_file()]
if not written:
    ctx.log.add("build", "The builder wrote no files to the workspace",
                f"status={build.status}, files_created={len(build.files_created)}, on_disk=0",
                "tool_unavailable",
                ["Retry the build", "Mark the run infrastructure-failed"], build.summary)
    build = await build_app(ctx, review, readiness)   # one retry
    written = [p for p in ctx.app_dir.rglob("*") if p.is_file()]
    if not written:
        build.status = "failed"
```

   The existing `build.status == "failed"` gate then returns `EXIT_BUILD_FAILED`. (Equivalent: have `factory/agents/builder.py` coerce `status` to `"failed"` when `ctx.app_dir` holds no files after the agent returns.) Also log the build-stage tool-call counts so an empty tree with zero `write_file` calls is visible in `events.jsonl`.

2. `loop/run_loop.py`: exit 6 (`EXIT_BUILD_FAILED`) is already outside `finished()`; make sure the sample is re-queued on the next loop pass (or retried like `MODEL_FAILURE_EXIT` under `--auto-resume`) and recorded as `infrastructure_failed` rather than silently skipped.

3. `loop/findings.py`: skip `requirement_results` from any run whose `app/` folder holds no files, so an empty tree can never produce kit, MCP or Learn findings. Do not key this on `files_created == []`, which would also drop the valid 14-loan-origination run.

4. Data clean-up for this experiment: drop F1465-F1482 and F3202-F3221 from the readiness roll-up, exclude the five empty runs above from the scores, and re-run 07-multi-currency-ledger, the only affected sample with no later run.

No change is needed in Azure/documentdb-agent-kit, microsoft/documentdb-mcp or the Learn pages for this theme.

## Evidence

- `runs/09-inventory-reorder-multi-agent-system/20261124-184020/03-build.json` (status partial, files_created [], "cannot run workspace actions right now")
- `runs/09-inventory-reorder-multi-agent-system/20261124-184020/05-audit.json` (17 not_met, 1 partly_met, 1 not_checkable, all cause tool_unavailable)
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/events.jsonl` (build stage: 6 log_decision calls, no write_file)
- `runs/19-cross-sell-recommendation-beanie/20261124-185532/05-audit.json` (20 of 20 not_met, cause tool_unavailable)
- `runs/09-inventory-reorder-multi-agent-system/20261125-054042/03-build.json` and `events.jsonl` (same sample, same tool list, 10 write_file calls, 10 files on disk)
- `runs/14-loan-origination-workflow-orchestration/20261124-191837/03-build.json` (files_created [] but 10 files in app/; why the gate must check the disk)

## Verification

### 1. Already covered? confirmed (not there)
The target is the experiment harness. `factory/pipeline.py` gates the audit only on `build.status == "failed"` (line ~223) and has no check of the workspace contents; `factory/agents/auditor.py` passes `build.files_created` into the prompt but does not refuse an empty tree; `loop/findings.py` (line ~169) harvests every `not_met`/`partly_met` result with cause `tool_unavailable` without looking at the build; `loop/run_loop.py` `finished()` returns true for exit codes 0 and 4. Nothing in the harness detects an empty build.

### 2. Is the premise true? confirmed, with corrections applied
Checked against the run folders and the harness source.
- Confirmed: exactly five runs on 2026-11-24 reached the build stage and left `app/` empty (07-customer-review, 07-multi-currency-ledger, 09-inventory-reorder, 13-product-q-a, 19-cross-sell); each has `status: partial`, `files_created: []`, only `log_decision`/`load_skill` in the build stage, and FunctionArgumentValidationError lines in `events.jsonl`. (01-product-catalog `20261124-174657` also has no app/ but stopped before the build with exit 0, so it is not affected.)
- Confirmed: audit counts (18 + 20 = 38 tool_unavailable findings), the pipeline gate code, exit codes 4 and 6, `finished()`, and the findings.py harvest rule (which routes tool_unavailable to `documentdb-mcp`, explaining the bucket).
- Corrected: the draft gated on `files_created == []`; 14-loan-origination `20261124-191837` has `files_created: []` but 10 files on disk and a passing audit, so the check now uses the files on disk.
- Corrected: the draft said 07-customer-review and 13-product-q-a have no later successful run; both were re-run on 2026-11-25 with files and `pass_with_findings` audits (as was 19-cross-sell). Only 07-multi-currency-ledger needs a re-run.
- Corrected: the interleaving times quoted (05:32/05:36/05:40 UTC) did not match the runs; replaced with the run-folder timestamps (18:37, 18:40, 18:41).
- Corrected: the 09 re-run made 6 `run_command` calls, not 5.
- Corrected: exit 6 is already outside `finished()`; the ask is to re-queue or retry it, not to remove it.
No Azure DocumentDB facts are asserted in the draft.

### 3. Maintainer skeptic: confirmed
As maintainer of the harness I would accept this: it names the files (`factory/pipeline.py`, `factory/agents/builder.py`, `loop/run_loop.py`, `loop/findings.py`), gives a concrete gate and filter, and shows the defect contaminates the DocumentDB readiness score with 38 false MCP findings. It belongs in this repository, not in the kit, MCP server or Learn docs.

## Finding ids
F1465, F1466, F1467, F1468, F1469, F1470, F1471, F1472, F1473, F1474, F1475, F1476, F1477, F1478, F1479, F1480, F1481, F1482, F3202, F3203, F3204, F3205, F3206, F3207, F3208, F3209, F3210, F3211, F3212, F3213, F3214, F3215, F3216, F3217, F3218, F3219, F3220, F3221
