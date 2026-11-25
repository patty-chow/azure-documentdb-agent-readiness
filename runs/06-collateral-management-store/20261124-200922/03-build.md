# 3. Build report: 06-collateral-management-store

**Status: completed**

Created a small Node.js (Express + Mongoose) sample that stores versioned collateral assets in Azure DocumentDB, enriches documents with an LLM classification step (configurable), provides endpoints to add asset versions and to compute a total collateral coverage ratio, includes an idempotent seed script that inserts sample data into the required database, and tests that run offline via mocks. Verified by running npm install, unit tests, seeding the live cluster, and inspecting the created database/collection and aggregation explain plan via the DocumentDB MCP tools.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI (mongodb+srv... with TLS). Optionally set OPENAI_API_KEY and MODEL_NAME, or set DISABLE_LLM=true to skip LLM calls.
2) npm install
3) npm run seed (loads idempotent sample data into DB named sample_banking_06)
4) npm start (starts the Express API on PORT, default 3000)

API endpoints:
- POST /assets  (body: { assetId, valuation: { amount, currency }, metadata, embedding? }) — inserts a new versioned document and runs classification (unless disabled)
- GET /assets/:assetId/history — returns version history for an asset
- GET /coverage?totalLiabilities=NUMBER&eligibleOnly=true — returns { totalCollateral, totalLiabilities, coverageRatio, count }

Tests: npm test runs unit tests (jest). Tests are offline-mock based; they mock the Mongoose model so the tests do not require mongod or the live cluster.

## Verified by running

- npm install: completed successfully (dependencies installed).
- jest unit tests: passed (tests use model mocks; mongodb-memory-server attempted earlier but failed on this platform, so tests were switched to mocking; final run passed).
- npm run seed: ran successfully and inserted sample documents (7 total) into database 'sample_banking_06'.
- documentdb_list_databases via MCP tool: returned 'sample_banking_06' (present) and 'test'.
- documentdb_find_documents via MCP tool: sample documents returned from collection 'collateral_assets' in database 'sample_banking_06' (7 documents, sample output inspected).
- documentdb_explain_operation via MCP tool: returned an explain of the aggregation pipeline used by /coverage (execution plan and stats returned).

## Not verified

- Starting the long-running server and manual integration tests with a live LLM: I did not run the HTTP server against a real OpenAI API key (DISABLE_LLM=true by default); the sample supports live LLMs but environment must supply OPENAI_API_KEY and MODEL_NAME. Reason: to keep verification safe and reproducible in this run I left DISABLE_LLM=true in .env.example; callers can enable it locally.
- Vector index creation and end-to-end vector queries: Embeddings are optional in the schema and vector-index creation is documented in README, but the sample did not create any vector indexes or generate embeddings during seed or tests. This was a deliberate choice (optional feature) because embedding dims and model choice are environment-dependent.
- Full production connection tuning (pool sizes, CMK, private endpoints): sample uses sensible defaults and documents where to tune; no production-scale validation was done here.

## Open issues

- Initial seed run used the default database from the connection string; I corrected the code to explicitly connect to database 'sample_banking_06' (DB_NAME env var). If you previously ran the seed, you may have sample data in another DB — drop those if you want to avoid duplicates.
- mongodb-memory-server could not start in this environment (spawn Unknown system error -86). Per instructions I stopped attempting to use it and switched tests to mock the Mongoose model so tests remain offline and CI-friendly. If you want real integration tests, run them locally where mongod/memory-server can spawn, or use the live DOCUMENTDB_URI with caution.

## Files

- `package.json`
- `package-lock.json`
- `src/index.js`
- `src/models/collateral.js`
- `src/llm/classifier.js`
- `src/routes/assets.js`
- `src/routes/coverage.js`
- `scripts/seed.js`
- `.env.example`
- `README.md`
- `tests/assets.test.js`
- `tests/asset.test.js`

