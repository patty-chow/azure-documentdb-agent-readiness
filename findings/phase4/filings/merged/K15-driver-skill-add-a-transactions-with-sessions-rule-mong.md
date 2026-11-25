---
id: K15
title: "driver skill: add a transactions-with-sessions rule (Mongoose, Node, PyMongo)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P2
sample_count: 3
member_drafts:
  - 095-misc-one-off-agent-kit-gaps-bicep-mongoclusters-example-mong.md
open_questions: 3
---

# driver skill: add a transactions-with-sessions rule (Mongoose, Node, PyMongo)

## What happens today

`skills/driver/` has a single rule, `driver-singleton-client.md`. Nothing in `skills/` shows how to run a multi-document transaction on Azure DocumentDB: `grep -rni transaction skills knowledge-base` finds only one bullet in `skills/natural-language-querying/SKILL.md` ("Azure DocumentDB supports multi-document transactions"), plus sharding and HA notes. There is no `startSession()` / `withTransaction()` example, no note that the session must be passed to every operation, and no mention of the service's 30-second maximum transaction lifetime (documented on the Learn limitations page). Learn covers the basics (how-to-transactions, and the "Mongoose on Azure DocumentDB" table in the Mongoose tutorial), but the kit, which is what coding agents load during a build, neither covers them nor links to them. `docs/SKILLS.md` describes `driver/` as "singleton client, pooling".

Separately, `skills/azure-deployment/` already ships a correct `Microsoft.DocumentDB/mongoClusters` Bicep template, but nothing tells an agent not to generate `Microsoft.DocumentDB/databaseAccounts` or `az cosmosdb` instead.

## Why it matters

We ran an agent (gpt-5-mini with this kit plus the DocumentDB, Azure and Learn MCP servers) over 100 sample app prompts. This PR rests on 3 recorded findings from 3 samples: 07-multi-currency-ledger (missing transaction recipe), 03-next-best-action-multi-agent (asked for an IaC example the kit already ships, addressed by the disambiguation note below) and 10-wealth-management-rag-portal (a PII-redaction request, left out of scope). In 07 the audit classified the agent's transaction practice as prior MongoDB knowledge only. When checking the evidence, the draft's verification also found transaction doc gaps in the run folders of 03-core-banking-transaction-ledger, 12-clv-prediction-pipeline, 15-supplier-po-management, 16-multi-touch-attribution-model and 20-provider-directory-semantic-search; those are not separate recorded findings and are not counted in the sample count. In 07 the agent designed "transactionally-protected" posting and then wrote no transaction code; the audit's smallest fix was to start a Mongoose session, use `withTransaction`, and pass `{ session }` to every operation. In 03-core-banking the agent got it right, but its doc-gaps note still asked for one compact snippet. Counts are from one experiment run and may shift on a re-run.

The failure modes are quiet: a write without `{ session }` lands outside the transaction and the ledger looks fine in tests; a hand-written retry loop around `withTransaction` can double-apply side effects because the driver already retries the callback; and long work inside the transaction risks the 30-second lifetime, which no MongoDB prior teaches. The driver skill is already on the agent's path (run 07 loads `documentdb-driver` repeatedly), so a rule there will be read.

## Proposed change

### 1. New file `skills/driver/driver-transactions-session.md`

Same template as `driver-singleton-client.md`:

````markdown
# driver-transactions-session

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB supports multi-document transactions through the standard
driver session API. Three things agents often miss: the session must be passed
to **every** operation, or that write silently lands outside the transaction;
the service enforces a **30-second maximum transaction lifetime**; and
`withTransaction()` can run the callback more than once, so the callback must be
idempotent and must not be wrapped in a second retry loop.

## Incorrect

```javascript
const session = await mongoose.startSession();
await session.withTransaction(async () => {
  await Transaction.create({ ...entry });                 // WRONG: no session, outside the txn
  await Account.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  await heavyReport.aggregate([...]).session(session);    // WRONG: long work risks the 30 s lifetime
});
```

## Correct (Mongoose)

```javascript
const session = await mongoose.startSession();
try {
  await session.withTransaction(async () => {
    // Model.create accepts options only in array form
    await Transaction.create([{ ...entry }], { session });
    await Account.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  });
} finally {
  await session.endSession();
}
```

## Correct (Node driver)

