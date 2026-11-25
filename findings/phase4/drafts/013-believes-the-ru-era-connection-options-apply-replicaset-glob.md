---
title: "Align retryWrites with the portal connection string and fix a non-existent host suffix in connection, driver, security and local-deployment skills"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 20
findings: 21
bucket: confusion-Q04
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Align `retryWrites` with the portal connection string and fix a non-existent host suffix in the connection, driver, security and local-deployment skills

## What happens today

The kit disagrees with itself, and with the string the portal and CLI emit, about the one string every builder copies:

| File | Line | Today | Problem |
|---|---|---|---|
| `skills/connection/SKILL.md` | 60 | `...?tls=true&authMechanism=SCRAM-SHA-256&retryWrites=true` | Differs from the published string (`retrywrites=false`); also omits `maxIdleTimeMS=120000` |
| `skills/security/security-tls-required.md` | 26 | `retryWrites: true` in the **Correct** block | Contradicts the published string |
| `skills/driver/driver-singleton-client.md` | 26 | `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })` in the **Correct** block | Contradicts the published string |
| `skills/local-deployment/local-env-driven-config.md` | 68 | `<cluster>.mongocluster.documentdb.azure.com` | Host suffix does not exist; no `retrywrites=false` or `maxIdleTimeMS` |
| `skills/azure-deployment/SKILL.md` | 288-291 | `...&retrywrites=false&maxIdleTimeMS=120000` plus a note that "Azure DocumentDB does not support retryable writes" | Value matches the portal; the stated reason is not backed by Learn (see below) |

The portal, `az documentdb mongocluster list-connection-strings` and the Learn quickstarts (quickstart-nodejs, quickstart-python, how-to-connect-mongo-shell) all emit `retrywrites=false&maxIdleTimeMS=120000`. `documentdb-connection` is the skill that triggers on `connect()` code, so it is the one builders read at the moment they write the client options, and it shows a different value.

The Cosmos DB RU product (`*.mongo.cosmos.azure.com:10255`, `ssl=true`, `replicaSet=globaldb`) is never named anywhere in the kit, so a builder carrying that option set from training data is never told it belongs to a different product.

## Why it matters

In a 100-sample agent-readiness run with gpt-5-mini (DocumentDB Agent Kit + DocumentDB/Azure/Learn MCP servers):

- **20 of 100 samples** answered the cold-quiz question "what does a connection string look like" with the RU-era shape: `mongodb://...@<account>.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb...`, several leaving `retryWrites` at the driver default and two explicitly unsure whether it must be `false`.
- After loading the kit the builder followed the kit. In `runs/03-core-banking-transaction-ledger/20261124-200452/events.jsonl` the build stage loads `documentdb-driver` and `documentdb-connection`, then writes `src/db.js` with `retryWrites: true` (line 23), exactly what the two skills show.
- Across the generated apps, **19 run folders ship `retryWrites: true`** in client code or `.env.example` (e.g. `05-shopping-cart-with-real-time-inventory/.../app/src/db.js` line 22), and **24 `.env.example` files ship an RU-style URI** with `replicaSet=globaldb` and/or `:10255` (recount over `runs/`, excluding dependency folders).
- At least one audit stage (`runs/11-preference-center-consent-store/20261124-204614/05-audit.md`) recommended adding `retryWrites=true&retryReads=true` to the connection string as a *fix*, so the inconsistent value propagates from the kit into the reviewer as well as the builder.

Net effect: generated apps diverge from the connection string Microsoft publishes for the service, and RU-only options (`replicaSet=globaldb`, port `10255`, `.mongo.cosmos.azure.com`) produce hosts that do not resolve for an Azure DocumentDB cluster.

## Proposed change

**1. `skills/connection/SKILL.md`** -- replace the Connection String Format block (around lines 58-61) with:

```
mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

and add directly under it:

> This is the string the portal (**cluster > Connection strings**) and `az documentdb mongocluster list-connection-strings` emit. Copy it from there rather than composing one by hand, and keep its options (`retrywrites=false`, `maxIdleTimeMS=120000`) unless you have verified a different retry configuration for your deployment. Driver-level retries are not a substitute for idempotent application writes; see Learn "Reliability in Azure DocumentDB".
>
> **This is not Azure Cosmos DB for MongoDB (RU).** Options from that product do not apply here and must not be carried over: `replicaSet=globaldb`, `ssl=true`, port `10255`, and hosts ending in `.mongo.cosmos.azure.com`. SRV resolution handles routing; there is no replica-set name to pass.

**2. `skills/security/security-tls-required.md` line 26** -- `retryWrites: true` -> `retryWrites: false` (matches the published string; the rule is about TLS, so the option should not contradict the connection skill).

**3. `skills/driver/driver-singleton-client.md` line 26** -- `{ maxPoolSize: 50, retryWrites: true }` -> `{ maxPoolSize: 50, retryWrites: false }`.

**4. `skills/local-deployment/local-env-driven-config.md` line 68** --

```
DOCUMENTDB_URI=mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

**5. `skills/azure-deployment/SKILL.md` line 291** -- soften the rationale so it matches Learn: replace "Azure DocumentDB does not support retryable writes; leaving it at the driver default will cause connection errors" with "This matches the string the portal emits; keep it unless you have verified a different retry configuration (see `documentdb-connection`)." The open-source engine implements retryable-write bookkeeping and the Learn Mongoose quickstart says `retryWrites=false` "isn't presented as a service requirement", so the kit should not assert that the service rejects retryable writes.

**Not included here:** `skills/security/security-entra-rbac.md` line 15 has the same bad host suffix (inside its **Incorrect** example), but open PR #14 already rewrites that file with `.mongocluster.cosmos.azure.com` and `retryWrites: false` examples, so this PR leaves it alone to avoid a merge conflict. If #14 stalls, that one-line fix should be added here.

