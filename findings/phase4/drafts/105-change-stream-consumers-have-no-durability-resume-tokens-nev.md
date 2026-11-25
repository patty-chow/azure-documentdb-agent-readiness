---
title: "Add a change-streams skill with a durable consumer reference (resume-token checkpoints, restart loop with backoff, historical fallback, server-side $match, outbox pattern, multishard notes)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 8
findings: 17
bucket: sample-violated-practice
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add `skills/change-streams/`: durable change-stream consumer rules for Azure DocumentDB

## What happens today

The kit has **no change-stream guidance in any skill**. `grep -riE "change ?stream|resumeAfter|resume token|\.watch\(|startAtOperationTime"` over `skills/`, `docs/` and `knowledge-base/` returns nothing. The only hits in the repo are test fixtures under `scenarios/ecommerce-advanced/` (`cases/change-streams.json`, `scripts/generate.mjs`), which the builder never reads as guidance. `docs/SKILLS.md` lists 17 skills, and none covers `watch()`, resume tokens or the multishard requirements.

In a 100-sample agent-readiness run (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), **7 samples opened `coll.watch()`**: event-stream ingestion, portfolio alerts, lab-results aggregator, trade settlement, bed-occupancy tracker, ATM monitor and outreach listener. An 8th sample (cohort analysis) recomputed snapshots weekly where an incremental change-stream path would have fit. **All 7 streaming samples shipped the same non-durable consumer:**

- The resume token (`change._id`) is never written to a durable checkpoint, and startup passes no `resumeAfter` / `startAtOperationTime`, so a restart loses or replays events.
- `on('error')` either logs a TODO, calls `process.exit`, or is missing. There is no restart loop and no handling of non-resumable errors.
- Webhook delivery (`await axios.post(...)`) runs inside the change handler with unbounded concurrency and no outbox or queue.
- One sample calls `watch([], { fullDocument: 'updateLookup' })` with an empty pipeline, so every change is shipped to the client even though a server-side `$match` on `fullDocument.status` was the obvious filter.
- No sample sets `maxAwaitTimeMS`, and neither the README nor the code mentions the multishard change-stream requirements.
- One build was unsure whether client `writeConcern` settings were what made its checkpoint durable.

In every one of the 7 runs, the builder loaded `documentdb-driver` and `documentdb-connection` and found nothing that applied. The audit stage then found the practices on its own on the Learn page https://learn.microsoft.com/en-us/azure/documentdb/change-streams (sections "Resume a change stream", "Multi-shard change streams (preview)" and "Limitations") and marked them violated. In total there are **17 violated-practice findings across 8 of 100 samples.** In sample 02, the builder's own `scripts/watch_once.js` verification exited with `Timeout waiting for change event`, and the builder had no checklist to debug it with.

## Why it matters

Change streams are Azure DocumentDB's change-feed mechanism, and "watch a collection and alert" is one of the most common sample shapes an agent is asked to build. With no kit rule, the model falls back to the generic tutorial shape (open a stream, print the changes). That shape is fine for a demo but loses events without warning in production. This is the kind of correct-but-incomplete habit the kit exists to fix. The fix is cheap because the service-specific facts are already on Learn. They are just not in front of the builder when it writes the code.

## Proposed change (one PR)

### 1. New rule-folder skill `skills/change-streams/`

`skills/change-streams/SKILL.md` uses the same shape as `skills/data-modeling/SKILL.md`:

```yaml
---
name: documentdb-change-streams
description: Durable change-stream consumers on Azure DocumentDB — persist resume tokens to a checkpoint collection, resume with resumeAfter (or startAtOperationTime for historical replay), restart loop with backoff after errors and failover, server-side $match pipelines, short idempotent handlers with an outbox + bounded worker, multishard preview requirements. Use when code calls collection.watch(), builds a listener/trigger/alerting service, or chooses between periodic full recompute and incremental processing.
license: MIT
---
```

Each rule follows the kit's usual layout: why it matters, then incorrect code, then correct code, then references.

