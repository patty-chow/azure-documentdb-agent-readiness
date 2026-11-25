---
title: "connection skill: replace RU-era 429/16500 retry snippet with vCore-correct transient-error retry, and fix retryWrites=true in examples"
repo: Azure/documentdb-agent-kit
type: issue
status: ready_with_edits
priority: P1
sample_count: 1
findings: 1
bucket: mcp-server
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# connection skill: replace RU-era 429/16500 retry snippet with a vCore-correct transient-error retry; fix `retryWrites=true` examples

## What happens today

`skills/connection/SKILL.md` → **Retry Logic** has a `withRetry` helper that retries only when `err.code === 16500 || err.code === 429`. Those are the request-unit throttling codes from Azure Cosmos DB for MongoDB (RU). Azure DocumentDB (vCore) sizes capacity by M-tier and has no request-unit throttling, so neither code is a documented DocumentDB error. The helper therefore re-throws, without retrying, the transient errors a vCore cluster can actually produce:
- network resets
- server selection timeouts
- primary stepdown or failover (HA and cross-region failover)
- idle-connection drops

The driver's built-in `retryReads` covers a single retry of reads only; writes get no retry from the driver because retryable writes are turned off (see below).

The same skill's connection-string example also sets `retryWrites=true`, and so do `skills/security/security-tls-required.md` (`retryWrites: true`) and `skills/driver/driver-singleton-client.md` (`{ maxPoolSize: 50, retryWrites: true }`). That contradicts `skills/azure-deployment/SKILL.md`, which says "Azure DocumentDB does not support retryable writes; leaving it at the driver default will cause connection errors" and uses `retrywrites=false&maxIdleTimeMS=120000` in its connection string.

## Why it matters

In the 100-sample agent-readiness run (gpt-5-mini plus this kit), the audit for `02-ai-powered-product-recommendations` flagged "no retry/backoff" as a high-priority gap. The agent read the connection and query-optimizer skills, found nothing it could use on vCore, and shipped a seed script that runs `insertMany(batch, {ordered:false}).catch(e => console.warn(...))`. Any failed batch is logged and dropped, so ingestion can end up partial without anyone noticing. The agent also framed the problem as "429 / Retry-After". That framing matches the kit's own 16500/429 snippet, and the only "Throttling" source the audit cites is an unrelated Azure App Configuration REST API throttling page, which shows the agent had no DocumentDB-specific guidance to go on. Only 1 of the 100 samples hit this, but the snippet is the only retry guidance in the kit and it is wrong for this service.

## Proposed change

1. `skills/connection/SKILL.md`, **Connection String Format**: use `mongodb+srv://<username>:<password>@<cluster-name>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`, matching `azure-deployment/SKILL.md`.
2. `skills/connection/SKILL.md`, **Retry Logic**: replace the snippet with:
   - one sentence: Azure DocumentDB has no RU throttling; capacity is the M-tier, so sustained overload is fixed by scaling the tier (or adding shards), not by backing off on 429;
   - `withRetry(fn, {retries: 5, baseMs: 200, capMs: 10000})`, which retries only on `MongoNetworkError`, `MongoServerSelectionError`, errors labelled `TransientTransactionError`, and `NotWritablePrimary` / `PrimarySteppedDown` (codes 10107 / 189), using exponential backoff with full jitter and re-throwing everything else;
   - a note that, because retryable writes are off, retried writes must be idempotent. Show `bulkWrite` with `updateOne({filter:{productId}, update:{$set:doc}, upsert:true})` and a unique index on the key, keep batches under the 25,000-writes-per-batch limit, and say not to swallow batch errors (collect `BulkWriteError` results and retry or fail the run).
3. Add one line: `429` + `Retry-After` comes from Azure OpenAI or other embedding/LLM HTTP calls, not from DocumentDB. Use the SDK's built-in `maxRetries` (OpenAI JS/Python), or honour `Retry-After` in your own wrapper.
4. Change `retryWrites: true` to `retryWrites: false` in `skills/security/security-tls-required.md` and `skills/driver/driver-singleton-client.md`.

## Evidence

- `runs/02-ai-powered-product-recommendations/20261124-181835/doc-gaps.md` (section "[high] Retry-and-throttle helpers")
- `runs/02-ai-powered-product-recommendations/20261124-181835/05-audit.json` (summary: "retries honoring Retry-After ... "; requirement result citing a "Throttling" source that is the Azure App Configuration REST API throttling page)
- `runs/02-ai-powered-product-recommendations/20261124-181835/app/src/seed.js` (lines 143 and 165: insertMany errors swallowed with `.catch(console.warn)`)
- `runs/02-ai-powered-product-recommendations/20261124-181835/02-readiness.json` (cold quiz mixes RU-account `.mongo.cosmos.azure.com:10255` and vCore `mongocluster.cosmos.azure.com` connection-string forms)

## Verification

### 1. Already covered? partially_covered
- The kit has a retry helper, so the audit's "no packaged helper" claim is only half true: `skills/connection/SKILL.md` lines 222-238 define `async function withRetry(fn, maxRetries = 3)` with `if (err.code === 16500 || err.code === 429) { // Rate limited — wait and retry`. It exists but targets the wrong error codes for vCore, and there is no idempotent bulk-load pattern and no note on Azure OpenAI 429s.
- `skills/azure-deployment/SKILL.md` lines 288-291 already give the correct `retrywrites=false&maxIdleTimeMS=120000` string and say retryable writes aren't supported. But `skills/connection/SKILL.md:60`, `skills/security/security-tls-required.md:26` and `skills/driver/driver-singleton-client.md:26` contradict it with `retryWrites=true`.
- No other retry, Retry-After or MongoNetworkError guidance exists anywhere in `skills/` or `knowledge-base/` (grep for retrywrites|16500|429|retry-after|withRetry|MongoNetworkError|TransientTransaction).
- Learn: https://learn.microsoft.com/en-us/azure/documentdb/limitations has no throttling or retry guidance, though it does document the 25,000-writes-per-batch limit and failover modes. https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features does not mention retryable writes.

### 2. Premise true? confirmed (wording tightened)
- vCore capacity is set by M-series tiers (limitations page: "Maximum: M200 / 64 vCores / 256-GiB RAM per physical shard"), with no request units. 16500 / 429 are RU-era Cosmos DB for MongoDB throttling codes and are not documented for Azure DocumentDB. Confirmed.
- The documented vCore connection string uses `tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` (the kit's azure-deployment skill and the reference facts for this review). The kit's `retryWrites=true` examples are therefore wrong. Confirmed.
- seed.js lines 143 and 165 swallow insertMany errors via `.catch(e => console.warn(...))`. Confirmed.
- Edits applied: the "never fires" claim now says the codes are not documented DocumentDB errors, rather than asserting what the server can never emit. The claim that the 429 prior "comes from the kit's own snippet" is softened to "matches", and the audit's mis-sourced App Configuration throttling page is added as evidence. The note that driver `retryReads` covers reads only is added. Concrete stepdown error codes and the 25,000-writes batch limit are added. The generated app sets no retryWrites option, so the wrong `retryWrites=true` example did not reach this sample's code.

### 3. Maintainer skeptic: confirmed
It names exact files and line-level changes, fixes an internal contradiction in the kit (`retryWrites=true` versus azure-deployment's `retrywrites=false`), and replaces an RU-era snippet with one specific to Azure DocumentDB. That is squarely in scope for Azure/documentdb-agent-kit, not documentdb-mcp. The theme bucket says "mcp-server", but the fix target is the kit, so the repo stays Azure/documentdb-agent-kit. I would accept it with the small edits above.

## Finding ids

- F0198
