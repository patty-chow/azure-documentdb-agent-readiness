DocumentDB Customer 360 Sample

This sample demonstrates a Node.js + Mongoose service that ingests customer events from multiple source systems (CRM, e-commerce, support) and upserts them into a canonical customer profile document in Azure DocumentDB (MongoDB-compatible).

What this sample shows
- How to connect to a DocumentDB cluster using the environment-provided connection string (DOCUMENTDB_URI).
- How to structure a canonical customer profile that contains nested sub-documents per source system (sources.crm, sources.ecommerce, sources.support).
- How to perform idempotent upserts using updateOne with $set on the nested source path and upsert:true, avoiding overwriting unrelated fields.
- How to create a unique index on customerId to support identity resolution.

Prerequisites
- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster. The connection string must be provided in the environment variable DOCUMENTDB_URI.
- This sample uses the database named: sample_customer_360_01 (the sample will use this DB for all created collections).

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string.
2. Install dependencies:
   npm install
3. Seed sample events into the database (this will create the customers collection and the unique index on customerId):
   npm run seed
   The seed script reads sample-data/events.json and upserts them.
4. Start the HTTP API server:
   npm start
   The server listens on PORT (default 3000).
5. Send an event to the service:
   curl -X POST http://localhost:3000/events -H "Content-Type: application/json" -d '{"source":"crm","customerId":"cust-123","attributes":{"email":"x@example.com"}}'

Files of interest
- src/index.js - Express server and integration wiring
- src/db.js - Mongoose connection and DB selection (uses sample_customer_360_01)
- src/models/customer.js - Customer schema and model factory
- src/lib/upsert.js - Upsert logic used by both the HTTP route and seed script
- scripts/seed.js - Loads sample-data/events.json and upserts into DB
- scripts/verify.js - Simple verification script to list customers

Security notes
- The connection URI is read only from process.env.DOCUMENTDB_URI at runtime. Do not put secrets into source files.

Limitations and notes
- This sample does not provision Azure resources. It uses the provided cluster. The run environment for this sample may already provide DOCUMENTDB_URI.
- The sample purposely keeps the data model small and focused on demonstrating the upsert merge pattern.

License: MIT
