Azure DocumentDB Customer Journey Sample (Node.js)

This sample demonstrates how to reconstruct a customer's journey by aggregating touchpoint events stored in Azure DocumentDB (MongoDB wire protocol) and using an LLM (OpenAI-compatible) to generate a plain-language summary highlighting inflection points.

What it shows
- How to connect to an existing Azure DocumentDB cluster using the official mongodb driver (singleton MongoClient).
- Create an idempotent seed script to populate a `touchpoints` collection with synthetic events.
- Create a compound index to support match+sort queries ({customerId:1, timestamp:1}).
- A small HTTP API (GET /journey?customerId=...) and CLI to fetch a chronological timeline and generate a LLM summary.

Prerequisites
- Node.js 24+ and npm
- An accessible Azure DocumentDB cluster. Place its connection string in DOCUMENTDB_URI (see .env.example). The run environment for this sample includes a reachable cluster; set DOCUMENTDB_URI accordingly.
- An OpenAI-compatible API key in OPENAI_API_KEY and optional MODEL_NAME.

Setup
1. cp .env.example .env and fill values
2. npm install
3. npm run seed   # idempotent; creates indexes and populates sample data
4. npm start     # starts HTTP server on port 3000

CLI demo
- npm run journey -- --customer cust_0001

API demo
- curl "http://localhost:3000/journey?customerId=cust_0001"

Design notes and choices
- Driver: mongodb ^5.x, configured as a process-wide singleton per documentdb-driver guidance.
- Connection pool: conservative OLTP settings (maxPoolSize=20, maxIdleTimeMS=300000). See src/db.js for details and comments.
- Collection: `touchpoints` with documents { _id, customerId, timestamp (ISODate), channel, eventType, metadata }.
- Index: compound { customerId: 1, timestamp: 1 } to support match+sort queries.
- LLM: The sample uses OpenAI Chat completions via the `openai` npm package. The sample constructs a context-rich prompt ("LlamaIndex-style") from the structured timeline and asks the LLM to return JSON with a summary and inflection points.

Security and cost
- Do not commit .env or any secrets to version control.
- This sample connects to your existing cluster and will insert data; it does not provision Azure resources.

Files
- src/: application source
- scripts/seed.js: idempotent seeding and index creation
- .env.example: placeholder environment variables
- tests/: unit tests (prompt builder)

Troubleshooting
- If the seed step fails, ensure DOCUMENTDB_URI is valid and reachable and that your IP / VNet is allowed by the cluster network settings.

License: MIT
