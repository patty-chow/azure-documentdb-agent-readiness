---
id: K34
title: "azure-deployment skill: name az documentdb mongocluster as the CLI group with a tooling preflight, fix the mongo-cluster typo, and add an author-IaC-only (no deploy) path"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 100
member_drafts:
  - 004-believes-az-cosmosdb-databaseaccounts-ru-account-path-is-the.md
  - 005-believes-the-cluster-commands-live-in-the-core-azure-cli-wit.md
  - 007-believes-the-subgroup-is-spelled-mongodb-cluster-mongo-clust.md
  - 061-azure-deployment-skill-assumes-bicep-terraform-azd-without-s.md
  - 115-azure-deployment-skill-ships-no-minimal-bicep-terraform-temp.md
merged_from:
  - K34
  - K02
open_questions: 2
---

# azure-deployment skill: name `az documentdb mongocluster` as the CLI group with a tooling preflight, fix the `mongo-cluster` typo, and add an author-IaC-only (no deploy) path

## What happens today

`skills/azure-deployment/SKILL.md` is written only as an interactive, end-to-end deployment, and it never names the Azure CLI command group for an Azure DocumentDB cluster (`Microsoft.DocumentDB/mongoClusters`).

**No CLI group, wrong-group prior left uncorrected (from K02).**

- **Step 0 (preflight)** has six checks (`az version`, sign-in, subscription, `Microsoft.DocumentDB` provider, role, region). It does not check for the `documentdb` CLI extension, `az bicep`, `terraform` or `azd`, even though Step 5 offers Bicep, CLI, Terraform and portal paths.
- **Step 6b** and **Step 9** use generic `az resource create --resource-type Microsoft.DocumentDB/mongoClusters --api-version 2025-09-01`; **Step 7** verifies with `az resource list`; **Step 8** fetches the connection string from the portal only.
- The strings `az documentdb mongocluster`, `az extension add --name documentdb` and "not `az cosmosdb`" appear nowhere in the skills, `AGENTS.md`, `README.md` or `docs/SKILLS.md`.
- The only CLI-group mention in the repo is wrong: `skills/storage/storage-premium-ssdv2-limitations.md:28` reads `az documentdb mongo-cluster restore`, which the CLI rejects (the group is the single token `mongocluster`). Its trailing comment ("set storage.type in the restore template") is also stale: `restore` takes `--storage-type` directly.

Because the service was formerly "Azure Cosmos DB for MongoDB vCore", models strongly assume the cluster lives under `az cosmosdb` in the core CLI. `az cosmosdb create --kind MongoDB` creates a request-unit `Microsoft.DocumentDB/databaseAccounts` account, a different resource with a different capacity model (vCore tiers vs request units), flags and connection string. There is also an older `az cosmosdb mongocluster` group in the separate `cosmosdb-preview` extension, with different flags (`--administrator-login`, `--shard-node-tier`, ...), pinned to management API 2024-03-01-preview, and no `list-connection-strings`, `restore`, `replica`, `identity` or `microsoft-entra-user`. It is still a live Preview group, not deprecated, but every Learn Azure DocumentDB page (quickstart-cli, how-to-scale-cluster, development-loop) uses `az documentdb mongocluster`. Mixing the two groups' flags produces commands that fail. The kit is the only thing in an agent's loop that could override this prior, and today it does not.

**No entry point for writing IaC without deploying (from K34).**

The kit already ships good `Microsoft.DocumentDB/mongoClusters` templates (API `2025-09-01`):

- `skills/azure-deployment/references/bicep-cluster-template.md`
- `skills/azure-deployment/references/terraform-cluster-template.md` (`azurerm_mongo_cluster` plus AzAPI firewall rules)
- `examples/azure-deployment/main.bicep` with `main.parameters.dev.json` and `main.parameters.sample.json`

The skill's description starts with "Deploy an Azure DocumentDB cluster ... end-to-end". Step 0 is a preflight to "run before anything else" that needs the Azure CLI, `az login`, the right subscription, provider registration and Contributor/Owner rights. The templates are pointed to only from Step 5 ("choose a deployment path"), Step 6a/6c and the closing References list. So an agent that must write infrastructure files but must not deploy either does not load the skill, or loads it and stops at a preflight it is not allowed to run.

## Why it matters

We ran an agent-readiness experiment: 100 Azure DocumentDB sample prompts, gpt-5-mini with this kit loaded plus the DocumentDB, Azure and Learn MCP servers, under a policy that did not allow creating Azure resources; an auditor then checked each sample. All counts below come from that single run and may shift on a re-run. Together the members cover all 100 samples.

