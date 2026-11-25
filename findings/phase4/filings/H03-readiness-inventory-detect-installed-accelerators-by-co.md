---
id: H03
title: "Readiness inventory: detect installed accelerators by code so the Agent Kit, MCP server and local container are not reported as missed"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 59
member_drafts:
  - 058-readiness-stage-reports-installed-accelerators-the-agent-kit.md
  - 070-readiness-inventory-one-offs-azd-not-installed-agent-kit-rec.md
  - 063-documentdb-local-container-not-pre-pulled-or-running-in-the-.md
open_questions: 4
---

# Readiness inventory: detect installed accelerators by code so the Agent Kit, MCP server and local container are not reported as missed

> This repository belongs to a colleague (abinav2307); coordinate with them before opening this PR.

## What happens today

The readiness stage gives the model two things that nothing joins:

- The machine inventory from `collect_inventory()` (`factory/agents/readiness.py`) lists `installed_skills` (the 17 `documentdb-*` skills), `mcp_servers` and CLI probes, but has no `accelerators` section and never says which known accelerator those skills or servers are.
- `prompts/known_accelerators.md` lists the DocumentDB Agent Kit only by its installer (`npx skills add Azure/documentdb-agent-kit`), and lists "Local DocumentDB container" as a plain accelerator, while `loop/run-environment.md` tells every agent that no local gateway is running, on purpose, and to build against the live cluster.

`prompts/readiness_checker.md` then says "anything that exists and would speed this build up but is not installed goes in `accelerators_missed`". The model fills that field by guessing, with four kinds of wrong entry:

1. **Installed kit reported as missing.** For example: "installed skills cover many areas but the named agent kit accelerator from the known list is not present", while `events.jsonl` in the same run shows 9 kit skills being loaded.
2. **Installed MCP server reported as missing.** One run has "Azure DocumentDB MCP Toolkit (documentdb MCP) is installed, so no action required." inside `accelerators_missed`. Another lists the `documentdb` MCP entry as missing even though the inventory shows it answered with 18 tools.
3. **Local container that is deliberately absent.** It is listed as missed in some runs and not in others, even though every run that reported Docker (118 of 120) had the same environment: Docker present, no container running. A rerun of the same sample can flip the result.
4. **azd.** One run marked `azd` as `worth_adding: true`. Nothing records that the harness builds against a cluster that is already provisioned and never deploys.

## Why it matters

- **How many samples.** 59 of the 100 loop samples have at least one of these false entries. That is 47 for the kit (in the skills arm), 21 for the container, 2 for an MCP server that was available, and 1 for azd (samples overlap, so these add up to more than 59). The kit alone appears in 50 of 110 skills-arm runs (about 45%; 48 sample folders, one of them the pre-loop `retail-semantic-search` sample). In the 10 runs of the `no-skills` control arm, listing the kit as missing is correct, and the fix keeps that. These counts come from one experiment run (2026-11-24/25). The member drafts reported 24, 2 and 21, because they counted extracted findings rather than run folders. The numbers above were recounted from every `runs/*/*/02-readiness.json` and its `02-inventory.json`.
- **What the agent got wrong.** It recommended installing tools that were already loaded. The verdict rule ("`ready_with_gaps` ... or accelerators are missing") then downgraded those runs, so the split between `ready` and `ready_with_gaps` cannot be trusted for the skills arm.
- **Where the noise spreads.** `factory/agents/auditor.py` passes the list to the auditor. `factory/aggregate.py` and `factory/reports.py` count it under "Accelerators not installed". `loop/findings.py` turns every entry into an `agent-kit` finding with a fixed detail ("was not installed"). As a result, a harness artifact shows up as 25+ Agent Kit findings and hides real gaps.
- **Not affected.** `factory/scoring.py` never reads `accelerators_missed`, so the numeric score does not change.

## Proposed change

