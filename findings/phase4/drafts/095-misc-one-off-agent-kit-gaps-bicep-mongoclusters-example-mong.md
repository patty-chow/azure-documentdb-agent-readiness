---
title: "driver skill: add a \"transactions with sessions\" rule (Mongoose/Node/PyMongo), plus a one-line mongoClusters-vs-databaseAccounts note in azure-deployment"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 3
findings: 3
bucket: kit-doc-gap
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# driver skill: add a "transactions with sessions" rule, plus a one-line mongoClusters-vs-databaseAccounts note

## What happens today

`skills/driver/` has one rule (`driver-singleton-client`). Nothing in `skills/` shows how to run a multi-document transaction on Azure DocumentDB: `grep -ri transaction skills/` finds only a one-line bullet in `natural-language-querying/SKILL.md` ("Azure DocumentDB supports multi-document transactions") and the sharding notes about cross-shard transactions. There is no example of `startSession()` / `withTransaction()`, no mention that the session must be passed to every operation, and no mention of the service's **30-second maximum transaction lifetime** (Learn: limitations#mongodb-execution-limitations). Microsoft Learn does cover the basics (how-to-transactions, and the "Mongoose on Azure DocumentDB" table in the Mongoose tutorial), but the kit, which is what agents load during builds, does not point to them.

In an experiment that ran gpt-5-mini with this kit plus the DocumentDB/Azure/Learn MCP servers over 100 sample prompts, several samples' audits flagged the missing transaction recipe as a doc gap (including 03-core-banking-transaction-ledger, 07-multi-currency-ledger and 16-multi-touch-attribution-model). The audit stage classified the agents' transaction practice as `prior_knowledge_only`: they reasoned from generic MongoDB memory. In run 07 the builder designed "transactionally-protected transaction posting" and then produced no code for it; the audit's smallest fix was "start a Mongoose session, use session.withTransaction, pass { session } to all Mongoose operations". In run 03-core-banking the builder got it right but the audit still asked for a compact snippet showing session passing and retry semantics in one place.

## Why it matters

