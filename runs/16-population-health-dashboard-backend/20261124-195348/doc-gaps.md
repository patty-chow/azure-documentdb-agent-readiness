# Documentation and tooling gaps: 16-population-health-dashboard-backend

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Complete .env.example

- **What was missing:** The repository's .env.example only contains DOCUMENTDB_URI. The sample expects and uses other configurable values (cache name, TTL, refresh schedule, optional pool sizing), but those are not listed.
- **Where the agent looked:** Inspected repo files (.env.example, README) and discovery searches for 'env example refresh schedule SUMMARY_NAME TTL_SECONDS'.
- **Effect on this build:** Developers must manually know these settings; the builder used sensible defaults in code (DEFAULT_SUMMARY_NAME, TTL_SECONDS, hourly refresh) rather than exposing them as env-configurable. This makes reproducing different schedules or cache names harder.
- **Suggested fix (learn_doc):** Add to .env.example and README entries: REFRESH_HOURS=1, SUMMARY_NAME=default_cohort, TTL_SECONDS=86400, MAX_POOL_SIZE=100, SOCKET_TIMEOUT_MS=20000, RETRY_WRITES=false (or instruction that retryWrites is set in the connection string). Document what each does and defaults used in code.

## [high] DocumentDB guidance for materialized cache id naming

- **What was missing:** No public advice was found about naming conventions for deterministic cache document _id values for materialized summaries (what keys to include to guarantee idempotence and cache locality).
- **Where the agent looked:** Searched for 'deterministic cache _id materialized summary best practice' and similar phrases; discovery recorded no useful public hits.
- **Effect on this build:** The builder implemented a SHA256 of (name, params) which is reasonable, but agents may choose non-deterministic ids or naive UUIDs without guidance, breaking upserts and causing duplicate cache entries.
- **Suggested fix (learn_doc):** A short doc section 'Materialized summary id recommendations' recommending deterministic keys (hash of canonicalized params + summary name), examples in Python and how to handle param ordering, TTL, and collision considerations.

## [high] Public guidance to prefer $setOnInsert on upserts

- **What was missing:** Although the $setOnInsert operator exists in public docs, sample-level guidance to prefer using $setOnInsert when creating cache documents was not explicit in the repository's README.
- **Where the agent looked:** Repo README and skills resources; $setOnInsert docs exist but no sample snippet used it.
- **Effect on this build:** The upsert implementation currently overwrites createdAt on every refresh which loses insert-time metadata; this is a small correctness issue easily fixed, but an explicit sample guidance would prevent the mistake.
- **Suggested fix (discoverability):** Add a short 'Materialized cache upsert pattern' in the README showing an example use of update_one(..., {'$set': {...}, '$setOnInsert': {...}}, upsert=True).

## [medium] Driver-version compatibility table

- **What was missing:** No clear public, discoverable mapping in the repo that tells which pymongo version is recommended for the cluster wire-protocol/serverVersion targeted by the sample (the repo pins pymongo==4.5.0 but no rationale is present).
- **Where the agent looked:** Searched Microsoft Learn and installed skills for 'supported pymongo versions' and 'driver compatibility' but did not find a single, agent-friendly table mapping client driver versions to cluster serverVersion.
- **Effect on this build:** The sample pins a driver version; an agent or user might pick an incompatible version for a particular cluster serverVersion. This risks runtime errors on some clusters.
- **Suggested fix (discoverability):** A short Learn quickstart section or a line in the documentdb-driver skill that lists recommended driver versions (pymongo) for each supported serverVersion and known incompatibilities. Example: 'If cluster serverVersion=7.0, use pymongo >=4.4 and tested with 4.5.0'.

## [medium] Guidance for scheduler choice and refresh frequency

- **What was missing:** No public guidance in the skills or quickstarts recommends in-process APScheduler vs an external scheduled job (Functions/Logic Apps) or which default refresh frequency suits which workloads.
- **Where the agent looked:** documentdb-connection, documentdb-data-modeling, general operational guidance and README; no authoritative instruction on choosing scheduler patterns for demo vs production.
- **Effect on this build:** The builder chose an in-process APScheduler hourly refresh by default. That choice is reasonable for a sample but may be inadequate for production (observability, retries, scaling).
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule: 'For samples, prefer in-process scheduler when demonstrating behaviour only; add a README callout that production deployments should use an external scheduled job or serverless function; include an example Azure Function-based refresh in infra examples.'

## [medium] Test-database naming and teardown guidance

- **What was missing:** No authoritative public guidance found that recommends a test database name or teardown approach for DocumentDB sample tests (e.g., whether to use a separate 'sample_healthcare_16_test' DB and automated cleanup).
- **Where the agent looked:** Searched for 'DocumentDB testing separate test database tear down tests sample_healthcare_16_test' and related queries; no clear public best-practice was found.
- **Effect on this build:** The sample's unit tests are pure-Python and run without a cluster, but there is no pattern or helper for integration tests that would seed/tear-down a test DB; builders may be uncertain how to add integration tests safely.
- **Suggested fix (sample_or_quickstart):** Add a small 'Testing and CI' page: recommend using a separate test database name (e.g., <sample>_test), provide an optional test_seed.py that creates and drops test DB collections, and example CI snippets that require an env var TEST_DOCUMENTDB_URI pointed at a throwaway cluster.

## [low] Model-default decisions (Python minor, seed size, hourly refresh)

- **What was missing:** Several builder choices were made from model defaults rather than public guidance: Python minor version selection (3.11), seed size (5000), and default refresh frequency (1 hour).
- **Where the agent looked:** Readiness notes and decision logs; searches for explicit recommended defaults did not yield a single 'for samples use X' page.
- **Effect on this build:** These defaults are reasonable for a sample but inconsistent or undocumented defaults across samples can confuse users and agents.
- **Suggested fix (agent_kit_rule):** Add an Agent Kit rule file stating recommended defaults for gallery samples (target Python minor, seed sizes for small/medium/large demos, and recommended demo refresh frequencies), and suggest doc locations to override.

