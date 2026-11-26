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
open_questions: 3
---

# Add a "Test your Azure DocumentDB application" page

**Proposed page:** `/azure/documentdb/how-to-test-application` (Python and Node.js pivots), linked from the `development-loop` tutorial, both quickstarts' next steps and the hub page's *Developer and DevOps guides*.

## What happens today

The [`development-loop`](https://learn.microsoft.com/azure/documentdb/development-loop) tutorial is the only Learn page that walks through running the local container (the OSS overview page builds the engine from source and connects with psql on port 9712; the VS Code extension page only links out). It runs the `ghcr.io/documentdb/documentdb/documentdb-local` container (floating `:latest` tag) on port 10260 and connects with TLS and `tlsAllowInvalidCertificates`. Neither the hub page nor the quickstarts link to it. It has no unit tests, mocks, test database, test gating or CI job, and its code creates the `MongoClient` at module load, which makes the code hard to unit-test.

The Python and Node.js quickstarts never mention tests, mocks, Docker or CI. `/azure/documentdb/how-to-develop-locally` returns 404. documentdb.io and the Agent Kit cover only container-based integration tests; nothing covers offline unit tests: mocking the database factory, faking a Motor/Beanie client, stubbing Mongoose models, or generating deterministic test embeddings without an embedding-service key.

## Why it matters

In one run of an experiment where an AI coding agent built 100 Azure DocumentDB sample apps (with the Agent Kit skills and the DocumentDB, Azure and Learn MCP servers), **58 samples** (61 findings) hit this gap. Counts come from that single run, which had known harness defects, and will be recounted after the re-run. The agent:

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
   - Beanie: target Beanie 2 on PyMongo's `AsyncMongoClient`, as Learn's Beanie quickstart does ("This example uses Beanie 2 and PyMongo's asynchronous client, not Motor"; Beanie 1 with Motor is to be updated, and Motor was deprecated on 14 May 2025 with end of life on 14 May 2026). `mongomock-motor` fakes Motor, so it does not apply to Beanie 2: unit-test the Pydantic models without Beanie and cover `init_beanie` paths in Tier 2, until a mock for `AsyncMongoClient` that Beanie 2 accepts is confirmed [needs SME confirmation];
   - Jest `jest.mock` of the db module, and `jest.spyOn` for Mongoose models;
   - a deterministic `fake_embed(text, dims)` returning a normalised `number[]`, labelled "unit-test/CI only, never seed data", with `dims` matching the `cosmosSearch` index. Mock the OpenAI, Azure OpenAI or LangChain embedding client to return it, and assert ranking and prompt-assembly logic, not vector quality.
   
   Present mongodb-memory-server as optional: it starts a real `mongod`, can fail on some platforms, and does not behave like DocumentDB; provide a mocks fallback and state in the README which one CI uses. Add a box on **what Tier 1 cannot test**: `explain()`, index creation, `cosmosSearch` (`vector-ivf`, `vector-hnsw`, `vector-diskann`), `$search`, transactions, change streams, SCRAM/TLS.
3. **Tier 2: integration tests against the local DocumentDB container.** Reuse the tutorial's setup, adding: pin a versioned tag (`pg17-1.2.0` today; `latest` and `1.2` are floating aliases for it, `pg15-1.2.0` to `pg18-1.2.0` exist for amd64 and arm64, and the OSS docs say "Use a versioned tag when you need a reproducible setup") and bind to `127.0.0.1:10260`; credentials work as `-e USERNAME/PASSWORD` or `--username/--password` (the container exits at startup without a password); the StoreData sample set is opt-in (`--init-data true` or `INIT_DATA=true`; `SKIP_INIT_DATA` is a legacy alias for `--init-data false`), and `INIT_DATA_PATH` loads schema scripts; wait for the ready log line, because `docker ps` shows `Up` earlier; the image defaults to `--tlsMode allowTLS` with a self-signed certificate generated on first start (valid 365 days, not renewed), so set `tlsAllowInvalidCertificates` from the environment, never as a code default, or supply your own certificate with `--cert-path`/`--key-file` and use `tlsCAFile`; `authMechanism=SCRAM-SHA-256` is negotiated and need not be in the URI. Warning box: **a plain `mongo:*` image on port 27017 is not a substitute.** Parity box (settled from the open-source engine and documentdb.io, because no Learn page states it): the local container runs the open-source DocumentDB engine and differs from the managed service as follows. `cosmosSearch` supports `vector-ivf` and `vector-hnsw` only, up to 2,000 dimensions uncompressed and 4,000 with `compression: "half"`; `vector-diskann`, `pq` compression and 16,000 dimensions are Azure-only. `createSearchIndexes` returns code 115 `CommandNotSupported` ("Command 'createSearchIndexes' not supported."), and `$search` is vector-only (`cosmosSearch`), so a full-text `text` operator is rejected ("Unrecognized $search option: text"). Change streams fail with code 115 ("Stage $changeStream is not supported yet in native pipeline"; documentdb/documentdb#50 is open, and its stated Q3 2026 target has passed with no newer date). Multi-document transactions work with the default read concern, but `readConcern: { level: "snapshot" }` is rejected with code 115 (documentdb/documentdb#736), while the managed service accepts it. Only SCRAM-SHA-256 is offered, so Microsoft Entra ID (MONGODB-OIDC) cannot be tested locally. Some differences run the other way, so a passing local test does not prove the behaviour on the service (managed test of 2026-11-25): `w` of 2 or more is accepted silently by documentdb-local 1.2.0 but rejected by the service with `BadValue` and not applied; client-level `bulkWrite` is refused client-side by PyMongo locally (wire version 21) but sent by PyMongo 4.20.1 on an 8.0 cluster (wire version 25) and rejected at run time with code 2 (other drivers were not tried); `hello` and `buildInfo` report wire version 21 and 7.0.0 locally against 25 and 8.0.0 on an 8.0 cluster. Link the issues rather than promising dates.
4. **Tier 3: live-cluster tests, gating and CI.**
   - A dedicated `<app>_test` database with seed and teardown that drop only it.
   - `@pytest.mark.integration`, default `-m "not integration"`; skip *with a visible reason* when the URI is unset, fail when `CI_REQUIRE_INTEGRATION=1`; Jest `projects` for Node.js.
   - Scripts `test:unit` (default), `test:integration`, optional `test:stress`.
   - A CI job with **no Azure secrets** for unit tests on every PR, and a second job running the pinned container as a service, with credentials from non-production CI variables.
   - README "Testing" template text, and a table of what still needs a live cluster: index verification on the managed service, `vector-diskann` and `pq` compression (or vectors above 4,000 dimensions), full-text `$search` and `createSearchIndexes`, change streams, snapshot read concern (accepted by the service in transactions, rejected locally), write concern `w` of 2 or more (rejected by the service, accepted locally), client-level `bulkWrite` (fails at run time on an 8.0 cluster with PyMongo 4.20.1), `explain()` plans, Microsoft Entra ID auth. Plan and latency checks right after a bulk load can measure the wrong plan: on the managed service indexed queries appear to have run as full scans until autovacuum had run, at a time that varied (an `executionStats` explain still showed an `IXSCAN` with one document examined; `allPlansExecution` and latency indicated the full scan), and whether `COLLSCAN` shows depends on the vacuum state and the explain verbosity.
5. **Related Learn fixes on the same topic.** The `development-loop` tutorial pulls `documentdb-local:latest` with no versioned-tag guidance, says nothing about the parity gaps listed under Tier 2, and names the container `documentdb` where every other Microsoft source uses `documentdb-local`; add the tag guidance and link the new page's parity box from it. The `limitations` page has no statement that feature availability differs on the local container (DiskANN, `pq` compression, the full-text preview, change streams and Entra ID are cluster-only, and snapshot read concern in transactions and `w` of 2 or more behave differently); add a local-container line and cross-link the new page.

For cloud connection strings, link the quickstarts' `mongodb+srv` format rather than restating it. Any connection string this page does show (Tier 2 local container, Tier 3 CI variables) must keep `retrywrites=false`, and the page should explain in one sentence why it is required, with the de-duplication reason: "Keep `retrywrites=false` in every Azure DocumentDB connection string. The service does not support retryable writes: the server does not de-duplicate a retried write, so a driver retry can apply a non-idempotent write twice. Handle transient write failures in application code with idempotent operations (upserts, deterministic keys)." Link the connection-string reference for the full explanation rather than restating more than that. Test guidance must not enable `retryWrites` to "make flaky tests pass"; a retried insert can report a duplicate key for a write that succeeded, which a test suite would misread as a bug.

Follow-ups outside this Learn item (separate repos, not part of this ask): the Agent Kit's `skills/local-deployment/local-prod-parity.md` should link this page and list the parity differences above (its vector-search skill advertises DiskANN, `pq` and 16,000 dimensions without the local caveat), the kit's CI should move off its orphaned 1.0.0 digest pin to a current versioned tag, and the experiment harness's build and sample-prompt templates should reference this page.

## Evidence

- `runs/14-loan-origination-workflow-orchestration/20261124-191837/05-audit.json`: unit tests call `init_db`, so they need a cluster.
- `runs/17-stress-testing-multi-agent-runner/20261124-202407/doc-gaps.md`: fragile mock, false negative.
- `runs/06-collateral-management-store/20261124-200922/events.jsonl`: memory-server failed; README not updated.
- `runs/14-telehealth-session-summarizer/20261124-195137/05-audit.json`: tests skip without the URI; no mocks.
- `runs/08-regulatory-compliance-rag-checker/20261124-190949/doc-gaps.md`: `mongo:latest` is no parity substitute; no Learn guidance found.

The run told the agent that no local gateway was running, which discouraged Tier 2. Most findings are Tier 1 failures that this did not cause.

## Resolved

- retryWrites: answered 2026-11-25, see findings/phase4/DECISIONS.md. Retryable writes are not supported; retrywrites=false is required; the server does not de-duplicate retried writes (documentdb/documentdb#767).
- Local container parity (former open question 1): settled 2026-11-25 from the open-source engine (commit a5f1636) and documentdb.io, since no Learn page states it. documentdb-local supports `vector-ivf` and `vector-hnsw` (2,000 dimensions uncompressed, 4,000 with `half`; no DiskANN, no `pq`), rejects `createSearchIndexes` and `$changeStream` with code 115, rejects full-text `$search` operators ("Unrecognized $search option: text"; `$search` there is vector-only), runs multi-document transactions with the default read concern but rejects snapshot read concern (documentdb/documentdb#736), and offers SCRAM-SHA-256 only (no Entra ID). Sources: findings/phase4/DECISIONS.md topic 12; https://documentdb.io/docs/reference/operators/aggregation/$vectorsearch/; https://documentdb.io/docs/reference/operators/aggregation/$search/; https://documentdb.io/docs/reference/operators/aggregation/$changestream/; https://github.com/documentdb/documentdb/issues/736; https://github.com/documentdb/documentdb/issues/803; https://github.com/documentdb/documentdb/issues/50; https://learn.microsoft.com/en-us/azure/documentdb/limitations. The managed test of 2026-11-25 confirmed the cluster side (change streams, full-text search, DiskANN and MONGODB-OIDC present) and found differences a local test cannot catch: snapshot read concern is accepted in transactions by the service, `w` of 2 or more is rejected by the service but accepted by documentdb-local 1.2.0, and PyMongo 4.20.1's client-level `bulkWrite` fails at run time on the service (code 2) but is refused client-side locally; other drivers were not tried (ENGINE-TESTS.md, Managed service; DECISIONS.md topic 12, "Managed vs local").
- Available image tags (the factual part of the CI-pin question): settled 2026-11-25. `latest` and `1.2` point to `pg17-1.2.0`; `pg15-1.2.0` to `pg18-1.2.0` exist for amd64 and arm64; the OSS docs recommend a versioned tag for reproducible setups, while Learn's development-loop tutorial still shows `:latest`. Sources: https://documentdb.io/docs/documentdb-local/; https://documentdb.io/docs/getting-started/release-notes-1.2; https://learn.microsoft.com/en-us/azure/documentdb/development-loop.
- Beanie and Motor (reframes the mock-client question): settled 2026-11-25. Learn's Beanie quickstart uses Beanie 2 on PyMongo's `AsyncMongoClient` and tells Beanie 1 + Motor users to update; Motor was deprecated 14 May 2025, end of life 14 May 2026, critical fixes until 14 May 2027, per the Motor page; MongoDB's PyMongo migration guide still gives 14 May 2026 as the deprecation date, a one-year discrepancy in MongoDB's own docs. Sources: https://learn.microsoft.com/en-us/azure/documentdb/quickstart-python-beanie; https://beanie-odm.dev/changelog/; https://www.mongodb.com/docs/drivers/motor/; https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/.

## Open questions

1. Which mock stands in for PyMongo's `AsyncMongoClient` in Beanie 2 unit tests, now that Learn requires Beanie 2 without Motor and `mongomock-motor` no longer applies? Until confirmed, the page recommends model-only tests plus Tier 2. [needs SME confirmation]
2. Which exact `documentdb-local` tag or digest should CI pin? Maintainer decision (no source names a preferred pin): DECISIONS.md's best guess is `pg17-1.2.0` by digest, bumped deliberately on each DocumentDB release, with `:latest` kept only in copy-paste quickstarts.
3. The 58-sample count comes from one run with known harness defects; recount after the re-run before quoting it publicly.

## Source drafts

- 080-develop-and-test-documentdb-apps-without-a-live-cluster-loca.md
