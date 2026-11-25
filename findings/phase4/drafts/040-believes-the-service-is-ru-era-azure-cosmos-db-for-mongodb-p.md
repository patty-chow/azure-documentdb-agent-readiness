---
title: "Agent Kit: fix retryWrites, host suffix and CLI spelling; add an explicit 'this is not RU-era Cosmos DB for MongoDB' contrast"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P0
sample_count: 32
findings: 40
bucket: confusion-sample-specific
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Fix retryWrites / host suffix / CLI spelling and add an explicit "not RU-era Cosmos DB for MongoDB" contrast

## What happens today

When an LLM agent is asked about Azure DocumentDB *before* loading these skills, its default mental model is the legacy request-unit **Azure Cosmos DB for MongoDB (RU)**: a `databaseAccounts` host ending in `.mongo.cosmos.azure.com` on hard-coded port `10255`, `ssl=true&replicaSet=globaldb`, `az cosmosdb create`, `az cosmosdb mongodb collection create --throughput 400 --shard key=...`, RU/s tuning, and stale Mongoose flags (`useNewUrlParser`/`useUnifiedTopology`).

The kit mostly displaces that prior once loaded (connection/SKILL.md and mcp-setup show the SRV host with `tls=true` + `SCRAM-SHA-256`; local-deployment documents 10260; azure-deployment has the Bicep template and the `retrywrites=false` string; sharding covers `sh.shardCollection`). But at commit 4f41c15 the kit is wrong or silent at exactly the points where the model is wrong:

| File | Line | Today | Problem |
|---|---|---|---|
| `skills/connection/SKILL.md` | 60 | `...&authMechanism=SCRAM-SHA-256&retryWrites=true` | Contradicts `skills/azure-deployment/SKILL.md:288-291`, which prints `retrywrites=false` and says leaving the driver default "will cause connection errors". Also omits `maxIdleTimeMS=120000` that the portal and Learn quickstart strings carry. |
| `skills/security/security-tls-required.md` | 26 | `retryWrites: true` in the **Correct** block | Same contradiction, in a block labelled "Correct". |
| `skills/driver/driver-singleton-client.md` | 26 | `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })` in the **Correct** block | Same. |
| `skills/local-deployment/local-env-driven-config.md` | 68 | `<cluster>.mongocluster.documentdb.azure.com` | Host suffix does not exist. Real suffix is `.mongocluster.cosmos.azure.com`. |
| `skills/security/security-entra-rbac.md` | 15 | `prod-ddb.mongocluster.documentdb.azure.com` | Same non-existent suffix. |
| `skills/storage/storage-premium-ssdv2-limitations.md` | 28 | `az documentdb mongo-cluster restore` | The extension's group is `az documentdb mongocluster` (no hyphen). This is the **only** `az documentdb` mention in the whole kit. |
| `skills/azure-deployment/SKILL.md` | — | Shows `az account`, `az provider`, `az deployment group`, `az resource create` only | Never names `az documentdb mongocluster create` or `list-connection-strings`; Step 8 says "From the portal" only. |
| all skills | — | zero occurrences of "RU", "request unit", "10255", "replicaSet", "mongo.cosmos.azure.com" | Nothing tells the agent *what this is not*, so the RU prior survives on provisioning/capacity questions. |

## Why it matters

In a 100-sample agent-readiness experiment (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), **40 cold-quiz answers across 32 of 100 samples** were graded "confused with azure_cosmos_db_for_mongodb_ru" (8 outright wrong, the rest partly wrong or outdated). Typical cold answers:

- `az cosmosdb create --kind MongoDB ...` for "which resource/CLI creates the cluster"
- `az cosmosdb mongodb collection create ... --throughput 400 --shard key=/tradeId` for "how do I create the collection"
- `mongodb://user:pass@host:10255/?ssl=true&replicaSet=globaldb` for "what port/TLS settings"
- `mongoose.connect(uri, { useNewUrlParser: true, useUnifiedTopology: true })`

Grounding on the kit fixed the host and port in most cases, but the kit cannot correct what it itself gets wrong: in one build the generated `app/src/db.js` shipped `retryWrites: true` and the audit marked it **followed** because the kit's own driver/security files show that value. Several other builds' `.env.example` carried a Cosmos-style host pattern or the wrong suffix, and readiness reports repeatedly asked for a "copy the connection string as-is, do not hand-assemble it" rule that no skill states.

