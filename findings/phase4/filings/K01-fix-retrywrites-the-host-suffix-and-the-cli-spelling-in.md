---
id: K01
title: "Fix retryWrites and the host suffix in connection/SKILL.md, driver-singleton-client.md, security-tls-required.md and local-env-driven-config.md (one canonical connection string)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P0
sample_count: 43
member_drafts:
  - 040-believes-the-service-is-ru-era-azure-cosmos-db-for-mongodb-p.md
  - 013-believes-the-ru-era-connection-options-apply-replicaset-glob.md
open_questions: 0
---

# Fix retryWrites and the host suffix in the kit (one canonical connection string)

## What happens today

The kit disagrees with itself, and with the string the portal and Learn publish, on the one value every builder copies. At commit 4f41c15:

| File | Line | Today | Problem |
|---|---|---|---|
| `skills/connection/SKILL.md` | 60 | `...?tls=true&authMechanism=SCRAM-SHA-256&retryWrites=true` | Published string has `retrywrites=false` and `maxIdleTimeMS=120000` |
| `skills/driver/driver-singleton-client.md` | 26 | `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })` in the **Correct** block | Contradicts the published string |
| `skills/security/security-tls-required.md` | 26 | `retryWrites: true` in the **Correct** block | Same |
| `skills/local-deployment/local-env-driven-config.md` | 68 | `<cluster>.mongocluster.documentdb.azure.com` | Suffix does not exist; real suffix is `.mongocluster.cosmos.azure.com` |
| `skills/storage/storage-premium-ssdv2-limitations.md` | 28 | `az documentdb mongo-cluster restore` | CLI group is `az documentdb mongocluster` (no hyphen); fixed in K02, not here |
| `skills/azure-deployment/SKILL.md` | 288-291 | `<cluster>.global.mongocluster.cosmos.azure.com` as "Form of the connection string", `retrywrites=false&maxIdleTimeMS=120000`, plus a sentence that the service does not support retryable writes | Only file with the published `retrywrites` value; its rationale sentence also claims the driver default causes connection errors, which is not established (see Resolved). The `.global.` host is valid but unexplained and disagrees with every other kit file, which uses the plain host (see Resolved) |
| `skills/security/security-entra-rbac.md` | 15 | `<name>.mongocluster.documentdb.azure.com` in the Incorrect sample | Same non-existent suffix; open PR #14 rewrites the file but has not merged |

No file names the legacy request-unit product (`*.mongo.cosmos.azure.com`, port `10255`, `ssl=true`, `replicaSet=globaldb`), so an agent that arrives with that prior is never told it belongs to a different service.

## Why it matters

In one 100-sample run of an agent-readiness experiment (gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers), **43 of 100 samples** produced at least one finding in this set (61 findings). Counts are from that single run and may move on a re-run.

- Before loading the kit, agents answered with the RU-era shape: `az cosmosdb create`, `az cosmosdb mongodb collection create --throughput 400`, `mongodb://...:10255/?ssl=true&replicaSet=globaldb`, stale Mongoose flags.
- After loading `documentdb-driver` and `documentdb-connection`, builders copied the kit: generated `src/db.js` files shipped `retryWrites: true`, and audits graded that "followed" because the kit's own Correct blocks show it. One audit even recommended adding `retryWrites=true&retryReads=true` as a fix.
- Generated `.env.example` files carried RU-style hosts or the non-existent `.documentdb.azure.com` suffix, which do not resolve for an Azure DocumentDB cluster.

Learn already publishes the correct string, so this is a kit fix.

## Proposed change

**1. `skills/connection/SKILL.md`, Connection String Format (lines 57-61).** Replace the code block and add the notes below it:

```
mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

> Copy this string unchanged from the portal (**Cluster > Settings > Connection strings**) or from `az documentdb mongocluster list-connection-strings --resource-group <rg> --cluster-name <name>` (it lists `GlobalReadWrite` first and `Self` second, so pick the entry by `name`, not by position), and pass it to the driver as-is (`new MongoClient(process.env.DOCUMENTDB_URI)`). Do not assemble it by hand and do not override its options (`retrywrites=false`, `maxIdleTimeMS=120000`) in driver options. Never construct the host from the cluster name; use the string the portal, CLI or REST API returns.
>
> **Two valid hosts.** The portal offers two strings: **Self (always this cluster)** on `<cluster>.mongocluster.cosmos.azure.com` and **Global read-write** on `<cluster>.global.mongocluster.cosmos.azure.com`. On a single cluster they are interchangeable. If the cluster has or may get a cross-region replica, use the Global read-write string for writes so that a promotion needs no code change; the Self string of the old primary becomes read-only after promotion. Replica clusters expose only a Self string. In-region HA failover changes neither. (Learn: how-to-connect-role-based-access-control, "Get cluster credentials"; how-to-cluster-replica, "Use connection strings"; tutorial-nodejs-mongoose, "Verify the cluster from a terminal".)
>
> Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys).
>
> **This is not Azure Cosmos DB for MongoDB (RU).** There is no explicit port and no replica-set name: the cluster host is an SRV name only, with no A record, so a `mongodb://` string with the cluster host does not resolve. `replicaSet=globaldb`, `ssl=true`, port `10255`, `appName=@<account>@` and hosts ending in `.mongo.cosmos.azure.com` belong to that separate service and must not be carried over.
>
> Local Docker gateway: `mongodb://<admin-username>:<admin-password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` (the container requires a username and password; see `documentdb-local-deployment` and the Learn development-loop tutorial).

