# 3. Build report: 06-omnichannel-interaction-history

**Status: completed**

Implemented a small Node.js + Express + Mongoose sample that stores omnichannel customer interaction documents in a single Azure DocumentDB collection (database: sample_customer_360_06, collection: interactions). The app creates the two required compound indexes, provides a seed script to idempotently upsert sample data, and exposes REST endpoints for paginated customer history and channel-breakdown aggregation. I verified index creation and ran sample queries against the live cluster using the provided DOCUMENTDB_URI environment variable and the documentdb MCP server tools.

## How to run

1) Install dependencies: npm install
2) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string
3) Seed sample data (idempotent upserts): npm run seed
4) Run the one-shot test query example (does not start long-running server): npm run test-queries
5) To run the HTTP server locally: npm start (server listens on PORT or 3000). Note: in this build run I did not start the long-running server; the test queries exercise the same data access logic.

API endpoints (when server is running):
- GET /interactions/history?customerId=<id>&limit=<n>&cursor=<cursor>
  - Returns time-ordered interactions for a given customer. Uses a base64-encoded cursor with {ts, id} for stable pagination.
- GET /interactions/channel-breakdown[?customerId=<id>]
  - Returns counts grouped by channel; optional customerId filters the aggregation.

## Verified by running

- npm install: completed (dependencies installed)
- npm run seed: completed — upserted 6 sample documents (int-1..int-6) into database sample_customer_360_06
- npm run test-queries: completed — returned recent history for cust-1 and overall channel breakdown (printed to stdout)
- documentdb_list_indexes (documentdb MCP server, connection_profile 'default'): returned indexes for sample_customer_360_06.interactions including compound indexes customerId_1_timestamp_-1 and channel_1_timestamp_-1

## Not verified

- Starting and leaving the HTTP server running (npm start) was not executed here because the run tool should not be used to start long-running processes in this environment. The server can be started locally with npm start following the README instructions.
- Exact recommended pinned Mongoose minor/patch version that guarantees compatibility with MongoDB wire protocol 7.0/8.0 on the target cluster: the readiness report flagged an information gap; I selected Mongoose ^7 (7.x) as a reasonable, modern choice but could not confirm a single 'recommended' exact version from authoritative docs in this run. (Decision logged as model_default.)

## Open issues

None.

## Files

- `package.json`
- `.gitignore`
- `.env.example`
- `README.md`
- `src/models/interaction.js`
- `src/index.js`
- `data/sample-data.json`
- `scripts/seed.js`
- `scripts/test_queries.js`

