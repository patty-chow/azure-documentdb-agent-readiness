---
title: "Readiness inventory: compute accelerator status by code so the Agent Kit (already loaded) is not reported missing in ~45% of runs; record azd as out of scope"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 2
findings: 2
bucket: other-inventory
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Readiness inventory: compute known-accelerator status by code so the Agent Kit is not re-recommended when it is already loaded

## What happens today

`collect_inventory` (factory/agents/readiness.py) hands the readiness checker a machine inventory with `installed_skills` (17 `documentdb-*` skills under `.agents/skills`) and, separately, the `known_accelerators.md` table whose row reads "DocumentDB Agent Kit — `npx skills add Azure/documentdb-agent-kit`". Nothing joins the two: the inventory never says "the Agent Kit is installed", and the prompt only says "check the known accelerators: anything that exists ... but is not installed goes in `accelerators_missed`".

gpt-5-mini therefore treats the kit as a separate, uninstalled package. In the 2026-11-24/25 batch:

- 50 of the 110 kit-arm runs on disk (48 distinct samples, ~45%; 49 of 106 when the findings were extracted) list the DocumentDB Agent Kit in `accelerators_missed` while `02-inventory.json` in the same folder shows all 17 kit skills loaded. Run 06 also made it a `worth_adding: true` entry in `inventory_recommendations`.
- All 50 of those runs received verdict `ready_with_gaps`; the prompt's verdict rule includes "or accelerators are missing", so the false entry can be the reason the run did not get `ready`.
- The false entries propagate: `aggregate.py` counts `accelerators_missed` into "Accelerators not installed", `auditor.py` line 139 passes the list to the auditor, and `loop/findings.py` line 109 turns each entry into a finding (which is how F0901 got here).
- Runs in the no-skills arm (`loop/arms/no-skills`, empty `installed_skills`) also flag the kit, and there it is correct; the fix must keep that.

A second, smaller item: `azd` is probed (`factory/tools/environment.py` `CLI_PROBES`) but not installed. Of 117 `inventory_recommendations` entries naming azd, 116 correctly said it is not worth adding; run 07 said it is, because nothing in the inventory or prompt records that the harness builds against a pre-provisioned cluster and does not deploy.

## Why it matters

The readiness stage is meant to tell the PM where the product makes an agent's life hard. A recommendation slot spent on "install the Agent Kit" in a run where the kit is loaded is noise in every downstream report, lowers the readiness verdict for the wrong reason, and hides the real accelerator gaps (for example the local container not running).

## Proposed change

1. **`factory/agents/readiness.py`, `collect_inventory`** — add an `accelerators` section computed by code, one entry per row of `known_accelerators.md`:

```python
def accelerator_status(ctx, clis: list[CliStatus], sign_in: CliStatus) -> list[dict]:
    clis = {c.name: c for c in clis}  # probe_clis() returns list[CliStatus]
    kit_sources = {e.get("source") for e in _lock_entries(ctx.settings.skill_paths).values()}
    kit_installed = "Azure/documentdb-agent-kit" in kit_sources and bool(ctx.skills)
    mcp = {s.name: s for s in ctx.mcp_statuses}
    def srv(name):
        s = mcp.get(name); return bool(s and s.available), (s.detail if s else "no mcp.json entry")
    rows = [
        ("DocumentDB Agent Kit", kit_installed,
         f"{len(ctx.skills)} skills from Azure/documentdb-agent-kit in {ctx.skill_roots}" if kit_installed else "no skill from Azure/documentdb-agent-kit found"),
        ("Azure DocumentDB MCP Toolkit", *srv("documentdb")),
        ("Azure MCP Server", *srv("azure")),
        ("Microsoft Learn MCP Server", *srv("learn")),
        ("Azure CLI", clis["az"].available and sign_in.available, clis["az"].detail),
        ("Local DocumentDB container", clis["docker"].available, "docker present; container not started by the harness"),
    ]
    return [{"name": n, "installed": i, "detail": d} for n, i, d in rows]
```

   `_lock_entries` reads `skills-lock.json` (version 2: a `skills` map whose entries carry `source`, e.g. `"Azure/documentdb-agent-kit"`) the same way `environment.skill_public_urls` in `factory/tools/environment.py` already does; split that function so both share the parse. In `collect_inventory`, keep the `clis = environment.probe_clis()` list and the `probe_azure_login()` result in locals and add `"accelerators": accelerator_status(ctx, clis, sign_in)` to the returned dict. The MCP names `documentdb`, `azure` and `learn` match the keys in `mcp.json`.

2. **`prompts/readiness_checker.md`, "Tools" paragraph** — replace "Check the known accelerators: anything that exists and would speed this build up but is not installed goes in `accelerators_missed`" with:

   > Check `machine_inventory.accelerators`. Only an accelerator marked `installed: false` may go in `accelerators_missed`, with the install command from the known-accelerators table. The DocumentDB Agent Kit is the set of `documentdb-*` skills in `installed_skills`; when it is marked installed, never recommend `npx skills add Azure/documentdb-agent-kit` and do not list it under `inventory_recommendations`.

