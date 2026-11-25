---
title: "Add a 'Driver compatibility and tested versions' page to Azure DocumentDB Learn docs, linked from every language quickstart, with copyable pins"
repo: learn-docs
type: pr
status: ready_with_edits
priority: P0
sample_count: 48
findings: 62
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add "Driver compatibility and tested versions" page, link it from every quickstart, and pin the Python/Node driver quickstarts

## What happens today

Learn already knows the right pairings, but only two pages say so and only in a prerequisites sub-heading:

- `quickstart-python-beanie`: "Tested with Beanie 2.2.0 and PyMongo 4.19.0", Python 3.13, `AsyncMongoClient` (not Motor).
- `quickstart-nodejs-mongoose`: "Tested with MongoDB Node.js driver 7.8.0, a dependency of Mongoose 9.12.1", Node 22.12+, `autoIndex: false`.

Everything else is silent:

- `quickstart-python` runs `pip install pymongo` and `quickstart-nodejs` runs `npm install mongodb` with no version, no "Tested with" line, no pinning advice.
- `how-to-connect-role-based-access-control` shows `authMechanism=MONGODB-OIDC` for Entra ID but never says which driver version first supports it.
- No page states the matrix (Beanie <-> AsyncMongoClient/Motor <-> PyMongo <-> Python; Mongoose <-> mongodb driver <-> Node), the minimum versions newer features need, or a pinning policy for sample repos. Searching Learn for "driver version", "driver compatibility" or "pymongo tested version" returns nothing targeted (the `compatibility` and `compatibility-and-feature-support` URLs 404).

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini + DocumentDB Agent Kit + Learn/Azure/DocumentDB MCP), 62 audit findings across **48 of 100 samples** are this one gap seen from Python, Node and LangChain stacks. Because the builder could not find an authoritative pin, it chose by model default, and the defaults are two years stale:

- **Mongoose:** 22 samples use Mongoose; **21 pinned `^7.x`**, 1 pinned 9.x. Quickstart tests 9.12.1. Direct `mongodb` driver pins were `^5.x` in 16 of 26 Node samples (quickstart tests 7.8.0).
- **Python async:** 17 samples import `motor.motor_asyncio`, **1** uses `AsyncMongoClient`. Of 18 Beanie samples, 10 pinned `beanie==1.x`, 1 pinned 2.x. `pymongo==4.4.0` is the most common exact pin (11 samples); 28 exact pins are below 4.9, the floor for `AsyncMongoClient`.
- **Concrete breakage caused by the stale defaults:**
  - 13 runs hit `npm error notarget` (e.g. `mongodb@^5.10.0` does not exist) and settled on a lower 5.x by trial.
  - 2 runs: `init_beanie` failed with "MotorDatabase object is not callable" (Beanie 1.x API mismatch); the sample silently fell back to raw Motor writes.
  - 2 runs: `ImportError: cannot import name _QUERY_OPTIONS from pymongo.cursor` (Motor vs PyMongo internals); one builder rewrote the seed script to synchronous `pymongo`, so the async FastAPI startup was never exercised.
  - 4 runs: `pip` tried to build `pydantic-core` from source (Rust toolchain error) on Python 3.13 while iterating through old Beanie/pydantic pins (for example `pydantic==2.6.1`, which has no cp313 wheel); one builder dropped Beanie entirely.
  - 4 runs: `ERR_PACKAGE_PATH_NOT_EXPORTED` for `langchain/chat_models/openai` (langchain `^0.2.2` deep subpath under CommonJS); two builders removed LangChain, so the sample no longer demonstrates what the prompt asked for.
  - One sample committed a `requirements.txt` with seven bare names and no versions, then failed verification on an `init_beanie` TypeError.

Readers copying these samples inherit the same failures. Agents reading Learn will keep choosing Mongoose 7 and Beanie 1 + Motor until the tested pairing is discoverable by a general search and copyable.

## Proposed change (one PR to `azure/documentdb/`)

### 1. New page `driver-compatibility.md` — "Driver compatibility and tested versions"

Sections (short, table-first):

**Python**

