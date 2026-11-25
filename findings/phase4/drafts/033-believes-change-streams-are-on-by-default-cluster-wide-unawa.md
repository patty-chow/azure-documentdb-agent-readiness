---
title: "Add a \"change streams on multishard clusters\" callout to the sharding skill (preview Features toggle, Rebalancer precondition, collMod opt-ins)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 30
findings: 30
bucket: confusion-Q12
verdicts:
  covered: confirmed
  premise: confirmed
  maintainer: confirmed
---

# Add a "change streams on multishard clusters" callout to the sharding skill

## What happens today

No skill in the kit mentions change streams. `grep -riE 'change ?stream|watch\(|pre-?image|multishard' skills/` returns nothing. The only hits in the repo are test fixtures under `scenarios/ecommerce-advanced/` (`README.md`, `package.json`, `scripts/generate.mjs`, `scripts/validate.mjs`) and a pointer to them in `scenarios/ecommerce/README.md`; none of these are loaded as skill guidance. `skills/sharding/sharding-logical-vs-physical.md` has a rule for cross-shard transactions ("### 4. Transactions across shards work, but plan for them") and `sharding-scaling-out-vs-up.md` discusses the rebalancer, but neither says that cross-shard change streams have a cluster-level precondition.

So an agent that loads the sharding skill to decide on a multishard layout, then writes `collection.watch()`, is never told that change streams across physical shards on a multishard cluster are a preview capability that must be enabled per cluster (**Change streams for multishard clusters**, under cluster > **Settings** > **Features**), and that this feature cannot be enabled while **Rebalancer for multishard clusters** is on.

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), 30 samples in this theme were graded `partly_wrong` or `outdated` on the cold question "Are change streams supported, and does anything have to be enabled first?". Two failure modes appeared:

- Assuming MongoDB Server/Atlas behaviour: cluster-wide `watch()` just works, no toggle, nothing to check (e.g. `09-trade-settlement-tracker`, `16-atm-network-status-monitor`, `03-substitute-product-finder`).
- Carrying the old Azure Cosmos DB for MongoDB (RU) belief that change streams are limited or unavailable, and reaching for polling instead (e.g. `12-hospital-bed-occupancy-tracker`, `12-cross-border-payment-audit-trail`). Across all Q12 confusion records in the experiment, this RU-era prior was the more common of the two.

The build-stage audits of samples that actually open a stream (`09-trade-settlement-tracker`, `16-atm-network-status-monitor`) flag that the generated apps do not persist change-stream resume tokens. At least one readiness report asked for exactly this kit change: "Add a short checklist in the agent kit: if you need multishard change streams, enable the cluster feature and ensure Rebalancer is off" (`03-substitute-product-finder`).

The Learn page already has the enablement steps, the Rebalancer caveat and the `collMod` commands, so this is a kit discoverability gap, not a docs gap.

## Proposed change

### 1. `skills/sharding/sharding-logical-vs-physical.md` — new rule after "### 4. Transactions across shards work, but plan for them"

````markdown
### 5. Change streams across shards need the preview feature

The multishard change-streams feature applies only to **multishard** clusters; a single-shard cluster has no such toggle. On a multishard cluster, change streams that span physical shards are a preview capability, **Change streams for multishard clusters**, enabled per cluster:

- Enable it in the Azure portal: cluster → **Settings** → **Features** → **Change streams for multishard clusters** → **Enable**, then confirm on the Features page that it shows as enabled. The Learn change-streams page documents only this portal path; do not invent an `az` / ARM / Bicep property for it — tell the user to flip the toggle and verify it.
- It **cannot be enabled while "Rebalancer for multishard clusters" is enabled**. Check the Features page and make sure the Rebalancer is off first.
- A topology transition from single-shard to multi-shard **breaks change-stream resumability**, and multi-shard deployments **do not preserve global event ordering**.
- Change stream cursors must be reinitialized after a failover (resume capability is preserved).

Two related opt-ins are **per collection**, off by default, and set with `collMod` (not a cluster feature):

```javascript
// document state before update/delete/replace -> fullDocumentBeforeChange
db.runCommand({ collMod: "orders", changeStreamPreAndPostImages: { enabled: true } });
// field-level diff on update events (preview)
db.runCommand({ collMod: "orders", enableUpdateDescription: { enabled: true } });
```

