---
title: "Readiness stage reports the installed Agent Kit (and an installed MCP) as missed accelerators: detect accelerators in the inventory, split present/missed, filter in the extractor"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 24
findings: 25
bucket: kit-accelerator-missed
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Readiness stage reports the installed Agent Kit (and an installed MCP) as missed accelerators

## What happens today

`prompts/known_accelerators.md` lists the DocumentDB Agent Kit by its installer, `npx skills add Azure/documentdb-agent-kit`. The machine inventory (`collect_inventory()` in `factory/agents/readiness.py`, using probes from `factory/tools/environment.py`) reports 17 `installed_skills` named `documentdb-*` but never says which known accelerator they belong to. The readiness checker (`prompts/readiness_checker.md`, "Check the known accelerators: anything that exists ... but is not installed goes in `accelerators_missed`") then does not connect the two and writes things like:

- "DocumentDB Agent Kit (npx skills add Azure/documentdb-agent-kit) — installed skills cover many areas but the named agent kit accelerator from the known list is not present" (`runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`)
- "DocumentDB Agent Kit (single npx package) — not present as a named accelerator; the installed granular skills appear to cover most kit functionality" (`runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json`)

In the same runs `events.jsonl` shows the kit's skills being loaded (4 to 13 distinct `documentdb-*` skills per run; e.g. 9 in the atm-monitor run).

A second false positive of the same class: `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` has `"Azure DocumentDB MCP Toolkit (documentdb MCP) is installed, so no action required."` inside `accelerators_missed`, and `loop/findings.py` turned it into finding F2031 with the fixed detail "Exists and would have sped this build up, but was not installed."

## Why it matters

- Counted over the 120 phase runs: 60 list the kit as missed. 10 of those are the `no-skills` control arm (correct). The other 50 had all 17 skills installed, so 50/110 = 45% of kit-arm runs carry a false accelerator miss. This theme covers 24 samples / 25 findings; the rest of the 50 are the near-duplicate rows in `findings/TRIAGE.md` lines 141-144.
- All 24 runs in this theme ended with verdict `ready_with_gaps`. The readiness prompt says missing accelerators are one reason for that verdict, so the verdict split between `ready` and `ready_with_gaps` is not trustworthy for the kit arm.
- `factory/agents/auditor.py` passes `accelerators_missed` to the auditor as a readiness finding, so the audit was told the kit was absent in runs where it was used.
- `factory/aggregate.py` ("Accelerators not installed") and the `agent-kit` findings bucket are dominated by this noise; the extractor assigns target `agent-kit` and priority `low` to every accelerator entry, so a harness artefact shows up as 25+ Agent Kit findings for the kit maintainers.
- Not affected: `factory/scoring.py` never reads `accelerators_missed`, so the numeric readiness score is unchanged. This PR fixes verdicts, audits and reports, not the score.

## Proposed change

**1. `factory/tools/environment.py` + `factory/agents/readiness.py` (`collect_inventory`) — detect accelerators by code, not by the model.**
Add `probe_accelerators(skills: list[SkillInfo], skill_paths, mcp_statuses) -> list[AcceleratorStatus]` with fields `name, installed, evidence`. The inventory dict itself is assembled in `collect_inventory()` in `factory/agents/readiness.py`, so add `"accelerators": environment.as_dicts(environment.probe_accelerators(ctx.skills, ctx.settings.skill_paths, ctx.mcp_statuses))` there, next to `installed_skills` and `mcp_servers`. Rules:
- `DocumentDB Agent Kit`: installed if `skills-lock.json` (already read by `skill_public_urls`) has any entry with `source == "Azure/documentdb-agent-kit"`, or at least one installed skill name starts with `documentdb-`. Evidence: "17 skills from Azure/documentdb-agent-kit at <path>".
- `Azure DocumentDB MCP Toolkit`, `Azure MCP Server`, `Microsoft Learn MCP Server`: installed if the `documentdb` / `azure` / `learn` entry in `mcp_statuses` is `available`.
- `Azure CLI`: `az` CLI probe available. `Local DocumentDB container`: leave `installed: false` with evidence "not probed" unless a Docker probe is added later.

**2. `prompts/known_accelerators.md` — say what the kit is.**
Add a column "How the inventory detects it" and rewrite the kit row: "The kit is the set of `documentdb-*` skills (17 folders with SKILL.md). It is installed when the inventory's `installed_skills` lists them; `npx skills add` installs nothing else." Same for the MCP rows ("installed when `mcp_servers[].available` is true").

**3. `factory/models.py` + `prompts/readiness_checker.md` — separate present from missed.**
Add `accelerators_present: list[str] = Field(default_factory=list, description="Known accelerators the inventory reports as installed.")` to `ReadinessReport` and fill it in `_older_files` for old run folders. In the prompt replace the "Check the known accelerators" sentence with: "The inventory's `accelerators` section says which known accelerators are installed; copy the installed ones to `accelerators_present`. Only an accelerator the inventory marks `installed: false` may go in `accelerators_missed`. Never put an item in `accelerators_missed` to say it is installed."

