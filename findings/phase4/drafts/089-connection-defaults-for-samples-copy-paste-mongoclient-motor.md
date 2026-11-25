---
title: "connection: add copy-paste client defaults for samples; fix retryWrites=true in three skills; concrete Node Entra snippet"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 12
findings: 12
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# connection: add copy-paste client defaults for samples; fix `retryWrites=true` in three skills; concrete Node Entra snippet

## What happens today

An agent that builds a sample against Azure DocumentDB loads `documentdb-connection`, `documentdb-driver` and `documentdb-security`. Those skills explain pool sizing per scenario and why TLS matters, but:

1. **The kit shows the wrong `retryWrites` value in three places.** Learn documents `retrywrites=false` for every driver (see the connection-string table and code samples on [how-to-connect-role-based-access-control](https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control)). The kit says the opposite:
   - `skills/connection/SKILL.md:60` — connection string ends in `&retryWrites=true`
   - `skills/driver/driver-singleton-client.md:26` — `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })` (the "Correct" example)
   - `skills/security/security-tls-required.md:26` — `retryWrites: true` (the "Correct" example)
2. **No constructor snippet a sample can copy.** The singleton example at `skills/connection/SKILL.md:158` is `new MongoClient(process.env.DOCUMENTDB_URI)` with no options. The tuning tables (lines 91-148) give ranges, not a default, and "Configuration Design" / "When Creating Code" instruct the agent to ask the user targeted questions, one at a time, before choosing values. A sample builder has no user to ask, so it ships the driver defaults.
3. **No guidance on merging query options into a user-supplied URI.** Builders string-append `&retryWrites=false&tls=true` and trigger pymongo's `Duplicate URI option 'retryWrites'` warning when the env URI already carries it.
4. **The Entra example is a placeholder.** `skills/security/security-entra-rbac.md:23-29` reads `authMechanism: "MONGODB-OIDC", // or the current documented mechanism` with a commented-out credential provider. Learn has a complete Node/Python/C# sample (`OIDC_CALLBACK` + `DefaultAzureCredential`, scope `https://ossrdbms-aad.database.windows.net/.default`, `ALLOWED_HOSTS: ['*.azure.com']`).

The kit is not uniformly wrong: `skills/azure-deployment/SKILL.md:288-291` already shows `retrywrites=false&maxIdleTimeMS=120000`. But the connection, driver and security skills, which are the ones loaded when writing client code, contradict it.

## Why it matters

Across the 100-sample gpt-5-mini readiness run (DocumentDB Agent Kit + DocumentDB/Azure/Learn MCP):

- **12 samples'** audits raised this gap explicitly (02-clinical-trial-matching, 02-swift-message-parser, 04-medical-imaging-metadata, 05-kyc-document-ingestion, 07-lab-results-aggregator, 09-clinical-notes-de-identification, 12-abandoned-cart-recovery, 12-cross-border-payment-audit-trail, 12-invoice-matching, 14-customer-complaint-classifier, 17-stress-testing-runner, 20-identity-resolution).
- **18 runs** emitted code or a URI with `retryWrites: true` / `retryWrites=true`; 12-abandoned-cart's shipped `db.js` has it, and the audit traced it to the kit's own examples.
- **38 runs** never set `maxPoolSize`, `serverSelectionTimeoutMS`, `socketTimeoutMS` or `connectTimeoutMS` anywhere. 17-stress-testing's builder logged an intention to set `maxPoolSize` and then did not, because no snippet was nearby.
- **2 runs** (07-lab-results, 10-wealth-management-rag) logged pymongo `Duplicate URI option 'retryWrites'` from naive appends.
- **5 runs** asked for a Node Entra example; 12-cross-border's cold quiz also believed Entra auth was unsupported for the MongoDB API, and the builder fell back to SCRAM.

## Proposed change

### 1. New file `skills/connection/connection-sample-defaults.md`

Same `<prefix>-<slug>.md` shape as `driver-singleton-client.md`. Proposed content:

~~~markdown
# connection-sample-defaults

**Category:** Connection · **Priority:** HIGH

## Why it matters

When you generate a sample, CLI or quickstart and have no user to ask, use these defaults and comment them. They match the connection string Azure DocumentDB hands out (`tls=true`, `authMechanism=SCRAM-SHA-256`, `retrywrites=false`, `maxIdleTimeMS=120000`) and keep failures fast instead of hanging. Do not emit `retryWrites: true`.

