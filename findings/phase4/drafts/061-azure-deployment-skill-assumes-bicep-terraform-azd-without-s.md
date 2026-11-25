---
title: "azure-deployment skill: add a per-path tooling preflight (az bicep / terraform / azd) and name the az-only path as the default for samples"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 14
findings: 33
bucket: kit-accelerator-missed
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# azure-deployment: add a per-path tooling preflight (`az bicep` / `terraform` / `azd`) and name the az-only path as the default for samples

## What happens today

`skills/azure-deployment/SKILL.md` offers four deployment paths in Step 5 (Bicep recommended, Azure CLI one-shot, Terraform, portal), but **Step 0 — preflight checks** only verifies that `az` exists, is signed in, has the right subscription, the `Microsoft.DocumentDB` provider, a write role and a supported region. The skill never:

- runs `az bicep version`, or tells the agent that the Azure CLI installs and manages its own self-contained Bicep CLI (under `~/.azure/bin`, **not** added to PATH), so a standalone `bicep` binary is not needed for `az deployment group create --template-file main.bicep`;
- checks `terraform` before Step 6c offers the Terraform route;
- mentions the Azure Developer CLI (`azd`) at all;
- uses the `az documentdb mongocluster` extension command group. Step 6b uses generic `az resource create`; the only other kit reference to the extension (`skills/storage/storage-premium-ssdv2-limitations.md`) spells it `az documentdb mongo-cluster restore`, which the CLI rejects ("'mongo-cluster' is misspelled ... Did you mean 'mongocluster'?").

Result in the agent-readiness experiment (100 Azure DocumentDB sample prompts, gpt-5-mini, kit skills + DocumentDB/Azure/Learn MCP): in 14 of 100 samples (33 findings) the readiness stage reported `bicep`, `terraform` and/or `azd` as accelerators that were not installed (bicep 13 findings, terraform 13, azd 11). On that machine `az bicep version` succeeds (Bicep CLI 0.48.1, managed by `az`), so the "bicep not on PATH" report was a false negative that one preflight line would have prevented. The builder also shipped no infrastructure files: the audit requirement "infrastructure for the cluster is provided as code using the Azure DocumentDB resource type" was `not_met` in 100/100 samples (115 audited runs). Several audits' smallest_fix is literally "add a minimal Bicep template or document `az documentdb mongocluster create`", which is what this skill is for.

## Why it matters

Agents either spend turns discovering that `bicep`/`terraform`/`azd` are absent, emit an unvalidated `main.bicep`, or report all three tools as gaps and skip IaC. A prerequisites block scoped per path (and explicitly optional under a no-provisioning policy) removes the discovery cost, stops false "missing tool" reports, and gives the agent a zero-extra-tooling default.

## Proposed change (primarily `skills/azure-deployment/SKILL.md`)

### 1. Add check 7 to **Step 0 — preflight checks**

```bash
# 7. Tooling for the deployment path you will pick in Step 5 (all optional —
#    skip entirely if the run policy forbids provisioning).
#    Bicep: the Azure CLI installs and manages its own Bicep CLI (not on PATH).
#    Do not look for a `bicep` binary on PATH.
az bicep version || { az bicep install && az bicep version; }
#    Terraform: only if the user chose Step 6c.
terraform -version
# → If missing: https://developer.hashicorp.com/terraform/install
#    azd (Azure Developer CLI): only if the user chose Step 6d.
azd version
# → If missing: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd
#    az documentdb extension (zero extra tooling; used by Step 6b):
az extension add --name documentdb --upgrade
az documentdb mongocluster --help >/dev/null
```

Add one sentence after the block: "Do not report `bicep` as missing because `which bicep` fails — `az bicep version` is the check. Azure CLI installs its Bicep CLI automatically the first time a command needs it, so `az deployment group what-if --resource-group <rg> --template-file main.bicep` (signed in, existing resource group) validates a template without any separately installed `bicep` binary."

### 2. Extend the **Step 5** path table

Add a row above Terraform:

