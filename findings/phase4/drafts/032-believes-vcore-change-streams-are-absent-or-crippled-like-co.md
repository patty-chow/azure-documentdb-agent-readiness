---
title: "Add a change-streams rule to the driver skill (watch(), resume tokens, pre-images) so agents stop assuming Cosmos RU change-feed limits"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 51
findings: 52
bucket: confusion-Q12
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add `driver-change-streams` rule: native change streams, resume tokens, pre-images

## What happens today

Nothing in the kit says that Azure DocumentDB supports MongoDB change streams. `grep -rniE "change ?stream|\.watch\(|pre-?image|fullDocumentBeforeChange|changeStream"` over `skills/`, `knowledge-base/` and `compat/` returns no hits (the only matches are the e-commerce scenario fixtures under `scenarios/ecommerce` and `scenarios/ecommerce-advanced`). `skills/driver/` has a single rule (`driver-singleton-client.md`); `skills/connection/` covers pools and timeouts; `skills/monitoring/` covers diagnostics and alerts.

Because the kit is silent, an agent carrying the Cosmos DB for MongoDB (RU) prior keeps it. In an experiment that ran gpt-5-mini with this kit plus the DocumentDB/Azure/Learn MCP servers over 100 Azure DocumentDB sample prompts, the cold answer to "Are change streams supported, and does anything have to be enabled first?" was graded wrong, partly wrong or outdated in **51 of 100 samples** (52 findings; 27 graded outright wrong). In nearly every case the grader traced the answer to the RU API / Cosmos change feed; one each to Cosmos DB for NoSQL and Amazon DocumentDB. Typical cold answers:

- "The Cosmos DB MongoDB API does not reliably support MongoDB change streams ... use the Cosmos DB Change Feed ..." (06-order-history-timeline-agent)
- "Cosmos DB's Mongo API historically did not support MongoDB change streams; instead use Cosmos DB Change Feed ... billed by RU." (07-mortgage-application-multi-agent)
- "Change streams not universally supported on Cosmos Mongo API; use Cosmos Change Feed for change notifications." (13-product-q-a-chatbot-rag)

## Why it matters

