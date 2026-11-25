---
title: "Agent Kit: document Azure DocumentDB change-stream limitations (no global ordering across shards, failover/topology resume rules, 400 MB log) and a resume/reinitialize pattern"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 1
findings: 1
bucket: confusion-Q12
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Document Azure DocumentDB change-stream limitations and a resume/reinitialize pattern in the kit

## What happens today

No skill in the kit mentions change streams. `grep -rniE "change.?stream|resume.?token|\.watch\(" skills/ knowledge-base/` returns nothing. The Learn page (https://learn.microsoft.com/azure/documentdb/change-streams#limitations) lists real differences from MongoDB server/Atlas behaviour, but an agent that has installed the kit never sees them, so it falls back on what it knows about Atlas.

In the readiness experiment (100 Azure DocumentDB sample prompts, gpt-5-mini, kit skills + DocumentDB/Azure/Learn MCP servers), the cold quiz question "Are change streams supported, and does anything have to be enabled first?" produced this build risk for sample 15-cohort-analysis-backend:

> If the app assumes full MongoDB change-stream semantics (global ordering across shards, resumability across topology changes) it may break on resume behavior or miss cases where Azure-managed topology changes require cursor reinitialization.

The same run's doc-gaps file records that the agent searched the installed skills (`documentdb-data-modeling`, `documentdb-monitoring`) for change-stream guidance and found none.

## Why it matters

- The specific "Atlas semantics" assumption was recorded in only 1 of 100 samples. It is part of a larger gap: the change-streams question was answered wrong or partly wrong in 88 of 118 runs, mostly because the kit gives the model nothing to correct its MongoDB/Cosmos DB assumptions.
- 7 of the generated apps call `.watch()` in their own code (02-real-time-event-stream-ingestion, 03-portfolio-tracker-with-live-alerts, 07-lab-results-aggregator, 09-trade-settlement-tracker, 12-hospital-bed-occupancy-tracker, 16-atm-network-status-monitor, 19-proactive-outreach-orchestration). None of them persists a resume token, reinitializes the cursor after failover or guards against cross-shard ordering. Each could lose or reorder events without any error on an HA failover or a scale-out to multiple shards.
- The facts are already on Learn. This is only a kit-coverage gap, so the fix is a text-only PR.

## Proposed change

### 1. New rule file: `skills/change-streams/change-streams-limitations-and-resume.md`

(Uses the rule-folder format of the other skills: Why it matters / Incorrect / Correct / References.)

````markdown
# change-streams-limitations-and-resume

**Category:** Change Streams · **Priority:** HIGH

## Why it matters

Azure DocumentDB supports `watch()` with resume tokens (`resumeAfter`),
`startAtOperationTime`, customization pipeline stages (`$match`, `$project`,
`$addFields`, `$set`, `$unset`), pre-images (`fullDocumentBeforeChange`) and
`updateDescription` (preview). Some MongoDB server/Atlas behaviours do not
apply. The documented limitations are:

- **Multi-shard deployments do not preserve global event ordering.** Do not rely
  on arrival order across shards. Order by a field you control (a sequence
  number, or per `documentKey`).
- **Moving from a single-shard to a multi-shard topology breaks change stream
  resumability.** Saved resume tokens cannot be used across that transition, so
  include a fresh start (for example `startAtOperationTime`) in the scale-out
  runbook.
- **Change stream cursors must be reinitialized after failover.** The resume
  capability is preserved: reopen with the saved token in `resumeAfter`.
- **Standard change streams only reach events in the active 400 MB change log.**
  Rotated entries are archived. Historical change streams (`startAtOperationTime`)
  read the archived logs, back to 35 days or the cluster initialization point,
  whichever is earlier. Run historical replays during low traffic.
- **`showExpandedEvents` is not supported.**
- **`updateDescription` (preview)** must be enabled per collection
  (`collMod: <coll>, enableUpdateDescription: { enabled: true }`). It is not
  produced for updates issued as aggregation-pipeline updates; updates that
  use update operators are supported.
- **Pre-images** need `collMod: <coll>, changeStreamPreAndPostImages: { enabled: true }`,
  cover only update/delete/replace events, add write amplification, and are
  not available when replaying historical logs.
- **Multi-shard change streams are a preview feature.** Enable them per cluster
  in the portal (Settings → Features → "Change streams for multishard clusters").
  They cannot be enabled while "Rebalancer for multishard clusters" is on.

## Incorrect

```python
stream = coll.watch()            # no resume token persisted
for change in stream:            # dies on failover; a restart loses events
    handle(change)               # assumes events arrive in global order
```

## Correct

```python
token = load_token()                         # durable store
start_ts = None
while True:
    try:
        if token:
            opts = {"resume_after": token}
        elif start_ts:
            opts = {"start_at_operation_time": start_ts}   # historical change stream
        else:
            opts = {}
        with coll.watch(**opts) as stream:
            for change in stream:
                handle(change)               # idempotent; order per documentKey only
                token = change["_id"]; save_token(token)
                start_ts = change.get("clusterTime", start_ts)
    except PyMongoError as e:
        if is_resume_token_unusable(e):      # e.g. after a single-to-multi-shard transition
            token = None                     # re-seed from start_ts / last checkpoint
        time.sleep(backoff())                # failover: loop reopens with the same token
```

Checklist for agents generating consumers:
1. Persist `change["_id"]` after each **successfully processed** event.
2. Wrap the loop in a reconnect-and-`resumeAfter` retry, because the cursor must be reinitialized after HA failover.
3. If a token cannot be used, re-seed from a stored timestamp with `startAtOperationTime` instead of failing.
4. Make handlers idempotent, and do not assume ordering across shards.
5. If the cluster has more than one physical shard, confirm that the multi-shard change-streams feature is enabled before relying on a cluster-wide stream.

## References

- [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams): Resume a change stream, Historical checkpoints, Multi-shard change streams (preview), Limitations
- Related: `high-availability/` (failover behaviour), `sharding/` (single- vs multi-shard topology)
````

### 2. Register the rule

- `skills/change-streams/SKILL.md`: if the change-streams skill proposed in the companion issue has not landed yet, create it with front matter `name: documentdb-change-streams` and a trigger description covering `watch()`, CDC, resume tokens and "change feed", then list the rule under `## Rules`. If that note landed as a section in another skill instead, append this content there.
- `docs/SKILLS.md` rule-folder table and `AGENTS.md` skill table: add a `change-streams/` row with prefix `change-streams-`.

### 3. One-line cross-references in existing skills

- `skills/high-availability/SKILL.md`, under `## Rules`: "HA failover requires change-stream cursors to be reinitialized; reopen with `resumeAfter` (the token stays valid). See `change-streams/`."
- `skills/sharding/SKILL.md`, under `## References` → Related: "`change-streams/` (multi-shard clusters do not preserve global event ordering; a single-to-multi-shard transition breaks resumability; multi-shard streams are a portal-enabled preview that conflicts with the multishard Rebalancer)."

## Evidence (run folders from the experiment)

- `runs/15-cohort-analysis-backend/20261124-205336/02-readiness.json`: confusions[Q12], outcome `partly_wrong`, build_risk quoted above.
- `runs/15-cohort-analysis-backend/20261124-205336/doc-gaps.md`, section "[high] Change-feed / incremental-snapshots guidance": the agent searched the installed skills and found nothing on change streams.
- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json`: the Q12 build_risk says the builder must handle resume tokens, but `app/index.js` calls `.watch()` without persisting one.
- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` and its `app/`: a `.watch()` consumer with no resume or failover handling.
- `runs/02-real-time-event-stream-ingestion/20261124-203233/02-readiness.json` and its `app/`: the same pattern, and the cold answer reached for the Cosmos DB change feed instead.

## Verification

### 1. Already covered? confirmed (not covered in the target)
- Ran `grep -rniE "change.?stream|resume.?token|\.watch\(|changestream"` over `documentdb-agent-kit/skills` and `documentdb-agent-kit/knowledge-base` and got zero hits. None of the 17 skill folders (azure-deployment, connection, data-modeling, driver, full-text-search, high-availability, indexing, local-deployment, mcp-setup, monitoring, natural-language-querying, query-optimization, query-optimizer, security, sharding, storage, vector-search) covers change streams. `skills/high-availability/` holds only backup-retention, cross-region-replica and enable-for-production rules. `skills/sharding/` holds only hot-partition and how-to-commands rules.
- microsoft/documentdb-mcp: no change-stream content either, but that is not the fix target.
- Learn already documents all the limitations and includes a resume-token persistence sample (https://learn.microsoft.com/en-us/azure/documentdb/change-streams, "Resume a change stream" and "Limitations"), so this is a kit gap rather than a Learn gap.

### 2. Premise true? confirmed (wording corrections applied)
Each limitation matches the Learn change-streams page (updated 2026-11-17). Its Limitations section says that a cluster topology transition from single-shard to multi-shard breaks change stream resumability, that multi-shard deployments don't preserve global event ordering, and that cursors must be reinitialized after failover while resume capability remains preserved. The same section lists `updateDescription`, pre-image and `showExpandedEvents` restrictions, and the page also covers the 400 MB active change log, 35-day PITR-backed historical recovery, the multi-shard preview enabled under Features with the Rebalancer conflict, and `collMod` for `enableUpdateDescription` / `changeStreamPreAndPostImages`. The generated-app claim was confirmed: 7 run `app/` folders call `.watch()`.
Corrections applied to the body:
- `startAfter` was removed from the list of supported resume options. Learn names `startAt`, `resumeAfter` and `startAtOperationTime`, and the rule keeps only what Learn states.
- The `updateDescription` limitation was restated. Learn says it is not supported for update events issued through aggregation pipelines, while update operators are supported. The draft's "unavailable inside aggregation pipelines" could be read as covering the change-stream customization pipeline.
- Two limitations were added: pre-images are unavailable for historical processing and cover only update/delete/replace events.
- The "Correct" code sample was fixed. The original assigned `start_at_operation_time` options inside the except branch, and the next loop iteration discarded them, so the historical fallback never ran.
- The failover wording now uses Learn's term "reinitialized", and the cross-reference names the Rebalancer conflict.

### 3. Maintainer skeptic? confirmed
The PR names the exact files (new `skills/change-streams/change-streams-limitations-and-resume.md`, `skills/change-streams/SKILL.md`, `docs/SKILLS.md`, `AGENTS.md`, one-line additions to `skills/high-availability/SKILL.md` and `skills/sharding/SKILL.md`), follows the kit's rule format, and is specific to Azure DocumentDB, with every behaviour sourced from Learn. A maintainer could accept it as written. Its only dependency is the companion change-streams skill note, and the body says how to merge if that note lands first.

## Finding ids

- F2492
