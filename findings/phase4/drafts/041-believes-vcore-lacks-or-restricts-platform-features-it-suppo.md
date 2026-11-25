---
title: "Agent Kit: add runnable MONGODB-OIDC examples, a change-streams rule and a transactions rule so builders stop carrying RU-API/stale-ecosystem priors"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 19
findings: 19
bucket: confusion-sample-specific
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add runnable MONGODB-OIDC examples, a change-streams rule and a transactions rule (closes three vCore-feature blind spots)

## What happens today

When an AI agent builds an app against Azure DocumentDB with this kit installed, it still carries three priors from Azure Cosmos DB for MongoDB (RU) and the pre-vCore ecosystem:

1. **Auth.** Agents plan username/password-only or "account primary key" code, propose that the app `createUser`s its own DB users at startup, or treat Microsoft Entra ID as a control-plane-only / "too exotic for a sample" feature. The only Entra example in the kit (`skills/security/security-entra-rbac.md`) is a stub: `authMechanism: "MONGODB-OIDC", // or the current documented mechanism` with `// credentialProvider: Azure Managed Identity` left as a comment. The only concrete `authMode: "entra"` lives in the MCP connection-profile docs (`skills/mcp-setup/SKILL.md`), which is for the MCP server, not application drivers. `skills/connection/SKILL.md` says only "Default mechanism: `SCRAM-SHA-256`" and "Credentials are managed through the Azure portal", and never links to the security rule. (Its sample connection string also uses `retryWrites=true`; Learn's recommended setting is `retrywrites=false`.)
2. **Change streams.** None of the 17 skills mentions `watch()`, change streams, multishard change streams or resume tokens. Agents either avoid `collection.watch()` as "unsupported / RU-limited" or plan cluster-wide streams without knowing that multishard clusters need the *Change streams for multishard clusters* feature (preview) enabled, and without persisting resume tokens.
3. **Transactions.** Agents assume the RU-API restriction on multi-document transactions (single partition / shard key) and start denormalising schemas to satisfy it. The kit's only statements that cross-shard transactions are supported are in `skills/sharding/sharding-logical-vs-physical.md` (lines 45 and 88-90) and one bullet in `skills/natural-language-querying/SKILL.md` (line 258), files a builder of an *unsharded* ledger or billing sample never loads. `driver`, `data-modeling` and `connection` are silent.

The fourth prior in this cluster (Motor as the async Python client) is already corrected by `skills/connection/SKILL.md` lines 45-49 ("not Motor", `AsyncMongoClient`, deprecation). No change proposed there.

## Why it matters

In a 100-sample readiness experiment (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), **19 distinct samples** hit this theme in the cold quiz: 9 on auth, 3 on change streams, 2 on transactions, 5 on Motor. Concrete consequences in the builds:

- `16-subscription-billing-engine` answered *wrong* (confused with the RU API): it claimed transactions require all documents to be in the same logical partition and planned to force charge events and subscription records onto one partition key. Only the grounding pass against Learn corrected it.
- `16-loyalty-points-ledger` logged a **high** doc gap: no copy-paste Node + Entra example found, so the builder shipped SCRAM credentials and wrote in the README that Entra ID was not demonstrated.
- `08-interest-rate-scenario-modeler` planned `pymongo.MongoClient(os.environ['DOCUMENTDB_URI'])` as the only code path; `20-provider-directory-semantic-search` planned "DOCUMENTDB_URI with primary key" (RU terminology).
- `09-trade-settlement-tracker` and `05-appointment-scheduling-assistant` designed change-stream consumers with no multishard gate and no resume-token persistence.

Learn already has runnable code for all three (the RBAC how-to has Python/TypeScript/C# OIDC callbacks; the change-streams page has resume-token consumers and the multishard enablement steps; the sharding page states transactions span logical and physical shards). The kit should surface that content in the skills builders actually load, instead of a hedged stub or nothing.

## Proposed change (3 files edited/added, 3 index lines)

### 1. `skills/security/security-entra-rbac.md` - make the Entra example runnable

Replace the hedged "Correct" block with:

````markdown
## Correct

Prerequisites (done once by an operator on the cluster, **not** by the application at startup):
1. Enable Microsoft Entra ID as an allowed authentication mode on the cluster: portal > Authentication, or
   `az documentdb mongocluster update ... --auth-allowed-modes NativeAuth MicrosoftEntraID`
   (keep `NativeAuth` until Entra principals are verified to connect).
2. Register the app's principal (managed identity, service principal or user):
   - administrative access: `az documentdb mongocluster microsoft-entra-user assign` (or the ARM/Bicep
     `Microsoft.DocumentDB/mongoClusters/users` resource);
   - least-privilege (read-only / read-write) access: an admin runs the MongoDB `createUser` database
     command for the principal's object ID. The ARM `users` resource supports administrative registration only.
   Exact commands: https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control

Then connect with `authMechanism=MONGODB-OIDC` and a token from `azure-identity` for the scope
`https://ossrdbms-aad.database.windows.net/.default`. `DefaultAzureCredential` covers `az login`
locally and managed identity in Azure, so the same code runs in both places. Keep the recommended
options `tls=true`, `retryWrites=false`, `maxIdleTimeMS=120000`. Use the `<cluster>.global.mongocluster.cosmos.azure.com`
host if the cluster has a cross-region replica; otherwise either host works.

**Python (PyMongo 4.9+, works with `AsyncMongoClient` too):**
```python
import os
from azure.identity import DefaultAzureCredential
from pymongo import MongoClient
from pymongo.auth_oidc import OIDCCallback, OIDCCallbackContext, OIDCCallbackResult

SCOPE = "https://ossrdbms-aad.database.windows.net/.default"

class AzureIdentityTokenCallback(OIDCCallback):
    def __init__(self, credential):
        self.credential = credential
    def fetch(self, context: OIDCCallbackContext) -> OIDCCallbackResult:
        return OIDCCallbackResult(access_token=self.credential.get_token(SCOPE).token)

client = MongoClient(
    f"mongodb+srv://{os.environ['CLUSTER_NAME']}.mongocluster.cosmos.azure.com/",
    tls=True,
    retryWrites=False,
    maxIdleTimeMS=120000,
    authMechanism="MONGODB-OIDC",
    authMechanismProperties={"OIDC_CALLBACK": AzureIdentityTokenCallback(DefaultAzureCredential())},
)
```

**Node.js (mongodb 6.x, `@azure/identity`):**
```javascript
const { MongoClient } = require("mongodb");
const { DefaultAzureCredential } = require("@azure/identity");

const SCOPE = "https://ossrdbms-aad.database.windows.net/.default";
const credential = new DefaultAzureCredential();

const client = new MongoClient(`mongodb+srv://${process.env.CLUSTER_NAME}.mongocluster.cosmos.azure.com/`, {
  tls: true,
  retryWrites: false,
  maxIdleTimeMS: 120000,
  authMechanism: "MONGODB-OIDC",
  authMechanismProperties: {
    OIDC_CALLBACK: async () => {
      const { token, expiresOnTimestamp } = await credential.getToken(SCOPE);
      // expiresOnTimestamp is in milliseconds
      return { accessToken: token, expiresInSeconds: Math.floor((expiresOnTimestamp - Date.now()) / 1000) };
    },
    ALLOWED_HOSTS: ["*.azure.com"],
  },
});
```

**When to fall back to SCRAM-SHA-256:** the cluster does not have Entra enabled, the runtime has no Azure identity (e.g. a CI box outside Azure without `az login`), or the client is a third-party tool that cannot run an OIDC callback. In that case have an admin create a least-privilege secondary user (below) and put the URI in `DOCUMENTDB_URI`; do not use the built-in admin user and do not have the app create users at startup.
````

Keep the existing secondary-user snippet and references; add the Learn link to *Manage secondary Microsoft Entra ID identities* (same page) next to the existing link.

### 1b. `skills/connection/SKILL.md` - cross-link from the Authentication section

Replace the "### Authentication" bullets ("Default mechanism: `SCRAM-SHA-256`" / "Credentials are managed through the Azure portal") with:

```markdown
### Authentication

