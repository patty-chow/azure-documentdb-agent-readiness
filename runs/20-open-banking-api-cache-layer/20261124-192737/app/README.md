Azure DocumentDB: Open Banking API cache layer (stale-while-revalidate)

What this sample shows
- A Node.js (Express) middleware and HTTP-client wrapper using Mongoose to cache upstream API responses in Azure DocumentDB (MongoDB-compatible).
- Per-document TTL implemented with an expiresAt field and a TTL index.
- Stale-while-revalidate: serve stale data immediately while refreshing in the background.

Prerequisites
- Node.js >=18 (Node 24 available in the build environment)
- An Azure DocumentDB cluster reachable via the DOCUMENTDB_URI environment variable. Do NOT commit this string. See .env.example.
- The sample uses the database sample_fintech_20 and creates a collection named api_cache.

Quickstart
1. Copy .env.example -> .env and set DOCUMENTDB_URI.
2. npm install
3. npm run seed   # optional: seed a demo document
4. npm start      # runs src/demo.js which starts a short-lived server, runs several requests to demonstrate cache behavior, then exits

Files created
- src/mongo.js          Singleton Mongoose connect/disconnect helpers
- src/models/ApiCache.js Mongoose schema and TTL index on expiresAt
- src/cache.js          The caching layer; createCache({ttlSeconds, staleWindowSeconds, fetcher})
- src/demo.js           Demo server that runs a one-shot demonstration and exits
- src/seed.js           Optional seeding script
- .env.example          Example env file

Design notes
- The sample reads DOCUMENTDB_URI at runtime and connects with dbName=sample_fintech_20.
- TTL index uses expiresAt with expireAfterSeconds: 0 so each document can expire at a custom time.
- Default demo TTLs are short (5s TTL, 10s stale window) so the demo completes quickly. Configure as needed for production workloads.

Cleanup
- Run a delete on the collection or drop the sample_fintech_20 database via your portal/CLI if desired. The TTL index will eventually remove expired documents.

Security
- Never commit DOCUMENTDB_URI. Use environment variables or a secret store in production.
