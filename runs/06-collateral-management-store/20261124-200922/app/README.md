Azure DocumentDB Collateral Management Sample

This sample shows how to store versioned collateral assets and valuations in Azure DocumentDB (MongoDB-compatible), enrich assets with an LLM classification, and compute a total collateral coverage ratio via aggregation.

What's included
- Node.js (Express) service using Mongoose to talk to Azure DocumentDB
- POST /assets to create a new versioned valuation (triggers LLM classification)
- GET /assets/:assetId/history to view version history
- GET /coverage?totalLiabilities=NUMBER to compute coverageRatio = sum(latest valuations (optionally only eligible assets)) / totalLiabilities
- scripts/seed.js to load idempotent sample data and create indexes

Prerequisites
- Node.js 24+ and npm
- An Azure DocumentDB cluster reachable from this machine; the connection string must be set in DOCUMENTDB_URI environment variable (SRV-style mongodb+srv URI). Do NOT commit secrets.

Quickstart
1. Copy .env.example to .env and fill DOCUMENTDB_URI. Optionally set OPENAI_API_KEY or set DISABLE_LLM=true for offline runs.
2. npm install
3. npm run seed
4. npm start

API examples
- Create/update asset (new version):
  POST /assets
  Body: { "assetId": "A-123", "valuation": { "amount": 100000, "currency": "USD" }, "metadata": { "category": "residential_mortgage" } }

- History:
  GET /assets/A-123/history

- Coverage:
  GET /coverage?totalLiabilities=200000

Design notes and decisions
- Each valuation update is a separate document with fields: assetId, version, createdAt, valuation, metadata, llmTags.
- LLM classification uses OpenAI by default; model and API key are configurable. Set DISABLE_LLM=true to skip.
- Coverage formula: sum(latest valuations) / totalLiabilities. The endpoint by default excludes assets tagged as 'ineligible'.
- Indexes: compound index { assetId: 1, version: -1 } and createdAt index to support efficient latest-version aggregation.

Testing
- Unit tests (jest) use mongodb-memory-server to run an in-memory MongoDB for fast offline tests. Run npm test.

Cleanup
- Remove sample documents from the 'sample_banking_06' database or drop the "collateral_assets" collection as desired.

Security
- Never commit credentials. Use environment variables or a secrets manager.

Notes
- This sample targets a managed Azure DocumentDB cluster already provisioned. It does not create cloud resources.
