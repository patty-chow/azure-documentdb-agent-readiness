---
title: "Add `local-offline-test-harness` rule: mocked unit tests, env-gated integration tests, Gateway container recipe"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P1
sample_count: 10
findings: 10
bucket: kit-doc-gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# Add `local-offline-test-harness` rule: mocked unit tests, env-gated integration tests, Gateway container recipe

## What happens today

`skills/local-deployment/SKILL.md` lists seven rules. The only one that mentions tests, `local-prod-parity.md`, says "Integration tests target the local Gateway container, not an in-memory MongoDB" and shows a 4-line `docker compose up / npm run test:integration / docker compose down` snippet. Nothing in the kit shows:

- how to write a **unit** test that runs with no cluster at all (a fake collection, a monkeypatched `get_client()` / `init_db()`, a jest mock of the driver module);
- how to keep module-import-time DB connects out of the test path (lazy init);
- how to **separate** the two tiers so CI runs unit tests always and integration tests only when `DOCUMENTDB_URI` is set (`@pytest.mark.integration`, `integration/` folder, jest `testPathIgnorePatterns`);
- how to mock the embedder / LLM / web-search provider so tests need no API key either;
- the exact `docker compose` setup/teardown and the connection string shape (port 10260, `tls=true&tlsAllowInvalidCertificates=true`, SCRAM-SHA-256) to use **from a test runner**.

## Why it matters

In a 100-sample agent-readiness run (gpt-5-mini + this kit + the DocumentDB/Azure/Learn MCP servers), the audit requirement "Unit tests run without a live cluster" was **not met in 65 of 117 audited runs** and only partly met in 6 more. Ten samples raised this as an explicit doc gap against the kit. Concrete failure modes the agent produced because no pattern existed:

- `11-preference-center-consent-store`: the only test imports `app.main` at module scope, which runs FastAPI startup -> `init_beanie` -> needs `DOCUMENTDB_URI`; the suite cannot run offline.
- `13-basel-iii-capital-ratio-calculator`: test is `skipif` on `DOCUMENTDB_URI` *and* imports a class that does not exist; zero coverage offline.
- `08-regulatory-compliance-rag-checker`: a mongomock test and a live-cluster test (`test_seed_and_query.py`) sit in the same folder with no marker; `pytest` either fails or hits real resources.
- `18-adverse-event-reporting-pipeline`: README claims "pytest runs lightweight unit tests"; no test files exist.
- `10-multi-tenant-storefront-saas`: `tests/isolation.test.js` runs against the live cluster; the agent asked for the exact Gateway docker invocation (port 10260, TLS) to run it locally.
- `04-customer-journey-mapper`: tests cover only `buildPrompt`; auditor notes aggregation/seed cannot be tested "without a live cluster or a documented mocking approach".
- `17-seasonal-trend-spotter-agent`, `05-churn-prediction-pipeline`: no tests at all; auditor asks for a canonical harness that mocks pymongo and the search provider.

The skill's own description already says "Use when ... building integration tests", so agents load it for this task and find nothing to follow.

## Proposed change

### 1. New rule `skills/local-deployment/local-offline-test-harness.md`

Follow the existing rule template (Why it matters / Incorrect / Correct / References). Core content:

**Policy.** Two tiers, never mixed in one file:
- *Unit tests* — no network, no `DOCUMENTDB_URI`, no API key. Stub the sample's DB accessor and any embedder/LLM/search client. Run on every push.
- *Integration tests* — run only when `DOCUMENTDB_URI` is set, against the local Gateway container (or a dev cluster). Anything DocumentDB-specific (`cosmosSearch` vector queries, `createSearchIndexes` / `$search` text search, TTL, `explain`) belongs here, because mongomock / in-memory servers do not implement those operators.

**Incorrect** (from the runs above):
```python
# tests/test_api.py
from app.main import app          # module import triggers init_db() -> needs DOCUMENTDB_URI
```
```python
# one folder, no markers
def test_aggregate_with_mongomock(): ...
def test_seed_and_query_live_cluster(): ...   # silently hits a real cluster in CI
```

