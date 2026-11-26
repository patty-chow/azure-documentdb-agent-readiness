---
id: K23
title: "local-deployment skill: steer agents away from the Cosmos DB Emulator, add a gateway quick start, offline test tiers, and an idempotent seed and bulk-load rule"
repo: Azure/documentdb-agent-kit
type: pr
status: ready
priority: P1
sample_count: 55
member_drafts:
  - 030-believes-the-azure-cosmos-db-emulator-ports-8081-10250-10255.md
  - 059-local-documentdb-gateway-container-is-never-started-surface-.md
  - 091-offline-test-harness-mocked-unit-tests-env-gated-integration.md
  - 052-no-offline-vs-live-test-strategy-for-generated-samples-mocks.md
  - 103-seed-and-batch-load-scripts-are-per-document-loops-not-idemp.md
  - 053-documentdb-local-deployment-skill-lacks-an-idempotent-seed-s.md
merged_from:
  - K23
  - K09
  - K08
  - K26
open_questions: 7
---

# local-deployment skill: steer agents away from the Cosmos DB Emulator, add a gateway quick start, offline test tiers, and an idempotent seed and bulk-load rule

This PR makes `skills/local-deployment` the single place an agent goes to run, test and seed Azure DocumentDB locally. It has four parts: a "Not this" disambiguation against the Azure Cosmos DB Emulator and stock MongoDB (from K23), a runnable gateway quick start reachable from `AGENTS.md` and `mcp-setup` (K26), a two-tier offline/integration test rule (K09), and an idempotent seed and bulk-load rule with reference seed scripts (K08). The bulk-load rule lives in `skills/driver/`, which the K07 connection/driver PR also edits; coordinate the `skills/driver/SKILL.md` Rules list with that PR.

## What happens today

`skills/local-deployment/SKILL.md` names the right image (`ghcr.io/documentdb/documentdb/documentdb-local`, MongoDB wire protocol on port **10260**, TLS with a self-signed certificate, SCRAM-SHA-256) and links seven rule files: choose-deployment-method, connection-config, docker-compose-setup, env-driven-config, ports-and-bindings, prod-parity and sample-data-management. Its description says "Use when ... building integration tests". Four gaps remain.

**1. Nothing says what *not* to use (K23).** `grep -rniE 'emulator|cosmos|10255|8081|27017' skills/local-deployment` returns nothing, and `grep -rni emulator skills knowledge-base` returns nothing (checked at commit `4f41c15`). An agent's default answer is carried over from Azure Cosmos DB (NoSQL) and Azure Cosmos DB for MongoDB (RU): the **Azure Cosmos DB Emulator** (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`, endpoint `localhost:8081`; the classic emulator can also expose a MongoDB (RU) endpoint, 10255 by default). Stating only the right answer does not displace that prior. Several kit files add to the confusion by labelling plain MongoDB on 27017 as "local DocumentDB":

- `skills/mcp-setup/SKILL.md` line 88, Step 2 option **B. Local MongoDB / DocumentDB** -> `mongodb://localhost:27017`
- `README.md` line 160 (`export DOCUMENTDB_LOCAL_URI='mongodb://localhost:27017'`), repeated in `GEMINI.md` line 27, `install.sh` lines 8/522/527, `install.ps1` lines 46/491 and `docs/installation/macos.md` line 21

**2. No runnable quick start, and nothing at the entry points routes to one (K26).** The runnable pieces are scattered: `docker run` is in `local-choose-deployment-method.md` ("Correct") and `local-ports-and-bindings.md`; `mongosh` and driver examples are in `local-connection-config.md`; teardown exists only as `docker compose down` in `local-docker-compose-setup.md` and the integration-test snippet in `local-prod-parity.md`.

- `AGENTS.md` "Routing hints" routes to the skill only on "Running DocumentDB locally", so an agent building a sample against a provisioned Azure cluster never gets there. (The only other `docker run` pointer in `AGENTS.md` is the Route A diagnostic toolbox via `docs/DIAGNOSTICS.md`.)
- `skills/mcp-setup/SKILL.md` Step 1 ("Confirm prerequisites") checks only `node --version` and `git --version`.
- `skills/mcp-setup/SKILL.md` Step 2 row B gives the 27017 community-MongoDB URI, not the 10260 gateway URI (which needs TLS and SCRAM credentials).
- `skills/connection/SKILL.md` never mentions a local target.
- Microsoft Learn's only local page is the development-loop tutorial (https://learn.microsoft.com/en-us/azure/documentdb/development-loop, updated 2026-11-23): it runs `ghcr.io/documentdb/documentdb/documentdb-local:latest` with no versioned-tag guidance and says nothing about which cluster features the container lacks; the older `oss` page (updated 2026-04-27) still builds from source and connects with psql on 9712. Neither page covers tests or seeding, so the kit is the right home for this (the Learn gaps are tracked in the Learn filings).

**3. No test-tier convention (K09).** The only testing guidance is one bullet in `local-prod-parity.md` ("Integration tests target the local Gateway container, not an in-memory MongoDB") plus a four-line `docker compose up -d documentdb / ./wait-for-port.sh 10260 / npm run test:integration / docker compose down` snippet. No skill or knowledge-base file mentions pytest, jest, mocks or markers. Nothing tells an agent:

- how to write a unit test that needs no cluster and no AI key (a stubbed collection, a fake embedder, LLM or web-search client);
- how to keep connects out of import time, so `import app` does not need `DOCUMENTDB_URI`;
- how to gate integration tests on `DOCUMENTDB_URI` so they are skipped, not failed, when it is unset, and how CI runs the two tiers separately;
- how to isolate test data (a per-run database dropped on teardown);
- which DocumentDB features (`cosmosSearch` vector search, `createSearchIndexes` / `$search`, DocumentDB index options, TTL expiry, `explain`) cannot be mocked and belong in the integration tier, and which of those the local container cannot run at all (full-text `$search`, DiskANN, product quantization, change streams, Entra ID; see Resolved) and therefore need an Azure cluster.

The kit's own `testing/conftest.py` already uses a skip-when-no-container fixture, but that is the kit's eval harness, not a rule agents load.

**4. No seed or bulk-load pattern, and the one example is not idempotent (K08).**

- `skills/local-deployment/local-sample-data-management.md` says "Idempotent scripts only", but its own *Correct* example is an `insertMany` with fixed `_id: 1` / `_id: 2`. Run a second time against a populated database (a manual `mongosh` run, CI, or the same code reused as an app seed) it fails with E11000. The image's own sample data is opt-in (`--init-data true` / `INIT_DATA`; `SKIP_INIT_DATA` is a legacy alias for `--init-data false`) and is the StoreData set (stores, ratings), not the `sampledb` (users, products, orders, analytics) that the same rule file claims is seeded by default, so the problem is the pattern the example teaches, not the container.
- `skills/driver/SKILL.md` has one rule (`driver-singleton-client`), and its description does not mention seeding or bulk loading, so an agent writing `seed.py` has no reason to open it.
- A grep of `skills/` and `knowledge-base/` for `bulkWrite`, `bulk_write`, `insert_many`, `writeErrors` or `allowDiskUse` returns no hits, and `insertMany` appears only in that one example. Nothing covers chunking, natural-key upserts, partial-failure handling, index ordering, a sample fixture with a licence, or demo dataset size.
- `scenarios/contoso/contoso-seed.js` already follows the right contract (resumable, seeded PRNG, opt-in drop), but no skill links to it. `scenarios/ecommerce/seed.sh` drops collections every run and uses unseeded `Math.random()`.
- Microsoft Learn has no Azure DocumentDB bulk-write page (`.../azure/documentdb/how-to-optimize-write-performance` and `.../best-practices` return 404). Agents land on the request-unit-based Cosmos DB page and copy its "RU charge" wording; Azure DocumentDB capacity is sized by vCore tier, not request units.

## Why it matters

We ran gpt-5-mini on 100 Azure DocumentDB sample-app prompts with this kit installed and the DocumentDB, Azure and Learn MCP servers available (120 run logs including reruns). **55 distinct samples** are covered by this PR. All figures come from that single experiment run and may move on a re-run after the harness fixes; re-baseline before quoting them externally. The union was recounted from the member drafts' finding lists (K23, K26, K09) and evidence paths (K08); the per-member counts overlap on 13 samples.