Learn already shows the correct SRV string on the connect/quickstart pages, so this is a kit fix, not a docs fix.

## Proposed changes

### 1. `skills/connection/SKILL.md` — "Connection String Format" (line 57-61)

Replace the code block and add a short rule list:

```
mongodb+srv://<user>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

Rules:
- Copy the string **unchanged** from the portal (**cluster → Connection strings**) or from `az documentdb mongocluster list-connection-strings --resource-group <rg> --cluster-name <name>`. The host the portal and Learn quickstarts hand out may be `<cluster>.global.mongocluster.cosmos.azure.com` (global endpoint) or `<cluster>.mongocluster.cosmos.azure.com`; both are valid, so keep whichever you are given. Do not assemble or rewrite it; pass it to the driver as-is (`new MongoClient(process.env.DOCUMENTDB_URI)`).
- `retrywrites=false` is required (see `documentdb-azure-deployment`); never override it with `retryWrites: true` in driver options.
- There is **no explicit port** (SRV) and **no `replicaSet`**. If you find yourself typing `:10255`, `ssl=true&replicaSet=globaldb`, `appName=@<account>@` or a host ending in `.mongo.cosmos.azure.com`, you are describing the legacy RU-based Azure Cosmos DB for MongoDB, not Azure DocumentDB.
- Local Docker gateway: `mongodb://localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` (see `documentdb-local-deployment`).

### 2. `skills/security/security-tls-required.md` line 26 and 3. `skills/driver/driver-singleton-client.md` line 26

`retryWrites: true` -> `retryWrites: false // required by Azure DocumentDB; matches retrywrites=false in the cluster connection string`

### 4. `skills/local-deployment/local-env-driven-config.md` line 68

```dotenv
DOCUMENTDB_URI=mongodb+srv://<username>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

### 5. `skills/security/security-entra-rbac.md` line 15

`prod-ddb.mongocluster.documentdb.azure.com` -> `prod-ddb.mongocluster.cosmos.azure.com`

### 6. `skills/storage/storage-premium-ssdv2-limitations.md` line 28

`az documentdb mongo-cluster restore` -> `az documentdb mongocluster restore`. The `restore` subcommand exists in the `documentdb` extension ("Restore a mongo cluster to a new cluster from a point in time"); check the remaining flags in that block against `az documentdb mongocluster restore --help`.

### 7. `skills/azure-deployment/SKILL.md`

(a) After the intro (line 7-13), add a callout:

> **This is not the RU API.** Azure DocumentDB is the resource type `Microsoft.DocumentDB/mongoClusters` (formerly "Azure Cosmos DB for MongoDB vCore"), managed with the `az documentdb mongocluster` extension or Bicep/Terraform. Capacity is vCore **M-tiers** (M30, M40, ...), not RU/s; there is no throughput to provision per collection. Databases and collections are created through the driver or `mongosh`, not via ARM/CLI. `az cosmosdb ...`, `databaseAccounts`, `*.mongo.cosmos.azure.com:10255` and `replicaSet=globaldb` all belong to the separate RU-based service and must not be used.

(b) Step 6b — add the extension path alongside `az resource create`:

```bash
# The documentdb extension (Azure CLI 2.75.0+) installs automatically on first use;
# `az extension add --name documentdb` installs it explicitly.
az documentdb mongocluster create \
  --resource-group "$RG" --cluster-name "$CLUSTER" --location "$LOCATION" \
  --admin-user "$ADMIN_USER" --admin-password "$ADMIN_PW" \
  --tier M30 --storage-size 128 --storage-type PremiumSSDv2 \
  --shard-count 1 --high-availability Disabled
