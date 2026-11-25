---
title: "Add copyable retry/backoff and bulk-write partial-failure helpers (Python + Node) to the connection skill"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 14
findings: 14
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add copyable retry/backoff and bulk-write partial-failure helpers (Python + Node) to the connection skill

## What happens today

`skills/connection/SKILL.md` has a `## Retry Logic` section (lines 209-240) whose only code is a Node `withRetry(fn, maxRetries)` that:

- retries only when `err.code === 16500 || err.code === 429`, so `MongoNetworkError`, `MongoServerSelectionError` and failover errors are rethrown on the first attempt;
- uses pure doubling with no jitter and never reads `Retry-After` / `retry-after-ms`;
- has no timeout, no Python equivalent, and nothing for `bulkWrite` partial failures.

`skills/driver/SKILL.md` (13 lines) defers to the connection skill for retries. No other skill, example or script in the repo ships a retry or bulk-error helper. The kit's own `documentdb-azure-deployment` skill (`skills/azure-deployment/SKILL.md` lines 288-291) correctly requires `retrywrites=false` and states that Azure DocumentDB does not support retryable writes, which means the driver does **not** auto-retry writes, so an application-level helper matters more here than on stock MongoDB.

The kit contradicts itself on this point, which this PR should fix at the same time: `skills/connection/SKILL.md` line 60 shows a connection string ending in `retryWrites=true`, `skills/driver/driver-singleton-client.md` line 26 constructs `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })`, and `skills/security/security-tls-required.md` line 26 sets `retryWrites: true`. All three should use `retrywrites=false` (with `maxIdleTimeMS=120000`) to match the azure-deployment skill.

## Why it matters

In a 100-sample readiness run (gpt-5-mini + this kit + DocumentDB/Azure/Learn MCP servers), audits of **14 distinct samples** (roughly half Python, half Node) flagged the same gap. Concretely, the agent:

- called `collection.aggregate(...)` and `update_one` with no retry wrapper and no `maxTimeMS` (17-stress-testing-multi-agent-runner, 08-dynamic-segmentation-engine, 18-sanctions-list-screening-agent);
- did unordered `bulkWrite` and only logged `MongoBulkWriteError`, never separating duplicate-key (11000) from retryable write errors or re-sending the retryable subset (02-real-time-event-stream-ingestion);
- made Azure OpenAI embedding/chat calls with no timeout, no 429/Retry-After handling and no circuit breaker, so one slow LLM call could block the whole orchestration (18-returns-refund-workflow-orchestration, 20-provider-directory-semantic-search, 18-chargeback-dispute-multi-agent);
- relied on prior knowledge for OpenAI concurrency limits and DB batch sizes because searches returned nothing (07-customer-review-sentiment-pipeline);
- had `requests.get(timeout=10)` plus a mock fallback in one sample, but only because the model improvised, not because the kit asked for it (17-seasonal-trend-spotter-agent).

Several audits also searched for the pattern in the connection and driver skills, found the prose, and still had no snippet short enough to copy. Builders copying these samples into production inherit unbounded or absent retries.

One caveat for maintainers: most audits phrased the DB gap as "honor 429 / x-ms-retry-after-ms", sourcing the Cosmos DB RU throughput page. On vCore DocumentDB there is no RU-style 429 throttling; the DB-side risk is transient network / server-selection / failover errors (plus connection limits). 429 + Retry-After is real for the Azure OpenAI calls every one of these samples also makes. The helper below handles both and the skill text should say so explicitly, so agents stop importing the RU mental model.

## Proposed change

### 1. New sidecar `skills/connection/connection-retry-helpers.md`

Follows the existing per-skill reference-file pattern (`driver/driver-singleton-client.md`, `vector-search/vector-*.md`). Contents:

**`retry_util.py`** (stdlib only; note that `tenacity` is an acceptable drop-in if already a dependency):

```python
import random, time
from pymongo.errors import (AutoReconnect, NetworkTimeout,
                            ServerSelectionTimeoutError, OperationFailure, BulkWriteError)

TRANSIENT_DB = (AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError)
LEGACY_THROTTLE_CODES = {16500, 429}          # harmless on vCore, kept for RU-API portability
RETRYABLE_HTTP = {408, 429, 500, 502, 503, 504}

def retry_after_seconds(err):
    headers = getattr(getattr(err, "response", None), "headers", None) or {}
    for h in ("retry-after-ms", "x-ms-retry-after-ms"):
        if h in headers:
            return int(headers[h]) / 1000
    if "retry-after" in headers:
        return float(headers["retry-after"])
    return None

def is_retryable(err):
    if isinstance(err, TRANSIENT_DB):
        return True
    if isinstance(err, OperationFailure) and err.code in LEGACY_THROTTLE_CODES:
        return True
    return getattr(err, "status_code", None) in RETRYABLE_HTTP

def with_retry(fn, *, attempts=4, base=0.5, cap=20.0):
    """Wrap ONLY idempotent work: reads, aggregate, upsert / $setOnInsert,
    embedding calls. Never wrap a blind insert_one/insert_many."""
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if i == attempts - 1 or not is_retryable(e):
                raise
            delay = retry_after_seconds(e) or min(cap, base * 2 ** i) * random.uniform(0.5, 1.5)
            time.sleep(delay)

def partition_bulk_errors(exc: BulkWriteError, ops):
    """Split writeErrors into duplicate-key (do not retry; count them) and retryable ops."""
    dup, retry = [], []
    for we in exc.details.get("writeErrors", []):
        (dup if we["code"] == 11000 else retry).append(ops[we["index"]])
    return dup, retry
```

