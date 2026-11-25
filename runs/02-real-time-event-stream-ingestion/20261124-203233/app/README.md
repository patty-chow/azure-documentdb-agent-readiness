DocumentDB Event Ingestion Sample

This sample demonstrates a Node.js (Express) service that accepts customer behavioral events and bulk-writes them to an Azure DocumentDB (MongoDB-compatible) cluster using unordered bulk operations for throughput. It also opens a change stream to trigger downstream profile update jobs.

Prerequisites
- Node.js 24+
- An Azure DocumentDB cluster (MongoDB-compatible). Connection string must be set in DOCUMENTDB_URI environment variable.
- The cluster must be reachable from your machine.

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI
   cp .env.example .env
   # edit .env and fill DOCUMENTDB_URI
2. Install dependencies
   npm install
3. Create DB / indexes
   npm run setup
4. Seed sample data (idempotent)
   npm run seed
5. Start the ingestion service
   npm start
6. In another terminal, run the change-stream watcher to see downstream jobs
   npm run watch

What the sample shows
- Unordered bulkWrite operations for ingestion (configurable batch size and flush interval).
- Compound unique index on (customerId, eventId) for deduplication.
- A change stream consumer that reacts to inserts and logs a simulated downstream job.

Files
- src/index.js — Express HTTP service exposing POST /events and /health
- src/db.js — MongoClient singleton and helpers
- src/ingest.js — Buffering and bulk-write logic
- src/setup.js — Ensures database and index exist
- src/watch.js — Change stream consumer that simulates downstream work
- scripts/seed.js — Idempotent seed script using upserts

Notes
- This sample reads secrets from environment variables. Do NOT commit real secrets.
- The sample writes data to the target cluster. Do not run against production clusters.

Verification
The build report included with this sample documents the commands I ran to verify creation of indexes and sample data.
