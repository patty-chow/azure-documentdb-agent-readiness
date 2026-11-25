---
id: K07
title: "connection and driver skills: get_client() factory with vCore-correct retry and bulk-write helpers, a 'What differs from MongoDB' block, Beanie 2.x on AsyncMongoClient, transactions with sessions, a copy-paste PyMongo connect rule, and reproducible installs"
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
  - 027-believes-the-unsupported-feature-list-is-the-ru-api-generic-.md
  - 135-believes-beanie-requires-motor-asynciomotorclient-and-that-m.md
  - 088-reproducible-installs-dependency-pinning-lockfile-policy-and.md
  - 095-misc-one-off-agent-kit-gaps-bicep-mongoclusters-example-mong.md
  - 120-documentdb-driver-skill-lacks-an-authoritative-copy-paste-py.md
merged_from:
  - K07
  - K21
  - K37
  - K29
  - K15
  - K16
open_questions: 7
---

# connection and driver skills: `get_client()` factory with vCore-correct retry and bulk-write helpers, a "What differs from MongoDB" block, Beanie 2.x on `AsyncMongoClient`, transactions with sessions, a copy-paste PyMongo connect rule, and reproducible installs

One PR for the two skills an agent loads every time it writes code that creates a MongoDB client: `skills/connection/` and `skills/driver/`. It adds five rule files and edits both `SKILL.md` files, plus small consistency fixes in `skills/natural-language-querying/`, `skills/data-modeling/`, `compat/QUICKSTART.md`, `skills/azure-deployment/SKILL.md`, `docs/SKILLS.md` and `CHANGELOG.md`.

## What happens today

`skills/connection/SKILL.md` explains *why* pools, timeouts and retries matter, and `skills/driver/SKILL.md` links a single rule (`driver-singleton-client.md`), but neither gives an agent code it can paste for the things sample apps actually need.

**Client construction (from K07, K16)**

- **No production client constructor with full options.** The connection skill's only code is Node: an Azure Functions example with pool options only (around line 107) and the singleton example (line 159), `new MongoClient(process.env.DOCUMENTDB_URI)` with no options. Python gets a prose note about `AsyncMongoClient`. `skills/driver/SKILL.md` claims to cover "Node.js, Python, Java, Go, and .NET", but all of its code is JavaScript. The only PyMongo code in the kit is in `skills/local-deployment/` (`local-env-driven-config.md`, `local-connection-config.md`); it targets the local container, and the `tlsAllowInvalidCertificates` setting it shows (sometimes as an anti-pattern) must never be used against the managed service. There is no PyMongo async/Beanie or Mongoose snippet anywhere in the kit, no `ping` check at startup, no shutdown hook, and no link to the Learn Python quickstart.
- **No defaults for unattended builds.** The tuning tables give ranges, and "Configuration Design" (line 80) and "When Creating Code" (around line 263) tell the agent to ask the user questions first. A sample builder has no user to ask, so it ships driver defaults.

**Retries and bulk writes (from K07)**

- **The retry snippet targets the wrong service.** "Retry Logic" (lines 209-241) defines `withRetry` that retries only on `err.code === 16500 || err.code === 429`, the request-unit throttling codes of Azure Cosmos DB for MongoDB (RU). Azure DocumentDB is sized in vCore tiers with no request units and never returns either code: neither appears in the engine's error-mapping files or on Learn's troubleshooting table, and no run in the experiment received one (DECISIONS.md, topic 2). The snippet re-throws, on the first attempt, the errors a driver does surface: network resets, server-selection timeouts, `HostUnreachable` (6), `ShutdownInProgress` (91) and `ExceededTimeLimit` (50) around a failover, and `WriteConflict` (112) inside a transaction. It has no jitter, no Python version, and nothing for `bulkWrite` partial failures. The same section (lines 211-219) says "Azure DocumentDB supports retryable reads" (no Learn page says so) and "for transient errors (network blips, failovers), the driver will automatically retry", which is overstated: `retrywrites=false` is required and the server sends no `RetryableWriteError` label, so drivers never retry writes, and Learn's reliability page puts retry responsibility on the application. Line 207 ("Use `nearest` read preference for geo-distributed setups") has no basis either: the gateway discards `nearest`/`primaryPreferred`/`secondaryPreferred`, rejects `secondary` and tag sets with `FailedToSatisfyReadPreference`, and standby shards never serve reads (DECISIONS.md, topic 9). `skills/driver/SKILL.md` defers retries to the connection skill, so no skill ships a usable helper.

**Compatibility (from K21)**

- Neither `SKILL.md` has a supported-versus-unsupported summary. No file under `skills/` or `knowledge-base/` mentions change streams. Cross-shard transactions are stated only in `skills/sharding/sharding-logical-vs-physical.md:45`, which loads only for sharding tasks. `skills/natural-language-querying/SKILL.md:258` says only "Azure DocumentDB supports multi-document transactions", with nothing on shards or change streams, and line 261 (and `compat/QUICKSTART.md:103`) links to `learn.microsoft.com/azure/documentdb/compatibility`, which returns 404.
- `skills/data-modeling/model-embed-vs-reference.md:7,49`, `model-16mb-limit.md:7,45` and `model-denormalize-reads.md:39` still say "Cosmos DB for MongoDB vCore" and link to `/azure/cosmos-db/mongodb/vcore/` pages, reinforcing the Cosmos DB association behind wrong answers.

**Transactions (from K15)**

