---
title: "documentdb-azure-deployment: preflight never checks for the `documentdb` CLI extension, and the skill never names the `az documentdb mongocluster` group"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 11
findings: 11
bucket: confusion-Q02
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# documentdb-azure-deployment: check for the `documentdb` CLI extension in preflight and name the `az documentdb mongocluster` group

## What happens today

`skills/azure-deployment/SKILL.md` (frontmatter name `documentdb-azure-deployment`) runs a six-step preflight loop in Step 0: CLI installed, signed in, subscription, `Microsoft.DocumentDB` provider registered, RBAC, region support. It never checks whether the `documentdb` CLI extension is installed. The rest of the skill never uses the extension either: Step 6b deploys with `az resource create`, Step 7 verifies with `az resource list`, Step 8 sends the user to the portal for the connection string. The strings `az documentdb mongocluster`, `az extension add`, `documentdb extension` and `az cosmosdb mongocluster` appear nowhere in the 17 skills (`grep -rn "az extension\|az documentdb\|az cosmosdb" skills/` returns only one hit, and that hit is a misspelling: `skills/storage/storage-premium-ssdv2-limitations.md:28` writes `az documentdb mongo-cluster restore`; the real subgroup is `mongocluster`).

Per Learn (https://learn.microsoft.com/cli/azure/documentdb/mongocluster): the `az documentdb mongocluster` group is part of the **documentdb** extension (Azure CLI 2.75.0 or higher), is in preview, and "will automatically install the first time you run an az documentdb command". That auto-install goes through `extension.use_dynamic_install`, which by default prompts, so it does not help an agent running non-interactively. A vanilla `az` has no `documentdb` group at all; `az cosmosdb mongocluster` is the older group from the cosmosdb-preview extension (Cosmos DB for MongoDB vCore era), still published as preview but not the current group, and `az cosmosdb create` provisions an RU-based `Microsoft.DocumentDB/databaseAccounts` resource, not a `mongoClusters` cluster.

## Why it matters

Across the 100-sample gpt-5-mini run (106 run folders, 120 Q02 cold answers), **114 cold answers claimed the cluster commands live in the core CLI with no extension**, almost always as `az cosmosdb create`; only 3 mentioned `az documentdb` at all. So the model prior is wrong nearly every time and the Agent Kit is the only thing in the loop that could correct it. It does not, because it never mentions the extension.

11 samples were flagged in this bucket (03-substitute-product-finder, 04-natural-language-product-search, 04-regulatory-reporting-orchestration, 07-multi-currency-ledger, 08-dynamic-segmentation-engine, 18-sanctions-list-screening-agent, 19-care-coordination-multi-agent, 19-cross-sell-recommendation-beanie, 20-identity-resolution-multi-agent, 20-provider-directory-semantic-search, 20-store-locator-with-geospatial-search). In all 11, even after the readiness stage grounded against Learn with the kit loaded, it still hedged between `az documentdb mongocluster` and `az cosmosdb mongocluster` and could not say which extension provides them. The test machine had both `cosmosdb-preview 1.7.0` and `documentdb` installed, so both groups resolved and nothing in the kit told the agent which one is canonical.

What the agent did wrong because of it: these samples were told to use a provided cluster, so no generated `app/` tree emitted an `az` cluster command (checked: 0 hits for `az cosmosdb`, `az documentdb`, `az extension add` under `runs/*/*/app`). The damage showed up in the guidance the agents wrote instead: 08-dynamic-segmentation-engine's doc-gaps proposes a README step `az extension install documentdb` (not a real subcommand); 07-multi-currency-ledger's audit recommends "az documentdb CLI" with no extension requirement; 19-cross-sell-recommendation-beanie's grounded answer picks the legacy `az cosmosdb mongocluster` form and asks for it to be added to this skill. When the deployment skill is used for its actual purpose (a user asking to provision a cluster), Step 0 passes on a vanilla install, and an agent that falls back to its prior will run `az cosmosdb create` and build the wrong resource type.

## Proposed change

### 1. `skills/azure-deployment/SKILL.md`, Step 0: add check 1b

Insert after check 1 (`az version`):

```bash
# 1b. documentdb CLI extension present? (the `az documentdb mongocluster` group is NOT in core az;
#     it ships in the 'documentdb' extension, Azure CLI >= 2.75.0, currently preview)
az extension show --name documentdb --query version -o tsv 2>/dev/null \
  || az extension add --name documentdb --upgrade
# → Install explicitly. First-use auto-install prompts interactively and fails in non-interactive shells.
#   Only the `az documentdb ...` commands below need this; Bicep (6a), `az resource` and Terraform (6c) do not.
```

Change the sentence after the loop from "implement checks 1–4" to "implement checks 1–4 (not 1b: the Bicep path does not need the extension)".

### 2. `skills/azure-deployment/SKILL.md`: add a "CLI naming" callout (after the preflight, before Step 0.5)

> **CLI naming.** The cluster command group is `az documentdb mongocluster` (documentdb extension). `az cosmosdb mongocluster` is the older group from the `cosmosdb-preview` extension (Azure Cosmos DB for MongoDB vCore era); it is still published on Learn as preview, with different parameter names (`--administrator-login`, `--shard-node-tier`, `--shard-node-ha`, `-c` for the cluster name) and a smaller command set (no `list-connection-strings`, `restore`, `replica` or `microsoft-entra-user`). Do not generate it in new scripts. `az cosmosdb create` creates an RU-based `Microsoft.DocumentDB/databaseAccounts` resource, not a `Microsoft.DocumentDB/mongoClusters` cluster. Reference: https://learn.microsoft.com/cli/azure/documentdb/mongocluster

### 3. Step 6b: offer the extension command as the one-shot, keep `az resource create` as the no-extension fallback

```bash
az documentdb mongocluster create \
  --resource-group rg-docdb-dev --name docdb-dev-001 --location eastus2 \
  --admin-user clusteradmin --admin-password "$DOCDB_ADMIN_PASSWORD" \
  --tier M10 --storage-size 32 --shard-count 1 \
  --high-availability Disabled
# --server-version is optional and defaults to the latest available version
```

(Parameter names verified against the Learn reference: required `--admin-user/-u`, `--admin-password/-p`, `--cluster-name/--name/-n`, `--resource-group`, `--tier`, `--storage-size`, `--shard-count`, `--high-availability {Disabled, SameZone, ZoneRedundantPreferred}`, `--storage-type {PremiumSSD, PremiumSSDv2}`.) Keep the existing `az resource create` block under a heading such as "If you cannot install extensions".

### 4. Step 7 and Step 8: use the extension's commands

Step 7, replace `az resource list ...` with:

```bash
az documentdb mongocluster show -g "<resource-group-name>" -n "<cluster-name>" \
  --query "{name:name, state:properties.provisioningState, tier:properties.compute.tier}" -o json
```

Step 8, add before the portal instructions:

```bash
az documentdb mongocluster list-connection-strings --cluster-name "<cluster-name>" -g "<resource-group-name>" -o json
```

(Note `list-connection-strings` takes `--cluster-name`, not `-n`.) Keep the existing connection-string shape and the `retrywrites=false` note.

### 5. `skills/storage/storage-premium-ssdv2-limitations.md` line 28

`az documentdb mongo-cluster restore` → `az documentdb mongocluster restore`.

No change to `examples/azure-deployment/deploy.sh` / `deploy.ps1`: they deploy via Bicep and do not need the extension.

## Evidence (run folders under azure-documentdb-agent-readiness/runs/)

- `runs/04-natural-language-product-search/20261124-183232/02-readiness.json` — confusions[Q02]: cold answer says `az cosmosdb` is "part of the core az CLI, not a separate extension"; grounded answer still hedges between both groups.
- `runs/20-provider-directory-semantic-search/20261124-200008/02-readiness.json` — confusions[Q02]: same core-CLI claim; improvements explicitly ask for an "az module/extension check" snippet.
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/02-readiness.json` — confusions[Q02]: grounded answer selects the legacy `az cosmosdb mongocluster` group and proposes adding it to `documentdb-azure-deployment`; inventory lists `cosmosdb-preview 1.7.0` installed.
- `runs/08-dynamic-segmentation-engine/20261124-204222/doc-gaps.md` — line 17 proposes `az extension install documentdb` (invalid subcommand) in a README.
- `runs/07-multi-currency-ledger/20261124-190814/05-audit.md` — line 96 recommends "az documentdb CLI" for IaC with no extension requirement.

## Verification

### 1. Already covered? confirmed (not covered)

Grepped the Agent Kit clone (`skills/`, `knowledge-base/`, `examples/`) for `az extension`, `az documentdb`, `az cosmosdb`, `mongocluster` and `mongo-cluster`. The only CLI hit is the misspelling `skills/storage/storage-premium-ssdv2-limitations.md:28: az documentdb mongo-cluster restore \`; every other `mongocluster` hit is a hostname in a connection string or a `Microsoft.DocumentDB/mongoClusters` template link. `skills/azure-deployment/SKILL.md` Step 0 has checks 1 to 6 (`az version`, login, subscription, provider registration, role, region) and no extension check. Line 51 says the example scripts "implement checks 1–4 automatically". Step 6b (line 224) uses `az resource create`, and Step 7 (line 271) uses `az resource list`. The documentdb-mcp clone has no `az documentdb` or extension guidance, which is expected because it is a data-plane server. The fix belongs in the kit. The Learn CLI reference does document the extension, but agents that load the deployment skill don't look there.

### 2. Premise true? confirmed (small corrections applied)

The https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster note says: "part of the **documentdb** extension for the Azure CLI (version 2.75.0 or higher)", that it "will automatically install the first time you run" a command, and that it is in preview. The page lists `create`, `show`, `list`, `list-connection-strings`, `restore`, `firewall-rule`, `replica` and `microsoft-entra-user`. The `create` signature requires `--admin-password/-p`, `--admin-user/-u`, `--cluster-name/--name/-n`, `--high-availability {Disabled, SameZone, ZoneRedundantPreferred}`, `--resource-group`, `--shard-count`, `--storage-size` and `--tier`. Optional parameters include `--storage-type {PremiumSSD, PremiumSSDv2}` and `--server-version`, which "Defaults to the latest available version". `list-connection-strings` takes `--cluster-name` with no `-n` alias. These match the draft.

Corrections applied:
- https://learn.microsoft.com/en-us/cli/azure/cosmosdb/mongocluster is still published. It is "part of the **cosmosdb-preview** extension", in preview, has a smaller command set and uses different parameter names (`--administrator-login`, `--shard-node-tier`, `--shard-node-ha`, `-c`). It is not marked deprecated, so the wording changed from "pre-rename spelling" to "older group, still published as preview, not the current one".
- The draft hard-coded `--server-version 8.0`. Learn gives no accepted-value list and says the flag defaults to latest, so the value was removed and the flag is now noted as optional.
- `--resource-group` was added to the list of required parameters.

The remaining claims match the facts brief and are consistent with Learn: the resource type is `Microsoft.DocumentDB/mongoClusters`, `az cosmosdb create` makes RU-based `databaseAccounts`, and the CLI group is `az documentdb mongocluster`.

### 3. Maintainer skeptic: confirmed

The draft names exact files and steps (`skills/azure-deployment/SKILL.md` Step 0, Steps 6b, 7 and 8, and `skills/storage/storage-premium-ssdv2-limitations.md:28`). It gives concrete commands checked against the CLI reference and fixes a real typo in the kit. The change is specific to Azure DocumentDB, and it keeps the no-extension Bicep and `az resource` paths. I would accept it as a PR.

## Finding ids

- F0493
- F0626
- F0658
- F1128
- F1195
- F3107
- F3141
- F3223
- F3357
- F3456
- F3495