| **Azure CLI via `az documentdb mongocluster`** | Samples, CI, any run where no extra tooling may be installed; needs only `az` + the `documentdb` extension | [Step 6b](#step-6b--deploy-with-azure-cli-one-shot) |

and mark the Bicep row "(recommended for repos; `az bicep version` must pass)" and the Terraform row "(requires `terraform -version` to pass)".

### 3. In **Step 6b** show the extension command alongside `az resource create`

```bash
az extension add --name documentdb --upgrade
az documentdb mongocluster create \
  --resource-group rg-docdb-dev --name docdb-dev-001 --location eastus2 \
  --admin-user clusteradmin --admin-password "$DOCDB_ADMIN_PASSWORD" \
  --tier M10 --storage-size 32 --shard-count 1 \
  --high-availability Disabled --server-version 8.0
```

(Flags verified against `az documentdb mongocluster create --help`, extension `documentdb` 1.0.0: `--tier`, `--storage-size`, `--shard-count`, `--high-availability`, `--admin-user`, `--admin-password` are required.) Keep the existing `az resource create` block as the fallback when the extension cannot be installed.

### 4. Add **Step 6d — deploy with azd (optional)**

Short subsection: state that azd is optional and what it adds (one `azd up` for infra + app, per-environment `.azure/<env>/.env`, no secrets in the repo; azd carries its own Bicep CLI). Layout:

```
azure.yaml            # name: <app>; services: {} or the sample's service
infra/main.bicep      # reuse references/bicep-cluster-template.md (resource-group scope, or a subscription-scope wrapper)
infra/main.parameters.json
```

Wiring: `azd env set DOCDB_ADMIN_PASSWORD "$(az keyvault secret show ... -o tsv)"` and expose the cluster host as an output the app reads from `azd env get-values`; never write the password or a full connection string into `azure.yaml` or source. If `azd version` fails, fall back to Step 6a/6b; nothing in a sample should require azd.

### 5. One line in the **Step 0** intro

"When the run or user policy forbids creating Azure resources, skip checks 5–7, still generate the IaC file (Bicep or the Step 6b script), and validate it with `az deployment group what-if` if a resource group is available."

### 6. Small related fixes in other skills

- Bicep snippets for `Microsoft.DocumentDB/mongoClusters` also appear in `skills/storage/storage-choose-premium-ssdv2.md`, `skills/storage/storage-disk-hydration-sequencing.md`, `skills/high-availability/ha-enable-for-production.md` and `ha-cross-region-replica.md` (plus Bicep blocks in `security-private-endpoint.md`, `security-cmk-encryption.md`, `storage-tier-iops-caps.md`, `monitoring-metrics-alerts.md`). Rather than duplicate the preflight, add a one-line pointer in each: "Prerequisites: see azure-deployment Step 0, check 7."
- `skills/storage/storage-premium-ssdv2-limitations.md` line 28: change `az documentdb mongo-cluster restore` to `az documentdb mongocluster restore`.

## Evidence (run folders from the experiment; no connection strings)

- `runs/07-customer-review-sentiment-pipeline/20261124-183656/02-readiness.json` — `accelerators_missed` lists azd, bicep, terraform with install hints; `02-inventory.json` in the same folder shows `az` 2.89.1 present with the `documentdb` extension, yet `bicep: not found on PATH`.
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/02-readiness.json` and `05-audit.json` — all three tools flagged; IaC requirement `not_met`, smallest_fix suggests a small Bicep/ARM/Terraform sample or an `az documentdb mongocluster` CLI snippet.
- `runs/20-open-banking-api-cache-layer/20261124-192737/02-readiness.json` — bicep and terraform described as useful only for optional IaC; the agent skipped IaC because tools were absent.
- `runs/14-hyper-personalized-content-engine/20261124-205043/02-readiness.json`, `runs/18-sanctions-list-screening-agent/20261124-202645/02-readiness.json` — same three-tool pattern.

Affected samples (14/100): 07-customer-review-sentiment-pipeline, 08-interest-rate-scenario-modeler, 10-support-ticket-rag-assistant, 10-wealth-management-rag-portal, 11-visual-similarity-search-image-embeddings, 12-hospital-bed-occupancy-tracker, 14-hyper-personalized-content-engine, 16-multi-touch-attribution-model, 17-ai-survey-response-analyzer, 17-stress-testing-multi-agent-runner, 18-sanctions-list-screening-agent, 19-proactive-outreach-orchestration, 20-identity-resolution-multi-agent, 20-open-banking-api-cache-layer.

## Notes for reviewers

- The main change is in `skills/azure-deployment/SKILL.md`; `references/bicep-cluster-template.md` and `references/terraform-cluster-template.md` are untouched (the Terraform reference already pins `required_version >= 1.2.0`, which the new `terraform -version` check makes actionable).
- The experiment harness probes `bicep` as a PATH binary; that is a harness defect filed separately, but the skill should still make `az bicep version` the documented check so agents do not inherit the same mistake.

## Verification

### 1. Already covered? — confirmed (not there)

- `skills/azure-deployment/SKILL.md` Step 0 (lines 15–51) has checks 1–6 only: `az version`, `az account show`, subscription, provider registration, role assignment, region list. No `az bicep`, `terraform`, or `azd` check.
- Step 5 table (lines 162–171) lists Bicep / Azure CLI one-shot / Terraform; Step 6b (lines 214–248) uses `az resource create`, not the `documentdb` extension.
- Grep of `skills/`, `knowledge-base/`, `examples/`, `README.md` for `az bicep`, `azd`, `terraform -version`, `what-if`, `az documentdb`: the only hit is `skills/storage/storage-premium-ssdv2-limitations.md:28` (`az documentdb mongo-cluster restore`, misspelled group).
- Learn quickstart (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-bicep) lists Azure CLI only as prerequisite and does not mention `az bicep`, azd or Terraform tooling checks, so the kit cannot defer to it.

### 2. Is the premise true? — confirmed (two secondary statements corrected in the body)

- Core claims verified: Step 0 checks only `az` (kit file above); 33 findings across 14 samples all target agent-kit (bicep 13, terraform 13, azd 11) from findings-default.json; IaC requirement `not_met` in 115 of 117 audit files, covering all 100 samples; `az bicep version` on the experiment machine prints "Bicep CLI version 0.48.1" while `which bicep/terraform/azd` fail; inventory shows the `documentdb` extension installed.
- Bicep install page (https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/install): "Azure CLI automatically installs the Bicep CLI when a command is executed that needs it" and "The Azure CLI doesn't add Bicep CLI to your PATH." Draft said Bicep "ships inside" the Azure CLI and that `what-if` validates "with no local compiler step"; corrected to: az installs and manages its own Bicep CLI on first use (still a local compile, just no separate install), and `what-if` needs a sign-in and an existing resource group.
- Draft said "No other skill in the kit embeds Bicep for mongoClusters (grep confirms)"; false — `storage-choose-premium-ssdv2.md`, `storage-disk-hydration-sequencing.md`, `ha-enable-for-production.md`, `ha-cross-region-replica.md` and others contain Bicep blocks. Replaced with item 6 (pointers to the preflight).
- `az documentdb mongocluster create --help` (extension documentdb 1.0.0) confirms all flags used; `az documentdb mongo-cluster` is rejected by the CLI.
- azd install page (https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/install-azd) confirms `azd version` as the verify command and that azd installs its own Bicep CLI.
- Shell precedence fixed: `az bicep version || az bicep install && az bicep version` now grouped as `az bicep version || { az bicep install && az bicep version; }`.

### 3. Maintainer skeptic — confirmed

Names the exact file and steps, gives concrete diffs with verified commands, has a direct Azure DocumentDB angle (`Microsoft.DocumentDB/mongoClusters`, the `documentdb` CLI extension), and fixes a real defect (misspelled CLI group). The azd subsection is marked optional and small; a maintainer may trim it, but the preflight and the extension path are acceptable as written.

## Finding ids

F1013, F1014, F1015, F1276, F1277, F1278, F1695, F1696, F1697, F1735, F1736, F1905, F2067, F2404, F2405, F2726, F2727, F2823, F2955, F2956, F3126, F3127, F3336, F3337, F3443, F1734, F2403, F2725, F2822, F2954, F3125, F3375, F3442