**Correct — Python (pymongo / Motor / Beanie):**
```python
# app/db.py  — lazy, injectable accessor
_client = None
def get_client():
    global _client
    if _client is None:
        from pymongo import MongoClient
        _client = MongoClient(os.environ["DOCUMENTDB_URI"])
    return _client
def get_collection(name): return get_client()[DB_NAME][name]
```
```python
# tests/conftest.py
import os, pytest

class FakeCollection:
    def __init__(self, docs=None): self.docs = list(docs or [])
    def insert_many(self, docs): self.docs += docs
    def find(self, flt=None, *a, **k): return [d for d in self.docs if all(d.get(k) == v for k, v in (flt or {}).items())]
    def aggregate(self, pipeline, *a, **k):
        # keep it honest: only support the stages your code uses, assert on the pipeline shape
        self.last_pipeline = pipeline
        return iter(self.docs)

@pytest.fixture
def fake_collection(monkeypatch):
    col = FakeCollection()
    monkeypatch.setattr("app.db.get_collection", lambda name: col)
    monkeypatch.setattr("app.db.init_db", lambda *a, **k: None)   # Beanie/Motor: no-op startup
    return col

@pytest.fixture
def fake_embedder(monkeypatch):
    monkeypatch.setattr("app.embeddings.embed", lambda texts: [[0.0] * 8 for _ in texts])

def pytest_collection_modifyitems(config, items):
    if os.getenv("DOCUMENTDB_URI"): return
    skip = pytest.mark.skip(reason="integration test: set DOCUMENTDB_URI")
    for item in items:
        if "integration" in item.keywords: item.add_marker(skip)
```
```ini
# pytest.ini
[pytest]
markers = integration: needs a live DocumentDB (local Gateway or cluster)
```
```python
# tests/integration/test_vector_query.py
@pytest.mark.integration
def test_cosmos_search_returns_neighbours(): ...   # real cosmosSearch, real container
```
Mention `mongomock` as an acceptable drop-in for plain CRUD/aggregation shapes, with the explicit caveat that it does not implement `cosmosSearch`, `$search`, or DocumentDB index options.

**Correct — Node (mongodb driver / Mongoose, jest):**
```js
// src/db.js — lazy accessor
let client;
export async function getDb() {
  if (!client) { const { MongoClient } = await import("mongodb"); client = new MongoClient(process.env.DOCUMENTDB_URI); await client.connect(); }
  return client.db(process.env.DB_NAME);
}
```
```js
// tests/unit/orders.test.js
jest.mock("../../src/db.js", () => {
  const docs = [];
  const col = { insertMany: async d => docs.push(...d), find: () => ({ toArray: async () => docs }),
                aggregate: pipeline => ({ toArray: async () => { col.lastPipeline = pipeline; return docs; } }) };
  return { getDb: async () => ({ collection: () => col }) };
});
```
```json
// package.json
"scripts": { "test": "jest tests/unit", "test:integration": "jest tests/integration --runInBand" }
```
with each `tests/integration/*.test.js` wrapping its suite in `const describeIfLive = process.env.DOCUMENTDB_URI ? describe : describe.skip; describeIfLive("orders (live DocumentDB)", () => { ... });` so the whole file is skipped, not just one placeholder test, when no URI is set. (If the sample uses ESM `export`, the jest config needs `babel-jest` or `--experimental-vm-modules` for `jest.mock` to apply.)

**Correct — Gateway container for the integration tier:**
```yaml
# docker-compose.test.yml
services:
  documentdb:
    image: ghcr.io/documentdb/documentdb/documentdb-local:latest
    ports: ["127.0.0.1:10260:10260"]
    environment:
      - USERNAME=docdbuser
      - PASSWORD=${DOCUMENTDB_PASSWORD:?}
      - SKIP_INIT_DATA=true
```
```bash
docker compose -f docker-compose.test.yml up -d
./wait-for-port.sh 10260
export DOCUMENTDB_URI="mongodb://docdbuser:${DOCUMENTDB_PASSWORD}@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256"
pytest -m integration            # or: npm run test:integration
docker compose -f docker-compose.test.yml down
```
State explicitly: `tlsAllowInvalidCertificates=true` is for the self-signed local cert only; the Azure DocumentDB connection string (`mongodb+srv://...mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000`) must not carry it (cross-link `local-env-driven-config`).

**Correct — CI split:**
```yaml
jobs:
  unit:        { runs-on: ubuntu-latest, steps: [checkout, setup, run: pytest -m "not integration"] }
  integration:
    runs-on: ubuntu-latest
    services: { documentdb: { image: ghcr.io/documentdb/documentdb/documentdb-local:latest, ports: ["10260:10260"], env: { USERNAME: docdbuser, PASSWORD: ${{ secrets.DOCUMENTDB_PASSWORD }} } } }
    env: { DOCUMENTDB_URI: mongodb://docdbuser:${{ secrets.DOCUMENTDB_PASSWORD }}@localhost:10260/?tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256 }
    steps: [checkout, setup, run: ./wait-for-port.sh 10260, run: pytest -m integration]   # service containers start before steps but the Gateway may not be ready yet
```

**README rule for samples.** A sample README must have a "Testing without cloud" section stating which command runs offline, which needs `DOCUMENTDB_URI`, and must not claim tests it does not ship.

### 2. Register the rule

- `skills/local-deployment/SKILL.md`: add under `## Rules`:
  `- [local-offline-test-harness](local-offline-test-harness.md) — Two-tier tests: mocked unit tests that need no cluster or API key; integration tests gated on \`DOCUMENTDB_URI\` and run against the Gateway container.`
- Front-matter `description`: append "two-tier test harness (mocked unit tests, env-gated integration tests)".
- `local-prod-parity.md`: change "Integration tests target the local Gateway container, not an in-memory MongoDB" to "...; unit tests may stub the driver — see `local-offline-test-harness`" so the two rules do not read as contradictory.

