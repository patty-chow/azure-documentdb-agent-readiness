---
title: "connection/driver skills: ship a per-language get_client() factory (tls, SCRAM-SHA-256, retrywrites=false, maxIdleTimeMS=120000, env-driven pool/timeouts, singleton + shutdown) and a transient-error retry helper; drop the RU-API 429/16500 retry snippet and the retryWrites=true examples"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 85
findings: 159
bucket: sample-violated-practice
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# connection/driver: canonical `get_client()` factory + transient-error retry helper; remove RU-API retry codes and `retryWrites=true` examples

## What happens today

`skills/connection/SKILL.md` is strong on *why* (pool lifecycle, serverless vs OLTP tables) but gives an agent nothing it can paste for the stacks it actually generates:

- The only concrete client code is Node (`new MongoClient(process.env.DOCUMENTDB_URI, { maxPoolSize: 5, ... })`). Python gets a prose note about `AsyncMongoClient`; there is no PyMongo sync, PyMongo async, Beanie or Mongoose snippet anywhere in the kit.
- The connection-string example (line ~60) ends in `retryWrites=true`. So do the "Correct" examples in `skills/driver/driver-singleton-client.md` (line 26) and `skills/security/security-tls-required.md` (line 26). `skills/azure-deployment/SKILL.md` (line ~288) shows the string the portal actually hands out, `...?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`, and says leaving the driver default causes connection errors. The kit contradicts itself, and the audit rubric built from it inherited the contradiction (some checks demand `retryWrites=true`, others `retrywrites=false`).
- The "Retry Logic" section's `withRetry` keys on `err.code === 16500 || err.code === 429`. 16500 (`TooManyRequests`, carrying an embedded 429) is how the request-unit-based Azure Cosmos DB for MongoDB (RU) API reports throttling; that API also speaks the Mongo wire protocol, so the code is a real Mongo error code, but only on the RU service. Azure DocumentDB (vCore) is provisioned in M-series vCore tiers with no request-unit budget, so it does not throttle this way: no 16500/429, no `Retry-After`, no `x-ms-retry-after-ms`. The snippet never mentions the things a Mongo driver *does* surface: `TransientTransactionError` / `UnknownTransactionCommitResult` / `RetryableWriteError` labels, `AutoReconnect` / `NetworkTimeout` / `ServerSelectionTimeoutError`, `WriteConflict` (112), and the non-retryable `DuplicateKey` (11000).
- The Motor note itself says MongoDB announced the deprecation "in May 2024"; MongoDB's Motor page says Motor was deprecated on May 14, 2025, reached end of life on May 14, 2026, and gets critical fixes only until May 14, 2027.
- Nothing tells an agent to register a shutdown hook, to pin the driver exactly, or (beyond the Motor note) which Beanie major pairs with `AsyncMongoClient`.

## Why it matters

In a 100-sample experiment (221 run folders, gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), 85 of the 100 samples produced 159 audit findings in exactly this cluster, the largest single theme in the "sample violated a documented practice" bucket (~30%). Counting over the generated apps:

