---
title: "Add a single \"Client drivers, ODMs, and tested versions\" matrix to Azure DocumentDB Learn docs and link it from every language quickstart"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 40
findings: 42
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add a "Client drivers, ODMs, and tested versions" matrix and link it from every quickstart

**Pages:** `compatibility-features` (new section, or a new `compatibility-drivers` page under *Compatibility* in the TOC), `quickstart-python`, `quickstart-nodejs`, `quickstart-nodejs-mongoose`, `quickstart-python-beanie`, `quickstart-python-django`, `query-knowledge-base` (LlamaIndex), `how-to-connect-role-based-access-control`.

## What happens today

Tested driver and ODM versions for Azure DocumentDB exist, but only as a one-paragraph "Tested driver version" note inside the ODM quickstarts (ms.date 2026-11-17):

- `quickstart-nodejs-mongoose`: "tested with MongoDB Node.js driver 7.8.0, a dependency of Mongoose 9.12.1"; Node 22.12.0 or later in the 22.x line.
- `quickstart-python-beanie`: "tested with Beanie 2.2.0 and PyMongo 4.19.0" using `AsyncMongoClient`, Python 3.13.x, with an "Already using Beanie?" note telling Beanie 1 + Motor apps to move to Beanie 2 + `AsyncMongoClient`, and an `init_beanie` example.
- `quickstart-python-django`: "tested with Django MongoDB Backend 6.1.0 and PyMongo 4.19.0" (Django 6.1.3), Python 3.13.x.
- Similar ODM quickstarts exist for Prisma, Spring Data MongoDB and EF Core (not individually checked for a tested-version block).

Nothing ties these together or covers the other stacks:

- `compatibility-features` lists only unsupported or limited server features (aggregation stages, command categories, collection types); it has no server-version list and no driver or ODM table. The *Compatibility* TOC node (`managed-service-compatibility`, `compatibility-features`, `compatibility-query-language`) has no drivers page.
- `quickstart-python` says "Python 3.12 or later", runs `pip install pymongo` unpinned, shows only the sync `MongoClient`, and says nothing about `AsyncMongoClient` vs Motor for FastAPI/agent workloads. It therefore disagrees with the Python 3.13.x stated on the Beanie and Django pages.
- `quickstart-nodejs` (raw `mongodb` driver) says "Node.js 22 or newer", runs `npm install mongodb` unpinned and has no tested version, so builders who do not use Mongoose have nowhere to look.
- `query-knowledge-base` (LlamaIndex) installs `llama-index`, `llama-index-vector-stores-azurecosmosmongo` and `pymongo` unpinned; version 0.9.0 of the vector store package is mentioned only in passing for behavior caveats (index-kind default, `pre_filter` vs `MetadataFilters`).
- `how-to-connect-role-based-access-control` shows `MONGODB-OIDC` / `OIDC_CALLBACK` code for Python, TypeScript and C# but states no minimum driver version that supports the callback mechanism.

## Why it matters

40 of the 100 generated samples (42 findings) logged this as an information gap in the readiness stage, in both stacks, and the build results show what the agent did instead:

- **Node.js samples pinned Mongoose `^7.x` or `mongodb ^5.x`**, never Mongoose 9 / driver 7.8. Agents invented versions that do not exist (`mongoose@7.14.0`, `7.9.3`), hit npm `ETARGET`, then fell back to caret ranges with no lockfile. The 09-trade-settlement audit marked the pin decision "wrong" against published guidance and the sample failed its reproducible-install check.
- **Beanie samples pinned Beanie 1.x + Motor 3.x**, the stack the Beanie quickstart tells readers to move off. Agents also tried non-existent Beanie versions and retried until pip accepted one; some samples hit Beanie API breaks from the version churn.
- PyMongo pins landed at 4.4 to 4.7 (2023) rather than 4.19; LlamaIndex was pinned `>=0.9.0` with pymongo `>=4.5`, an untested combination.
- `events.jsonl` for these runs shows no ODM quickstart URL was opened during the build; Learn search snippets did not surface the "Tested driver version" block. The per-page note is correct but undiscoverable, and it is absent from the pages a driver-only, LlamaIndex or Entra ID builder does read.

