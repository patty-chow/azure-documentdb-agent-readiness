---
title: "Fix `az documentdb mongo-cluster` typo in storage skill and show the canonical `az documentdb mongocluster` spelling once in azure-deployment"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 2
findings: 2
bucket: confusion-Q02
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Fix `az documentdb mongo-cluster` typo in the storage skill and show the canonical `az documentdb mongocluster` spelling once in `azure-deployment`

## What happens today

The dedicated Azure CLI group for Azure DocumentDB clusters is a single token: `az documentdb mongocluster` (documentdb extension, preview; subcommands `check-name-availability | create | show | list | update | delete | restore | list-connection-strings | reset-password | wait` and subgroups `firewall-rule | identity | microsoft-entra-user | replica`). Models that have not been grounded often split or hyphenate it: `az documentdb mongodb cluster create`, `az cosmosdb mongodb cluster ...`, `az documentdb mongo ...`, `az mongodb cluster ...`.

The kit currently reinforces the wrong token instead of correcting it:

- `skills/storage/storage-premium-ssdv2-limitations.md` line 28 is the **only** `az documentdb ...` invocation in the whole repository, and it reads `az documentdb mongo-cluster restore`, a hyphenated group that does not exist. Its trailing comment (`# In the restore template, set storage.type = 'PremiumSSDv2'.`) is also stale: the real `restore` command takes `--storage-type {PremiumSSD, PremiumSSDv2}` directly.
- `skills/azure-deployment/SKILL.md` never names the `mongocluster` group. Steps 6b, 7 and 9 use `az resource create/list --resource-type Microsoft.DocumentDB/mongoClusters`, which works, but leaves an agent with no canonical spelling to copy when a user asks for "the az command to create/show/restore the cluster".

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini, Agent Kit skills loaded), the cold-quiz question "Which Azure CLI command group creates and manages a cluster?" was answered wrong or partly wrong in most run folders. Most of those are the separate "`az cosmosdb`" prior; this PR targets the smaller, distinct subgroup-spelling error seen in the 2 samples tagged for this theme (13-household-grouping-linkage, 17-esg-scoring-pipeline) and also visible in cold answers for samples 01, 02, 03, 04, 05 and 19. In run 17 the agent emitted `az documentdb mongodb cluster create` and only switched to `mongocluster` after a Learn lookup. A script generated from the ungrounded answer, or copied from the storage skill as written, fails because the CLI does not recognize the `mongo-cluster` / `mongodb cluster` group.

## Proposed change

### 1. `skills/storage/storage-premium-ssdv2-limitations.md` (Path A, lines 27-34)

Replace:

```azurecli
az documentdb mongo-cluster restore \
  --resource-group "<rg>" \
  --cluster-name "<new-v2-cluster>" \
  --source-cluster "<existing-v1-cluster>" \
  --restore-time "2026-04-29T10:00:00Z"
# In the restore template, set storage.type = 'PremiumSSDv2'.
```

with:

```azurecli
# documentdb extension (auto-installs on first use; Azure CLI >= 2.75.0; preview). Group is one token: mongocluster.
az documentdb mongocluster restore \
  --resource-group "<rg>" \
  --cluster-name "<new-v2-cluster>" \
  --location "<region>" \
  --source-cluster "<existing-v1-cluster>" \
  --restore-time "2026-04-29T10:00:00Z" \
  --admin-user "<admin>" \
  --admin-password "$DOCUMENTDB_ADMIN_PASSWORD" \
  --storage-type PremiumSSDv2
```

### 2. `skills/azure-deployment/SKILL.md`

Add a callout at the top of **Step 6b — deploy with Azure CLI one-shot**, before the existing `az resource create` block:

> **Dedicated CLI group.** Azure DocumentDB clusters also have a first-class group, `az documentdb mongocluster` (single token; not `mongodb cluster`, `mongo-cluster`, or any `az cosmosdb ...` group). It ships in the `documentdb` extension, which installs automatically the first time you run it (Azure CLI 2.75.0+), and is in preview. Subcommands: `check-name-availability`, `create`, `show`, `list`, `update`, `delete`, `restore`, `list-connection-strings`, `reset-password`, `wait`; subgroups: `firewall-rule`, `identity`, `microsoft-entra-user`, `replica`. The `az resource` form below is kept because it pins the `2025-09-01` API version and needs no extension; use whichever the user prefers. Reference: https://learn.microsoft.com/cli/azure/documentdb/mongocluster

