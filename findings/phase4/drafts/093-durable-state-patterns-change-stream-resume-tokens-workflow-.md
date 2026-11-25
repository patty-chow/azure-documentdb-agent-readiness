---
title: "Add a `durable-state` rule-folder skill: change-stream checkpointing, resumable workflow runs, agent-memory schema"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 7
findings: 7
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add `skills/durable-state/`: change-stream checkpointing, resumable workflow runs, agent-memory schema

## What happens today

The kit has no change-streams skill and no rule about persisting application state between process restarts. `docs/SKILLS.md` lists the rule folders (data-modeling, sharding, query-optimization, indexing, driver, vector-search, full-text-search, high-availability, storage, security, monitoring, local-deployment) and none mention resume tokens, checkpoints, workflow runs or agent memory. The only change-stream material in the repo is the `scenarios/ecommerce-advanced` test fixture (`data/cases/change-streams.json`), which is not a skill and is not loaded by agents.

When an agent builds a sample with a long-running watcher or a multi-step/multi-agent flow, it therefore falls back to training priors and ships code that persists only the final result:

- **Change-stream watchers** (3 samples, native driver and Mongoose) open `collection.watch()` but never store the resume token. One leaves a `// TODO: persist resume token` in `changeStream.on('error')`; on restart they reprocess or miss events.
- **Orchestrators** (2 samples) log step timestamps into a `workflow_runs` or `preauth` document but cannot resume from the last completed step or dedupe a retry; one writes only the final submission, so a transient failure loses `reviewResult`/`draftDocument` and can double-submit.
- **Agent memory** (2 samples) is either an in-process `Map` (lost on restart, unsafe across processes) or a hand-rolled `agent_memory` collection with no unique dedupe key, which the audit flagged as a duplicate-order risk under concurrent runs.

## Why it matters

7 of 100 generated samples hit this. In the audit stage the checks "Persist resume token", "Change stream checkpoint frequency", "Persist intermediate state" and "Workflow-run resumability" were marked **violated** or **prior_knowledge_only** (no discoverable source in the kit).