Net effect: samples ship 2023-era dependency pins, several with broken installs, and agents give conflicting Beanie guidance (Motor vs `AsyncMongoClient`) to users.

## Proposed change

### 1. One matrix on a compatibility page

Add a section **"Client drivers, ODMs, and tested versions"** to `compatibility-features` (or a new `compatibility-drivers` page under *Compatibility* in `toc.json`). Suggested columns and rows, using the values already published; the docs team fills the cells marked *confirm*:

| Language | Runtime tested | Driver (tested) | ODM / integration (tested) | Minimum | Last verified | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Node.js | 22.12+ (Node 24: *confirm*) | `mongodb` 7.8.0 | none | *confirm* | 2026-11 | `quickstart-nodejs` should pin this |
| Node.js | 22.12+ in the 22.x line (Node 24: *confirm*) | `mongodb` 7.8.0 (bundled) | Mongoose 9.12.1 | Mongoose 9 | 2026-11 | Don't install a separate `mongodb` copy |
| Python | 3.13.x | PyMongo 4.19.0 (`MongoClient` or `AsyncMongoClient`) | none | PyMongo 4.13 for `AsyncMongoClient` (GA; 4.9 to 4.12 were beta) | 2026-11 | Motor is deprecated by MongoDB as of May 14, 2026; don't start new code on it |
| Python | 3.13.x | PyMongo 4.19.0 (`AsyncMongoClient`) | Beanie 2.2.0 | Beanie 2 | 2026-11 | Beanie 1 + Motor: migrate before use; see quickstart note |
| Python | 3.13.x | PyMongo 4.19.0 | Django MongoDB Backend 6.1.0 (Django 6.1.3) | match Django and backend at 6.1 | 2026-11 | |
| Python | *confirm* | PyMongo (*confirm*) | `llama-index-vector-stores-azurecosmosmongo` 0.9.0 (`AzureCosmosDBMongoDBVectorSearch`) | *confirm* | *confirm* | `pre_filter` via `vector_store_kwargs`; `MetadataFilters` not translated in 0.9.0; set `kind` explicitly (defaults to HNSW) |
| Python / Node.js / .NET | | PyMongo *confirm* / `mongodb` *confirm* / C# driver *confirm* | Entra ID `MONGODB-OIDC` with `OIDC_CALLBACK` | *confirm* | *confirm* | Minimum driver that supports the callback mechanism |
| Java, Go, Rust, C# (and Prisma, Spring Data, EF Core) | *confirm* | *confirm* | *confirm* | *confirm* | *confirm* | Carry over values from each quickstart's tested-version block |

Add one sentence above the table: "Azure DocumentDB implements the MongoDB wire protocol; use a driver release that supports the MongoDB compatibility version you selected for the cluster (the quickstarts select 8.0). The versions below are the ones Microsoft last verified in the quickstarts." The docs team should also state the list of selectable MongoDB compatibility versions here (*confirm*), since no Learn page checked lists it.

### 2. Link to it from every quickstart

In each quickstart's existing **Tested driver version** block (Mongoose, Beanie, Django, and the Prisma, Spring Data and EF Core pages where present) and in the driver quickstarts that lack one (`quickstart-python`, `quickstart-nodejs`, and the C#, Java, Go and Rust driver quickstarts), add: "For all languages and ODMs, see [Client drivers, ODMs, and tested versions](compatibility-features#client-drivers-odms-and-tested-versions)." Add the same link to `query-knowledge-base` and to the "Connect using Microsoft Entra ID in code" section of `how-to-connect-role-based-access-control`.

