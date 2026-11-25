---
title: "local-deployment: add a `local-test-tiers` rule (offline unit tests, DOCUMENTDB_URI-gated integration tests, mocked LLM calls)"
repo: Azure/documentdb-agent-kit
type: pr
status: ready_with_edits
priority: P2
sample_count: 7
findings: 7
bucket: learn-information_gap
verdicts:
  covered: partially_covered
  premise: confirmed
  maintainer: confirmed
---

# local-deployment: add a `local-test-tiers` rule (offline unit tests, `DOCUMENTDB_URI`-gated integration tests, mocked LLM calls)

## What happens today

`skills/local-deployment/SKILL.md` covers starting the Gateway image, Compose, connection config, env-driven config, seed data, ports and prod parity. `local-prod-parity.md` says "Integration tests target the local Gateway container, not an in-memory MongoDB" and shows `docker compose up && npm run test:integration`, but nothing in the kit says:

- which tests must run **offline** (no cluster, no LLM/embedding key) and how to structure code so they can;
- how integration tests are **gated** on `DOCUMENTDB_URI` and skipped, not failed, when it is absent;
- how to **fake embedding/LLM calls** so a RAG or agent sample is testable in CI;
- how to isolate test data (per-run database name, drop on teardown).

The kit's own `testing/conftest.py` already has the right pattern (`require_container` fixture that `pytest.skip`s when no password/container is present), but it is the kit's internal harness, not a rule an agent reads when building a sample.

## Why it matters

In a 100-sample agent-readiness run with gpt-5-mini plus this kit, 7 samples raised this exact gap in the readiness stage (01-anti-money-laundering-pattern-detector, 03-next-best-action-multi-agent, 05-appointment-scheduling-assistant, 06-order-history-timeline-agent, 06-symptom-triage-chatbot-rag, 18-adverse-event-reporting-pipeline, 20-identity-resolution-multi-agent). With no convention, the agent did one of three things:

- **Hit the live cluster from "unit" tests with no guard**: `06-order-history-timeline-agent/app/tests/test_db.py` calls `db.seed_sample(10)` and `count_documents` against whatever `DOCUMENTDB_URI` resolves to; `01-anti-money-laundering-pattern-detector/app/tests/test_seed_and_analysis.py` does `load_dotenv(); get_db().list_collection_names()` and assumes a seed has already been run. `pytest` fails with a connection error on a clean checkout.
- **Shipped placeholder tests**: `03-next-best-action-multi-agent` asserts `callable(orchestrate)`; `20-identity-resolution-multi-agent` tests only a Pydantic model. Nothing touching DocumentDB or the LLM is exercised.
- **Claimed tests that do not exist**: `18-adverse-event-reporting-pipeline/app/README.md` says "pytest will run lightweight unit tests (some integration tests require DOCUMENTDB_URI)" but the app has no `tests/` directory. The audit stage flagged "Owners may publish samples that claim test coverage they do not have."

A gallery that publishes these samples gets CI that is red without secrets or green without coverage.

## Proposed change

### 1. New rule file `skills/local-deployment/local-test-tiers.md`

```markdown
# local-test-tiers

**Category:** Local Deployment · **Priority:** HIGH

## Why it matters

A sample must be testable on a clean checkout with no cluster and no AI key, and
must also prove it works against real DocumentDB. Those are two tiers, not one
suite. Mixing them produces tests that fail in CI (no secrets) or tests that
never touch the database.

Rules:
- **Tier 1 – unit (always runs).** No driver import at module level, no network,
  no LLM/embedding key. Business logic (parsing, ranking, prompt assembly,
  aggregation-pipeline *construction*) takes the collection/client as a
  parameter or behind a small repository interface, so tests pass a stub.
  Embedding and chat calls go through one function/class that tests replace
  with a deterministic fake (fixed-dimension vectors, canned completions).
- **Tier 2 – integration (gated).** Marked `integration`. A session fixture reads
  `DOCUMENTDB_URI`; when unset it `skip`s with a message telling the developer
  to start the local Gateway. The documented value in `.env.example` points at
  the local container on `127.0.0.1:10260` (see `local-connection-config`);
  set `tlsAllowInvalidCertificates` only for that self-signed local endpoint,
  never for an Azure cluster. The same tests run
  unchanged against an Azure DocumentDB cluster when the URI points there.
  Do not use mongomock / mongodb-memory-server for this tier (see
  `local-prod-parity`): the Gateway is the real engine.
- **Isolate data.** Each run uses its own database name
  (`<sample>_test_<uuid8>`) and drops it on teardown. Never test against the
  sample's seed database.
- **README states the convention in one line**: "`pytest` runs offline unit
  tests; `pytest -m integration` needs `DOCUMENTDB_URI` (local Gateway or an
  Azure DocumentDB cluster)."

## Incorrect

```python
# tests/test_db.py — runs against whatever DOCUMENTDB_URI resolves to, or crashes
from app import db
def test_seed_and_queries():
    db.seed_sample(size=10)
    assert db.get_orders_collection().count_documents({}) >= 10