- `cs-durable-resume-checkpoint.md`: After an event is processed, write `change._id` to a `consumer_checkpoints` collection. On startup, read it back and pass it as `resumeAfter`. Also store the event's `clusterTime` so the consumer can fall back to `startAtOperationTime`. Delivery is at-least-once, so handlers must be idempotent (for example, upsert keyed by `documentKey._id` plus the resume token). A normal acknowledged write is enough for the checkpoint. What matters is that it happens *after* the side effect, not any special client `writeConcern` setting.
- `cs-restart-backoff.md`: Never call `process.exit` on a stream error. Wrap `watch()` in a restart loop with exponential backoff and jitter. Learn states that change-stream cursors must be reopened after failover and that resume still works afterwards. That reopen is exactly what the loop does. If the stored token can no longer be resumed, for example because it has aged out of the active 400 MB change log, fall back to `startAtOperationTime` from the stored `clusterTime`. Historical change streams can replay up to 35 days back (PITR-backed) or to cluster creation, whichever is earlier. Beyond that, alert an operator instead of retrying forever or restarting silently from "now".
- `cs-server-side-match.md`: Don't call `watch([])` when only some events matter. Filter server-side with `$match` on `operationType` / `fullDocument.<field>`. The supported change-stream stages are `$match`, `$project`, `$addFields`, `$set` and `$unset`. Ask for `fullDocument: 'updateLookup'` only when the post-update document is needed. For field-level reactions, `updateDescription` (preview, enabled per collection with `collMod`) avoids comparing whole documents.
- `cs-short-handler-outbox.md`: The handler does one fast local write (an `outbox` document) and returns. A separate worker with a concurrency bound N drains the outbox and does the HTTP/webhook I/O with its own retries. Checkpoint only after the outbox write succeeds.
- `cs-multishard-limitations.md`: On multishard clusters, change streams are a **preview** feature. Enable it in the Azure portal under **Features > Change streams for multishard clusters**. It can't be enabled while "Rebalancer for multishard clusters" is on. Global event ordering is not preserved across shards, and moving a cluster from single-shard to multi-shard breaks resumability. `showExpandedEvents` is not supported. Link the Learn "Multi-shard change streams (preview)" and "Limitations" sections, and say all of this in the sample README.
- `cs-incremental-vs-recompute.md`: To maintain snapshots or aggregates over large collections, prefer an updater driven by change streams over periodic full recomputes. Show both approaches and when each fits.

### 2. Reference durable consumer

