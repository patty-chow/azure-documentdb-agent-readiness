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
open_questions: 7
---

# Add one change-streams skill: availability, multishard enablement, limitations and a durable resume-token consumer

## What happens today

No skill in the kit mentions change streams. `grep -riE "change ?stream|resumeAfter|resume token|\.watch\(|startAtOperationTime|pre-?image"` over `skills/`, `docs/`, `knowledge-base/` and `AGENTS.md` (commit 4f41c15) returns nothing. The only hits are test fixtures under `scenarios/ecommerce-advanced/` (plus one README line in `scenarios/ecommerce/` pointing to them), which agents do not load as guidance. `skills/driver/` has one rule (`driver-singleton-client.md`), and `docs/SKILLS.md` describes it as "singleton client, pooling".

The Learn page [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) (ms.date 2026-11-16) already covers resume tokens, historical change streams, pre-images, `updateDescription`, multishard enablement and limitations. Agents using the kit never get pointed to it, so they fall back on what they learned in training. Four wrong beliefs showed up:

- **"Not supported, use the Cosmos DB change feed."** This is the Azure Cosmos DB for MongoDB (RU) belief. It leads to polling on `updatedAt` or to a lease-collection design.
- **"Gated by `serverVersion` / compatibility level."** In fact `$changeStream` is listed as supported in the 5.0, 6.0, 7.0 and 8.0 columns of the [MQL compatibility matrix](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#operators).
- **"Works cluster-wide with no setup, like Atlas."** On multishard clusters this is wrong. Change streams there are a preview feature ("Multi-shard change streams (preview)" on the Learn page) that has to be turned on under **Settings > Features > Change streams for multishard clusters**, and the Learn page's step 5 Important box says the toggle can't be turned on while **Rebalancer for multishard clusters** is on. Single-shard clusters have no documented enablement step, and the experiment observed a change stream working on one without any toggle.
- **"Full MongoDB semantics."** In fact global ordering across shards is not preserved, going from single-shard to multishard breaks resumability, and cursors must be reopened after failover.

When a prompt needed streaming, the agent did call `watch()`, but every consumer it built could lose events: the resume token (`change._id`) was never saved and there was no `resumeAfter` on startup. Error handling was `process.exit`, a TODO, or nothing. Webhook calls ran inside the handler with no limit on concurrency. One sample used `watch([])`, which ships every change to the client. None of the samples set `maxAwaitTimeMS`, and none of the READMEs mentioned the multishard requirements. In every one of these builds the agent loaded `documentdb-driver` and `documentdb-connection` and found nothing about change streams.

## Why it matters

These counts come from one experiment run: 100 Azure DocumentDB sample prompts, gpt-5-mini, this kit, and the DocumentDB/Azure/Learn MCP servers. Treat them as indicative.

- **83 of 100 samples** answered the cold question "Are change streams supported, and does anything have to be enabled first?" wrongly. Across those 83 samples there are 86 findings: 29 wrong, 54 partly wrong and 3 outdated. Cold answers show the model's priors before it reads anything, and correcting those priors is the kit's job. The graders flagged a build risk in these cases: polling, a change-feed-style design, or a made-up precondition.
- **8 of those samples** built change-stream code or needed it, and the audit stage flagged 17 violated practices in them. These were missing resume-token checkpoints, missing restart handling, client-side filtering and missing multishard notes. In one sample, the agent's own `watch_once.js` check timed out, and the agent had nothing in the kit to help it debug. (The script inserted right after calling `watch()` without awaiting cursor initialisation, so the timeout is a client-side race, not a service-side enablement requirement; see DECISIONS.md, change streams, single-shard item.)

"Watch a collection and react" is one of the most common shapes of sample an agent is asked to build. The tutorial-style consumer works in a demo but loses events without any error after a restart or failover.

## Proposed change (one PR)

The facts below (multishard change streams and `updateDescription` are preview, the Rebalancer conflict, the 400 MB active change log, the 35-day historical window, no enablement step on single-shard clusters) are settled from the Learn change-streams page (ms.date 2026-11-16) and the experiment runs; see `findings/phase4/DECISIONS.md`, change streams. What is still open (the non-resumable-token error code, the `previewFeatures` value for the multishard toggle, GA status of single-shard change streams, the per-tier historical window, the reverse-order Rebalancer behaviour, `resumeAfter` across the 400 MB boundary, and the `updateDescription` aggregation-pipeline exclusion) is written into the rules as "undocumented; do this instead" so the PR does not block on them.

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

- [cs-availability](cs-availability.md) — Change streams are supported natively via `watch()`. Do not poll, do not port a Cosmos DB change-feed design, and never gate on `serverVersion`. Not available in the local `documentdb-local` container.
- [cs-multishard](cs-multishard.md) — On multishard clusters, enable the preview feature "Change streams for multishard clusters" in the portal (Rebalancer must be off; no CLI/IaC value is documented); no global ordering across shards.
- [cs-durable-consumer](cs-durable-consumer.md) — Checkpoint the resume token and cluster time after the work is durable, resume with `resumeAfter`, restart with backoff after errors and failover, fall back to `startAtOperationTime` (historical replay, up to 35 days), keep handlers short and idempotent.
- [cs-pipeline-and-events](cs-pipeline-and-events.md) — Filter server-side with `$match`; supported stages; `updateLookup`, pre-images and `updateDescription` (preview) opt-ins.

For snapshots or aggregates over large collections, prefer an updater driven by change streams over a periodic full recompute.

## References

- [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams) — Resume a change stream, Recovering streams from historical checkpoints, pre-images, updateDescription (preview), Multi-shard change streams (preview), Limitations
- [$changeStream operator](https://learn.microsoft.com/documentdb/query/operators/aggregation/$changestream) — fullDocument options
- [Scale a cluster — Rebalance data](https://learn.microsoft.com/azure/documentdb/how-to-scale-cluster) — the preview Rebalancer toggle and sh.startBalancer()
- [Restore a cluster — Backups](https://learn.microsoft.com/azure/documentdb/how-to-restore-cluster) — 35-day retention behind the historical window
```

`cs-availability.md`: Azure DocumentDB (`Microsoft.DocumentDB/mongoClusters`) supports standard MongoDB change streams through `watch()`. Insert, update, replace and delete events have the usual shape (`_id` resume token, `operationType`, `ns`, `documentKey`, `fullDocument`). This is not the Azure Cosmos DB for MongoDB (RU) change feed, and there is no "API version" or "compatibility level" to check. `$changeStream` is supported on every server version (5.0 to 8.0). The Learn change-streams page lists `showExpandedEvents` as unsupported (the `$changeStream` operator page lists it as a parameter; treat it as unsupported), and `$changeStreamSplitLargeEvent` is unsupported on all versions. Single-shard clusters need no enablement step: the Learn page's "Get started" opens `collection.watch()` directly in six languages, and the only enablement procedure on the page is scoped to multishard clusters (run 07-lab-results-aggregator received an insert event on the experiment's M30 cluster with no toggle). If `watch()` fails with an operation error on a multishard cluster, check that portal toggle, not the server version. `fullDocument: 'updateLookup'` has no documented tier restriction. The local `documentdb-local` container does not support `$changeStream`: `watch()` fails with `CommandNotSupported` (code 115) "Stage $changeStream is not supported yet in native pipeline" (engine issue documentdb/documentdb#50 is open), so test change-stream code against a cluster. Incorrect: an `updatedAt` polling loop, and a `serverInfo()` version check that falls back to polling. Correct: open `watch()` and persist the token (see `cs-durable-consumer`).

`cs-multishard.md`: On a multishard cluster, turn on **Settings > Features > Change streams for multishard clusters** in the portal, then check on the Features page that it shows as enabled. The feature is preview ("Multi-shard change streams (preview)" on Learn). It can't be turned on while **Rebalancer for multishard clusters** is on (Learn, step 5 Important box); the Rebalancer is itself a preview Features-page toggle driven by `sh.startBalancer()` / `sh.stopBalancer()` (how-to-scale-cluster, "Rebalance data"). Learn does not say what happens if the Rebalancer is enabled after multishard change streams, so treat the two as mutually exclusive in both directions and re-open streams with `startAtOperationTime` after any topology or rebalance operation. Learn documents only the portal path. The cluster property that carries feature toggles exists on every surface (`properties.previewFeatures` in ARM/Bicep and REST, `az documentdb mongocluster create|update --preview-features`, Terraform `azurerm_mongo_cluster.preview_features`; Learn uses `FullTextSearch` for full-text search and `ShardRebalancer` for the Rebalancer), but no primary source names the value for multishard change streams, so tell the user to flip the portal toggle and check it, and do not invent an `az`/ARM/Bicep value. If a user insists on IaC, point to the full-text-search overview's `az rest` PATCH / AzAPI pattern and warn that `azurerm` `preview_features` forces cluster recreation, so use `azapi_update_resource` plus `lifecycle.ignore_changes`. Learn shows no toggle for single-shard clusters. Multishard deployments do not preserve global event ordering, so order by a field you control or per `documentKey`. Going from single-shard to multishard breaks resumability, so a scale-out runbook needs a fresh start from `startAtOperationTime`. Agent checklist before writing `watch()` against a cluster you did not create: (1) is it multishard, and if so, is the feature enabled with the Rebalancer off; (2) does the consumer persist `change._id` and `clusterTime`; (3) are the `collMod` opt-ins it needs in place; (4) does the sample README say all of this.

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
- Learn says cursors must be reopened after failover and that resume still works. The loop does exactly this. The reliability page says in-flight requests that were not acknowledged before an HA failover can fail and must be retried by the client; no error code is documented for that window, so treat connection errors during failover as transient.
- Persist both `change._id` and `change.clusterTime`. Standard change streams are limited to events in the active 400 MB change log; once rotated, older entries are archived, and historical change streams retrieve the archived logs transparently so a stream can be replayed or resumed from a past timestamp. Resuming inside the active log is cheap; a historical replay costs more (run large replays when traffic is low, and keep extra storage on clusters of 128 GB or less). Learn's only historical example uses `startAtOperationTime`, and whether `resumeAfter` alone crosses the 400 MB boundary is not stated, which is why the loop falls back to the stored `clusterTime`.
- Historical recovery reaches back up to 35 days or the cluster initialization point, whichever is earlier (Learn ties it to PITR log integration; backups are retained 35 days on M30+ and 7 days on burstable tiers, and the page does not say whether the window shrinks on burstable tiers). Pre-images are not available when processing historical logs. Beyond the replay window, alert an operator.
- Learn documents no change-stream error code. `isTokenNotResumable()` must match on the server error generically (any non-transient error on open or resume); do not hard-code MongoDB's 286 `ChangeStreamHistoryLost` or the engine table's 40647 `ChangeStreamBadResumeToken`, neither of which is documented for the service.
- A separate worker drains `outbox` with a concurrency limit (for example `p-limit(8)`), makes the webhook call, retries with its own backoff, and never blocks the stream.
- Include a restart test: insert 3 documents, kill the consumer, insert 2 more, restart, and assert that exactly 2 new events are handled. Await the cursor's first `getMore` (or the driver's `init` event) before inserting the test documents.

`cs-pipeline-and-events.md`:
- Don't use `watch([])` when only some events matter. Filter on the server with `$match` on `operationType` or `fullDocument.<field>`. The supported stages are `$match`, `$project`, `$addFields`, `$set` and `$unset`.
- Ask for `fullDocument: 'updateLookup'` only when you need the post-update document. The `$changeStream` operator page lists `default`, `updateLookup`, `whenAvailable` and `required`; no tier restriction is documented.
- Pre-images: run `db.runCommand({ collMod: "<coll>", changeStreamPreAndPostImages: { enabled: true } })`, then call `watch()` with `fullDocumentBeforeChange: "whenAvailable"`. Pre-images cover only update, delete and replace events. They add write amplification, and they are not available when processing historical logs. Pre-images carry no preview label on Learn.
- `updateDescription` is preview and opt-in per collection ("updateDescription for field-level changes in change streams (preview)" on Learn): run `db.runCommand({ collMod: "<coll>", enableUpdateDescription: { enabled: true } })` first; without it update events carry no `updateDescription`, even though an earlier, unlabelled sub-section of the same Learn page shows it without the opt-in. Learn's Limitations bullet says `updateDescription` isn't supported for update events within aggregation pipelines while update operators are supported; the rule should quote that bullet rather than restate it, because its exact scope is unclear [needs SME confirmation] (open question 7).
- These `collMod` options change what an event contains. They do not control whether a stream can be opened.

### 2. Edits to existing files (one each)

- `skills/driver/SKILL.md`: append `Also routes change-stream work (watch(), resume tokens) to documentdb-change-streams.` to the `description`, and add under `## Rules`:

  ```markdown
  - Building a watcher, listener or trigger with `collection.watch()`? See the `documentdb-change-streams` skill.
  ```

- `skills/sharding/SKILL.md`: append `, or when an app on a multishard cluster uses change streams (watch())` to the "Use when" clause of the `description`, and under Rules, in the `sharding-logical-vs-physical` bullet, add: `Change streams on a multishard cluster need the preview "Change streams for multishard clusters" portal toggle, which cannot be enabled while the preview Rebalancer toggle is on; a single-shard to multishard transition breaks change-stream resumability; see documentdb-change-streams.` (The sharding skill's wording that adding shards rebalances automatically is a separate sharding filing; this PR only adds the change-stream cross-reference.)
- `skills/high-availability/SKILL.md`, under Rules: `After an HA failover, change-stream cursors must be reopened; resume with the saved token (see documentdb-change-streams).`
- `skills/azure-deployment/SKILL.md`, Step 9: `- **Change streams on a multishard cluster.** If shardCount > 1 and the app uses watch(), enable Settings → Features → Change streams for multishard clusters in the portal (preview; Rebalancer must be off). Learn documents the portal path only; no previewFeatures value for this toggle is published, so do not add one to the Bicep.`
- `scenarios/ecommerce-advanced/README.md` (line 59) and `scenarios/ecommerce-advanced/data/cases/change-streams.json`: the README asks the compatibility test to compare `updateDescription` across MongoDB and Azure DocumentDB, but the case file never runs `collMod` with `enableUpdateDescription`, so on Azure DocumentDB (where `updateDescription` is preview and opt-in per collection) the comparison fails or is vacuous. Either add the `collMod` enablement to the case setup or drop the `updateDescription` comparison; also handle the `replace` event's `fullDocument` and the resume-token shape differences the Learn page shows.
- `docs/SKILLS.md`, rule-folder table, new row:

  ```markdown
  | [`change-streams/`](../skills/change-streams/) | `cs-` | Availability (not RU change feed, not version-gated, not in documentdb-local), multishard preview toggle and Rebalancer conflict, limitations, server-side `$match`, pre-images/updateDescription (preview), durable consumer with resume-token checkpoints, backoff and historical fallback (400 MB active log, 35-day replay) |
  ```

- `AGENTS.md`: a skills-table row for `documentdb-change-streams`, and a routing line: `- **Reacting to inserts / updates / deletes in real time (alerts, CDC, cache invalidation, "change feed")** → documentdb-change-streams`.
- `CHANGELOG.md`: `Added change-streams rule folder (4 rules).`

Not in this PR: the workflow-run and agent-memory rules from draft 093 (a separate durable-state proposal); a documentdb-mcp command that reports change-stream availability (the MCP clone has no change-stream code at all); and Learn feedback on the change-streams page (the Node.js "Get started" sample uses `watch([])` and `process.exit(1)`; the duplicated `updateDescription` section; the missing `previewFeatures` value; the missing error code), which belongs in the Learn filings.

## Evidence

- `runs/02-real-time-event-stream-ingestion/20261124-203233/05-audit.json`
- `runs/16-atm-network-status-monitor/20261124-202405/05-audit.json`
- `runs/06-order-history-timeline-agent/20261124-183612/02-readiness.json`
- `runs/03-substitute-product-finder/20261124-183232/02-readiness.json`
- `runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json`
- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json`
- `runs/07-lab-results-aggregator/20261124-194018/03-build.md` (change stream observed working on the experiment cluster with no enablement step)

## Resolved

retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

400 MB active change log: settled 2026-11-25 (documented). Standard change streams are limited to events in the active 400 MB change log; once rotated, entries are archived and historical change streams retrieve them transparently, so 400 MB is where the active log ends and historical retrieval begins, not where resumption fails. Source: https://learn.microsoft.com/en-us/azure/documentdb/change-streams ("Recovering Streams from Historical checkpoints" and its Important box).

Historical window: settled 2026-11-25 (documented). With PITR log integration, stream recovery extends up to 35 days or the cluster initialization point, whichever is earlier; pre-images are not available for historical processing. Sources: https://learn.microsoft.com/en-us/azure/documentdb/change-streams (Important box; Limitations); https://learn.microsoft.com/en-us/azure/documentdb/how-to-restore-cluster ("Backups").

Rebalancer conflict: settled 2026-11-25 (documented). Multishard change streams still cannot be enabled while "Rebalancer for multishard clusters" is enabled; the Rebalancer is itself a preview Features-page toggle. Sources: https://learn.microsoft.com/en-us/azure/documentdb/change-streams ("Multi-shard change streams (preview)", step 5 Important box); https://learn.microsoft.com/en-us/azure/documentdb/how-to-scale-cluster ("Rebalance data").

Preview status: settled 2026-11-25 (documented). Multishard change streams and `updateDescription` are both preview; `updateDescription` is enabled per collection with `collMod enableUpdateDescription`; pre-images carry no preview label. Source: https://learn.microsoft.com/en-us/azure/documentdb/change-streams (headings "Multi-shard change streams (preview)" and "updateDescription for field-level changes in change streams (preview)").

Single-shard enablement: settled 2026-11-25 (observed_in_runs). No enablement step is documented for single-shard clusters and the experiment observed a change stream working without one; the one timed-out run was a client-side race. Sources: https://learn.microsoft.com/en-us/azure/documentdb/change-streams ("Get started"); runs/07-lab-results-aggregator/20261124-194018/03-build.md; runs/02-real-time-event-stream-ingestion/20261124-203233/app/scripts/watch_once.js.

CLI/ARM/Bicep property (what exists): settled 2026-11-25 (documented). The toggle carrier exists on every surface (`properties.previewFeatures` in ARM/Bicep/REST, `az documentdb mongocluster --preview-features`, Terraform `preview_features`, free-form strings), but no primary source names the value for multishard change streams; the value itself stays open. Sources: https://learn.microsoft.com/en-us/azure/templates/microsoft.documentdb/mongoclusters; https://learn.microsoft.com/en-us/cli/azure/documentdb/mongocluster; https://github.com/hashicorp/terraform-provider-azurerm/blob/main/website/docs/r/mongo_cluster.html.markdown; https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview.

`fullDocument: 'updateLookup'` tiers: settled 2026-11-25 (documented). No tier restriction is documented; the option is listed on the `$changeStream` operator page and used in the Learn C# sample. Sources: https://learn.microsoft.com/en-us/documentdb/query/operators/aggregation/$changestream; https://learn.microsoft.com/en-us/azure/documentdb/limitations; https://learn.microsoft.com/en-us/azure/documentdb/free-tier.

Local container: settled 2026-11-25 (engine_source). `documentdb-local` does not support `$changeStream`; `watch()` fails with CommandNotSupported (code 115), issue documentdb/documentdb#50 open. Sources: https://documentdb.io/docs/reference/operators/aggregation/$changestream/; https://github.com/documentdb/documentdb/issues/50.

## Open questions

1. [needs SME confirmation] What error (code and message) does the service return for a resume token that can no longer be resumed, for example one older than both the active 400 MB log and the 35-day historical window? No Learn page documents any change-stream error; the engine tables list `ChangeStreamBadResumeToken` (40647) but nothing raises it. The rule's `isTokenNotResumable()` needs it.
2. [needs SME confirmation] What is the exact `previewFeatures` string (ARM/Bicep/REST/CLI/Terraform) that enables "Change streams for multishard clusters", and is non-portal enablement supported at all? Learn documents the portal path only; `FullTextSearch` and `ShardRebalancer` show the mechanism for other features.
3. [needs SME confirmation] Are single-shard change streams generally available, or still preview? The current Learn page labels only multishard change streams and `updateDescription` as preview; Microsoft DevBlogs announced GA on 2025-05-21, but no Learn page records it.
4. [needs SME confirmation] Is the historical change-stream window 35 days on every paid tier, or 7 days on burstable tiers (M10, M20, M25), and does it exist on the free tier, which has no backup?
5. [needs SME confirmation] Does enabling the Rebalancer on a cluster that already has multishard change streams enabled fail, disable the streams, or silently break resumability? Only the other direction is documented.
6. [needs SME confirmation] Does `resumeAfter` with a token that has rotated out of the active 400 MB log transparently fall back to archived logs, or must the client switch to `startAtOperationTime`? Learn's only historical example uses `startAtOperationTime`.
7. [needs SME confirmation] Is the `updateDescription` exclusion limited to aggregation-pipeline updates, with update operators supported? Learn's Limitations bullet ("UpdateDescription isn't supported for update events within aggregation pipelines. However, update operators are supported.") is ambiguous.

## Source drafts

105-change-stream-consumers-have-no-durability-resume-tokens-nev.md, 032-believes-vcore-change-streams-are-absent-or-crippled-like-co.md, 033-believes-change-streams-are-on-by-default-cluster-wide-unawa.md, 034-believes-azure-documentdb-change-streams-have-full-mongodb-s.md, 035-believes-change-stream-availability-is-gated-by-the-cluster-.md, 093-durable-state-patterns-change-stream-resume-tokens-workflow-.md

sample_count 83 is the distinct samples behind the Q12 findings in 032, 033, 034 and 035 (86 findings). The 8 samples from 105 and 6 of the 7 from 093 fall inside those 83. The seventh 093 sample (04-regulatory-reporting-orchestration) has only a workflow-run finding, which this PR leaves out, so it is not counted. REVIEW.md section 1 also lists draft 041 among the change-stream overlaps; its change-stream part is not in this filing's member list and should be dropped from 041 when it is filed.