- `SCRAM-SHA-256` with a native database user (default). The built-in admin is created with the cluster; secondary users are created by an admin with the `createUser` command, not by the application at startup. There are no account keys.
- `MONGODB-OIDC` with Microsoft Entra ID (managed identity / service principal / user) is supported on the data plane. Runnable Python and Node examples: see [security-entra-rbac](../security/security-entra-rbac.md).
```

While editing this file, change `retryWrites=true` in the "Connection String Format" example to `retrywrites=false&maxIdleTimeMS=120000`, matching the Learn connection guidance.

### 2. New rule `skills/data-modeling/model-change-streams.md` (+ one line in `data-modeling/SKILL.md` Rules list)

````markdown
# model-change-streams

**Category:** Data modeling · **Priority:** MEDIUM

## Why it matters

Azure DocumentDB supports MongoDB change streams through the standard driver `watch()` API on a collection or database. Agents frequently assume change streams are missing or RU-API-limited and fall back to polling, or open streams that silently miss events. For a correct consumer:

1. **Multishard clusters need a feature enabled.** On a cluster with more than one physical shard, enable *Change streams for multishard clusters* (preview) under cluster > Settings > **Features** before relying on `watch()`. It cannot be enabled while *Rebalancer for multishard clusters* is on. Single-shard clusters need nothing. Multishard streams don't preserve global event ordering.
2. **Persist the resume token.** Store `change._id` (the resume token) durably after each processed event and reopen with `resumeAfter`; to replay from a point in time use `startAtOperationTime`. A consumer that keeps the token only in memory re-processes or loses events on restart.
3. **Know the retention window.** Standard streams read the active change log (400 MB). Historical change streams can resume or replay from archived logs via PITR integration, up to 35 days or the cluster's creation, whichever is earlier; run large historical replays during low traffic.
4. **Handle topology events.** Reinitialise the cursor after a failover (resume still works). Moving a cluster from single-shard to multishard breaks resumability, so plan a rebuild (full scan + new stream) for that case.

## Incorrect
```javascript
// In-memory cursor, no resume handling, assumes the stream works on any cluster topology
const stream = db.collection("trades").watch();
for await (const ev of stream) handle(ev);
```

## Correct
```javascript
const checkpoints = db.collection("_checkpoints");
const saved = await checkpoints.findOne({ _id: "trades" });
const stream = db.collection("trades").watch(
  [{ $match: { operationType: { $in: ["insert", "update"] } } }],
  { fullDocument: "updateLookup", ...(saved && { resumeAfter: saved.token }) }
);
for await (const ev of stream) {
  await handle(ev);
  await checkpoints.updateOne({ _id: "trades" }, { $set: { token: ev._id } }, { upsert: true });
}
```

## References
- https://learn.microsoft.com/azure/documentdb/change-streams
````

### 3. New rule `skills/driver/driver-transactions.md` (+ one line in `driver/SKILL.md` Rules list)

````markdown
# driver-transactions

**Category:** Driver · **Priority:** MEDIUM

## Why it matters

Azure DocumentDB supports multi-document ACID transactions through the standard driver session API (`startSession()` + `withTransaction`). **Transactions are not limited to one logical shard**: documents in different collections and on different logical or physical shards can participate in one transaction. This differs from Azure Cosmos DB for MongoDB (RU), whose multi-document transactions are restricted (single partition / unsharded collection); agents carrying that rule add needless denormalisation.

Cross-shard transactions cost more than single-shard ones, so when a collection is sharded, choose a shard key that keeps the documents of one business operation together. Do not let that concern drive the schema of an unsharded collection.

## Incorrect
```javascript
// Forcing charge events into the subscription document "so the transaction stays in one partition"
await subscriptions.updateOne({ _id: subId }, { $push: { charges: charge } });
```

## Correct
```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await subscriptions.updateOne({ _id: subId }, { $inc: { balance: -charge.amount } }, { session });
    await charges.insertOne({ ...charge, subId, idempotencyKey }, { session });
  });
} finally {
  await session.endSession();
}
```
```python
def apply_charge(s):
    subscriptions.update_one({"_id": sub_id}, {"$inc": {"balance": -amount}}, session=s)
    charges.insert_one({**charge, "subId": sub_id}, session=s)

