---
id: L01
title: "Add a driver and ODM compatibility page with tested versions and client options, linked from every quickstart"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P0
sample_count: 64
member_drafts:
  - 075-tested-driver-and-odm-version-matrix-with-copyable-pins-per-.md
  - 044-learn-compatibility-page-lacks-a-tested-driver-odm-version-m.md
  - 126-driver-compatibility-matrix-connection-options-and-read-writ.md
open_questions: 5
---

# Add a driver and ODM compatibility page with tested versions and client options, linked from every quickstart

## What happens today

Azure DocumentDB's Learn docs already know the tested driver pairings, but only as a "Tested driver version" sub-heading on individual ODM quickstarts:

- `quickstart-nodejs-mongoose`: MongoDB Node.js driver 7.8.0 via Mongoose 9.12.1, Node 22.12+.
- `quickstart-python-beanie`: Beanie 2.2.0 with PyMongo 4.19.0 (`AsyncMongoClient`, not Motor), Python 3.13.
- `quickstart-python-django`: Django MongoDB Backend 6.1.0 with PyMongo 4.19.0 (Django 6.1.3), Python 3.13.
- ODM quickstarts also exist for Prisma, Spring Data MongoDB and EF Core; whether each has a tested-version block was not checked.

Nothing ties these together or covers other stacks:

- `quickstart-python` (`pip install pymongo`) and `quickstart-nodejs` (`npm install mongodb`) are unpinned and state no tested version. `quickstart-python` says "Python 3.12 or later" while the Beanie and Django pages say 3.13, and it never says when to use `AsyncMongoClient` instead of Motor.
- `query-knowledge-base` (LlamaIndex) installs its packages unpinned.
- `how-to-connect-role-based-access-control` shows `MONGODB-OIDC` code but no minimum driver version.
- The FAQ lists supported wire protocol versions (5.0 to 8.0) but no per-language driver table. The *Compatibility* TOC node has no drivers page; `/compatibility` and `/driver-compatibility` return 404.
- No page maps `writeConcern`, `readConcern` and `readPreference` to service behaviour, gives pool and timeout recommendations, or says that `useNewUrlParser` / `useUnifiedTopology` do nothing in current drivers. The `high-availability` page says primary and standby shards use synchronous replication with zero data loss on failover, but does not tie that to concern values. The Mongoose tutorial uses `maxPoolSize: 10` and `serverSelectionTimeoutMS: 30000` without explaining them; other quickstarts show a bare client.
- Pages are inconsistent on retryable writes. The portal connection string and every quickstart include `retrywrites=false`, which is required because Azure DocumentDB does not support retryable writes, but the Mongoose tutorial calls the value "a sample" rather than a requirement, and no Learn page (limitations, compatibility, connect) explains why the setting is required.

## Why it matters

In one experiment run, a coding agent (gpt-5-mini with the DocumentDB Agent Kit and Learn MCP) built 100 sample apps. 114 findings across **64 of the 100 samples** trace to this gap. Counts are from that single run and are approximate. With no general page to find, the agent picked versions from model memory, which are about two years stale:

- 21 of 22 Mongoose samples pinned `^7.x`; 16 of 26 direct-driver Node samples pinned `mongodb ^5.x`. Agents invented versions that do not exist (`mongodb@^5.10.0`, `mongoose@7.14.0`) and hit `npm notarget` in 13 runs.
- 17 Python samples used Motor and only 1 used `AsyncMongoClient`; most Beanie samples pinned Beanie 1.x, the stack the Beanie quickstart tells readers to leave. Results included `init_beanie` failures ("MotorDatabase object is not callable"), `cannot import name _QUERY_OPTIONS from pymongo.cursor`, and pydantic-core source builds on Python 3.13 (old pydantic 2.x pins such as `pydantic==2.6.1` ship no cp313 wheel) [needs SME confirmation: the reviewer flags Python 3.13 install failures as possibly a harness artifact]. Several agents dropped Beanie or LangChain to get a green build.
- 10 audits could not verify driver pins, concern levels or pool settings against any public source, so a points ledger shipped with `w: "majority"` assumptions copied from generic MongoDB guidance.

Agent logs show no ODM quickstart was opened during builds: the per-page note is correct but not discoverable.

The reviewer notes that sample counts in this experiment are unstable and should be re-checked after the harness fixes before they are quoted externally [needs SME confirmation].

## Proposed change

**1. New page "Driver compatibility and recommended client options"** under *Compatibility* in the TOC, linked from the FAQ answer on driver compatibility.