| Stack | Pin | Notes |
|---|---|---|
| PyMongo (sync or async) | `pymongo==4.19.0` | Tested with server compatibility 8.0. `AsyncMongoClient` first shipped (beta) in PyMongo 4.9 and is GA from 4.13; pin 4.13 or later for async code. |
| Beanie ODM | `beanie==2.2.0` + `pymongo==4.19.0` | Beanie 2 uses PyMongo's `AsyncMongoClient`. Do not install Motor. |
| Motor | not recommended | Deprecated upstream (critical fixes only through May 2026). Imports PyMongo internals and breaks on PyMongo minor upgrades (`cannot import name _QUERY_OPTIONS`). |
| Python | 3.12 or 3.13 | On 3.13, older pydantic 2.x pins (for example `pydantic==2.6.1`) have no prebuilt `pydantic-core` wheel, so pip builds it from source and needs a Rust toolchain. Let Beanie 2 resolve a current pydantic 2.x, or pin one that ships Python 3.13 wheels. |
| Entra ID (`MONGODB-OIDC`) | PyMongo 4.7+ (maintainers confirm exact floor) | Older pins such as `pymongo==4.4.0` silently cannot use Entra ID. |

Copyable `requirements.txt`:
```
beanie==2.2.0
pymongo==4.19.0
python-dotenv>=1,<2
```
and the same lines as `constraints.txt` with `pip install -r requirements.txt -c constraints.txt`.

**Node.js**

| Stack | Pin | Notes |
|---|---|---|
| MongoDB Node.js driver | `mongodb@7.8.0` | Node 22.12+ (22.x line tested). 5.x is two majors behind the tested version. |
| Mongoose | `mongoose@9.12.1` | Bundles driver 7.8.0; do not install a separate `mongodb`. Mongoose 7 bundles driver 5.x and is not what the quickstarts test. |
| Entra ID (`MONGODB-OIDC`) | driver 6.7+ (maintainers confirm) | |
| LangChain.js | `langchain` + `@langchain/openai` + `@langchain/mongodb` (exact versions) | Deep subpaths such as `langchain/chat_models/openai` are not exported in 0.2+ and fail with `ERR_PACKAGE_PATH_NOT_EXPORTED` under both ESM and CommonJS; import `ChatOpenAI` from `@langchain/openai` instead. |

Copyable `package.json` fragment with exact versions (no caret) and `"engines": { "node": ">=22.12" }`.

**Canonical client options** (one snippet per language, mirroring the quickstarts): `tls=true`, `authMechanism=SCRAM-SHA-256`, `retryWrites=false`, `maxIdleTimeMS=120000`, `serverSelectionTimeoutMS=30000`; one client per process.

**Pin and lock** (one paragraph): pin direct dependencies to the exact tested versions, commit `package-lock.json` / `constraints.txt`, install with `npm ci` / `pip install -c constraints.txt`; re-pin by re-running the quickstart, not by widening ranges.

**Migrating from Motor to `AsyncMongoClient`** (6-line before/after): `from motor.motor_asyncio import AsyncIOMotorClient` -> `from pymongo import AsyncMongoClient`; `init_beanie(database=client[db_name], document_models=[...])` unchanged; `await client.close()` is now awaited.

**Beanie on Azure DocumentDB** (short): `init_beanie` creates indexes declared in `Settings.indexes` and `Indexed()` fields; TTL via `IndexModel([("expiresAt", 1)], expireAfterSeconds=0)` in `Settings.indexes`; atomic `find_one(...).update({"$push": ..., "$set": ...}, response_type=UpdateResponse.NEW_DOCUMENT)`; optimistic concurrency by including a `version` field in the filter and `$inc` in the update; idempotent fallback `await db[collection].create_index(...)` when init runs without index permission.

**Mongoose production configuration**: `autoIndex: false`, `autoCreate: false`, `bufferCommands: false`, then `Model.createCollection()` / `Model.createIndexes()` in a seed or migration script (this is already what `quickstart-nodejs-mongoose` does; say why).

**Known-bad combinations** (bullet list, each with the exact error string from the runs above).

### 2. "Tested with" callout on the four language quickstarts

