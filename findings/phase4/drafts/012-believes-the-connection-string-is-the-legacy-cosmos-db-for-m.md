---
title: "Generated samples ship .env.example placeholder URIs in the Cosmos DB for MongoDB (RU) shape; kit needs a canonical cloud placeholder and an RU-vs-vCore contrast line"
repo: Azure/documentdb-agent-kit
type: issue
status: ready_with_edits
priority: P1
sample_count: 46
findings: 48
bucket: confusion-Q04
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Generated samples ship `.env.example` placeholders in the Cosmos DB for MongoDB (RU) connection-string shape

## What happens today

When an agent using this kit scaffolds a sample, its prior for "an Azure DocumentDB connection string" is the legacy **Azure Cosmos DB for MongoDB (RU)** form: `mongodb://` scheme, `<account>.mongo.cosmos.azure.com`, hard-coded port `10255`, `ssl=true&replicaSet=globaldb`, account-key credentials. In a 100-sample experiment with gpt-5-mini, almost every cold-quiz answer to "what does the connection string look like" gave that form or a variant of it; only a couple were correct.

The kit does state the vCore host and scheme (`skills/connection/SKILL.md` L60, `skills/mcp-setup/SKILL.md` L87, `skills/azure-deployment/SKILL.md` L288), and every build read the real URI from `DOCUMENTDB_URI`, so the apps connected. But the prior survives into the **committed placeholder**: at least 27 run folders (26 distinct samples) shipped an `.env.example` or README whose example `DOCUMENTDB_URI` is RU-shaped or an RU/vCore hybrid, for example:

- `mongodb://<user>:<pw>@your-mongocluster.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb`
- `mongodb://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com:10260/?tls=true&replicaSet=globaldb&authMechanism=SCRAM-SHA-256`
- `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/<db>?ssl=true&replicaSet=globaldb`
- `mongodb://<user>:<pw>@host:27017/?ssl=true&replicaSet=globaldb`

Two things in the kit let this through:

1. The only `.env.example` template, `skills/local-deployment/local-env-driven-config.md` L57-69, shows the local gateway string and then a cloud line whose host suffix (`<cluster>.mongocluster.documentdb.azure.com`) is not the published host (`<cluster>.mongocluster.cosmos.azure.com`) and which omits `retrywrites=false&maxIdleTimeMS=120000`. There is no canonical cloud placeholder an agent can copy verbatim. (The same wrong suffix also appears in `skills/security/security-entra-rbac.md` L15.)
2. No skill says what the string is **not**. Every mention states the vCore form positively; none names the RU tokens (`:10255`, `replicaSet=globaldb`, `.mongo.cosmos.azure.com`, account keys) as belonging to a different service, so a model that "knows" them merges them into the vCore host.

## Why it matters

- 46 of the 100 samples carried this confusion in their readiness report, and 26 samples published an RU-shaped or hybrid placeholder.
- A reader who copies the placeholder and only swaps credentials gets a string that does not match what the service publishes: the `.mongo.cosmos.azure.com` host and port `10255` belong to RU accounts, `replicaSet=globaldb` is not part of the vCore string, and with SRV no port is written. Errors from that string send the reader to Cosmos DB RU documentation.
- Audits in several runs flagged the same gap independently (`doc_gaps`: contrast older Cosmos `mongo.cosmos.azure.com` examples, with `replicaSet=globaldb` and port 10255, against the DocumentDB mongoClusters SRV pattern).

## Proposed change (PR, two files)

**`skills/local-deployment/local-env-driven-config.md`** — replace the cloud block at L65-69 with a canonical placeholder and a rule:

```dotenv
# Azure DocumentDB cluster: copy from portal -> cluster -> Connection strings
# (or: az documentdb mongocluster list-connection-strings)
DOCUMENTDB_URI=mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
# With cross-region replication, use the Global read-write string
# (<cluster>.global.mongocluster.cosmos.azure.com) for writes; see skills/high-availability
```

Add to **Rules**: "The committed `.env.example` must use this placeholder shape. Never write a `mongodb://` cloud URI with a port, `replicaSet=globaldb`, an account key, or a `.mongo.cosmos.azure.com` / `.documents.azure.com` host — those belong to Azure Cosmos DB (RU-based accounts), a different service. Prefer `tls=true` over the legacy `ssl=true` alias. `localhost:10260` is only the local gateway."

**`skills/connection/SKILL.md`** — under "Connection String Format" (L58-61), add a short callout:

> **Not Cosmos DB for MongoDB (RU).** Azure DocumentDB publishes an SRV (`mongodb+srv://`) string on `<cluster>.mongocluster.cosmos.azure.com`, so no port appears. `replicaSet=globaldb`, port `10255` and `.mongo.cosmos.azure.com` hosts belong to RU-based accounts and are not part of this string. Copy the string from the portal **Connection strings** pane or `az documentdb mongocluster list-connection-strings`; do not assemble it by hand.