- **No IaC shipped (K34, 100 samples).**
  - The audit requirement "Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type" was not met in all 100 samples (114 of 114 audits, including re-runs). No sample shipped an `infra/` folder or any Bicep/Terraform file.
  - In 20 samples the agent or auditor raised this explicitly as a missing kit capability. In the build stage the skill was never loaded and its references and examples were never opened. Where it was loaded at all (for example samples 03 and 16), it was only in the earlier readiness stage; the builder logged a decision such as "target the existing DocumentDB cluster and not provision any resources" and moved on.
  - In the latest audit of each sample, the auditor attributed 97 of the 100 misses to the build instructions not asking for IaC (`prompt_silent`) and 3 to the agent believing it could not proceed without deploy tooling (`tool_unavailable`). The build instructions are being fixed separately on the experiment side; this PR covers the kit side: once asked for IaC, the skill should let an agent copy the existing template without deploying. The fix is cheap because the templates already exist.
- **Wrong CLI group (K02, 97 samples).**
  - 97 of 100 samples (102 findings) gave a wrong, partly wrong or outdated cold answer to "Which Azure CLI command group creates and manages a cluster?" before grounding. Most answered `az cosmosdb create ... --kind MongoDB` and said it is core CLI (85 samples in the lead draft's set). A few answered with Cosmos DB for NoSQL flags. Two samples were tagged for hyphenating or splitting the group (`az documentdb mongodb cluster create`, `az cosmosdb mongodb cluster`), and the same split shows up in other cold answers. The cold quiz also often named the resource type as `Microsoft.DocumentDB/databaseAccounts`. These are model priors, but they are exactly what the skill should correct: a developer copying a sample with no template is likely to provision the wrong resource.
  - Even after grounding with the kit loaded, answers still hedged between `az documentdb mongocluster` and `az cosmosdb mongocluster`: 11 samples were tagged for this, and others (such as 10-expense-report-auto-categorizer) did too, so 11 is a floor. One picked the legacy group and asked for it to be added to this skill. One proposed a README step `az extension install documentdb`, which is not a real subcommand.
- **Tooling reported missing (K02, 14 samples, 33 findings).** The agent reported `bicep`, `terraform` and/or `azd` as missing. Bicep was a false negative: `az bicep version` worked on that machine, but the agent looked for `bicep` on PATH.

In this experiment the builder was handed an existing cluster, so no sample actually ran `az cosmosdb`. Any user who asks this skill to provision a cluster would hit the same prior, though: Step 0 passes on a stock install, and the agent would create the wrong resource type.

## Proposed change

### 1. `skills/azure-deployment/SKILL.md`

No new templates are needed. Edits in file order:

**a. Frontmatter `description`:** it already ends with "or wants infrastructure-as-code for one". Extend that to "...or needs to add Bicep or Terraform for a cluster to a repository, including when nothing may be deployed."

**b. New section after the intro, before Step 0 — CLI command group:**

```markdown
## CLI command group (read this first)

Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`) are managed by one group:

    az documentdb mongocluster ...

It is a single token (not `mongo-cluster`, not `mongodb cluster`) and ships in the
**`documentdb` extension** (Azure CLI >= 2.75.0), not in core `az`. The version that
`az extension add --name documentdb` installs today (1.0.0) is a stable release; the Learn
reference page is generated from the newer 1.1.0bX preview line and so marks every command
Preview. Install the extension explicitly rather than relying on first-use auto-install
(which prompts in an interactive shell and silently installs the stable version when there
is no TTY), so the version in use is known:

    az extension add --name documentdb --upgrade

Learn's own CLI quickstart uses this group: https://learn.microsoft.com/azure/documentdb/quickstart-cli

Commands: `check-name-availability`, `create`, `show`, `list`, `update`, `delete`, `wait`,
`restore`, `list-connection-strings`, `reset-password`; subgroups `firewall-rule`,
`identity`, `microsoft-entra-user`, `replica`.
Reference: https://learn.microsoft.com/cli/azure/documentdb/mongocluster