Pre-images are only produced for `update`, `delete` and `replace` events, are not available when processing historical (archived) change logs, and add write amplification and latency — enable them only where the workload needs them.

Agent checklist before writing `watch()` code against a cluster you did not create:
1. Is the cluster multishard? If yes, is **Change streams for multishard clusters** enabled on its Features page (with the Rebalancer off)?
2. Does the consumer persist the resume token (`change._id`) after each event and pass it to `resumeAfter` on restart?
3. If it needs `fullDocumentBeforeChange` or `updateDescription`, run the `collMod` above on each collection.
````

and add to that file's `## References`:

```markdown
- [Change streams in Azure DocumentDB — Multi-shard change streams (preview)](https://learn.microsoft.com/azure/documentdb/change-streams#multi-shard-change-streams-preview)
- [Change streams — Pre-images](https://learn.microsoft.com/azure/documentdb/change-streams#pre-images-in-change-streams), [updateDescription (preview)](https://learn.microsoft.com/azure/documentdb/change-streams#updatedescription-for-field-level-changes-in-change-streams-preview), [Limitations](https://learn.microsoft.com/azure/documentdb/change-streams#limitations)
```

### 2. `skills/sharding/SKILL.md`

- In the frontmatter `description`, append `, or when an app on a multishard cluster uses change streams (watch())` to the "Use when" clause so the skill is loaded for that case.
- Extend the `sharding-logical-vs-physical` bullet under `## Rules`:

```markdown
- [sharding-logical-vs-physical](sharding-logical-vs-physical.md) — … Cross-shard transactions are supported but not free. **Change streams across physical shards on a multishard cluster require the preview "Change streams for multishard clusters" Features toggle, which cannot be enabled while the multishard Rebalancer is on.**
```

### 3. `skills/azure-deployment/SKILL.md` — one bullet in "## Step 9 — configure access"

```markdown
- **Change streams on a multishard cluster.** If `shardCount > 1` and the application uses `watch()`, enable **Settings → Features → Change streams for multishard clusters** in the portal (preview; cannot be enabled while **Rebalancer for multishard clusters** is on). The Learn page documents only the portal path. See `documentdb-sharding` rule 5.
```

## Out of scope / deliberately not included

- No Learn change: `https://learn.microsoft.com/azure/documentdb/change-streams` already has the toggle steps, the Rebalancer note, the `collMod` commands and the limitations list. Two secondary gaps exist (the page shows no CLI/ARM equivalent of the portal toggle, and no programmatic way to read whether the feature is enabled) but they are product/docs gaps, not something this kit should paper over.
- Several readiness reports asked for "the exact az CLI / ARM / Bicep command to toggle the feature". No such command is documented on the change-streams page, so this PR tells the agent not to invent one.

## Evidence (run folders from the readiness experiment)

- `runs/09-trade-settlement-tracker/20261124-201323/02-readiness.json` (confusions Q12, S05) and `05-audit.json` — audit asks to "persist change-stream resume tokens"
- `runs/16-atm-network-status-monitor/20261124-202405/02-readiness.json` (Q12) and `05-audit.json` — audit lists missing resume-token persistence
- `runs/12-hospital-bed-occupancy-tracker/20261124-194835/02-readiness.json` (Q12 — RU-era prior, polling fallback)
- `runs/03-substitute-product-finder/20261124-183232/02-readiness.json` (Q12 — proposes this kit checklist)
- `runs/15-digital-onboarding-orchestration/20261124-202211/02-readiness.json` (Q12 — proposes a monitoring/sharding callout)

Full list of affected samples (30): 02-clinical-trial-matching-orchestration, 03-substitute-product-finder, 04-customer-journey-mapper, 04-natural-language-product-search, 05-appointment-scheduling-assistant, 08-regulatory-compliance-rag-checker, 09-trade-settlement-tracker, 10-drug-formulary-semantic-search, 11-care-gap-identification-pipeline, 11-correspondent-banking-risk-screener, 11-preference-center-consent-store, 12-cross-border-payment-audit-trail, 12-hospital-bed-occupancy-tracker, 13-household-grouping-linkage, 13-product-q-a-chatbot-rag, 14-customer-complaint-classifier, 14-hyper-personalized-content-engine, 14-telehealth-session-summarizer, 15-digital-onboarding-orchestration, 16-atm-network-status-monitor, 17-esg-scoring-pipeline, 17-rare-disease-literature-search, 18-chargeback-dispute-multi-agent, 19-care-coordination-multi-agent, 19-insider-threat-detection-pipeline, 19-proactive-outreach-orchestration, 20-identity-resolution-multi-agent, 20-interest-accrual-batch-processor, 20-provider-directory-semantic-search, 20-store-locator-with-geospatial-search.

