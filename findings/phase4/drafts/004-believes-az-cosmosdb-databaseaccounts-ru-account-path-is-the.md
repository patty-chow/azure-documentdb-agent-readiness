---
title: "azure-deployment skill: name `az documentdb mongocluster` (documentdb extension) as the CLI command group; say explicitly \"not az cosmosdb\""
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 85
findings: 89
bucket: confusion-Q02
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# azure-deployment: name `az documentdb mongocluster` as the CLI command group and say "not `az cosmosdb`"

## What happens today

`skills/azure-deployment/SKILL.md` (335 lines) never names the Azure CLI command group for `Microsoft.DocumentDB/mongoClusters`. Its only CLI path is the generic `az resource create --resource-type "Microsoft.DocumentDB/mongoClusters" --api-version 2025-09-01` (Step 6b, Step 9), verification is `az resource list` (Step 7), and connection-string retrieval is portal-only (Step 8). The strings `az documentdb mongocluster`, `az extension add --name documentdb` and "not `az cosmosdb`" do not appear anywhere in the skill, in AGENTS.md, README.md or docs/SKILLS.md. The only mention of the group in the whole repo is a misspelled `az documentdb mongo-cluster restore` in `skills/storage/storage-premium-ssdv2-limitations.md`.

Because the service used to be "Azure Cosmos DB for MongoDB vCore", models carry a strong prior that vCore clusters live under `az cosmosdb`. The kit is where that prior should be overridden, and currently it is not.

## Why it matters

In an agent-readiness run over 100 Azure DocumentDB sample prompts (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), the cold-quiz question "Which Azure CLI command group creates and manages a cluster? Is it in the core CLI or an extension?" was answered wrongly in **89 readiness runs covering 85 of the 100 samples**:

- 54 wrong, 29 partly wrong, 2 outdated: the model answered `az cosmosdb create --name <account> --resource-group <rg> --kind MongoDB` (or other `az cosmosdb` subcommands) and said it is in the core CLI, i.e. it conflated the vCore cluster with a Cosmos DB for MongoDB RU account (`Microsoft.DocumentDB/databaseAccounts`).
- 3 runs went further and answered with Cosmos DB for NoSQL flags (`--default-consistency-level Session`).
- Even after grounding, some runs hedged: "under both `az cosmosdb mongocluster` and `az documentdb mongocluster`... may require the cosmosdb/documentdb extension" (run 10-expense-report-auto-categorizer).

What is true: a vCore cluster is a `Microsoft.DocumentDB/mongoClusters` resource managed by the `az documentdb mongocluster` command group, shipped in the `documentdb` Azure CLI extension (currently marked preview; it auto-installs on first use with CLI >= 2.75.0, or run `az extension add --name documentdb --upgrade`). `az cosmosdb` (core CLI) targets `databaseAccounts`: running `az cosmosdb create --kind MongoDB` provisions an RU account with a different capacity model, flags and connection string, and none of the cluster options (`--tier M30`, `--storage-size`, `--shard-count`, `--high-availability`) exist there. There is also an older `az cosmosdb mongocluster` group in the separate `cosmosdb-preview` extension; it targets the same resource type but with a different, older flag set (`--administrator-login`, `--shard-node-tier`, `--shard-node-disk-size-gb`, `--shard-node-ha`) and lacks `list-connection-strings`, `restore`, `replica`, `reset-password` and `microsoft-entra-user`. Mixing the two groups' flags produces commands that fail. Any deploy script, README or CI step an agent writes from the prior would create the wrong resource or fail. The Learn CLI quickstart (https://learn.microsoft.com/azure/documentdb/quickstart-cli) already uses `az documentdb mongocluster` throughout, so this is a kit gap, not a docs gap.

The audits agree: 10 of the `05-audit.json` doc_gaps call out "agents confused resource types and CLI groups (mongoClusters vs databaseAccounts / az documentdb vs az cosmosdb)". In this experiment the build stage was handed an existing cluster, so no sample actually ran `az cosmosdb`, but any sample that must provision its own cluster would.