And in **Step 8 — retrieve the connection string**, add after the portal sentence:

```bash
az documentdb mongocluster list-connection-strings \
  --resource-group "<rg>" --cluster-name "<cluster>" -o json
```

Optionally mirror the same one-line note in the `docs/SKILLS.md` row for `azure-deployment/`.

## Evidence (run folders from the readiness experiment)

- `runs/13-household-grouping-linkage/20261124-204947/02-readiness.json`: confusions[Q02], cold answer `az cosmosdb mongodb cluster create`, outcome `wrong`
- `runs/17-esg-scoring-pipeline/20261124-192259/02-readiness.json`: confusions[Q02], cold answer `az documentdb mongodb cluster create ... --sku M30`, outcome `partly_wrong`
- `runs/17-esg-scoring-pipeline/20261124-192259/events.jsonl`: agent used `az documentdb mongodb cluster create` before grounding corrected it to `mongocluster`
- `runs/05-appointment-scheduling-assistant/20261124-193733/02-readiness.json`: confusions[Q02], `az documentdb mongodb` / `az documentdb mongo`
- `runs/03-substitute-product-finder/20261124-183232/02-readiness.json`: confusions[Q02], `az cosmosdb mongodb cluster`

Kit state checked at commit `4f41c15` (2026-11-23); CLI spelling and `restore` parameters verified against the `az documentdb mongocluster` reference page (updated 2026-11-17).

## Verification

### 1. Already covered? — confirmed (not covered)

Grepped `skills/`, `knowledge-base/` and `docs/` of the Azure/documentdb-agent-kit clone (commit 4f41c15) for `mongocluster`, `mongo-cluster`, `az documentdb` and `mongodb cluster`. The only CLI-group hit is `skills/storage/storage-premium-ssdv2-limitations.md:28`: "az documentdb mongo-cluster restore \" (wrong spelling). Every other `mongocluster` hit is a hostname (`*.mongocluster.cosmos.azure.com`) or the ARM type `Microsoft.DocumentDB/mongoClusters`. `skills/azure-deployment/SKILL.md` Step 6b (line 214) deploys with `az resource create` (line 224) and Step 8 (line 281) has no CLI example. The microsoft/documentdb-mcp clone has no `mongocluster` CLI references. The kit does not cover the ask; it contradicts it.

### 2. Premise true? — confirmed

Checked against https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster (updated 2026-11-17): the group is `az documentdb mongocluster`, part of the **documentdb** extension "(version 2.75.0 or higher)", which "will automatically install the first time you run" a command; every command is marked Preview. `restore` syntax: required `--cluster-name/--name`, `--resource-group`, `--restore-time`, `--source-cluster`; optional `--admin-user`, `--admin-password`, `--location`, `--storage-type {PremiumSSD, PremiumSSDv2}` among others, so the old "set storage.type in the restore template" comment is unnecessary. `list-connection-strings` takes `--cluster-name` and `--resource-group`. Correction applied: the draft's subcommand list omitted `check-name-availability` (and listed `wait` inconsistently); both lists now match the reference page, with subgroups separated from commands. The unverified "106 of 120 run folders" figure was replaced by a qualitative statement; the sample list (01, 02, 03, 04, 05, 13, 17, 19) was confirmed by grepping the runs' 02-readiness.json files.

### 3. Maintainer skeptic — confirmed

Names two exact files and line ranges, gives drop-in replacement text, fixes a concrete bug (a non-existent CLI group taught by the kit itself), and is specific to Azure DocumentDB. It keeps the existing `az resource` path rather than rewriting the skill. Belongs in Azure/documentdb-agent-kit, which owns both files. I would merge it with the small edits above.

Priority P1: a wrong fact in the kit that agents act on (a copied command fails), although only 2 theme samples are tagged and no build is recorded as broken by it.

## Finding ids

- F2214
- F2839
