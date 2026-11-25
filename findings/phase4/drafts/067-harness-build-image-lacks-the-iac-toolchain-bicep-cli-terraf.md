---
title: "Build image: install Bicep via az, allow local `az bicep build/lint` under the read-only policy, mark Terraform optional in the inventory"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: ready_with_edits
priority: P1
sample_count: 19
findings: 29
bucket: other-inventory
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Build image: install Bicep via az, allow local `az bicep build/lint` under the read-only policy, mark Terraform optional in the inventory

## What happens today

`factory/tools/environment.py` probes `bicep --version` and `terraform version` ("Infrastructure as code") on every run. On the build machine both are `not found on PATH` in all 120 runs (`02-inventory.json`), so `prompts/readiness_checker.md` makes the readiness agent write one `inventory_recommendations` entry per tool per run. `worth_adding: true` appears 20 times for bicep and 12 times for terraform, across 19 sample folders (29 findings). The text is always some version of "install with `az bicep install`", "install Terraform if the sample ships Terraform", or "the deployment skill should tell agents how to cope without `bicep`".

Two things turn the recommendation into repeated noise instead of a fix:

1. The builder loads the agent kit's `azure-deployment` skill. That skill recommends Bicep (Step 6a, using `references/bicep-cluster-template.md`) and also has a Terraform path (Step 6c, `azurerm_mongo_cluster` on `Microsoft.DocumentDB/mongoClusters`). So the model keeps planning IaC it has no way to check locally. None of the generated apps contains a `.bicep` or `.tf` file (`find runs -path '*/app/*' \( -name '*.bicep' -o -name '*.tf' \)` returns 0). The drafted requirement "Infrastructure for the cluster is provided as code" is `not_met` in all 114 audits that contain it.
2. The command policy refuses the workaround that the readiness prompt suggests ("compile Bicep through `az bicep build` when `bicep` is not on PATH"). `AZ_READ_VERBS` in `factory/tools/shell.py` includes `validate`, `what-if` and `export` but has no Bicep subcommands. With Azure writes off, a command runs only if one of its positional words is a read verb:

```
az bicep build --file infra/main.bicep   -> REFUSED: this run may not change Azure resources ...
az bicep lint  --file infra/main.bicep   -> REFUSED ...
az bicep install                         -> REFUSED ...
az bicep version                         -> ALLOWED ("version" is a read verb)
az deployment group validate ... --template-file infra/main.bicep -> ALLOWED (calls Azure, no writes)
bicep build infra/main.bicep             -> ALLOWED by policy, but bicep is not installed
```

`bicep` and `terraform` are already in `DEFAULT_ALLOWED_COMMANDS` (`factory/config.py`). The executables are allowed but missing.

## Why it matters

- 19 sample folders carry a `worth_adding: true` recommendation for a tool that the harness controls, not the sample author. A triager has to read and discard every one.
- The builder cannot check an IaC artifact offline, and that removes the cheapest reason to write one. The IaC requirement also fails for other reasons (builders logged "do not provision" in the decision log), but an artifact nobody can verify is one of them.
- The pipeline contradicts itself: `readiness_checker.md` tells the model to recommend `az bicep build` as the fallback, and `shell.py` refuses that command.

## Proposed change (one decision at the pipeline level)

**1. `loop/provision.sh`**: install the Bicep CLI that the Azure CLI manages, next to the existing prerequisite (the header comment on line 3 already names `az extension add -n documentdb`):

```bash
# Bicep: the azure-deployment skill recommends Bicep; let the builder compile and lint templates locally.
az bicep install >/dev/null 2>&1 || az bicep upgrade >/dev/null 2>&1
az bicep version
```

The Azure CLI installs its own self-contained copy of Bicep under `~/.azure/bin` and **does not add it to PATH**. So this step makes `az bicep ...` work. It does not make a bare `bicep` command work. `az` is already required, so the step adds no new dependency. Do **not** install Terraform in the image (see step 3).

**2. `factory/tools/shell.py`**: allow only the local `az bicep` subcommands. Do not add `"bicep"` to `AZ_READ_VERBS`. The current check accepts a command if *any* positional word is a read verb, so adding `bicep` would also allow `az bicep publish`, which pushes a module to an Azure Container Registry. That is a write. Add an explicit rule for the group instead:

```python
# `az bicep` subcommands that only read or write local files (build/lint may restore
# registry modules into the local cache, which is a read). `publish` writes to a registry and stays refused.
AZ_BICEP_LOCAL_VERBS = {
    "build", "build-params", "lint", "format", "decompile", "decompile-params",
    "generate-params", "restore", "version", "list-versions", "install", "upgrade",
}
...
if exe == "az" and words[:1] == ["bicep"]:
    if len(words) > 1 and words[1] in AZ_BICEP_LOCAL_VERBS:
        return None
    # fall through to the normal refusal (covers `az bicep publish`)
```

After this change, `az bicep build --file infra/main.bicep` and `az bicep lint ...` run under the default no-writes policy, alongside the `az deployment group validate/what-if --template-file infra/main.bicep` commands that are already allowed. That gives the "write infra as files, verify without provisioning" path that `prompts/builder.md` asks for.

**3. `factory/tools/environment.py` + `prompts/readiness_checker.md`**: probe Bicep the way it is installed, and mark Terraform (plus `azd` and `dotnet`) as optional so the recommendation stops firing when a sample does not ask for that toolchain:

```python
# name -> (command, what it is for, optional)
CLI_PROBES = {
    "az":        (["az", "version", "--output", "json"], "Provision and inspect Azure resources", False),
    "azd":       (["azd", "version"], "Template-based provision and deploy", True),
    # az installs Bicep off PATH, so probe it through az; fall back to a standalone `bicep --version`.
    "bicep":     (["az", "bicep", "version"], "Infrastructure as code (installed via `az bicep install`)", False),
    "terraform": (["terraform", "version"], "Infrastructure as code (only when the prompt asks for Terraform)", True),
    ...
}

@dataclass
class CliStatus:
    name: str
    purpose: str
    available: bool
    detail: str
    optional: bool
```

The probe change matters. If it keeps calling `bicep --version`, the inventory still reports bicep as missing after step 1, and the recommendation keeps firing.

Add this to the "Inventory recommendations" paragraph of `prompts/readiness_checker.md`:

> For a tool the inventory marks `optional`, set `worth_adding` to true only if the sample prompt or its requirements name that toolchain (for example a prompt that asks for Terraform). Otherwise set it to false and write "optional, not requested by this sample".

Also change the paragraph's example fallback to "compile Bicep through `az bicep build`, which uses the Bicep copy that the Azure CLI installs". `factory/reports.py` can print `(optional)` after the tool name, the same way it already prints `(required)` for MCP servers. Update the tests:

- `tests/test_pipeline_offline.py`: the `ToolReadiness(name="bicep", ... workaround="az bicep build")` fixture at line 75 becomes accurate.
- `tests/test_units.py` lines 47-48: add an `az bicep build --file main.bicep` → allowed case and an `az bicep publish --file m.bicep --target br:...` → refused case.

## Optional follow-up outside this repo (F0865)

In `Azure/documentdb-agent-kit`, `skills/azure-deployment/SKILL.md`, Step 6a, add one sentence: Azure CLI deployments (`az deployment group create|validate|what-if --template-file main.bicep`) compile the Bicep file locally with a Bicep copy that the Azure CLI installs automatically on first use, so no standalone `bicep` on PATH is needed. When there is no network to download it, `az bicep install` (or copying the binary into `~/.azure/bin`) is the fix, and `az bicep build --file main.bicep` produces the ARM JSON for review. An agent in any environment could then answer its own "bicep missing" question. The pipeline change above does not depend on this.

## Evidence (run folders, no secrets)

- `runs/06-collateral-management-store/20261124-200922/02-inventory.json`: `bicep` and `terraform` both `not found on PATH`; `az` 2.89.1 present.
- `runs/06-collateral-management-store/20261124-200922/02-readiness.json`: `inventory_recommendations` for bicep and terraform (F0865/F0866), including the suggestion that the agent kit provide generated ARM JSON if Bicep is unavailable.
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: the recommendation notes that `az deployment group create --template-file main.bicep` works without a standalone CLI (F0126/F0127).
- `runs/19-insider-threat-detection-pipeline/20261124-202818/05-audit.md`: IaC requirement `not_met`, with no Bicep/Terraform files targeting `Microsoft.DocumentDB/mongoClusters` in the repo.
- `runs/19-insider-threat-detection-pipeline/20261124-202818/doc-gaps.md`: no IaC example in the repo or in the agent-kit templates for gallery samples.

## Verification

### 1. Already covered? confirmed (not there)
- Pipeline (the target repo, local checkout): `factory/tools/shell.py` lines 27-30 define `AZ_READ_VERBS = {"list","show","version","find","help","list-locations","list-skus","list-connection-strings","check-name-availability","what-if","validate","export"}`, with no Bicep subcommands. `factory/tools/environment.py` lines 20-21 probe `"bicep": (["--version"], "Infrastructure as code")` and `"terraform": (["version"], "Infrastructure as code")`, with no optional flag. `loop/provision.sh` does not run `az bicep install`. `prompts/readiness_checker.md` line 45 suggests `az bicep build` as the fallback.
- Agent kit (follow-up only): grepping `skills/` and `knowledge-base/` for `az bicep`, `bicep install` and `bicep CLI` finds nothing. `skills/azure-deployment/SKILL.md` Step 6a deploys with Bicep but says nothing about the Bicep CLI being missing.

### 2. Is the premise true? confirmed, with three corrections applied to the body
- Confirmed by recount: all 120 inventories lack bicep and terraform; `worth_adding` is true 20 times for bicep and 12 for terraform across 19 sample folders (the draft said 18); 0 `.bicep` or `.tf` files are under `runs/*/*/app`; the IaC requirement is `not_met` in 114 of 114 audits that contain it; `az bicep build|lint|install` are refused by the any-word read-verb check, and `az bicep version` is allowed.
- Correction A: the draft said the `az bicep` group "never changes Azure resources" and proposed adding `"bicep"` to `AZ_READ_VERBS`. That is wrong. Per https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/bicep-cli, `publish` "adds a module to a registry" (an Azure Container Registry). With the any-word check, a bare `"bicep"` read verb would allow it. The body now allowlists the local subcommands and keeps `publish` refused.
- Correction B: per https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/install, "The Azure CLI installs a self-contained instance of the Bicep CLI" and "doesn't add Bicep CLI to your PATH". So after `az bicep install`, the existing `bicep --version` probe would still report bicep missing. The body now probes `az bicep version`.
- Correction C: the draft's agent-kit follow-up said `az deployment group create` compiles Bicep "server-side". The same install page says "Azure CLI automatically installs the Bicep CLI when a command is executed that needs it", and the bicep-cli page says `build` "runs automatically when you deploy a Bicep file". Compilation happens on the client, using the CLI-managed copy. The follow-up text is corrected.
- Agent-kit facts checked: Step 6a uses Bicep and is marked "(recommended)"; Step 6c uses `azurerm_mongo_cluster` on `Microsoft.DocumentDB/mongoClusters`. Both are consistent with the service facts.

### 3. Maintainer skeptic: confirmed
The draft names exact files, line numbers and code changes in the harness repo (`loop/provision.sh`, `factory/tools/shell.py`, `factory/tools/environment.py`, `prompts/readiness_checker.md`, tests). It fixes a real contradiction between the prompt and the command policy, and it stops a recurring false recommendation. The Azure DocumentDB angle is the Bicep-first `azure-deployment` skill targeting `mongoClusters`. I would accept it with the corrections applied, which avoid opening a registry-write path. The agent-kit item is correctly marked as an optional follow-up for `Azure/documentdb-agent-kit`, so the repo in the front matter stays the same.

## Finding ids

F0089, F0090, F0126, F0127, F0436, F0510, F0674, F0865, F0866, F1018, F1019, F1177, F1237, F1279, F1998, F2068, F1178, F1238, F2069, F2567, F2629, F2824, F2992, F3274, F3474, F2568, F2630, F2993, F3475
