---
id: K02
title: "azure-deployment skill: name az documentdb mongocluster (documentdb extension) as the CLI group, add an extension and per-path tooling preflight, and fix the mongo-cluster typo"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 97
member_drafts:
  - 004-believes-az-cosmosdb-databaseaccounts-ru-account-path-is-the.md
  - 005-believes-the-cluster-commands-live-in-the-core-azure-cli-wit.md
  - 007-believes-the-subgroup-is-spelled-mongodb-cluster-mongo-clust.md
  - 061-azure-deployment-skill-assumes-bicep-terraform-azd-without-s.md
open_questions: 5
---

# azure-deployment skill: name `az documentdb mongocluster` (documentdb extension) as the CLI group, add an extension and per-path tooling preflight, and fix the `mongo-cluster` typo

## What happens today

`skills/azure-deployment/SKILL.md` never names the Azure CLI command group for an Azure DocumentDB cluster (`Microsoft.DocumentDB/mongoClusters`):

- **Step 0 (preflight)** has six checks (`az version`, sign-in, subscription, `Microsoft.DocumentDB` provider, role, region). It does not check for the `documentdb` CLI extension, `az bicep`, `terraform` or `azd`, even though Step 5 offers Bicep, CLI, Terraform and portal paths.
- **Step 6b** and **Step 9** use generic `az resource create --resource-type Microsoft.DocumentDB/mongoClusters --api-version 2025-09-01`; **Step 7** verifies with `az resource list`; **Step 8** fetches the connection string from the portal only.
- The strings `az documentdb mongocluster`, `az extension add --name documentdb` and "not `az cosmosdb`" appear nowhere in the skills, `AGENTS.md`, `README.md` or `docs/SKILLS.md`.
- The only CLI-group mention in the repo is wrong: `skills/storage/storage-premium-ssdv2-limitations.md:28` reads `az documentdb mongo-cluster restore`, which the CLI rejects (the group is the single token `mongocluster`). Its trailing comment ("set storage.type in the restore template") is also stale: `restore` takes `--storage-type` directly.

Because the service was formerly "Azure Cosmos DB for MongoDB vCore", models strongly assume the cluster lives under `az cosmosdb` in the core CLI. `az cosmosdb create --kind MongoDB` creates a request-unit `Microsoft.DocumentDB/databaseAccounts` account, a different resource with a different capacity model (vCore tiers vs request units), flags and connection string. There is also an older `az cosmosdb mongocluster` group in the separate `cosmosdb-preview` extension, with different flags (`--administrator-login`, `--shard-node-tier`, ...) and no `list-connection-strings`, `restore`, `replica` or `microsoft-entra-user`. Mixing the two groups' flags produces commands that fail. The kit is the only thing in an agent's loop that could override this prior, and today it does not.

## Why it matters

We ran an agent-readiness experiment: 100 Azure DocumentDB sample prompts, gpt-5-mini with this kit loaded plus the DocumentDB, Azure and Learn MCP servers. All counts below come from that single run and may shift on a re-run.