```

(c) Step 8 — add the CLI alternative to "From the portal":

```bash
az documentdb mongocluster list-connection-strings --resource-group "$RG" --cluster-name "$CLUSTER"
```

and state: "Pass the returned string to the application **unchanged** (as `DOCUMENTDB_URI`). Do not substitute a port or add `replicaSet`."

Flag names in (b)/(c) are taken from the Azure CLI reference for `az documentdb mongocluster` (extension commands, currently Preview); the command shape is what the agent needs to stop reaching for `az cosmosdb`.

## Out of scope (follow-up)

`skills/data-modeling/model-embed-vs-reference.md:7`, `model-16mb-limit.md:7` and their reference links still say "Cosmos DB for MongoDB vCore" and point at `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/`; renaming to Azure DocumentDB and `learn.microsoft.com/azure/documentdb/` would remove the last place the kit itself reinforces the Cosmos naming.

## Evidence (run folders from the experiment)

- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json` — confusions S01 (`az cosmosdb create`) and S02 (`:10255/?ssl=true&replicaSet=globaldb`)
- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` — confusion S03 (`az cosmosdb mongodb collection create --throughput 400`)
- `runs/15-prescription-refill-agent/20261124-195253/02-readiness.json` — confusion S03 (port 10255 vs SRV / local 10260)
- `runs/03-medication-interaction-checker/20261124-193347/02-readiness.json` — confusion S02 (stale Mongoose flags, `authSource=admin`, 10255)
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/05-audit.json` — generated `app/src/db.js` shipped `retryWrites: true`, graded "followed" because the kit's own files show it

(32 distinct samples / 40 findings in total; the five above are representative.)

## Verification

### 1. Already covered? -- confirmed (not covered)

Grep of the kit clone at commit 4f41c15 (`skills/`, `knowledge-base/`):
- `skills/connection/SKILL.md:60` prints `...&authMechanism=SCRAM-SHA-256&retryWrites=true`.
- `skills/security/security-tls-required.md:26` has `retryWrites: true`; `skills/driver/driver-singleton-client.md:26` has `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })`.
- `skills/azure-deployment/SKILL.md:288-291` prints `retrywrites=false` and says "leaving it at the driver default will cause connection errors", so the kit contradicts itself.
- `skills/local-deployment/local-env-driven-config.md:68` and `skills/security/security-entra-rbac.md:15` use `.mongocluster.documentdb.azure.com`.
- `skills/storage/storage-premium-ssdv2-limitations.md:28` is the only `az documentdb` mention and spells it `mongo-cluster`.
- Zero hits for `10255`, `replicaSet`, `mongo.cosmos.azure`, `request unit`, `RU/s` anywhere in skills or knowledge-base: there is no RU-vs-vCore contrast.
The MCP server repo is not the right home for this. Learn already shows the correct string (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs uses `mongodb+srv://...@<cluster>.global.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` and tells readers to copy it from **Connection strings**), so no Learn change is needed.

### 2. Premise true? -- confirmed (with flag-level corrections applied)

- Connection string, `retrywrites=false`, `maxIdleTimeMS=120000`, SRV host on `.mongocluster.cosmos.azure.com`: matches the given ground truth and the Learn Node.js quickstart above. The Learn string uses the `.global.` host form, so a note was added that both host forms are valid and the string must be kept as given.
- `.mongocluster.documentdb.azure.com` is not a real suffix: confirmed against ground truth and Learn.
- CLI: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster confirms the group `az documentdb mongocluster` (part of the **documentdb** extension, Azure CLI 2.75.0+, installs automatically on first use) with `create`, `list-connection-strings` (`--cluster-name ... -g ...`), and `restore` ("Restore a mongo cluster to a new cluster from a point in time").
- Corrections applied to the body: the `create` flags are `--admin-user` / `--admin-password` (the draft had `--administrator-login` / `--administrator-login-password`), with `--tier M30 --storage-size 128 --storage-type PremiumSSDv2 --shard-count 1 --high-availability Disabled` from the reference example. The "verify restore exists" hedge was replaced with a confirmation, and the extension auto-install note was added.
- vCore M-tiers rather than RUs, `Microsoft.DocumentDB/mongoClusters`, and the former name "Azure Cosmos DB for MongoDB vCore" all agree with the given ground truth.

### 3. Maintainer skeptic -- confirmed

The change names exact files and line numbers, gives line-level replacements, and fixes real inconsistencies in the kit (its own files contradict each other on retryWrites, two examples show a non-existent host, and the CLI is misspelled). The RU-contrast callout is DocumentDB-specific and short. I would accept it as a PR with the corrected CLI flags.

## Finding ids

- F0118
- F0119
- F0267
- F0358
- F0359
- F0395
- F0431
- F0081
- F0157
- F0393
- F0703
- F0803
- F0858
- F0926
- F1113
- F1140
- F1380
- F1410
- F1633
- F1664
- F1566
- F1726
- F1799
- F1835
- F1991
- F2026
- F2027
- F2252
- F2333
- F2561
- F2600
- F2658
- F2693
- F2694
- F3119
- F3151
- F3153
- F3185
- F3187
- F3235
