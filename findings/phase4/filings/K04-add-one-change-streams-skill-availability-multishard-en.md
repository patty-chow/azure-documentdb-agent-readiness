---
id: K04
title: "Add one change-streams skill: availability, multishard enablement, limitations and a durable resume-token consumer"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 83
member_drafts:
  - 105-change-stream-consumers-have-no-durability-resume-tokens-nev.md
  - 032-believes-vcore-change-streams-are-absent-or-crippled-like-co.md
  - 033-believes-change-streams-are-on-by-default-cluster-wide-unawa.md
  - 034-believes-azure-documentdb-change-streams-have-full-mongodb-s.md
  - 035-believes-change-stream-availability-is-gated-by-the-cluster-.md
  - 093-durable-state-patterns-change-stream-resume-tokens-workflow-.md
open_questions: 8
---

# Add one change-streams skill: availability, multishard enablement, limitations and a durable resume-token consumer

## What happens today

No skill in the kit mentions change streams. `grep -riE "change ?stream|resumeAfter|resume token|\.watch\(|startAtOperationTime|pre-?image"` over `skills/`, `docs/`, `knowledge-base/` and `AGENTS.md` (commit 4f41c15) returns nothing. The only hits are test fixtures under `scenarios/ecommerce-advanced/` (plus one README line in `scenarios/ecommerce/` pointing to them), which agents do not load as guidance. `skills/driver/` has one rule (`driver-singleton-client.md`), and `docs/SKILLS.md` describes it as "singleton client, pooling".

The Learn page [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) already covers resume tokens, historical change streams, pre-images, `updateDescription`, multishard enablement and limitations. Agents using the kit never get pointed to it, so they fall back on what they learned in training. Four wrong beliefs showed up:

