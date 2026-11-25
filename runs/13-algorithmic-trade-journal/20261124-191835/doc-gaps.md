# Documentation and tooling gaps: 13-algorithmic-trade-journal

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Server-side max-drawdown aggregation example

- **What was missing:** A complete, tested, production-ready aggregation pipeline example that computes maximum drawdown purely server-side (using $setWindowFields, $reduce, or equivalent DocumentDB-supported stages) was not found in the discovered docs or skills.
- **Where the agent looked:** Searched DocumentDB skills (documentdb-query-optimization, documentdb-indexing), and Microsoft Learn pages for aggregation/windowing examples; readiness_findings and discovered_practices search logs show the gap.
- **Effect on this build:** Builder chose to compute max drawdown client-side (app/app/aggregations.py:56-73). This makes the implementation correct and deterministic, but prevents an example that demonstrates purely server-side computation for very large series and misses a teaching example for gallery users who want server-side-only solutions.
- **Suggested fix (learn_doc):** A 'Max drawdown with aggregation pipelines' documentation page showing: (1) a $match/$sort/$setWindowFields-based pipeline that computes cumulative P&L and peak-to-trough declines, (2) a $reduce or windowed approach for max-drawdown, (3) allowDiskUse considerations, explain() examples and explain('executionStats') guidance, and (4) fallbacks (client-side algorithm) with performance tradeoffs.

## [high] setWindowFields availability & examples

- **What was missing:** Clear guidance mapping cluster 'server-version' settings to availability of $setWindowFields and other windowing operators, plus a small examples page showing how to test for operator support (explain or server-version check).
- **Where the agent looked:** Searched for '$setWindowFields support Azure DocumentDB' on Microsoft Learn and in documentdb skills; only general compatibility pages were found, not the per-cluster actionable guidance.
- **Effect on this build:** Builder conservatively implemented drawdown client-side (app/app/aggregations.py:56-73). Without clear guidance an agent or builder may attempt server-side pipelines that fail or are inefficient on some clusters.
- **Suggested fix (discoverability):** Add a small 'operator availability by server-version' section in the compatibility docs and a one-page example showing how to detect support and fall back to client-side if needed.

## [high] Retry/backoff example in the agent kit

- **What was missing:** A concrete code sample in the documentdb-connection skill showing a small Python helper that wraps pymongo operations with exponential backoff + jitter and examples of which error codes to treat as retryable vs fatal.
- **Where the agent looked:** Searched documentdb-connection and connection-related skills; the conceptual guidance exists, but a short copy-paste-ready code snippet was not found.
- **Effect on this build:** The sample omitted application-level retries (app/app/db.py and app/app/journal.py) and thus may be brittle during transient network faults. The builder set serverSelectionTimeoutMS but did not implement backoff.
- **Suggested fix (sample_or_quickstart):** A one-file snippet 'pymongo_retry.py' demonstrating a retry_with_backoff decorator (initial_delay=150ms, factor=2, max_attempts=4) and examples of wrapping insert_one/aggregate calls; include guidance on idempotency keys or unique constraints for safe retries.

## [high] IaC resource-type disambiguation (mongoClusters vs databaseAccounts)

- **What was missing:** Clear, prominent guidance in the deployment docs that vCore clusters use Microsoft.DocumentDB/mongoClusters (not the older databaseAccounts resource), with Bicep/Terraform examples. The readiness notes show that agents can confuse the two.
- **Where the agent looked:** Searched Microsoft Learn pages and the agent kit; the authoritative mongoClusters templates page exists but agent guidance that disambiguates older docs from vCore cluster templates is thin.
- **Effect on this build:** If an agent or builder attempts to provide IaC and uses databaseAccounts templates, they'll target the wrong product model. This repo omitted IaC (not included), increasing the chance of user confusion when they try to repro the environment from IaC.
- **Suggested fix (naming_or_disambiguation):** Add a 'Deployment' note calling out Microsoft.DocumentDB/mongoClusters with example Bicep and Terraform snippets for a minimal cluster, a short explanation of why databaseAccounts is for RU-based Cosmos accounts, and a pointer to the mongoClusters template.

## [medium] Driver-version compatibility & pinning guidance

- **What was missing:** A compact compatibility note that lists recommended/pinned driver versions for common languages (Python/pymongo version recommended for DocumentDB) and the reason to pin (compatibility matrix).
- **Where the agent looked:** Searched Microsoft Learn quickstarts and skills; compatibility pages confirm 'drivers work' but do not give a recommended pinned version matrix for samples.
- **Effect on this build:** The sample pinned dependencies sensibly (app/requirements.txt) but external users and agents would benefit from a short authoritative note on which driver major/minor versions are tested/supported.
- **Suggested fix (discoverability):** Add a short 'Driver compatibility' table to the quickstart documenting supported driver ranges (e.g., 'pymongo 4.x supported; sample pins 4.4.0') and guidance on pinning.

## [medium] Tests: offline mocking patterns

- **What was missing:** A short example showing how to write unit tests for DocumentDB-backed code using mongomock or by patching app.db.get_db, so unit tests run without a live cluster.
- **Where the agent looked:** Searched skills/local-deployment and sample tests; the seed/idempotence guidance exists but the exact mocking pattern for unit tests (mongomock example) was not present in the agent kit docs.
- **Effect on this build:** Current tests run against the live cluster (app/tests/test_aggregations.py), which prevents running unit tests in CI without a cluster. That increases friction for contributors.
- **Suggested fix (sample_or_quickstart):** Add a 'Testing' quickstart page with two patterns: (1) use mongomock for unit tests with an example that patches app.db.get_db to return mongomock.MongoClient().db, and (2) run integration tests gated by an env var or a pytest marker.

## [medium] Collection-level JSON Schema examples for event journals

- **What was missing:** Concrete JSON Schema validator examples tailored to event journals (requirements for strategy_id, type, timestamp, pnl), with commands to apply the validator at collection creation time.
- **Where the agent looked:** Searched for 'DocumentDB JSON Schema validator example' in skills and learn pages but no small event-journal-specific example was found.
- **Effect on this build:** The app uses Pydantic validation on incoming payloads but lacks a DB-level validator; malformed data could be inserted if callers bypass the API.
- **Suggested fix (learn_doc):** A one-page example showing createCollection with 'validator' option, example JSON Schema for the journal collection, and migration steps for applying validation to an existing collection.