- 53 runs construct `MongoClient(uri)` / `AsyncIOMotorClient(uri)` with no options at all (e.g. `runs/01-anti-money-laundering-pattern-detector/20261124-200112/app/aml_agent/db.py`, whose docstring says "following driver best-practices: singleton MongoClient" and then passes nothing but the URI).
- 186 runs leave `retryWrites` unset and 19 set it to `true` in code because the kit's Node examples do; only 16 set it to `false`. Mongoose samples leave a comment like "retryWrites is commonly disabled in SRV for some managed clusters; the environment-provided URI controls it" (`runs/06-collateral-management-store/20261124-200922/app/src/index.js`) because the skill gives no rule.
- 18 runs chose Motor. The Beanie run `runs/07-customer-review-sentiment-pipeline/20261125-054042` pins `beanie==1.13.0 motor==3.1.2 pymongo==4.6.0 pydantic==1.10.12`, i.e. a Beanie 1 / Motor / Pydantic 1 stack, and creates a new `AsyncIOMotorClient` inside `init_db()` with no singleton. The earlier run of the same sample (`20261124-183656`) logged the gap explicitly: the skills say "use AsyncMongoClient" but do not say which Beanie release makes that work, so the builder picked Motor (decision D004) and the audit filed a doc gap.
- 0 runs register a `SIGINT`/`SIGTERM` close. 0 runs ship any backoff helper (`tenacity`, `retryWithBackoff` or hand-rolled); the only "retry" seen is a single webhook re-send.
- The RU framing leaked downstream: 64 of 150 retry-related audit checks across the runs demand "honor Retry-After / 429 / avoid RU spikes" and several cite `learn.microsoft.com/azure/cosmos-db/optimize-cost-throughput` as the source. Agents reading the kit learn the wrong failure model for vCore.

Because the published connection string turns driver retryable writes off, application-level retries matter *more* on this service, and the kit currently teaches none that would fire.

## Proposed change (one PR)

### 1. `skills/connection/SKILL.md`

**a. Fix the connection string example and the Motor date** (section "Connection String Format") to the published form and state the reason once:

```
mongodb+srv://<user>:<pw>@<cluster>.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000
```

Also correct the Python async note to "Motor was deprecated on May 14, 2025 (end of life May 14, 2026; critical fixes only until May 14, 2027)".

> Keep `retrywrites=false`: this is the string the portal issues for Azure DocumentDB; driver-level retryable writes are off, so transient write failures must be handled by the application (see "Retrying transient errors" below). Keep `maxIdleTimeMS=120000` unless a scenario table below says otherwise. Do not set `retryWrites: true` in driver options; it overrides the URI.

**b. New section "Canonical client factory (copy this)"**, placed before "Configuration Design". Rules stated once above the snippets: one module-level client per process; read the URI from `DOCUMENTDB_URI` and fail fast if it is missing or does not start with `mongodb+srv://` / contain `tls=true`; timeouts and pool sizes come from env with two documented defaults (serverless: `maxPoolSize=5 minPoolSize=0 maxIdleTimeMS=30000`; long-running: `maxPoolSize=50 minPoolSize=5 maxIdleTimeMS=120000`); `serverSelectionTimeoutMS=5000 connectTimeoutMS=10000 socketTimeoutMS=30000` unless OLAP; close on `SIGINT`/`SIGTERM`.

PyMongo (sync):

```python
# db.py — one client per process
import os, signal, sys
from pymongo import MongoClient

_client: MongoClient | None = None

def _opts() -> dict:
    serverless = os.getenv("DOCUMENTDB_SERVERLESS", "false").lower() == "true"
    return dict(
        tls=True,
        retryWrites=False,                      # matches the Azure DocumentDB connection string
        serverSelectionTimeoutMS=int(os.getenv("DOCUMENTDB_SERVER_SELECTION_TIMEOUT_MS", 5000)),
        connectTimeoutMS=int(os.getenv("DOCUMENTDB_CONNECT_TIMEOUT_MS", 10000)),
        socketTimeoutMS=int(os.getenv("DOCUMENTDB_SOCKET_TIMEOUT_MS", 30000)),
        maxPoolSize=int(os.getenv("DOCUMENTDB_MAX_POOL_SIZE", 5 if serverless else 50)),
        minPoolSize=int(os.getenv("DOCUMENTDB_MIN_POOL_SIZE", 0 if serverless else 5)),
        maxIdleTimeMS=int(os.getenv("DOCUMENTDB_MAX_IDLE_TIME_MS", 30000 if serverless else 120000)),
        appname=os.getenv("APP_NAME", "sample"),
    )

def get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.environ["DOCUMENTDB_URI"]           # KeyError is the right failure
        if "tls=true" not in uri.lower():
            raise RuntimeError("DOCUMENTDB_URI must include tls=true")
        _client = MongoClient(uri, **_opts())
    return _client

def close_client(*_):
    global _client
    if _client is not None:
        _client.close(); _client = None

def install_shutdown_handlers() -> None:
    # Call once from the process entry point (CLI/worker main), not at import time;
    # under uvicorn/gunicorn use the framework's lifespan/shutdown hook instead,
    # so the server's own SIGTERM handling is not replaced.
    for _sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(_sig, lambda s, f: (close_client(), sys.exit(0)))
```

