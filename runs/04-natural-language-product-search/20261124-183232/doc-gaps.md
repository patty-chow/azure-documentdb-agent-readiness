# Documentation and tooling gaps: 04-natural-language-product-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Automated index creation and safe defaults

- **What was missing:** A safe, opt-in script or seed flag that programmatically applies createSearchIndexes and createIndexes (vector) using the exact 'cosmosSearch' payload templates. The repo has templates but no automated, documented way to apply them.
- **Where the agent looked:** Repo indexes/ and events.jsonl; Microsoft Learn docs on createSearchIndexes and vector index creation (see vector-search and BM25 docs discovered by the agent).
- **Effect on this build:** The builder did not create indexes automatically and verification used fallbacks (regex and in-app cosine). As a result, the real $search BM25 and DB-side vector knn pipelines were not exercised during verification.
- **Suggested fix (agent_kit_rule):** Provide a small CLI script (e.g., scripts/create_indexes.py) that accepts --apply flag and runs db.command({createSearchIndexes: ...}) and db.command({createIndexes: ...}) using the templates in indexes/. Document that the script is opt-in and show exact mongosh/db.runCommand examples. Include checks to avoid applying templates to non-demo clusters (e.g., confirm env var APPLY_INDEXES=yes).

## [high] Pinning dependency versions for gallery samples

- **What was missing:** A pinned requirements.txt (or constraints file) showing exact package versions used during verification and a short policy in README that gallery samples must pin the dependencies they were tested with.
- **Where the agent looked:** app/requirements.txt and README.md in repo. No pinned versions present.
- **Effect on this build:** The sample installs latest versions which may change behaviour over time; CI or future builds may fail if upstream packages change API or break compatibility.
- **Suggested fix (agent_kit_rule):** Replace requirements.txt with pinned versions (requirements.txt or requirements.lock) and add a small note in README describing the pinned-test matrix (Python version, package versions). Optionally provide a workflow snippet showing how to regenerate pins (pip-tools or pip freeze).

## [high] Tests that run offline (no live cluster)

- **What was missing:** Unit tests and mocks allowing verification of rewrite, fusion, and search logic without a live DocumentDB cluster (e.g., using mongomock and mocking embedding clients).
- **Where the agent looked:** Repo root and app/; no tests found. Skills mention local-deployment but repository lacks tests.
- **Effect on this build:** Verification relied on live cluster for many steps; absence of offline tests reduces confidence and makes CI more brittle.
- **Suggested fix (sample_or_quickstart):** Add tests/ with pytest tests for rewrite_query, rrf_fusion, _vector_search fallback using mongomock for DB operations and monkeypatching a fake embedding client. Include guidance in README how to run them (pytest).

## [medium] Index tuning guidance for samples

- **What was missing:** Concise guidance in indexes/README.md and main README explaining how to change lBuild/lSearch/numLists/other vector params for datasets of different sizes and the memory/tier implications.
- **Where the agent looked:** indexes/README.md and app/README.md; Microsoft Learn vector-search pages.
- **Effect on this build:** The builder picked reasonable defaults but did not provide explicit tuning advice; users with larger catalogs may apply the templates without understanding tradeoffs, leading to poor recall/latency or excessive resource usage.
- **Suggested fix (learn_doc):** Add a section 'Index tuning for different dataset sizes' in indexes/README.md with tables: small (<=10k) -> vector-ivf example params; medium (10k-50k) -> vector-hnsw with recommended m/efConstruction; large (>50k) -> vector-diskann guidance. Include example db.runCommand snippets and a short checklist for choosing cluster tier (M30+) and monitoring index-build progress.

## [medium] README clean-up instructions

- **What was missing:** Explicit clean-up steps showing how to drop the sample database/collection and remove created indexes.
- **Where the agent looked:** app/README.md and indexes/README.md.
- **Effect on this build:** Users may leave seed data or indexes in their cluster after trying the sample.
- **Suggested fix (learn_doc):** Add a 'Clean up' section to README with exact mongosh commands: use sample_retail_04; db.products.drop(); db.runCommand({dropIndexes: 'products', index: 'default-vector-index'}) or show portal steps. Mention any IAM/role cleanup for created admin users.

## [medium] Explicit guidance on authentication options (SCRAM vs Entra ID)

- **What was missing:** A short paragraph in README explaining that production deployments should consider Microsoft Entra ID (OIDC) and Key Vault for secrets, and show where to find cluster authAllowedModes. The sample currently uses a connection string in env without commenting on Entra ID choices.
- **Where the agent looked:** README.md and skill docs; Microsoft Learn auth docs exist but the sample README doesn't mention them.
- **Effect on this build:** Users may not be aware they can use Microsoft Entra ID and might copy long-lived credentials into environments.
- **Suggested fix (discoverability):** Add an 'Authentication' subsection describing SCRAM vs MONGODB-OIDC (Entra ID), when to use each, and link to Learn's 'Connect to Azure DocumentDB using role-based access control' doc. Suggest Key Vault for secrets in production.