with client.start_session() as s:
    s.with_transaction(apply_charge)
```

Keep transactions short. `withTransaction` commits on success and may run the callback more than once on transient errors, so keep the callback free of non-idempotent external side effects and use an idempotency key on inserts.

## References
- https://learn.microsoft.com/azure/documentdb/how-to-transactions
- https://learn.microsoft.com/azure/documentdb/partitioning (transactions across logical and physical shards)
- Related: [sharding-logical-vs-physical](../sharding/sharding-logical-vs-physical.md) §4
````

Update the `skills/driver/SKILL.md` front-matter description to mention transactions so the skill is selected for ledger/billing prompts, e.g. append "multi-document transactions via sessions".

## Evidence (run folders from the experiment; no connection strings)

- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json` - confusions[S02], outcome `wrong`, confused_with `azure_cosmos_db_for_mongodb_ru`
- `runs/16-loyalty-points-ledger/20261124-184937/doc-gaps.md` - [high] "Node.js Mongoose + Microsoft Entra ID example"; builder shipped SCRAM instead
- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` - confusions[S05], change stream with no multishard gate / resume handling
- `runs/08-interest-rate-scenario-modeler/20261124-201113/02-readiness.json` - confusions[S01], `pymongo.MongoClient(DOCUMENTDB_URI)` as the only path
- `runs/05-appointment-scheduling-assistant/20261124-193733/02-readiness.json` - confusions[S05], change streams for agent memory sync

Other samples in the theme: 06-collateral-management-store, 07-customer-review-sentiment-pipeline, 07-lab-results-aggregator, 09-crypto-wallet-activity-analyzer, 11-care-gap-identification-pipeline, 13-chronic-disease-risk-predictor, 18-sanctions-list-screening-agent, 19-insider-threat-detection-pipeline, 20-provider-directory-semantic-search (auth); 07-voice-of-customer-sentiment-hub, 09-clinical-notes-de-identification, 10-expense-report-auto-categorizer, 16-population-health-dashboard-backend, 17-ai-survey-response-analyzer (Motor, already handled by connection/SKILL.md).

## Notes for reviewers

- The OIDC snippets follow the "Connect using Microsoft Entra ID in code" section of the Learn RBAC how-to (same scope, callback shape, `retryWrites=false`). The Node callback computes `expiresInSeconds` from `expiresOnTimestamp` in milliseconds.
- CLI names (`az documentdb mongocluster update --auth-allowed-modes`, `az documentdb mongocluster microsoft-entra-user assign`) are taken from the same page; please re-check against the current `documentdb` CLI extension before merge.

## Verification

### 1. Already covered? - partially_covered

- **Agent kit, auth:** `skills/security/security-entra-rbac.md` recommends Entra + RBAC and links the Learn RBAC page, but its code is a stub ("`authMechanism: "MONGODB-OIDC", // or the current documented mechanism`", credential provider as a comment). `skills/connection/SKILL.md` Authentication section says only "Default mechanism: `SCRAM-SHA-256`" and has no cross-link. `authMode: "entra"` appears only in `skills/mcp-setup/SKILL.md` (MCP server profiles).
- **Agent kit, change streams:** grep for `change.?stream|watch\(|resume.?token|multishard` across `skills/` and `knowledge-base/` finds no change-stream content (only unrelated "multi-shard" topology lines in sharding/high-availability).
- **Agent kit, transactions:** only `skills/sharding/sharding-logical-vs-physical.md` line 45 ("Cross-shard transactions (across both logical and physical shards) are supported") and lines 88-90, plus `skills/natural-language-querying/SKILL.md` line 258. No driver/data-modeling rule.
- **Agent kit, Motor:** already covered by `skills/connection/SKILL.md` lines 45-49 ("Use PyMongo's native `AsyncMongoClient` (PyMongo 4.9+), **not** Motor"); draft correctly proposes nothing.
- **Learn:** the content exists on Learn (https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control has Python/TypeScript/C# OIDC callback code; https://learn.microsoft.com/en-us/azure/documentdb/change-streams has resume-token consumers and a "Multi-shard change streams (preview)" section; https://learn.microsoft.com/en-us/azure/documentdb/partitioning says "the service doesn't limit transactions to the scope of a logical shard"). So the ask is a kit gap (the content is not where the agent looked), not a Learn gap.

### 2. Premise true? - confirmed (details corrected in the body)

Core claims hold: Entra ID data-plane auth via `MONGODB-OIDC` with scope `https://ossrdbms-aad.database.windows.net/.default` and `DefaultAzureCredential` (Learn RBAC page, "Connect using Microsoft Entra ID in code"); change streams via `watch()` with `resumeAfter`/`startAtOperationTime` and a multishard preview feature (Learn change-streams page); transactions across logical and physical shards (Learn partitioning page; how-to-transactions shows `startSession()`/`withTransaction()`). Corrections applied to the body:
- The draft omitted `retryWrites` from the OIDC snippets on purpose; Learn's snippets and connection table set `retrywrites=false` (and `maxIdleTimeMS=120000`), so the snippets now include them. Also flagged `retryWrites=true` in `connection/SKILL.md`.
- The draft's "`az documentdb mongocluster user`" for creating users is replaced: Learn says admin Entra principals are registered via ARM (`az documentdb mongocluster microsoft-entra-user assign`, Bicep/Terraform `mongoClusters/users`), while nonadministrative identities and secondary native users are created with the MongoDB `createUser` command ("The ARM ... users endpoint supports administrative registration only").
- "Supported on the data plane for all official drivers" was an overclaim; changed to "supported on the data plane" with linked examples.
- Change-streams enablement location corrected from "portal > Preview features" to cluster > Settings > Features; added the Rebalancer conflict, the 400 MB active change log, the 35-day PITR-backed historical window, cursor reinitialisation after failover, broken resumability on single-to-multishard transition, and no global ordering on multishard (all from the Learn Limitations / Multi-shard sections), replacing the vague "check the Learn page for the current window".
- Node `ALLOWED_HOSTS` aligned with Learn (`*.azure.com`); Python transaction example rewritten as a named callback.

### 3. Maintainer skeptic - confirmed

Names exact files in Azure/documentdb-agent-kit (`skills/security/security-entra-rbac.md`, `skills/connection/SKILL.md`, new `skills/data-modeling/model-change-streams.md`, new `skills/driver/driver-transactions.md`, two SKILL.md index lines and one description), follows the kit's rule format (Why it matters / Incorrect / Correct / References), is DocumentDB-specific, and replaces an admittedly hedged stub with code that mirrors Learn. I would accept it with the edits above; the right repo is the agent kit (Learn already has the content, and the MCP server is unrelated).

## Finding ids

F0705, F1083, F1567, F0859, F1009, F1269, F1411, F1170, F1378, F1632, F1763, F2196, F2692, F2785, F3120, F3268, F3468, F2753, F2815