After this change every connection string and every `MongoClient(...)` options object under `skills/` agrees with the string the portal emits. No other file under `skills/` or `knowledge-base/` uses `retryWrites=true`, `globaldb`, `10255` or `ssl=true` (grep at commit 4f41c15, 2026-11-23). Outside those folders, `benchmarks/documentdb-sdk-skills/tasks/orders-api-python/environment/reference/app.py` still sets `retryWrites=True`; maintainers may want to align that benchmark reference too.

## Evidence (run folders)

- `runs/03-core-banking-transaction-ledger/20261124-200452/` -- `02-readiness.json` Q04 cold answer is the RU shape; `events.jsonl` shows `load_skill documentdb-connection` followed by writing `src/db.js` with `retryWrites: true`; `app/src/db.js` line 23.
- `runs/05-shopping-cart-with-real-time-inventory/20261124-183232/` -- `app/src/db.js` line 22 `retryWrites: true`; the audit records it as a choice, not a defect.
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/02-readiness.json` -- Q04 cold answer: `mongodb://...mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb...`; grounded answer cites the azure-deployment skill's `retrywrites=false`.
- `runs/18-chargeback-dispute-multi-agent/20261124-192501/app/.env.example` -- shipped `.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb` (placeholder credentials only).
- `runs/05-churn-prediction-pipeline/20261124-203754/app/.env.example` -- same RU-style URI shipped to the end user.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

## Verification

### 1. Already covered? -- confirmed (not covered in the target)

- Grep of `skills/` and `knowledge-base/` in the clone (commit 4f41c15, 2026-11-23) confirms every line the draft cites: `skills/connection/SKILL.md:60` ends `...&retryWrites=true` with no `maxIdleTimeMS`; `skills/security/security-tls-required.md:26` `retryWrites: true`; `skills/driver/driver-singleton-client.md:26` `{ maxPoolSize: 50, retryWrites: true }`; `skills/local-deployment/local-env-driven-config.md:68` and `skills/security/security-entra-rbac.md:15` use `.mongocluster.documentdb.azure.com`; `skills/azure-deployment/SKILL.md:288-291` is the only place with `retrywrites=false&maxIdleTimeMS=120000`.
- No file in the kit mentions `globaldb`, `10255`, `ssl=true` or `.mongo.cosmos.azure.com`, so the RU-product callout does not exist.
- Open PR #14 (`gh pr view 14 -R Azure/documentdb-agent-kit`, state OPEN, "docs(security): expand RBAC skill from the Entra ID Learn article") modifies `skills/security/security-entra-rbac.md` and its diff changes the suffix to `.mongocluster.cosmos.azure.com` and adds `retryWrites: false` examples -- the draft's exclusion of that file is correct. #14 does not touch the four files in this PR.
- Learn already publishes the canonical string (quickstart-nodejs, quickstart-python, how-to-connect-mongo-shell show `retrywrites=false&maxIdleTimeMS=120000`), which is why the fix belongs in the kit, not Learn.

### 2. Is the premise true? -- confirmed, with one supporting claim corrected

- True: the published mongoClusters string is `mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` (https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-mongo-shell, https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs). `.mongocluster.documentdb.azure.com` is not a valid suffix. `replicaSet=globaldb`, `ssl=true`, port 10255 and `.mongo.cosmos.azure.com` belong to Cosmos DB for MongoDB (RU). The kit is internally inconsistent as described.
- Corrected: the draft asserted "Azure DocumentDB does not support retryable writes, and leaving the driver default causes connection or write errors", and proposed copying that sentence into the connection skill. Authoritative sources do not support it. The Learn Mongoose quickstart (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-mongoose) says the sample "sets retryWrites=false" and that this "isn't presented as a service requirement; verify support and requirements for your target deployment". The open-source engine (github.com/documentdb/documentdb) has `pg_documentdb/src/commands/retryable_writes.c` and a `retryable_writes` table. Learn "Reliability in Azure DocumentDB" (https://learn.microsoft.com/en-us/azure/reliability/reliability-documentdb) tells customers to configure driver retry settings. The body now justifies the change as "match the published portal/CLI string" and adds item 5, which softens the unsupported claim in `skills/azure-deployment/SKILL.md:291`. The "why it matters" no longer claims writes will fail.
- Corrected: "no other file in the repo uses retryWrites=true" -- `benchmarks/documentdb-sdk-skills/tasks/orders-api-python/environment/reference/app.py` sets `retryWrites=True`; the claim is now scoped to `skills/` and `knowledge-base/` and the benchmark is mentioned.
- Corrected counts: a recount over `runs/` (excluding node_modules/venv) gives 19 run folders with `retryWrites: true`/`=true` in app code or `.env.example` and 24 `.env.example` files with `globaldb` or `:10255` (draft said 15 and 21). The evidence lines in `03-core-banking.../app/src/db.js:23` and `05-shopping-cart.../app/src/db.js:22` and the `load_skill documentdb-connection` event were confirmed. The audit recommending `retryWrites=true&retryReads=true` is in `runs/11-preference-center-consent-store/20261124-204614/05-audit.md`.

### 3. Maintainer skeptic -- confirmed

As maintainer of Azure/documentdb-agent-kit I would accept this. It names exact files and lines, the edits are small, it removes an internal contradiction in a skill that fires on every `connect()`, it is specific to Azure DocumentDB versus Cosmos DB RU, and it avoids conflicting with open PR #14. With the corrected rationale it no longer asserts an undocumented service limitation.

## Finding ids

F0071, F0214, F0348, F0556, F0763, F0792, F0846, F0916, F1073, F1101, F1486, F1716, F1921, F1950, F2016, F2051, F2324, F2425, F2745, F2804, F3071