**2. `skills/driver/driver-singleton-client.md` line 26:**

```js
new MongoClient(uri, { maxPoolSize: 50, retryWrites: false }) // required: Azure DocumentDB does not support retryable writes (see documentdb-connection)
```

**3. `skills/security/security-tls-required.md` line 26:** `retryWrites: true` -> `retryWrites: false` (same comment).

**4. `skills/local-deployment/local-env-driven-config.md` line 68:**

```dotenv
DOCUMENTDB_URI=mongodb+srv://<user>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

**5. `skills/azure-deployment/SKILL.md` lines 288-291:** keep `retrywrites=false`. Replace the rationale sentence with the canonical one-liner (findings/phase4/DECISIONS.md): "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." The current sentence's claim that leaving the driver default causes connection errors is not established and must be dropped. On line 288, replace `<cluster>.global.mongocluster.cosmos.azure.com` with the plain `<cluster>.mongocluster.cosmos.azure.com` so the file matches `connection/SKILL.md`, `mcp-setup/SKILL.md`, README.md, GEMINI.md, install.sh and install.ps1, and add one sentence pointing to the Self / Global read-write note in item 1 (either string works on a single cluster; use Global read-write for writes when a replica exists; never construct the host from the cluster name).

**6. `skills/security/security-entra-rbac.md` line 15:** `.mongocluster.documentdb.azure.com` -> `.mongocluster.cosmos.azure.com` in the Incorrect sample (one line). Open PR #14 rewrites this file with the correct suffix; if #14 merges first, drop this item at rebase. Everything else in that file (the `readWrite` role, the placeholder OIDC example) stays with #14 / K03.

Not in this PR:
- The `az documentdb mongo-cluster restore` typo in `skills/storage/storage-premium-ssdv2-limitations.md` line 28 (from draft 040). The reviewer merged the CLI-group fixes into draft 004, so it lands in K02, which replaces the whole restore block (including the stale trailing comment).
- Adding `az documentdb mongocluster create` / `list-connection-strings` steps and an RU-contrast callout to `azure-deployment/SKILL.md` (draft 040, item 7) goes in the CLI-group PR (K02) and the naming PR (K14).
- Renaming "Cosmos DB for MongoDB vCore" and the `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/` links in `skills/data-modeling/` (draft 040 follow-up) goes in K14.
- A kit CI check that rejects host suffixes and `retryWrites` values that disagree with the canonical string (reviewer's missing theme) would keep this from regressing; it is a separate change.
- `benchmarks/documentdb-sdk-skills/tasks/orders-api-python/environment/reference/app.py` sets `retryWrites=True`; it should be changed to `False` for the same reason (separate change).

After this change every `retryWrites` value and every host suffix in connection strings and `MongoClient` options objects under `skills/` agrees with the published string, every default snippet shows the plain Self host, and `connection/SKILL.md` explains when the Global read-write host is the better choice.

## Evidence

- `runs/03-core-banking-transaction-ledger/20261124-200452/` (`events.jsonl` loads `documentdb-connection`, then writes `app/src/db.js` with `retryWrites: true`, line 23)
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/05-audit.json` (`retryWrites: true` graded "followed")
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json` (cold `az cosmosdb create`, `:10255/?ssl=true&replicaSet=globaldb`)
- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` (cold `--throughput 400` collection create)
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/app/.env.example` (RU-style URI shipped, placeholder credentials)
- `runs/11-preference-center-consent-store/20261124-204614/05-audit.md` (audit recommends `retryWrites=true`)

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- Host form (`.global.` vs plain): settled from Learn, no SME needed (DECISIONS.md, SME topic 3). Both hosts are valid: the plain host is the portal's "Self (always this cluster)" string and `.global.` is the "Global read-write" string; "In a single-cluster configuration, you can use either connection string indiscriminately", the Global read-write string keeps writes working across a replica promotion and exists only on the primary, replica clusters expose only Self strings, and the host must be taken from the returned connection string rather than constructed from the cluster name. Kit default snippets show the plain host with that one-line note. The managed test of 2026-11-25 (one cluster, no replica) observed both hosts resolving, authenticating and taking writes, with writes through either host visible through the other; `list-connection-strings` returned `GlobalReadWrite` first and `Self` second; every service-issued string carried `retrywrites=false&maxIdleTimeMS=120000`; and each cluster host is an SRV name with no A record (ENGINE-TESTS.md, Managed service; DECISIONS.md, topic 3). Sources: https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control ("Get cluster credentials"); https://learn.microsoft.com/en-us/azure/documentdb/how-to-cluster-replica#use-connection-strings; https://learn.microsoft.com/en-us/azure/documentdb/how-to-private-link; https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose; https://learn.microsoft.com/en-us/training/modules/create-configure-azure-documentdb-cluster/3-connect-to-cluster.
- `security-entra-rbac.md` suffix and PR #14: DECISIONS.md (SME topic 3, kit statements contradicted by a source) records that `security-entra-rbac.md:15` carries the same non-existent `.mongocluster.documentdb.azure.com` suffix as `local-env-driven-config.md:68` and should be added to K01; it lands here as item 6, to be dropped at rebase if #14 merges first. Source: DECISIONS.md, host-forms section; https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose ("Azure DocumentDB hostnames use the `mongocluster.cosmos.azure.com` domain").

## Source drafts

- 040-believes-the-service-is-ru-era-azure-cosmos-db-for-mongodb-p.md
- 013-believes-the-ru-era-connection-options-apply-replicaset-glob.md