## Proposed change

### 1. `skills/azure-deployment/SKILL.md`

Insert after the intro paragraph (before "Step 0"):

```markdown
## CLI command group (read this first)

Use **one** Azure CLI command group for Azure DocumentDB clusters:

    az documentdb mongocluster ...

It ships in the **`documentdb` extension** (preview), not in core `az`
(CLI >= 2.75.0 auto-installs it on first use):

    az extension add --name documentdb --upgrade

Common subcommands: `create`, `show`, `list`, `update`, `delete`, `wait`,
`check-name-availability`, `firewall-rule {create,list,show,update,delete}`,
`list-connection-strings`, `reset-password`, `restore`, `replica {create,list,promote}`,
`microsoft-entra-user {assign,list,show,remove}`, `identity {assign,list,show,remove}`.
Reference: https://learn.microsoft.com/cli/azure/documentdb/mongocluster

**Do not use `az cosmosdb`.** `az cosmosdb create --kind MongoDB` targets
`Microsoft.DocumentDB/databaseAccounts` (Azure Cosmos DB for MongoDB RU): a
different resource type, capacity model (request units, not M-tiers), flag set
and connection string. Do not emit `az cosmosdb mongocluster` either: it is an
older group in the separate `cosmosdb-preview` extension with a different flag
set (`--administrator-login`, `--shard-node-tier`, ...) and fewer subcommands;
it is not an interchangeable alias, so never mix its flags with
`az documentdb mongocluster`. If you cannot install extensions, fall back to
`az resource ... --resource-type Microsoft.DocumentDB/mongoClusters
--api-version 2025-09-01` (see Step 6b note), never to `az cosmosdb`.
```

Step 0 preflight: add check 7:

```bash
# 7. documentdb extension present?
az extension show --name documentdb --query version -o tsv \
  || az extension add --name documentdb --upgrade
```

Step 6b ("deploy with Azure CLI one-shot"): replace the `az resource create` cluster + firewall commands with the extension commands, keeping the generic form as a one-line fallback note:

```bash
az documentdb mongocluster create \
  --name docdb-dev-001 --resource-group rg-docdb-dev --location eastus2 \
  --admin-user clusteradmin --admin-password "$ADMIN_PASSWORD" \
  --server-version 8.0 --tier M10 --storage-size 32 --shard-count 1 \
  --high-availability Disabled --public-network-access Enabled --no-wait
az documentdb mongocluster wait --name docdb-dev-001 --resource-group rg-docdb-dev --created

# "Allow Azure services" shortcut = 0.0.0.0 for both ends
az documentdb mongocluster firewall-rule create \
  --cluster-name docdb-dev-001 --resource-group rg-docdb-dev \
  --name AllowAllAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

Step 7 (verify): `az documentdb mongocluster show --name <cluster> --resource-group <rg> --query provisioningState` and `az documentdb mongocluster list --resource-group <rg> -o table` in place of `az resource list`.

Step 8 (connection string): make CLI the primary path, portal secondary:

```bash
az documentdb mongocluster list-connection-strings \
  --cluster-name <cluster> --resource-group <rg>