PyMongo async + Beanie 2 (replace the Motor note's prose with this):

```python
# db.py — PyMongo >= 4.9 AsyncMongoClient; Beanie >= 2.0 accepts it directly.
# Motor is deprecated (May 14, 2025), end of life May 14, 2026, critical fixes only until May 14, 2027:
# do not add motor to requirements.
import os
from pymongo import AsyncMongoClient
from beanie import init_beanie

_client: AsyncMongoClient | None = None

def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(os.environ["DOCUMENTDB_URI"], **_opts())   # same _opts() as above
    return _client

async def init_db(models: list[type]) -> None:
    await init_beanie(database=get_client()[os.getenv("DOCUMENTDB_DATABASE", "app")], document_models=models)

async def close_client() -> None:            # call from FastAPI lifespan / asyncio shutdown
    global _client
    if _client is not None:
        await _client.close(); _client = None
```

Node driver:

```javascript
// db.js — one client per process
const { MongoClient } = require("mongodb");
const serverless = process.env.DOCUMENTDB_SERVERLESS === "true";
const num = (k, d) => Number(process.env[k] ?? d);

let client;
function getClient() {
  if (!client) {
    const uri = process.env.DOCUMENTDB_URI;
    if (!uri || !/tls=true/i.test(uri)) throw new Error("DOCUMENTDB_URI must be set and include tls=true");
    client = new MongoClient(uri, {
      tls: true,
      retryWrites: false,                       // matches the Azure DocumentDB connection string
      serverSelectionTimeoutMS: num("DOCUMENTDB_SERVER_SELECTION_TIMEOUT_MS", 5000),
      connectTimeoutMS: num("DOCUMENTDB_CONNECT_TIMEOUT_MS", 10000),
      socketTimeoutMS: num("DOCUMENTDB_SOCKET_TIMEOUT_MS", 30000),
      maxPoolSize: num("DOCUMENTDB_MAX_POOL_SIZE", serverless ? 5 : 50),
      minPoolSize: num("DOCUMENTDB_MIN_POOL_SIZE", serverless ? 0 : 5),
      maxIdleTimeMS: num("DOCUMENTDB_MAX_IDLE_TIME_MS", serverless ? 30000 : 120000),
      appName: process.env.APP_NAME ?? "sample",
    });
  }
  return client;
}
async function closeClient() { if (client) { await client.close(); client = undefined; } }
for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => closeClient().finally(() => process.exit(0)));
module.exports = { getClient, closeClient };
```

Mongoose:

```javascript
// db.js — Mongoose passes these options straight to the driver
const mongoose = require("mongoose");
let connecting;
function connect() {
  if (!connecting) {
    const uri = process.env.DOCUMENTDB_URI;
    if (!uri || !/tls=true/i.test(uri)) throw new Error("DOCUMENTDB_URI must be set and include tls=true");
    connecting = mongoose.connect(uri, {
      dbName: process.env.DOCUMENTDB_DATABASE ?? "app",
      tls: true, retryWrites: false,
      serverSelectionTimeoutMS: 5000, connectTimeoutMS: 10000, socketTimeoutMS: 30000,
      maxPoolSize: Number(process.env.DOCUMENTDB_MAX_POOL_SIZE ?? 50),
      maxIdleTimeMS: Number(process.env.DOCUMENTDB_MAX_IDLE_TIME_MS ?? 120000),
    });
  }
  return connecting;
}
for (const sig of ["SIGINT", "SIGTERM"]) process.on(sig, () => mongoose.disconnect().finally(() => process.exit(0)));
module.exports = { connect };
```

**c. New bullet list "Dependency rules"** under the factory: pin the driver exactly (`pymongo==4.x.y`, `beanie==2.x.y`, `"mongodb": "6.x.y"`, `"mongoose": "8.x.y"`, no `^`/`~`/`>=`); never add `motor`; the pin must be a version the Learn "supported drivers" page lists.

**d. Replace the "Retry Logic" section** with "Retrying transient errors":

> Azure DocumentDB does not throttle with HTTP 429 / `Retry-After` / `x-ms-retry-after-ms` and has no request units; those belong to the Cosmos DB RU API and will never appear on a Mongo driver error. Retry on what the driver reports: network/server-selection errors and the `TransientTransactionError`, `UnknownTransactionCommitResult` and `RetryableWriteError` labels, plus `WriteConflict` (112) inside transactions. (With `retrywrites=false` the driver does not attempt retryable writes, so `RetryableWriteError` will rarely be attached; checking for it is harmless but network/selection errors are the main signal.) Never retry `DuplicateKey` (11000) or validation errors; those are domain outcomes. Retry a write only if it is idempotent (upsert on a stable key, `$setOnInsert`, or a client-supplied `_id`). For multi-document work use `session.with_transaction` / `session.withTransaction`, which already retries on the two transaction labels.

```python
# retry.py — bounded exponential backoff with jitter (tenacity==9.x pinned)
from pymongo.errors import (AutoReconnect, ConnectionFailure, NetworkTimeout,
                            ServerSelectionTimeoutError, OperationFailure, PyMongoError)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random_exponential

def _is_transient(e: BaseException) -> bool:
    if isinstance(e, (AutoReconnect, ConnectionFailure, NetworkTimeout, ServerSelectionTimeoutError)):
        return True
    if isinstance(e, PyMongoError) and (e.has_error_label("TransientTransactionError")
                                        or e.has_error_label("UnknownTransactionCommitResult")
                                        or e.has_error_label("RetryableWriteError")):
        return True
    return isinstance(e, OperationFailure) and e.code == 112      # WriteConflict; 11000 is NOT here

db_retry = retry(retry=retry_if_exception(_is_transient), stop=stop_after_attempt(5),
                 wait=wait_random_exponential(multiplier=0.2, max=5), reraise=True)

@db_retry
def upsert_customer(coll, doc):           # idempotent: safe to replay
    coll.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
```

```javascript
// retry.js
const { MongoNetworkError, MongoServerSelectionError, MongoNetworkTimeoutError } = require("mongodb");
const isTransient = (e) =>
  e instanceof MongoNetworkError || e instanceof MongoServerSelectionError || e instanceof MongoNetworkTimeoutError ||
  e?.hasErrorLabel?.("TransientTransactionError") || e?.hasErrorLabel?.("UnknownTransactionCommitResult") ||
  e?.hasErrorLabel?.("RetryableWriteError") || e?.code === 112;          // never 11000 (DuplicateKey)
async function retryWithBackoff(fn, { attempts = 5, baseMs = 200, maxMs = 5000 } = {}) {
  for (let i = 0; ; i++) {
    try { return await fn(); }
    catch (e) {
      if (!isTransient(e) || i >= attempts - 1) throw e;
      const delay = Math.min(maxMs, baseMs * 2 ** i) * (0.5 + Math.random() / 2);   // jitter
      await new Promise((r) => setTimeout(r, delay));
    }
  }
}
module.exports = { retryWithBackoff, isTransient };
```

Keep the existing `retryReads: true` line; it is correct.

### 2. `skills/driver/SKILL.md`

Add two rules to the list: `driver-client-factory.md` ("Construct the client through a single `get_client()` factory that sets tls, retryWrites=false, timeouts, pool size and a shutdown hook; never `MongoClient(uri)` bare") and `driver-retry-transient.md` ("Wrap idempotent DB calls in a bounded backoff helper keyed on driver transient labels; RU/429 semantics do not apply"). Each rule file follows the existing Why / Incorrect / Correct layout and links to the section above rather than duplicating the code.

### 3. `skills/driver/driver-singleton-client.md` and `skills/security/security-tls-required.md`

Change `retryWrites: true` to `retryWrites: false` in the "Correct" blocks (lines 26 in both) with the one-line comment `// matches the Azure DocumentDB connection string`. These two files are what agents quote back when they set `retryWrites: true` in code.

### Follow-up (not in this PR)

Once the snippet ships, the sample-prompt build contract in the readiness harness can add a single acceptance line: "all DB access goes through the kit's `get_client()` factory and transient-error retry helper".

## Evidence (run folders; no connection strings)

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112` — `app/aml_agent/db.py` is `MongoClient(DOCUMENTDB_URI)` with a "best-practices" docstring; `05-audit.json` "Retry on throttling" check demands `Retry-After` handling and cites a Cosmos DB RU page.
- `runs/07-customer-review-sentiment-pipeline/20261125-054042` — Beanie 1.13 + Motor 3.1.2 + Pydantic 1 pins, new `AsyncIOMotorClient(uri)` per `init_db()` call, `retryWrites` unset, no shutdown.
- `runs/07-customer-review-sentiment-pipeline/20261124-183656` — `02-readiness.json` information gap and `05-audit.json` doc gap "Beanie async-driver compatibility": the kit says use `AsyncMongoClient` but not which Beanie major; builder chose Motor (decision D004).
- `runs/06-collateral-management-store/20261124-200922` — Mongoose `connect()` with timeouts but no pool, no `retryWrites` decision (left to a comment), no `SIGINT`/`SIGTERM` handler.
- `runs/04-customer-journey-mapper/20261124-203553` — `src/db.js` sets `retryWrites: true` in client options, copied from the kit's Node examples; no retry wrapper.

## Verification

### 1. Already covered? partially_covered
The kit has pieces but not the ask. Covered: the singleton rule (`skills/driver/driver-singleton-client.md`; `skills/connection/SKILL.md` line 152, "create ONE MongoClient and reuse it"), the Motor deprecation note (`skills/connection/SKILL.md` lines 45-49, "Use PyMongo's native `AsyncMongoClient` (PyMongo 4.9+), **not** Motor"), and `retryReads: true` (line 215). Missing: there is no Python, Beanie or Mongoose client snippet in `skills/` or `knowledge-base/` (grep for pymongo/mongoose finds only prose in connection/SKILL.md and local-deployment config rules), no Beanie-version guidance, no shutdown hook, no transient-label retry helper (grep for TransientTransactionError / RetryableWriteError / SIGTERM returns nothing). The contradictions the draft names are real. `skills/connection/SKILL.md:60` ends `...authMechanism=SCRAM-SHA-256&retryWrites=true`, `skills/driver/driver-singleton-client.md:26` has `{ maxPoolSize: 50, retryWrites: true }`, `skills/security/security-tls-required.md:26` has `retryWrites: true`, and `skills/azure-deployment/SKILL.md:288-291` has `retrywrites=false&maxIdleTimeMS=120000` with the note "leaving it at the driver default will cause connection errors". `skills/connection/SKILL.md:230` has `if (err.code === 16500 || err.code === 429)`. The documentdb-mcp server does not generate application client code, so it is not the place for this fix.

### 2. Premise true? confirmed (minor corrections applied to the body)
The core premise holds. The documented Azure DocumentDB connection string carries `tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`. Capacity is vCore M-series tiers, not request units, so RU throttling codes do not apply. The kit contradicts itself as quoted above. Evidence spot-checked: `runs/04-customer-journey-mapper/20261124-203553/app/src/db.js:16` has `retryWrites: true`, `runs/01-anti-money-laundering-pattern-detector/20261124-200112/app/aml_agent/db.py:20` has `MongoClient(DOCUMENTDB_URI)` bare, and `runs/07-customer-review-sentiment-pipeline/20261125-054042` requirements pin `beanie==1.13.0`, `motor==3.1.2`. I corrected four things in the body:
- (a) The draft said 16500/429 "never appear on the Mongo wire protocol". In fact the RU-based Azure Cosmos DB for MongoDB API also speaks the wire protocol and returns 16500 (TooManyRequests) as a Mongo error. The accurate statement is that these are RU-API throttling codes and vCore has no RU budget.
- (b) The Motor dates. Per https://www.mongodb.com/docs/drivers/motor/, Motor was "deprecated" "As of May 14, 2025", reached end of life on May 14, 2026, and gets critical fixes until May 14, 2027. The draft's "critical fixes only until May 2026" was wrong, and the kit's own "May 2024" is also wrong, so the PR now corrects both.
- (c) With retrywrites=false the RetryableWriteError label rarely appears. The body now says so.
- (d) The module-import-time signal registration would override uvicorn/gunicorn handlers. It is now an explicit `install_shutdown_handlers()` called from the entry point, with lifespan hooks for web servers.

The Learn feature-compatibility page (https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features) lists no retryable-writes limitation. The draft therefore keeps the kit's own framing, "driver-level retryable writes are off per the published string", and does not claim the service rejects them.

### 3. Maintainer skeptic: confirmed
The draft names exact files and lines (connection/SKILL.md lines 60 and 209-235, driver-singleton-client.md:26, security-tls-required.md:26, plus two new driver rule files). It fixes a real internal contradiction and a wrong-service retry snippet, both specific to Azure DocumentDB. A maintainer might split the four-language factory into a follow-up, or trim it to PyMongo plus Node, but the retryWrites and 16500/429 fixes alone justify accepting it.

## Finding ids

- F0027
- F0201
- F0170
- F0239
- F0029
- F0035
- F0141
- F0171
- F0207
- F0245
- F0282
- F0305
- F0375
- F0379
- F0411
- F0412
- F0450
- F0487
- F0520
- F0549
- F0309
- F0447
- F0518
- F0372
- F0306
- F0413
- F0621
- F0652
- F0684
- F0685
- F0753
- F0817
- F0873
- F0587
- F0622
- F0686
- F0719
- F0752
- F0818
- F0841
- F0878
- F0910
- F0937
- F1065
- F1066
- F1096
- F1126
- F1219
- F0880
- F0882
- F0908
- F0962
- F1028
- F1062
- F1063
- F1094
- F1247
- F1290
- F1325
- F1328
- F1332
- F1424
- F1510
- F1253
- F1245
- F1246
- F1321
- F1359
- F1393
- F1426
- F1511
- F1394
- F1546
- F1583
- F1615
- F1675
- F1709
- F1745
- F1779
- F1512
- F1651
- F1706
- F1776
- F1880
- F1881
- F1885
- F1971
- F2008
- F2039
- F2076
- F2108
- F2109
- F1941
- F1975
- F2009
- F2043
- F2141
- F2173
- F2235
- F2350
- F2146
- F2174
- F2353
- F2378
- F2382
- F2452
- F2480
- F2507
- F2542
- F2546
- F2576
- F2640
- F2674
- F2454
- F2538
- F2539
- F2638
- F2639
- F2641
- F2705
- F2769
- F2800
- F2867
- F2900
- F2930
- F2968
- F3002
- F3034
- F2703
- F2736
- F2766
- F2863
- F2928
- F2967
- F3036
- F3064
- F3098
- F3140
- F3166
- F3250
- F3251
- F3289
- F3316
- F3347
- F3063
- F3095
- F3137
- F3165
- F3282
- F3388
- F3415
- F3485
- F3489
- F3522
- F3385
- F3413
- F3414
- F3452
- F3520