**1. `factory/tools/environment.py`**
- Split the `skills-lock.json` parsing out of `skill_public_urls` into `_lock_entries(skill_paths)`, so both functions share it. The lock file is version 2, and each entry carries `source`, e.g. `"Azure/documentdb-agent-kit"`.
- Add a probe next to `probe_azure_login()`:
```python
def probe_local_gateway() -> dict:
    """Whether a DocumentDB local gateway container publishes port 10260. Fact, not a model guess."""
    if not shutil.which("docker"):
        return {"state": "docker_absent", "containers": []}
    done = subprocess.run(["docker", "ps", "--filter", "publish=10260", "--format", "{{.Names}}"],
                          capture_output=True, text=True, timeout=15)
    names = [n for n in done.stdout.split() if n] if done.returncode == 0 else []
    return {"state": "running" if names else "not_running", "containers": names}

def probe_accelerators(skills, skill_paths, mcp_statuses, clis, sign_in, gateway) -> list[dict]:
    clis = {c.name: c for c in clis}            # probe_clis() returns list[CliStatus]
    mcp = {s.name: s for s in mcp_statuses}     # mcp.json keys: documentdb, azure, learn
    def srv(n):
        s = mcp.get(n); return bool(s and s.available), (s.detail if s else "no mcp.json entry")
    from_lock = any(e.get("source") == "Azure/documentdb-agent-kit" for e in _lock_entries(skill_paths).values())
    kit = sum(1 for s in skills if s.name.startswith("documentdb-"))
    kit_ok = bool(kit) and from_lock   # see open question 2
    rows = [
        ("DocumentDB Agent Kit", kit_ok, f"{kit} documentdb-* skills" + (" from Azure/documentdb-agent-kit" if from_lock else "")),
        ("Azure DocumentDB MCP Toolkit", *srv("documentdb")),
        ("Azure MCP Server", *srv("azure")),
        ("Microsoft Learn MCP Server", *srv("learn")),
        ("Azure CLI", clis["az"].available and sign_in.available, clis["az"].detail),
        ("Local DocumentDB container", gateway["state"] == "running", f"gateway {gateway['state']}"),
    ]
    return [{"name": n, "installed": i, "evidence": d} for n, i, d in rows]
```

**2. `factory/agents/readiness.py`**
- In `collect_inventory()`, keep the `probe_clis()` and `probe_azure_login()` results in local variables. Then add `"local_documentdb_gateway": gateway` and `"accelerators": environment.probe_accelerators(ctx.skills, ctx.settings.skill_paths, ctx.mcp_statuses, clis, sign_in, gateway)` next to `installed_skills` and `mcp_servers`.
- Add a gate and call it from `check_readiness` before `enforce_gates`. Put it under the same banner: these are rules the model does not get to overrule.
```python
INSTALLED_PHRASES = ("is installed", "already installed", "no action required", "is present")
ALIASES = {  # other names the model uses, including the mcp.json entry names
    "documentdb agent kit": ("agent kit", "agent-kit"),
    "azure documentdb mcp toolkit": ("documentdb mcp", "entry 'documentdb'", "entry `documentdb`"),
    "azure mcp server": ("entry 'azure'", "entry `azure`"),
    "microsoft learn mcp server": ("learn mcp", "entry 'learn'", "entry `learn`"),
}

def reconcile_accelerators(inventory: dict, report: ReadinessReport) -> ReadinessReport:
    installed = {a["name"].lower() for a in inventory.get("accelerators", []) if a.get("installed")}
    def is_installed(text: str) -> bool:
        low = text.lower()
        named = any(n in low for n in installed) or any(
            k in installed and any(a in low for a in al) for k, al in ALIASES.items())
        says = any(p in low for p in INSTALLED_PHRASES) and "not installed" not in low
        return named or says
    missed, present = [], list(report.accelerators_present)
    for entry in report.accelerators_missed:
        (present if is_installed(entry) else missed).append(entry)
    recs = [r for r in report.inventory_recommendations if not is_installed(r.model_dump_json())]  # InventoryRecommendation objects
    return report.model_copy(update={"accelerators_missed": missed,
                                     "accelerators_present": list(dict.fromkeys(present)),
                                     "inventory_recommendations": recs})
```

**3. `factory/models.py`.** Add the following to `ReadinessReport`, and default it in `_older_files` so older run folders still load:

`accelerators_present: list[str] = Field(default_factory=list, description="Known accelerators the inventory reports as installed.")`

**4. `prompts/known_accelerators.md`**
- Add a column "How the inventory detects it".
- Kit row: "The kit is the set of `documentdb-*` skills. It is installed when `machine_inventory.accelerators` marks it installed; `npx skills add` installs nothing else."
- MCP rows: "installed when `mcp_servers[].available` is true".
- Replace the container row with: `| Local DocumentDB container | Run the open-source engine locally for tests (image ghcr.io/documentdb/documentdb/documentdb-local, MongoDB wire protocol on 10260) | github.com/documentdb/documentdb | Docker. Loop runs intentionally do not start it: the environment note names a live cluster to build against. When that note is present, do not list this container in accelerators_missed. |`
- Add below the table: "`azd`, `bicep` and `terraform` are deliberately not installed: the harness builds against a pre-provisioned cluster and never deploys. Set `worth_adding` to true for them only when the sample itself asks for infrastructure-as-code or a deployment step."

