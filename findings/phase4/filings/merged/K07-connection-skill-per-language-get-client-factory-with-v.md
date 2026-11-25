---
id: K07
title: "connection skill: per-language get_client() factory with vCore-correct transient-error retry and bulk-write partial-failure helpers"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 85
member_drafts:
  - 096-connection-skill-lacks-a-canonical-client-factory-and-transi.md
  - 089-connection-defaults-for-samples-copy-paste-mongoclient-motor.md
  - 090-reusable-retry-backoff-and-resilience-helpers-429-retry-afte.md
  - 119-agent-kit-lacks-a-packaged-retry-backoff-helper-for-429-and-.md
open_questions: 6
---

# connection skill: per-language `get_client()` factory with vCore-correct transient-error retry and bulk-write partial-failure helpers

## What happens today

`skills/connection/SKILL.md` explains *why* pools, timeouts and retries matter, but gives an agent almost nothing to paste:

- **No production client constructor with full options.** The skill's only code is Node: an Azure Functions example with pool options only (around line 107) and the singleton example (line 159), `new MongoClient(process.env.DOCUMENTDB_URI)` with no options. Python gets a prose note about `AsyncMongoClient`. The only PyMongo code in the kit is in `skills/local-deployment/` (`local-env-driven-config.md`, `local-connection-config.md`) and targets the local container. There is no PyMongo async/Beanie or Mongoose snippet anywhere in the kit, and no shutdown hook.
- **No defaults for unattended builds.** The tuning tables give ranges, and "Configuration Design" (line 80) and "When Creating Code" (around line 263) tell the agent to ask the user questions first. A sample builder has no user to ask, so it ships driver defaults.
- **The retry snippet targets the wrong service.** "Retry Logic" (lines 209-241) defines `withRetry` that retries only on `err.code === 16500 || err.code === 429`, the request-unit throttling codes of Azure Cosmos DB for MongoDB (RU). Azure DocumentDB is sized in vCore tiers with no request units. The snippet re-throws, on the first attempt, the errors a driver does surface: network resets, server-selection timeouts, primary stepdown/failover, `TransientTransactionError` / `UnknownTransactionCommitResult` labels, `WriteConflict` (112). It has no jitter, no Python version, and nothing for `bulkWrite` partial failures.
- **Motor guidance is stale and incomplete.** The note (lines 45-49) dates Motor's deprecation to "May 2024" and critical fixes to "through May 2026"; MongoDB's Motor page gives deprecation May 14, 2025, end of life May 14, 2026, critical fixes until May 14, 2027. It does not say which Beanie major works with `AsyncMongoClient`.
- `skills/driver/SKILL.md` defers retries to the connection skill, so no skill ships a usable helper.

The `retryWrites=true` examples (connection/SKILL.md:60, driver-singleton-client.md:26, security-tls-required.md:26) and the host-suffix fixes are handled in a separate PR (K01); this PR does not touch those lines.

## Why it matters

In a 100-sample experiment (gpt-5-mini building sample apps with this kit plus the DocumentDB, Azure and Learn MCP servers; 221 run folders), **85 of the 100 samples** had at least one audit finding in this cluster. The four source drafts counted 85, 12, 14 and 1 samples; the 12, 14 and 1 are all inside the 85, so the union over the drafts' finding ids is 85. All counts come from a single experiment with known harness artifacts and may shift on a re-run [needs SME confirmation]. What the agent did:

- 53 runs (of the 221 run folders) constructed `MongoClient(uri)` / `AsyncIOMotorClient(uri)` with no options, one under a docstring claiming "driver best-practices". 38 never set any pool size or timeout.
- 0 runs registered a `SIGINT`/`SIGTERM` close; 0 shipped a DB backoff helper.
- 18 runs chose Motor; one pinned `beanie==1.13.0 motor==3.1.2 pydantic==1.10.12` and created a new client per `init_db()` call, after logging that the kit did not say which Beanie release supports `AsyncMongoClient`.
- Unordered `insertMany`/`bulkWrite` errors were logged and dropped (`.catch(console.warn)`), so seeding could end partial without notice; duplicate-key errors were never separated from retryable ones.
- 2 runs hit PyMongo's `Duplicate URI option 'retryWrites'` by string-appending options onto the env URI.
- The RU failure model leaked downstream: 64 of 150 retry-related audit checks demanded "honor 429 / Retry-After", citing Cosmos DB RU throughput pages (and once an App Configuration throttling page); whether vCore can ever return these codes is open question 1 [needs SME confirmation]. Azure OpenAI calls, which do return 429 + `Retry-After`, had no timeout or backoff.

