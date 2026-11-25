---
id: K34
title: "azure-deployment skill: add an author-IaC-only (no deploy) path"
repo: Azure/documentdb-agent-kit
type: issue
status: ready
priority: P1
sample_count: 100
member_drafts:
  - 115-azure-deployment-skill-ships-no-minimal-bicep-terraform-temp.md
open_questions: 2
---

# azure-deployment skill: add an author-IaC-only (no deploy) path

## What happens today

The kit already ships good `Microsoft.DocumentDB/mongoClusters` templates (API `2025-09-01`):

- `skills/azure-deployment/references/bicep-cluster-template.md`
- `skills/azure-deployment/references/terraform-cluster-template.md` (`azurerm_mongo_cluster` plus AzAPI firewall rules)
- `examples/azure-deployment/main.bicep` with `main.parameters.dev.json` and `main.parameters.sample.json`

Agents do not use them when they are building a sample app and have been told not to create Azure resources.

`skills/azure-deployment/SKILL.md` is written only as an interactive deployment. Its description starts with "Deploy an Azure DocumentDB cluster ... end-to-end". Step 0 is a preflight to "run before anything else" that needs the Azure CLI, `az login`, the right subscription, provider registration and Contributor/Owner rights. The templates are pointed to only from Step 5 ("choose a deployment path"), Step 6a/6c and the closing References list. Step 8 ("retrieve the connection string") gives only the portal route.

So an agent that must write infrastructure files but must not deploy has no entry point. It either does not load the skill, or loads it and stops at a preflight it is not allowed to run.

## Why it matters

We ran an agent-readiness experiment: an agent (gpt-5-mini) built 100 Azure DocumentDB sample apps under a policy that did not allow creating Azure resources, then an auditor checked each sample. Counts below are from that one experiment run.

- The audit requirement "Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type" was not met in all 100 samples (114 of 114 audits, including re-runs). No sample shipped an `infra/` folder or any Bicep/Terraform file.
- In 20 samples the agent or auditor raised this gap explicitly as a missing kit capability. In the build stage the skill was never loaded and its references and examples were never opened. Where the skill was loaded at all (for example samples 03 and 16), it was only in the earlier readiness stage. The builder logged a decision such as "target the existing DocumentDB cluster and not provision any resources" and moved on.
- In the same runs, the cold readiness quiz often named the resource type as `Microsoft.DocumentDB/databaseAccounts` (the RU-based Cosmos DB account). These quiz answers reflect model priors rather than a kit defect, but a developer copying a sample with no template is likely to provision the wrong resource.

In the latest audit of each sample, the auditor attributed 97 of the 100 misses to the build instructions not asking for IaC (`prompt_silent`), and 3 to the agent believing it could not proceed without deploy tooling (`tool_unavailable`). The build instructions are being fixed separately on the experiment side. This issue covers the kit side: once an agent is asked for IaC, the skill should let it copy the existing template without deploying. The fix is cheap because the templates already exist.

## Proposed change

Edit `skills/azure-deployment/SKILL.md` only. No new templates are needed.

1. **Frontmatter `description`:** it already ends with "or wants infrastructure-as-code for one". Extend that to "...or needs to add Bicep or Terraform for a cluster to a repository, including when nothing may be deployed."
2. **New section before Step 0, "IaC authoring only (no deployment)":**
   - Skip the Step 0 preflight. Writing files needs no `az login`.
   - Copy `examples/azure-deployment/main.bicep` and `main.parameters.sample.json` into the project's `infra/` folder, or generate them from `references/bicep-cluster-template.md` (use `references/terraform-cluster-template.md` if the project already uses Terraform). Never commit a password; keep `adminPassword` a secure parameter.
   - In the project README, state that the sample targets `Microsoft.DocumentDB/mongoClusters` (vCore compute tiers, not request units) and must not use `databaseAccounts` or `az cosmosdb` templates.
   - Show how to get the connection string after an optional deploy with `az documentdb mongocluster list-connection-strings` (from the `documentdb` CLI extension) without echoing it, and point the app at it through an environment variable.
   - Do not run `az deployment group create`. Say that deploying is optional and costs money.
3. **Step 8:** add the same `az documentdb mongocluster list-connection-strings` command next to the portal route.

## Evidence

Paths are run folders in the experiment repository:

- `runs/03-portfolio-tracker-with-live-alerts/20261124-190220/05-audit.json`: requirement not met; the builder chose not to provision (decision D009) because run policy forbids creating Azure resources.
- `runs/16-multi-touch-attribution-model/20261124-205342/05-audit.json`: no Bicep, Terraform or mongocluster files; the skill was loaded only in the readiness stage, and the build stage logged a no-provision decision.
- `runs/18-sanctions-list-screening-agent/20261124-202645/05-audit.json` and `02-readiness.json`: no infra artifact; quiz answered `databaseAccounts`.
- `runs/01-fraud-detection-with-vector-similarity/20261124-185817/doc-gaps.md`: "[high] IaC example for DocumentDB".

## Open questions

1. The source draft said 20 of 100 samples failed the IaC requirement. A recount of the audit files shows all 100 failed, and 20 is the number of samples where the gap was raised as a kit finding. Most misses were attributed to the build instructions, so these numbers should be re-measured after the experiment's build instructions are fixed and before they are quoted outside the team.
2. Should Step 8 recommend the CLI command as the main route for agents, with the portal as the fallback, or keep the portal first?

The experiment harness (abinav2307/azure-documentdb-agent-readiness) belongs to a colleague, so the companion change to its build instructions should be coordinated with them, not filed directly.

## Source drafts

- 115-azure-deployment-skill-ships-no-minimal-bicep-terraform-temp.md