(The `retryWrites=true` value on the L60 example, its missing `maxIdleTimeMS`, and the `mongocluster.documentdb.azure.com` suffix in two files are tracked in sibling issues; this issue is about the placeholder and the missing contrast. Merge if preferred.)

## Evidence (run folders from the experiment; no credentials)

- `runs/18-chargeback-dispute-multi-agent/20261124-192501` — `.env.example` uses `.mongo.cosmos.azure.com:10255` + `replicaSet=globaldb`; `05-audit.json` doc_gaps asks for exactly this guidance.
- `runs/08-dynamic-segmentation-engine/20261124-204222` — `.env.example` `your-cluster:10255/?ssl=true&replicaSet=globaldb`; `02-readiness.json` Q04 confusion.
- `runs/03-medication-interaction-checker/20261124-193347` — `app/.env.example` hybrid: vCore host with `:10260` and `replicaSet=globaldb`.
- `runs/20-store-locator-with-geospatial-search/20261124-185729` — `host:27017/?ssl=true&replicaSet=globaldb`.
- `runs/05-churn-prediction-pipeline/20261124-203754` — RU form in `.env.example` even though `04-decisions.md` D004 records reading the real URI from `DOCUMENTDB_URI`.

## Verification

### 1. Already covered? — confirmed (not there)

- `skills/local-deployment/local-env-driven-config.md` L65-69 (the kit's only `.env.example` guidance) shows the cloud line as `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.documentdb.azure.com/?tls=true&authMechanism=SCRAM-SHA-256` — wrong host suffix and no canonical published options.
- `skills/connection/SKILL.md` L60 gives the positive vCore form (with `retryWrites=true`), `skills/mcp-setup/SKILL.md` L87 and `skills/azure-deployment/SKILL.md` L288 likewise. `grep -rniE "10255|globaldb|mongo\.cosmos\.azure"` over `skills/` and `knowledge-base/` returns nothing: no skill contrasts the RU form.
- Learn already shows the right string (https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell: `mongodb+srv://<username>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`), which is why the target is the kit, not Learn. documentdb-mcp is not involved (it consumes a URI, it does not scaffold `.env.example`).

### 2. Is the premise true? — confirmed, with corrections applied

- Published string, SRV/no port, `.mongocluster.cosmos.azure.com` host: confirmed by the Learn mongosh page above.
- `az documentdb mongocluster list-connection-strings` exists: https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster ("List mongo cluster connection strings. This includes the default connection string using SCRAM-SHA-256...").
- Global read-write connection string exists when replication is enabled: https://learn.microsoft.com/en-us/azure/documentdb/cross-region-replication. The `.global.` host form is taken from the kit's own `skills/high-availability/SKILL.md` L34 and `ha-cross-region-replica.md` L80/L163; the draft now points there instead of asserting it as the default.
- Corrections applied to the body: (a) `ssl=true` is a legacy driver alias of `tls=true`, not an RU-only option that "will fail"; the rule now says prefer `tls=true` rather than banning it as RU. (b) Softened "gets a DNS or TLS failure" / "will fail here" to "does not match what the service publishes / not part of this string", since failure mode varies by driver. (c) Run counts re-measured by grepping `.env*`/`README*` in run folders for `replicaSet=globaldb|mongo.cosmos.azure.com|:10255`: 27 run folders, 26 samples (draft said 29 of 221 / 28 samples, and the "12 of those 46" and "26 latest runs" figures could not be reproduced, so they were removed). (d) Removed the precise "106 of 120" cold-quiz tally, which is not reproducible from this theme's 48 findings; kept the qualitative claim. (e) Line references corrected (L65-69, L58-61) and the second occurrence of the wrong host suffix (`skills/security/security-entra-rbac.md` L15) noted. (f) Option spelling aligned to the published `retrywrites=false`.

### 3. Maintainer skeptic — confirmed

Names two concrete files, line ranges, exact replacement text and a rule; the angle is DocumentDB-specific (distinguishing mongoClusters from RU accounts), and it fixes a factual error in the kit's own template. It overlaps the sibling connection-string issues (retryWrites value, maxIdleTimeMS, host suffix); a maintainer would likely ask to land them as one PR, which the body already invites. Belongs in Azure/documentdb-agent-kit.

## Finding ids

- F0039
- F0107
- F0257
- F0286
- F0314
- F0388
- F0420
- F0455
- F0495
- F0524
- F0596
- F0628
- F0660
- F0725
- F0942
- F0999
- F1039
- F1197
- F1223
- F1337
- F1368
- F1521
- F1556
- F1623
- F1655
- F1752
- F1788
- F1889
- F1981
- F2082
- F2120
- F2357
- F2387
- F2458
- F2550
- F2841
- F2874
- F2974
- F3040
- F3109
- F3143
- F3175
- F3225
- F3296
- F3323
- F3359
- F3458
- F3497