- **Emulator / 10255 carry-over: 22 samples (K23).** Before each build the agent answered a cold, tool-free question: "How do you run the database locally for development and tests: which image or emulator, and which port?" Nearly every sample answered wrongly; the grader logged a finding in 22 where the miss traced to the emulator or 10255 (a keyword recount gives 23, so treat the number as approximate). The cold quiz measures model priors, not a defect in kit content. Typical answers: "Use the Azure Cosmos DB Emulator ... connect to localhost with the Mongo port used by Cosmos (10255) and with TLS enabled" and "Use the Azure Cosmos DB Emulator; SQL API at https://localhost:8081; Cosmos Mongo emulator endpoint common is 10255". When the agent looked things up first it mostly gave the correct 10260 gateway answer, often citing this skill: the content is right, it only lacks the negative statement.
- **Gateway never started: 15 samples (K26).** The readiness review flagged "local DocumentDB gateway not running" as a missed accelerator in 15 samples (indicative only: part of this signal is a harness artifact, see Open questions). The agent loaded `documentdb-local-deployment` in several builds and still never started the container; across all 120 `events.jsonl` logs no command the agent ran invoked `docker`. When agents wrote a local command into their reports they improvised: several suggested a community `mongo:6.0` / `mongo:7` container on 27017, and the one that used the gateway image omitted credentials (the image requires `PASSWORD`). Every integration test and index-iteration cycle ran against the shared Azure cluster.
- **No offline test tier: 16 samples (K09).** 16 samples raised the missing test convention as a doc gap. Across 117 audited runs, "Unit tests run without a live cluster" was not met in 65 and only partly met in 6. Without a pattern the agent wrote:
  - live-cluster "unit" tests with no guard (`06-order-history-timeline-agent` seeds and counts against whatever `DOCUMENTDB_URI` resolves to; `01-anti-money-laundering-pattern-detector` calls `get_db()` and assumes a seed already ran; `11-preference-center-consent-store` imports the app at module scope, which triggers `init_beanie`; all three fail on a clean checkout);
  - mixed tiers (`08-regulatory-compliance-rag-checker` has a mongomock test and a live test in one folder with no marker);
  - placeholder or missing tests (`03-next-best-action-multi-agent` asserts only `callable(orchestrate)`; `20-identity-resolution-multi-agent` tests only a Pydantic model; `04-customer-journey-mapper` tests only `buildPrompt`; `13-basel-iii-capital-ratio-calculator` skips everything and imports a class that does not exist; `05-churn-prediction-pipeline` and `17-seasonal-trend-spotter-agent` ship no tests);
  - claimed coverage that does not exist (`18-adverse-event-reporting-pipeline`'s README says pytest runs unit tests, but there is no `tests/` directory).
  The result is CI that fails without secrets, or passes without testing anything.
- **Non-idempotent or slow seeds: 15 samples (K08).** Every prompt asked for a seed that loads data, creates the index and can run twice without duplicating data. 12 samples show a concrete seeding or bulk-load defect in their run folders, and 3 more (an earnings-call RAG assistant, a store locator and a customer-journey mapper) report that no skill gave them a seed dataset, licence, dataset size or chunk-id scheme. The model reached for `upsert: true` but:
  - wrote loops of single `update_one` / `replace_one` / `save()` calls (one sample made 5,000 single upserts);
  - mixed upserts with plain inserts or random ids, so every rerun added duplicates (an ATM monitor upserted status documents but created a new heartbeat on every run);
  - created every secondary index before the load;
  - caught `MongoBulkWriteError` and dropped `writeErrors`;
  - iterated nightly jobs over `find({})` with no batch size or resume marker;
  - seeded destructively with no check on the database name;
  - toggled `allowDiskUse` on a faceted aggregation expecting it to change memory behaviour (the service accepts and ignores the option; see Resolved).
  Every builder invented its own idempotency contract and dataset size (5 stores, 20 ATMs, 500 to 2,000 events). A seed is usually the first thing a developer runs against a new cluster; if it is slow or doubles its data, the service looks broken.

The common consequence: the emulator does not run the PostgreSQL-based open-source DocumentDB engine, so it has no `cosmosSearch` vector indexes (vector-ivf, vector-hnsw, vector-diskann), no DocumentDB text-search indexes and none of the gateway's TLS/SCRAM-SHA-256 behaviour; port 10255 belongs to Cosmos DB for MongoDB (RU). Azure DocumentDB uses 10260 locally and a `mongodb+srv://...mongocluster.cosmos.azure.com/` string with no explicit port in the cloud. An agent that follows its prior either cannot connect, or gets a local environment whose indexes differ from the cluster's, never starts it at all, writes tests that need the cluster, and seeds data that doubles on rerun.

## Proposed change

Each kit file appears once below, with all edits combined.

### 1. `skills/local-deployment/SKILL.md`

**(a) Front-matter `description`.** Append (K23, K09 and K08 combined):

```
... or diagnosing local connection problems. Also covers a one-shot gateway quick start, a two-tier test layout (offline unit tests, DOCUMENTDB_URI-gated integration tests), idempotent seed scripts and demo dataset sizing. Also use when someone proposes the Azure Cosmos DB Emulator, port 10255/8081, or a stock mongo:* image for Azure DocumentDB local development -- those are not DocumentDB.
```

**(b) New section above the "Image choices:" list (K26).**

````markdown
## Quick start (local dev loop)

Use this when Docker is present and you are writing a sample, running integration tests, or iterating on indexes. It avoids round-trips to the Azure cluster until the code is stable.

```bash
# 1. run (loopback only, named so teardown is one command). :latest is fine for a copy-paste
#    dev loop; in CI and compose files use a versioned tag (pg15-1.2.0 .. pg18-1.2.0; latest
#    and 1.2 point to pg17-1.2.0 as of DocumentDB 1.2, 2026-11-12), see local-prod-parity.
docker run --pull always -dt --name documentdb-local \
  -p 127.0.0.1:10260:10260 \
  -e USERNAME=docdbuser -e PASSWORD="${DOCUMENTDB_PASSWORD:?set DOCUMENTDB_PASSWORD}" \
  ghcr.io/documentdb/documentdb/documentdb-local:latest

# 2. verify (self-signed cert, so allow invalid certs locally only)
mongosh "mongodb://localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256" \
  -u docdbuser -p "$DOCUMENTDB_PASSWORD" --eval 'db.runCommand({ ping: 1 })'

# 3. connection string for the app (read from env, never hard-code)
export DOCUMENTDB_URI="mongodb://docdbuser:${DOCUMENTDB_PASSWORD}@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256"

# 4. teardown
docker rm -f documentdb-local
```

(`-e USERNAME/-e PASSWORD` and the `--username/--password` arguments after the image name are equivalent; the CLI arguments override the env vars. `authMechanism=SCRAM-SHA-256` is optional: the gateway advertises only SCRAM-SHA-256, so drivers negotiate it; Learn's development-loop tutorial gives the string without it. The image default is `--tlsMode allowTLS`, which accepts plain and TLS connections; `tls=true` with `tlsAllowInvalidCertificates=true` is still the right local setting because the certificate is self-signed, and `tlsAllowInvalidCertificates` must never reach an Azure URI.)

**Parity caveats vs Azure DocumentDB:** the local gateway speaks the same wire protocol, so the same driver code should work by swapping `DOCUMENTDB_URI` between this and the cluster's `mongodb+srv://...mongocluster.cosmos.azure.com` string. It is a single-container dev engine: one SCRAM admin user, no vCore tier sizing, HA/replication, firewall, `az documentdb mongocluster` or portal features. What runs locally: CRUD, aggregation, `explain`, TTL, multi-document transactions with the default read concern, and `cosmosSearch` vector indexes of kind `vector-ivf` and `vector-hnsw` up to 2,000 dimensions (4,000 with `compression: "half"`). What needs an Azure cluster: `vector-diskann` and product quantization (`pq`, 16,000 dimensions); full-text search (`createSearchIndexes` / `$search` with text operators: the local gateway returns code 115 "Command 'createSearchIndexes' not supported."; on Azure it is a preview that must be enabled per cluster); change streams (`$changeStream` returns code 115 locally; open-source issue documentdb/documentdb#50); Microsoft Entra ID (MONGODB-OIDC); and `readConcern: snapshot` in transactions (rejected locally, issue documentdb/documentdb#736; accepted on the service). Some behaviour differs and a local test cannot catch it: `w` of 2 or more is accepted silently locally but rejected with `BadValue` on a cluster without HA; client-level `bulkWrite` (`MongoClient.bulk_write`) is refused by the driver locally (wire version 21), while on an 8.0 cluster (wire version 25) the driver sends it and it fails at run time with code 2; and `hello`/`buildInfo` report wire version 21 and 7.0.0 locally, against 25 and 8.0.0 on an 8.0 cluster (managed test, 2026-11-25). Run those against the Azure cluster before shipping. See [local-prod-parity](local-prod-parity.md) and [local-test-tiers](local-test-tiers.md).
````

Sources for the quick-start commands (K26): https://documentdb.io/docs/documentdb-local/ (port 10260 default, `PASSWORD` required, `--username/--password` supported, `--tlsMode allowTLS` default, no replication or failover, versioned tags `pg15-1.2.0` to `pg18-1.2.0` with `latest` and `1.2` pointing to `pg17-1.2.0`, "Use a versioned tag when you need a reproducible setup"), https://documentdb.io/docs/getting-started/release-notes-1.2, https://learn.microsoft.com/en-us/azure/documentdb/development-loop (canonical local string without `authMechanism`) and the github.com/documentdb/documentdb README; the kit's own `local-prod-parity.md` already says to version-pin the image. Sources for the parity list: https://documentdb.io/docs/reference/operators/aggregation/$vectorsearch/ (only `vector-hnsw` and `vector-ivf`; caps 2,000 / 4,000 / 16,000), https://documentdb.io/docs/reference/operators/aggregation/$search/ (`$search` is vector-only in the open-source engine), https://documentdb.io/docs/reference/operators/aggregation/$changestream/, engine source `pg_documentdb/src/vector/vector_index_kind_impl.c`, `pg_documentdb_gw/documentdb_gateway_core/src/postgres/data_client.rs` and `src/auth/manager.rs` (SCRAM-SHA-256 only), issues documentdb/documentdb#50 and #736, and https://learn.microsoft.com/en-us/azure/documentdb/limitations (HNSW and DiskANN need M30 or higher on Azure). See findings/phase4/DECISIONS.md, SME topic 12.

**(c) Under "Image choices", after the two existing bullets (K23).**

```markdown
- **Not this:** the **Azure Cosmos DB Emulator** (`mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator`, endpoint 8081, MongoDB (RU) endpoint 10255) or a stock `mongo:*` image on 27017. The emulator serves Azure Cosmos DB (NoSQL and RU-based API for MongoDB) accounts, not Azure DocumentDB; neither runs the DocumentDB engine, so `cosmosSearch` vector indexes, DocumentDB text-search indexes and the gateway's TLS/SCRAM-SHA-256 behaviour will be missing or different. Port 10255 belongs to Cosmos DB for MongoDB (RU); Azure DocumentDB uses 10260 locally and no explicit port in the cloud `mongodb+srv://` string.
```

**(d) `## Rules` list (K09, K08).** Keep the seven existing entries (including `local-docker-compose-setup`): compose stays the recommended committed form; the quick start is the one-shot an agent runs at setup time. Add one entry after `local-prod-parity`:

```markdown
- [local-test-tiers](local-test-tiers.md) — Offline unit tests with stubbed driver and fake embeddings/LLM; integration tests marked and skipped unless DOCUMENTDB_URI is set, run against the Gateway container with a disposable per-run database.
```

Append one sentence to the end of the existing `local-sample-data-management` entry (its text is otherwise unchanged): "For seed, import and batch-job code, see [driver-bulk-load-idempotent-seed](../driver/driver-bulk-load-idempotent-seed.md)."

### 2. `skills/local-deployment/local-choose-deployment-method.md` (K23)

Add a row to the decision matrix:

```markdown
| "Run it like Cosmos DB" (Azure Cosmos DB Emulator, port 10255) | **Do not.** The emulator is for Azure Cosmos DB accounts; use the Gateway image on 10260 |
```

Add a second **Incorrect** block:

````markdown
## Incorrect

Reaching for the Azure Cosmos DB Emulator or a plain MongoDB image because the service used to be called "Azure Cosmos DB for MongoDB vCore":

```bash
# Wrong product: emulates Azure Cosmos DB (NoSQL / RU API for MongoDB), not Azure DocumentDB
docker run -p 8081:8081 -p 10250-10255:10250-10255 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator

# Wrong engine: plain MongoDB, no cosmosSearch / DocumentDB text indexes
docker run -p 27017:27017 mongo:7
```

Neither exposes `cosmosSearch` vector indexes, DocumentDB text-search indexes, or the 10260 gateway's TLS + SCRAM-SHA-256 behaviour, so local tests do not predict cluster behaviour.
````

### 3. `skills/local-deployment/local-prod-parity.md` (K09)

Replace the "Test what prod does" bullet with: "Integration tests target the local Gateway container, not an in-memory MongoDB. Unit tests may stub the driver. See `local-test-tiers` for the gating and fixture pattern." Keep the existing version-pin guidance and make it concrete (the quick start's tag comment points here): name the current versioned tags (`pg15-1.2.0` to `pg18-1.2.0`; `latest` and `1.2` resolve to `pg17-1.2.0`) and say that `latest` has moved from 1.0 to 1.2 since the kit's examples were written. Add a short "Local vs cluster" list with the settled parity facts: available locally are `vector-ivf` and `vector-hnsw` (2,000 dimensions, 4,000 with `compression: "half"`), TTL, `explain` and transactions with the default read concern; cluster-only are DiskANN and `pq` compression (16,000 dimensions), full-text search (`createSearchIndexes` / `$search`, preview on Azure), change streams, Microsoft Entra ID and `readConcern: snapshot`; different on the cluster are `w` of 2 or more (rejected on a cluster without HA, accepted locally) and client-level `bulkWrite` (fails at run time there, refused by the driver locally). The kit's `vector-search` skill advertises DiskANN, product quantization and fp16 without this caveat, so this list is also where that skill should link.

### 4. New `skills/local-deployment/local-test-tiers.md` (K09)

Follows the existing rule template (Why it matters / Incorrect / Correct / References).

**Rules**
- **Two tiers, never mixed in one file or one unmarked folder.**
- **Tier 1, unit (always runs):** no network, no `DOCUMENTDB_URI`, no AI key. The driver is created lazily behind a small accessor or repository (or business logic takes the collection as a parameter), so tests can swap in a stub. Embedding, chat and web-search calls go through one function that tests replace with a deterministic fake (fixed-dimension vectors, canned completions). `mongomock` is fine for plain CRUD and aggregation *shapes*. It does not implement `cosmosSearch`, `$search` or DocumentDB index options.
- **Tier 2, integration (gated):** marked `integration` and skipped with a clear message when `DOCUMENTDB_URI` is unset. It runs against the local Gateway container (or an Azure DocumentDB cluster when the URI points there), never an in-memory MongoDB. The documented `.env.example` value points at the local Gateway on `127.0.0.1:10260` (see `local-connection-config` and the SKILL.md quick start). Anything DocumentDB-specific (`cosmosSearch`, `$search`, TTL, `explain`, transactions) lives here. The local container runs `cosmosSearch` `vector-ivf` and `vector-hnsw` (up to 2,000 dimensions, 4,000 with `compression: "half"`), TTL, `explain` and transactions with the default read concern. It does not run full-text search (`createSearchIndexes` returns code 115; `$search` accepts only `cosmosSearch` and rejects text operators with "Unrecognized $search option"), `vector-diskann`, `pq` compression, change streams, Microsoft Entra ID or `readConcern: snapshot`; tests for those carry a second marker (for example `azure_only`) and are skipped when the URI host is `localhost` / `127.0.0.1`, and full-text tests additionally expect code 115 ("Search index creation is not supported yet") when the cluster's full-text preview is not enabled (and the same message under 115 or 67 for a few minutes after it is enabled). Optionally, a `pytest_collection_modifyitems` hook in `conftest.py` adds a skip marker to every `integration` item when `DOCUMENTDB_URI` is unset, so tests that do not use the `test_db` fixture are skipped too.
- **Isolation:** each run uses `<sample>_test_<uuid8>` and drops it on teardown. Never test against the seed database.
- **TLS:** invalid-certificate tolerance is for the self-signed local Gateway only, never for an Azure cluster (see `local-env-driven-config`, `local-connection-config`).
- **README:** a "Testing without cloud" line, for example: "`pytest` runs offline unit tests; `pytest -m integration` needs `DOCUMENTDB_URI`." A README must not claim tests that the sample does not ship.

**Incorrect**
```python
from app.main import app            # import runs init_db() -> needs DOCUMENTDB_URI
def test_seed_and_queries():        # unmarked; hits whatever cluster the env points at
    db.seed_sample(size=10)
    assert db.get_orders_collection().count_documents({}) >= 10
def test_orchestrate():             # proves nothing
    assert callable(orchestrate)
```

**Correct: Python**
```python
# app/db.py: lazy, injectable
_client = None
def get_client():
    global _client
    if _client is None:
        from pymongo import MongoClient
        _client = MongoClient(os.environ["DOCUMENTDB_URI"])
    return _client
def get_collection(name): return get_client()[DB_NAME][name]
```
```ini
# pytest.ini
[pytest]
markers =
    integration: needs DOCUMENTDB_URI (local Gateway on 10260 or an Azure DocumentDB cluster)
```
```python
# tests/conftest.py
import os, uuid, hashlib, pytest

class FakeCollection:
    def __init__(self): self.docs = []
    def insert_many(self, docs): self.docs += docs
    def find(self, flt=None, *a, **k):
        return [d for d in self.docs if all(d.get(f) == v for f, v in (flt or {}).items())]
    def aggregate(self, pipeline, *a, **k):
        self.last_pipeline = pipeline        # assert on pipeline shape, not on results
        return iter(self.docs)

@pytest.fixture
def fake_collection(monkeypatch):
    col = FakeCollection()
    monkeypatch.setattr("app.db.get_collection", lambda name: col)
    monkeypatch.setattr("app.db.init_db", lambda *a, **k: None, raising=False)  # Beanie/Motor startup
    return col

class FakeEmbeddings:
    dim = 8   # hashlib, not hash(): str hashing is salted per process
    def embed(self, texts):
        return [[b / 255.0 for b in hashlib.sha256(t.encode()).digest()[:self.dim]] for t in texts]

@pytest.fixture
def fake_embeddings(monkeypatch):
    fe = FakeEmbeddings()
    monkeypatch.setattr("app.embeddings.embed", fe.embed, raising=False)
    return fe

@pytest.fixture(scope="session")
def test_db():
    uri = os.getenv("DOCUMENTDB_URI")
    if not uri:
        pytest.skip("integration: set DOCUMENTDB_URI (docker compose -f docker-compose.test.yml up -d)")
    from pymongo import MongoClient
    allow_invalid = os.getenv("DOCUMENTDB_ALLOW_INVALID_CERTS", "false").lower() == "true"
    client = MongoClient(uri, tlsAllowInvalidCertificates=allow_invalid)
    name = f"sample_test_{uuid.uuid4().hex[:8]}"
    yield client[name]
    client.drop_database(name)
    client.close()
```
```python
# tests/test_search.py (tier 1)
def test_vector_pipeline_shape(fake_embeddings):
    from app.search import build_vector_pipeline
    p = build_vector_pipeline(fake_embeddings.embed(["refund"])[0], k=3)
    assert p[0]["$search"]["cosmosSearch"]["k"] == 3

# tests/integration/test_orders.py (tier 2)
@pytest.mark.integration
def test_insert_and_find(test_db):
    repo = OrdersRepo(test_db["orders"])
    repo.insert({"order_id": "o1", "customer_id": "c1"})
    assert repo.find_by_customer("c1")[0]["order_id"] == "o1"
```

**Correct: Node (jest)**
```js
// src/db.js: lazy accessor
let client;
export async function getDb() {
  if (!client) { const { MongoClient } = await import("mongodb");
    client = new MongoClient(process.env.DOCUMENTDB_URI); await client.connect(); }
  return client.db(process.env.DB_NAME);
}
// tests/unit/orders.test.js
jest.mock("../../src/db.js", () => { const docs = [];
  const col = { insertMany: async d => docs.push(...d), find: () => ({ toArray: async () => docs }),
    aggregate: p => ({ toArray: async () => { col.lastPipeline = p; return docs; } }) };
  return { getDb: async () => ({ collection: () => col }) }; });
jest.mock("../../src/embeddings.js");
// tests/integration/*.test.js: skip the whole file without a URI
const describeIfLive = process.env.DOCUMENTDB_URI ? describe : describe.skip;
```
`package.json`: `"test": "jest tests/unit"`, `"test:integration": "jest tests/integration --runInBand"`. Jest has no `describe.skipIf` (that is Vitest). With ESM `export`, `jest.mock` needs `babel-jest` or `--experimental-vm-modules`.

**Correct: container and CI**
```yaml
# docker-compose.test.yml
services:
  documentdb:
    image: ghcr.io/documentdb/documentdb/documentdb-local:pg17-1.2.0   # versioned tag; bump deliberately (OSS docs: use a versioned tag for a reproducible setup)
    ports: ["127.0.0.1:10260:10260"]
    environment:
      - USERNAME=${DOCUMENTDB_USER:?}
      - PASSWORD=${DOCUMENTDB_PASSWORD:?}
      # the image's StoreData sample set is opt-in (INIT_DATA=true); leave it off, the tests seed their own per-run database
```
```yaml
- run: pytest -m "not integration"                       # always
- run: docker compose -f docker-compose.test.yml up -d && ./wait-for-port.sh 10260 && pytest -m integration
  env:
    DOCUMENTDB_URI: ${{ secrets.DOCUMENTDB_TEST_URI }}   # local Gateway: port 10260, tls=true, SCRAM-SHA-256
    DOCUMENTDB_ALLOW_INVALID_CERTS: "true"               # self-signed local cert only
- run: docker compose -f docker-compose.test.yml down
  if: always()
```
The URI comes from a secret and is never written inline. For its shape, the rule cross-links `local-connection-config`. Integration tests that need seeded data call the same idempotent seed function as the app (see `driver-bulk-load-idempotent-seed`) against the per-run database.

### 5. `skills/local-deployment/local-sample-data-management.md` (K08)

**(a)** Replace the `insertMany` *Correct* example with:

```javascript
// seed/10_data.js: safe to re-run, upserts on the natural key
const users = db.getSiblingDB('app').users;
users.createIndex({ userId: 1 }, { unique: true, name: 'users_userId_unique' });
users.bulkWrite([
  { replaceOne: { filter: { userId: 'u-ada' },   replacement: { userId: 'u-ada',   name: 'Ada' },   upsert: true } },
  { replaceOne: { filter: { userId: 'u-linus' }, replacement: { userId: 'u-linus', name: 'Linus' }, upsert: true } }
], { ordered: false });
print('users: ' + users.countDocuments());   // 2 on every run
```

**(b)** Under *Incorrect*, add: "`insertMany` with fixed `_id`s fails with E11000 on the second run. Without a unique key it silently doubles the data."

**(c)** At the "Idempotent scripts only" bullet, add: "See `driver/driver-bulk-load-idempotent-seed` for the full pattern."

**(d)** Add this section:

> **Sizing a demo dataset** (rules of thumb): CRUD, REST and change-stream demos use 20 to 100 documents. Aggregation and dashboard demos use 1,000 to 10,000, generated from a seeded PRNG. Vector demos use 200 to 500 `number[]` vectors. Geospatial demos use 10 to 50 points in one city. Start from `seed/fixture.json`, which holds 12 synthetic products under the repository's licence. Each product has `sku`, `name`, `description`, `category`, `price`, `stock`, `updatedAt` and a GeoJSON `location`. Scale the fixture up with a generator function, not by hand-editing. `updatedAt` is stored as an ISO string in the fixture; convert it to a `Date` before writing if the app queries by date.

**(e)** Correct the rule's description of the image's own sample data (lines 7-14 today): the image seeds nothing unless `--init-data true` (env `INIT_DATA=true`) is passed; the opt-in dataset is StoreData (`stores`, `ratings`), not a `sampledb` with users, products, orders and analytics; `SKIP_INIT_DATA` is a legacy alias for `--init-data false`, not a default-false switch. Source: https://documentdb.io/docs/documentdb-local/ and `documentdb-local/scripts/documentdb_local_settings.sh` (line 37) in github.com/documentdb/documentdb.

### 6. New `skills/local-deployment/seed/fixture.json` (K08)

12 synthetic product documents, no real people, companies or places, under the repository's licence. `sku` is the natural key the seed upserts on. Shape (one document shown; the other 11 follow the same fields with distinct `sku` values and categories):

```json
[
  {
    "sku": "SKU-0001",
    "name": "Trail Bottle 750 ml",
    "description": "Insulated steel bottle for hiking and commuting.",
    "category": "outdoor",
    "price": 24.5,
    "stock": 120,
    "updatedAt": "2026-01-15T09:00:00Z",
    "location": { "type": "Point", "coordinates": [-122.335, 47.608] }
  }
]
```

### 7. New `skills/driver/driver-bulk-load-idempotent-seed.md` (K08; priority HIGH, same layout as `driver-singleton-client.md`)

> **Why it matters.** Seeds, imports and nightly jobs are the largest writes most apps make. One upsert per document costs one round trip each. A seed that is not keyed on a natural key duplicates data when rerun. A bulk error that is logged and dropped hides lost writes.
>
> **Contract.**
> 1. Give every document a deterministic natural key (or a stable string `_id`), never `Math.random()` or `uuid4()`.
> 2. Create a unique index on that key **before** the load. It keeps the upsert filter fast and turns a stray plain insert or a concurrent rerun into E11000 instead of a duplicate row. Learn says a unique index build blocks writes on the collection, so build it while the collection is empty (https://learn.microsoft.com/en-us/azure/documentdb/limitations).
> 3. Write in chunks with unordered collection-level `bulkWrite` upserts. Start at about 1,000 operations per call (a starting point, not a Learn figure; the 1,000-per-`insertMany` number on Learn belongs to the RU-based Cosmos DB for MongoDB page) and never exceed the documented hard cap of 25,000 writes per request: "Batch operations exceeding 25,000 writes will fail" (https://learn.microsoft.com/en-us/azure/documentdb/limitations, Batch limits). The compatibility page's `bulkWrite: No` row refers to the MongoDB 8.0 database-level `bulkWrite` command; collection-level `db.collection.bulkWrite()` maps to insert/update/delete and works (observed in this experiment: `ok:1, nUpserted:200`; the managed test of 2026-11-25 confirmed ordered and unordered). Client-level bulk writes (`MongoClient.bulk_write`) send the 8.0 command and fail at run time on an 8.0 cluster with code 2, so a multi-collection seed uses one collection-level call per collection. `hello.maxWriteBatchSize` is 25,000 on the service, so drivers split larger batches; a raw command over the cap fails with 16 `InvalidLength`.
> 4. Read `writeErrors`. Treat 11000 as "already present" and retry the other errors with backoff. Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys). The keyed upserts in this rule are that idempotent retry: with `retrywrites=false` the driver does not retry writes, so the script retries for itself.
> 5. Create secondary indexes **after** the load. For vector indexes the order depends on the kind (https://learn.microsoft.com/en-us/azure/documentdb/vector-search): HNSW can be created on an empty collection; IVF's `numLists` is derived from the document count, so create (or re-create) it after loading; a product-quantization (DiskANN) index should be created after the collection has data. Learn says a new vector index can return empty results for 2 to 3 minutes while it builds (https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-select-algorithm, Troubleshooting); the managed test of 2026-11-25 did not see this on 5-document collections (large collections untested), but the final count check still must not go through the vector index. Full-text search indexes are a separate step (`createSearchIndexes`, preview on Azure, not available on the local gateway) and are not part of a seed. Give every index an explicit name and send the same spec on every run, in a fixed key order with every value explicit: an identical `createIndexes` call (same name, same options, same key order, defaults included) is a no-op, the same name with other options fails with 86 `IndexKeySpecsConflict`, and a second vector index on a path fails with 85 `IndexOptionsConflict` (managed service and documentdb-local; undocumented on Learn). Treat 85 and 86 as stop signals, not as "already exists". Store embeddings as `number[]`: Learn requires an array of numbers, and a document whose vector has another type (for example BSON binary) is not indexed and is silently absent from results.
> 6. Never drop by default. Use an opt-in `--reset` flag (or `SEED_RESET=true`), and refuse non-`sample_` databases unless `--confirm` is passed.
> 7. Finish with a count check and exit non-zero on a mismatch.
> 8. For chunked RAG ingestion, upsert on `chunk_id = sha1(source_id + ":" + chunk_index)`.

**Incorrect** (generated):

```python
patients.create_index([("diagnoses", 1)])          # secondary indexes before the load
for i in range(1, 5001):
    patients.update_one({"patient_id": f"P{i}"}, {"$set": gen_patient(i)}, upsert=True)  # 5,000 round trips
```

**Correct: `seed.js`**

```javascript
import { MongoClient, MongoBulkWriteError } from "mongodb";
const DB_NAME = process.env.DATABASE_NAME;
const CHUNK = Number(process.env.SEED_CHUNK_SIZE ?? 1000);
if (!/^sample_/.test(DB_NAME) && !process.argv.includes("--confirm"))
  throw new Error(`Refusing to seed "${DB_NAME}": pass --confirm for a non-sample database`);
const client = new MongoClient(process.env.DOCUMENTDB_URI);   // from env, never hard-coded
const db = client.db(DB_NAME), products = db.collection("products");
let duplicates = 0;

async function runBulk(coll, ops, attempt = 0) {
  try { return await coll.bulkWrite(ops, { ordered: false }); }
  catch (err) {
    if (!(err instanceof MongoBulkWriteError)) throw err;
    const writeErrors = [].concat(err.writeErrors ?? []);      // may be one WriteError or an array
    const failed = writeErrors.filter(e => e.code !== 11000);
    duplicates += writeErrors.length - failed.length;
    if (failed.length === 0) return err.result;
    if (attempt >= 2) throw err;
    await new Promise(r => setTimeout(r, 500 * 2 ** attempt));
    return runBulk(coll, failed.map(e => ops[e.index]), attempt + 1);
  }
}

try {
  if (process.argv.includes("--reset")) await products.drop().catch(() => {});
  await products.createIndex({ productId: 1 }, { unique: true, name: "products_productId_unique" });
  const docs = generateProducts();                             // productId derived from data
  for (let i = 0; i < docs.length; i += CHUNK)
    await runBulk(products, docs.slice(i, i + CHUNK).map(d => ({
      updateOne: { filter: { productId: d.productId }, update: { $set: d }, upsert: true } })));
  await products.createIndex({ category: 1, price: -1 }, { name: "products_category_price" });
  await db.command({ createIndexes: "products", indexes: [{ name: "products_vec", key: { embedding: "cosmosSearch" },
    cosmosSearchOptions: { kind: "vector-hnsw", m: 16, efConstruction: 64, similarity: "COS", dimensions: 1536 } }] });
  const n = await products.countDocuments();
  console.log(`seeded ${n} products (${duplicates} duplicate-key ignored)`);
  if (n !== docs.length) process.exitCode = 1;
} finally { await client.close(); }
```

The HNSW values above (`m: 16`, `efConstruction: 64`) are the documented defaults: `m` 2 to 100 (default 16), `efConstruction` 4 to 1000 and at least `2m` (default 64), `efSearch` default 40; IVF uses `numLists` = documentCount/1000 (start at 1 for demos) and `nProbes` at most `numLists`. `dimensions` must be at most 2,000 for an uncompressed index, 4,000 with `compression: "half"` on HNSW or IVF, and 16,000 only with product quantization on DiskANN (the 8,000 figure on the select-algorithm quickstarts is wrong). One vector index per path. HNSW and DiskANN need an M30 or higher cluster. Sources: https://learn.microsoft.com/en-us/azure/documentdb/vector-search, https://learn.microsoft.com/en-us/azure/documentdb/half-precision, https://learn.microsoft.com/en-us/azure/documentdb/product-quantization, https://learn.microsoft.com/en-us/azure/documentdb/limitations.

**Correct: `seed.py`**

```python
import os, sys, time
from pymongo import MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

DB_NAME = os.environ["DATABASE_NAME"]
CHUNK = int(os.environ.get("SEED_CHUNK_SIZE", "1000"))
if not DB_NAME.startswith("sample_") and "--confirm" not in sys.argv:
    sys.exit(f'Refusing to seed "{DB_NAME}": pass --confirm for a non-sample database')

def run_bulk(coll, ops, attempt=0):
    try:
        return coll.bulk_write(ops, ordered=False)
    except BulkWriteError as e:
        failed = [w for w in e.details.get("writeErrors", []) if w["code"] != 11000]
        if not failed:
            return e.details
        if attempt >= 2:
            raise
        time.sleep(0.5 * 2 ** attempt)        # retryable writes unsupported (retrywrites=false): retry here
        return run_bulk(coll, [ops[w["index"]] for w in failed], attempt + 1)

with MongoClient(os.environ["DOCUMENTDB_URI"]) as client:
    coll = client[DB_NAME]["patients"]
    if "--reset" in sys.argv:
        coll.drop()
    coll.create_index([("patient_id", 1)], unique=True, name="patients_patient_id_unique")
    docs = list(generate_patients())          # patient_id derived from data
    for i in range(0, len(docs), CHUNK):
        run_bulk(coll, [UpdateOne({"patient_id": d["patient_id"]}, {"$set": d}, upsert=True)
                        for d in docs[i:i + CHUNK]])
    coll.create_index([("region", 1), ("age", 1)], name="patients_region_age")
    n = coll.count_documents({})
    print(f"seeded {n} patients")
    sys.exit(0 if n == len(docs) else 1)
```

> **Batch and nightly jobs.** Iterate with `find(filter).sort("_id", 1).batch_size(500)`. Save the last `_id` so that a restart resumes from `{"_id": {"$gt": marker}}`. Cap concurrency (`asyncio.Semaphore(8)` or `p-limit`). Do not rely on `allowDiskUse`: the service accepts and ignores it (engine `commands_common.c` lists it among ignored options); query memory is bounded per tier (about 150 MiB on M80) and sorting is done in memory, so bound `$group`, `$facet` and `$sort` input with an indexed `$match` and `$limit` instead. Retry network errors and code 50 `ExceededTimeLimit` (the 120-second default query limit, adjustable per query with `maxTimeMS`) with bounded backoff, and only for idempotent writes. Azure DocumentDB has no request units and never returns 16500 or 429: those are RU-based Cosmos DB for MongoDB codes, absent from the Learn troubleshooting table and from the engine's error mappings, and no run in this experiment saw one. Treat code 261 `TooManyLogicalSessions` ("There are too many open connections.") as "reduce connections", not as a retry signal.
>
> **Local and Azure.** The same script runs against the local Gateway container (see `local-deployment` Quick start) and an Azure DocumentDB cluster; only `DOCUMENTDB_URI` changes (see `local-env-driven-config`). The local URI carries the TLS relaxation for the self-signed certificate; the Azure URI uses `tls=true` with SCRAM-SHA-256 or Entra ID.
>
> **References.** Node.js `Collection.bulkWrite` / `MongoBulkWriteError`; PyMongo `bulk_write` / `BulkWriteError.details`; https://learn.microsoft.com/en-us/azure/documentdb/limitations (25,000 writes per batch, 120-second query limit, unique-index build); https://learn.microsoft.com/en-us/azure/documentdb/vector-search (parameter ranges, build order); https://learn.microsoft.com/en-us/azure/documentdb/how-to-create-indexes; `index-single-field`; `vector-search/vector-choose-index-type.md`; `local-deployment/seed/fixture.json`; `scenarios/contoso/contoso-seed.js` for a larger resumable example.

### 8. `skills/driver/SKILL.md` (K08; also edited by the K07 PR, coordinate the Rules list)

Add to Rules:

```markdown
- [driver-bulk-load-idempotent-seed](driver-bulk-load-idempotent-seed.md) — Seed, import and batch-job pattern: unique natural-key index first, chunked unordered bulkWrite upserts, writeErrors handling, indexes after load, opt-in reset, count check.
```

Append to the front-matter `description`: "…bulk loading, seed scripts, imports and batch jobs."

### 9. `skills/connection/SKILL.md` (no edit in this PR)

The `retryWrites=true` example (line 60) and the `withRetry` helper that retries only on `err.code === 16500 || err.code === 429` (lines 224-230) contradict the bulk-load rule's retry guidance and the decided positions (retryable writes are not supported by Azure DocumentDB and `retrywrites=false` is required; the service never returns 16500 or 429, so that helper never retries a real transient error; see Resolved), but they belong to the K07 connection-string PR. This PR only cross-links; land K07 first or in the same release so the retry story is consistent and K07 uses the same rationale sentence as the bulk-load rule. The missing local-target mention noted under "What happens today" is covered by the `mcp-setup` and `AGENTS.md` changes below; K07 may add a one-line link to the local-deployment quick start.

### 10. `skills/mcp-setup/SKILL.md` (K26 and K23)

**(a) Step 1**, after the `git --version` line (K26):

```bash
docker --version  # optional: if present, start a local gateway for the dev loop
                  # (skills/local-deployment/SKILL.md -> Quick start) and add it
                  # as a second CONNECTION_PROFILES entry, e.g. "local"
```

**(b) Step 2, line 88:** replace row B ("Local MongoDB / DocumentDB", `mongodb://localhost:27017`) with two rows so the targets are not conflated. This supersedes K23's single-row rename and uses the same 10260 URI; link the B1 row to `local-connection-config`.

| Option | When to use | Example URI |
|---|---|---|
| **B1. Local DocumentDB gateway (Docker)** | Local dev against the DocumentDB engine | `mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256` |
| **B2. Local community MongoDB (not DocumentDB)** | Generic MongoDB testing only | `mongodb://localhost:27017` |

### 11. `AGENTS.md`, "Routing hints for agents" (K26)

Add next to the existing local-deployment hint:

```markdown
- **Starting a new sample or integration tests and `docker` is on PATH** → `documentdb-local-deployment` (run its Quick start first; point tests at the local gateway, then switch `DOCUMENTDB_URI` to the Azure cluster)
```

### 12. `README.md` line 160, `GEMINI.md` line 27, `install.sh` lines 8/522/527, `install.ps1` lines 46/491, `docs/installation/macos.md` line 21 (K23)

Replace `mongodb://localhost:27017` with the 10260 gateway URI (`mongodb://<user>:<pw>@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256`), or label it explicitly as "plain MongoDB (not DocumentDB)". Script behaviour does not change beyond the default example URI and help text. (Scope: see Open question 1.)

### 13. New `examples/local-testing/` (K09)

Runnable versions of the `local-test-tiers` snippets. The folder is named `local-testing/` so it is not confused with the kit's own top-level `testing/` harness.

- `examples/local-testing/python/conftest.py` — the `tests/conftest.py` block from section 4
- `examples/local-testing/python/pytest.ini` — the `pytest.ini` block from section 4
- `examples/local-testing/node/__mocks__/db.js` — the `jest.mock` factory from section 4 as a manual mock
- `examples/local-testing/node/jest.config.js` — `testPathIgnorePatterns` separating `tests/unit` and `tests/integration`, plus the ESM transform note
- `examples/local-testing/docker-compose.test.yml` — the compose block from section 4
- `examples/local-testing/.github/workflows/tests.yml` — the CI block from section 4 (an example workflow for samples, not the kit's own CI), with the URI read from a repository secret

### 14. Corrections to existing `skills/local-deployment` rules (from findings/phase4/DECISIONS.md, SME topic 12)

Statements in the skill that the research contradicted; each is a small text edit in the same PR because the quick start and `local-test-tiers` would otherwise disagree with the rules they link.

- `local-connection-config.md` (lines 7, 13, 18-25): says a connection without `--tls` "fails" / the "server rejects" it and lists `--authenticationMechanism SCRAM-SHA-256` as a minimum requirement. The image default is `--tlsMode allowTLS`, which accepts plain and TLS connections (only `requireTLS` rejects plain ones), and the mechanism is negotiated because the gateway advertises only SCRAM-SHA-256. Reword to: TLS is recommended and the certificate is self-signed, so local URIs carry `tls=true&tlsAllowInvalidCertificates=true`; `authMechanism` is optional. Sources: https://documentdb.io/docs/documentdb-local/; engine `documentdb-local/scripts/documentdb_local_settings.sh` (line 44), `pg_documentdb_gw/documentdb_gateway_core/src/processor/ismaster.rs` (saslSupportedMechs).
- `local-docker-compose-setup.md` (lines 10, 34), `local-ports-and-bindings.md` (lines 28, 42, 50, 60), `local-choose-deployment-method.md` (line 38), `SKILL.md` (line 11): the rule text says to pin the image, but every example uses `:latest` with `pull_policy: always`. Change the compose and `docker run` examples to a versioned tag (`pg17-1.2.0` today, the build `latest` resolves to) with a comment on bumping, and keep `:latest` only in the copy-paste quick start. The kit's own CI (`.github/workflows/diagnostic-regression.yml` line 23, `docs/TESTING-MACOS.md` line 100, `CHANGELOG.md` line 9) pins digest `sha256:4a341d...` described as "the pg17-1.0.0 digest"; that digest still resolves but no named tag points to it any more (`pg17-1.0.0`, `pg17-1.0.1`, `1.0` and `stable` all resolve to the 1.0.1 build) and it is two releases behind 1.2.0 (2026-11-12); re-pin as part of the same change (which tag or digest is Open question 5). Source: https://documentdb.io/docs/documentdb-local/ ("Use a versioned tag when you need a reproducible setup"), https://documentdb.io/docs/getting-started/release-notes-1.2, GHCR tag listing observed 2026-11-25.
- `local-choose-deployment-method.md` (line 45) and `local-docker-compose-setup.md` (line 73): reference links point at `github.com/microsoft/documentdb`; the image and docs live under the `documentdb` GitHub organization (`ghcr.io/documentdb/documentdb/documentdb-local`, documentdb.io), as the kit's own CHANGELOG entry of 2026-10-19 records.
- `local-sample-data-management.md` (lines 7-14): sample-data claims, fixed in section 5(e).

### 15. `CHANGELOG.md` (K08, extended to the whole PR)

```markdown
- local-deployment: add "Not this" guidance against the Azure Cosmos DB Emulator / port 10255 / stock mongo images; add a gateway Quick start with a local-vs-cluster parity list (no DiskANN / pq, full-text search, change streams, Entra ID or snapshot read concern on the local gateway); add `local-test-tiers` rule; fix non-idempotent seed example and the image's sample-data description; add demo fixture (`seed/fixture.json`) and dataset sizing; examples use a versioned image tag; TLS/authMechanism wording in local-connection-config corrected.
- driver: add `driver-bulk-load-idempotent-seed` rule (25,000 writes per request cap, retrywrites=false rationale, no 16500/429 on Azure DocumentDB, allowDiskUse is ignored).
- mcp-setup / AGENTS.md / README / install scripts: local example URI now points at the 10260 gateway; plain MongoDB on 27017 is labelled as not DocumentDB.
```

Out of scope: `CONTRIBUTING.md` still points at `skills/documentdb-best-practices/rules/` and a `metadata.json` that no longer exist (separate small fix). The same 27017 "local URI" in the microsoft/documentdb-mcp README is tracked separately (Open question 2). Optional follow-up: link the seed pattern from the Learn quickstart "load sample data" sections (doc feedback, not this PR).

## Evidence

All from one experiment run.

- `runs/15-financial-advisor-chatbot-rag/20261124-192021/` (`02-readiness.json` -> `confusions[Q11]`: cold answer names the emulator image and 10255)
- `runs/15-cohort-analysis-backend/20261124-205336/` (`02-readiness.json` -> `confusions[Q11]`: emulator, 8081 and 10255 together; also flagged for the gateway not running)
- `runs/06-credit-risk-multi-agent-scorer/20261124-190546/` (`02-readiness.json` accelerators_missed; `events.jsonl`: skill loaded, no docker command run)
- `runs/13-chronic-disease-risk-predictor/20261124-194916/02-readiness.json` (improvised gateway `docker run` with no credentials; also suggested community `mongo:7` on 27017)
- `runs/11-preference-center-consent-store/20261124-204614/doc-gaps.md` (app imported at module scope triggers `init_beanie`; no offline test tier)
- `runs/06-order-history-timeline-agent/20261124-183612/app/tests/test_db.py` (unguarded live-cluster "unit" test)
- `runs/16-population-health-dashboard-backend/20261124-195348/05-audit.json` (per-document upsert loop, indexes before load)
- `runs/20-store-locator-with-geospatial-search/20261124-185729/02-readiness.json` (emulator cold answer on 10255, and no seed dataset or sizing guidance)

Further run folders cited by the members:

- K23 (`02-readiness.json` -> `confusions[Q11]`): `runs/16-loyalty-points-ledger/20261124-184937/`, `runs/02-ai-powered-product-recommendations/20261124-181835/`
- K26 (`02-readiness.json`): `runs/10-expense-report-auto-categorizer/20261124-191257/`, `runs/04-natural-language-product-search/20261124-183232/`, `runs/12-abandoned-cart-recovery-orchestration/20261124-184507/`
- K09: `runs/08-regulatory-compliance-rag-checker/20261124-190949/doc-gaps.md`, `runs/10-multi-tenant-storefront-saas/20261124-184121/doc-gaps.md`, `runs/01-anti-money-laundering-pattern-detector/20261124-200112/app/tests/test_seed_and_analysis.py`, `runs/18-adverse-event-reporting-pipeline/20261124-195726/05-audit.json`, `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/05-audit.json`, `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json`, `runs/20-identity-resolution-multi-agent/20261124-210002/02-readiness.json`; also raised in `04-customer-journey-mapper`, `05-churn-prediction-pipeline`, `05-appointment-scheduling-assistant`, `06-symptom-triage-chatbot-rag`, `07-voice-of-customer-sentiment-hub`, `15-digital-onboarding-orchestration` and `17-seasonal-trend-spotter-agent`
- K08: `runs/10-multi-tenant-storefront-saas/20261124-184121/05-audit.json`, `runs/02-real-time-event-stream-ingestion/20261124-203233/doc-gaps.md`, `runs/16-atm-network-status-monitor/20261124-202405/doc-gaps.md`, `runs/04-earnings-call-rag-assistant/20261124-190247/doc-gaps.md`

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- Local gateway feature parity (`cosmosSearch`, `createSearchIndexes` / `$search`): the documentdb-local image supports `vector-ivf` and `vector-hnsw` (2,000 dimensions uncompressed, 4,000 with `compression: "half"`) but not `vector-diskann` or `pq` compression, not `createSearchIndexes` / full-text `$search` (code 115 "Command 'createSearchIndexes' not supported."), not change streams (code 115), not Microsoft Entra ID (SCRAM-SHA-256 only), and not `readConcern: snapshot`, while transactions with the default read concern work. The managed test of 2026-11-25 saw each cluster-only feature work on the service (DiskANN, full-text search after enabling, change streams, MONGODB-OIDC once Entra ID is enabled, snapshot read concern in transactions) and listed the behaviour a local test cannot catch (DECISIONS.md, topic 12, "Managed vs local"). Sources (DECISIONS.md, SME topic 12): https://documentdb.io/docs/reference/operators/aggregation/$vectorsearch/, https://documentdb.io/docs/reference/operators/aggregation/$search/, https://documentdb.io/docs/reference/operators/aggregation/$changestream/, engine source `pg_documentdb/src/vector/vector_index_kind_impl.c`, `pg_documentdb_gw/documentdb_gateway_core/src/postgres/data_client.rs`, `src/auth/manager.rs`, `packaging/gateway/docker/Dockerfile_documentdb_local`, issues documentdb/documentdb#50, #736, #803.
- Full-text search status: preview, not GA; enablement is self-serve (portal Settings > Features > Full-text search, or Azure CLI / Bicep / Terraform PATCH of `properties.previewFeatures` adding `FullTextSearch`); Learn says to wait 10 minutes before creating a search index, an upper bound (the managed test of 2026-11-25 saw creation work about 210 seconds after enabling, after 115 and then 67 with the same message; DECISIONS.md topic 7); and a cluster without the preview returns code 115 `CommandNotSupported` "Search index creation is not supported yet". Sources (DECISIONS.md, SME topic 7): https://learn.microsoft.com/en-us/azure/documentdb/full-text-search-overview (updated 2026-11-17), https://devblogs.microsoft.com/documentdb/?p=259, observation in runs/07-voice-of-customer-sentiment-hub/20261124-204049.
- 16500 / 429 throttling: Azure DocumentDB never returns 16500, 429, TooManyRequests or any throttling code; those are RU-based Cosmos DB for MongoDB errors, absent from the Learn troubleshooting table and from the engine's error mappings, and no run observed one; resource pressure surfaces as timeouts (code 50 `ExceededTimeLimit`, 120-second default) and 261 `TooManyLogicalSessions` is a non-retryable connection-limit error. Sources (DECISIONS.md, SME topic 2): https://learn.microsoft.com/en-us/azure/documentdb/troubleshoot-common-issues, https://learn.microsoft.com/en-us/azure/documentdb/limitations, https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/error-codes-solutions, github.com/documentdb/documentdb at a5f1636 (error_mappings.csv, documentdb_errors.csv, `query_dispatch.rs`).
- Vector index build order per kind: HNSW can be created on an empty collection; IVF's `numLists` depends on document count, so create or re-create it after loading; a product-quantization index should be created after the collection has data; Learn says a new index can return empty results for 2 to 3 minutes while it builds, which the managed test of 2026-11-25 did not see on 5-document collections (large collections untested). Sources (DECISIONS.md, SME topic 6): https://learn.microsoft.com/en-us/azure/documentdb/vector-search, https://learn.microsoft.com/en-us/azure/documentdb/product-quantization, https://learn.microsoft.com/en-us/azure/documentdb/quickstart-nodejs-select-algorithm.
- HNSW options and binary vectors: `m: 16` and `efConstruction: 64` are the documented defaults (`m` 2 to 100, `efConstruction` 4 to 1000 and at least `2m`); dimension caps are 2,000 uncompressed, 4,000 with half precision, 16,000 with product quantization on DiskANN (the 8,000 figure on the select-algorithm quickstarts is wrong, confirmed by the product owner 2026-11-25); vectors must be arrays of numbers, and a document whose vector is another type (BSON binary) is not indexed and is silently absent from results. Sources (DECISIONS.md, SME topic 6): https://learn.microsoft.com/en-us/azure/documentdb/vector-search, https://learn.microsoft.com/en-us/azure/documentdb/half-precision, https://learn.microsoft.com/en-us/azure/documentdb/limitations, issue documentdb/documentdb#109.
- Pinning a versioned image tag: yes; the OSS docs say "Use a versioned tag when you need a reproducible setup", versioned tags are `pg15-1.2.0` to `pg18-1.2.0` (`latest` and `1.2` resolve to `pg17-1.2.0`, DocumentDB 1.2, 2026-11-12), and the kit's rule text already says to pin while its examples use `:latest`; which exact tag or digest the kit's CI pins is a maintainer choice (Open question 5). Sources (DECISIONS.md, SME topic 12): https://documentdb.io/docs/documentdb-local/, https://documentdb.io/docs/getting-started/release-notes-1.2, GHCR tag listing observed 2026-11-25.
- allowDiskUse (affects the batch-job paragraph): the engine accepts and ignores the option; query memory is bounded per tier (about 150 MiB on M80). Sources (DECISIONS.md, SME topic 10): engine `pg_documentdb/src/commands/commands_common.c` (IgnoredCommonSpecFields), https://learn.microsoft.com/en-us/azure/documentdb/limitations.
- Batch write cap (affects the bulk-load contract): 25,000 writes per batch request; collection-level `bulkWrite()` works, the compatibility page's `bulkWrite: No` row is the MongoDB 8.0 database-level command. The managed test of 2026-11-25 confirmed `hello.maxWriteBatchSize` 25,000 (drivers split larger batches) and found client-level `MongoClient.bulk_write` failing at run time with code 2 on an 8.0 cluster (ENGINE-TESTS.md, Managed service). Sources (DECISIONS.md, SME topic 9): https://learn.microsoft.com/en-us/azure/documentdb/limitations (Batch limits), https://learn.microsoft.com/en-us/azure/documentdb/compatibility-query-language, observation in runs/02-real-time-event-stream-ingestion/20261124-203233.

## Open questions

1. Should the install-script and README edits in section 12 stay in this PR or move to a follow-up? They change user-facing default example URIs. (Maintainer preference.)
2. The same 27017 "local URI" also appears in the microsoft/documentdb-mcp README (lines 73, 95, 115, 231 and the VS Code install badge) and on the Learn MCP Toolkit page. The facts are settled (a default documentdb-local container listens on 10260, exits without a password and serves a self-signed certificate, so that example cannot connect to it; DECISIONS.md, SME topic 12); whether the MCP repository adopts the same 10260 gateway example is a maintainer decision for that repository and is tracked as its own item, out of scope here.
3. Maintainers: is `AGENTS.md` routing on "docker is on PATH" the trigger you want, or would you prefer the hint only in `mcp-setup` so agents do not start containers unasked?
4. Part of the "gateway not running" missed-accelerator signal comes from the experiment harness (local tools such as documentdb-local were reported as missed even where the harness did not let the agent use them). The doc gap stands on the file evidence, but K26's 15-sample figure, and therefore part of the 55, should be treated as indicative until a rerun after the harness fixes.
5. Which exact tag or digest should the kit's compose example and CI pin (`pg17-1.2.0`, its digest, or the floating `1.2`)? That versioned tags should replace `:latest` is settled (see Resolved); the choice is a maintainer decision. Suggested default: `pg17-1.2.0` pinned by digest, bumped deliberately on each DocumentDB release, with `:latest` kept only in the copy-paste quick start.
6. Should the bulk-load rule live in `driver`, as proposed, or in `local-deployment`? Do the demo-size numbers suit the maintainers?
7. Sample counting: the 55 is the union of K23's 22 and K26's 15 (from finding-id lists), K09's 16 (finding-id lists of drafts 091 and 052, which share one sample) and K08's 15 (from evidence paths of drafts 103 and 053, which share one sample; their finding-id lists also include findings on unrelated topics such as cold-quiz naming). Members overlap on 13 samples. All counts come from one run and may change after the harness fixes; re-check before quoting them publicly.

## Source drafts

- 030-believes-the-azure-cosmos-db-emulator-ports-8081-10250-10255.md
- 059-local-documentdb-gateway-container-is-never-started-surface-.md
- 091-offline-test-harness-mocked-unit-tests-env-gated-integration.md
- 052-no-offline-vs-live-test-strategy-for-generated-samples-mocks.md
- 103-seed-and-batch-load-scripts-are-per-document-loops-not-idemp.md
- 053-documentdb-local-deployment-skill-lacks-an-idempotent-seed-s.md

## Merged from

- K23: local-deployment: add a "Not this" line steering agents away from the Azure Cosmos DB Emulator
- K09: local-deployment skill: offline test tiers (mocked unit tests, env-gated integration tests, local container)
- K08: driver/local-deployment skills: idempotent seed and bulk-load rule with reference seed scripts
- K26: local-deployment: add a gateway quick start surfaced from AGENTS.md and mcp-setup