**`retry.js`** (fixes the existing snippet rather than adding a second one):

```javascript
const { MongoNetworkError, MongoServerSelectionError } = require('mongodb');
const LEGACY_THROTTLE = new Set([16500, 429]);
const RETRYABLE_HTTP = new Set([408, 429, 500, 502, 503, 504]);

function retryAfterMs(err) {
  const h = err?.response?.headers ?? err?.headers ?? {};
  const get = k => (typeof h.get === 'function' ? h.get(k) : h[k]);
  const ms = get('retry-after-ms') ?? get('x-ms-retry-after-ms');
  if (ms) return Number(ms);
  const s = get('retry-after');
  return s ? Number(s) * 1000 : null;
}
function isRetryable(err) {
  return err instanceof MongoNetworkError || err instanceof MongoServerSelectionError
    || LEGACY_THROTTLE.has(err?.code) || RETRYABLE_HTTP.has(err?.status ?? err?.statusCode);
}
// Wrap ONLY idempotent work (find/aggregate/upsert/embeddings), never blind inserts.
async function withRetry(fn, { attempts = 4, baseMs = 500, capMs = 20000 } = {}) {
  for (let i = 0; ; i++) {
    try { return await fn(); }
    catch (err) {
      if (i >= attempts - 1 || !isRetryable(err)) throw err;
      const delay = retryAfterMs(err) ?? Math.min(capMs, baseMs * 2 ** i) * (0.5 + Math.random());
      await new Promise(r => setTimeout(r, delay));
    }
  }
}
function partitionBulkErrors(err /* MongoBulkWriteError */, ops) {
  const dup = [], retry = [];
  for (const we of err.writeErrors ?? []) (we.code === 11000 ? dup : retry).push(ops[we.index]);
  return { dup, retry };
}
module.exports = { withRetry, partitionBulkErrors, isRetryable, retryAfterMs };
```

**Rules paragraph** (sample-scale defaults, each one line):

- Bound every call: `maxTimeMS` on `find`/`aggregate` (the service default query limit is 120 seconds, too long for an interactive path), `timeoutMS` on the client (Node driver 6.x / PyMongo 4.x), `timeout=30` on OpenAI clients, 5-10 s on web-search tools.
- Cap LLM/embedding concurrency: `asyncio.Semaphore(4)` or `p-limit(4)`; raise only after measuring 429 rate.
- `bulkWrite` in batches of 500-1000 with `ordered: false` (the service hard limit is 25,000 writes per batch; larger batches fail); on `BulkWriteError`, call `partition_bulk_errors`, count duplicates as a metric, retry only the retryable subset through `with_retry`. The partition helper is only complete for `ordered: false`: with `ordered: true` the server stops at the first error and the unattempted ops after it do not appear in `writeErrors`.
- External tools (web search, LLM) must have a deterministic mock fallback after `attempts` failures so demos stay responsive; never fall back silently on DB writes.
- Idempotency: retry reads, aggregates, upserts and `$setOnInsert`; make merge/seed paths upserts keyed on a natural id before wrapping them.

**Usage examples**: one seed path (`bulk_write` + partition + retry) and one query path (`aggregate` with `maxTimeMS` inside `with_retry`) per language, ~10 lines each.

**Test**: `testing/test_retry_util.py` (or wherever the harness places unit tests) with a fake that raises an exception carrying `status_code=429` and `headers={'retry-after-ms': '50'}` twice then succeeds; assert 3 calls, assert sleep used the header value, assert a duplicate-key `BulkWriteError` is partitioned and not retried.

### 2. `skills/connection/SKILL.md`, section `## Retry Logic` (and line 60)

Replace the current `withRetry` block with the fixed `retry.js` version above plus the Python `with_retry`, and add two sentences: "Azure DocumentDB (vCore) does not return RU-style 429 throttling; retry DB calls on transient network, server-selection and failover errors. 429 with Retry-After comes from Azure OpenAI / embedding endpoints; honor the header there." End with "See `connection-retry-helpers.md` for bulk-write partitioning, timeouts and concurrency defaults." Also change the line 60 connection string from `retryWrites=true` to `retrywrites=false&maxIdleTimeMS=120000`, and add one sentence: "Retryable writes are not supported, so the driver will not retry writes for you; wrap idempotent writes with `withRetry`."

### 3. `skills/driver/SKILL.md`, `skills/driver/driver-singleton-client.md`, `skills/security/security-tls-required.md`

