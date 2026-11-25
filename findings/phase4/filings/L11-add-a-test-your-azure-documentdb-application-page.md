---
id: L11
title: "Add a 'Test your Azure DocumentDB application' page"
repo: learn-docs
type: learn-feedback
status: needs_sme
priority: P1
sample_count: 58
member_drafts:
  - 080-develop-and-test-documentdb-apps-without-a-live-cluster-loca.md
open_questions: 4
---

# Add a "Test your Azure DocumentDB application" page

**Proposed page:** `/azure/documentdb/how-to-test-application` (Python and Node.js pivots), linked from the `development-loop` tutorial, both quickstarts' next steps and the hub page's *Developer and DevOps guides*.

## What happens today

The [`development-loop`](https://learn.microsoft.com/azure/documentdb/development-loop) tutorial is the only Learn page on local development. It runs the `ghcr.io/documentdb/documentdb/documentdb-local` container on port 10260 and connects with TLS and `tlsAllowInvalidCertificates`. Neither the hub page nor the quickstarts link to it. It has no unit tests, mocks, test database, test gating or CI job, and its code creates the `MongoClient` at module load, which makes the code hard to unit-test.

The Python and Node.js quickstarts never mention tests, mocks, Docker or CI. `/azure/documentdb/how-to-develop-locally` returns 404. documentdb.io and the Agent Kit cover only container-based integration tests; nothing covers offline unit tests: mocking the database factory, faking a Motor/Beanie client, stubbing Mongoose models, or generating deterministic test embeddings without an embedding-service key.

## Why it matters

In one run of an experiment where an AI coding agent built 100 Azure DocumentDB sample apps (with the Agent Kit skills and the DocumentDB, Azure and Learn MCP servers), **58 samples** (61 findings) hit this gap. Counts come from that single run and may shift on re-run [needs SME confirmation]. The agent:

- wrote no tests, or a placeholder `test` script;
- wrote tests that need a live cluster and a real embedding key, or tests that **skip silently when the URI is unset**, so CI passes without running any assertions;
- called Beanie's `init_db([...])` inside unit tests, which requires a reachable cluster;
- wrote a `MagicMock` whose `__getitem__` returned a new mock on each access, giving a false-negative test;
- fell back to Jest mocks after mongodb-memory-server could not start `mongod`, but left the README claiming memory-server;
- used a plain `mongo` image on port 27017, so tests pass locally while `cosmosSearch` and DocumentDB `createIndexes` payloads fail on the service;
- made up pseudo-embeddings with no guidance that they are test-only.

Its Learn searches for testing guidance found nothing.

## Proposed change

1. **Design for testability.** One lazy factory (`get_db()` / `getDb()`) reads the URI from the environment; never connect at import. With Beanie, call `init_beanie` from an `init_db()` the app runs at startup and unit tests skip.
2. **Tier 1: offline unit tests (no cluster, no API key).** Include short examples for:
   - pytest with `mongomock`, patching the factory via `monkeypatch`;
   - one `MagicMock` per collection, returned from a dict, so every access gets the same mock;
   - Motor/Beanie with `mongomock-motor`, plus Pydantic model tests without Beanie (check that the mock client matches the pinned Beanie version, since newer Beanie releases use PyMongo's async API; otherwise fall back to model-only tests plus Tier 2 [needs SME confirmation]);
   - Jest `jest.mock` of the db module, and `jest.spyOn` for Mongoose models;
   - a deterministic `fake_embed(text, dims)` returning a normalised `number[]`, labelled "unit-test/CI only, never seed data", with `dims` matching the `cosmosSearch` index. Mock the OpenAI, Azure OpenAI or LangChain embedding client to return it, and assert ranking and prompt-assembly logic, not vector quality.
   
   Present mongodb-memory-server as optional: it starts a real `mongod`, can fail on some platforms, and does not behave like DocumentDB; provide a mocks fallback and state in the README which one CI uses. Add a box on **what Tier 1 cannot test**: `explain()`, index creation, `cosmosSearch` (`vector-ivf`, `vector-hnsw`, `vector-diskann`), `$search`, transactions, change streams, SCRAM/TLS.
3. **Tier 2: integration tests against the local DocumentDB container.** Reuse the tutorial's setup, adding: pin the image tag and bind to `127.0.0.1:10260`; credentials work as `-e USERNAME/PASSWORD` or `--username/--password` (password required); sample data is off by default (`INIT_DATA=false`; `SKIP_INIT_DATA` is a legacy alias), and `INIT_DATA_PATH` loads schema scripts; wait for the ready log line, because `docker ps` shows `Up` earlier; set `tlsAllowInvalidCertificates` from the environment, never as a code default, or use `tlsCAFile`. Warning box: **a plain `mongo:*` image on port 27017 is not a substitute.** The local container runs the same open-source DocumentDB engine, but parity with the managed service is not guaranteed for every index kind or option; link the feature-support documentation and list any `cosmosSearch` kinds not available locally [needs SME confirmation].
4. **Tier 3: live-cluster tests, gating and CI.**
   - A dedicated `<app>_test` database with seed and teardown that drop only it.
   - `@pytest.mark.integration`, default `-m "not integration"`; skip *with a visible reason* when the URI is unset, fail when `CI_REQUIRE_INTEGRATION=1`; Jest `projects` for Node.js.
   - Scripts `test:unit` (default), `test:integration`, optional `test:stress`.
   - A CI job with **no Azure secrets** for unit tests on every PR, and a second job running the pinned container as a service, with credentials from non-production CI variables.
   - README "Testing" template text, and a table of what still needs a live cluster: index verification, vector and text search parity, `explain()` plans, Microsoft Entra ID auth.

For cloud connection strings, link the quickstarts' `mongodb+srv` format rather than restating it. Any connection string this page does show (Tier 2 local container, Tier 3 CI variables) must keep `retrywrites=false`, and the page should explain in one sentence why it is required, with the de-duplication reason: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Link the connection-string reference for the full explanation rather than restating more than that. Test guidance must not enable `retryWrites` to "make flaky tests pass"; a retried insert can report a duplicate key for a write that succeeded, which a test suite would misread as a bug.

Follow-ups outside this Learn item (separate repos, not part of this ask): the Agent Kit's `skills/local-deployment/local-prod-parity.md` should link this page, and the experiment harness's build and sample-prompt templates should reference it.

## Evidence

- `runs/14-loan-origination-workflow-orchestration/20261124-191837/05-audit.json`: unit tests call `init_db`, so they need a cluster.
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/doc-gaps.md`: fragile mock, false negative.
- `runs/06-collateral-management-store/20261124-200922/events.jsonl`: memory-server failed; README not updated.
- `runs/14-telehealth-session-summarizer/20261124-195137/05-audit.json`: tests skip without the URI; no mocks.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/doc-gaps.md`: `mongo:latest` is no parity substitute; no Learn guidance found.

The run told the agent that no local gateway was running, which discouraged Tier 2. Most findings are Tier 1 failures that this did not cause.

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).

## Open questions

1. Which `cosmosSearch` index kinds and options, and which features (transactions, change streams, `$search`), does the local container support compared with the managed service? [needs SME confirmation]
2. Does `mongomock-motor` still work for Beanie releases built on PyMongo's async API? [needs SME confirmation]
3. Which pinned `documentdb-local` tag should CI use? [needs SME confirmation]
4. The 58-sample count comes from one run that had harness artifacts. Should it be re-checked before being quoted publicly? [needs SME confirmation]

## Source drafts

- 080-develop-and-test-documentdb-apps-without-a-live-cluster-loca.md