- **Driver and ODM table**: language, runtime tested, driver tested, ODM tested, minimum version (per wire protocol version, see open questions), last verified, notes. Open with one sentence: Azure DocumentDB implements the MongoDB wire protocol; use a driver release that supports the compatibility version selected for the cluster (the quickstarts select 8.0); the versions below are the ones last verified in the quickstarts. Seed it from published values: Node `mongodb` 7.8.0 (Node 22.12+); Mongoose 9.12.1 (bundles driver 7.8.0; do not install a separate `mongodb`; Mongoose 7 bundles driver 5.x); PyMongo 4.19.0 (`MongoClient` or `AsyncMongoClient`, Python 3.13); Beanie 2.2.0 + PyMongo 4.19.0 (do not install Motor); Django MongoDB Backend 6.1.0 with Django 6.1.3 and PyMongo 4.19.0; LlamaIndex `llama-index-vector-stores-azurecosmosmongo` 0.9.0 (`AzureCosmosDBMongoDBVectorSearch`; pass `pre_filter` via `vector_store_kwargs`, `MetadataFilters` are not translated in 0.9.0, set `kind` explicitly because it defaults to HNSW); an Entra ID `MONGODB-OIDC` row with the minimum PyMongo, Node and C# driver versions [needs SME confirmation]. Add Java, .NET, Go and Rust driver rows and Prisma, Spring Data MongoDB and EF Core ODM rows from their quickstarts.
- **Python 3.13 note**: older pydantic 2.x pins have no prebuilt `pydantic-core` wheel for 3.13, so pip builds from source and needs a Rust toolchain; let Beanie 2 resolve a current pydantic 2.x, or pin one that ships 3.13 wheels.
- **Copyable fragments**: a `requirements.txt` (`beanie==2.2.0`, `pymongo==4.19.0`, `python-dotenv>=1,<2`) with the same lines as `constraints.txt` for `pip install -r requirements.txt -c constraints.txt`, and a `package.json` fragment with exact versions (no caret) and `"engines": { "node": ">=22.12" }`.
- **Sync or async (Python)**: `MongoClient` for scripts and WSGI; `pymongo.AsyncMongoClient` for FastAPI and asyncio code. It was beta from PyMongo 4.9 and generally available from 4.13, so pin 4.13 or later for async code. MongoDB's migration guide dates Motor's deprecation to May 14, 2026; do not start new code on it. Add a short Motor-to-`AsyncMongoClient` before/after.
- **Known-bad combinations** with their exact error strings (above), including importing `ChatOpenAI` from `@langchain/openai`, not `langchain/chat_models/openai`.
- **Canonical client options** per language, matching the quickstarts and the portal connection string: `tls=true`, `authMechanism=SCRAM-SHA-256`, `retrywrites=false`, `maxIdleTimeMS=120000`, one client per process. Note that `useNewUrlParser` and `useUnifiedTopology` have no effect in Node driver 4+ and were removed in Mongoose 6.
- **Retryable writes statement**: state that retryable writes are not supported and that `retrywrites=false` is required, and explain why with the de-duplication reason. Suggested text: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Correct the Mongoose tutorial's "a sample" wording to match, so the quickstarts, the Mongoose tutorial and the Agent Kit say the same thing. Do not claim that `retryWrites=true` causes connection errors; that is not established.
- **Beanie on Azure DocumentDB**: `init_beanie` creates indexes declared in `Settings.indexes` and `Indexed()` fields; TTL via `IndexModel([("expiresAt", 1)], expireAfterSeconds=0)`; atomic `find_one(...).update({"$push": ..., "$set": ...}, response_type=UpdateResponse.NEW_DOCUMENT)`; optimistic concurrency with a `version` field in the filter and `$inc` in the update; idempotent fallback `create_index(...)` when init runs without index permission.
- **Mongoose production configuration**: `autoIndex: false`, `autoCreate: false`, `bufferCommands: false`, then `Model.createCollection()` / `Model.createIndexes()` in a seed or migration script, with a sentence on why (the Mongoose quickstart already does this).
- **Consistency table**: each `writeConcern` (`w: 1`, `w: "majority"`, `j`), `readConcern` and `readPreference` value, and what the service does with it (honored, accepted and ignored, or rejected), with and without in-region HA and on replica clusters [needs SME confirmation]. Cover `readConcern` `local`, `majority`, and `linearizable` / `snapshot` if applicable, and link the synchronous-replication statement on the `high-availability` page.
- **Pool and timeout table**: `maxPoolSize`, `minPoolSize`, `serverSelectionTimeoutMS`, `socketTimeoutMS`, `maxIdleTimeMS` for Functions, App Service/containers and batch jobs [needs SME confirmation], explaining the `maxPoolSize: 10` / `serverSelectionTimeoutMS: 30000` values the Mongoose tutorial uses.
- **Pinning**: pin direct dependencies to the tested versions, commit `package-lock.json` / `constraints.txt`, install with `npm ci` / `pip install -c constraints.txt`, and re-pin by re-running the quickstart rather than widening ranges.

**2. Link it from every quickstart.** In each existing "Tested driver version" block, promote it to a `> [!NOTE]` and add: "For all languages and ODMs, see Driver compatibility and recommended client options." Add the same block to quickstarts that lack one, `query-knowledge-base`, and the Entra ID section of `how-to-connect-role-based-access-control`.