3. **Code gate** (next to `clean_links` in readiness.py) — `drop_installed_accelerators(inventory, report)`: remove any `accelerators_missed` string or `inventory_recommendations` entry whose text matches the name (or `agent[- ]kit`, `mcp.json` entry name) of an accelerator the inventory marks installed. The model-independent gate keeps `aggregate.py`, the auditor prompt and `loop/findings.py` clean even when the model ignores the prompt.

4. **`prompts/known_accelerators.md`** — add below the table:

   > `azd`, `bicep` and `terraform` are deliberately not installed: the harness builds against a pre-provisioned cluster and never deploys. Set `worth_adding` to true for them only when the sample itself asks for infrastructure-as-code or a deployment step.

5. **Test** — in `tests/test_units.py`, a case where `installed_skills` holds kit skills and the report lists the kit in `accelerators_missed`; after the gate the list is empty. A second case with the no-skills arm (`installed_skills == []`) keeps the entry.

## Evidence (run folders)

- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json` — `inventory_recommendations[4]` and `accelerators_missed[0]` recommend installing the Agent Kit; `02-inventory.json` in the same folder lists 17 installed `documentdb-*` skills.
- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json` — the `accelerators_missed` entry says "installed skills cover ..." in the same sentence that reports the kit as missing.
- `runs/01-product-catalog-with-vector-search/20261124-174657/02-readiness.json` — kit in `accelerators_missed` with 17 skills loaded.
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json` — also reports the `documentdb` mcp.json entry missing while `02-inventory.json` shows the documentdb MCP server answered with 18 tools (same root cause: accelerator status is not computed by code).
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/02-readiness.json` — `azd` `worth_adding: true`; the only such run in the batch.

Count: 50 of 110 kit-arm runs (48 distinct samples) flag the kit as missing; all 50 are `ready_with_gaps`. No-skills-arm runs flag it correctly and are unaffected by the gate.

## Verification

### 1. Already covered? confirmed (not there)

The target is the pipeline, so I checked the repo code instead of Learn, the kit or the MCP server. Nothing computes accelerator status today:
- `factory/agents/readiness.py` `collect_inventory` (lines 22-39) returns `command_line_tools`, `azure_sign_in`, `skill_folders_searched`, `installed_skills`, `mcp_servers` and `run_policy`. It has no `accelerators` key and does not link the skills to the Agent Kit row.
- `prompts/readiness_checker.md` line 22 says only: "Check the known accelerators: anything that exists and would speed this build up but is not installed goes in `accelerators_missed`".
- `prompts/known_accelerators.md` line 8 lists the kit with `npx skills add Azure/documentdb-agent-kit`. Nothing in that file says azd, bicep or terraform are deliberately left out.
- `readiness.py` has only `clean_links` (line 97) and `enforce_gates` (line 124). Neither one filters `accelerators_missed`.

### 2. Premise true? confirmed (with corrections applied)

- I recounted across all `runs/*/*/02-readiness.json` whose `02-inventory.json` has non-empty `installed_skills`. 50 of 110 runs (48 samples) mention the agent kit in `accelerators_missed`, and every one of them is `ready_with_gaps`. The draft said 49/106/47. Those were the numbers when the findings were extracted, and the body now gives the current counts.
- Downstream use is confirmed: `factory/aggregate.py:64`, `factory/reports.py:130` ("Accelerators not installed"), `factory/agents/auditor.py:139` and `loop/findings.py:109`.
- The verdict rule in `prompts/readiness_checker.md` line 54 includes "or accelerators are missing".
- `skills-lock.json` is version 2. Each entry has `"source": "Azure/documentdb-agent-kit"`, so the detection rule works.
- The `mcp.json` server names are `documentdb`, `azure` and `learn`, which matches the draft.
- azd: 117 `inventory_recommendations` entries name azd and only 1 has `worth_adding: true`. The draft said 115/116, and the body is corrected.
- Code correction: `environment.probe_clis()` (`factory/tools/environment.py`) returns `list[CliStatus]`, not a dict. The draft's snippet indexed `clis["az"]`, so the snippet now builds a name-to-status map first.
- No claim about Azure DocumentDB itself is made, so none conflicts with the service facts.

### 3. Maintainer skeptic: confirmed

I would accept this as a PR to the harness. It names the exact files and functions (`collect_inventory`, `clean_links`, `readiness_checker.md`, `known_accelerators.md`, `tests/test_units.py`). It adds a model-independent gate and a test that keeps the no-skills arm correct. It fixes a measurable bias: about 45% of kit-arm runs are pushed to `ready_with_gaps` for a false reason. That bias is specific to this DocumentDB readiness experiment, not generic engineering hygiene. The right repo is the pipeline repo, not the kit or the MCP server.

## Finding ids

- F1017
- F0901