```

Step 9 (developer IP rule): use `az documentdb mongocluster firewall-rule create` instead of `az resource create ... mongoClusters/firewallRules`.

### 2. `AGENTS.md` and `docs/SKILLS.md`

Append to the `documentdb-azure-deployment` row: "CLI group is `az documentdb mongocluster` (`documentdb` extension), not `az cosmosdb`."

### 3. `skills/mcp-setup/SKILL.md` (Step 1 prerequisites) and `examples/azure-deployment/README.md` ("After deployment")

Add the one-liner `az documentdb mongocluster list-connection-strings --cluster-name <cluster> --resource-group <rg>` as the way to fetch the connection string from the CLI (the example README currently uses `az resource show ... --query properties.connectionString`; keep it as a fallback).

### 4. `skills/storage/storage-premium-ssdv2-limitations.md`

Fix `az documentdb mongo-cluster restore` to `az documentdb mongocluster restore`, and replace the "In the restore template, set storage.type = 'PremiumSSDv2'" comment with the command's own `--storage-type PremiumSSDv2` flag (the restore command accepts `--storage-type`).

### Explicitly not doing

Five of the findings (F1621, F1750, F1948, F2709, F2872) asked the kit or docs to "show both forms" / "document both aliases" (`az documentdb mongocluster` and `az cosmosdb mongocluster`) or to recommend `az cosmosdb mongocluster create` as primary. `az cosmosdb mongocluster` does exist (in `cosmosdb-preview`), but it is the older group with a different flag set, not an equivalent alias; presenting both as interchangeable would reinforce the confusion this PR exists to remove, so those proposals are not adopted. The kit should name exactly one command group and mention the older one only to say not to use it.

A lower-priority Learn-docs follow-up (cross-link from `az cosmosdb` / `az cosmosdb mongocluster` reference pages to `az documentdb mongocluster`; a short "Which CLI group" callout at the top of https://learn.microsoft.com/azure/documentdb/quickstart-cli) can be filed separately; it is not needed for this PR.

## Evidence (run folders under azure-documentdb-agent-readiness/runs/)

- `01-patient-record-summarizer-rag/20261124-192917/02-readiness.json` - confusions[Q02]: cold answer `az cosmosdb create ... --kind MongoDB`, "core Azure CLI"; outcome wrong.
- `02-ai-powered-product-recommendations/20261124-181835/02-readiness.json` - confusions[Q02]: confused with Cosmos DB for NoSQL (`--default-consistency-level Session`).
- `10-expense-report-auto-categorizer/20261124-191257/02-readiness.json` - confusions[Q02]: grounded answer still hedges between `az documentdb mongocluster` and `az cosmosdb mongocluster`.
- `03-portfolio-tracker-with-live-alerts/20261124-190220/05-audit.json` - doc_gaps: "future agents may pick the wrong resource type or CLI group (az cosmosdb vs az documentdb)".
- `01-anti-money-laundering-pattern-detector/20261124-200112/02-readiness.json` - confusions[Q02], partly wrong.

Totals: 89 Q02 confusion findings, 85 distinct samples out of 100; 57 rated high priority by the readiness stage.

## Verification

### 1. Already covered? - confirmed (not covered in the target)

- Grep of the kit clone (commit 4f41c15, 2026-11-23) for `az documentdb`, `az cosmosdb`, `extension add`, `mongo-cluster` across skills/, knowledge-base/, AGENTS.md, README.md, docs/: the only hit is `skills/storage/storage-premium-ssdv2-limitations.md:28` "az documentdb mongo-cluster restore" (misspelled). No skill names the command group or the extension.
- `skills/azure-deployment/SKILL.md`: Step 0 has six preflight checks, none for the extension; Step 6b uses `az resource create --resource-type "Microsoft.DocumentDB/mongoClusters" --api-version 2025-09-01`; Step 7 uses `az resource list`; Step 8 says "From the portal: cluster -> Connection strings"; Step 9 uses `az resource create`.
- `AGENTS.md:78` and `docs/SKILLS.md:40` describe the skill but do not name a CLI group. `examples/azure-deployment/README.md:89-94` uses `az resource show ... --query "properties.connectionString"`.
- microsoft/documentdb-mcp clone: no `az documentdb`/`az cosmosdb`/`mongocluster` CLI references (only host names in connection-profile examples); not the right place for this anyway.
- Learn already covers it: https://learn.microsoft.com/azure/documentdb/quickstart-cli runs `az extension add --name documentdb --upgrade` and uses `az documentdb mongocluster create/wait/firewall-rule create/show/list/list-connection-strings/update/reset-password/delete`. That confirms the draft's "kit gap, not docs gap" framing.

### 2. Premise true? - confirmed (with precision edits applied)

- https://learn.microsoft.com/cli/azure/documentdb/mongocluster: "This reference is part of the documentdb extension for the Azure CLI (version 2.75.0 or higher). The extension will automatically install the first time you run an az documentdb mongocluster command." Group is marked preview. Subcommands listed match the draft (check-name-availability, create, delete, firewall-rule, identity, list, list-connection-strings, microsoft-entra-user, replica create/list/promote, reset-password, restore, show, update, wait). `create` requires --admin-user, --admin-password, --name, --high-availability {Disabled, SameZone, ZoneRedundantPreferred}, --resource-group, --shard-count, --storage-size, --tier; optional --location, --server-version, --public-network-access, --no-wait. `list-connection-strings` takes --cluster-name and -g.
- https://learn.microsoft.com/cli/azure/documentdb/mongocluster/firewall-rule: `firewall-rule create --cluster-name --name --resource-group [--start-ip-address] [--end-ip-address]`; `wait --created` exists. The draft's Step 6b/9 commands match.
- https://learn.microsoft.com/cli/azure/cosmosdb/mongocluster: `az cosmosdb mongocluster` exists in the cosmosdb-preview extension, with flags --administrator-login, --administrator-login-password, --shard-node-tier, --shard-node-disk-size-gb, --shard-node-ha, --shard-node-count, and only create/delete/list/show/update/firewall rule. Correction applied: the draft said `az documentdb mongocluster` is "the only" group and treated `az cosmosdb mongocluster` purely as a wrong belief; the body now says it is a real older preview group with an incompatible flag set that the kit should not emit, rather than claiming it does not exist. Also noted that `az documentdb` is preview.
- `az cosmosdb create --kind MongoDB` creates a `databaseAccounts` (RU) resource: consistent with the TRUE facts in the brief (resource type Microsoft.DocumentDB/mongoClusters, capacity in M-tiers not RUs).
- Restore reference lists `--storage-type`, so the storage-file fix now uses that flag instead of a "restore template" comment.

### 3. Maintainer skeptic - confirmed

Names exact files and steps (azure-deployment SKILL.md Steps 0/6b/7/8/9, AGENTS.md row, docs/SKILLS.md row, mcp-setup Step 1, examples README, storage typo), gives drop-in text and commands that match the published CLI reference, and is specific to Azure DocumentDB. It belongs in Azure/documentdb-agent-kit (the skill is the place the agent's prior should be overridden). Small, reviewable PR; the only edit needed was the `az cosmosdb mongocluster` wording, now applied.

## Finding ids

- F0001
- F0037
- F0069
- F0105
- F0145
- F0176
- F0212
- F0255
- F0284
- F0312
- F0346
- F0386
- F0418
- F0453
- F0554
- F0594
- F0693
- F0723
- F0761
- F0790
- F0821
- F0885
- F0914
- F0940
- F0997
- F1037
- F1071
- F1099
- F1157
- F1221
- F1256
- F1295
- F1335
- F1366
- F1398
- F1431
- F1484
- F1519
- F1554
- F1587
- F1621
- F1653
- F1680
- F1714
- F1750
- F1786
- F1823
- F1857
- F1887
- F1919
- F1948
- F1979
- F2014
- F2049
- F2080
- F2118
- F2150
- F2182
- F2240
- F2285
- F2322
- F2355
- F2385
- F2423
- F2456
- F2483
- F2514
- F2548
- F2587
- F2617
- F2645
- F2680
- F2709
- F2743
- F2775
- F2802
- F2872
- F2905
- F2938
- F2972
- F3010
- F3038
- F3069
- F3173
- F3254
- F3294
- F3321
- F3390
- F3422