```

```python
# tests/test_orchestrator.py — proves nothing
def test_orchestrate_schema():
    assert callable(orchestrate)
```

## Correct

`pytest.ini`
```ini
[pytest]
markers =
    integration: needs DOCUMENTDB_URI (local Gateway on 10260 or an Azure DocumentDB cluster)
```

`tests/conftest.py`
```python
import os, uuid
import pytest

@pytest.fixture(scope="session")
def documentdb_uri():
    uri = os.getenv("DOCUMENTDB_URI")
    if not uri:
        pytest.skip("DOCUMENTDB_URI not set — start the local Gateway "
                    "(docker compose up -d documentdb) or point at a cluster")
    return uri

@pytest.fixture(scope="session")
def test_db(documentdb_uri):
    from pymongo import MongoClient
    allow_invalid = os.getenv("DOCUMENTDB_ALLOW_INVALID_CERTS", "false").lower() == "true"
    client = MongoClient(documentdb_uri, tlsAllowInvalidCertificates=allow_invalid)
    name = f"sample_test_{uuid.uuid4().hex[:8]}"
    yield client[name]
    client.drop_database(name)
    client.close()

import hashlib

class FakeEmbeddings:
    # Deterministic across processes: Python's built-in hash() of str is
    # salted per process (PYTHONHASHSEED), so derive vectors from hashlib.
    dim = 8
    def embed(self, texts):
        out = []
        for t in texts:
            d = hashlib.sha256(t.encode()).digest()
            out.append([d[i] / 255.0 for i in range(self.dim)])
        return out

@pytest.fixture
def fake_embeddings():
    return FakeEmbeddings()
```

`tests/test_ranking.py` (tier 1)
```python
def test_rank_by_similarity(fake_embeddings):
    from app.search import build_vector_pipeline
    q = fake_embeddings.embed(["refund"])[0]
    pipeline = build_vector_pipeline(q, k=3)
    assert pipeline[0]["$search"]["cosmosSearch"]["k"] == 3
    assert isinstance(pipeline[0]["$search"]["cosmosSearch"]["vector"][0], float)
```

`tests/test_orders_integration.py` (tier 2)
```python
import pytest
from app.repository import OrdersRepo

@pytest.mark.integration
def test_insert_and_find(test_db):
    repo = OrdersRepo(test_db["orders"])
    repo.insert({"order_id": "o1", "customer_id": "c1", "total": 10})
    assert repo.find_by_customer("c1")[0]["order_id"] == "o1"
```

CI:
```yaml
- run: pytest -m "not integration"          # always
- run: docker compose up -d documentdb && pytest -m integration   # when the job has Docker
  env: { DOCUMENTDB_URI: "${{ secrets.DOCUMENTDB_TEST_URI }}",   # points at 127.0.0.1:10260 (local Gateway, TLS, SCRAM-SHA-256)
         DOCUMENTDB_ALLOW_INVALID_CERTS: "true" }                # local Gateway only: self-signed cert
```

Node/Jest equivalent (Jest has no `describe.skipIf`; that is Vitest): guard with
`const uri = process.env.DOCUMENTDB_URI; (uri ? describe : describe.skip)("integration", ...)`,
`jest.mock("../src/embeddings")` for tier 1, and `--testPathIgnorePatterns integration` in the default `npm test`.

## References

- `local-prod-parity`, `local-env-driven-config`, `local-connection-config`
- pytest markers: https://docs.pytest.org/en/stable/how-to/mark.html
```

### 2. `skills/local-deployment/SKILL.md`

Add to the Rules list, after `local-prod-parity`:

```markdown
- [local-test-tiers](local-test-tiers.md) — Unit tests run offline with a fake embeddings/LLM client; integration tests are marked and skipped unless `DOCUMENTDB_URI` is set (local Gateway or an Azure DocumentDB cluster), using a disposable per-run database.
```

and extend the frontmatter `description` with "two-tier test layout (offline unit, `DOCUMENTDB_URI`-gated integration)" so the skill is selected when an agent is writing tests.

### 3. `skills/local-deployment/local-prod-parity.md`

Change the bullet "**Test what prod does.** Integration tests target the local Gateway container, not an in-memory MongoDB — avoiding behaviour drift." to end with "See `local-test-tiers` for the gating and fixture pattern."

## Evidence (run folders from the experiment)

