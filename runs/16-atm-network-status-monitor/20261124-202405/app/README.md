ATM Network Status Monitor (Azure DocumentDB sample)

This sample demonstrates a Node.js + Mongoose application that:
- Accepts ATM heartbeat documents (POST /heartbeat)
- Maintains per-ATM latest status (atm_statuses collection)
- Uses a change stream on heartbeats to keep a single network summary document (_id: 'network_summary')
- Emits alert documents when availability drops below a configured threshold

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB (MongoDB-compatible) cluster; set its connection string in DOCUMENTDB_URI
- The sample uses the database `sample_banking_16` by default

Quick start
1. Copy .env.example to .env and set DOCUMENTDB_URI
2. npm install
3. npm run seed   # seed sample ATMs + initial heartbeats and compute summary
4. npm start      # starts the Express API (POST /heartbeat, GET /summary)

Seed and verification
- The seed script is idempotent and will upsert atm_statuses and insert heartbeats.
- After running seed you can inspect collections using the DocumentDB MCP server or mongosh (not included here).

Design notes
- Connection string is read from DOCUMENTDB_URI at runtime (do not commit secrets).
- Singleton MongoClient pattern via Mongoose connection is used (see documentdb-driver guidance).
- Indexes created: heartbeats { atmId:1, timestamp:-1 }, heartbeats { status:1 }

Limitations
- This is a demo sample, not a production-grade service. It keeps per-ATM state in an atm_statuses collection for simplicity.

Cleaning up
- Delete the created documents/collections from the sample_banking_16 database if desired. No Azure resources were provisioned by this sample.