**3. Pin the driver quickstarts.** `quickstart-python`: `python -m pip install "pymongo==4.19.0"` plus "Tested with PyMongo 4.19.0 on Python 3.13 and MongoDB compatibility 8.0", so the Python pages agree. Add a short "Sync or async?" paragraph (`MongoClient` for scripts, batch jobs and WSGI; `AsyncMongoClient` for FastAPI and asyncio agents; not Motor) and an `AsyncMongoClient` connect-and-ping example that reads the URI from an environment variable and uses the documented URI options. `quickstart-nodejs`: `npm install mongodb@7.8.0` plus "Tested with driver 7.8.0, Node 22.12+". `query-knowledge-base`: pin the validated package versions.

**4. Beanie troubleshooting row**: "`TypeError` from `init_beanie` or 'MotorDatabase object is not callable': you have Beanie 1.x with Motor. Uninstall `motor`, install `beanie==2.2.0 pymongo==4.19.0`, pass `client[db]` from `AsyncMongoClient`."

**5. Entra ID page**: one sentence above the first `MONGODB-OIDC` example giving the minimum driver versions [needs SME confirmation; see open question 1].

**6. Follow-up outside Learn (separate Azure/documentdb-agent-kit change, not part of this feedback).** Once the page exists, the kit should link to it rather than restate versions:

- `skills/connection/SKILL.md` (Python async note, lines 45-49) says "PyMongo 4.9+" and that "MongoDB announced Motor's deprecation in May 2024"; the async API was beta in 4.9 and GA in 4.13, and MongoDB's migration guide gives May 14, 2026. It also has a pool-sizing table that should agree with the Learn pool table.
- `skills/driver/SKILL.md` (13 lines) has the singleton rule only and no versions.
- Retryable writes: `skills/connection/SKILL.md` line 60 has `retryWrites=true`, as do `skills/driver/driver-singleton-client.md` line 26 and `skills/security/security-tls-required.md` line 26, while `skills/azure-deployment/SKILL.md` line 291 correctly says retryable writes are not supported. Change the three `true` values to `retryWrites=false` and use the one-liner above as the rationale; drop any wording that says `retryWrites=true` causes connection errors, which is not established.

## Evidence

- `runs/20-identity-resolution-multi-agent/20261124-210002`: Beanie 1.x + Motor; `init_beanie failed: MotorDatabase object is not callable`.
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049`: pydantic-core build failure on Python 3.13, `_QUERY_OPTIONS` ImportError; Beanie removed.
- `runs/02-real-time-event-stream-ingestion/20261124-203233`: `npm error notarget` for `mongodb@^5.10.0`.
- `runs/09-trade-settlement-tracker/20261124-201323`: `mongoose ^7.9.0`, no lockfile; audit marks the pin wrong.
- `runs/16-population-health-dashboard-backend/20261124-195348`: driver pin `listed_not_found`; searches for a driver table recorded.
- `runs/16-loyalty-points-ledger/20261124-184937`: `writeConcern` semantics for a ledger from prior knowledge only.
- `runs/18-returns-refund-workflow-orchestration/20261124-185415`: `ERR_PACKAGE_PATH_NOT_EXPORTED` for `langchain/chat_models/openai`; LangChain dropped.
- `runs/03-core-banking-transaction-ledger/20261124-200452`: Mongoose pins 7.6.0, then 7.9.3, then `^7.0.0` after npm failure.
- `runs/17-ai-survey-response-analyzer/20261124-205518`: readiness gap "Beanie + Async driver compatibility matrix"; Beanie 1.24.0 + Motor 3.1.1 + PyMongo 4.6.0.
- `runs/17-rare-disease-literature-search/20261124-195633`: LlamaIndex pinned `>=0.9.0` with `pymongo>=4.5`.

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

## Open questions

1. [needs SME confirmation] Minimum PyMongo and Node driver versions for `MONGODB-OIDC` (drafts suggest PyMongo 4.7 and Node 6.7; no Learn page states them) and the Java and .NET floors.
2. [needs SME confirmation] Minimum supported driver version per language for each wire protocol version (5.0 to 8.0), and whether Node 24 is tested.
3. [needs SME confirmation] How the service treats each `writeConcern`, `readConcern` and `readPreference` value, with and without HA.
4. [needs SME confirmation] Recommended pool and timeout values per hosting model.
5. [needs SME confirmation] Tested versions for the LlamaIndex page (`llama-index`, `pymongo`) and the Java, .NET, Go and Rust quickstarts.

## Source drafts

- 075-tested-driver-and-odm-version-matrix-with-copyable-pins-per-.md
- 044-learn-compatibility-page-lacks-a-tested-driver-odm-version-m.md
- 126-driver-compatibility-matrix-connection-options-and-read-writ.md