## Proposed change

### 1. New `skills/connection/connection-client-factory.md`

Same layout as `driver-singleton-client.md`. Rules stated once: one client per process (in serverless, create it at module scope so warm invocations reuse it); read `DOCUMENTDB_URI`, fail fast if it is missing or lacks `tls=true`; pass options to the constructor and never string-append to the URI (if a user-supplied URI must be normalized, parse it, as below); set `retryWrites=False` to match the portal-issued connection string; pool and timeouts from env with two documented defaults; close on shutdown. When no user is available to answer questions (samples, quickstarts, CLIs), use these defaults and comment them. (Draft 096 also proposed rejecting URIs that do not start with `mongodb+srv://`; that check is left out because the local-deployment skill connects with `mongodb://localhost:10260`.)

| Option | Long-running | Serverless | Env var |
|---|---|---|---|
| `maxPoolSize` | 50 | 5 | `DOCUMENTDB_MAX_POOL_SIZE` |
| `minPoolSize` | 5 | 0 | `DOCUMENTDB_MIN_POOL_SIZE` |
| `maxIdleTimeMS` | 120000 | 30000 | `DOCUMENTDB_MAX_IDLE_TIME_MS` |
| `serverSelectionTimeoutMS` | 5000 | 5000 | `DOCUMENTDB_SERVER_SELECTION_TIMEOUT_MS` |
| `connectTimeoutMS` | 10000 | 10000 | `DOCUMENTDB_CONNECT_TIMEOUT_MS` |
| `socketTimeoutMS` | 30000 | 30000 | `DOCUMENTDB_SOCKET_TIMEOUT_MS` |

```python
# db.py  (PyMongo sync and async share _opts)
import os, signal, sys
from pymongo import MongoClient, AsyncMongoClient

def _opts() -> dict:
    sl = os.getenv("DOCUMENTDB_SERVERLESS", "false").lower() == "true"
    e = lambda k, d: int(os.getenv(k, d))
    return dict(tls=True, retryWrites=False,   # matches the portal-issued connection string
        maxPoolSize=e("DOCUMENTDB_MAX_POOL_SIZE", 5 if sl else 50),
        minPoolSize=e("DOCUMENTDB_MIN_POOL_SIZE", 0 if sl else 5),
        maxIdleTimeMS=e("DOCUMENTDB_MAX_IDLE_TIME_MS", 30000 if sl else 120000),
        serverSelectionTimeoutMS=e("DOCUMENTDB_SERVER_SELECTION_TIMEOUT_MS", 5000),
        connectTimeoutMS=e("DOCUMENTDB_CONNECT_TIMEOUT_MS", 10000),
        socketTimeoutMS=e("DOCUMENTDB_SOCKET_TIMEOUT_MS", 30000),
        appname=os.getenv("APP_NAME", "sample"))

def _uri() -> str:
    uri = os.environ["DOCUMENTDB_URI"]
    if "tls=true" not in uri.lower():
        raise RuntimeError("DOCUMENTDB_URI must include tls=true")
    return uri

_client = None
def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(_uri(), **_opts())
    return _client

def close_client(*_):
    global _client
    if _client is not None:
        _client.close(); _client = None

def install_shutdown_handlers() -> None:
    # Call from the CLI/worker entry point, not at import. Under uvicorn/gunicorn
    # use the framework lifespan hook so the server's SIGTERM handling is kept.
    for s in (signal.SIGINT, signal.SIGTERM):
        signal.signal(s, lambda *_: (close_client(), sys.exit(0)))

# Async: PyMongo >= 4.9 AsyncMongoClient; Beanie >= 2.0 accepts it directly (version floors: open question 5).
# Do not add motor (deprecated May 14, 2025; end of life May 14, 2026).
_aclient = None
def get_async_client() -> AsyncMongoClient:
    global _aclient
    if _aclient is None:
        _aclient = AsyncMongoClient(_uri(), **_opts())
    return _aclient

async def init_db(models):
    from beanie import init_beanie
    await init_beanie(database=get_async_client()[os.getenv("DOCUMENTDB_DATABASE", "app")],
                      document_models=models)

async def close_async_client():   # FastAPI lifespan / asyncio shutdown
    global _aclient
    if _aclient is not None:
        await _aclient.close(); _aclient = None
```