## Defaults

| Option | Long-running / CLI | Serverless / short-lived | Env var |
|---|---|---|---|
| `retryWrites` | `false` | `false` | — (never override) |
| `tls` | `true` | `true` | — |
| `maxPoolSize` | 20 | 5 | `DB_MAX_POOL_SIZE` |
| `minPoolSize` | 0 | 0 | `DB_MIN_POOL_SIZE` |
| `maxIdleTimeMS` | 120000 | 30000 | `DB_MAX_IDLE_TIME_MS` |
| `serverSelectionTimeoutMS` | 5000 | 5000 | `DB_SERVER_SELECTION_TIMEOUT_MS` |
| `connectTimeoutMS` | 10000 | 10000 | `DB_CONNECT_TIMEOUT_MS` |
| `socketTimeoutMS` | 60000 | 30000 | `DB_SOCKET_TIMEOUT_MS` |

Create the client **once per process** (see `driver-singleton-client`). In serverless, create it at module scope so warm invocations reuse it.

## Python (PyMongo; for async use `pymongo.AsyncMongoClient` (added in 4.9, GA in 4.13) with the same kwargs. Motor is deprecated in favour of it, but `motor.motor_asyncio.AsyncIOMotorClient(uri, **client_options())` accepts the same options)

```python
import os
from pymongo import MongoClient, AsyncMongoClient

def client_options(serverless: bool = False) -> dict:
    return {
        "retryWrites": False,
        "tls": True,
        "maxPoolSize": int(os.getenv("DB_MAX_POOL_SIZE", 5 if serverless else 20)),
        "minPoolSize": int(os.getenv("DB_MIN_POOL_SIZE", 0)),
        "maxIdleTimeMS": int(os.getenv("DB_MAX_IDLE_TIME_MS", 30_000 if serverless else 120_000)),
        "serverSelectionTimeoutMS": int(os.getenv("DB_SERVER_SELECTION_TIMEOUT_MS", 5_000)),
        "connectTimeoutMS": int(os.getenv("DB_CONNECT_TIMEOUT_MS", 10_000)),
        "socketTimeoutMS": int(os.getenv("DB_SOCKET_TIMEOUT_MS", 30_000 if serverless else 60_000)),
    }

_client: MongoClient | None = None
def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(os.environ["DOCUMENTDB_URI"], **client_options())
    return _client

# async: AsyncMongoClient(os.environ["DOCUMENTDB_URI"], **client_options())
```

## Node.js (mongodb driver)

```javascript
const { MongoClient } = require("mongodb");

function clientOptions({ serverless = false } = {}) {
  const n = (k, d) => Number(process.env[k] ?? d);
  return {
    retryWrites: false,
    tls: true,
    maxPoolSize: n("DB_MAX_POOL_SIZE", serverless ? 5 : 20),
    minPoolSize: n("DB_MIN_POOL_SIZE", 0),
    maxIdleTimeMS: n("DB_MAX_IDLE_TIME_MS", serverless ? 30_000 : 120_000),
    serverSelectionTimeoutMS: n("DB_SERVER_SELECTION_TIMEOUT_MS", 5_000),
    connectTimeoutMS: n("DB_CONNECT_TIMEOUT_MS", 10_000),
    socketTimeoutMS: n("DB_SOCKET_TIMEOUT_MS", serverless ? 30_000 : 60_000),
  };
}

// module-level singleton; also correct for Azure Functions
const client = new MongoClient(process.env.DOCUMENTDB_URI, clientOptions());
const clientPromise = client.connect();
module.exports = { client, clientPromise };
```

## Mongoose

```javascript
const mongoose = require("mongoose");
await mongoose.connect(process.env.DOCUMENTDB_URI, {
  ...clientOptions(),            // same keys; Mongoose forwards them to the driver
  dbName: process.env.DB_NAME,
});
```

## Merging required URI options without duplicates

Prefer passing options to the constructor (above) and leaving the URI alone. If you must normalize a user-supplied URI, parse it; never string-append:

```python
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

REQUIRED = {"tls": "true", "retrywrites": "false", "maxIdleTimeMS": "120000"}

def normalize_uri(uri: str) -> str:
    parts = urlsplit(uri)                                   # mongodb:// and mongodb+srv://
    required = {k.lower() for k in REQUIRED}
    kept = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if k.lower() not in required]                   # URI options are case-insensitive
    kept += list(REQUIRED.items())                          # required values win, no duplicates
    return urlunsplit(parts._replace(query=urlencode(kept)))
```