## Verification

### 1. Already covered? — confirmed (not covered)

- `grep -rliE 'change ?stream|watch\(|pre-?image|multishard'` over the Agent Kit clone returns no file under `skills/` or `knowledge-base/`; hits are only `scenarios/ecommerce-advanced/{README.md,package.json,scripts/generate.mjs,scripts/validate.mjs}` (fixture generator: "Deterministic ecommerce fixtures for transactions, change streams, and advanced MQL compatibility tests") and a pointer in `scenarios/ecommerce/README.md`. None of these is skill guidance.
- `skills/sharding/sharding-logical-vs-physical.md` headings end at "### 4. Transactions across shards work, but plan for them" then "## References"; `skills/sharding/SKILL.md` line 21 rule bullet ends "Cross-shard transactions are supported but not free." No change-stream content. `skills/azure-deployment/SKILL.md` "## Step 9 — configure access" (line 293) covers network posture only; `shardCount` appears in its Bicep at line 233.
- microsoft/documentdb-mcp clone: no change-stream hits (not the target anyway).
- Learn does cover it (https://learn.microsoft.com/en-us/azure/documentdb/change-streams, updated 2026-11-17), which is why the draft proposes no Learn change.

### 2. Is the premise true? — confirmed (wording corrections applied)

Checked against https://learn.microsoft.com/en-us/azure/documentdb/change-streams:
- Multishard: "Multi-shard change streams (preview)"; enable via cluster > Settings > Features > "Change streams for multishard clusters" > Enable, then verify. Rebalancer: the page states the feature cannot be enabled while Rebalancer for multishard clusters is enabled. Confirmed.
- Limitations section: single-shard to multi-shard transition breaks resumability; multi-shard does not preserve global ordering; cursors must be reinitialized after failover; pre-image not supported for historical processing of logs; updateDescription not supported for updates within aggregation pipelines. Confirmed.
- `collMod` with `changeStreamPreAndPostImages: { enabled: true }` and `enableUpdateDescription: { enabled: true }`; updateDescription section is marked preview; pre-images off by default, only for update/delete/replace. Confirmed.
- Only a portal path is shown on the page; no CLI/ARM/Bicep. Confirmed.
Corrections applied to the body: (a) "pre-images are not available when replaying with `startAtOperationTime`" narrowed to "not available when processing historical (archived) change logs", matching Learn (`startAtOperationTime` within the active log is not excluded); (b) "stored resume tokens become invalid" replaced with Learn's wording "breaks change-stream resumability"; (c) "the watch will not deliver cross-shard events" softened, since Learn does not document behaviour without the toggle; (d) "single-shard clusters need nothing" restated as "the toggle applies only to multishard clusters" (Learn does not state the single-shard case explicitly); (e) added the failover-reinitialization limitation; (f) the unverifiable "20 Atlas / 10 RU" split was removed (across all Q12 confusion records in `findings/findings.jsonl`, the RU-era prior is the more common); (g) the audit quote "does not persist resume tokens nor document the multishard caveat" was not found verbatim; the audits only flag missing resume-token persistence, so the body now says that; (h) the "only hit is the fixtures README" claim was corrected to list all scenario hits. The "checklist in the agent kit" quote was verified in `runs/03-substitute-product-finder/20261124-183232/02-readiness.json`.

### 3. Maintainer skeptic — confirmed

As maintainer of Azure/documentdb-agent-kit I would accept this: it names three exact files and headings, adds Azure DocumentDB-specific content (a preview Features toggle, the Rebalancer conflict, DocumentDB `collMod` options) that a Mongo-trained model will not know, links to the authoritative Learn anchors, and explicitly avoids inventing an undocumented CLI property. It is not generic hygiene and belongs in this repo (sharding/deployment skills), not Learn or the MCP server.

## Finding ids

F0220, F0501, F0531, F0634, F0701, F1343, F1562, F1594, F1759, F1795, F1866, F2023, F2058, F2222, F2249, F2331, F2394, F2465, F2523, F2654, F2847, F2881, F3047, F3150, F3263, F3328, F3365, F3398, F3464, F3504
