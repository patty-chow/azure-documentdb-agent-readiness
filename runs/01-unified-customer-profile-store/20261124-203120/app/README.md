DocumentDB Customer 360 Sample

This sample demonstrates a Node.js (Express) service that receives customer events from multiple source systems (crm, ecommerce, support) and upserts them into a canonical customer profile document stored in Azure DocumentDB (MongoDB wire protocol).

Prerequisites
- Node.js 24+
- A reachable Azure DocumentDB cluster. Place its connection string in DOCUMENTDB_URI (see .env.example). The run environment for this sample expects DOCUMENTDB_URI to be set.

What this sample shows
- A Mongoose model `CustomerProfile` with nested sub-documents for `crm`, `ecommerce`, and `support`.
- An HTTP POST /events endpoint for ingesting events:
  { source: 'crm'|'ecommerce'|'support', customerId: '...', attributes: {...} }
- Idempotent upserts that merge attributes into the appropriate sub-document using $set with dotted paths to avoid overwriting unrelated fields.
- A seed script to generate sample events and populate the `sample_customer_360_01` database, collection `customer_profiles`.

Setup
1. Copy .env.example to .env and set DOCUMENTDB_URI.
2. npm install
3. npm run seed   # idempotent: inserts/updates demo events into the live cluster's sample_customer_360_01 DB
4. npm start      # starts Express app on port 3000

API
POST /events
Body: { source, customerId, attributes }
Returns: { ok: true, matched, modified, upsertedId }

Testing
- Unit tests mock Mongoose and run offline: npm test

Cleanup
- Remove sample data manually using mongosh or via Azure Portal. This sample does not delete the database automatically.

Security
- Do NOT commit real credentials. Use environment variables or Key Vault in production.

Notes
- The sample creates a unique index on customerId. Index creation is performed during the seed step via Model.syncIndexes().