### 3. Copy-paste fixtures under `examples/local-testing/`

`python/conftest.py`, `python/pytest.ini`, `node/__mocks__/db.js`, `node/jest.config.js`, `docker-compose.test.yml`, `.github/workflows/tests.yml` — the snippets above as runnable files, mirroring how `examples/azure-deployment/` ships Bicep next to the azure-deployment skill. Use `examples/local-testing/` rather than `examples/testing/` so it is not confused with the kit's own top-level `testing/` eval harness (which already has its own `conftest.py` and `pytest.ini`).

## Evidence (run folders from the readiness experiment)

- `runs/11-preference-center-consent-store/20261124-204614/doc-gaps.md` — module-scope app import forces startup; tests cannot run offline
- `runs/13-basel-iii-capital-ratio-calculator/20261124-201926/05-audit.json` — requirement_results "Unit tests run without a live cluster": not_met
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/doc-gaps.md` — mongomock and live tests mixed, no skip markers
- `runs/10-multi-tenant-storefront-saas/20261124-184121/doc-gaps.md` — asks for exact Gateway docker invocation (10260, TLS) for `npm test`
- `runs/18-adverse-event-reporting-pipeline/20261124-195726/05-audit.json` — README claims pytest coverage; no tests present

Also hit: `04-customer-journey-mapper`, `05-churn-prediction-pipeline`, `07-voice-of-customer-sentiment-hub`, `15-digital-onboarding-orchestration`, `17-seasonal-trend-spotter-agent`.

## Verification

### 1. Already covered? partially_covered

Grepped `skills/` and `knowledge-base/` of the Azure/documentdb-agent-kit clone for `pytest`, `jest`, `mongomock`, `unittest`, `monkeypatch`, `mock`: no hits in any skill or knowledge-base file. The only testing guidance is in `skills/local-deployment/local-prod-parity.md`: "Integration tests target the local Gateway container, not an in-memory MongoDB" plus a 4-line `docker compose up -d documentdb / ./wait-for-port.sh 10260 / npm run test:integration / docker compose down` snippet. So the integration-tier container setup/teardown exists in outline, but there is no unit-test (no-cluster) pattern, fake collection, lazy-init guidance, marker/skip convention, LLM/embedder mocking, or CI split. `skills/local-deployment/SKILL.md` lists exactly seven rules (as the draft says) and its description includes "building integration tests". The repo's top-level `testing/` (conftest.py, pytest.ini, harness/) is the kit's own eval harness, not guidance for generated samples.

### 2. Premise true? confirmed (one figure corrected)

- Gateway image `ghcr.io/documentdb/documentdb/documentdb-local:latest`, port 10260, `USERNAME`/`PASSWORD`/`SKIP_INIT_DATA` env vars, `tls=true&tlsAllowInvalidCertificates=true&authMechanism=SCRAM-SHA-256` for the self-signed local cert: matches `skills/local-deployment/SKILL.md`, `local-docker-compose-setup.md`, `local-env-driven-config.md`, `local-connection-config.md`.
- Full-text search via `createSearchIndexes` + `$search` and vector search via `cosmosSearch`: matches `skills/full-text-search/SKILL.md` and the DocumentDB vector-search skill; mongomock does not implement these, so placing them in the integration tier is correct.
- The Azure connection-string shape quoted (mongodb+srv, mongocluster.cosmos.azure.com, tls=true, SCRAM-SHA-256, retrywrites=false, maxIdleTimeMS=120000) matches the reference facts; the rule that `tlsAllowInvalidCertificates` must not appear in the cloud string matches `local-env-driven-config.md`.
- Corrected: recounting `requirement_results` across all 117 `05-audit.json` files, the "Unit tests run without a live cluster" requirement is `not_met` in 65 runs and `partly_met` in 6 (draft said 67 and 5). Applied in the body.
- Corrected code: a top-level `test.skip(...)` placeholder in a jest file does not skip the other tests in that file; replaced with a `describe`/`describe.skip` switch. Added a readiness wait to the CI integration job, because GitHub Actions service containers are started but not guaranteed ready.

### 3. Maintainer skeptic: confirmed

Names concrete files (`skills/local-deployment/local-offline-test-harness.md`, `SKILL.md` rule list and description, a one-line edit to `local-prod-parity.md`, example files) and follows the existing rule template. The DocumentDB angle is specific: which features (cosmosSearch, $search, DocumentDB index options) cannot be mocked and must go to the Gateway container tier, and the local-vs-cloud TLS difference. It also removes an apparent conflict with `local-prod-parity.md`'s "not an in-memory MongoDB" line. Small edit applied: moved the examples to `examples/local-testing/` so they do not collide with the repo's own `testing/` harness. Acceptable as a PR with those edits.

## Finding ids

- F0546
- F0782
- F1187
- F1358
- F1673
- F1876
- F2170
- F2535
- F2923
- F3030
