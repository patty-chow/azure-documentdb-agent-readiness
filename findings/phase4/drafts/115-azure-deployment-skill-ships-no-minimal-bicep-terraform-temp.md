---
title: "azure-deployment skill: add an \"author IaC only, don't deploy\" path so no-provision builders vendor the existing mongoClusters Bicep"
repo: Azure/documentdb-agent-kit
type: issue
status: ready_with_edits
priority: P1
sample_count: 20
findings: 20
bucket: mcp-server
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# azure-deployment skill: add an "author IaC only, don't deploy" path

## What happens today
The kit already has good `Microsoft.DocumentDB/mongoClusters` templates (API `2025-09-01`): `skills/azure-deployment/references/bicep-cluster-template.md`, `references/terraform-cluster-template.md` and `examples/azure-deployment/main.bicep` (with `main.parameters.dev.json`). Agents don't use them when they are told not to provision anything.

`skills/azure-deployment/SKILL.md` is written as an interactive deployment. Its description starts with "Deploy an Azure DocumentDB cluster...", and Step 0 is a preflight that it says to "run before anything else": it needs `az login`, an active subscription, provider registration and Contributor rights. The templates are only pointed to from Step 5/6 ("choose a deployment path", "deploy with Bicep").

In our gpt-5-mini agent-readiness runs, the build policy did not allow creating Azure resources. In the runs we checked, the readiness stage sometimes loaded the skill (for example runs 03 and 16 called `load_skill documentdb-azure-deployment`), but the build stage never loaded the skill or opened its references or examples. The builder recorded a "target the existing cluster, do not provision" decision and shipped no `infra/` folder.

## Why it matters
- 20 of 100 samples failed the audit requirement "Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type".
- In the same runs, the cold readiness quiz often gave the resource type as `Microsoft.DocumentDB/databaseAccounts` (the RU-based Cosmos DB account resource). Someone copying a sample with no template is likely to provision the wrong resource.
- The fix is cheap because the template already exists. Agents only need to be told they can copy it without deploying.

## Proposed change (SKILL.md only, no new templates)
1. **Frontmatter `description`:** add a trigger such as "...or needs to add Bicep/Terraform for a cluster to a repository, even when it must not deploy anything."
2. **New section before Step 0, "IaC authoring only (no deployment)":**
   - Skip the Step 0 preflight. No `az login` is needed to write files.
   - Copy `examples/azure-deployment/main.bicep` and `main.parameters.dev.json` into the project's `infra/` folder, or generate them from `references/bicep-cluster-template.md` (or the Terraform reference if the project already uses Terraform). Do not commit passwords; keep `adminPassword` as a secure parameter.
   - In the README, state that the sample targets `Microsoft.DocumentDB/mongoClusters` (vCore, M-series tiers) and should not use `databaseAccounts` / `az cosmosdb` templates.
   - Show how to get the connection string with `az documentdb mongocluster list-connection-strings` (from the `documentdb` CLI extension) without echoing it, and point the app at it through an environment variable. Step 8 today only mentions the portal, so this command can also be added there.
   - Do not run `az deployment group create`. Note that deploying is optional and costs money.

## Evidence
- runs/03-portfolio-tracker-with-live-alerts/20261124-190220/05-audit.json (requirement not_met; the builder chose not to provision, decision D009, because run policy forbids creating Azure resources)
- runs/16-multi-touch-attribution-model/20261124-205342/05-audit.json (no bicep/terraform/mongocluster files in the repo; build log_decision "target the existing DocumentDB cluster and not provision any resources")
- runs/18-sanctions-list-screening-agent/20261124-202645/05-audit.json and 02-readiness.json (no infra artifact; quiz answered `databaseAccounts`)
- runs/01-fraud-detection-with-vector-similarity/20261124-185817/doc-gaps.md ("[high] IaC example for DocumentDB")

## Verification

### 1. Already covered? partially_covered
The templates the original theme asked for already exist. `skills/azure-deployment/SKILL.md` says the cluster type is "`Microsoft.DocumentDB/mongoClusters`, API `2025-09-01`" and Step 5 says "For Bicep, load `references/bicep-cluster-template.md`". `examples/azure-deployment/main.bicep` line 53 declares `resource cluster 'Microsoft.DocumentDB/mongoClusters@2025-09-01'`. `references/terraform-cluster-template.md` gives `azurerm_mongo_cluster` (AzureRM 4.x) plus AzAPI firewall rules. What is missing: the skill has no path for writing IaC without deploying. Step 0 is mandatory "before anything else", and the description is deployment-only. Step 8 gives only the portal route, not `az documentdb mongocluster list-connection-strings`. So the content is there but not where a no-provision builder looks. The theme's original proposal (add new templates) was dropped from this draft for that reason.

### 2. Premise true? confirmed (one detail corrected)
- The resource type `Microsoft.DocumentDB/mongoClusters` and the `az documentdb mongocluster` CLI group match the given facts. I checked `az documentdb mongocluster --help` locally (documentdb extension 1.0.0): it lists `list-connection-strings` ("List mongo cluster connection strings...").
- Build-stage behavior checked in events.jsonl: runs 03 and 16 show `load_skill documentdb-azure-deployment` only in the readiness stage, and run 16's build stage logged a no-provision decision. Runs 18 and 01 have no load of the skill at all. Corrected the draft's "0 reads in events.jsonl" claim: the skill was loaded in the readiness stage in some runs, but never in the build stage.
- Readiness cold answers of `Microsoft.DocumentDB/databaseAccounts` confirmed in 02-readiness.json for runs 16, 18 and 01 (question Q01).
- The audit text for run 03 confirms the "run policy forbids creating Azure resources" reason.

### 3. Maintainer skeptic: confirmed
It names one file (`skills/azure-deployment/SKILL.md`) and gives concrete edits (a description trigger, a new section, a CLI command in Step 8) that reuse assets already in the repo. It is specific to Azure DocumentDB (mongoClusters vs databaseAccounts). It belongs in Azure/documentdb-agent-kit, not documentdb-mcp, even though the extractor put it in the mcp-server bucket. Part of the cause is in the pipeline: the builder prompt could tell the agent to write infra/ even when it must not provision. That should be filed against the harness separately.

## Finding ids
F0062, F0236, F0275, F0339, F0406, F0491, F0906, F1124, F1213, F1744, F1816, F2234, F2346, F2741, F3032, F3058, F3134, F3280, F3382, F3412