```javascript
function normalizeUri(uri) {
  const u = new URL(uri);                                   // WHATWG URL handles mongodb+srv
  for (const [k, v] of Object.entries({ tls: "true", retrywrites: "false", maxIdleTimeMS: "120000" })) {
    for (const key of [...u.searchParams.keys()]) if (key.toLowerCase() === k.toLowerCase()) u.searchParams.delete(key);
    u.searchParams.set(k, v);
  }
  return u.toString();
}
```

## One-line test that options reach the driver

```python
def test_client_options(monkeypatch):
    monkeypatch.setenv("DOCUMENTDB_URI", "mongodb://localhost:27017/")
    assert get_client().options.retry_writes is False
```

```javascript
test("options reach the driver", () => {
  expect(new MongoClient("mongodb://localhost:27017/", clientOptions()).options.retryWrites).toBe(false);
});
```

## Microsoft Entra ID instead of a password (Node)

Requires the cluster to have Microsoft Entra ID enabled in its `authConfig` (allowed modes include `MicrosoftEntraID`) and the identity granted data-plane access (`az documentdb mongocluster microsoft-entra-user assign`). Token scope is `https://ossrdbms-aad.database.windows.net/.default`.

```javascript
const { MongoClient } = require("mongodb");
const { DefaultAzureCredential } = require("@azure/identity");

const credential = new DefaultAzureCredential();
const oidcCallback = async () => {
  const t = await credential.getToken(["https://ossrdbms-aad.database.windows.net/.default"]);
  return { accessToken: t.token, expiresInSeconds: Math.floor((t.expiresOnTimestamp - Date.now()) / 1000) };
};

const client = new MongoClient(`mongodb+srv://${process.env.DOCUMENTDB_CLUSTER}.global.mongocluster.cosmos.azure.com/`, {
  ...clientOptions(),
  authMechanism: "MONGODB-OIDC",
  authMechanismProperties: { OIDC_CALLBACK: oidcCallback, ALLOWED_HOSTS: ["*.azure.com"] },
});
// Mongoose: mongoose.connect(sameUri, sameOptions)
// Note: expiresOnTimestamp is in milliseconds; convert before subtracting from seconds.
```

## References

- https://learn.microsoft.com/azure/documentdb/how-to-connect-role-based-access-control (connection-string options table and OIDC code samples)
- https://learn.microsoft.com/azure/documentdb/quickstart-nodejs
~~~

### 2. `skills/connection/SKILL.md`

- Line 60: replace `&retryWrites=true` with `&retrywrites=false&maxIdleTimeMS=120000` so the example matches the portal string.
- Line 158: change the singleton example to `new MongoClient(process.env.DOCUMENTDB_URI, { retryWrites: false, tls: true, maxPoolSize: 20, serverSelectionTimeoutMS: 5000 })`.
- Under "When Creating Code" (line 260) add: "If you are generating a sample, quickstart or CLI and there is no user to ask, do not block on questions: apply [connection-sample-defaults](connection-sample-defaults.md), read overrides from the `DB_*` env vars it names, and comment the values."
- Under "Retry Logic" (line 209) add one sentence (this also makes the skill consistent with `skills/azure-deployment/SKILL.md:288-291`, which already shows `retrywrites=false`): "Azure DocumentDB's recommended connection string sets `retrywrites=false`; keep it that way and rely on application-level retries for writes."

### 3. `skills/driver/driver-singleton-client.md:26` and `skills/security/security-tls-required.md:26`

Change `retryWrites: true` to `retryWrites: false` in both "Correct" examples. In `skills/driver/SKILL.md` Rules list, add a pointer: "For the exact constructor options a sample should use, see `connection/connection-sample-defaults.md`."

### 4. `skills/security/security-entra-rbac.md` lines 22-30

Replace the placeholder block with the Node snippet from section 1 (and the Python `OIDCCallback` subclass from Learn). Remove the `// or the current documented mechanism` hedge; the mechanism is `MONGODB-OIDC`. Also fix the hostname in the "Incorrect" example on line 15 (`.mongocluster.documentdb.azure.com` is not the service host; it is `.mongocluster.cosmos.azure.com`).

### 5. `CHANGELOG.md`

Add an entry per CONTRIBUTING.md. (CONTRIBUTING.md still points at `skills/documentdb-best-practices/rules/`, which no longer exists; happy to update it to the current `skills/<category>/<prefix>-<slug>.md` layout in the same PR if wanted.)