**Do not use `az cosmosdb`.** `az cosmosdb create --kind MongoDB` creates a
`Microsoft.DocumentDB/databaseAccounts` (request-unit) account, not a cluster.
Do not emit `az cosmosdb mongocluster` either: it is an older, still-Preview group in the
separate `cosmosdb-preview` extension (not deprecated, but superseded) with a different flag
set, an older API version and fewer commands, not an alias; never mix its flags with
`az documentdb mongocluster`. Both groups manage the same `Microsoft.DocumentDB/mongoClusters`
resource, so a cluster created with the old group is managed with the new one. If extensions cannot be installed,
fall back to `az resource ... --resource-type Microsoft.DocumentDB/mongoClusters
--api-version 2025-09-01` (Step 6b fallback), never to `az cosmosdb`.
```

**c. New section after the CLI group section, still before Step 0 — "IaC authoring only (no deployment)":**

- Skip the Step 0 preflight. Writing files needs no `az login`.
- Copy `examples/azure-deployment/main.bicep` and `main.parameters.sample.json` into the project's `infra/` folder, or generate them from `references/bicep-cluster-template.md` (use `references/terraform-cluster-template.md` if the project already uses Terraform). Never commit a password; keep `adminPassword` a secure parameter.
- In the project README, state that the sample targets `Microsoft.DocumentDB/mongoClusters` (vCore compute tiers, not request units) and must not use `databaseAccounts` or `az cosmosdb` templates.
- Show how to get the connection string after an optional deploy with `az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <rg>` (from the `documentdb` CLI extension) without echoing it, and point the app at it through an environment variable.
- If the agent is already signed in and a resource group exists, it may validate the file with `az deployment group what-if`; this creates nothing.
- Do not run `az deployment group create`. Say that deploying is optional and costs money.

**d. Step 0: add check 7** (and change "implement checks 1–4" to say the scripts do not run check 7):

```bash
# 7. Tooling for the path chosen in Step 5. All optional; skip if the run forbids provisioning.
#    documentdb extension (Step 6b/7/8/9):
az extension show --name documentdb --query version -o tsv 2>/dev/null \
  || az extension add --name documentdb --upgrade
#    Bicep (Step 6a): az installs and manages its own Bicep CLI, NOT on PATH.
az bicep version || { az bicep install && az bicep version; }
#    Terraform (Step 6c only):
terraform -version
# → If missing: https://developer.hashicorp.com/terraform/install
#    azd (Step 6d only):
azd version
# → If missing: https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd
```

Follow with: "Do not report `bicep` as missing because `which bicep` fails; `az bicep version` is the check. When policy forbids creating resources, use **IaC authoring only (no deployment)** above instead of this preflight: still generate the IaC file, and validate it with `az deployment group what-if` only if you are signed in and a resource group exists."

**e. Step 5 table:** change the existing **Azure CLI one-shot** row (Step 6b) to "Azure CLI via `az documentdb mongocluster`: prototype, local dev, samples, CI, runs where no extra tooling may be installed; needs only `az` + `documentdb` extension". Mark Bicep "(recommended for repos; `az bicep version` must pass)" and Terraform "(requires `terraform -version`)". Add a row pointing to "IaC authoring only (no deployment)" for runs that must not create resources.

**f. Step 6b:** make the extension the primary one-shot. Keep the existing `az resource create` block under "If you cannot install extensions".

```bash
az documentdb mongocluster create \
  --resource-group <rg> --name <cluster> --location <region> \
  --admin-user <admin> --admin-password "$DOCDB_ADMIN_PASSWORD" \
  --tier M10 --storage-size 32 --shard-count 1 \
  --high-availability Disabled --public-network-access Enabled \
  --server-version 8.0 --no-wait
# --server-version is optional (the service defaults to the latest version, 8.0 today);
# pass it explicitly, as Learn's quickstart-cli and the kit's templates (serverVersion '8.0') do.
az documentdb mongocluster wait --resource-group <rg> --name <cluster> --created

# "Allow Azure services" = 0.0.0.0 for both ends
az documentdb mongocluster firewall-rule create \
  --cluster-name <cluster> --resource-group <rg> \
  --name AllowAllAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

**g. Step 6d (new, optional) — deploy with azd:** `azure.yaml` + `infra/main.bicep` (reuse `references/bicep-cluster-template.md`) + `infra/main.parameters.json`; state that one `azd up` covers infra and app with per-environment `.azure/<env>/.env` and that azd carries its own Bicep CLI; set the admin password with `azd env set` from Key Vault and expose the cluster host as a Bicep output the app reads from `azd env get-values`; never write a password or connection string into `azure.yaml` or source. If `azd version` fails, use 6a/6b; nothing in a sample should require azd.

**h. Step 7:** replace `az resource list` with
`az documentdb mongocluster show -g <rg> -n <cluster> --query "{name:name, state:properties.provisioningState, tier:properties.compute.tier}"` and `az documentdb mongocluster list -g <rg> -o table`.