### 3. `quickstart-python`: pin and say sync vs async

- Change `pip install pymongo` to `python -m pip install "pymongo==4.19.0"` and add a **Tested driver version** block matching the Beanie and Django pages (PyMongo 4.19.0, Python 3.13.x), so the Python pages agree on the Python version.
- Add a short paragraph **"Sync or async?"**: use `MongoClient` for scripts, batch jobs and WSGI apps; use `pymongo.AsyncMongoClient` (generally available since PyMongo 4.13) for FastAPI, asyncio agents and other event-loop code; don't start new code on Motor, which MongoDB deprecated on May 14, 2026. Include a short `AsyncMongoClient` connect/ping example that reads the URI from an environment variable and uses the documented URI options (`tls=true`, `authMechanism=SCRAM-SHA-256`, `retrywrites=false`).

### 4. `quickstart-nodejs`: pin the driver

Change `npm install mongodb` to `npm install mongodb@7.8.0` (or the version the page is retested with) and add a **Tested driver version** block.

### 5. `query-knowledge-base`: pin the install line

Replace the unpinned `pip install` with the versions the page was validated against (at least `llama-index-vector-stores-azurecosmosmongo==0.9.0` and the `llama-index` and `pymongo` versions used), and add a **Tested package versions** line.

### Follow-up outside Learn (not part of this change)

`Azure/documentdb-agent-kit` `skills/connection/SKILL.md` says to use "PyMongo's native `AsyncMongoClient` (PyMongo 4.9+), not Motor" and that "MongoDB announced Motor's deprecation in May 2024". Both details are off: the async API was beta in 4.9 and GA in 4.13, and MongoDB's migration guide says Motor is deprecated on May 14, 2026. The skill never mentions Beanie or any pin, and `skills/driver/SKILL.md` has no versions. Once the matrix exists, both skills should link to it and fix those two facts, not restate versions.

## Evidence (run folders)

- `runs/09-trade-settlement-tracker/20261124-201323`: `05-audit.json` flags `"mongoose": "^7.9.0"` with no lockfile; decision D003 marked "wrong" against published 9.x guidance; npm `ETARGET` in `events.jsonl`; `doc-gaps.md` first entry.
- `runs/03-core-banking-transaction-ledger/20261124-200452`: `decisions.jsonl` D003 (7.6.0), then D011 (7.9.3), then D016 (`^7.0.0` after npm failure).
- `runs/05-kyc-document-ingestion-pipeline/20261124-190500`: `doc-gaps.md` "Beanie + async client authoritative guidance (Motor vs AsyncMongoClient)"; `app/requirements.txt` beanie==1.16.4, motor==3.5.3.
- `runs/17-ai-survey-response-analyzer/20261124-205518`: `02-readiness.json` information_gaps "Beanie + Async driver compatibility matrix" and "Exact Beanie initialization snippet for DocumentDB"; `app/requirements.txt` beanie==1.24.0, motor==3.1.1, pymongo==4.6.0.
- `runs/17-rare-disease-literature-search/20261124-195633`: `02-readiness.json` "LlamaIndex and DocumentDB connector compatibility and version pins"; `app/requirements.txt` llama-index>=0.9.0, pymongo>=4.5.

## Verification

### 1. Already covered? partially_covered

