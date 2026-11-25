---
id: H09
title: "Build image: install Bicep via az and allow local az bicep build/lint"
repo: abinav2307/azure-documentdb-agent-readiness
type: pr
status: needs_sme
hold: owner decision 2026-11-25, no PRs or issues against the harness for now; share with its owner informally instead
priority: P1
sample_count: 19
member_drafts:
  - 067-harness-build-image-lacks-the-iac-toolchain-bicep-cli-terraf.md
open_questions: 2
---

# Build image: install Bicep via az and allow local az bicep build/lint

> This repository belongs to a colleague (abinav2307); coordinate with them before opening this PR.

## What happens today

`factory/tools/environment.py` probes `bicep --version` and `terraform version` on every run. On the build machine both are reported `not found on PATH` in every run's `02-inventory.json`. Because of this, `prompts/readiness_checker.md` makes the readiness agent write one `inventory_recommendations` entry per tool per run, for example "install with `az bicep install`" or "install Terraform if the sample ships Terraform".

Two problems turn that recommendation into recurring noise instead of a fix:

1. **The builder keeps planning IaC it cannot check.** The builder loads the agent kit's `azure-deployment` skill, which recommends Bicep (Step 6a) and also offers Terraform (Step 6c, `azurerm_mongo_cluster` on `Microsoft.DocumentDB/mongoClusters`). No generated app contains a `.bicep` or `.tf` file. The requirement "Infrastructure for the cluster is provided as code" is `not_met` in every audit that contains it (114 of 114).
2. **The command policy refuses the workaround the prompt suggests.** `readiness_checker.md` recommends "compile Bicep through `az bicep build`". But `AZ_READ_VERBS` in `factory/tools/shell.py` has no Bicep subcommands, and with Azure writes off a command runs only if one of its positional words is a read verb:

```
az bicep build --file infra/main.bicep   -> REFUSED
az bicep lint  --file infra/main.bicep   -> REFUSED
az bicep install                         -> REFUSED
az bicep version                         -> ALLOWED ("version" is a read verb)
az deployment group validate ... --template-file infra/main.bicep -> ALLOWED
bicep build infra/main.bicep             -> ALLOWED by policy, but bicep is not installed
```

`bicep` and `terraform` are already in `DEFAULT_ALLOWED_COMMANDS` (`factory/config.py`); the executables are allowed but missing.

## Why it matters

- 19 of the 100 samples carry a `worth_adding: true` recommendation for a tool the harness controls, not the sample author (32 recommendations: bicep 20 times, terraform 12 times; 29 of them are the finding ids listed for this filing). A triager has to read and discard each one. Counts are from one experiment run and may shift on a re-run.
- The builder cannot verify an IaC artifact offline, which removes the cheapest reason to write one. (Builders also skipped IaC because they were told not to provision, so this is one cause, not the only one.)
- The pipeline contradicts itself: the readiness prompt recommends `az bicep build`, and the shell policy refuses it.

## Proposed change

**1. `loop/provision.sh`**: install the Bicep CLI that the Azure CLI manages, next to the existing `az extension add -n documentdb` prerequisite:

```bash
# Bicep: the azure-deployment skill recommends Bicep; let the builder compile and lint templates locally.
az bicep install >/dev/null 2>&1 || az bicep upgrade >/dev/null 2>&1
az bicep version
```

The Azure CLI installs a self-contained Bicep under `~/.azure/bin` and does not add it to PATH, so this makes `az bicep ...` work, not a bare `bicep`. `az` is already required, so there is no new dependency. Do not install Terraform in the image (see step 3).

**2. `factory/tools/shell.py`**: allow only the local `az bicep` subcommands. Do **not** add `"bicep"` to `AZ_READ_VERBS`: the any-word check would then also allow `az bicep publish`, which pushes a module to an Azure Container Registry (a write).

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

After this, `az bicep build` and `az bicep lint` run under the default no-writes policy, alongside the already-allowed `az deployment group validate/what-if --template-file`. That is the "write infra as files, verify without provisioning" path `prompts/builder.md` asks for.

**3. `factory/tools/environment.py`**: probe Bicep the way it is installed, and mark Terraform, `azd` and `dotnet` optional:

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

Without the probe change, the inventory still reports bicep missing after step 1 and the recommendation keeps firing.

**4. `prompts/readiness_checker.md`**: add to the "Inventory recommendations" paragraph:

> For a tool the inventory marks `optional`, set `worth_adding` to true only if the sample prompt or its requirements name that toolchain (for example a prompt that asks for Terraform). Otherwise set it to false and write "optional, not requested by this sample".

and change the example fallback to "compile Bicep through `az bicep build`, which uses the Bicep copy that the Azure CLI installs".

**5. `factory/reports.py`**: print `(optional)` after the tool name, as it already prints `(required)` for MCP servers.

**6. Tests**: in `tests/test_units.py` (near lines 47-48) add `az bicep build --file main.bicep` -> allowed and `az bicep publish --file m.bicep --target br:...` -> refused. The `ToolReadiness(name="bicep", ... workaround="az bicep build")` fixture in `tests/test_pipeline_offline.py` (line 75) then matches real behavior.

Optional follow-up, separate from this PR: in `Azure/documentdb-agent-kit`, `skills/azure-deployment/SKILL.md` Step 6a could add one sentence saying Azure CLI deployments compile the Bicep file locally with a Bicep copy the CLI installs on first use, so no standalone `bicep` on PATH is needed, and that when there is no network to download it, `az bicep install` (or copying the binary into `~/.azure/bin`) fixes the offline case, with `az bicep build --file main.bicep` producing the ARM JSON for review.

## Evidence

- `runs/06-collateral-management-store/20261124-200922/02-inventory.json`: bicep and terraform `not found on PATH`; `az` present.
- `runs/06-collateral-management-store/20261124-200922/02-readiness.json`: bicep and terraform inventory recommendations.
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json`: notes that `az deployment group create --template-file main.bicep` works without a standalone CLI.
- `runs/19-insider-threat-detection-pipeline/20261124-202818/05-audit.md`: IaC requirement `not_met`, no Bicep/Terraform files in the app.
- `runs/19-insider-threat-detection-pipeline/20261124-202818/doc-gaps.md`: no IaC example in the repo or the agent-kit templates.

## Open questions

1. Is it acceptable for `az bicep build`/`restore` to pull registry modules into the local cache under the no-writes policy, or should `restore` be left out of the allowlist?
2. For the optional agent-kit follow-up: confirm that Azure CLI deployments compile Bicep on the client with the CLI-managed Bicep copy (as Learn's Bicep install and Bicep CLI pages state), not server-side, before that sentence is added to the skill. [needs SME confirmation]

## Source drafts

- 067-harness-build-image-lacks-the-iac-toolchain-bicep-cli-terraf.md
