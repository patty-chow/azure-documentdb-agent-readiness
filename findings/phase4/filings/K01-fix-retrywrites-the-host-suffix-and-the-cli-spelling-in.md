---
id: K01
title: "Fix retryWrites and the host suffix in connection/SKILL.md, driver-singleton-client.md, security-tls-required.md and local-env-driven-config.md (one canonical connection string)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P0
sample_count: 43
member_drafts:
  - 040-believes-the-service-is-ru-era-azure-cosmos-db-for-mongodb-p.md
  - 013-believes-the-ru-era-connection-options-apply-replicaset-glob.md
open_questions: 2
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
| `skills/azure-deployment/SKILL.md` | 288-291 | `retrywrites=false&maxIdleTimeMS=120000`, plus a sentence that the service does not support retryable writes | Only file with the published value; its rationale sentence also claims the driver default causes connection errors, which is not established (see Resolved) |

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

> Copy this string unchanged from the portal (**cluster > Connection strings**) or from `az documentdb mongocluster list-connection-strings --resource-group <rg> --cluster-name <name>`, and pass it to the driver as-is (`new MongoClient(process.env.DOCUMENTDB_URI)`). Do not assemble it by hand and do not override its options (`retrywrites=false`, `maxIdleTimeMS=120000`) in driver options.
>
> Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys).
>
> **This is not Azure Cosmos DB for MongoDB (RU).** There is no explicit port (SRV) and no replica-set name. `replicaSet=globaldb`, `ssl=true`, port `10255`, `appName=@<account>@` and hosts ending in `.mongo.cosmos.azure.com` belong to that separate service and must not be carried over.
>
> Local Docker gateway: `mongodb://localhost:10260/?tls=true&tlsAllowInvalidCertificates=true` (see `documentdb-local-deployment`).

**2. `skills/driver/driver-singleton-client.md` line 26:**

```js
new MongoClient(uri, { maxPoolSize: 50, retryWrites: false }) // required: Azure DocumentDB does not support retryable writes (see documentdb-connection)
```

**3. `skills/security/security-tls-required.md` line 26:** `retryWrites: true` -> `retryWrites: false` (same comment).

**4. `skills/local-deployment/local-env-driven-config.md` line 68:**

```dotenv
DOCUMENTDB_URI=mongodb+srv://<user>:<password>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

**5. `skills/azure-deployment/SKILL.md` line 291:** keep `retrywrites=false`. Replace the rationale sentence with the canonical one-liner (findings/phase4/DECISIONS.md): "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." The current sentence's claim that leaving the driver default causes connection errors is not established and must be dropped.

Not in this PR:
- The `az documentdb mongo-cluster restore` typo in `skills/storage/storage-premium-ssdv2-limitations.md` line 28 (from draft 040). The reviewer merged the CLI-group fixes into draft 004, so it lands in K02, which replaces the whole restore block (including the stale trailing comment).
- `skills/security/security-entra-rbac.md` line 15 has the same bad suffix, but open PR #14 rewrites that file with the correct suffix. If #14 stalls, add that one-line fix here.
- Adding `az documentdb mongocluster create` / `list-connection-strings` steps and an RU-contrast callout to `azure-deployment/SKILL.md` (draft 040, item 7) goes in the CLI-group PR (K02) and the naming PR (K14).
- Renaming "Cosmos DB for MongoDB vCore" and the `learn.microsoft.com/azure/cosmos-db/mongodb/vcore/` links in `skills/data-modeling/` (draft 040 follow-up) goes in K14.
- A kit CI check that rejects host suffixes and `retryWrites` values that disagree with the canonical string (reviewer's missing theme) would keep this from regressing; it is a separate change.
- `benchmarks/documentdb-sdk-skills/tasks/orders-api-python/environment/reference/app.py` sets `retryWrites=True`; it should be changed to `False` for the same reason (separate change).

After this change every `retryWrites` value and every host suffix in connection strings and `MongoClient` options objects under `skills/` agrees with the published string (except `security-entra-rbac.md`, which PR #14 fixes). `azure-deployment/SKILL.md` keeps its `.global.` host form pending Open question 1.

## Evidence

- `runs/03-core-banking-transaction-ledger/20261124-200452/` (`events.jsonl` loads `documentdb-connection`, then writes `app/src/db.js` with `retryWrites: true`, line 23)
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/05-audit.json` (`retryWrites: true` graded "followed")
- `runs/01-product-catalog-with-vector-search/20261124-175429/02-readiness.json` (cold `az cosmosdb create`, `:10255/?ssl=true&replicaSet=globaldb`)
- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` (cold `--throughput 400` collection create)
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/app/.env.example` (RU-style URI shipped, placeholder credentials)
- `runs/11-preference-center-consent-store/20261124-204614/05-audit.md` (audit recommends `retryWrites=true`)

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

## Open questions

1. **Host form.** [needs SME confirmation] Draft 040 reports Learn quickstarts show `<cluster>.global.mongocluster.cosmos.azure.com`, and the kit's own `skills/azure-deployment/SKILL.md` line 288 uses that form. Should the kit say both `.global.` and non-global hosts are valid and to keep whichever the portal gives (040's proposed wording), or only show `<cluster>.mongocluster.cosmos.azure.com`?
2. **PR #14.** Should the `security-entra-rbac.md` suffix fix wait for #14 or land here?

## Source drafts

- 040-believes-the-service-is-ru-era-azure-cosmos-db-for-mongodb-p.md
- 013-believes-the-ru-era-connection-options-apply-replicaset-glob.md
