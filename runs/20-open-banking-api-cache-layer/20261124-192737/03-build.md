# 3. Build report: 20-open-banking-api-cache-layer

**Status: completed**

A small Node.js sample implementing an Open Banking API cache layer (stale-while-revalidate) using Mongoose against an Azure DocumentDB (MongoDB-compatible) cluster. The sample includes a reusable caching module (wrapper + Express middleware), a Mongoose model with a per-document TTL index (expiresAt), a one-shot demo that exercises miss→hit→stale-while-revalidate→forced-refresh flows, and verification using the DocumentDB MCP server to show the TTL index and a cached document.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string (do NOT commit it).
2) npm install
3) (optional) npm run seed  # creates one demo document
4) npm start               # runs the one-shot demo (starts a short-lived server, runs a few requests to demonstrate caching behavior, then exits)

Notes: The demo uses the database sample_fintech_20 and collection api_cache. Default demo TTLs are short (5s TTL, 10s stale window) so the demo completes quickly. For production, call createCache with larger ttlSeconds and staleWindowSeconds and tune connection pool settings in src/mongo.js.

## Verified by running

- npm install: succeeded (packages installed).
- demo run (node src/demo.js): succeeded. Observed behavior: initial network fetch (miss), immediate cache hit (fresh), request after TTL returned stale result and triggered background refresh, request after stale window performed synchronous network fetch. The demo exited cleanly.
- DocumentDB index inspection (documentdb_list_indexes for sample_fintech_20.api_cache): returned three indexes including the TTL index on expiresAt with expireAfterSeconds: 0.
- DocumentDB document inspection (documentdb_find_documents for sample_fintech_20.api_cache): returned a sample cached document showing response, cachedAt, expiresAt, and staleUntil fields as expected.

## Not verified

- No separate automated unit tests were run (the sample uses the live cluster for verification).
- Production-scale connection pool tuning and production security posture (Private Endpoint, RBAC, CMK) were not validated against organizational policies — the sample uses reasonable demo defaults but these need to be reviewed for production use.
- End-to-end verification of background refresh under heavy concurrency (race conditions / in-flight deduplication) was not stress-tested; the sample includes a simple in-flight guard but full concurrency tests are outside scope.

## Open issues

None.

## Files

- `package.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `src/mongo.js`
- `src/models/ApiCache.js`
- `src/cache.js`
- `src/seed.js`
- `src/demo.js`