**4. `factory/agents/readiness.py` — enforce it in code.**
Add `reconcile_accelerators(inventory, report)` and call it from `check_readiness` before `enforce_gates`:
```python
INSTALLED_PHRASES = ("is installed", "already installed", "no action required", "is present")

def reconcile_accelerators(inventory: dict, report: ReadinessReport) -> ReadinessReport:
    installed = {a["name"].lower() for a in inventory.get("accelerators", []) if a.get("installed")}
    missed, present = [], list(report.accelerators_present)
    for entry in report.accelerators_missed:
        low = entry.lower()
        names_installed = any(n in low for n in installed) or (
            ("agent kit" in low or "agent-kit" in low) and "documentdb agent kit" in installed
        )
        says_installed = any(p in low for p in INSTALLED_PHRASES) and "not installed" not in low
        (present if names_installed or says_installed else missed).append(entry)
    return report.model_copy(update={"accelerators_missed": missed, "accelerators_present": list(dict.fromkeys(present))})
```
Docstring it under the same banner as `enforce_gates`: rules the model does not get to overrule.

**5. `loop/findings.py` — stop manufacturing agent-kit findings from this field.**
In the `accelerators_missed` loop: skip entries that match `INSTALLED_PHRASES` without "not installed", skip entries naming an accelerator that `02-inventory.json` marks installed (read the inventory file next to the readiness file), set `target="pipeline"` (the proposed fix "make the pipeline install it" is a harness action in every case), and use the entry text itself as `detail` instead of the fixed "was not installed" string.

**6. `tests/test_units.py` — regression check.**
Two cases: (a) inventory with `accelerators=[{"name":"DocumentDB Agent Kit","installed":true,...}]` and a report whose `accelerators_missed` contains "DocumentDB Agent Kit (npx skills add Azure/documentdb-agent-kit) — not installed" → after `reconcile_accelerators` `accelerators_missed == []` and the kit is in `accelerators_present`; (b) `"Azure DocumentDB MCP Toolkit is installed, so no action required."` is moved to present. Also extend `tests/test_pipeline_offline.py` (which already seeds `accelerators_missed=["DocumentDB Agent Kit"]`) so the offline run uses a no-skills inventory, otherwise the seeded entry is now filtered and the assertion flips.

Optional, not in this PR: run the kit's documented installer (`npx skills add Azure/documentdb-agent-kit`) in the build image so `skills-lock.json` is always the marker; the repo already has it, so detection (step 1) is the cheaper fix.

## Evidence

- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json` (accelerators_missed[0]; `02-inventory.json` lists 17 skills; `events.jsonl` loads 9 kit skills)
- `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` (kit missed + "MCP Toolkit ... is installed, so no action required" in accelerators_missed; F2031)
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json` ("installed granular skills appear to cover most kit functionality")
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/02-readiness.json`
- `runs/13-product-q-a-chatbot-rag/20261125-055422/02-readiness.json`
- Counts: 60/120 phase runs list the kit as missed; 10 are the `loop/arms/no-skills` control arm, 50 had the skills installed.

## Verification

### 1. Already covered? confirmed (not there)
- `factory/agents/readiness.py` `collect_inventory()` returns `command_line_tools`, `azure_sign_in`, `skill_folders_searched`, `installed_skills`, `mcp_servers`, `run_policy`; there is no `accelerators` section and nothing maps installed skills to a known accelerator.
- `prompts/known_accelerators.md` kit row: How to add it = "`npx skills add Azure/documentdb-agent-kit`"; no detection column.
- `prompts/readiness_checker.md` line 22: "anything that exists and would speed this build up but is not installed goes in `accelerators_missed`"; no `accelerators_present`.
- `factory/models.py` line 155 has only `accelerators_missed`; `enforce_gates` (readiness.py line 124) handles MCP-required and prompt-insufficient gates only.
- `loop/findings.py` lines 109-115 copy every entry with target `agent-kit`, priority `low`, fixed detail "Exists and would have sped this build up, but was not installed."

### 2. Premise true? confirmed
- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`: verdict `ready_with_gaps`, accelerators_missed[0] is the quoted kit entry; `events.jsonl` references 9+ kit skills (connection, data-modeling, driver, indexing, monitoring, query-optimizer, security, vector-search, local-deployment).
- `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json`: accelerators_missed contains "Azure DocumentDB MCP Toolkit (documentdb MCP) is installed, so no action required." (F2031).
- Recount over `runs/*/*/02-readiness.json`: 120 runs, 60 list the kit as missed, 50 of them had `documentdb-*` skills in `02-inventory.json` installed_skills, 10 did not (control arm). Matches the draft.
- `skills-lock.json` entries carry `source: "Azure/documentdb-agent-kit"`, so the proposed lock-file detection works.
- `factory/scoring.py` contains no reference to accelerators; `factory/auditor.py` line 139 and `factory/aggregate.py` lines 37/64/144 do read `accelerators_missed`. Claims about score/audit/aggregate impact hold.
- Correction applied: the draft placed the inventory dict in `factory/tools/environment.py`; it is built in `collect_inventory()` in `factory/agents/readiness.py`. Also parenthesised the `names_installed` expression for clarity (same semantics). No Azure DocumentDB service facts are asserted.

### 3. Maintainer skeptic: confirmed
Concrete files, functions, schema field, code-enforced rule and regression tests in the harness repo; fixes a measured false positive affecting 45% of kit-arm runs and the triage buckets. Right repo (pipeline), not the Agent Kit.

## Finding ids

- F1768
- F1806
- F1842
- F1872
- F1997
- F2030
- F2064
- F2098
- F2132
- F2203
- F2227
- F2302
- F2497
- F2662
- F2696
- F2790
- F2821
- F2990
- F3052
- F3084
- F3273
- F3374
- F3441
- F3510
- F2031