**i. Step 8:** CLI first, portal second: `az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <rg>` (takes `--cluster-name`, no `-n`); do not echo the result into logs, pass it to the app through an environment variable. Keep the portal route as the second option. Keep the connection-string shape with `retrywrites=false`, and replace the existing rationale sentence (which says the setting avoids connection errors; that is not established) with the canonical one-liner from `findings/phase4/DECISIONS.md`: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." The same wording is being applied to the other kit files that still show `retryWrites: true` in the K01 PR; this PR touches only the azure-deployment sentence.

**j. Step 9:** use `az documentdb mongocluster firewall-rule create` instead of `az resource create ... mongoClusters/firewallRules`.

### 2. `skills/storage/storage-premium-ssdv2-limitations.md` (lines 27–34)

Replace the `mongo-cluster` block (and its stale "set storage.type in the restore template" comment) with:

```azurecli
az documentdb mongocluster restore \
  --resource-group "<rg>" --cluster-name "<new-v2-cluster>" --location "<region>" \
  --source-cluster "<existing-v1-cluster>" --restore-time "2026-04-29T10:00:00Z" \
  --admin-user "<admin>" --admin-password "$DOCUMENTDB_ADMIN_PASSWORD" \
  --storage-type PremiumSSDv2
```

Filing group K01 also fixes this typo. Whichever PR merges second should drop its copy.

### 3. `AGENTS.md`

`documentdb-azure-deployment` row (line 78): add "CLI group is `az documentdb mongocluster` (`documentdb` extension), not `az cosmosdb`."

### 4. `docs/SKILLS.md`

`azure-deployment/` row (line 40): same one-line pointer as `AGENTS.md`.

### 5. `skills/mcp-setup/SKILL.md`

Step 2 ("Pick the connection target"), under "**Azure DocumentDB connection string:**", which today gives only the portal route: add the `az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <rg>` one-liner, and keep the portal route as the fallback. (The member draft said Step 1 and an `az resource show` fallback; Step 1 is "Confirm prerequisites" and this file has no `az resource show` command.)

### 6. `examples/azure-deployment/README.md`

"After deployment": add the same `list-connection-strings` one-liner before the existing `az resource show ... --query "properties.connectionString"` block, and keep that block as the fallback.

Prerequisites (line 29): change "Azure CLI 2.60 or later" to "Azure CLI 2.75.0 or later (the minimum for the `documentdb` extension; Bicep deploys alone need 2.20.0)". The extension's `azext.minCliCoreVersion` is 2.75.0 and the Learn reference note says the same.

### 7. Skills with `mongoClusters` Bicep blocks

`storage-choose-premium-ssdv2.md`, `storage-disk-hydration-sequencing.md`, `ha-enable-for-production.md`, `ha-cross-region-replica.md`, `security-private-endpoint.md`, `security-cmk-encryption.md`, `storage-tier-iops-caps.md`, `monitoring-metrics-alerts.md`: add "Prerequisites: see azure-deployment Step 0, check 7."

**Not changed:** `examples/azure-deployment/deploy.sh`/`.ps1` (they use Bicep) and the `references/` templates. Some findings asked to "document both aliases"; this PR does not, because naming one group is the point.

**Follow-ups outside this repo:** a "superseded by `az documentdb mongocluster`" note and cross-link in the `az cosmosdb mongocluster` help text (which generates its Learn reference page) belongs in Azure/azure-cli-extensions (filing X01; the group is not deprecated, so the note should not say so); the `az documentdb mongocluster` Learn reference should say which extension version it documents, since it shows Preview while the default install is stable 1.0.0; the Azure CLI extensions overview should state that dynamic install does not prompt without a TTY and skips preview versions by default; and a "Which CLI group" callout belongs on the Learn CLI quickstart (quickstart-cli). The companion change to the experiment's build instructions (asking for IaC) belongs to the experiment harness, which is owned by a colleague; coordinate with them rather than filing it directly.

## Evidence

Run folders in the experiment harness:

- `runs/03-portfolio-tracker-with-live-alerts/20261124-190220/05-audit.json`: IaC requirement not met; the builder chose not to provision (decision D009) because run policy forbids creating Azure resources.
- `runs/16-multi-touch-attribution-model/20261124-205342/05-audit.json`: no Bicep, Terraform or mongocluster files; the skill was loaded only in the readiness stage, and the build stage logged a no-provision decision.
- `runs/18-sanctions-list-screening-agent/20261124-202645/` (`05-audit.json`, `02-readiness.json`): no infra artifact; quiz answered `databaseAccounts`.
- `runs/01-fraud-detection-with-vector-similarity/20261124-185817/doc-gaps.md`: "[high] IaC example for DocumentDB".
- `runs/01-patient-record-summarizer-rag/20261124-192917/02-readiness.json`: cold answer `az cosmosdb create --kind MongoDB`, "core CLI".
- `runs/10-expense-report-auto-categorizer/20261124-191257/02-readiness.json`: grounded answer hedges between both groups.
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/02-readiness.json`: picks the legacy `az cosmosdb mongocluster`.
- `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl`: `az documentdb mongodb cluster create` before grounding.
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/02-readiness.json`: bicep/terraform/azd reported missing while `az bicep` works.

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- `az cosmosdb mongocluster` deprecated or superseded: not deprecated, a live Preview group with no `deprecate_info` and no Learn deprecation marker, superseded in practice by `az documentdb mongocluster` (every Learn DocumentDB page uses the new group; the old one pins API 2024-03-01-preview and lacks list-connection-strings, restore, replica, identity and microsoft-entra-user). Sources: https://learn.microsoft.com/en-us/cli/azure/cosmosdb/mongocluster; Azure/azure-cli-extensions src/cosmosdb-preview/azext_cosmosdb_preview/commands.py lines 437-449; https://learn.microsoft.com/en-us/azure/documentdb/quickstart-cli (DECISIONS.md, SME topic 11).
- `documentdb` extension Preview status and CLI floor: 2.75.0 is the right minimum (`azext.minCliCoreVersion` 2.75.0 on every published version; Learn reference note); the version a fresh `az extension add --name documentdb` installs (1.0.0) is a stable release (PR Azure/azure-cli-extensions#10316), while the 1.1.0bX line and the generated Learn page are Preview, so the kit must not call the group unconditionally Preview or GA. Sources: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster; src/documentdb/HISTORY.rst and azext_metadata.json; https://aka.ms/azure-cli-extension-index-v1 (DECISIONS.md, SME topic 11).
- First-use dynamic install in non-interactive shells: it does not prompt; without a TTY the CLI defaults to `yes_without_prompt`, logs that the extension will be installed first and continues (installing the stable version), and only an explicit `extension.use_dynamic_install=yes_prompt` with no TTY exits with NoTTYError, so the explicit `az extension add` step is for a known, pinned version rather than to avoid a stall. Source: Azure/azure-cli src/azure-cli-core/azure/cli/core/extension/dynamic_install.py lines 112-148 and 212-236 (DECISIONS.md, SME topic 11).
- Pinning `--server-version`: the documented values are 5.0, 6.0, 7.0 and 8.0, the service default is the latest available version (8.0 today), and every current Learn provisioning page (quickstart-cli `--server-version 8.0`, quickstart-bicep, quickstart-terraform, development-loop) sets 8.0 explicitly, as do the kit's templates, so the one-shot passes `--server-version 8.0`. Sources: https://learn.microsoft.com/en-us/azure/documentdb/faq; https://learn.microsoft.com/en-us/azure/documentdb/quickstart-cli; https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/mongoclusters; aaz _create.py lines 165-168 (DECISIONS.md, SME topic 11).

## Open questions

1. Step 8 ordering (maintainer decision): this PR makes the CLI command the main route (for agents) with the portal as fallback. Reviewers should confirm that over keeping the portal first.
2. Sample counts: the original IaC draft said 20 of 100 samples failed the IaC requirement; a recount of the audit files shows all 100 failed, and 20 is the number where the gap was raised as a kit finding. Most IaC misses were attributed to the build instructions, and the "missing bicep" reports partly come from the harness checking PATH (harness fix filed separately). These numbers should be re-measured after the experiment's build instructions and harness are fixed and before they are quoted outside the team.

## Source drafts

- 004-believes-az-cosmosdb-databaseaccounts-ru-account-path-is-the.md (lead of K02)
- 005-believes-the-cluster-commands-live-in-the-core-azure-cli-wit.md
- 007-believes-the-subgroup-is-spelled-mongodb-cluster-mongo-clust.md
- 061-azure-deployment-skill-assumes-bicep-terraform-azd-without-s.md
- 115-azure-deployment-skill-ships-no-minimal-bicep-terraform-temp.md (lead of K34)

## Merged from

- K34 — azure-deployment skill: add an author-IaC-only (no deploy) path (issue, ready, P1, 100 samples)
- K02 — azure-deployment skill: name az documentdb mongocluster (documentdb extension) as the CLI group, add an extension and per-path tooling preflight, and fix the mongo-cluster typo (pr, needs_sme, P1, 97 samples)