```javascript
// db.js  (mongodb driver; Mongoose forwards the same options)
const { MongoClient } = require("mongodb");
const sl = process.env.DOCUMENTDB_SERVERLESS === "true";
const n = (k, d) => Number(process.env[k] ?? d);
function clientOptions() {
  return { tls: true, retryWrites: false,   // matches the portal-issued connection string
    maxPoolSize: n("DOCUMENTDB_MAX_POOL_SIZE", sl ? 5 : 50),
    minPoolSize: n("DOCUMENTDB_MIN_POOL_SIZE", sl ? 0 : 5),
    maxIdleTimeMS: n("DOCUMENTDB_MAX_IDLE_TIME_MS", sl ? 30000 : 120000),
    serverSelectionTimeoutMS: n("DOCUMENTDB_SERVER_SELECTION_TIMEOUT_MS", 5000),
    connectTimeoutMS: n("DOCUMENTDB_CONNECT_TIMEOUT_MS", 10000),
    socketTimeoutMS: n("DOCUMENTDB_SOCKET_TIMEOUT_MS", 30000),
    appName: process.env.APP_NAME ?? "sample" };
}
function uri() {
  const u = process.env.DOCUMENTDB_URI;
  if (!u || !/tls=true/i.test(u)) throw new Error("DOCUMENTDB_URI must be set and include tls=true");
  return u;
}
let client;
function getClient() { return (client ??= new MongoClient(uri(), clientOptions())); }
async function closeClient() { if (client) { await client.close(); client = undefined; } }

// Mongoose variant:
// let connecting;
// const connect = () => (connecting ??= mongoose.connect(uri(), { ...clientOptions(), dbName: process.env.DOCUMENTDB_DATABASE ?? "app" }));
// shutdown: mongoose.disconnect()

for (const s of ["SIGINT", "SIGTERM"]) process.on(s, () => closeClient().finally(() => process.exit(0)));
module.exports = { getClient, closeClient, clientOptions };
```