- The wrong belief pushes builders toward polling, offline migration, or a Cosmos change-feed-style design (lease collections, no delete events) for anything event-driven: real-time alerts, cache invalidation, CDC into a search index, order-status timelines. The graders flagged this build risk in all 51 samples.
- Where the prompt forced the issue (7 samples: 02-real-time-event-stream-ingestion, 03-portfolio-tracker-with-live-alerts, 07-lab-results-aggregator, 09-trade-settlement-tracker, 12-hospital-bed-occupancy-tracker, 16-atm-network-status-monitor, 19-proactive-outreach-orchestration) the builder did open `watch()` after reading Learn, but **0 of 7 persisted a resume token or used `resumeAfter`**, and none used pre-images where the prompt needed the before/after status (12-hospital-bed-occupancy-tracker's transition detection was graded `not_met` for exactly this). The audits for 02, 03, 07, 12 and 16 record that the agent looked in `documentdb-driver` / `documentdb-connection` for a change-stream pattern and found nothing, and list "Change-stream resume / checkpointing" as a violated practice.
- The Learn page (https://learn.microsoft.com/en-us/azure/documentdb/change-streams) already documents change streams with resume-token examples in six languages, historical change streams, pre-images, `updateDescription` and multi-shard enablement. Most of the 52 "fix the docs" suggestions ask for content that is already there. The gap is that the agent never gets to that page because the kit never points at it. The correction belongs in the kit.

## Proposed change (this PR)

**1. New rule file `skills/driver/driver-change-streams.md`** (same shape as `driver-singleton-client.md`: Why it matters / Incorrect / Correct / References):

````markdown
# driver-change-streams

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB supports **standard MongoDB change streams** through the driver's
`watch()`. This is *not* the Azure Cosmos DB for MongoDB (RU) change feed: insert,
update, replace **and delete** events are emitted with the usual event shape
(`_id` resume token, `operationType`, `ns`, `documentKey`, `fullDocument`), and
resume tokens work. The Learn page documents an enablement step only for
**multi-shard** clusters: turn on the preview feature *Change streams for
multishard clusters* under the cluster's **Settings > Features** blade first (it
cannot be enabled while *Rebalancer for multishard clusters* is on).

Do not poll on an `updatedAt` field or port a Cosmos change-feed / lease-collection
design. Do persist the resume token after each processed event so the watcher
can resume after a restart instead of missing or re-processing events. After a
failover the cursor must be reopened; the saved resume token still works, so
wrap the watch loop in a reconnect-and-resume retry.

## Incorrect

```javascript
// Polling because "Cosmos DB for MongoDB has no change streams"
setInterval(async () => {
  const rows = await orders.find({ updatedAt: { $gt: lastSeen } }).toArray(); // BAD: misses deletes, re-reads, adds latency
  for (const r of rows) await handle(r);
  lastSeen = new Date();
}, 5000);
```

## Correct

```javascript
const checkpoints = client.db().collection("watch_checkpoints");

async function run() {
  const last = await checkpoints.findOne({ _id: "orders" });
  const stream = orders.watch(
    [{ $match: { operationType: { $in: ["insert", "update", "replace", "delete"] } } }],
    { fullDocument: "updateLookup", ...(last && { resumeAfter: last.token }) }
  );
  for await (const change of stream) {
    await handle(change);                       // make this idempotent: events can be redelivered
    await checkpoints.updateOne(
      { _id: "orders" }, { $set: { token: change._id, at: new Date() } }, { upsert: true }
    );
  }
}

// Reopen after failover / transient errors; the stored token resumes the stream.
for (;;) { try { await run(); } catch (e) { console.error(e); await new Promise(r => setTimeout(r, 1000)); } }
```

Python (PyMongo/Motor): `coll.watch(pipeline, full_document="updateLookup", resume_after=token)`; Mongoose: `Model.watch(pipeline, { fullDocument: "updateLookup", resumeAfter: token })`.

Pipeline stages supported in a change-stream pipeline: `$match`, `$project`,
`$addFields`, `$set`, `$unset`. `showExpandedEvents` is not supported.

Also available on Azure DocumentDB:

- **Historical change streams** — `startAtOperationTime` (or `resumeAfter` / `startAt`) can reach past the 400 MB active change log; with point-in-time-restore log integration recovery extends up to 35 days or the cluster's creation, whichever is earlier. Run large replays in low-traffic periods.
- **Pre-images (opt-in per collection)** — `db.runCommand({ collMod: "orders", changeStreamPreAndPostImages: { enabled: true } })`, then pass `fullDocumentBeforeChange: "whenAvailable"` (or `"required"`) to `watch()` to get the document as it was before an update / replace / delete. Adds write amplification; enable only where needed. Not available when replaying historical logs.
- **`updateDescription` (preview, opt-in per collection)** — `db.runCommand({ collMod: "orders", enableUpdateDescription: { enabled: true } })` adds `updatedFields` / `removedFields` / `truncatedArrays` to update events. Not supported for updates made with aggregation-pipeline updates.

Limitations to design around: moving a cluster from single-shard to multi-shard breaks resumability (saved tokens become invalid); multi-shard streams do not preserve global event ordering.

## References

- [Change streams in Azure DocumentDB](https://learn.microsoft.com/en-us/azure/documentdb/change-streams) — resume tokens, historical change streams, pre-images, updateDescription, multi-shard enablement, limitations, driver examples (Python, Java, JavaScript, C#, Ruby, Node.js)
````

**2. `skills/driver/SKILL.md`** — add to the rule list:

```markdown
- [driver-change-streams](driver-change-streams.md) — Use native change streams (`watch()`) instead of polling or a Cosmos change-feed design; persist resume tokens; opt in to pre-images when you need the before-image.
```

and extend the front-matter `description` so discovery matches change-stream tasks, e.g. append: `Also covers MongoDB change streams on Azure DocumentDB: watch(), resume tokens, pre-images, multi-shard enablement. Use when a task needs real-time reaction to inserts/updates/deletes (alerts, CDC, cache invalidation) or when an agent is about to poll or build a Cosmos DB change-feed-style consumer.`

**3. `AGENTS.md`**
- "Skills in this kit" row for `documentdb-driver` (line 63): `Singleton MongoClient, connection reuse fundamentals, change streams (watch(), resume tokens, pre-images)`.
- Task-routing list (after the `Configuring MongoClient` line, ~line 95): add `- **Reacting to inserts / updates / deletes in real time (alerts, CDC, cache invalidation, "change feed")** → documentdb-driver (driver-change-streams)`.

**4. `docs/SKILLS.md`** line 24: `MongoDB driver/SDK usage (singleton client, pooling, change streams)`.

**5. `CHANGELOG.md`** entry: "Add `driver-change-streams` rule: Azure DocumentDB supports native MongoDB change streams; shows resume-token checkpointing, failover resume and pre-image opt-in; corrects the Cosmos DB for MongoDB (RU) change-feed assumption."

Not in this PR (secondary, raised in 2 of 52 findings: F0427, F0462): a `documentdb-mcp` status command that reports whether change streams are available on the connected cluster. Worth a separate issue on microsoft/documentdb-mcp if there is appetite.

## Evidence (run folders from the experiment; no connection strings)

- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json` — confusions[Q12]: cold answer recommends the Cosmos DB Change Feed rather than MongoDB change streams, outcome wrong; improvement explicitly asks the agent kit for a small `watch()` + `resumeAfter` sample.
- `runs/07-mortgage-application-multi-agent/20261124-201025/02-readiness.json` — confusions[Q12]: RU-era "historically did not support change streams ... billed by RU", outcome wrong.
- `runs/03-portfolio-tracker-with-live-alerts/20261124-190220/doc-gaps.md` — "[high] Resume-token persistence for change streams": looked in documentdb-driver/connection skills, found no copy-paste pattern; sample opens `Model.watch()` but cannot resume after restart.
- `runs/07-lab-results-aggregator/20261124-194018/05-audit.json` — checks "Change-stream resume" and "Change-stream checkpointing" status violated; doc_gaps "Resume-token persistence for change streams (best-practice example)".
- `runs/16-atm-network-status-monitor/20261124-202405/05-audit.json` — checks "Change-stream resume token", "Change-stream server-side filtering" and "Change-stream limitations" all violated; empty pipeline, no checkpoint, no multi-shard note.

## Verification

### 1. Already covered? — confirmed (not covered in the target)

Agent kit clone at commit 4f41c15 (2026-11-23): `grep -rniEl "change ?stream|\.watch\(|pre-?image|fullDocumentBeforeChange|changeStream"` over the whole repo matches only `scenarios/ecommerce/README.md`, `scenarios/ecommerce-advanced/README.md`, `scenarios/ecommerce-advanced/package.json` and two scenario scripts. Nothing under `skills/`, `knowledge-base/` (README.md, kb.json, routers) or `compat/`. `skills/driver/` contains only `SKILL.md` and `driver-singleton-client.md`; the driver SKILL.md description covers "singleton MongoClient, connection reuse, connection-pool fundamentals" only. AGENTS.md line 63 and docs/SKILLS.md line 24 describe the driver skill as singleton client / pooling. microsoft/documentdb-mcp clone: no change-stream matches either (relevant only to the out-of-PR secondary note).
Learn does cover the subject (https://learn.microsoft.com/en-us/azure/documentdb/change-streams, updated 2026-11-17): "Change streams are a real-time stream of database changes that flows from your database to your application", with resume-token examples. So the service docs are not the gap; the kit is.

### 2. Premise true? — confirmed, with corrections applied

Checked against https://learn.microsoft.com/en-us/azure/documentdb/change-streams:
- Change streams via `watch()`, insert/update/delete events, `resumeAfter` with the event `_id` as the token: confirmed ("Change streams are resumable by specifying a 'resume token' to `resumeAfter`").
- Multi-shard needs the preview feature "Change streams for multishard clusters" under Settings > Features: confirmed. Added: it cannot be enabled while "Rebalancer for multishard clusters" is enabled.
- "Nothing to enable on single-shard": the page does not state this in words; it documents enablement only for multi-shard. Reworded accordingly.
- Historical change streams: confirmed. Added the facts the draft left vague: active change log is 400 MB; PITR integration extends recovery up to 35 days or cluster initialization, whichever is earlier; `startAt`, `resumeAfter`, `startAtOperationTime` all supported.
- Pre-images: confirmed (`collMod ... changeStreamPreAndPostImages`, `fullDocumentBeforeChange` off / whenAvailable / required; only for update, delete, replace). Added: not supported for historical processing; storage/write-amplification cost.
- `updateDescription` (preview): the draft implied it is always present. Corrected: it requires per-collection opt-in `collMod ... enableUpdateDescription: { enabled: true }` and is not supported for updates within aggregation pipelines.
- Added limitations from the page: single-shard to multi-shard transition breaks resumability; no global ordering in multi-shard; cursors must be reinitialized after failover (resume preserved), so the Correct example now wraps the loop in a reconnect-and-resume retry; `showExpandedEvents` unsupported; supported pipeline stages $addFields, $match, $project, $set, $unset.
- Removed the `$changeStream` aggregation-operator reference link: https://learn.microsoft.com/en-us/azure/documentdb/query/operators/aggregation/$changestream returns HTTP 404.
- Removed the emoji marker in the Incorrect snippet (replaced with a `BAD:` comment).
No conflict with the required facts (vCore / mongoClusters, M-series tiers, PostgreSQL-based engine).

### 3. Maintainer skeptic — confirmed

As a maintainer of Azure/documentdb-agent-kit I would accept this: it names the exact new file (`skills/driver/driver-change-streams.md`), follows the existing rule template (`driver-singleton-client.md`: Category/Priority, Why it matters, Incorrect, Correct, References), names the exact registration points (driver SKILL.md rule list and description, AGENTS.md line 63 and routing list, docs/SKILLS.md line 24, CHANGELOG.md), and is specific to Azure DocumentDB (RU-vs-vCore confusion, multi-shard preview feature, historical change streams, pre-image opt-in). The MCP-server idea is correctly scoped out to microsoft/documentdb-mcp. Small edits applied above (facts and the dead link); the repo stays Azure/documentdb-agent-kit.

## Finding ids

- F0010
- F0046
- F0077
- F0114
- F0154
- F0185
- F0264
- F0292
- F0355
- F0427
- F0462
- F0563
- F0603
- F0731
- F0799
- F0853
- F0893
- F0923
- F0949
- F0975
- F1006
- F1080
- F1108
- F1137
- F1167
- F1204
- F1230
- F1265
- F1304
- F1376
- F1407
- F1440
- F1493
- F1528
- F1630
- F1688
- F1723
- F1957
- F1988
- F2127
- F2191
- F2294
- F2557
- F2596
- F2689
- F2752
- F2812
- F2914
- F2981
- F3182
- F3303
- F3431
