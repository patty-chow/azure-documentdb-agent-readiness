---
id: K09
title: "local-deployment skill: offline test tiers (mocked unit tests, env-gated integration tests, local container)"
repo: Azure/documentdb-agent-kit
type: pr
status: needs_sme
priority: P1
sample_count: 16
member_drafts:
  - 091-offline-test-harness-mocked-unit-tests-env-gated-integration.md
  - 052-no-offline-vs-live-test-strategy-for-generated-samples-mocks.md
open_questions: 4
---

# local-deployment skill: offline test tiers (mocked unit tests, env-gated integration tests, local container)

## What happens today

`skills/local-deployment/SKILL.md` has seven rules (choose-deployment-method, connection-config, docker-compose-setup, env-driven-config, ports-and-bindings, prod-parity, sample-data-management). Its description says "Use when ... building integration tests", so agents load it when writing tests. The only testing guidance is one bullet in `local-prod-parity.md` ("Integration tests target the local Gateway container, not an in-memory MongoDB") plus a four-line `docker compose up -d documentdb / ./wait-for-port.sh 10260 / npm run test:integration / docker compose down` snippet. No skill or knowledge-base file mentions pytest, jest, mocks or markers. Nothing tells an agent:

- how to write a unit test that needs no cluster and no AI key (a stubbed collection, a fake embedder, LLM or web-search client);
- how to keep connects out of import time, so `import app` does not need `DOCUMENTDB_URI`;
- how to gate integration tests on `DOCUMENTDB_URI` so they are skipped, not failed, when it is unset, and how CI runs the two tiers separately;
- how to isolate test data (a per-run database dropped on teardown);
- which DocumentDB features (vector search via `cosmosSearch`, `createSearchIndexes` / `$search`, DocumentDB index options, TTL expiry, `explain`) cannot be mocked and belong in the container tier.

The kit's own `testing/conftest.py` already uses a skip-when-no-container fixture, but that is the kit's eval harness. Agents do not load it as a rule.

## Why it matters

These figures come from one run of a 100-sample agent-readiness experiment (gpt-5-mini plus this kit and the DocumentDB, Azure and Learn MCP servers). Counts may move on a re-run.

- 16 distinct samples raised the missing test convention as a doc gap.
- Across 117 audited runs, the requirement "Unit tests run without a live cluster" was not met in 65 and only partly met in 6.

What the agent did without a pattern:

- **Live-cluster "unit" tests with no guard.** `06-order-history-timeline-agent` seeds and counts against whatever `DOCUMENTDB_URI` resolves to. `01-anti-money-laundering-pattern-detector` calls `get_db()` and assumes a seed already ran. `11-preference-center-consent-store` imports the app at module scope, which triggers `init_beanie`. On a clean checkout all three fail with connection errors.
- **Mixed tiers.** `08-regulatory-compliance-rag-checker` puts a mongomock test and a live test in one folder with no marker.
- **Placeholder or missing tests.** `03-next-best-action-multi-agent` asserts only `callable(orchestrate)`. `20-identity-resolution-multi-agent` tests only a Pydantic model, and `04-customer-journey-mapper` tests only `buildPrompt`. `13-basel-iii-capital-ratio-calculator` skips everything and imports a class that does not exist. `05-churn-prediction-pipeline` and `17-seasonal-trend-spotter-agent` ship no tests.
- **Claimed coverage that does not exist.** `18-adverse-event-reporting-pipeline`'s README says pytest runs unit tests, but there is no `tests/` directory.

The result is CI that fails without secrets, or passes without testing anything.

## Proposed change

### 1. New rule `skills/local-deployment/local-test-tiers.md`

It follows the existing rule template (Why it matters / Incorrect / Correct / References).