- Nothing in `skills/` shows how to run a multi-document transaction: `grep -rni transaction skills knowledge-base` finds only one bullet in `skills/natural-language-querying/SKILL.md` plus sharding and HA notes. There is no `startSession()` / `withTransaction()` example, no note that the session must be passed to every operation, no mention of the 30-second maximum transaction lifetime (Learn limitations page), and nothing about the two service-specific facts an agent cannot guess: the server returns `WriteConflict` (112) and `NoSuchTransaction` (251) without the `TransientTransactionError` label (engine issue documentdb/documentdb#339, reproduced against the managed service), so `withTransaction()` does not retry a conflict and the application must re-run the transaction itself; and DDL/admin commands (`createIndexes`, `dropIndexes`, `drop`, `renameCollection`, `listCollections`, ...) are refused inside a transaction with code 263. `docs/SKILLS.md` describes `driver/` as "singleton client, pooling".
- Separately, `skills/azure-deployment/` ships a correct `Microsoft.DocumentDB/mongoClusters` Bicep template, but nothing tells an agent not to generate `Microsoft.DocumentDB/databaseAccounts` or `az cosmosdb` instead.

**Python async, Motor and Beanie (from K07, K37)**

- The "Python async note" blockquote (lines 45-49) correctly says to use PyMongo's `AsyncMongoClient` and not Motor, but gives "4.9+" (the beta; the async API is GA from PyMongo 4.13, and Beanie 2 requires `pymongo>=4.11`), dates Motor's deprecation to "May 2024" and critical fixes to "through May 2026"; MongoDB's Motor page gives deprecation May 14, 2025, end of life May 14, 2026, critical fixes until May 14, 2027 (DECISIONS.md, topic 4, items 4.5 and 4.7). It says nothing about ODMs: neither `skills/` nor `knowledge-base/` mentions Beanie, whose older docs taught agents that "Beanie requires an `AsyncIOMotorClient`". The agent reads the two as a conflict, hedges, and falls back to Motor.

**Dependencies (from K29)**

- No skill says how a generated project should declare or install dependencies, or which driver/ODM versions the kit has verified. The kit's own `compat/` workload follows a good convention (`"mongodb": "6.20.0"` in `compat/package.json`, `npm ci` in `compat/QUICKSTART.md`) but never states it as guidance. A search of `skills/` and `knowledge-base/` for lockfile, `npm ci`, `pip-compile`, `requirements.txt` or `--save-exact` finds nothing about application dependencies.

The `retryWrites=true` examples (connection/SKILL.md:60, driver-singleton-client.md:26, security-tls-required.md:26) and the host-suffix fixes are handled in K01; Microsoft Entra ID (MONGODB-OIDC) guidance, including the PyMongo OIDC example from draft 120 and the Node Entra snippet from draft 089, is handled in K03 / the Entra PR. This PR does not touch those lines.

## Why it matters

In a 100-sample experiment (gpt-5-mini building sample apps with this kit plus the DocumentDB, Azure and Learn MCP servers; 221 run folders), **at least 85 of the 100 samples** had at least one finding in this merged group. All figures come from one experiment run with known harness artifacts and may shift on a re-run (open question 5, a harness recount, not an SME item). The 85 is the union K07 computed over its four drafts' finding ids. The other members add 42 sample-hits (24 + 11 + 3 + 3 + 1); their finding ids could not be mapped back to sample names from the drafts, so how many of them fall outside K07's 85 is unresolved: the distinct count is between 85 and 100, and `sample_count` records the confirmed floor. Per member:

- **Client factory, retry and bulk-write helpers (K07): 85 samples** (drafts 096: 85, 089: 12, 090: 14, 119: 1; the last three are inside the 85).
  - 53 runs (of the 221 run folders) constructed `MongoClient(uri)` / `AsyncIOMotorClient(uri)` with no options, one under a docstring claiming "driver best-practices". 38 never set any pool size or timeout.
  - 0 runs registered a `SIGINT`/`SIGTERM` close; 0 shipped a DB backoff helper.
  - 18 runs chose Motor; one pinned `beanie==1.13.0 motor==3.1.2 pydantic==1.10.12` and created a new client per `init_db()` call, after logging that the kit did not say which Beanie release supports `AsyncMongoClient`.
  - Unordered `insertMany`/`bulkWrite` errors were logged and dropped (`.catch(console.warn)`), so seeding could end partial without notice; duplicate-key errors were never separated from retryable ones.
  - 2 runs hit PyMongo's `Duplicate URI option 'retryWrites'` by string-appending options onto the env URI.
  - The RU failure model leaked downstream: 64 of 150 retry-related audit checks demanded "honor 429 / Retry-After", citing Cosmos DB RU throughput pages; Azure DocumentDB never returns these codes (see Resolved). Azure OpenAI calls, which do return 429 + `Retry-After`, had no timeout or backoff.
- **Compatibility block (K21): 24 samples** answered "which MongoDB features are unsupported" from the Azure Cosmos DB for MongoDB (RU) prior:

  | Claim in the agent's answer | Samples (of 24) | Azure DocumentDB |
  |---|---|---|
  | Multi-document transactions "limited" or "only within a partition/shard key" | 20 | Supported across collections and across logical and physical shards (`startSession` / `withTransaction` / `commitTransaction` / `abortTransaction`, wire versions 5.0 to 8.0); 30-second maximum lifetime; conflicts arrive as `WriteConflict` (112) without the `TransientTransactionError` label, so the application retries |
  | Change streams "not supported" or "support varies" | 8 | Supported on single-shard clusters with no enablement step: `watch()`, `resumeAfter` / `startAtOperationTime`, pre-images, 400 MB active log plus historical replay up to 35 days; `updateDescription` (opt-in per collection) and multi-shard change streams (enabled under Settings > Features) are preview |
  | "Some aggregation stages may be missing" | 18 | 58/60 stages, 181/181 aggregation operators, 99.03% overall; the missing stages are diagnostic |
  | No server-side JavaScript; no host-level admin commands | 22 / 15 | Correct |

  A Learn MCP search corrected the belief before code was written in these runs, so no sample shipped a workaround; without it the agent co-locates documents by shard key to keep a transaction "inside one partition", polls instead of using change streams, and avoids `$setWindowFields`, `$facet` and `$graphLookup`. The sharding skill already says cross-shard transactions work, so this is also an internal-consistency fix.
- **Reproducible installs (K29): 11 samples** (7 high severity).
  - Versions invented from memory: one Node sample failed `npm install` twice with `ETARGET` for `supertest@^6.4.3` then `^6.4.4` (the 6.x line stops at 6.3.4), halting the build; a Python sample failed on `pymongo==4.5.1` and `langchain==0.0.418`, which do not exist, and the agent "fixed" it by relaxing both to `>=` ranges.
  - 7 Python samples shipped `requirements.txt` with `>=` ranges or bare names; where the agent pinned, it used training-era versions (`openai==0.27.0`, `motor==3.1.1`).
  - 2 Node samples committed `package-lock.json` but kept caret ranges and told users to run `npm install`, not `npm ci`.
  - Stack contradicting the kit: one sample pinned `beanie==1.24.0` + `motor==3.1.1` although the connection skill says not to use Motor (also counted under K37).
  - A plain "pin exact versions" rule would pin a hallucinated version; the rule must say **resolve first, then lock**.
- **Beanie 2.x on `AsyncMongoClient` (K37): 3 samples** wrote their Beanie layer on Motor after hedging between the skill and the Beanie-needs-Motor prior. Two pin Beanie 1.x with Motor; the third (`voice-of-customer-sentiment-hub`) uses Motor in code but pins neither, so the app cannot import its own database layer. One found the Learn Beanie quickstart (`beanie==2.2.0` with `AsyncMongoClient`) and still shipped `beanie==1.26.0` + `motor==3.1.1`. Beanie 2.0 dropped Motor; the Learn docs need no change.
- **Transactions with sessions (K15): 3 samples** with recorded findings (07-multi-currency-ledger: missing transaction recipe; 03-next-best-action-multi-agent: asked for an IaC example the kit already ships; 10-wealth-management-rag-portal: PII-redaction request, out of scope). Transaction doc gaps also appear in the run folders of 03-core-banking-transaction-ledger, 12-clv-prediction-pipeline, 15-supplier-po-management, 16-multi-touch-attribution-model and 20-provider-directory-semantic-search; those are not separate recorded findings and are not counted. In 07 the agent designed "transactionally-protected" posting and wrote no transaction code. The failure modes are quiet: a write without `{ session }` lands outside the transaction; because the server sends no `TransientTransactionError` label, a write conflict (112) is not retried by `withTransaction` and the transaction simply fails (engine issue #339: "one of the transactions fails and we lose an update"), while an unbounded or non-idempotent application retry loop double-applies side effects; long work inside the transaction risks the 30-second lifetime.
- **Copy-paste PyMongo connect (K16): 1 sample** (19-care-coordination-multi-agent) logged a high-priority gap: no authoritative PyMongo connection example; the builder wrote a bare `MongoClient(DOCUMENTDB_URI)`, which fails at the first query with a server-selection timeout if the URI was hand-typed or trimmed. The pattern is wider: by grep, 57 run folders contain Python that builds a `MongoClient(...)` (about 93 calls); about 7 pass `tls=True` and about 5 pass `retryWrites=False` (indicative, not per-sample review).

## Proposed change

File by file. Line numbers are against kit commit `4f41c15` (2026-11-23).

### 1. New `skills/connection/connection-client-factory.md` (K07, plus a startup `ping` from K16)

Same layout as `driver-singleton-client.md`. Rules stated once: one client per process (in serverless, create it at module scope so warm invocations reuse it); read `DOCUMENTDB_URI`, fail fast if it is missing or lacks `tls=true`; pass options to the constructor and never string-append to the URI (if a user-supplied URI must be normalized, parse it, as below); set `retryWrites=False` (required: Azure DocumentDB does not support retryable writes, which is why the portal-issued connection string carries `retrywrites=false`; rationale in `connection-retry-helpers.md`); pool and timeouts from env with two documented defaults; verify with `ping` at startup (see `driver/driver-python-connect.md`); close on shutdown. When no user is available to answer questions (samples, quickstarts, CLIs), use these defaults and comment them. (Draft 096 also proposed rejecting URIs that do not start with `mongodb+srv://`; that check is left out because the local-deployment skill connects with `mongodb://localhost:10260`.)

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
    return dict(tls=True, retryWrites=False,   # required: the service does not support retryable writes
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
        _client.admin.command("ping")   # fail fast on bad host, credentials, firewall or TLS
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

# Async: PyMongo AsyncMongoClient (GA from 4.13; beta in 4.9). Beanie 2.x accepts it directly
# and requires pymongo>=4.11; Learn's Beanie quickstart is tested with Beanie 2.2.0 + PyMongo 4.19.0.
# Do not add motor (deprecated May 14, 2025; end of life May 14, 2026; critical fixes until May 14, 2027).
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

(Merge note: the `ping` line in `get_client()` comes from K16; K07's original factory had no startup check. Maintainers who prefer construction without I/O can move the `ping` to the app's startup hook instead.)

```javascript
// db.js  (mongodb driver; Mongoose forwards the same options)
const { MongoClient } = require("mongodb");
const sl = process.env.DOCUMENTDB_SERVERLESS === "true";
const n = (k, d) => Number(process.env[k] ?? d);
function clientOptions() {
  return { tls: true, retryWrites: false,   // required: the service does not support retryable writes
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

Test that options reach the driver (constructing the client does not connect; the test uses the client constructor directly so the `ping` is not run):

```python
def test_client_options(monkeypatch):
    monkeypatch.setenv("DOCUMENTDB_URI", "mongodb://localhost:10260/?tls=true")
    assert MongoClient(_uri(), **_opts()).options.retry_writes is False
```

```javascript
test("options reach the driver", () => {
  expect(new MongoClient("mongodb://localhost:10260/?tls=true", clientOptions()).options.retryWrites).toBe(false);
});
```

**Dependency rules:** pin drivers exactly (`pymongo==4.x.y`, `beanie==2.x.y`, `"mongodb": "7.x.y"` (or `6.x.y` on Node 22 and earlier), `"mongoose": "8.x.y"`; no `^`, `~` or `>=`); never add `motor`; Learn publishes no tested-driver table (the FAQ says only that any wire-protocol driver connects), so the pin must be the current stable release and at least the row MongoDB's compatibility table marks fully compatible for server 5.0 to 8.0 (PyMongo 4.9, `mongodb` 6.9, `mongoose` 8.7, Java 5.2, .NET 2.29, Go 2.1, Rust 3.1). On Node 24 use `mongodb` 7.x; MongoDB marks 6.x untested there. How to resolve and lock those versions: `driver/driver-reproducible-installs.md`.

### 2. New `skills/connection/connection-retry-helpers.md` (K07, cross-linked to K15's transactions rule)

Text: "Retry on what the driver and the gateway report: network and server-selection errors, `HostUnreachable` (6), `ShutdownInProgress` (91) and `ExceededTimeLimit` (50), the codes a client can see while a shard failover or primary drain outlives the gateway's own internal retry (Learn documents failover as 'write slowness' and 'brief transient errors' and names no code; these are the open-source gateway's candidates). Code 50 is also what a `maxTimeMS` expiry returns, so the bounded attempt count is what keeps a genuinely slow query from being re-run forever. Never retry `DuplicateKey` (11000), validation errors, `IllegalOperation` (20: a write to a replica or demoted cluster, fix the connection string), `TooManyLogicalSessions` (261: reduce the pool, do not back off) or `OperationNotSupportedInTransaction` (263). Do not code against 16500 or 429: Azure DocumentDB has no request units and never returns them (not in any engine error-mapping file, not on Learn's troubleshooting table, never observed in 120 runs); do not code against `PrimarySteppedDown` (189), which the engine cannot emit, or `NotWritablePrimary` (10107), which the engine raises only on its own, with a message that points at a full disk ('may be due to the database disk being full'). The server sends no error labels at all (`TransientTransactionError`, `UnknownTransactionCommitResult`, `RetryableWriteError`; engine issue documentdb/documentdb#339); the helpers still check them because drivers attach `UnknownTransactionCommitResult` themselves to their own network errors on commit. Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys). With `retrywrites=false` the driver does not retry writes for you; retry a write through this helper only if it is idempotent (upsert on a stable key, `$setOnInsert`, client-supplied `_id`). For multi-document work use `with_transaction` / `withTransaction` inside `retry_transaction` / `retryTransaction` below: because the server sends no labels, `withTransaction` does not retry a `WriteConflict` (112) or `NoSuchTransaction` (251) for you, and those two codes mean 're-run the whole transaction', not 'repeat the statement', so they are deliberately not in `is_transient` (see `driver/driver-transactions-session.md`). Capacity is vCore tiers, not request units: sustained overload is fixed by scaling the tier (or adding shards), not by backing off. 429 + `Retry-After` comes from Azure OpenAI and other HTTP APIs, never from the database; use the SDK's `maxRetries` or honor the header there."

```python
# retry_util.py  (stdlib; tenacity is an acceptable drop-in)
import random, time
from pymongo.errors import (AutoReconnect, ConnectionFailure, NetworkTimeout,
    ServerSelectionTimeoutError, OperationFailure, PyMongoError, BulkWriteError)

TRANSIENT_CODES = {6, 50, 91}       # HostUnreachable, ExceededTimeLimit (also a maxTimeMS expiry), ShutdownInProgress
TXN_RETRY_CODES = {112, 251}        # WriteConflict, NoSuchTransaction: re-run the whole transaction (retry_transaction)
# Never retried: 11000 DuplicateKey, 20 IllegalOperation (replica/demoted cluster), 261 TooManyLogicalSessions,
# 263 OperationNotSupportedInTransaction. 16500/429 (RU throttling) and 189 do not exist on this service.

def is_transient(e):
    if isinstance(e, (AutoReconnect, ConnectionFailure, NetworkTimeout, ServerSelectionTimeoutError)):
        return True
    # The server sends no labels (documentdb/documentdb#339); drivers attach these to their own network errors.
    if isinstance(e, PyMongoError) and any(e.has_error_label(l) for l in
            ("TransientTransactionError", "UnknownTransactionCommitResult", "RetryableWriteError")):
        return True
    return isinstance(e, OperationFailure) and e.code in TRANSIENT_CODES

def _sleep(i, base=0.2, cap=5.0):
    time.sleep(min(cap, base * 2 ** i) * random.uniform(0.5, 1.0))

def with_retry(fn, *, attempts=5, base=0.2, cap=5.0):
    """Wrap only idempotent work."""
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            if i == attempts - 1 or not is_transient(e):
                raise
            _sleep(i, base, cap)

def retry_transaction(client, txn, *, attempts=3):
    """txn(session) runs inside with_transaction; it must be idempotent. Re-runs the whole
    transaction on WriteConflict/NoSuchTransaction, which arrive without a transient label."""
    for i in range(attempts):
        try:
            with client.start_session() as s:
                return s.with_transaction(txn)
        except OperationFailure as e:
            if i == attempts - 1 or e.code not in TXN_RETRY_CODES:
                raise
            _sleep(i)

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
const TRANSIENT_CODES = new Set([6, 50, 91]);   // HostUnreachable, ExceededTimeLimit (also maxTimeMS expiry), ShutdownInProgress
const TXN_RETRY_CODES = new Set([112, 251]);    // WriteConflict, NoSuchTransaction: re-run the whole transaction
// Never retried: 11000, 20 IllegalOperation, 261 TooManyLogicalSessions, 263. 16500/429 and 189 do not exist here.
const isTransient = (e) =>
  e instanceof MongoNetworkError || e instanceof MongoServerSelectionError ||
  // the server sends no labels (documentdb/documentdb#339); drivers attach these to their own network errors
  ["TransientTransactionError", "UnknownTransactionCommitResult", "RetryableWriteError"]
    .some((l) => e?.hasErrorLabel?.(l)) ||
  TRANSIENT_CODES.has(e?.code);
const sleep = (i, baseMs = 200, capMs = 5000) =>
  new Promise((r) => setTimeout(r, Math.min(capMs, baseMs * 2 ** i) * (0.5 + Math.random() / 2)));
async function withRetry(fn, { attempts = 5, baseMs = 200, capMs = 5000 } = {}) {
  for (let i = 0; ; i++) {
    try { return await fn(); }
    catch (e) {
      if (!isTransient(e) || i >= attempts - 1) throw e;
      await sleep(i, baseMs, capMs);
    }
  }
}
// txn(session) must be idempotent; withTransaction will not retry 112/251 on this service (no labels).
async function retryTransaction(client, txn, { attempts = 3 } = {}) {
  for (let i = 0; ; i++) {
    const session = client.startSession();
    try { return await session.withTransaction(() => txn(session)); }
    catch (e) {
      if (!TXN_RETRY_CODES.has(e?.code) || i >= attempts - 1) throw e;
      await sleep(i);
    } finally { await session.endSession(); }
  }
}
function partitionBulkErrors(err, ops) {   // MongoBulkWriteError, ordered:false only
  const dup = [], retry = [];
  for (const we of err.writeErrors ?? []) (we.code === 11000 ? dup : retry).push(ops[we.index]);
  return { dup, retry };
}
module.exports = { withRetry, retryTransaction, isTransient, partitionBulkErrors };
```

Rules (one line each): set `maxTimeMS` on interactive `find`/`aggregate` (the service default is 120 s) and `timeoutMS` on the client (Node driver 6.x / PyMongo 4.x); `bulkWrite` in batches of 500-1000 with `ordered: false` (service limit 25,000 writes per batch), partition errors, count duplicates, retry only the retryable subset, and never swallow batch errors; make seed/merge writes idempotent `updateOne(..., upsert: true)` keyed on a natural id with a unique index on that key; with `ordered: true` unattempted ops do not appear in `writeErrors`; cap LLM/embedding concurrency (`asyncio.Semaphore(4)` / `p-limit(4)`) and set `timeout=30` on those clients and 5-10 s on web-search tools; external tools (web search, LLM) may fall back to a deterministic mock after the last attempt so demos stay responsive, but never fall back silently on DB writes. Usage examples, about 10 lines each per language: one seed path (`bulkWrite` + partition + retry) and one query path (`aggregate` with `maxTimeMS` inside `with_retry`). Test: a fake raising `AutoReconnect` twice then succeeding is called 3 times; a duplicate-key `BulkWriteError` is partitioned and not retried; an `OperationFailure` with code 112 is not retried by `with_retry` but is re-run by `retry_transaction`.

### 3. `skills/connection/SKILL.md` (K07, K37, K21, K29)

Edits in file order:

- **"Python async note" blockquote (lines 45-49)** (K07 + K37): replace the existing date text with "Use PyMongo's `AsyncMongoClient` (generally available since PyMongo 4.13; the API first shipped as a beta in 4.9) with Beanie 2.x. Motor was deprecated on May 14, 2025 (end of life May 14, 2026; critical fixes only until May 14, 2027; source: MongoDB's Motor page and README; the PyMongo migration guide's 'deprecated on May 14th, 2026' is the outlier)." (DECISIONS.md, topic 4, items 4.5 and 4.7), then append K37's ODM lines:

  ```markdown
  > **ODMs:** Beanie 2.x accepts PyMongo's `AsyncMongoClient` directly (Beanie 2.0
  > dropped Motor). Do not pair Beanie with Motor and do not pin Beanie 1.x for
  > new code. Use Beanie 2.x with PyMongo 4.13+ (Beanie 2.0.0 itself requires
  > `pymongo>=4.11`; Learn's quickstart is tested with Beanie 2.2.0 and
  > PyMongo 4.19.0 on Python 3.13; Beanie 2.2.0 declares Python >=3.10,<3.14),
  > pinned exactly as in `documentdb-driver` →
  > `driver-reproducible-installs`, and initialise like this:
  >
  > ```python
  > from beanie import init_beanie
  > from db import get_async_client   # connection-client-factory.md
  > await init_beanie(database=get_async_client()[DB_NAME], document_models=[...])
  > ```
  > Use `Document.get_pymongo_collection()` (Beanie 2's replacement for
  > `get_motor_collection()`) for raw aggregations.
  > Reference: https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie
  ```

  Merge note: K37's text said "Pin `beanie>=2` and `pymongo>=4.9`" and built `AsyncMongoClient(os.environ["DOCUMENTDB_URI"])` inline. Both conflict with other parts of this PR (exact pins from K07/K29; no bare constructor from K07), so the merged text points at the factory and the pinning rule. The version floors are settled (see Resolved): 4.9 is the beta, 4.13 the GA release, 4.11 Beanie 2's own requirement.

- **New subsection under "Azure DocumentDB Connection Specifics", after "Authentication"** (K21):

  ```markdown
  ### Compatibility at a glance: what differs from MongoDB

  Azure DocumentDB speaks MongoDB wire protocol **5.0, 6.0, 7.0 or 8.0** (the
  cluster's `serverVersion`) and supports 99.03% of MongoDB query, projection,
  update and aggregation operators (Learn FAQ). Do **not** apply Azure Cosmos DB
  for MongoDB (RU) or Amazon DocumentDB limitations here; they are different
  services. There are no request units and no 16500/429 throttling codes.

  **Supported (use them):**
  - Multi-document ACID transactions across collections and across logical and
    physical shards (`startSession` → `withTransaction` or
    `commitTransaction`/`abortTransaction`). They are not partition-key scoped.
    Keep each transaction under the 30-second maximum lifetime. The server
    returns `WriteConflict` (112) and `NoSuchTransaction` (251) **without** the
    `TransientTransactionError` label, so `withTransaction` does not retry a
    conflict: re-run the transaction in application code. DDL and admin
    commands (`createIndexes`, `dropIndexes`, `drop`, `renameCollection`,
    `listCollections`, ...) are refused inside a transaction (code 263).
    See `documentdb-driver` → `driver-transactions-session`.
  - Change streams on single-shard clusters with no enablement step:
    `collection.watch()`, `resumeAfter`, `startAtOperationTime`, pre-images,
    resumable within the active 400 MB change log and, through historical
    replay, up to 35 days back. Preview: multi-shard change streams (enable per
    cluster under Settings > Features > "Change streams for multishard
    clusters"; cannot be enabled while "Rebalancer for multishard clusters" is
    on) and `updateDescription` (opt in per collection with
    `collMod ... enableUpdateDescription`).
  - All common aggregation stages (`$lookup`, `$facet`, `$graphLookup`,
    `$setWindowFields`, `$merge`, `$out`, `$unionWith`, ...).
  - Vector search via `cosmosSearch` (`vector-ivf`, `vector-hnsw`, `vector-diskann`);
    vectors must be `number[]`.
  - Full-text search via `createSearchIndexes` + `$search` (preview; enable it
    under Settings > Features > Full-text search and wait about ten minutes
    before creating a search index; `compound` with `must`/`should`/`mustNot`/
    `filter` works; see the documentdb-full-text-search skill).

  **Not available (do not generate):**
  - Server-side JavaScript: `$where`, `$function`, `$accumulator`, `mapReduce`.
  - Host-level admin/diagnostic commands: `serverStatus`, `top`, `connPoolStats`,
    `fsync`, `setFeatureCompatibilityVersion`, replication and shard-balancer
    commands (the service manages these).
  - The MongoDB 8.0 database-level `bulkWrite` *server command*; the driver's
    collection-level `bulkWrite()` / `insertMany()` helpers are fine
    (max 25,000 writes per batch).
  - Retryable writes (`retrywrites=false` is required) and the
    `TransientTransactionError` / `UnknownTransactionCommitResult` /
    `RetryableWriteError` labels: the server never sends them.
  - `readPreference` routing: `nearest`/`primaryPreferred`/`secondaryPreferred`
    are accepted and ignored, `secondary`, tag sets and hedged reads are
    rejected; reads always go to the primary shards. `writeConcern` and
    `readConcern` are validated and ignored (`w` above 1 other than
    `"majority"` is rejected); durability comes from the cluster's HA setting.
  - Atlas-only `$vectorSearch` (use `cosmosSearch`).
  - Time series, capped and clustered collections.

  Authoritative lists:
  https://learn.microsoft.com/azure/documentdb/compatibility-query-language ·
  https://learn.microsoft.com/azure/documentdb/compatibility-features ·
  https://learn.microsoft.com/azure/documentdb/faq ·
  https://learn.microsoft.com/azure/documentdb/how-to-transactions ·
  https://learn.microsoft.com/azure/documentdb/partitioning (cross-shard transactions) ·
  https://learn.microsoft.com/azure/documentdb/change-streams ·
  https://learn.microsoft.com/azure/documentdb/full-text-search-overview ·
  https://learn.microsoft.com/azure/documentdb/limitations ·
  https://github.com/documentdb/documentdb/issues/339 (no transient labels)
  ```

  (The cross-link to `driver-transactions-session` in the transactions bullet is added by the merge.) The three claims this block used to hedge are settled in DECISIONS.md and stated above as fact: transactions span logical and physical shards with the same 30-second limit (partitioning page, compare-mongodb-atlas; topic 9); multi-shard change streams are enabled per cluster under Features and cannot coexist with the rebalancer, the active log is 400 MB and historical replay reaches 35 days (change-streams page; topic 8); full-text search, multi-shard change streams and `updateDescription` are preview, single-shard change streams carry no preview label (full-text-search-overview, change-streams page; topics 7 and 8). The error code for a resume token that can no longer be resumed and the non-portal `previewFeatures` string for multi-shard change streams remain open in DECISIONS.md but are not needed by this block; they belong to the change-streams skill filing.

- **Singleton example (around line 158)** (K07): replace the bare constructor with `getClient()` from `connection-client-factory.md`.

- **Line 207** (K07, from DECISIONS.md topic 9): delete "Use `nearest` read preference for geo-distributed setups" and replace it with "Leave `readPreference` at its default. The gateway accepts and ignores `nearest`, `primaryPreferred` and `secondaryPreferred`, rejects `secondary`, tag sets and hedged reads (`FailedToSatisfyReadPreference` / `BadValue`), and standby shards never serve reads. For read-heavy clients in another region, connect to the replica cluster's own connection string."

- **"Retry Logic" (lines 209-241)** (K07): delete "Azure DocumentDB supports retryable reads" (no Learn page says so) and "for transient errors (network blips, failovers), the driver will automatically retry" (the server sends no `RetryableWriteError` label and `retrywrites=false` is required, so drivers never retry writes); replace the `withRetry` block with the `retry.js` above, keep `retryReads: true` as a harmless driver default without the support claim, and add: "Azure DocumentDB capacity is vCore tiers, not request units; the service never returns 16500 or 429. Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys). Wrap idempotent writes in the helper. Retry on network and server-selection errors and on codes 6, 50 and 91, the errors a failover can surface after the gateway's own internal retry (Learn's reliability page: in-flight requests 'can fail and must be retried by the client'); re-run whole transactions on 112/251 with `retryTransaction`. See `connection-retry-helpers.md` for bulk-write partitioning and timeouts."

- **"When Creating Code" (around line 260)** (K07 + K29), add two lines:
  - "If you are generating a sample, quickstart or CLI and no user is available to answer, do not block on questions: use `connection-client-factory.md` and comment the defaults."
  - "Pin the driver version you verified against; see `documentdb-driver` → `driver-reproducible-installs`."

- Not in this PR: draft 120's cross-link line "Python example: see `documentdb-driver` → `driver-python-connect`" belongs in the Authentication section that K03 rewrites; add it there.

### 4. New `skills/driver/driver-python-connect.md` (K16)

````markdown
# driver-python-connect

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB (resource type `Microsoft.DocumentDB/mongoClusters`) always requires TLS. Native users authenticate with SCRAM-SHA-256. The connection string from the portal (Cluster > Settings > Connection strings) uses the `mongodb+srv` scheme, a host ending in `.mongocluster.cosmos.azure.com`, and these query options:

| Option | Value |
|---|---|
| `tls` | `true` |
| `authMechanism` | `SCRAM-SHA-256` (native users; for Microsoft Entra ID see the `documentdb-connection` skill, Authentication section) |
| `retrywrites` | `false` (required; the service does not support retryable writes, see below) |
| `maxIdleTimeMS` | `120000` |

The portal string leaves out the password, so fill in the placeholder yourself. Legacy Azure Cosmos DB for MongoDB (RU) strings (`*.mongo.cosmos.azure.com`, port 10255, `replicaSet=globaldb`) belong to a different service and will not connect.

Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys). Learn's connection strings carry `retrywrites=false` but do not yet explain why; the reason above is the one to repeat.

If an option is set in both the URI and a PyMongo keyword argument, the keyword argument wins. Keep the two consistent.

## Correct

```python
import os
from pymongo import MongoClient

# Portal connection string with the password filled in, read from the
# environment or a secret store. Never commit it.
uri = os.environ["DOCUMENTDB_URI"]

client = MongoClient(
    uri,
    tls=True,                       # TLS is always required
    retryWrites=False,              # required: retryable writes are not supported
    maxIdleTimeMS=120000,           # matches the published connection string
    serverSelectionTimeoutMS=5000,  # fail fast instead of waiting 30 s
)
client.admin.command("ping")        # raises on a bad host, bad credentials, a firewall block or a TLS error
```

Create this client once per process (see `driver-singleton-client`). `AsyncMongoClient` takes the same keyword arguments. For pool sizes, timeouts from env, serverless defaults and a shutdown hook, use the `get_client()` factory in `documentdb-connection` → `connection-client-factory`.

## Incorrect

```python
client = MongoClient(os.environ["DOCUMENTDB_URI"])           # works only if the URI carries every option
client = MongoClient(uri, retryWrites=True)                  # retryable writes are not supported; a retried write can be applied twice
client = MongoClient(uri, tlsAllowInvalidCertificates=True)  # local emulator only, never the managed service
```

## References

- [Quickstart: Python driver — Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python)
- [Connect using role-based access control and Microsoft Entra ID](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control)
````

(The sentence pointing to `connection-client-factory` is added by the merge so the two Python snippets do not read as competing guidance.)

### 5. New `skills/driver/driver-transactions-session.md` (K15)

````markdown
# driver-transactions-session

**Category:** Driver Best Practices · **Priority:** HIGH

## Why it matters

Azure DocumentDB supports multi-document transactions through the standard
driver session API, across collections and across logical and physical shards
(they are not partition-key scoped). Five things agents often miss: the session
must be passed to **every** operation, or that write silently lands outside the
transaction; the service enforces a **30-second maximum transaction lifetime**
(same limit on sharded clusters); the server returns `WriteConflict` (112) and
`NoSuchTransaction` (251) **without** the `TransientTransactionError` label
(engine issue documentdb/documentdb#339, reproduced against the managed
service), so `withTransaction()` does **not** retry a conflict for you and the
application must re-run the whole transaction with a bounded, idempotent retry
(the callback must also be idempotent because drivers may still re-run it for
their own network errors on commit); DDL and admin commands (`createIndexes`,
`createSearchIndexes`, `dropIndexes`, `drop`, `renameCollection`,
`listCollections`, ...) are refused inside a transaction with code 263, so
create indexes before the transaction; and `readConcern`, `writeConcern` and
`readPreference` are validated and ignored by the gateway (durability comes from
the cluster's HA setting), so omit them from transaction options.

## Incorrect

```javascript
const session = await mongoose.startSession();
await session.withTransaction(async () => {
  await Transaction.create({ ...entry });                 // WRONG: no session, outside the txn
  await Account.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  await heavyReport.aggregate([...]).session(session);    // WRONG: long work risks the 30 s lifetime
});
```

## Correct (Mongoose)

```javascript
const session = await mongoose.startSession();
try {
  await session.withTransaction(async () => {
    // Model.create accepts options only in array form
    await Transaction.create([{ ...entry }], { session });
    await Account.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  });
} finally {
  await session.endSession();
}
```

## Correct (Node driver)

```javascript
const session = client.startSession();
try {
  await session.withTransaction(async () => {
    await ledger.insertOne(entry, { session });
    await accounts.updateOne({ _id }, { $inc: { balance: -amt } }, { session });
  });
} finally {
  await session.endSession();
}
```

## Correct (PyMongo)

```python
def txn(s):
    ledger.insert_one(entry, session=s)
    accounts.update_one({"_id": _id}, {"$inc": {"balance": -amt}}, session=s)

retry_transaction(client, txn)   # connection-retry-helpers.md: with_transaction inside a bounded 112/251 retry
```

Wrap the Node and Mongoose variants the same way with `retryTransaction(client, (session) => ...)`
from `connection-retry-helpers.md`; `withTransaction` alone surfaces the first write conflict
to the application.

Rules of thumb:
- Keep the transaction to a few documents and no aggregation; do reads and
  external calls (LLM, HTTP) before `withTransaction`, not inside it.
- Make the callback idempotent (for example a unique `idempotencyKey` index and
  `$setOnInsert`), because it will be re-run on a conflict and the driver may
  also re-run it for its own network errors on commit.
- Retry the **whole transaction** on codes 112 and 251, with a bounded attempt
  count and backoff; the general `isTransient` helper in `documentdb-connection`
  → `connection-retry-helpers` deliberately excludes those two codes because
  they mean "re-run the transaction", not "repeat the statement".
- Expect the server to abort a transaction that passes 30 seconds; later
  statements and the commit then fail (the exact code is undocumented).

## References

- https://learn.microsoft.com/azure/documentdb/how-to-transactions
- https://learn.microsoft.com/azure/documentdb/partitioning (transactions across logical and physical shards)
- https://learn.microsoft.com/azure/documentdb/limitations#mongodb-execution-limitations (30 s lifetime)
- https://github.com/documentdb/documentdb/issues/339 (no `TransientTransactionError` label)
- https://learn.microsoft.com/azure/documentdb/tutorial-nodejs-mongoose#mongoose-on-azure-documentdb
````

(The references to `connection-retry-helpers` are added by the merge.) The cross-shard claim is settled (partitioning page: transactions apply "across multiple logical shards and across multiple physical shards"; see Resolved) and is now stated in the rule. The retryWrites rationale is settled (see Resolved) and is carried by `connection-client-factory.md`, `connection-retry-helpers.md`, the connection `SKILL.md` Retry Logic edit and `driver-python-connect.md`, so this rule does not repeat it. The DDL list is given as a category with examples rather than an exact list because the gateway's `main` branch and `release/1.0-RC2` differ on it (DECISIONS.md, topic 9).

### 6. New `skills/driver/driver-reproducible-installs.md` (K29, plus K07's Learn supported-drivers check)

~~~markdown
# driver-reproducible-installs — Resolve versions from the registry, then lock them

## Why it matters
A sample that installs differently tomorrow than it did when it was verified is not a sample. Driver
versions also gate features (for example PyMongo 4.13 for the GA `AsyncMongoClient`, PyMongo 4.7 /
`mongodb` 6.7.0 for MONGODB-OIDC), so an unpinned driver can silently change what works against
Azure DocumentDB. Never write a version you remember; look it up.

## Rules
1. **Resolve before you write.** Before adding a dependency, query the registry and use a version it
   returns: `npm view <pkg> version` / `npm view <pkg> versions --json`, or
   `pip index versions <pkg>` (pip >= 21.2). Never copy a version from memory or an old tutorial;
   if the lookup fails, say so instead of guessing. For the MongoDB driver itself, use the current
   stable release; Learn publishes no tested-driver table (the FAQ says any wire-protocol driver
   connects), so treat MongoDB's compatibility table as the floor: the row marked fully compatible
   for server 5.0 to 8.0 (PyMongo 4.9, `mongodb` 6.9, `mongoose` 8.7, Java 5.2, .NET 2.29, Go 2.1,
   Rust 3.1). On Node 24 use `mongodb` 7.x (requires Node >= 20.19.0); MongoDB marks 6.x untested
   on Node 24.
2. **Node samples** commit `package-lock.json`, use exact versions (no `^`/`~`) for the client and
   ODM (`mongodb`, `mongoose`), and tell users to run `npm ci`, not `npm install`. CI runs `npm ci`
   too, so an out-of-date lockfile fails fast.
3. **Python samples** ship an exact-pinned `requirements.txt` (or `requirements.in` +
   `pip-compile`d `requirements.txt`) matching the interpreter used for verification, and the
   README carries one line: `Tested on Python 3.12 / pip 24.x`. Never add `motor`.
4. **Ranges are for libraries, not samples.** A `>=` floor is acceptable only in a package others
   depend on. A runnable sample pins everything it imports.
5. **Updating pins is a deliberate step.** Re-run the resolve step, regenerate the lockfile, re-run
   the sample's seed/verify, then commit the new pins with a CHANGELOG line.

## Incorrect
```json
"devDependencies": { "supertest": "^6.4.3" }     // version never existed; npm install -> ETARGET
```
```text
pymongo>=4.5          # floats; a future major could change behaviour under the sample
langchain             # resolves to whatever is newest today
```
README: `npm install`

## Correct
```bash
npm view mongodb version          # use the value printed
npm install --save-exact mongodb@<printed-version>
npm ci                            # what the README and CI run
```
```bash
python -m pip install pip-tools
pip index versions pymongo        # confirm the version exists before pinning
pip-compile requirements.in       # produces exact-pinned requirements.txt
python -m pip install -r requirements.txt
```
README: `Tested on Python 3.12 / pip 24.3 — regenerate pins with pip-compile requirements.in`

## Tested stacks (fill from CI; keep this table short)
| Language | Client / ODM | Verified version | Notes |
|---|---|---|---|
| Node.js | `mongodb` | 6.20.0 (as pinned in `compat/package.json`) on Node <= 22; <fill> for 7.x on Node 24 | MongoDB marks 6.x untested on Node 24; 7.x requires Node >= 20.19.0 |
| Node.js | `mongoose` | <fill> (8.7 or later for server 8.0) | wraps `mongodb` above |
| Python  | `pymongo` (sync `MongoClient`) | <fill> | |
| Python  | `pymongo` (`AsyncMongoClient`) | GA from 4.13 (beta in 4.9); verified <fill> | preferred async client; Learn's Beanie quickstart is tested with 4.19.0 (requires Python >= 3.11) |
| Python  | `beanie` 2.x | <fill> (Learn: 2.2.0 with PyMongo 4.19.0 on Python 3.13) | uses PyMongo's async client; Beanie 2.0.0 declares `pymongo>=4.11,<5` and no Motor dependency; 2.2.0 declares Python >=3.10,<3.14 |
| Python  | `beanie` 1.x + `motor` | not recommended | Motor is deprecated (see `documentdb-connection`); Beanie 1 + Motor stacks failed in the experiment with `MotorDatabase object is not callable` and `cannot import name '_QUERY_OPTIONS'` |

## References
- npm: `npm ci`, `npm view`
- pip-tools `pip-compile`; `pip index versions`
- `skills/connection/SKILL.md` (Python async note)
~~~

Maintainers should replace each `<fill>` with versions actually exercised by `evals/` and `testing/`, so the table states fact (open question 4, a maintainer item). The driver version floors in this rule are settled from primary sources (see Resolved): `AsyncMongoClient` is beta in PyMongo 4.9 and GA in 4.13; Beanie 2.0.0 requires `pymongo>=4.11.0,<5.0.0` and no Motor (PyPI metadata); Learn's Beanie quickstart and tutorial are tested with Beanie 2.2.0 and PyMongo 4.19.0. Whether Microsoft keeps DocumentDB-specific tested floors beyond MongoDB's wire-protocol table is open question 3. (Merge note: the compatibility-table check in rule 1 and "Never add `motor`" in rule 3 come from K07's dependency rules; the original "Learn's supported-drivers page" wording is dropped because no such page exists.)

### 7. `skills/driver/SKILL.md` (K21, K37, K07, K16, K15, K29)

- **Front-matter `description`**: extend with "multi-document transactions with sessions (Mongoose, Node, Python); dependency pinning and lockfiles for samples; PyMongo connection example" (K15 + K29 + K16).
- **Under the intro paragraph** (not in the Rules list) (K21):

  ```markdown
  Before avoiding a MongoDB feature, check "Compatibility at a glance" in the documentdb-connection skill; multi-document transactions and change streams are supported.
  ```

- **`## Rules` list**: after `driver-singleton-client`, add (K16, K15, K29):

  ```markdown
  - [driver-python-connect](driver-python-connect.md) — Connect from PyMongo with explicit `tls=True`, `retryWrites=False` and `maxIdleTimeMS`, and verify the connection with `ping` at startup.
  - [driver-transactions-session](driver-transactions-session.md) — Multi-document transactions (across collections and shards): `startSession()` + `withTransaction()`, pass `{ session }` to every operation, stay under the 30 s lifetime, re-run the whole transaction yourself on `WriteConflict` (112) / `NoSuchTransaction` (251) because the server sends no `TransientTransactionError` label, no DDL inside (code 263).
  - [driver-reproducible-installs](driver-reproducible-installs.md) — Resolve dependency versions from the registry (never from memory), commit lockfiles, `npm ci` / exact-pinned `requirements.txt`, tested-stack matrix.
  ```

- **Below the Rules list** (K07 + K37):

  ```markdown
  - Construct the client through one `get_client()` factory (tls, retryWrites=false, timeouts, pool, shutdown hook); never bare `MongoClient(uri)`: see `connection/connection-client-factory.md`.
  - Wrap idempotent DB calls in the bounded backoff helper in `connection/connection-retry-helpers.md`; Azure DocumentDB never returns 16500/429 (no request units), and the server sends no transient-error labels, so re-run transactions on 112/251 yourself.

  Python async / Beanie: use `AsyncMongoClient` (GA in PyMongo 4.13) and Beanie 2, never Motor. See the Python async note in `documentdb-connection`.
  ```

  Draft 096 proposed the first two as separate rule files (`driver-client-factory.md`, `driver-retry-transient.md`); bullets pointing to the connection files avoid duplicating the code, and maintainers can ask for the rule files instead.

### 8. `skills/natural-language-querying/SKILL.md` (K21)

- Line 258: "supports multi-document transactions" → "supports multi-document transactions across collections and shards (30-second maximum lifetime); change streams are also supported".
- Line 261: `.../azure/documentdb/compatibility` → `.../azure/documentdb/compatibility-query-language`.

### 9. `skills/data-modeling/` (K21)

- `model-embed-vs-reference.md:7`: "Cosmos DB for MongoDB vCore" → "Azure DocumentDB"; line 49: link → `https://learn.microsoft.com/azure/documentdb/` (or the specific page maintainers prefer).
- `model-16mb-limit.md:7`: same rename; line 45: link → `https://learn.microsoft.com/azure/documentdb/limitations` (states the 16 MB BSON limit).
- `model-denormalize-reads.md:39`: link → `https://learn.microsoft.com/azure/documentdb/`.

### 10. `compat/QUICKSTART.md` (K21)

- Line 103: `.../azure/documentdb/compatibility` → `.../azure/documentdb/compatibility-query-language`.

### 11. `skills/azure-deployment/SKILL.md` (K15)

One note after the intro paragraph:

```markdown
> Azure DocumentDB clusters are **`Microsoft.DocumentDB/mongoClusters`** (CLI: `az documentdb mongocluster`, `documentdb` extension, Azure CLI 2.75.0 or later). Do not generate `Microsoft.DocumentDB/databaseAccounts` templates or `az cosmosdb create` / `az cosmosdb mongodb` commands; those create Azure Cosmos DB (including the RU-based MongoDB API), a different service. The legacy preview group `az cosmosdb mongocluster` targets the same `mongoClusters` resource and is not deprecated, but it is superseded: every Learn page uses `az documentdb mongocluster`, and the legacy group lacks `list-connection-strings`, `replica` and the Entra ID commands. The checked-in `examples/azure-deployment/main.bicep` is the correct resource.
```

### 12. `docs/SKILLS.md` (K15)

Change the `driver/` row from "singleton client, pooling" to "singleton client, pooling, transactions, Python connect, reproducible installs".

### 13. `CHANGELOG.md` (K07 + K29 + others)

One entry: "Added `connection-client-factory` and `connection-retry-helpers` (replacing the RU-era Retry Logic snippet; Azure DocumentDB never returns 16500/429 and sends no transient-error labels), `driver-python-connect`, `driver-transactions-session` (application-level retry on 112/251, 30 s lifetime, cross-shard support, DDL refused with 263) and `driver-reproducible-installs` (registry-resolved versions, lockfile + `npm ci`, pinned `requirements.txt`, tested-stack matrix); added a 'Compatibility at a glance' block, corrected Motor dates and the `AsyncMongoClient` GA floor (PyMongo 4.13), Beanie 2.x guidance and the read-preference line in the connection skill; fixed compatibility links and Cosmos DB vCore naming in natural-language-querying, data-modeling and compat."

### 14. `CONTRIBUTING.md` (optional, K07 and K29)

Lines 8 and 14-15 still point at `skills/documentdb-best-practices/rules/`, a path that no longer exists; update them to the current `skills/<category>/<prefix>-<slug>.md` layout, which the new rule files follow.

### Out of scope

- The `retryWrites=true` and host-suffix line fixes (K01); the Node Entra/OIDC snippet and the PyMongo MONGODB-OIDC example with its evidence (K03 / the Entra PR).
- A PII-redaction rule for sample apps that send data to LLMs (a sample-gallery convention, not a DocumentDB skill), and the discoverability of the existing Bicep example (only 2 of 100 runs opened it), which deserves its own issue (K15).
- Follow-up for the harness owner (coordinate first): once the helpers ship, the sample-prompt build contract can add "all DB access goes through the kit's `get_client()` factory and transient-error retry helper" (K07).
- Learn needs no change for Beanie: the Beanie tutorial (ms.date 2026-11-16) and quickstart both say "This example uses Beanie 2 and PyMongo's asynchronous client, not Motor" and pin `beanie==2.2.0 pymongo==4.19.0`; the "initialise Beanie with an AsyncIOMotorClient" practice one audit traced to `tutorial-python-beanie#prerequisites` is no longer on the page (DECISIONS.md, topic 4, item 4.6) (K37).

## Evidence

Run folders in the experiment harness (`runs/`):

- `runs/01-anti-money-laundering-pattern-detector/20261124-200112`: bare `MongoClient(uri)` in `app/aml_agent/db.py`; audit's retry check cites a Cosmos DB RU page (K07).
- `runs/07-customer-review-sentiment-pipeline/20261125-054042`: Beanie 1 / Motor / Pydantic 1 pins, new client per `init_db()`, no shutdown (K07).
- `runs/02-ai-powered-product-recommendations/20261124-181835`: `app/src/seed.js` swallows `insertMany` errors (K07).
- `runs/02-real-time-event-stream-ingestion/20261124-203233`: `bulkWrite` errors only logged, never partitioned (K07).
- `runs/07-lab-results-aggregator/20261124-194018`: `Duplicate URI option 'retryWrites'` from string-appending (K07).
- `runs/18-returns-refund-workflow-orchestration/20261124-185415`: Azure OpenAI calls with no timeout or backoff (K07).
- `runs/16-subscription-billing-engine/20261124-192251/02-readiness.json`: confusion Q10, assumes cross-partition transactions unavailable; build risk "over-constrain its schema" (K21).
- `runs/07-lab-results-aggregator/20261124-194018/02-readiness.json`: confusion Q10, "no support for multi-shard distributed transactions and MongoDB change streams"; the build later used `coll.watch()` successfully (K21).
- `runs/20-interest-accrual-batch-processor/20261124-202826/02-readiness.json`: confusion Q10, transactions spanning partition keys "may not be supported" (K21).
- `runs/06-symptom-triage-chatbot-rag/20261124-193845/02-readiness.json`: confusion Q10, confused with Cosmos DB for MongoDB RU (K21).
- `runs/01-unified-customer-profile-store/20261124-203120/02-readiness.json`: confusion Q10, aggregation stages and transaction semantics "may be restricted" (K21).
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049`: `02-readiness.json` (Q07), `app/src/db.py` Motor singleton, `app/scripts/run_aggregations.py` calls `get_motor_collection()`, `app/requirements.txt` pins neither Motor nor Beanie (K37).
- `runs/17-ai-survey-response-analyzer/20261124-205518`: `02-readiness.json` (Q07), `app/requirements.txt` (`beanie==1.24.0`, `motor==3.1.1`), `05-audit.json` (K37, K29).
- `runs/09-clinical-notes-de-identification/20261124-194349`: `02-readiness.json` (Q07), `app/requirements.txt`, `05-audit.json` ("Driver version choice": violated) (K37).
- `runs/20-identity-resolution-multi-agent/20261124-210002/events.jsonl` and `runs/11-preference-center-consent-store/20261125-064954/events.jsonl`: Beanie 1.x + Motor stacks failed with `MotorDatabase object is not callable`; `runs/07-customer-review-sentiment-pipeline/20261125-054042` and `runs/11-preference-center-consent-store/20261124-204614`: old Motor/Beanie against current PyMongo failed with `cannot import name '_QUERY_OPTIONS' from 'pymongo.cursor'` (DECISIONS.md, topic 4, item 4.6) (K37, K29).
- `runs/03-core-banking-transaction-ledger/20261124-200452/05-audit.json` and `runs/05-appointment-scheduling-assistant/20261124-193733/05-audit.json`: `withTransaction` ran against the live single-shard cluster; both audits flag "no automated retry logic for transient transaction errors", which on this service must be application code (DECISIONS.md, topic 9) (K15).
- `runs/16-atm-network-status-monitor/20261124-202405/events.jsonl`: two `npm install` `ETARGET` failures for `supertest`; build halted (K29).
- `runs/06-order-history-timeline-agent/20261124-183612/decisions.jsonl`: D009/D010, nonexistent `pymongo`/`langchain` pins relaxed to `>=` ranges (K29).
- `runs/04-natural-language-product-search/20261124-183232/app/requirements.txt`: nine dependencies, zero pins (K29).
- `runs/02-transaction-categorization-agent/20261124-190028/app/package.json`: caret ranges beside a committed `package-lock.json`; README says `npm install` (K29).
- `runs/07-multi-currency-ledger/20261124-190814/05-audit.json`: transaction practice classified as prior knowledge only; no DocumentDB Mongoose recipe found (K15).
- `runs/07-multi-currency-ledger/20261124-190814/02-readiness.json`: transaction lifetime unknown to the agent (K15).
- `runs/03-core-banking-transaction-ledger/20261124-200452/doc-gaps.md`: Mongoose sessions, transaction retry semantics (K15).
- `runs/16-multi-touch-attribution-model/20261124-205342/doc-gaps.md`: transactions vs single-document updates (K15).
- `runs/03-next-best-action-multi-agent/20261124-203319/doc-gaps.md`: IaC example requested although the kit ships one (K15).
- `runs/10-wealth-management-rag-portal/20261124-201449/doc-gaps.md`: PII-redaction rule request; out of scope (K15).
- `runs/19-care-coordination-multi-agent/20261124-195730/doc-gaps.md`: "[high] Explicit PyMongo connection examples for mongoClusters"; `05-audit.json` `doc_gaps[0]`; `app/app/db.py` line 27 is a bare `MongoClient(DOCUMENTDB_URI)`; `05a-practice-discovery.md` practice P02 (enforce TLS) found only in the Learn quickstart, not in the kit (K16).

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- 16500 / 429 throttling (was open question 1): Azure DocumentDB never returns them; 16500 is a request-unit error of the RU-based Cosmos DB for MongoDB, the vCore service has no request units, neither code is in any engine error-mapping file or on Learn's troubleshooting table, and no run observed one; the helpers drop the legacy set. Sources: DECISIONS.md topic 2; learn.microsoft.com/azure/cosmos-db/mongodb/error-codes-solutions (RU page); learn.microsoft.com/azure/documentdb/troubleshoot-common-issues; documentdb/documentdb @ a5f1636 error_mappings.csv, documentdb_errors.csv, all_error_mappings_oss_generated.csv.
- Stepdown codes 10107 / 189 (the settled half of old open question 2): 189 `PrimarySteppedDown` does not exist in any engine mapping and 10107 `NotWritablePrimary` is raised only by the engine itself, with a hedged message that points at a full disk ('may be due to the database disk being full'); the codes the open-source gateway can surface after its own internal retry are 6 `HostUnreachable`, 91 `ShutdownInProgress` and 50 `ExceededTimeLimit`, none with a `RetryableWriteError` label, and Learn puts retry on the application. Sources: DECISIONS.md topic 2; documentdb/documentdb @ a5f1636 all_error_mappings_oss_generated.csv, error.rs:518-575, pg.rs:197-205 and 455-470, query_dispatch.rs:75-143; learn.microsoft.com/azure/reliability/reliability-documentdb; learn.microsoft.com/azure/documentdb/high-availability.
- `AsyncMongoClient` and Beanie version floors (the settled half of old open question 4): the async API is beta in PyMongo 4.9 and GA in 4.13; Beanie 2.0.0 requires `pymongo>=4.11.0,<5.0.0` with no Motor dependency; Learn's Beanie quickstart and tutorial are tested with Beanie 2.2.0 and PyMongo 4.19.0 (Python 3.13; Beanie 2.2.0 declares Python >=3.10,<3.14). Sources: DECISIONS.md topic 4, items 4.5 and 4.6; mongodb.com PyMongo release notes (4.9, 4.13); pypi.org/pypi/beanie/2.0.0 and 2.2.0; learn.microsoft.com/azure/documentdb/quickstart-python-beanie; learn.microsoft.com/azure/documentdb/tutorial-python-beanie.
- Beanie 2.x on PyMongo's async client as the recommended path, Beanie 1.x + Motor not recommended (was open question 5): the evidence supports exactly that pairing (Learn: "If your app uses Beanie 1 with Motor, stop and update the app to Beanie 2 and PyMongo's AsyncMongoClient"); Beanie 1 + Motor stacks failed in five experiment runs. Sources: DECISIONS.md topic 4, item 4.6; learn.microsoft.com/azure/documentdb/quickstart-python-beanie; beanie-odm.dev/changelog (2.0.0 "Motor -> async pymongo").
- Motor dates (was open question 6): deprecated May 14, 2025; end of life May 14, 2026; critical fixes only until May 14, 2027; the kit's "May 2024" and "through May 2026" are wrong under every source; the PyMongo migration guide's "deprecated on May 14th, 2026" is the one-year outlier. Sources: DECISIONS.md topic 4, item 4.7; mongodb.com/docs/drivers/motor; github.com/mongodb/motor README; pypi.org/pypi/motor (3.7.1, 2025-05-14).
- Cross-shard transactions (was open question 8): supported across collections and across logical and physical shards, with the single 30-second lifetime stated without any shard qualifier (gateway default `TRANSACTION_TIMEOUT_DEFAULT_SEC = 30`). Sources: DECISIONS.md topic 9; learn.microsoft.com/azure/documentdb/partitioning (Logical shards); learn.microsoft.com/azure/documentdb/compare-mongodb-atlas; learn.microsoft.com/azure/documentdb/limitations; documentdb/documentdb dynamic.rs:26.
- Multi-shard change streams (was open question 9): enabled per cluster under Settings > Features > "Change streams for multishard clusters", cannot be enabled while "Rebalancer for multishard clusters" is on, single-shard clusters need no enablement step; the active change log is 400 MB and historical replay through PITR reaches up to 35 days or the cluster's creation. Sources: DECISIONS.md topic 8; learn.microsoft.com/azure/documentdb/change-streams; learn.microsoft.com/azure/documentdb/how-to-scale-cluster; learn.microsoft.com/azure/documentdb/how-to-restore-cluster.
- Preview labels (was open question 10): full-text search "remains in preview" (self-serve enablement under Features, wait ten minutes), multi-shard change streams and `updateDescription` are preview (the latter opt-in per collection via `collMod enableUpdateDescription`); single-shard change streams carry no preview label on Learn (GA announced on Microsoft DevBlogs 2025-05-21, supporting evidence only). Sources: DECISIONS.md topics 7 and 8; learn.microsoft.com/azure/documentdb/full-text-search-overview; learn.microsoft.com/azure/documentdb/change-streams.
- Transient-error labels (was open question 11): the gateway never writes an `errorLabels` field, so `TransientTransactionError`, `UnknownTransactionCommitResult` and `RetryableWriteError` are never sent; a write conflict arrives as code 112 with no label (issue #339, reproduced against the managed service) and `withTransaction` therefore does not retry it; the application must re-run the transaction on 112/251. Sources: DECISIONS.md topics 2 and 9; github.com/documentdb/documentdb/issues/339, /698, /428, /836; documentdb/documentdb @ a5f1636 responses/error.rs:64-71, pg.rs:245-258 and 297-315.

## Open questions

1. [needs SME confirmation] Which exact error code(s) and messages does a client receive for a write that fails during an in-region HA failover or a cross-region promotion on the managed service, and for how long? Learn describes the effect ("write slowness", "brief interruption", "can fail and must be retried") without a code; the open-source gateway's candidates are 6, 91 and 50, and 20 `IllegalOperation` for a write to a demoted or replica cluster. The helpers retry 6/50/91 and treat 20 as terminal until this is answered. (K07; DECISIONS.md topic 2, open items 1 and 2)
2. Pool defaults: draft 096 proposes 50/5 (long-running) and 30 s socket timeout; draft 089 proposed 20/0 and 60 s, with `DB_*` env-var names instead of `DOCUMENTDB_*`. This PR uses 096's values and names. Maintainers may prefer the other set. (K07)
3. [needs SME confirmation] Does Microsoft maintain Azure DocumentDB-specific tested driver floors per compatibility version (5.0 to 8.0), and has Node.js 24 been tested, with which `mongodb` line? No Learn page names a minimum or tested driver version; this PR uses MongoDB's fully-compatible rows as the floor and pairs Node 24 with `mongodb` 7.x. (K07, K29; DECISIONS.md topic 4, open items 4.8 and 4.9)
4. Which versions of `mongodb`, `mongoose`, `pymongo` and `beanie` has the kit's CI actually verified against Azure DocumentDB, so every `<fill>` cell in the tested-stack table is a tested fact, and should kit skills state driver minimums at all (DECISIONS.md topic 4, open item 4.11, a maintainer decision; this PR states floors only where a feature is gated and otherwise says "resolve current stable and pin exactly")? (K07, K37, K29)
5. Sample counts come from one experiment run with known harness artifacts; some Python install failures may be environment artifacts (for example interpreter-version issues) rather than pinning gaps. Recount after the harness re-run before quoting 85 (or any per-member figure) externally, and resolve the cross-member overlap, which the drafts' finding ids did not allow. (K07, K29, K37, K21)
6. [needs SME confirmation] Is there a plan or ETA to emit `TransientTransactionError` (and `RetryableWriteError` / `UnknownTransactionCommitResult`) labels in the gateway, so that drivers' `withTransaction` retry works as on MongoDB? Issue documentdb/documentdb#339 has been open since 2025-09-30 with no maintainer statement of intent; until then `driver-transactions-session` documents application-level retry on 112/251. (K15; DECISIONS.md topic 2, open item 4)
7. [needs SME confirmation] Should every client set `maxIdleTimeMS=120000`, or is 120000 only the portal default? The factory uses 120000 long-running and 30000 serverless; `driver-python-connect` uses 120000 to match the published string. DECISIONS.md does not cover this option. (K16)

## Source drafts

- 096-connection-skill-lacks-a-canonical-client-factory-and-transi.md (lead)
- 089-connection-defaults-for-samples-copy-paste-mongoclient-motor.md
- 090-reusable-retry-backoff-and-resilience-helpers-429-retry-afte.md
- 119-agent-kit-lacks-a-packaged-retry-backoff-helper-for-429-and-.md
- 027-believes-the-unsupported-feature-list-is-the-ru-api-generic-.md
- 135-believes-beanie-requires-motor-asynciomotorclient-and-that-m.md
- 088-reproducible-installs-dependency-pinning-lockfile-policy-and.md
- 095-misc-one-off-agent-kit-gaps-bicep-mongoclusters-example-mong.md
- 120-documentdb-driver-skill-lacks-an-authoritative-copy-paste-py.md

## Merged from

- K07: connection skill: per-language get_client() factory with vCore-correct transient-error retry and bulk-write partial-failure helpers (P1, 85 samples)
- K21: connection skill: add a 'What differs from MongoDB' compatibility block (P1, 24 samples)
- K37: connection skill: Beanie 2.x runs on AsyncMongoClient, not Motor (P2, 3 samples)
- K29: driver skill: add a reproducible-installs rule plus a tested-stack matrix (P1, 11 samples)
- K15: driver skill: add a transactions-with-sessions rule (Mongoose, Node, PyMongo) (P2, 3 samples)
- K16: driver skill: add a copy-paste PyMongo 'Connect to Azure DocumentDB' rule (P1, 1 sample)