**5. `prompts/readiness_checker.md`, Tools paragraph.** Replace "Check the known accelerators: anything that exists and would speed this build up but is not installed goes in `accelerators_missed`, with the install command if you know it from a source." with:

> Check `machine_inventory.accelerators`. Copy the installed ones to `accelerators_present`. Only an accelerator marked `installed: false` may go in `accelerators_missed`, with the install command from the known-accelerators table. Never put an item in `accelerators_missed` to say it is installed. The DocumentDB Agent Kit is the set of `documentdb-*` skills in `installed_skills`; when it is marked installed, never recommend `npx skills add Azure/documentdb-agent-kit` and do not list it under `inventory_recommendations`. An accelerator that the shared environment note says is deliberately not provided for this run (for example a local DocumentDB container when a live cluster is the target) is not missed; at most mention it as the `workaround` for the tool it would replace.

**6. `loop/findings.py`, `accelerators_missed` loop.**
- Skip entries that match `INSTALLED_PHRASES` without "not installed".
- Skip entries that name an accelerator the `02-inventory.json` next to the readiness file marks as installed.
- Set `target="pipeline"`.
- Use the entry's own text as `detail`.

**7. Tests**
- `tests/test_units.py`:
  - (a) Kit marked installed, and "DocumentDB Agent Kit (npx skills add ...) — not installed" in the missed list: after `reconcile_accelerators`, `accelerators_missed == []` and the kit is in `accelerators_present`.
  - (b) "Azure DocumentDB MCP Toolkit is installed, so no action required." moves to present.
  - (c) No-skills arm (`installed_skills == []`): the kit entry stays in missed.
- `tests/test_pipeline_offline.py` seeds `accelerators_missed=["DocumentDB Agent Kit"]`. Give it a no-skills inventory so the assertion does not flip.

**Not in this PR.** Starting the local container in loop runs would change what the experiment measures: builders could verify against the local container instead of the live cluster. If that workflow is ever wanted, it should be a separate opt-in arm, for example a `--local-gateway` flag with one container per run on its own port. Installing Bicep in the build image is handled in a separate filing. Running the kit's own installer (`npx skills add Azure/documentdb-agent-kit`) in the build image, so that `skills-lock.json` is always present as the marker, is optional; the repository already has the lock file, so detection is the cheaper fix.

## Evidence

- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`: the kit is listed as missed; `02-inventory.json` lists 17 skills, and `events.jsonl` loads 9 of them.
- `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json`: "MCP Toolkit ... is installed, so no action required" appears in `accelerators_missed`.
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/02-readiness.json`: the kit is in both `accelerators_missed` and `inventory_recommendations`.
- `runs/18-360-data-platform-cdp-orchestration/20261124-205822/02-readiness.json`: the documentdb MCP is reported missing although it answered with 18 tools.
- `runs/17-esg-scoring-pipeline/20261124-192259/02-readiness.json`: the local container is the only missed accelerator; the build completed against the live cluster.
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/02-readiness.json`: `azd` is marked `worth_adding: true`.

## Open questions

1. Does the open-source `documentdb-local` image match the managed service for `vector-diskann` indexes and Entra ID authentication? This matters only if a local-container arm is added later. [needs SME confirmation]
2. The drafts disagree on how to detect the kit. 058 counts it as installed if `skills-lock.json` names `Azure/documentdb-agent-kit` **or** any `documentdb-*` skill is present. 070 requires the lock entry **and** at least one skill. The code above uses AND. The maintainer should decide whether hand-copied skills with no lock file count as the kit.
3. Should the container carve-out also be enforced in code (for example, dropping container entries when the environment note is present), or is the prompt change enough?
4. The counts come from a single run, and the reviewer flags them as unstable. Before quoting them outside the team, re-run the batch after this PR (and the harness MCP and audit-rubric fixes).

## Source drafts

- 058-readiness-stage-reports-installed-accelerators-the-agent-kit.md
- 070-readiness-inventory-one-offs-azd-not-installed-agent-kit-rec.md
- 063-documentdb-local-container-not-pre-pulled-or-running-in-the-.md
