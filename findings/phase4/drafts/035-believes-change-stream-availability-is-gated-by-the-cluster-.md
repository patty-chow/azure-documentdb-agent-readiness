---
title: "Add an Agent Kit change-streams rule stating that availability does not depend on the cluster's serverVersion"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 3
findings: 3
bucket: confusion-Q12
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add `driver-change-streams` rule: change-stream availability is not gated by `serverVersion`

## What happens today

The kit has no guidance on change streams at all (`grep -ri "change.\?stream" skills/` returns nothing; the only mention is seed data under `scenarios/ecommerce-advanced/`). Left to its own knowledge, gpt-5-mini answers the readiness question "Are change streams supported, and does anything have to be enabled first?" with an RU-era prior: features are unlocked by the account's MongoDB API/compatibility version, so it tells the builder to check the cluster's configured `serverVersion` or "compatibility level" before relying on `$changeStream`, and in two of three runs it first denied support entirely and pointed at Cosmos DB change feed.

What is actually true for Azure DocumentDB (vCore):

- The MQL compatibility matrix (https://learn.microsoft.com/azure/documentdb/compatibility-query-language#operators) lists `$changeStream` as supported in every server-version column (5.0, 6.0, 7.0, 8.0). Only `$changeStreamSplitLargeEvent` is unsupported, and that is also version-independent.
- The change-streams page (https://learn.microsoft.com/azure/documentdb/change-streams) documents exactly one enablement step: the portal **Features** toggle "Change streams for multishard clusters" (preview) on multishard clusters, which cannot be on while "Rebalancer for multishard clusters" is on. No step is documented for single-shard clusters. `collMod { enableUpdateDescription }` (preview) and `collMod { changeStreamPreAndPostImages }` are optional output features, not availability gates.
- Nothing anywhere ties change streams to `serverVersion`.

## Why it matters

3 of the 100 samples in the readiness run hit this exact confusion (two graded wrong, one partly wrong). In each case the agent's grounded answer still carried a "verify your cluster's serverVersion / compatibility level" caveat into the build plan. The failure modes were: (a) proposing a polling fallback the service does not need, and (b) adding a non-existent precondition that a builder would waste time trying to verify (`az documentdb mongocluster show` exposes `serverVersion`, so the check is cheap to write and permanently misleading). Two of the runs went on to propose Learn-doc edits (a compatibility-table footnote about "very old compatibility tiers", an MQL-matrix cross-reference) that would document a condition that does not exist; those should not be made. The right place to kill the prior is the kit, since it is the only material that is loaded on every build.

## Proposed change

**1. New rule file `skills/driver/driver-change-streams.md`** (same shape as `driver-singleton-client.md`):

```markdown
# driver-change-streams

**Category:** Driver Best Practices · **Priority:** MEDIUM

## Why it matters

Azure DocumentDB supports MongoDB change streams (`collection.watch()`, `$changeStream`)
on **every supported server-version setting (5.0, 6.0, 7.0, 8.0)**. Availability does
not depend on `serverVersion`, and there is no "compatibility level" or "API version"
to check — that concept belongs to the separate Azure Cosmos DB for MongoDB (RU)
service, not to Azure DocumentDB (`Microsoft.DocumentDB/mongoClusters`).

The only documented enablement step is for **multishard clusters** (preview): turn on
*Features → Change streams for multishard clusters* in the portal (it cannot be
enabled while *Rebalancer for multishard clusters* is on). No enablement step is
documented for single-shard clusters. `collMod { enableUpdateDescription }` (preview)
and `collMod { changeStreamPreAndPostImages }` change what an event contains; they do
not gate whether you can open a stream. `$changeStreamSplitLargeEvent` and
`showExpandedEvents` are not supported on any version.

## Incorrect

```javascript
// Gating on a version the service does not use for feature availability
const { version } = await db.admin().serverInfo();
if (parseFloat(version) < 6.0) {
  startPollingLoop(); // 🔥 unnecessary fallback; change streams work on 5.0 too
} else {
  collection.watch();
}
```

## Correct

```javascript
// Just open the stream; persist the resume token so you can resume after failover
const stream = collection.watch([], { resumeAfter: await loadResumeToken() });
for await (const change of stream) {
  await handle(change);
  await saveResumeToken(change._id);
}
```

If `watch()` fails with an operation error on a **multishard** cluster, check the
portal feature toggle above — not the server version. After a failover, reopen the
cursor with the saved resume token (cursors must be reinitialized; resumability is kept).

## References

- [Change streams in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/change-streams)
- [MQL compatibility — `$changeStream` supported on all versions](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#operators)
```

**2. `skills/driver/SKILL.md`** — add under `## Rules`:

```markdown
- [driver-change-streams](driver-change-streams.md) — Change streams work on every server version; nothing to enable except the multishard feature toggle. Never gate on `serverVersion`.
```

and extend the front-matter `description` with "change streams (`watch()`), resume tokens".

**3. `docs/SKILLS.md`** — append "change streams / resume tokens" to the `driver/` row.

Note for maintainers: a sibling finding from the same run proposes a change-streams note about the multishard toggle. If that lands first, merge the "not version-gated" paragraph into that file rather than adding a second rule.

## Evidence (run folders; `02-readiness.json` → `confusions[Q12]`)

- `runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json` — outcome `wrong`, confused with Cosmos DB for MongoDB (RU); build_risk tells builder to "always check the cluster's configured MongoDB server version".
- `runs/14-dynamic-pricing-engine/20261124-184622/02-readiness.json` — outcome `partly_wrong`; cold answer says availability "depends on the Cosmos DB account's MongoDB API version"; proposes a Learn footnote about "very old compatibility tiers".
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/02-readiness.json` — outcome `wrong`; proposes an Agent Kit note telling users to check the MQL matrix "for your cluster's configured serverVersion".
- `runs/19-cross-sell-recommendation-beanie/20261125-055705/02-readiness.json` → `confusions[Q10]` — same prior surfaces in the server-version question ("historically some change-stream/transaction semantics were limited").
- Kit clone: `skills/driver/SKILL.md` currently lists a single rule; no skill file mentions change streams.

## Verification

### 1. Already covered? confirmed (not covered)

`grep -rli "change.?stream|watch()"` over the kit's `skills/`, `knowledge-base/` and `docs/` returns nothing. `skills/driver/` holds only `SKILL.md` and `driver-singleton-client.md`; the SKILL.md `## Rules` list has a single entry (driver-singleton-client), and `docs/SKILLS.md` line 24 describes `driver/` as "MongoDB driver/SDK usage (singleton client, pooling)". No skill tells an agent that change streams are not version-gated. microsoft/documentdb-mcp is a separate tool surface and not the place for this guidance. The Learn pages do carry the facts (see check 2), but the agent did not consult them in its cold answer, and the kit is what gets loaded on every build.

### 2. Is the premise true? confirmed

- https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language#operators: the Aggregation Pipeline Stages row for `$changeStream` is "Yes" in the v5.0, v6.0, v7.0 and v8.0 columns; `$changeStreamSplitLargeEvent` is "No" in all four. Nothing gates change streams by version.
- https://learn.microsoft.com/en-us/azure/documentdb/change-streams (updated 2026-11-17): the only enablement procedure is "Multi-shard change streams (preview)", under Settings > Features > "Change streams for multishard clusters", with the note that it cannot be enabled while Rebalancer for multishard clusters is enabled. `updateDescription` (preview, enabled per collection with `collMod enableUpdateDescription`) and pre-images (`collMod changeStreamPreAndPostImages`) are output options. Limitations list includes cursor reinitialization after failover (resume preserved) and no `showExpandedEvents`. No mention of serverVersion or a compatibility level.
- Evidence files exist and contain the confusion: runs/12-invoice-matching-reconciliation/20261124-191603/02-readiness.json ("compatibility level"), runs/14-dynamic-pricing-engine/20261124-184622/02-readiness.json ("API version", "compatibility level"), runs/19-cross-sell-recommendation-beanie/20261125-055705/02-readiness.json ("API version", "serverVersion").

Corrections applied to the body: (a) the draft called Azure Cosmos DB for MongoDB (RU) "retired"; it is a separate, current service, so the text now says "separate"; (b) "single-shard clusters need nothing enabled" was an inference and is now "no enablement step is documented for single-shard clusters"; (c) marked multishard change streams and updateDescription as preview, named the pre-images `collMod` option, and added the version-independent unsupported items (`$changeStreamSplitLargeEvent`, `showExpandedEvents`); (d) "the fix is the toggle, not a version upgrade" softened to "check the toggle, not the server version", and the failover note now follows the Learn limitation (reinitialize the cursor, resume token still valid).

### 3. Maintainer skeptic: confirmed

The PR names concrete files (`skills/driver/driver-change-streams.md` new, `skills/driver/SKILL.md`, `docs/SKILLS.md`), matches the existing rule shape (Category/Priority header, Why it matters, Incorrect with the `// 🔥` marker, Correct, References), and states a DocumentDB-specific fact that the kit lacks. It also tells maintainers to merge with the sibling multishard-toggle change if that lands first, which avoids duplicate rules. I would accept it with the edits above.

## Finding ids

- F2089
- F2364
- F3231