The facts exist on Learn, but spread across individual ODM quickstarts. No single matrix exists, and the pages agents actually read have none of it.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-mongoose: "This quickstart was tested with MongoDB Node.js driver 7.8.0, a dependency of Mongoose 9.12.1."
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-beanie: "This quickstart was tested with Beanie 2.2.0 and PyMongo 4.19.0." Also: "This example uses Beanie 2 and PyMongo's asynchronous client, not Motor."
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-django: tested with Django MongoDB Backend 6.1.0 and PyMongo 4.19.0.
- https://learn.microsoft.com/en-us/azure/documentdb/compatibility-features (updated 2026-05-22): only aggregation stages, command categories and collection features; no driver table.
- https://learn.microsoft.com/en-us/azure/documentdb/managed-service-compatibility: no driver or server-version list.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python: "Python 3.12 or later", `pip install pymongo` unpinned, sync `MongoClient` only.
- https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs: "Node.js 22 or newer", `npm install mongodb` unpinned.
- https://learn.microsoft.com/en-us/azure/documentdb/query-knowledge-base: unpinned `pip install`; 0.9.0 is mentioned only in behavior notes.
- https://learn.microsoft.com/en-us/azure/documentdb/how-to-connect-role-based-access-control: OIDC callback code with no driver minimum.
- TOC (https://learn.microsoft.com/en-us/azure/documentdb/toc.json): the *Compatibility* node has no drivers page.
- Agent kit: `skills/connection/SKILL.md` lines 42-49 cover AsyncMongoClient vs Motor only. There is nothing on Beanie, Mongoose or pins in `skills/` or `knowledge-base/`.

### 2. Premise true? confirmed (with factual corrections applied)

The core premise holds: there is no consolidated matrix, and the quickstart versions are as the draft quoted. Corrections applied to the body:
- The original draft said "PyMongo 4.9 minimum for `AsyncMongoClient`". The PyMongo release notes say 4.9 "Adds a new experimental asynchronous API ... This API is in beta", and 4.13 says "The PyMongo Async API is generally available". The table and the sync/async paragraph now give 4.13 as the production minimum (https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/release-notes/).
- The original draft said "Motor is deprecated (MongoDB, May 2024)". MongoDB's migration guide says Motor "will be deprecated on May 14th, 2026" (https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/). The body now uses that date, and the agent-kit follow-up notes that the kit's "May 2024" and "4.9+" also need fixing.
- The original draft had "Wire protocol 5.0 to 8.0" in the table. No Learn page checked lists the selectable MongoDB compatibility versions (the quickstarts only say to select 8.0). That claim was replaced with neutral wording plus a *confirm* request.
- The Django row was filled in from the Django quickstart (6.1.0 / Django 6.1.3 / PyMongo 4.19.0) instead of *confirm*.
- `quickstart-python` "Python 3.12 or later" and `quickstart-nodejs` "Node.js 22 or newer" were confirmed verbatim. The `quickstart-nodejs` pin step was added because that page is also unpinned.
- Spot-checked the run evidence: 05-kyc and 17-ai-survey `requirements.txt` (Beanie 1.x + Motor), 17-rare-disease (llama-index>=0.9.0, pymongo>=4.5), 09-trade audit (`mongoose ^7.9.0`, `ETARGET` in events). Not every per-sample count in "Why it matters" was re-verified, so the absolute "all 12 / all 14" wording was softened.

### 3. Maintainer skeptic: confirmed

A MicrosoftDocs (nosql-docs-pr, `azure/documentdb/`) maintainer would accept this. It names the exact pages and anchors, gives a concrete table schema with values already published on Learn, and asks for specific pin lines in three pages. It is specific to Azure DocumentDB (cosmosSearch LlamaIndex wrapper, MONGODB-OIDC on the service, the service's quickstarts). Cells marked *confirm* are ones only the docs team can verify. The agent-kit change is correctly split out as a follow-up for Azure/documentdb-agent-kit.

## Finding ids

- F0124
- F0158
- F0268
- F0294
- F0360
- F0398
- F0466
- F0508
- F0736
- F0804
- F0927
- F1010
- F1053
- F1084
- F1141
- F1174
- F1208
- F1383
- F1414
- F1499
- F1570
- F1635
- F1666
- F1694
- F1730
- F1804
- F1869
- F1963
- F2029
- F2226
- F2337
- F2435
- F2529
- F2817
- F2819
- F2886
- F2950
- F3156
- F3239
- F3307
- F3401
- F3439