If a user-supplied URI must carry required options, parse it and replace keys case-insensitively; never string-append (string-appending is what produced PyMongo's `Duplicate URI option 'retryWrites'`):

```python
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
REQUIRED = {"tls": "true", "retrywrites": "false", "maxIdleTimeMS": "120000"}
def normalize_uri(uri: str) -> str:
    parts = urlsplit(uri)
    req = {k.lower() for k in REQUIRED}
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in req]
    return urlunsplit(parts._replace(query=urlencode(kept + list(REQUIRED.items()))))
```

Node: the same with `new URL(uri)`, deleting each required key case-insensitively from `searchParams` before `set`.

Test that options reach the driver (constructing the client does not connect):

```python
def test_client_options(monkeypatch):
    monkeypatch.setenv("DOCUMENTDB_URI", "mongodb://localhost:10260/?tls=true")
    assert get_client().options.retry_writes is False
```

```javascript
test("options reach the driver", () => {
  expect(new MongoClient("mongodb://localhost:10260/?tls=true", clientOptions()).options.retryWrites).toBe(false);
});
```

**Dependency rules:** pin drivers exactly (`pymongo==4.x.y`, `beanie==2.x.y`, `"mongodb": "6.x.y"`, `"mongoose": "8.x.y"`; no `^`, `~` or `>=`); never add `motor`; the pin must be a version Learn's supported-drivers page lists.

### 2. New `skills/connection/connection-retry-helpers.md`

Text: "Retry on what the driver reports: network and server-selection errors, the `TransientTransactionError` and `UnknownTransactionCommitResult` labels, `WriteConflict` (112) and primary stepdown (`NotWritablePrimary` 10107, `PrimarySteppedDown` 189). (With `retryWrites=false` the driver rarely attaches `RetryableWriteError`; the helpers check it because it is harmless.) Never retry `DuplicateKey` (11000) or validation errors. Because `retryWrites=false`, the driver does not retry writes for you; retry a write only if it is idempotent (upsert on a stable key, `$setOnInsert`, client-supplied `_id`). For multi-document work use `with_transaction` / `withTransaction`, which already retries on the transaction labels. Capacity is vCore tiers, not request units: sustained overload is fixed by scaling the tier (or adding shards), not by backing off. 429 + `Retry-After` comes from Azure OpenAI and other HTTP APIs [needs SME confirmation that the DocumentDB service never returns 16500/429; open question 1]; use the SDK's `maxRetries` or honor the header there."

```python
# retry_util.py  (stdlib; tenacity is an acceptable drop-in)
import random, time
from pymongo.errors import (AutoReconnect, ConnectionFailure, NetworkTimeout,
    ServerSelectionTimeoutError, OperationFailure, PyMongoError, BulkWriteError)

TRANSIENT_CODES = {112, 10107, 189}
LEGACY_RU_CODES = {16500}   # RU API throttling; kept pending confirmation, see PR notes

def is_transient(e):
    if isinstance(e, (AutoReconnect, ConnectionFailure, NetworkTimeout, ServerSelectionTimeoutError)):
        return True
    if isinstance(e, PyMongoError) and any(e.has_error_label(l) for l in
            ("TransientTransactionError", "UnknownTransactionCommitResult", "RetryableWriteError")):
        return True
    return isinstance(e, OperationFailure) and e.code in TRANSIENT_CODES | LEGACY_RU_CODES

def with_retry(fn, *, attempts=5, base=0.2, cap=5.0):
    """Wrap only idempotent work."""
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if i == attempts - 1 or not is_transient(e):
                raise
            time.sleep(min(cap, base * 2 ** i) * random.uniform(0.5, 1.0))

def partition_bulk_errors(exc: BulkWriteError, ops):
    """ordered=False only. Returns (duplicates, retryable ops)."""
    dup, retry = [], []
    for we in exc.details.get("writeErrors", []):
        (dup if we["code"] == 11000 else retry).append(ops[we["index"]])
    return dup, retry
```

```javascript
// retry.js  (replaces the withRetry block in SKILL.md)
const { MongoNetworkError, MongoServerSelectionError } = require("mongodb");
const TRANSIENT_CODES = new Set([112, 10107, 189]);
const LEGACY_RU_CODES = new Set([16500]);   // pending confirmation, see PR notes
const isTransient = (e) =>
  e instanceof MongoNetworkError || e instanceof MongoServerSelectionError ||
  ["TransientTransactionError", "UnknownTransactionCommitResult", "RetryableWriteError"]
    .some((l) => e?.hasErrorLabel?.(l)) ||
  TRANSIENT_CODES.has(e?.code) || LEGACY_RU_CODES.has(e?.code);   // never 11000
async function withRetry(fn, { attempts = 5, baseMs = 200, capMs = 5000 } = {}) {
  for (let i = 0; ; i++) {
    try { return await fn(); }
    catch (e) {
      if (!isTransient(e) || i >= attempts - 1) throw e;
      await new Promise((r) => setTimeout(r, Math.min(capMs, baseMs * 2 ** i) * (0.5 + Math.random() / 2)));
    }
  }
}
function partitionBulkErrors(err, ops) {   // MongoBulkWriteError, ordered:false only
  const dup = [], retry = [];
  for (const we of err.writeErrors ?? []) (we.code === 11000 ? dup : retry).push(ops[we.index]);
  return { dup, retry };
}
module.exports = { withRetry, isTransient, partitionBulkErrors };
```

Rules (one line each): set `maxTimeMS` on interactive `find`/`aggregate` (the service default is 120 s) and `timeoutMS` on the client (Node driver 6.x / PyMongo 4.x); `bulkWrite` in batches of 500-1000 with `ordered: false` (service limit 25,000 writes per batch), partition errors, count duplicates, retry only the retryable subset, and never swallow batch errors; make seed/merge writes idempotent `updateOne(..., upsert: true)` keyed on a natural id with a unique index on that key; with `ordered: true` unattempted ops do not appear in `writeErrors`; cap LLM/embedding concurrency (`asyncio.Semaphore(4)` / `p-limit(4)`) and set `timeout=30` on those clients and 5-10 s on web-search tools; external tools (web search, LLM) may fall back to a deterministic mock after the last attempt so demos stay responsive, but never fall back silently on DB writes. Usage examples, about 10 lines each per language: one seed path (`bulkWrite` + partition + retry) and one query path (`aggregate` with `maxTimeMS` inside `with_retry`). Test: a fake raising `AutoReconnect` twice then succeeding is called 3 times; a duplicate-key `BulkWriteError` is partitioned and not retried.

### 3. `skills/connection/SKILL.md`

- Python async note: replace with "Use PyMongo's `AsyncMongoClient` (4.9+) with Beanie 2.x. Motor was deprecated on May 14, 2025 (end of life May 14, 2026; critical fixes only until May 14, 2027)."
- Singleton example (around line 158): replace the bare constructor with `getClient()` from `connection-client-factory.md`.
- "When Creating Code" (around line 260), add: "If you are generating a sample, quickstart or CLI and no user is available to answer, do not block on questions: use `connection-client-factory.md` and comment the defaults."
- "Retry Logic": replace the `withRetry` block with the `retry.js` above, keep `retryReads: true`, and add: "Azure DocumentDB capacity is vCore tiers, not request units. Keep `retrywrites=false` as in the portal-issued string, so the driver does not retry writes; wrap idempotent writes in the helper. Retry on transient network, server-selection, stepdown and transaction-label errors. See `connection-retry-helpers.md` for bulk-write partitioning and timeouts."

### 4. `skills/driver/SKILL.md`

Add two rule bullets: "Construct the client through one `get_client()` factory (tls, retryWrites=false, timeouts, pool, shutdown hook); never bare `MongoClient(uri)`: see `connection/connection-client-factory.md`." and "Wrap idempotent DB calls in the bounded backoff helper in `connection/connection-retry-helpers.md`; RU 429 semantics do not apply." [needs SME confirmation, open question 1] Draft 096 proposed these as two separate rule files (`driver-client-factory.md`, `driver-retry-transient.md`); bullets pointing to the connection files avoid duplicating the code, and maintainers can ask for the rule files instead.

### 5. `CHANGELOG.md`

One entry for the two new files and the Retry Logic replacement. Optionally, in the same PR, update `CONTRIBUTING.md` (lines 8 and 14-15), which still points at `skills/documentdb-best-practices/rules/`, a path that no longer exists, to the current `skills/<category>/<prefix>-<slug>.md` layout.

Out of scope: the `retryWrites=true` and host-suffix line fixes (K01) and the Node Entra/OIDC snippet (the Entra PR).

Follow-up (not in this PR; the harness repo is someone else's, so coordinate first): once the helpers ship, the sample-prompt build contract can add one acceptance line, "all DB access goes through the kit's `get_client()` factory and transient-error retry helper".

## Evidence

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112`: bare `MongoClient(uri)` in `app/aml_agent/db.py`; audit's retry check cites a Cosmos DB RU page.
- `runs/07-customer-review-sentiment-pipeline/20261125-054042`: Beanie 1 / Motor / Pydantic 1 pins, new client per `init_db()`, no shutdown.
- `runs/02-ai-powered-product-recommendations/20261124-181835`: `app/src/seed.js` swallows `insertMany` errors.
- `runs/02-real-time-event-stream-ingestion/20261124-203233`: `bulkWrite` errors only logged, never partitioned.
- `runs/07-lab-results-aggregator/20261124-194018`: `Duplicate URI option 'retryWrites'` from string-appending.
- `runs/18-returns-refund-workflow-orchestration/20261124-185415`: Azure OpenAI calls with no timeout or backoff.

## Open questions

1. [needs SME confirmation] Can Azure DocumentDB ever return error 16500 or HTTP-style 429 to a Mongo driver? Drafts 096 and 119 say these RU-API codes do not apply to vCore; draft 090 keeps them as harmless legacy codes. The helpers keep 16500 in a labeled set until this is answered; drop it if engineering confirms it cannot occur.
2. [needs SME confirmation] retryWrites. Draft 090 and the kit's `azure-deployment` skill state that Azure DocumentDB does not support retryable writes and that the driver default causes connection errors. Drafts 096 and 089 only state that the portal-issued string sets `retrywrites=false`, and note that Learn's feature-compatibility page lists no retryable-writes limitation. Which is correct? The PR wording ("the driver does not retry writes for you") holds either way, but the rationale text should follow the engineering answer.
3. [needs SME confirmation] Are 10107 and 189 (stepdown) the codes a client sees during Azure DocumentDB HA or cross-region failover, or does failover surface only as network errors?
4. Pool defaults: draft 096 proposes 50/5 (long-running) and 30 s socket timeout; draft 089 proposed 20/0 and 60 s, with `DB_*` env-var names instead of `DOCUMENTDB_*`. This PR uses 096's values and names. Maintainers may prefer the other set.
5. [needs SME confirmation] Driver version floors: is Beanie 2.x plus `AsyncMongoClient` (PyMongo 4.9+, GA in 4.13) the pairing the kit should recommend?
6. [needs SME confirmation] Sample counts come from one experiment with known harness artifacts. Recount after the harness re-run before quoting 85 externally.

## Source drafts

- 096-connection-skill-lacks-a-canonical-client-factory-and-transi.md (lead)
- 089-connection-defaults-for-samples-copy-paste-mongoclient-motor.md
- 090-reusable-retry-backoff-and-resilience-helpers-429-retry-afte.md
- 119-agent-kit-lacks-a-packaged-retry-backoff-helper-for-429-and-.md