- **"Not supported, use the Cosmos DB change feed."** This is the Azure Cosmos DB for MongoDB (RU) belief. It leads to polling on `updatedAt` or to a lease-collection design.
- **"Gated by `serverVersion` / compatibility level."** In fact `$changeStream` is listed as supported in the 5.0, 6.0, 7.0 and 8.0 columns of the [MQL compatibility matrix](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#operators).
- **"Works cluster-wide with no setup, like Atlas."** On multishard clusters this is wrong. Change streams there are a preview feature [needs SME confirmation] that has to be turned on under **Settings > Features > Change streams for multishard clusters**, and the toggle can't be turned on while **Rebalancer for multishard clusters** is on [needs SME confirmation].
- **"Full MongoDB semantics."** In fact global ordering across shards is not preserved, going from single-shard to multishard breaks resumability, and cursors must be reopened after failover.

When a prompt needed streaming, the agent did call `watch()`, but every consumer it built could lose events: the resume token (`change._id`) was never saved and there was no `resumeAfter` on startup. Error handling was `process.exit`, a TODO, or nothing. Webhook calls ran inside the handler with no limit on concurrency. One sample used `watch([])`, which ships every change to the client. None of the samples set `maxAwaitTimeMS`, and none of the READMEs mentioned the multishard requirements. In every one of these builds the agent loaded `documentdb-driver` and `documentdb-connection` and found nothing about change streams.

## Why it matters

These counts come from one experiment run: 100 Azure DocumentDB sample prompts, gpt-5-mini, this kit, and the DocumentDB/Azure/Learn MCP servers. Treat them as indicative.

- **83 of 100 samples** answered the cold question "Are change streams supported, and does anything have to be enabled first?" wrongly. Across those 83 samples there are 86 findings: 29 wrong, 54 partly wrong and 3 outdated. Cold answers show the model's priors before it reads anything, and correcting those priors is the kit's job. The graders flagged a build risk in these cases: polling, a change-feed-style design, or a made-up precondition.
- **8 of those samples** built change-stream code or needed it, and the audit stage flagged 17 violated practices in them. These were missing resume-token checkpoints, missing restart handling, client-side filtering and missing multishard notes. In one sample, the agent's own `watch_once.js` check timed out, and the agent had nothing in the kit to help it debug.

"Watch a collection and react" is one of the most common shapes of sample an agent is asked to build. The tutorial-style consumer works in a demo but loses events without any error after a restart or failover.

## Proposed change (one PR)

The Rebalancer conflict and the "preview" status of multishard change streams and `updateDescription` are taken from the Learn page and must be confirmed before this PR is opened [needs SME confirmation] (open questions 3 and 4). Every place below that states them depends on that answer.

### 1. New rule-folder skill `skills/change-streams/` (prefix `cs-`)

`skills/change-streams/SKILL.md`:

```markdown
---
name: documentdb-change-streams
description: MongoDB change streams on Azure DocumentDB — availability (supported on every server version, not the Cosmos DB RU change feed), multishard preview enablement and the Rebalancer conflict, limitations (ordering, topology change, failover), server-side pipelines, pre-images and updateDescription, and a durable consumer that checkpoints resume tokens, restarts with backoff and falls back to historical replay. Use when code calls collection.watch() or Model.watch(), when building a listener, trigger, alerting, CDC or cache-invalidation service, when an agent is about to poll for changes or design a "change feed" consumer, or when choosing between periodic full recompute and incremental updates.
license: MIT
---

# Change Streams — Azure DocumentDB

Each rule follows the same shape — why it matters → incorrect example → correct example → references.

## Rules

- [cs-availability](cs-availability.md) — Change streams are supported natively via `watch()`. Do not poll, do not port a Cosmos DB change-feed design, and never gate on `serverVersion`.
- [cs-multishard](cs-multishard.md) — On multishard clusters, enable the preview feature "Change streams for multishard clusters" (Rebalancer must be off); no global ordering across shards.
- [cs-durable-consumer](cs-durable-consumer.md) — Checkpoint the resume token after the work is durable, resume with `resumeAfter`, restart with backoff after errors and failover, fall back to `startAtOperationTime`, keep handlers short and idempotent.
- [cs-pipeline-and-events](cs-pipeline-and-events.md) — Filter server-side with `$match`; supported stages; `updateLookup`, pre-images and `updateDescription` opt-ins.

For snapshots or aggregates over large collections, prefer an updater driven by change streams over a periodic full recompute.

## References

- [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) — Resume a change stream, historical change streams, pre-images, updateDescription, Multi-shard change streams (preview), Limitations
```

`cs-availability.md`: Azure DocumentDB (`Microsoft.DocumentDB/mongoClusters`) supports standard MongoDB change streams through `watch()`. Insert, update, replace and delete events have the usual shape (`_id` resume token, `operationType`, `ns`, `documentKey`, `fullDocument`). This is not the Azure Cosmos DB for MongoDB (RU) change feed, and there is no "API version" or "compatibility level" to check. `$changeStream` is supported on every server version (5.0 to 8.0). `$changeStreamSplitLargeEvent` and `showExpandedEvents` are unsupported on all versions. The only documented enablement step is the multishard toggle (see `cs-multishard`). If `watch()` fails with an operation error on a multishard cluster, check that portal toggle, not the server version. Incorrect: an `updatedAt` polling loop, and a `serverInfo()` version check that falls back to polling. Correct: open `watch()` and persist the token (see `cs-durable-consumer`).

`cs-multishard.md`: On a multishard cluster, turn on **Settings > Features > Change streams for multishard clusters** in the portal, then check on the Features page that it shows as enabled. The feature is labelled preview on Learn [needs SME confirmation]. It can't be turned on while **Rebalancer for multishard clusters** is on [needs SME confirmation]. Learn documents only the portal path, so tell the user to flip the toggle and check it, and do not invent an `az`/ARM/Bicep property. Learn shows no toggle for single-shard clusters. Multishard deployments do not preserve global event ordering, so order by a field you control or per `documentKey`. Going from single-shard to multishard breaks resumability, so a scale-out runbook needs a fresh start from `startAtOperationTime`. Agent checklist before writing `watch()` against a cluster you did not create: (1) is it multishard, and if so, is the feature enabled with the Rebalancer off; (2) does the consumer persist `change._id`; (3) are the `collMod` opt-ins it needs in place; (4) does the sample README say all of this.

`cs-durable-consumer.md`. Incorrect: `watch()` with no saved token and `on('error', () => process.exit(1))`. Correct (Node.js; Python uses `resume_after=` / `start_at_operation_time=`, Mongoose uses `Model.watch(pipeline, { resumeAfter })`):

```javascript
const CONSUMER = 'alerts-v1';
const checkpoints = db.collection('consumer_checkpoints');
const outbox = db.collection('outbox');

async function run() {
  let attempt = 0;
  let useTimestampFallback = false;
  for (;;) {
    const cp = await checkpoints.findOne({ _id: CONSUMER });
    const opts = { fullDocument: 'updateLookup', maxAwaitTimeMS: 10_000, batchSize: 100 };
    if (cp?.resumeToken && !useTimestampFallback) opts.resumeAfter = cp.resumeToken;
    else if (cp?.clusterTime) opts.startAtOperationTime = cp.clusterTime; // historical replay

    const pipeline = [{ $match: { operationType: { $in: ['insert', 'update'] },
                                  'fullDocument.status': { $in: ['offline', 'low_cash'] } } }];
    const stream = coll.watch(pipeline, opts);
    try {
      for await (const change of stream) {
        // 1. fast, idempotent local work only: enqueue, never call out over HTTP here
        await outbox.updateOne({ _id: change._id },
          { $setOnInsert: { consumer: CONSUMER, change, createdAt: new Date() } }, { upsert: true });
        // 2. checkpoint AFTER the work is durable
        await checkpoints.updateOne({ _id: CONSUMER },
          { $set: { resumeToken: change._id, clusterTime: change.clusterTime, updatedAt: new Date() } },
          { upsert: true });
        attempt = 0;
        useTimestampFallback = false;
      }
    } catch (err) {
      await stream.close().catch(() => {});
      if (isTokenNotResumable(err)) {               // app-defined check on the server error
        if (useTimestampFallback || !cp?.clusterTime) {
          await alertOperator(err);                 // beyond replayable history: human decision
          return;                                   // never restart silently from "now"
        }
        useTimestampFallback = true;
      }
      // transient errors and failover: reopen with the stored token after backoff
      const delay = Math.min(30_000, 500 * 2 ** attempt++) + Math.random() * 250;
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

Notes in the rule:
- Checkpoint after each event, or after each small batch when throughput is high.
- Delivery is at-least-once, because events after the last checkpoint come again. Make handlers idempotent, for example by keying on the resume token or on `documentKey._id`.
- Write the checkpoint as an ordinary acknowledged write, after the side effect.
- Keep `retrywrites=false` in the connection string; it is required, not a sample choice. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Because the driver does not retry writes, a transient failure on the outbox or checkpoint write surfaces as an error; the loop reopens from the last checkpoint, and the upserts keyed on `change._id` make the replay safe. Do not set `retryWrites: true` to work around this.
- Learn says cursors must be reopened after failover and that resume still works. The loop does exactly this.
- If the stored token can no longer be resumed, fall back to `startAtOperationTime` from the stored `clusterTime`. This is a historical change stream; run large replays when traffic is low. Beyond the replay window, alert an operator.
- A separate worker drains `outbox` with a concurrency limit (for example `p-limit(8)`), makes the webhook call, retries with its own backoff, and never blocks the stream.
- Include a restart test: insert 3 documents, kill the consumer, insert 2 more, restart, and assert that exactly 2 new events are handled.

`cs-pipeline-and-events.md`:
- Don't use `watch([])` when only some events matter. Filter on the server with `$match` on `operationType` or `fullDocument.<field>`. The supported stages are `$match`, `$project`, `$addFields`, `$set` and `$unset`.
- Ask for `fullDocument: 'updateLookup'` only when you need the post-update document.
- Pre-images: run `db.runCommand({ collMod: "<coll>", changeStreamPreAndPostImages: { enabled: true } })`, then call `watch()` with `fullDocumentBeforeChange: "whenAvailable"`. Pre-images cover only update, delete and replace events. They add write amplification, and they are not available when processing historical logs.
- `updateDescription` (preview [needs SME confirmation]): run `db.runCommand({ collMod: "<coll>", enableUpdateDescription: { enabled: true } })`. Updates made with an aggregation pipeline don't produce it; updates made with update operators do.
- These `collMod` options change what an event contains. They do not control whether a stream can be opened.

### 2. Edits to existing files (one each)

- `skills/driver/SKILL.md`: append `Also routes change-stream work (watch(), resume tokens) to documentdb-change-streams.` to the `description`, and add under `## Rules`:

  ```markdown
  - Building a watcher, listener or trigger with `collection.watch()`? See the `documentdb-change-streams` skill.
  ```

- `skills/sharding/SKILL.md`: append `, or when an app on a multishard cluster uses change streams (watch())` to the "Use when" clause of the `description`, and under Rules, in the `sharding-logical-vs-physical` bullet, add: `Change streams on a multishard cluster need the preview "Change streams for multishard clusters" toggle (Rebalancer off); see documentdb-change-streams.`
- `skills/high-availability/SKILL.md`, under Rules: `After an HA failover, change-stream cursors must be reopened; resume with the saved token (see documentdb-change-streams).`
- `skills/azure-deployment/SKILL.md`, Step 9: `- **Change streams on a multishard cluster.** If shardCount > 1 and the app uses watch(), enable Settings → Features → Change streams for multishard clusters in the portal (preview; Rebalancer must be off).`
- `docs/SKILLS.md`, rule-folder table, new row:

  ```markdown
  | [`change-streams/`](../skills/change-streams/) | `cs-` | Availability (not RU change feed, not version-gated), multishard preview toggle and Rebalancer conflict, limitations, server-side `$match`, pre-images/updateDescription, durable consumer with resume-token checkpoints, backoff and historical fallback |
  ```

- `AGENTS.md`: a skills-table row for `documentdb-change-streams`, and a routing line: `- **Reacting to inserts / updates / deletes in real time (alerts, CDC, cache invalidation, "change feed")** → documentdb-change-streams`.
- `CHANGELOG.md`: `Added change-streams rule folder (4 rules).`

Not in this PR: the workflow-run and agent-memory rules from draft 093 (a separate durable-state proposal); a documentdb-mcp command that reports change-stream availability; and Learn feedback on the Node.js "Get started" sample, which uses `watch([])` and `process.exit(1)`.

## Evidence

- `runs/02-real-time-event-stream-ingestion/20261124-203233/05-audit.json`
- `runs/16-atm-network-status-monitor/20261124-202405/05-audit.json`
- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json`
- `runs/03-substitute-product-finder/20261124-183232/02-readiness.json`
- `runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json`
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json`

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

## Open questions

1. [needs SME confirmation] Is the active change log 400 MB, and is that the boundary past which `resumeAfter` stops working?
2. [needs SME confirmation] Do historical change streams reach back up to 35 days through PITR, or to cluster creation, whichever is earlier?
3. [needs SME confirmation] Can "Change streams for multishard clusters" still not be enabled while "Rebalancer for multishard clusters" is on?
4. [needs SME confirmation] Are multishard change streams still preview, or GA? Is `updateDescription` still preview?
5. [needs SME confirmation] Are single-shard clusters really without any enablement step? Learn shows only the multishard toggle.
6. [needs SME confirmation] What error code or label does the service return when a resume token can no longer be resumed? The rule's `isTokenNotResumable()` needs it.
7. [needs SME confirmation] Is there a CLI, ARM or Bicep property for the multishard toggle, or a way to read its state programmatically?
8. [needs SME confirmation] Is the `updateDescription` exclusion limited to aggregation-pipeline updates, with update operators supported?

## Source drafts

105-change-stream-consumers-have-no-durability-resume-tokens-nev.md, 032-believes-vcore-change-streams-are-absent-or-crippled-like-co.md, 033-believes-change-streams-are-on-by-default-cluster-wide-unawa.md, 034-believes-azure-documentdb-change-streams-have-full-mongodb-s.md, 035-believes-change-stream-availability-is-gated-by-the-cluster-.md, 093-durable-state-patterns-change-stream-resume-tokens-workflow-.md

sample_count 83 is the distinct samples behind the Q12 findings in 032, 033, 034 and 035 (86 findings). The 8 samples from 105 and 6 of the 7 from 093 fall inside those 83. The seventh 093 sample (04-regulatory-reporting-orchestration) has only a workflow-run finding, which this PR leaves out, so it is not counted. REVIEW.md section 1 also lists draft 041 among the change-stream overlaps; its change-stream part is not in this filing's member list and should be dropped from 041 when it is filed.