- `quickstart-python`: replace `pip install pymongo` with `python -m pip install "pymongo==4.19.0"` and add, directly under Prerequisites, a boxed note: "Tested with PyMongo 4.19.0 on Python 3.13 and MongoDB compatibility 8.0. See Driver compatibility and tested versions." Also note Python 3.12+ prerequisite vs Beanie's 3.13 so the two pages agree.
- `quickstart-nodejs`: replace `npm install mongodb` with `npm install mongodb@7.8.0` and the same boxed note (driver 7.8.0, Node 22.12+).
- `quickstart-python-beanie` and `quickstart-nodejs-mongoose`: promote the existing "Tested driver version" sub-heading to a `> [!NOTE]` box placed before "Already using ...?", and add a one-line link to the new page. Keep the existing text.

### 3. Beanie quickstart troubleshooting row

Add to the "Troubleshoot common issues" table:

| `TypeError` from `init_beanie`, or "MotorDatabase object is not callable" | You have Beanie 1.x with Motor installed. Uninstall `motor`, install `beanie==2.2.0 pymongo==4.19.0`, and pass `client[database]` from `pymongo.AsyncMongoClient`. |

### 4. Entra ID how-to

In `how-to-connect-role-based-access-control`, add one sentence above the first `MONGODB-OIDC` connection example: "`MONGODB-OIDC` requires PyMongo 4.7 or later and MongoDB Node.js driver 6.7 or later; the quickstarts pin 4.19.0 and 7.8.0." (Maintainers: confirm the Java/.NET floors or omit them.)

### Out of scope here, filed separately