The Learn page [Change streams](https://learn.microsoft.com/en-us/azure/documentdb/change-streams#resume-a-change-stream) does show the store-and-resume pattern: per-language consumers (Python, Java, C#, Ruby, Node.js) call `loadResumeToken()` on startup, pass `resumeAfter`, and call `saveResumeToken(change._id)` after each event, and the page says to "Store it durably". But the helper that actually persists the token is not shown, the agent did not reach that page from the kit, and the page covers nothing about workflow checkpoints or agent memory. The kit is where the agent looks first, so it should carry a short, copyable rule that links to Learn.

Gallery samples are copied by developers. Azure DocumentDB connection strings use `retrywrites=false`, so the driver does not retry writes for you; the kit's `connection` skill already tells agents to write application-level retries (`withRetry` with exponential backoff). Application-level retries are only safe when the step they repeat is idempotent, and a watcher without checkpointing or an orchestrator without a dedupe key is not.

## Proposed change

New rule-folder skill `skills/durable-state/` (prefix `durable-`), same shape as `skills/data-modeling/` (why it matters -> incorrect -> correct -> references). Files:

### `skills/durable-state/SKILL.md`

```markdown
---
name: documentdb-durable-state
description: Durable application state on Azure DocumentDB: change-stream resume-token checkpointing, resumable multi-step workflow runs, and persisted agent memory with dedupe keys. Use when writing a change-stream watcher (collection.watch / Mongoose Model.watch), an orchestrator or saga that runs several steps, a multi-agent or LangChain app that keeps memory between turns, or when reviewing code that must survive a restart, retry safely, or avoid duplicate side effects.
license: MIT
---

# Durable State: Azure DocumentDB

Guiding principle: **anything a process must not redo after a restart belongs in a document with a unique key, written before the side effect is acknowledged.**

## Rules

- [durable-change-stream-checkpoint](durable-change-stream-checkpoint.md): Persist the resume token after each event or batch; pass `resumeAfter` on startup; fall back to `startAtOperationTime` when the token is no longer in the active change log.
- [durable-workflow-run-resume](durable-workflow-run-resume.md): One `workflow_runs` document per run, keyed by a unique `dedup_key`; per-step updates with status, timestamps and a version check; skip completed steps on resume.
- [durable-agent-memory-schema](durable-agent-memory-schema.md): Persist agent memory in a collection with a unique `(agent_name, item_id, event_hash)` index; use ephemeral memory only for single-process demos.
```

### `skills/durable-state/durable-change-stream-checkpoint.md`

Priority HIGH. Incorrect example: `watch()` with no token storage and an `on('error')` that only logs. Correct example (Node.js driver; the Mongoose variant uses `Model.watch([], { resumeAfter })`, as on the Learn page):

```javascript
const checkpoints = db.collection('watch_checkpoints');
await checkpoints.createIndex({ watcherId: 1 }, { unique: true });

async function startWatcher(watcherId, coll, pipeline, handle) {
  const cp = await checkpoints.findOne({ watcherId });
  const opts = { fullDocument: 'updateLookup' };
  if (cp?.lastResumeToken) opts.resumeAfter = cp.lastResumeToken;

  const stream = coll.watch(pipeline, opts);
  for await (const change of stream) {
    await handle(change);                       // must be idempotent (see durable-workflow-run-resume)
    await checkpoints.updateOne(
      { watcherId },
      { $set: { lastResumeToken: change._id, lastProcessedTs: new Date() } },
      { upsert: true });
  }
}
```

Document shape: `{ watcherId: 'trades-failed', lastResumeToken: <change._id>, lastProcessedTs: ISODate }`. Azure DocumentDB-specific notes to include:

- Checkpoint per event, or per small batch if throughput is high; either way the handler must be idempotent because events after the last checkpoint are redelivered.
- Wrap the watcher in a reconnect loop with exponential backoff. Learn lists that "Change stream cursors must be reinitialized after failover events, while resume capability remains preserved", so reopen with the stored token after a failover.
- Resuming with `resumeAfter` works while the token is still in the active change log (Learn: the active change log is 400 MB). If the token has rotated out, resume from `startAtOperationTime` built from `lastProcessedTs` (historical change streams, which Learn says can reach back up to 35 days or to cluster initialization, whichever is earlier) instead of silently restarting from "now". Only skip ahead to "now" if the business accepts lost events, and log it.
- On a multishard cluster, change streams require the "Change streams for multishard clusters" preview feature (cannot be enabled while Rebalancer for multishard clusters is on); global event ordering is not preserved across shards, and a topology change from single-shard to multishard breaks resumability.
- Supported pipeline stages in `watch()` are `$addFields`, `$match`, `$project`, `$set`, `$unset`.
- Include a restart test: start the watcher, insert 3 docs, kill it, insert 2 more, restart, assert exactly 2 new events were handled.

References: https://learn.microsoft.com/en-us/azure/documentdb/change-streams#resume-a-change-stream and the Limitations and Multi-shard change streams sections of the same page.

### `skills/durable-state/durable-workflow-run-resume.md`

Priority HIGH. Document shape:

```javascript
{
  _id: 'reg-report-2026-11-24',          // run_id
  dedup_key: 'reg-report:2026-11-24',    // unique index; a retry reuses the same run
  status: 'running',                     // 'running' | 'completed' | 'failed'
  version: 3,                            // bumped on every write; used for optimistic checks
  start_ts, end_ts,
  last_checkpoint: 'aggregate',          // name of last completed step
  steps: [ { name: 'extract',   status: 'completed', started_ts, ended_ts, result_ref },
           { name: 'aggregate', status: 'completed', started_ts, ended_ts, result_ref },
           { name: 'submit',    status: 'pending' } ]
}
```

Correct example:

```javascript
await runs.createIndex({ dedup_key: 1 }, { unique: true });

async function startRun(runs, runId, dedupKey) {
  // Idempotent: a retry with the same dedup_key gets the existing run back.
  await runs.updateOne(
    { dedup_key: dedupKey },
    { $setOnInsert: { _id: runId, status: 'running', version: 0, start_ts: new Date(), steps: [] } },
    { upsert: true });
  return runs.findOne({ dedup_key: dedupKey });
}

async function runStep(runs, runId, name, fn) {
  let run = await runs.findOne({ _id: runId });
  if (run.steps.some(s => s.name === name && s.status === 'completed')) return; // resume: skip
  if (!run.steps.some(s => s.name === name)) {
    await runs.updateOne(
      { _id: runId, version: run.version, 'steps.name': { $ne: name } },
      { $push: { steps: { name, status: 'running', started_ts: new Date() } }, $inc: { version: 1 } });
    run = await runs.findOne({ _id: runId });
  }
  const result = await fn();                                   // the side effect; must itself be idempotent
  const r = await runs.updateOne(
    { _id: runId, version: run.version, 'steps.name': name },
    { $set: { 'steps.$.status': 'completed', 'steps.$.ended_ts': new Date(),
              'steps.$.result_ref': result, last_checkpoint: name },
      $inc: { version: 1 } });
  if (r.matchedCount === 0) throw new Error('concurrent writer modified run ' + runId);
}
```

Also show the multi-agent variant from the pre-auth sample: write `reviewResult` and `draftDocument` into the case document as they are produced (`updateOne` with `$set` + timestamps + version check), not only the final submission. Cross-reference the `connection` skill's Retry Logic section and note that, because Azure DocumentDB connection strings set `retrywrites=false`, write retries happen in application code and therefore depend on these idempotency keys. If the collection is sharded, the unique `dedup_key` index must include the shard key (or the shard key should be `dedup_key`).

### `skills/durable-state/durable-agent-memory-schema.md`

Priority MEDIUM. Guidance: in-process memory (a `Map`, LangChain in-memory buffer memory) is acceptable only for single-process demos; gallery samples that run more than one agent or worker must persist memory. Schema:

```javascript
// agent_memory
{ agent_name: 'reorder-planner', item_id: 'SKU-123', event_hash: sha256(payload),
  kind: 'decision', content: {...}, created_ts, ttl_ts }
await mem.createIndex({ agent_name: 1, item_id: 1, event_hash: 1 }, { unique: true });
await mem.createIndex({ ttl_ts: 1 }, { expireAfterSeconds: 0 });       // optional expiry
await mem.updateOne({ agent_name, item_id, event_hash }, { $setOnInsert: doc }, { upsert: true }); // duplicate event -> no-op
```

Plus a minimal LangChain adapter (a `BaseChatMessageHistory` subclass whose `addMessage` upserts into `agent_memory` keyed by `session_id` and whose `getMessages` reads them in order), with a note that LangChain's MongoDB chat-history integrations (`MongoDBChatMessageHistory` in `langchain-mongodb` / `@langchain/mongodb`) use the same wire protocol and can be preferred once verified against Azure DocumentDB. Same sharding caveat as above for the unique index.

### Other files

- `docs/SKILLS.md`: add row `| [`durable-state/`](../skills/durable-state/) | `durable-` | Change-stream resume-token checkpointing, resumable workflow runs, persisted agent memory with dedupe keys |` to the rule-folder table.
- `CHANGELOG.md`: "Added `durable-state` rule folder (3 rules)."

If maintainers prefer not to add a folder, the same three files fit under `skills/data-modeling/` as `model-change-stream-checkpoint.md`, `model-workflow-run-resume.md`, `model-agent-memory.md`, with the `data-modeling` SKILL.md description extended to mention change streams, orchestrators and agent memory so the skill triggers.

## Evidence (run folders from the 100-sample experiment)

- `runs/02-real-time-event-stream-ingestion/20261124-203233/doc-gaps.md`: watcher with no resume-token persistence; end-to-end verification timed out.
- `runs/09-trade-settlement-tracker/20261124-201323/05-audit.json`: checks P10 "Persist resume token" and P19 "checkpoint frequency" violated; `changeStream.on('error')` is a TODO.
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/doc-gaps.md`: Mongoose watcher, no `resumeAfter`; asks for a "store and resume" snippet.
- `runs/04-regulatory-reporting-orchestration/20261124-200545/05-audit.json`: workflow_runs logged but resumability rated prior_knowledge_only; no dedup key.
- `runs/08-insurance-pre-auth-multi-agent/20261124-194215/doc-gaps.md`: intermediate reviewResult/draftDocument not persisted; duplicate-submission risk.
- `runs/09-inventory-reorder-multi-agent-system/20261125-054042/doc-gaps.md` and `runs/12-invoice-matching-reconciliation/20261124-191603/doc-gaps.md`: agent memory without dedupe key / in-process Map.

## Verification

### 1. Already covered? partially_covered

- Agent kit: not covered. `grep -rniE "change.?stream|resumeAfter|\.watch\(|resume ?token|checkpoint|agent.?memory|workflow_run"` over `skills/` and `knowledge-base/` returns nothing; the only change-stream hits in the repo are the `scenarios/ecommerce-advanced` fixture (README, `scripts/validate.mjs`, `data/cases/change-streams.json`). `docs/SKILLS.md` has no change-stream, workflow or memory row. Idempotency appears only incidentally (`skills/storage/storage-disk-hydration-sequencing.md`, `skills/local-deployment/local-sample-data-management.md`).
- documentdb-mcp: no change-stream or resume-token material (grep for `resumeAfter|change stream|watch(` returned nothing).
- Learn: partially covered. https://learn.microsoft.com/en-us/azure/documentdb/change-streams (updated 2026-11-16) has a "Resume a change stream" section stating the `_id` of each event is the resume token, to "Store it durably and pass it back", and per-language consumers that call `loadResumeToken()` / `saveResumeToken(change._id)`. The helper bodies (where the token is stored) are not shown, and nothing covers workflow-run checkpoints or agent memory. The draft's original claim that Learn explains `resumeAfter` "conceptually" with no store-and-resume snippet was corrected in the body.

### 2. Premise true? confirmed (secondary claims corrected)

The core premise (kit has no durable-state guidance; agents shipped watchers and orchestrators without checkpoints) holds. Corrections applied to the body:

- The draft said the kit's `connection` skill says "retryWrites=false, design idempotent application-level retries". It does not: `skills/connection/SKILL.md` line 60 shows a connection string with `retryWrites=true`, and its "Retry Logic" section (lines 209-240) shows `retryReads: true` and a `withRetry` backoff helper with no mention of idempotency. The body now states the true fact (Azure DocumentDB connection strings use `retrywrites=false`, so write retries are application-level) and only cites the connection skill for its `withRetry` helper. (The kit's `retryWrites=true` example conflicts with the documented connection string; that is a separate issue for the connection skill.)
- Token-expiry fallback: the draft said to clear the checkpoint and reprocess "from now". Learn documents a 400 MB active change log and historical change streams via `startAtOperationTime` reaching back up to 35 days (PITR integration), so the body now recommends resuming from `startAtOperationTime` using `lastProcessedTs`.
- Added Learn's limitations: cursors must be reinitialized after failover; single-shard to multishard transition breaks resumability; no global ordering across shards; multishard requires the "Change streams for multishard clusters" preview feature, which cannot be enabled while Rebalancer for multishard clusters is on; supported `watch()` stages are `$addFields`, `$match`, `$project`, `$set`, `$unset`.
- `runStep` code bug: the original read `run.version` when `run` could be null and `$push`ed a step without creating the run document, so the first step of a new run would throw. Replaced with a `startRun` upsert keyed on the unique `dedup_key` plus a version-checked `$push`.
- Added that a unique index on a sharded collection must include the shard key (standard MongoDB-compatible rule).
- LangChain `MongoDBChatMessageHistory` exists in `langchain-mongodb` (Python) and `@langchain/mongodb` (JS); kept with "verify against Azure DocumentDB" wording.

Sources: https://learn.microsoft.com/en-us/azure/documentdb/change-streams (Resume a change stream; Recovering Streams from Historical checkpoints; Multi-shard change streams; Limitations); `skills/connection/SKILL.md` in the kit clone.

### 3. Maintainer skeptic: confirmed

Names exact files (`skills/durable-state/SKILL.md` plus three rule files, `docs/SKILLS.md` row, `CHANGELOG.md`), follows the kit's existing rule shape, and has a clear Azure DocumentDB angle for change streams (400 MB active log, `startAtOperationTime` historical fallback, failover reinitialization, multishard preview feature). The workflow-run and agent-memory rules are closer to general engineering patterns; a maintainer may ask to keep them short and tie them to DocumentDB specifics (`retrywrites=false`, unique-index-with-shard-key), which the edited body now does. Would accept with small edits; the fallback of placing the files under `skills/data-modeling/` is offered.

## Finding ids

- F0273
- F0680
- F1241
- F1576
- F2073
- F1504
- F2105
