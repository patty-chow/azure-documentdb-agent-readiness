06-omnichannel-interaction-history

This sample shows how to store customer interactions from multiple channels in a single Azure DocumentDB (Mongo-compatible) collection and expose history and channel-breakdown endpoints.

Prerequisites
- Node.js 24+
- A reachable Azure DocumentDB cluster; set its connection string in DOCUMENTDB_URI environment variable

Setup
1. npm install
2. cp .env.example .env and set DOCUMENTDB_URI
3. npm run seed  # idempotently insert sample data into database `sample_customer_360_06`
4. npm start

API
- GET /interactions/history?customerId=<id>&limit=<n>&cursor=<cursor>
  - Returns time-ordered interactions for a customer. Use the returned `nextCursor` for pagination.

- GET /interactions/channel-breakdown[?customerId=<id>]
  - Returns counts grouped by channel. If customerId provided, returns breakdown for that customer.

Notes
- The app reads DOCUMENTDB_URI from environment and will not write any secrets.
- The sample creates compound indexes on (customerId, timestamp) and (channel, timestamp).
- To verify indexes and documents against the live cluster, use the DocumentDB MCP server tools (documentdb_list_indexes, documentdb_find_documents, documentdb_explain_operation) if available.