- **97 of 100 samples** (102 findings) gave a wrong, partly wrong or outdated cold answer to "Which Azure CLI command group creates and manages a cluster?" before grounding. Most answered `az cosmosdb create ... --kind MongoDB` and said it is core CLI (85 samples in the lead draft's set). A few answered with Cosmos DB for NoSQL flags. Two samples were tagged for hyphenating or splitting the group (`az documentdb mongodb cluster create`, `az cosmosdb mongodb cluster`), and the same split shows up in other cold answers. These are model priors, but they are exactly what the skill should correct.
- Even after grounding with the kit loaded, grounded answers still hedged between `az documentdb mongocluster` and `az cosmosdb mongocluster`: the 11 samples tagged for this did, and so did others such as 10-expense-report-auto-categorizer, so 11 is a floor, not a total. One picked the legacy group and asked for it to be added to this skill. One proposed a README step `az extension install documentdb`, which is not a real subcommand.
- In 14 of the 97 samples (33 findings) the agent reported `bicep`, `terraform` and/or `azd` as missing. Bicep was a false negative: `az bicep version` worked on that machine, but the agent looked for `bicep` on PATH. No sample shipped infrastructure-as-code.

In this experiment the builder was handed an existing cluster, so no sample actually ran `az cosmosdb`. Any user who asks this skill to provision a cluster would hit the same prior, though: Step 0 passes on a stock install, and the agent would create the wrong resource type.

## Proposed change

### 1. `skills/azure-deployment/SKILL.md`

**a. New section after the intro, before Step 0:**

```markdown
## CLI command group (read this first)

Azure DocumentDB clusters (`Microsoft.DocumentDB/mongoClusters`) are managed by one group:

    az documentdb mongocluster ...

It is a single token (not `mongo-cluster`, not `mongodb cluster`) and ships in the
**`documentdb` extension** (preview; Azure CLI >= 2.75.0), not in core `az`. Install it
explicitly; first-use auto-install can prompt and stall a non-interactive shell:

    az extension add --name documentdb --upgrade

Commands: `check-name-availability`, `create`, `show`, `list`, `update`, `delete`, `wait`,
`restore`, `list-connection-strings`, `reset-password`; subgroups `firewall-rule`,
`identity`, `microsoft-entra-user`, `replica`.
Reference: https://learn.microsoft.com/cli/azure/documentdb/mongocluster

**Do not use `az cosmosdb`.** `az cosmosdb create --kind MongoDB` creates a
`Microsoft.DocumentDB/databaseAccounts` (request-unit) account, not a cluster.
Do not emit `az cosmosdb mongocluster` either: it is an older group in the separate
`cosmosdb-preview` extension with a different flag set and fewer commands, not an alias;
never mix its flags with `az documentdb mongocluster`. If extensions cannot be installed,
fall back to `az resource ... --resource-type Microsoft.DocumentDB/mongoClusters
--api-version 2025-09-01` (Step 6b fallback), never to `az cosmosdb`.
```

**b. Step 0: add check 7** (and change "implement checks 1–4" to say the scripts do not run check 7):

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

Follow with: "Do not report `bicep` as missing because `which bicep` fails; `az bicep version` is the check. When policy forbids creating resources, skip checks 5–7, still generate the IaC file, and validate it with `az deployment group what-if` if a resource group exists."

**c. Step 5 table:** change the existing **Azure CLI one-shot** row (Step 6b) to "Azure CLI via `az documentdb mongocluster`: prototype, local dev, samples, CI, runs where no extra tooling may be installed; needs only `az` + `documentdb` extension". Mark Bicep "(recommended for repos; `az bicep version` must pass)" and Terraform "(requires `terraform -version`)".

**d. Step 6b:** make the extension the primary one-shot. Keep the existing `az resource create` block under "If you cannot install extensions".

```bash
az documentdb mongocluster create \
  --resource-group <rg> --name <cluster> --location <region> \
  --admin-user <admin> --admin-password "$DOCDB_ADMIN_PASSWORD" \
  --tier M10 --storage-size 32 --shard-count 1 \
  --high-availability Disabled --public-network-access Enabled --no-wait
# --server-version is optional and defaults to the latest version
az documentdb mongocluster wait --resource-group <rg> --name <cluster> --created

# "Allow Azure services" = 0.0.0.0 for both ends
az documentdb mongocluster firewall-rule create \
  --cluster-name <cluster> --resource-group <rg> \
  --name AllowAllAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

**e. Step 6d (new, optional) — deploy with azd:** `azure.yaml` + `infra/main.bicep` (reuse `references/bicep-cluster-template.md`) + `infra/main.parameters.json`; state that one `azd up` covers infra and app with per-environment `.azure/<env>/.env` and that azd carries its own Bicep CLI; set the admin password with `azd env set` from Key Vault and expose the cluster host as a Bicep output the app reads from `azd env get-values`; never write a password or connection string into `azure.yaml` or source. If `azd version` fails, use 6a/6b; nothing in a sample should require azd.

**f. Step 7:** replace `az resource list` with
`az documentdb mongocluster show -g <rg> -n <cluster> --query "{name:name, state:properties.provisioningState, tier:properties.compute.tier}"` and `az documentdb mongocluster list -g <rg> -o table`.

**g. Step 8:** CLI first, portal second: `az documentdb mongocluster list-connection-strings --cluster-name <cluster> -g <rg>` (takes `--cluster-name`, no `-n`). Leave the existing connection-string shape and its `retrywrites=false` note unchanged (see Open questions).

**h. Step 9:** use `az documentdb mongocluster firewall-rule create` instead of `az resource create ... mongoClusters/firewallRules`.

### 2. `skills/storage/storage-premium-ssdv2-limitations.md` (lines 27–34)

Replace the `mongo-cluster` block with:

```azurecli
az documentdb mongocluster restore \
  --resource-group "<rg>" --cluster-name "<new-v2-cluster>" --location "<region>" \
  --source-cluster "<existing-v1-cluster>" --restore-time "2026-04-29T10:00:00Z" \
  --admin-user "<admin>" --admin-password "$DOCUMENTDB_ADMIN_PASSWORD" \
  --storage-type PremiumSSDv2
```

Filing group K01 also fixes this typo. Whichever PR merges second should drop its copy.

### 3. One-line pointers elsewhere

- `AGENTS.md` and `docs/SKILLS.md`, `documentdb-azure-deployment` row: "CLI group is `az documentdb mongocluster` (`documentdb` extension), not `az cosmosdb`."
- `skills/mcp-setup/SKILL.md` Step 1 and `examples/azure-deployment/README.md` "After deployment": add the `list-connection-strings` one-liner, and keep `az resource show ... properties.connectionString` as a fallback.
- Skills with `mongoClusters` Bicep blocks (`storage-choose-premium-ssdv2.md`, `storage-disk-hydration-sequencing.md`, `ha-enable-for-production.md`, `ha-cross-region-replica.md`, `security-private-endpoint.md`, `security-cmk-encryption.md`, `storage-tier-iops-caps.md`, `monitoring-metrics-alerts.md`): "Prerequisites: see azure-deployment Step 0, check 7."

**Not changed:** `examples/azure-deployment/deploy.sh`/`.ps1` (they use Bicep) and the `references/` templates. Some findings asked to "document both aliases"; this PR does not, because naming one group is the point.

**Follow-ups outside this repo:** a cross-link or deprecation note on `az cosmosdb mongocluster` belongs in Azure/azure-cli-extensions help text, and a "Which CLI group" callout belongs on the Learn CLI quickstart.

## Evidence

Run folders in the experiment harness:

- `runs/01-patient-record-summarizer-rag/20261124-192917/02-readiness.json` (cold answer `az cosmosdb create --kind MongoDB`, "core CLI")
- `runs/10-expense-report-auto-categorizer/20261124-191257/02-readiness.json` (grounded answer hedges between both groups)
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/02-readiness.json` (picks the legacy `az cosmosdb mongocluster`)
- `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl` (`az documentdb mongodb cluster create` before grounding)
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/02-readiness.json` (bicep/terraform/azd reported missing while `az bicep` works)

## Open questions

1. [needs SME confirmation] Is `az cosmosdb mongocluster` (cosmosdb-preview) deprecated or only superseded? Learn does not mark it deprecated. This PR calls it "older; do not use" and makes no deprecation claim.
2. [needs SME confirmation] Is the `documentdb` extension still preview, and is 2.75.0 the right minimum CLI version? The callout says "preview".
3. [needs SME confirmation] Does first-use dynamic install prompt in non-interactive shells by default? The explicit `az extension add` step rests on this.
4. [needs SME confirmation] Should the kit pin a `--server-version`? The member drafts disagree: one used `8.0`, another removed it because Learn lists no accepted values and the flag defaults to latest. This PR omits it.
5. [needs SME confirmation] retryWrites: Step 8 keeps the existing `retrywrites=false` note. Other drafts in this effort disagree on why. One position is that retryable writes are unsupported and must be disabled. The other is that Learn does not claim they are unsupported. This PR does not change that text. Engineering should settle it in the K01 PR.

The "missing bicep" reports partly come from the harness checking PATH. The harness fix is filed separately, so these counts may drop on a re-run.

## Source drafts

- 004-believes-az-cosmosdb-databaseaccounts-ru-account-path-is-the.md (lead)
- 005-believes-the-cluster-commands-live-in-the-core-azure-cli-wit.md
- 007-believes-the-subgroup-is-spelled-mongodb-cluster-mongo-clust.md
- 061-azure-deployment-skill-assumes-bicep-terraform-azd-without-s.md