- `runs/06-order-history-timeline-agent/20261124-183612/app/tests/test_db.py` — unguarded live-cluster "unit" test; gap recorded in `02-readiness.json` information_gaps ("Unit-test strategy for offline runs")
- `runs/01-anti-money-laundering-pattern-detector/20261124-200112/app/tests/test_seed_and_analysis.py` — `load_dotenv(); get_db()` in tests, assumes seed already ran; `02-readiness.json` "Test isolation strategy for unit tests"
- `runs/18-adverse-event-reporting-pipeline/20261124-195726/05-audit.json` — doc_gaps "Testing strategy for DocumentDB samples (unit vs integration)", proposed_fix_type `agent_kit_rule`; README claims pytest coverage, no `tests/` shipped
- `runs/03-next-best-action-multi-agent/20261124-203319/02-readiness.json` — "Unit-test mocking strategy for LLM / external calls"; shipped test is `assert callable(orchestrate)`
- `runs/20-identity-resolution-multi-agent/20261124-210002/02-readiness.json` — "Run/test matrix (mocked vs live)"

Also raised in `runs/05-appointment-scheduling-assistant/20261124-193733/02-readiness.json` and `runs/06-symptom-triage-chatbot-rag/20261124-193845/02-readiness.json`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)


## Verification

### 1. Already covered? — partially_covered
The kit points at integration testing against the Gateway but gives no layout, gating or fake-LLM pattern.
- `skills/local-deployment/local-prod-parity.md`: "**Test what prod does.** Integration tests target the local Gateway container, not an in-memory MongoDB — avoiding behaviour drift." plus a `npm run test:integration` snippet. Nothing on offline unit tests, skip-when-unset or test-data isolation.
- `skills/local-deployment/SKILL.md` description mentions "building integration tests", and its Rules list has no testing rule (rules: choose-deployment-method, connection-config, docker-compose-setup, env-driven-config, ports-and-bindings, prod-parity, sample-data-management).
- `testing/conftest.py` (`require_container`) calls `pytest.skip("No DB password configured ...")` / `pytest.skip(f"DocumentDB container '{container_name}' is not running ...")`. This is the kit's own scenario harness, not a skill rule that an agent loads.
- A grep of `skills/` and `knowledge-base/` for pytest, jest, mock, unit test and integration finds no testing-convention rule. The Learn docs were not checked further because the fix target is the agent kit.

### 2. Premise true? — confirmed (code fixes applied)
- The Gateway listens for the MongoDB wire protocol on 10260 with TLS and SCRAM-SHA-256 (`local-ports-and-bindings.md`, `local-connection-config.md`). Its self-signed certificate is why `tlsAllowInvalidCertificates` is used locally only.
- The vector stage shape `{"$search": {"cosmosSearch": {"vector": [...], "path": ..., "k": N}}}` matches Azure DocumentDB vector search, with vectors as number[].
- Pytest custom markers in `pytest.ini` and `pytest.skip` inside a session fixture are valid (https://docs.pytest.org/en/stable/how-to/mark.html). `--testPathIgnorePatterns` is a valid Jest CLI option.
- The evidence was checked on disk. `runs/06-order-history-timeline-agent/20261124-183612/app/tests/test_db.py` calls `db.seed_sample(size=10)` and `count_documents` with no guard. `runs/18-adverse-event-reporting-pipeline/20261124-195726/app/tests` does not exist.
- Corrections applied to the body:
  - (a) The `FakeEmbeddings` example used Python's built-in `hash()`, which is salted per process for `str` (PYTHONHASHSEED), so it was not deterministic as the rule claimed. It now uses `hashlib.sha256`.
  - (b) The draft called the Jest guard "`describe.skipIf`-style". `describe.skipIf` is Vitest, not Jest, so the body now says so and keeps the `(uri ? describe : describe.skip)` guard.
  - (c) The CI snippet built a full connection string inline. It now reads a `DOCUMENTDB_TEST_URI` secret.
  - (d) The draft said the fixture "defaults" to the local Gateway, but the fixture skips when the URI is unset. The body now says the `.env.example` value points at the Gateway, and adds that invalid-cert tolerance is for the local endpoint only.

### 3. Maintainer skeptic — confirmed
The draft names exact files: new `skills/local-deployment/local-test-tiers.md`, plus edits to `SKILL.md` Rules/description and `local-prod-parity.md`. It follows the kit's Why/Incorrect/Correct rule format. It is specific to DocumentDB (the Gateway container on 10260, cosmosSearch pipeline construction, and it rejects in-memory MongoDB for consistency with the existing parity rule). Azure/documentdb-agent-kit is the right repo, and I would accept it with the small edits applied.

## Finding ids
- F0015
- F0435
- F0710
- F0954
- F0983
- F3026
- F3373