**Rules**
- **Two tiers, never mixed in one file or one unmarked folder.**
- **Tier 1, unit (always runs):** no network, no `DOCUMENTDB_URI`, no AI key. The driver is created lazily behind a small accessor or repository (or business logic takes the collection as a parameter), so tests can swap in a stub. Embedding, chat and web-search calls go through one function that tests replace with a deterministic fake (fixed-dimension vectors, canned completions). `mongomock` is fine for plain CRUD and aggregation *shapes*. It does not implement `cosmosSearch`, `$search` or DocumentDB index options.
- **Tier 2, integration (gated):** marked `integration` and skipped with a clear message when `DOCUMENTDB_URI` is unset. It runs against the local Gateway container (or an Azure DocumentDB cluster when the URI points there), never an in-memory MongoDB. The documented `.env.example` value points at the local Gateway on `127.0.0.1:10260` (see `local-connection-config`). Anything DocumentDB-specific (`cosmosSearch`, `$search`, TTL, `explain`) lives here. Optionally, a `pytest_collection_modifyitems` hook in `conftest.py` adds a skip marker to every `integration` item when `DOCUMENTDB_URI` is unset, so tests that do not use the `test_db` fixture are skipped too.
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
    image: ghcr.io/documentdb/documentdb/documentdb-local:latest
    ports: ["127.0.0.1:10260:10260"]
    environment:
      - USERNAME=${DOCUMENTDB_USER:?}
      - PASSWORD=${DOCUMENTDB_PASSWORD:?}
      - SKIP_INIT_DATA=true
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
The URI comes from a secret and is never written inline. For its shape, the rule cross-links `local-connection-config`.

### 2. `skills/local-deployment/SKILL.md`

- Under `## Rules`, after `local-prod-parity`: `- [local-test-tiers](local-test-tiers.md): Offline unit tests with stubbed driver and fake embeddings/LLM; integration tests marked and skipped unless DOCUMENTDB_URI is set, run against the Gateway container with a disposable per-run database.`
- Append to the front-matter `description`: "two-tier test layout (offline unit tests, DOCUMENTDB_URI-gated integration tests)".

### 3. `skills/local-deployment/local-prod-parity.md`

Make one edit to the "Test what prod does" bullet: "Integration tests target the local Gateway container, not an in-memory MongoDB. Unit tests may stub the driver. See `local-test-tiers` for the gating and fixture pattern."

### 4. `examples/local-testing/`

Add the snippets above as runnable files: `python/conftest.py`, `python/pytest.ini`, `node/__mocks__/db.js`, `node/jest.config.js`, `docker-compose.test.yml` and `.github/workflows/tests.yml`. The folder is named `local-testing/` so it is not confused with the kit's own top-level `testing/` harness.

## Evidence

- `runs/11-preference-center-consent-store/20261124-204614/doc-gaps.md`
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/doc-gaps.md`
- `runs/10-multi-tenant-storefront-saas/20261124-184121/doc-gaps.md`
- `runs/06-order-history-timeline-agent/20261124-183612/app/tests/test_db.py`
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/app/tests/test_seed_and_analysis.py`
- `runs/18-adverse-event-reporting-pipeline/20261124-195726/05-audit.json`
- `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/05-audit.json`
- `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json`
- `runs/20-identity-resolution-multi-agent/20261124-210002/02-readiness.json`

Also raised in `04-customer-journey-mapper`, `05-churn-prediction-pipeline`, `05-appointment-scheduling-assistant`, `06-symptom-triage-chatbot-rag`, `07-voice-of-customer-sentiment-hub`, `15-digital-onboarding-orchestration` and `17-seasonal-trend-spotter-agent`.

## Open questions

1. [needs SME confirmation] Does the local Gateway image support `cosmosSearch` vector indexes (vector-ivf, vector-hnsw, vector-diskann) and `createSearchIndexes` / `$search`, so the integration tier can exercise them? If not, the rule should name which features need a real Azure DocumentDB cluster.
2. [needs SME confirmation] Is full-text search (`$search`) generally available, or still in preview? The rule should not imply that a preview feature is GA.
3. [needs SME confirmation] Should CI pin a versioned `documentdb-local` tag instead of `:latest`?
4. [needs SME confirmation] retryWrites: this PR deliberately states no value. Other kit drafts disagree. One position is that Learn does not say retryable writes are unsupported, so the kit's rationale should be softened. The other is that retryWrites must be false because retryable writes are unsupported and cause write errors. Please give the engineering answer, so that the connection-string rules this one cross-links all say the same thing.

## Source drafts

- 091-offline-test-harness-mocked-unit-tests-env-gated-integration.md
- 052-no-offline-vs-live-test-strategy-for-generated-samples-mocks.md