In `skills/driver/SKILL.md` add one bullet: "Application-level retry, bulk-write error partitioning and LLM concurrency limits: see `documentdb-connection` -> `connection-retry-helpers.md`." In `driver-singleton-client.md` line 26 and `security-tls-required.md` line 26 replace `retryWrites: true` with `retryWrites: false`.

## Evidence (run folders from the readiness experiment)

- `runs/02-real-time-event-stream-ingestion/20261124-203233/doc-gaps.md` - bulkWrite errors only logged, writeErrors never partitioned
- `runs/20-provider-directory-semantic-search/20261124-200008/05-audit.json` - checks P05/P17 "violated": no retry around db.py or createIndexes/embedding calls
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/05-audit.json` - "Retry semantics: violated", aggregate() with no wrapper
- `runs/07-customer-review-sentiment-pipeline/20261124-183656/doc-gaps.md` - concurrency/batch sizes from prior knowledge, searches returned nothing
- `runs/18-returns-refund-workflow-orchestration/20261124-185415/doc-gaps.md` - callOpenAI with no timeout or circuit breaker

Other samples hitting the same gap: 01-unified-customer-profile-store, 03-medication-interaction-checker, 03-next-best-action-multi-agent, 07-mortgage-application-multi-agent, 08-dynamic-segmentation-engine, 17-seasonal-trend-spotter-agent, 18-chargeback-dispute-multi-agent, 18-sanctions-list-screening-agent, 20-identity-resolution-multi-agent.

## Verification

### 1. Already covered? partially_covered

The kit has some retry content, but nothing copyable for the cases the samples hit:
- `skills/connection/SKILL.md` lines 209-240, `## Retry Logic`: enables `retryReads: true` and gives one Node `withRetry` that retries only `if (err.code === 16500 || err.code === 429)` with `Math.min(1000 * Math.pow(2, i), 30000)` and no jitter, no Retry-After, no network-error classes, no Python, no bulk-write handling. The draft's description of it is accurate.
- `skills/driver/SKILL.md` (13 lines) only points to the connection skill for retries.
- `skills/storage/storage-disk-hydration-sequencing.md` line 96 and `skills/local-deployment/local-docker-compose-setup.md` line 14 recommend backoff/retry in prose only.
- `knowledge-base/kb.json`: no retry, backoff, throttling or 429 content. microsoft/documentdb-mcp clone: no retry/backoff content (not the target anyway).
- No `writeErrors`/11000 partitioning, `Semaphore`/`p-limit`, or `maxTimeMS`/`timeoutMS` guidance anywhere under `skills/`.

### 2. Premise true? confirmed (with additions applied)

- Azure DocumentDB (vCore) capacity is vCore tiers, not request units, so there is no RU-style 429 throttling on DB calls; the draft already says this, which is correct. 429 + Retry-After / retry-after-ms is real for Azure OpenAI endpoints.
- Retryable writes are not supported: true-facts connection string uses `retrywrites=false`; `skills/azure-deployment/SKILL.md` line 291 says "Azure DocumentDB does not support retryable writes". Added correction: the kit itself contradicts this in `skills/connection/SKILL.md` line 60, `skills/driver/driver-singleton-client.md` line 26 and `skills/security/security-tls-required.md` line 26 (all `retryWrites=true`); the PR now fixes those.
- https://learn.microsoft.com/en-us/azure/documentdb/limitations: "Default query execution limit: 120 seconds. This limit can be overridden on a per-query basis using `maxTimeMS`" and "Maximum writes per batch operation: 25,000 writes"; both added to the rules paragraph. The 500-1000 batch default is well inside that limit.
- PyMongo `AutoReconnect`, `NetworkTimeout`, `ServerSelectionTimeoutError`, `OperationFailure`, `BulkWriteError` (with `details['writeErrors'][i]['index'/'code']`) and Node `MongoNetworkError`, `MongoServerSelectionError`, `MongoBulkWriteError.writeErrors` exist as used. Duplicate-key code 11000 is correct. Added caveat that partitioning only covers `ordered: false` batches.

### 3. Maintainer skeptic: confirmed

Names exact files and line ranges (`skills/connection/SKILL.md` 60 and 209-240, new `skills/connection/connection-retry-helpers.md` following the `driver-singleton-client.md` sidecar pattern, `skills/driver/SKILL.md`), supplies working code, and has a DocumentDB-specific angle (no retryable writes, no RU throttling, 25,000-write batch limit, 120 s default query limit) plus a real defect fix (contradictory `retryWrites=true`). Belongs in Azure/documentdb-agent-kit. Small scope concern: the LLM concurrency and web-search mock-fallback rules are generic; a maintainer may ask to keep them to one line each, as drafted.

Citations: skills/connection/SKILL.md, skills/driver/SKILL.md, skills/driver/driver-singleton-client.md, skills/security/security-tls-required.md, skills/azure-deployment/SKILL.md (in the documentdb-agent-kit clone); https://learn.microsoft.com/en-us/azure/documentdb/limitations; https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features.

## Finding ids

- F0165
- F0403
- F0441
- F1120
- F1215
- F0274
- F1024
- F2962
- F3056
- F3132
- F3380
- F3479
- F3092
- F2925
