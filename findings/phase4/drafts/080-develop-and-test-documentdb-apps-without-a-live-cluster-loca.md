---
title: "Add a Learn page \"Test your Azure DocumentDB application\" (offline unit tests, local-container integration tests, secrets-free CI) and link it from the development-loop tutorial and the Node.js and Python quickstarts"
repo: learn-docs
type: learn-feedback
status: ready_with_edits
priority: P1
sample_count: 58
findings: 61
bucket: learn-doc_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add "Test your Azure DocumentDB application" how-to page and link it from the development-loop tutorial and the Node.js and Python quickstarts

**Proposed URL:** `https://learn.microsoft.com/en-us/azure/documentdb/how-to-test-application` (new page, Python and Node.js pivots)
**Link from:** the existing tutorial `development-loop` ("Build a TypeScript app with DocumentDB and deploy to Azure"), `quickstart-python` and `quickstart-nodejs` (new "Test your application" next-step link), and the hub page's *Developer and DevOps guides* section.

## What happens today

Learn already has one page on local development: the tutorial [`development-loop`](https://learn.microsoft.com/en-us/azure/documentdb/development-loop). It shows how to pull and run the `ghcr.io/documentdb/documentdb/documentdb-local` container on port 10260 and connect with `tls=true&tlsAllowInvalidCertificates=true`, then switch the connection string to an Azure cluster. That tutorial is not linked from the hub page or from the quickstarts, and it says nothing about tests. It has no unit tests, mocks, test database, test gating or CI job, and its sample code hard-codes the connection string and creates the `MongoClient` at module load, which is the pattern that makes code hard to unit-test.

The hub page lists quickstarts, vector search, IaC, connection tools and security, but has no testing or local-development entry. `quickstart-python` and `quickstart-nodejs` go from creating a cluster, through the code examples and an "Explore your data using Visual Studio Code" section, to "Clean up resources". They never mention tests, mocks, Docker or CI. `/azure/documentdb/how-to-develop-locally` returns 404. Outside Learn, documentdb.io (DocumentDB Local) and the `documentdb-local-deployment` skill of Azure/documentdb-agent-kit cover the container. The skill's `local-prod-parity` rule says integration tests target the local Gateway container rather than an in-memory MongoDB, but it covers only the integration tier. No source shows the unit-test tier: how to mock `get_db()`, fake a Motor/Beanie client, stub Mongoose models, or produce deterministic test embeddings without an OpenAI key.

## Why it matters

An experiment built 100 Azure DocumentDB sample apps with gpt-5-mini, the Agent Kit skills and the DocumentDB, Azure and Learn MCP servers. In it, **58 of 100 samples** (61 audit findings) hit this gap:

- **No tests at all**, or `"test": "echo placeholder"` in package.json (for example 08-personalized-email-campaign-builder, 09-trade-settlement-tracker, 11-correspondent-banking-risk-screener).
- **Tests that need a live cluster and a real embedding key** (12-clv-prediction-pipeline, 08-dynamic-segmentation-engine, 13-algorithmic-trade-journal), or tests that **skip entirely when `DOCUMENTDB_URI` is absent**, so CI passes with zero assertions (14-telehealth-session-summarizer, 10-drug-formulary-semantic-search).
- **Beanie tests that call `init_db([Model])` inside the test**, which needs a reachable cluster (14-loan-origination-workflow-orchestration).
- **A false negative from a fragile mock:** `fake_db.__getitem__.side_effect = lambda name: ... else MagicMock()` returned a new mock on each access, so `fake_db['stress_runs'].insert_one.called` was always False (17-stress-testing-multi-agent-runner).
- **README and tests out of sync:** mongodb-memory-server failed to spawn `mongod` (spawn error -86), the builder silently switched to Jest mocks, and the README still says the tests use mongodb-memory-server (06-collateral-management-store).
- Builders repeatedly reached for a plain `mongo` image on port 27017 instead of the DocumentDB container. Local tests can then pass while `cosmosSearch` vector queries and the DocumentDB `createIndexes` payload fail on the real cluster (08-regulatory-compliance-rag-checker, 01-patient-record-summarizer-rag).
- Builders invented deterministic pseudo-embeddings from prior knowledge, with no guidance that they are a test-only device, so nothing stops them leaking into seed data (10-support-ticket-rag-assistant, 02-ai-powered-product-recommendations).

Agents searched Learn for "DocumentDB unit tests mongomock", "test without live cluster" and "local gateway port 10260". None of them reached a page with testing guidance, and the development-loop tutorial, which the hub page does not link, was not found or cited. One discoverable page, cross-linked from the existing tutorial, would address all of these at once.

## Proposed page content

### Tier 1: Unit tests that run offline (no cluster, no API key)

State the rule up front. **Put the client behind one factory (`get_db()` / `getDb()`), create it lazily, read the URI from an environment variable, and never connect at import time.** For Beanie, never call `init_beanie` at module import. Wrap it in an `async def init_db()` that the app calls at startup and unit tests do not. The development-loop tutorial's `app/data.tsx` builds `new MongoClient(...)` at module scope, so link to this rule from that tutorial as well.

Python / PyMongo (pytest + mongomock):

```python
# tests/conftest.py
import mongomock, pytest
import app.db

@pytest.fixture
def db(monkeypatch):
    client = mongomock.MongoClient()
    monkeypatch.setattr(app.db, "get_client", lambda: client)
    return client["sample_test"]
```

Python, one mock per collection (when you only need call assertions; this avoids the `__getitem__` pitfall):

```python
from unittest.mock import MagicMock
def fake_db(*names):
    cols = {n: MagicMock(name=n) for n in names}
    db = MagicMock()
    db.__getitem__.side_effect = cols.__getitem__   # same mock every access
    return db, cols
db, cols = fake_db("positions", "stress_runs")
cols["stress_runs"].insert_one.assert_called_once()
```

Python / Motor + Beanie: show `init_beanie(database=AsyncMongoMockClient()["sample_test"], document_models=[...])` from the `mongomock-motor` package inside an `@pytest_asyncio.fixture`, plus pure Pydantic model tests that never initialise Beanie. Note the version caveat: newer Beanie releases are built on PyMongo's async API rather than Motor, so check that the mock client matches the Beanie version the sample pins, or fall back to model-only tests plus Tier 2.

Node / mongodb driver and Mongoose (Jest):

```js
// tests/unit/orders.test.js
jest.mock("../../src/db", () => ({ getDb: jest.fn() }));
const { getDb } = require("../../src/db");
const insertOne = jest.fn().mockResolvedValue({ insertedId: "x" });
getDb.mockResolvedValue({ collection: () => ({ insertOne }) });
```

Add a Mongoose variant (`jest.spyOn(Order, "findOne")`). mongodb-memory-server can be mentioned as an optional variant only. Say that it downloads and spawns a real `mongod`, which may fail on some platforms, and that it is not a DocumentDB parity target (consistent with the Agent Kit's `local-prod-parity` guidance). Tell readers to provide a mocks fallback and to state in the README which one CI uses.

Deterministic test embeddings (shared by both pivots):

```python
import hashlib, math
def fake_embed(text: str, dims: int = 1536) -> list[float]:
    """Unit-test/CI device only. Never use for seed data or production vectors."""
    h = hashlib.sha256(text.encode()).digest()
    v = [((h[i % len(h)] / 255.0) * 2 - 1) for i in range(dims)]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]            # number[]; BSON binary vectors are not indexed
```

Mock the OpenAI, Azure OpenAI or LangChain embedding client to return these vectors. Make `dims` match the `dimensions` of the sample's `cosmosSearch` index. Assert ranking and prompt-assembly logic, not vector quality.

**What Tier 1 cannot exercise** (state this plainly): `explain()`, index creation and `createIndexes` validation, `cosmosSearch` vector search and `$search` text search, multi-document transactions, change streams, and SCRAM/TLS connection behaviour. mongomock rejects or ignores these. mongodb-memory-server runs a real `mongod`, which has none of the DocumentDB-specific stages.

### Tier 2: Integration tests against the local DocumentDB container

Reuse and link the container setup from the `development-loop` tutorial rather than restating it differently. For tests, pin the image tag and bind to loopback:

```bash
docker run -d --name documentdb -p 127.0.0.1:10260:10260 \
  -e USERNAME="${DOCUMENTDB_USERNAME:?}" -e PASSWORD="${DOCUMENTDB_PASSWORD:?}" \
  ghcr.io/documentdb/documentdb/documentdb-local:<pinned-tag>
```

```yaml
# docker-compose.test.yml
services:
  documentdb:
    image: ghcr.io/documentdb/documentdb/documentdb-local:<pinned-tag>
    ports: ["127.0.0.1:10260:10260"]
    environment:
      - USERNAME=${DOCUMENTDB_USERNAME:?}
      - PASSWORD=${DOCUMENTDB_PASSWORD:?}
```

Notes for the page:

- Credentials can be passed either as `-e USERNAME` / `-e PASSWORD` or as `--username` / `--password` container arguments (the form the development-loop tutorial uses). The password is required.
- Sample data is off by default (`INIT_DATA=false`). `SKIP_INIT_DATA` is only a legacy alias, so tests don't need to set it. Use `INIT_DATA_PATH` to mount the repo's `schema/` scripts.
- Wait for the "DocumentDB is ready" log line before running tests. `docker ps` reports `Up` before the gateway accepts connections.

`.env.example` entry: `DOCUMENTDB_URI=mongodb://<user>:<password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256`. Note that `tlsAllowInvalidCertificates` is only for the self-signed local certificate and must be driven by the environment, never by a code default. The alternative is to copy the generated certificate out of the container and pass `tlsCAFile`. Cloud connections keep the `mongodb+srv://...mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000` shape from the quickstarts.

**Warning box:** a plain `mongo:*` image on port 27017 is not a substitute. It lacks `cosmosSearch` indexes (`vector-ivf`, `vector-hnsw`, `vector-diskann`), the DocumentDB `createIndexes` option shape and DocumentDB text-search behaviour, so tests that pass there can fail on Azure DocumentDB. The local container runs the same open-source DocumentDB engine, but feature parity with the managed service is not guaranteed for every index kind or option. Link the DocumentDB feature-support documentation and list any vector index kinds that are not available locally. Pin the image tag in CI.

### Tier 3: Live-cluster tests, gating and CI

- Use a separate database named `<sample>_test`. Provide `tests/seed_test_db.py` / `tests/seedTestDb.js` to upsert fixtures, and a teardown that drops only that database.
- Gating: run pytest with `-m "not integration"` by default. Mark integration tests with `@pytest.mark.integration` and have them `pytest.skip` **with a visible reason** when `DOCUMENTDB_URI` is unset, and fail rather than skip when `CI_REQUIRE_INTEGRATION=1`. For Jest, use `projects: [unit, integration]` with `testPathIgnorePatterns` driven by the same variable.
- Scripts: `test:unit` (offline, and the default for `npm test` / `pytest`), `test:integration` (local container or cluster), and an optional `test:stress` concurrency check (`Promise.all` / `asyncio.gather` of N writes, asserting no oversell and no duplicate ledger entries).
- CI: one GitHub Actions job with **no Azure secrets** that runs `test:unit` on every pull request, and a second job that starts the pinned DocumentDB container as a service container (credentials from non-production CI variables) and runs `test:integration`.
- README template text for the *Testing* section, including this fallback sentence: "Unit tests use mocks and run offline; if mongodb-memory-server cannot spawn `mongod` on your platform, the suite falls back to mocks automatically."
- Closing table of what still needs a live Azure DocumentDB cluster: index verification (`listIndexes` shape, `cosmosSearch` options), vector and text search parity, `explain()` plans, and Microsoft Entra ID auth paths.

## Why Learn rather than only the Agent Kit

Learn already owns the local-container story through the `development-loop` tutorial. The new page should extend it with the testing tiers, and the tutorial should link to the page. The Agent Kit's `documentdb-local-deployment` skill already carries the container recipe and should link to this page from `local-prod-parity.md` rather than duplicate it. The readiness pipeline's build template and the sample-prompt template should reference the page as the source of the "tests pass without a live cloud resource" expectation. Builders in this experiment searched Learn first, and so do people, and the quickstarts are the entry point for every language. That makes the page plus the quickstart and tutorial links the fix with the widest reach.

## Evidence (run folders, 100-sample experiment)

- `runs/14-loan-origination-workflow-orchestration/20261124-191837/05-audit.json`: requirement "Unit tests run without a live cluster" is not_met. `app/tests/test_model.py:5-10` calls `init_db([LoanApplication])`, which needs a reachable cluster.
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/doc-gaps.md`: `__getitem__.side_effect` returned a fresh `MagicMock` on each access, which caused a false-negative unit test.
- `runs/06-collateral-management-store/20261124-200922/events.jsonl`: mongodb-memory-server failed to spawn (`spawn Unknown system error -86`), the tests switched to Jest mocks, and the README still claims memory-server.
- `runs/14-telehealth-session-summarizer/20261124-195137/05-audit.json`: `tests/test_smoke.py` skips when `DOCUMENTDB_URI` is unset, and no mocked tests exist.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/doc-gaps.md`: the builder noted that `mongo:latest` on 27017 is not a parity substitute (no `cosmosSearch`) and found no Learn guidance.

Caveat on the evidence: the experiment's run-environment note told builders "no local DocumentDB gateway is running; build and verify against the live cluster", which pushed them away from Tier 2. That note did not cause the Tier 1 failures (missing mocks, import-time `init_beanie`, skip-on-missing-env, fragile MagicMock), and those failures make up most of the 61 findings.

## Verification

### 1. Already covered? partially_covered

- **Learn, local container: covered.** <https://learn.microsoft.com/en-us/azure/documentdb/development-loop> ("Tutorial: Build a TypeScript app with DocumentDB and deploy to Azure", updated 2026-11-23) documents `docker pull ghcr.io/documentdb/documentdb/documentdb-local:latest`, a `docker run --publish 10260:10260 ... --username <admin-username> --password <admin-password>` command, and the connection format `mongodb://<admin-username>:<admin-password>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true`. The original draft claimed that the local container was documented only on documentdb.io and in the Agent Kit. That was wrong, and the body now builds on this tutorial.
- **Learn, testing: not covered.** The development-loop tutorial has no tests, mocks, test database, gating or CI. The hub page <https://learn.microsoft.com/en-us/azure/documentdb/> does not link the tutorial and has no testing or local-dev entry. <https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python> has no testing, Docker or CI content; its sections run from cluster creation, through code examples and "Explore your data using Visual Studio Code", to "Clean up resources". The original draft said the quickstart went "straight to Clean up"; this is now corrected. `https://learn.microsoft.com/en-us/azure/documentdb/how-to-develop-locally` and `.../local-emulator` both return 404.
- **Agent Kit: integration tier only.** `skills/local-deployment/local-prod-parity.md` says: "Integration tests target the local Gateway container, not an in-memory MongoDB", and gives a compose file plus `npm run test:integration`. No file under `skills/` or `knowledge-base/` mentions mongomock, Jest or pytest unit fixtures, deterministic embeddings, or a secrets-free CI job.
- **documentdb-mcp:** not relevant; it has no testing guidance.

### 2. Premise true? confirmed (with technical corrections applied)

- The container image `ghcr.io/documentdb/documentdb/documentdb-local`, port 10260, the self-signed TLS certificate and `tlsAllowInvalidCertificates` are confirmed by Learn development-loop and by <https://documentdb.io/docs/documentdb-local/>.
- Correction: on documentdb.io, `INIT_DATA` defaults to `false` and `SKIP_INIT_DATA` is described as a "legacy alias for INIT_DATA=false". The draft's `SKIP_INIT_DATA=true` is therefore redundant, so it was removed from the snippets and replaced with a note.
- Correction: credentials work both as `-e USERNAME/PASSWORD` (documentdb.io, Agent Kit) and as `--username/--password` container arguments (Learn). Both are now noted.
- Correction: documentdb.io warns that `docker ps` shows `Up` before the gateway accepts connections, and that you should wait for the ready banner. A readiness-wait note was added. Its examples pin a tag (`pg17-1.2.0`), so the snippets now use `<pinned-tag>` instead of `:latest`.
- Hedge added: documentdb.io does not state which vector index kinds the local container supports. The draft no longer implies full `cosmosSearch` parity locally and asks the page to list the gaps.
- Hedge added: newer Beanie releases use PyMongo's async API instead of Motor, so `mongomock_motor` compatibility depends on the Beanie version.
- Hedge added: mongodb-memory-server conflicts with the Agent Kit's parity rule, so it is now described as optional and not a parity target.
- Unchanged: the cloud connection-string shape, `number[]` vectors (BSON binary vectors are not indexed), and the fact that a plain `mongo` image lacks `cosmosSearch` all match the service facts.
- The scale figures (58 distinct samples, 61 findings, all from audit) were recounted from the findings records.

### 3. Maintainer skeptic? confirmed

As a maintainer of the Azure DocumentDB Learn docs (MicrosoftDocs/nosql-docs-pr), I would accept this with the edits applied. It names a concrete new page and URL, specific link points (development-loop, quickstart-python, quickstart-nodejs and the hub), and concrete content. It also has a real Azure DocumentDB angle: the local DocumentDB container rather than a generic `mongo` image, the `cosmosSearch` and `createIndexes` parity warning, and the connection-string and TLS differences between local and cloud. Generic Tier 1 mocking material should stay short and serve the DocumentDB-specific tiers. The Agent Kit and pipeline cross-links are follow-ups in other repos, not part of this ask.

## Finding ids

- F0020
- F0026
- F0061
- F0098
- F0099
- F0200
- F0580
- F0619
- F0649
- F0679
- F0717
- F0746
- F0816
- F0836
- F0872
- F0904
- F0931
- F0959
- F0987
- F1026
- F1089
- F1153
- F1212
- F1285
- F1317
- F1354
- F1421
- F1452
- F1577
- F1607
- F1645
- F1700
- F1703
- F1773
- F1815
- F1849
- F1911
- F1937
- F2004
- F2036
- F2071
- F2106
- F2138
- F2206
- F2233
- F2267
- F2443
- F2476
- F2574
- F2608
- F2702
- F2732
- F2763
- F2797
- F2829
- F2963
- F3059
- F3091
- F3200
- F3343
- F3447