## Evidence (run folders from the readiness experiment)

- `runs/12-abandoned-cart-recovery-orchestration/20261125-054042/doc-gaps.md` — shipped `db.js` has `retryWrites: true`; audit traces it to kit examples
- `runs/07-lab-results-aggregator/20261124-194018/events.jsonl` — pymongo `Duplicate URI option 'retryWrites'` from string-appending onto the env URI
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/doc-gaps.md` — builder planned `maxPoolSize`, never set it; asks for a long-running vs serverless snippet
- `runs/12-cross-border-payment-audit-trail/20261124-201744/02-readiness.json` — cold quiz believed Entra unsupported; `information_gaps` asks for a Node Entra example
- `runs/20-identity-resolution-multi-agent/20261124-210002/05-audit.json` — connection-options check: client created with no options, asks for `DB_MAX_POOL_SIZE` / `DB_SERVER_SELECTION_TIMEOUT_MS` helper and a passthrough test

## Verification

### 1. Already covered? partially_covered
- `skills/azure-deployment/SKILL.md:288-291` already shows the portal-style string with `retrywrites=false&maxIdleTimeMS=120000` and says to keep it false. That is the only correct place.
- These are wrong or missing, as the draft says: `skills/connection/SKILL.md:60` ends in `&retryWrites=true`. `skills/driver/driver-singleton-client.md:26` has `new MongoClient(uri, { maxPoolSize: 50, retryWrites: true })`. `skills/security/security-tls-required.md:26` has `retryWrites: true`. The singleton at `skills/connection/SKILL.md:157-159` is `new MongoClient(process.env.DOCUMENTDB_URI)` with no options. "When Creating Code" (line 260) says "If not, ask targeted questions first".
- `skills/security/security-entra-rbac.md:24-28` is a hedged placeholder: "or the current documented mechanism".
- No file in skills/ or knowledge-base/ has a sample-defaults snippet, a URI-merge helper or a Node OIDC callback.
- `CONTRIBUTING.md:8,14-15` still refers to `skills/documentdb-best-practices/rules/`.

### 2. Premise true? confirmed (small precision edits applied)
- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control (updated 2026-11-23). In the options table, `retrywrites` is `false` and `authMechanism` is `MONGODB-OIDC`. The sample URI is `...?tls=true&authMechanism=MONGODB-OIDC&retrywrites=false&maxIdleTimeMS=120000`.
- On the same page, the Node sample uses `getToken(['https://ossrdbms-aad.database.windows.net/.default'])`, `OIDC_CALLBACK` and `ALLOWED_HOSTS: ['*.azure.com']` on host `<cluster>.global.mongocluster.cosmos.azure.com`. The Python sample uses `OIDC_CALLBACK` and `retryWrites=False`. The CLI command is `az documentdb mongocluster microsoft-entra-user assign`. Entra must first be enabled via the cluster's `authConfig`.
- The service host is `*.mongocluster.cosmos.azure.com` (or `*.global.`), so `.mongocluster.documentdb.azure.com` in `security-entra-rbac.md:15` is wrong, as the draft says.
- Edits applied:
  - The AsyncMongoClient version note now says it was added in 4.9 and went GA in 4.13. Motor is deprecated but still accepts the same kwargs.
  - The Python URI helper now removes duplicates case-insensitively for every required key. Before, it did this only for tls and retrywrites, so `maxIdleTimeMS` could still be duplicated.
  - The Entra prerequisites now name `authConfig`.
  - Added a note that `expiresOnTimestamp` is in milliseconds. The Learn Node sample subtracts seconds from milliseconds.
  - Credited the existing azure-deployment coverage.

### 3. Maintainer skeptic: confirmed
The PR names exact files and lines, fixes three examples that are factually wrong and that agents copy, and adds one rule file in the existing `<prefix>-<slug>.md` layout with Azure DocumentDB-specific defaults (retrywrites=false, maxIdleTimeMS=120000, MONGODB-OIDC with the ossrdbms-aad scope). The fix belongs in Azure/documentdb-agent-kit. Pool and timeout numbers are opinionated defaults for samples, which reviewers may want to adjust, but they don't block the PR.

## Finding ids
- F0234
- F0299
- F0616
- F0812
- F1092
- F1967
- F2101
- F2035
- F1391
- F2348
- F2961
- F3379