Agents that forget `{ session }` on one call produce writes that silently fall outside the transaction, i.e. non-atomic ledgers that look correct in tests. Agents that wrap `withTransaction` in their own retry loop can double-apply side effects, because the driver already retries the callback. And agents that run a long aggregation inside the transaction hit the 30-second lifetime, which they cannot know from MongoDB memory. The driver skill is where every build that instantiates a client already looks (run 07's events show it loading `documentdb-driver` repeatedly), so a rule here is on the path the agent actually walks.

## Proposed change

### 1. New file `skills/driver/driver-transactions-session.md`

Same template as `driver-singleton-client.md`:

````markdown
# driver-transactions-session

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB supports multi-document (and cross-shard) transactions through
the standard driver session API. Three things matter that agents often miss:
the session must be passed to **every** operation or that write silently lands
outside the transaction; the service enforces a **30-second maximum
transaction lifetime**; and `withTransaction()` already retries the callback on
`TransientTransactionError` and the commit on `UnknownTransactionCommitResult`,
so the callback must be idempotent and must not be wrapped in a second retry loop.

## Incorrect

```javascript
const session = await mongoose.startSession();
await session.withTransaction(async () => {
  await Transaction.create({ ...entry });                 // 🔥 no session: outside the txn
  await Account.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  await heavyReport.aggregate([...]).session(session);    // 🔥 long work: risks the 30 s lifetime
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

## Correct (Node driver / PyMongo)

```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await ledger.insertOne(entry, { session });
    await accounts.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  });
} finally { await session.endSession(); }
```

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
- Make the callback idempotent (e.g. a unique `idempotencyKey` index) because
  the driver may run it more than once.
- Use the connection string the portal gives you (`retrywrites=false`); the
  convenient-transaction retry in `withTransaction` is independent of
  retryable single writes.
- Only if you use explicit `startTransaction()/commitTransaction()` do you need
  your own bounded retry on the `TransientTransactionError` /
  `UnknownTransactionCommitResult` labels.

## References

- https://learn.microsoft.com/azure/documentdb/how-to-transactions
- https://learn.microsoft.com/azure/documentdb/limitations#mongodb-execution-limitations (30 s lifetime)
- https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#mongoose-on-azure-documentdb
````

### 2. `skills/driver/SKILL.md`

Add to the Rules list:

```markdown
- [driver-transactions-session](driver-transactions-session.md) — Multi-document transactions: `startSession()` + `withTransaction()`, pass `{ session }` to every operation, keep under the 30 s lifetime, do not add a second retry loop.
```

and extend the front-matter `description` with "...multi-document transactions with sessions (Mongoose, Node, Python)...". Update the `driver/` row in `docs/SKILLS.md` from "singleton client, pooling" to "singleton client, pooling, transactions".

### 3. One sentence in `skills/azure-deployment/SKILL.md`

The requested `mongoCluster.bicep` already exists (`examples/azure-deployment/main.bicep`, `skills/azure-deployment/references/bicep-cluster-template.md`, both `Microsoft.DocumentDB/mongoClusters@2025-09-01`), so the only missing piece from the IaC finding is the disambiguation. Add after the intro paragraph:

```markdown
> Azure DocumentDB clusters are **`Microsoft.DocumentDB/mongoClusters`** (CLI: `az documentdb mongocluster`). Do not generate `Microsoft.DocumentDB/databaseAccounts` templates or `az cosmosdb` commands — those create Azure Cosmos DB (including the RU-based MongoDB API), a different service. The checked-in `examples/azure-deployment/main.bicep` is the correct resource.
```

(Discoverability of the existing Bicep is a larger problem: many sample audits asked for an IaC example that the kit already ships, and only 2 of 100 runs' event logs show the agent opening `bicep-cluster-template.md` or `examples/azure-deployment/`. That likely deserves its own issue and is not addressed here.)

### Not included: PII / redaction opt-in for LLM-bound client data

Finding F1742 asks for a rule that samples sending client data to third-party LLMs either redact first or gate it behind an explicit env flag with a README warning. That is a sample-gallery convention rather than a DocumentDB skill, so it is left out of this PR. If it is wanted in the kit, the pattern already exists in `skills/natural-language-querying/SKILL.md` ("Safety: Handling Sensitive Data in Sampled Documents") and could be referenced from a sample-authoring guide.

### Related inconsistency (not fixed here)

`skills/connection/SKILL.md` (line ~60), `skills/security/security-tls-required.md` and `driver-singleton-client.md` show `retryWrites=true`, while `skills/azure-deployment/SKILL.md` (line ~291) says the service does not support retryable writes and the portal string uses `retrywrites=false`. The Learn Mongoose tutorial says its `retryWrites=false` setting is a sample choice, not a statement that the service requires it. Worth a separate pass so the kit says one thing.

## Evidence (run folders under azure-documentdb-agent-readiness/runs/)

- `07-multi-currency-ledger/20261124-190814/05-audit.json` — practice `prior_knowledge_only`, "no DocumentDB-hosted Mongoose recipe found" (finding F1147)
- `07-multi-currency-ledger/20261124-190814/02-readiness.json` — transaction lifetime unknown
- `03-core-banking-transaction-ledger/20261124-200452/doc-gaps.md` — Mongoose transactions + session usage, transaction retry semantics
- `16-multi-touch-attribution-model/20261124-205342/doc-gaps.md` — transaction and single-document preference
- `03-next-best-action-multi-agent/20261124-203319/doc-gaps.md` — IaC example asked for although the kit ships one (finding F0446)
- `10-wealth-management-rag-portal/20261124-201449/doc-gaps.md` — PII-handling rule request (finding F1742; declined for this repo, see above)

## Verification

### 1. Already covered? — confirmed

The kit does not cover transactions. `skills/driver/` contains only `SKILL.md` and `driver-singleton-client.md`. `grep -rni transaction skills knowledge-base` returns only `skills/natural-language-querying/SKILL.md:258` ("Transactions — Azure DocumentDB supports multi-document transactions"), sharding notes (`sharding-logical-vs-physical.md:45,88-90`) and an HA note; no session/`withTransaction` usage and no 30-second lifetime. `docs/SKILLS.md:24` describes `driver/` as "singleton client, pooling".
The Bicep part of the theme IS already covered: `examples/azure-deployment/main.bicep:53` and `skills/azure-deployment/references/bicep-cluster-template.md:57` define `Microsoft.DocumentDB/mongoClusters@2025-09-01`, and `skills/azure-deployment/SKILL.md` front matter names `Microsoft.DocumentDB/mongoClusters`; no file mentions `databaseAccounts` or `az cosmosdb`, so only the disambiguation sentence is new. The PII part: `skills/natural-language-querying/SKILL.md:13` has "Safety: Handling Sensitive Data in Sampled Documents" (query sampling, not sample-app LLM calls).
Learn already covers the transaction basics (https://learn.microsoft.com/en-us/azure/documentdb/how-to-transactions: "Pass the session in the options for every operation that belongs to the transaction" and "The callback can run more than once if the driver retries the transaction"), which is why the new rule links to it; the gap is in the kit, which is where agents look.

### 2. Is the premise true? — confirmed

- 30-second lifetime: https://learn.microsoft.com/en-us/azure/documentdb/limitations — "Maximum transaction lifetime: 30 seconds."
- Session passing and `withTransaction` retry/idempotency: how-to-transactions (quotes above).
- Mongoose: https://learn.microsoft.com/en-us/azure/documentdb/tutorial-nodejs-mongoose ("Mongoose on Azure DocumentDB" table) — "Use Mongoose sessions and pass the session to each operation ... 30-second maximum transaction lifetime"; anchor `#mongoose-on-azure-documentdb` exists. Same page: `retryWrites=false` "is a sample, not a statement that Azure DocumentDB requires retryable writes to be disabled".
- `Model.create` takes options only in array form; `withTransaction` retries on `TransientTransactionError`/`UnknownTransactionCommitResult` — standard MongoDB driver/Mongoose behaviour, consistent with the Learn note that the callback can run more than once.
- Resource type `Microsoft.DocumentDB/mongoClusters` and CLI `az documentdb mongocluster` match the known facts; `databaseAccounts` is Cosmos DB.
Edits applied: removed a garbled clause in the original proposed change ("never `Microsoft.DocumentDB/mongoClusters` via `az cosmosdb`"); replaced unverified counts ("19 prompts", "6 distinct samples", "49 of 100", "loaded 9 times") with wording supported by the evidence checked (transaction doc gaps confirmed in the run folders of 03-core-banking, 07, 12, 15, 16 and 20; 2 of 100 event logs open the Bicep reference; run 07 loads the driver skill repeatedly); "exceeds" softened to "risks" the 30 s lifetime; added that Learn covers the basics and the kit should link to it; added `security-tls-required.md` to the retryWrites inconsistency list.

### 3. Maintainer skeptic — confirmed

Names concrete files (`skills/driver/driver-transactions-session.md` new, `skills/driver/SKILL.md`, `docs/SKILLS.md`, `skills/azure-deployment/SKILL.md`), follows the existing rule template exactly, is DocumentDB-specific (30 s lifetime, Learn links, mongoClusters vs databaseAccounts), and correctly drops the out-of-scope PII convention (sample-gallery / harness concern, not a kit skill). Acceptable as a PR with the edits above.

## Finding ids

- F0446
- F1147
- F1742