```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await ledger.insertOne(entry, { session });
    await accounts.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  });
} finally {
  await session.endSession();
}
```

## Correct (PyMongo)

```python
with client.start_session() as s:
    def txn(s):
        ledger.insert_one(entry, session=s)
        accounts.update_one({"_id": _id}, {"$inc": {"balance": -amt}}, session=s)
    s.with_transaction(txn)
```

Rules of thumb:
- Keep the transaction to a few documents and no aggregation; do reads and
  external calls (LLM, HTTP) before `withTransaction`, not inside it.
- Make the callback idempotent (for example a unique `idempotencyKey` index),
  because the driver may run it more than once.
- Only if you use explicit `startTransaction()` / `commitTransaction()` do you
  need your own bounded retry on the `TransientTransactionError` /
  `UnknownTransactionCommitResult` labels.

## References

- https://learn.microsoft.com/azure/documentdb/how-to-transactions
- https://learn.microsoft.com/azure/documentdb/limitations#mongodb-execution-limitations (30 s lifetime)
- https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#mongoose-on-azure-documentdb
````

### 2. `skills/driver/SKILL.md`

Add to the Rules list:

```markdown
- [driver-transactions-session](driver-transactions-session.md) — Multi-document transactions: `startSession()` + `withTransaction()`, pass `{ session }` to every operation, stay under the 30 s lifetime, no second retry loop.
```

Extend the front-matter `description` with "multi-document transactions with sessions (Mongoose, Node, Python)".

### 3. `docs/SKILLS.md`

Change the `driver/` row from "singleton client, pooling" to "singleton client, pooling, transactions".

### 4. `skills/azure-deployment/SKILL.md` (one note after the intro paragraph)

```markdown
> Azure DocumentDB clusters are **`Microsoft.DocumentDB/mongoClusters`** (CLI: `az documentdb mongocluster`). Do not generate `Microsoft.DocumentDB/databaseAccounts` templates or `az cosmosdb` commands; those create Azure Cosmos DB (including the RU-based MongoDB API), a different service. The checked-in `examples/azure-deployment/main.bicep` is the correct resource.
```

Out of scope: a PII-redaction rule for sample apps that send data to LLMs (a sample-gallery convention, not a DocumentDB skill), and the wider discoverability problem of the existing Bicep example (only 2 of 100 runs opened it), which deserves its own issue.

## Evidence

Run folders in the experiment repository (`runs/`):

- `07-multi-currency-ledger/20261124-190814/05-audit.json` (practice classified as prior knowledge only; no DocumentDB Mongoose recipe found)
- `07-multi-currency-ledger/20261124-190814/02-readiness.json` (transaction lifetime unknown to the agent)
- `03-core-banking-transaction-ledger/20261124-200452/doc-gaps.md` (Mongoose sessions, transaction retry semantics)
- `16-multi-touch-attribution-model/20261124-205342/doc-gaps.md` (transactions vs single-document updates)
- `03-next-best-action-multi-agent/20261124-203319/doc-gaps.md` (IaC example requested although the kit ships one)
- `10-wealth-management-rag-portal/20261124-201449/doc-gaps.md` (PII-redaction rule request; out of scope for this PR)

## Open questions

1. [needs SME confirmation] retryWrites. The kit currently disagrees with itself: `skills/connection/SKILL.md`, `skills/security/security-tls-required.md` and `driver-singleton-client.md` show `retryWrites=true`, while `skills/azure-deployment/SKILL.md` says the service does not support retryable writes, and the portal connection string uses `retrywrites=false`. The Learn Mongoose tutorial describes its `retryWrites=false` as a sample choice, not a service requirement. This PR deliberately says nothing about retryWrites; please give the engineering answer (supported or not, and whether it affects `withTransaction` retries) so a follow-up can make the kit consistent.
2. [needs SME confirmation] Does the engine return the standard `TransientTransactionError` and `UnknownTransactionCommitResult` error labels, so the drivers' `withTransaction` retry behaves as it does against MongoDB?
3. [needs SME confirmation] Are multi-document transactions across shards supported on sharded clusters, with the same 30-second limit? The kit's `skills/sharding/sharding-logical-vs-physical.md` already says cross-shard transactions are supported; the new rule avoids repeating the claim until confirmed.

## Source drafts

- 095-misc-one-off-agent-kit-gaps-bicep-mongoclusters-example-mong.md