This goes in `cs-durable-resume-checkpoint.md` in Node.js. A PyMongo variant in `references/` is optional.

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
    else if (cp?.clusterTime) opts.startAtOperationTime = cp.clusterTime; // historical replay (up to 35 days)

    const pipeline = [{ $match: { operationType: { $in: ['insert', 'update'] },
                                  'fullDocument.status': { $in: ['offline', 'low_cash'] } } }];
    const stream = coll.watch(pipeline, opts);
    try {
      for await (const change of stream) {
        // 1. fast, idempotent local work only: enqueue, never call out over HTTP here
        await outbox.updateOne({ _id: change._id }, { $setOnInsert: { consumer: CONSUMER, change, createdAt: new Date() } },
                               { upsert: true });
        // 2. checkpoint AFTER the work is durable
        await checkpoints.updateOne({ _id: CONSUMER },
          { $set: { resumeToken: change._id, clusterTime: change.clusterTime, updatedAt: new Date() } }, { upsert: true });
        attempt = 0;
        useTimestampFallback = false;
      }
    } catch (err) {
      await stream.close().catch(() => {});
      if (isTokenNotResumable(err)) {            // token aged out of the active change log, etc.
        if (useTimestampFallback || !cp?.clusterTime) { alertOperator(err); }  // beyond history: human decision
        useTimestampFallback = true;
      }
      // transient errors and failover: reopen with the stored token after backoff
      const delay = Math.min(30_000, 500 * 2 ** attempt++) + Math.random() * 250;
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
```

A separate `worker.js` drains `outbox` with a concurrency bound (for example `p-limit(8)`), makes the webhook call and marks the document delivered. Failures retry with their own backoff and never block the stream.

### 3. Discoverability

- Add a row to the rule-folder table in `docs/SKILLS.md`: `change-streams/` | `cs-` | "Durable consumers: resume-token checkpoints, restart loop with backoff and historical fallback, server-side `$match`, outbox + bounded worker, multishard preview requirements, incremental vs full recompute".
- Add one line under Rules in `skills/driver/SKILL.md`: "Building a watcher / listener / trigger with `collection.watch()`? See the `documentdb-change-streams` skill." The builder loaded `documentdb-driver` in all 7 streaming runs, so this is the cheapest hook.
- `scripts/validate-skills.ps1` already validates every `skills/*/SKILL.md`. No installer or manifest lists the skill folders, so nothing else needs registering.

### Related (not part of this PR)

The Node.js tab of the Learn "Get started" sample itself ends its error path with `process.exit(1)` and opens `model.watch([], watchOptions)` with an empty pipeline. A builder that copies it reproduces two of the violations above. That is worth a separate learn-docs feedback item.

## Evidence (run folders under the readiness repo; no connection strings)

- `runs/02-real-time-event-stream-ingestion/20261124-203233/05-audit.json`: `watch.js` exits on error and sets no `resumeAfter` and no `maxAwaitTimeMS`. In `events.jsonl`, `node scripts/watch_once.js` exits with code 3 ("Timeout waiting for change event"). `doc-gaps.md` has a section "Change-stream resume-token guidance and sample code".
- `runs/03-portfolio-tracker-with-live-alerts/20261124-190220/05-audit.json`: no token persistence, and `await axios.post` runs inside the change handler.
- `runs/09-trade-settlement-tracker/20261124-201323/05-audit.json`: the pipeline filter is present, but `on('error')` is a TODO comment. Three checkpointing checks are violated.
- `runs/16-atm-network-status-monitor/20261124-202405/05-audit.json`: `watch([])` with an empty pipeline, no multishard note in the README, no token persistence.
- `runs/19-proactive-outreach-orchestration/20261124-205844/05-audit.json`: no `on('error')` handler at all, and confusion over writeConcern versus checkpointing. In `02-readiness.json`, the Q12 cold answer "no special feature flag required" was marked partly_wrong against the Learn multishard preview section.
- Also hit: `runs/07-lab-results-aggregator/20261124-194018`, `runs/12-hospital-bed-occupancy-tracker/20261124-194835`, and `runs/15-cohort-analysis-backend/20261124-205336` (weekly full recompute where an incremental path fits).

## Verification

### 1. Already covered? Status: confirmed (not covered in the target)

- I grepped the kit clone (`skills/`, `docs/`, `knowledge-base/`) for `change stream`, `changestream`, `resumeAfter`, `resume token`, `.watch(` and `startAtOperationTime`. None of the 17 skills, `docs/SKILLS.md` or `knowledge-base/kb.json` matches. The only matches are in `scenarios/ecommerce-advanced/` (fixture generator and validator, plus a README line that compares resume token, `clusterTime` and `wallTime` for test cases). That is test data, not guidance the builder can follow.
- microsoft/documentdb-mcp has no change-stream guidance either, and it is not the right home for it.
- Learn (https://learn.microsoft.com/en-us/azure/documentdb/change-streams, updated 2026-11-17) does document resume tokens ("The `_id` field of each change event serves as the resume token. Store it durably and pass it back when reopening the stream"), historical `startAtOperationTime`, pipeline stages, multishard enablement and limitations. It does not cover restart/backoff loops, outbox or handler patterns, or idempotency. Those gaps do not affect this agent-kit PR, which is about putting the practices where the builder looks.

### 2. Is the premise true? Status: confirmed, with corrections applied

These claims were checked against the Learn change-streams page:

- Resume via `resumeAfter` with `change._id`: confirmed.
- `startAtOperationTime` is supported: confirmed. The draft framed it only as a cold-start fallback. I corrected it to its documented role, historical replay once the 400 MB active change log has rotated, up to 35 days via PITR or to cluster creation, whichever is earlier. The reference code now stores `clusterTime` and falls back to it.
- `fullDocument: 'updateLookup'` and `maxAwaitTimeMS`: confirmed. The Learn C# sample sets `FullDocument = UpdateLookup` and `MaxAwaitTime`.
- Server-side pipeline: confirmed. I added the supported stage list (`$match`, `$project`, `$addFields`, `$set`, `$unset`).
- Multishard: confirmed as a preview feature that must be enabled. I sharpened the wording to Learn's text: it is enabled under Portal > Features, it can't be enabled while Rebalancer for multishard clusters is on, it gives no global ordering, and a single-shard to multi-shard transition breaks resumability. The draft's vague "ordering/resumability differ" was replaced.
- Removed an unsupported claim: the draft said checkpoint durability "comes from the service's replication, not from client writeConcern options". No source supports this, so it is replaced with neutral guidance: use an acknowledged write and checkpoint after the side effect.
- Softened the `invalidate` handling: Learn does not document `invalidate` events (or drop/rename invalidation) for Azure DocumentDB. The rule now keys on "token no longer resumable", falls back to historical replay and alerts beyond that. It does not hard-code invalidate semantics.
- Added a failover fact from Learn ("Change stream cursors must be reinitialized after failover events, while resume capability remains preserved"). It directly supports the restart-loop rule.
- Added at-least-once delivery and idempotency, which follow from "checkpoint after processing". The outbox write in the code is now an idempotent upsert keyed by the resume token.
- Sample count: the 17 finding ids map to 8 distinct samples (02, 03, 07, 09, 12, 15, 16, 19), which matches the draft.

### 3. Maintainer skeptic. Status: confirmed

As a kit maintainer, I would accept this. It names concrete files (`skills/change-streams/SKILL.md` plus six `cs-*.md` rules, a row in `docs/SKILLS.md`, a pointer line in `skills/driver/SKILL.md`). It follows the existing rule-folder convention (`data-modeling/` with its `model-` prefix), fills a real topic gap (change streams are a headline DocumentDB feature with no skill), and has a clear DocumentDB angle: the 400 MB change log, 35-day historical replay, failover reinitialization, multishard preview enablement and the Rebalancer conflict, and the supported pipeline stages. The generic-hygiene parts (backoff, outbox) are tied to the service's failover and resumability behaviour rather than offered as abstract advice. The repo is correct: Azure/documentdb-agent-kit.

## Finding ids

F0279, F0280, F0483, F0484, F1095, F1097, F1579, F1581, F1584, F2077, F2672, F2511, F2675, F2678, F3348, F3349, F3353