Mirror the two tables and the "which Python async driver" rule into `Azure/documentdb-agent-kit` `skills/connection/SKILL.md` (it already says to use PyMongo's `AsyncMongoClient` (4.9+), not Motor, but gives no tested pins) and `skills/driver/SKILL.md` (13 lines, singleton only), with a one-line reproduction command (`python -c "import beanie, pymongo; print(beanie.__version__, pymongo.version)"`) so builders stop iterating through pip failures.

## Evidence (run folders under `azure-documentdb-agent-readiness/runs/`; no connection strings)

- `runs/20-identity-resolution-multi-agent/20261124-210002` — `requirements.txt` has `beanie>=1.12.0 motor>=3.1.1 pymongo>=4.5.0`; `events.jsonl` shows `init_beanie failed: MotorDatabase object is not callable` on every seed and orchestrator run; `doc-gaps.md` "Beanie initialization compatibility note".
- `runs/11-preference-center-consent-store/20261124-204614` — pinned `beanie==1.22.1 motor==3.1.1 pydantic==1.10.12`; decision D016 rewrote the seed script to sync `pymongo` after a Motor ImportError; `03-build.json` records the async app was never started.
- `runs/15-supplier-po-management/20261124-184929` — `requirements.txt` has seven bare names; `doc-gaps.md` "Dependency-version pins in quickstart" (init_beanie TypeError blocked verification) even though readiness had already surfaced the Beanie quickstart's "Beanie 1 with Motor, stop and update" text.
- `runs/02-real-time-event-stream-ingestion/20261124-203233` — `npm error notarget No matching version found for mongodb@^5.10.0`; settled on `^5.9.0` (quickstart tests 7.8.0).
- `runs/18-returns-refund-workflow-orchestration/20261124-185415` — `mongoose ^7.6.0`, `langchain ^0.2.2`; `ERR_PACKAGE_PATH_NOT_EXPORTED: ./chat_models/openai`; LangChain dropped from the sample.
- `runs/07-voice-of-customer-sentiment-hub/20261124-204049` — `No matching distribution found for beanie==1.20.1`; pydantic-core Rust build failure on Python 3.13 (D016/D017); `cannot import name _QUERY_OPTIONS from pymongo.cursor` (D018); Beanie removed.

Aggregate counts above come from `runs/*/*/app/{requirements.txt,package.json}` and `runs/*/*/events.jsonl` across all 100 runs.

## Verification

### 1. Already covered? partially_covered

The tested pairings exist on Learn, but only on two framework quickstarts, under a prerequisites sub-heading. Nothing links them from the driver quickstarts or from a general page.

- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-beanie (updated 2026-11-24):
  - "This quickstart was tested with Beanie 2.2.0 and PyMongo 4.19.0."
  - It also says it uses "Beanie 2 and PyMongo's asynchronous client, not Motor".
  - Its troubleshooting table has no init_beanie or Motor row.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-mongoose:
  - "tested with MongoDB Node.js driver 7.8.0, a dependency of Mongoose 9.12.1".
  - It already uses `autoIndex: false`, `autoCreate: false` and `bufferCommands: false`, then `createCollection()` and `createIndexes()`.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python: unpinned `pip install pymongo`, prerequisite "Python 3.12 or later", no tested-version text.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs: unpinned `npm install mongodb`, prerequisite "Node.js 22 or newer", no tested-version text.
- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control: uses `authMechanism=MONGODB-OIDC` with `OIDCCallback` (Python) and `OIDC_CALLBACK` (Node), but states no minimum driver version.
- https://learn.microsoft.com/en-us/azure/documentdb/compatibility and https://learn.microsoft.com/en-us/azure/documentdb/driver-compatibility both return HTTP 404.
- Agent kit (companion PR only):
  - `skills/connection/SKILL.md` lines 45-49 say "Use PyMongo's native `AsyncMongoClient` (PyMongo 4.9+), **not** Motor", but give no tested pins.
  - `skills/driver/SKILL.md` is 13 lines and has no version guidance.
  - documentdb-mcp has no driver-version guidance.

### 2. Premise true? confirmed, with three corrections applied in the body

What checks out:

- The quickstart pins match the live pages quoted above: Beanie 2.2.0 with PyMongo 4.19.0, Mongoose 9.12.1 with driver 7.8.0, Node 22.12+, and Python 3.13 for Beanie.
- Mongoose 7 depends on the mongodb 5.x driver. The 5.x line ended at 5.9.x, so `mongodb@^5.10.0` genuinely fails with `notarget`.
- Motor is deprecated in favor of PyMongo's async API and gets only critical fixes until May 2026. The kit text says the same.
- Nothing contradicts the service facts. The client options match the quickstarts, and the draft makes no RU or Atlas Search claims.

Corrections:

- **`AsyncMongoClient` version.** It first shipped as a beta in PyMongo 4.9 and is GA from 4.13. The body now recommends 4.13 or later instead of "requires 4.9+".
- **pydantic-core build failures.** These were not caused by pydantic v1 pins, because pydantic 1.x does not depend on pydantic-core. On Python 3.13, pip built `pydantic-core` from source for old pydantic 2.x pins that ship no cp313 wheel.
  - `runs/03-substitute-product-finder/20261124-183232` pins `pydantic==2.6.1`.
  - The events.jsonl files of runs 03, 05, 07 and 19 show "Failed building wheel for pydantic-core" or Rust toolchain errors.
- **LangChain import error.** `ERR_PACKAGE_PATH_NOT_EXPORTED` for `langchain/chat_models/openai` comes from the removed subpath export, not from CommonJS vs ESM. The fix is to import from `@langchain/openai`, not to set `"type": "module"`.

The MONGODB-OIDC floors (PyMongo 4.7 and Node driver 6.7 for the callback API) stay marked "maintainers confirm", because no Learn page states them.

### 3. Maintainer skeptic: confirmed

I would accept this as a maintainer, possibly split into two PRs: "pin the driver quickstarts" and "new compatibility page".

- It names exact existing pages: `quickstart-python`, `quickstart-nodejs`, `quickstart-python-beanie`, `quickstart-nodejs-mongoose` and `how-to-connect-role-based-access-control`. It also proposes one new page, `driver-compatibility.md`.
- The edits are concrete and copyable: pinned install commands, a NOTE box, one troubleshooting row and one sentence on the Entra page.
- It reuses pins the docs team has already verified, and it is specific to Azure DocumentDB.
- It correctly sends the agent-kit mirror to a separate PR in Azure/documentdb-agent-kit.

## Finding ids

- F0095
- F0133
- F0164
- F0167
- F0272
- F0296
- F0368
- F0442
- F0473
- F0541
- F0813
- F0930
- F1022
- F1055
- F1088
- F1122
- F1146
- F1183
- F1217
- F1316
- F1388
- F1417
- F1450
- F1505
- F1573
- F1641
- F1647
- F1672
- F1739
- F1847
- F1874
- F1875
- F1879
- F2100
- F2136
- F2168
- F2375
- F2413
- F2439
- F2442
- F2446
- F2477
- F2532
- F2534
- F2537
- F2634
- F2637
- F2760
- F2793
- F2922
- F2960
- F2999
- F3031
- F3033
- F3086
- F3093
- F3199
- F3384
- F3407
- F3445
- F3512
- F3514
