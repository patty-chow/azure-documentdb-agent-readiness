Multi-tenant storefront sample using Azure DocumentDB (MongoDB wire protocol) and Mongoose.

What it shows:
- Single shared collections for products, inventory, and orders
- tenantId on every document
- Compound indexes: (tenantId, sku) and (tenantId, createdAt)
- Repository layer that enforces tenant isolation so queries cannot cross tenant boundaries

Prerequisites:
- Node.js 18+ installed
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in your environment (see .env.example). The sample will use database `sample_retail_10`.

Quickstart:
1. npm install
2. Copy .env.example -> .env and set DOCUMENTDB_URI
3. npm run seed    # creates indexes and loads sample data
4. npm run verify-indexes  # lists indexes found on the collections
5. npm test        # runs an integration test that verifies tenant isolation against the live cluster

Files:
- src/mongoose.js        - connection helper (reads DOCUMENTDB_URI)
- src/models/*           - Mongoose schemas and index definitions
- src/repos/*            - Repository classes that require a tenantId
- src/seed.js            - Idempotent seed script (upserts sample data)
- src/verify_indexes.js  - Helper to list indexes using Mongoose (and MCP server is also used by CI)
- tests/isolation.test.js - Integration test demonstrating tenant isolation

Cleanup:
- The sample creates documents in the database `sample_retail_10`. Delete them manually or drop the database via your admin tools when finished.

Security:
- Do not commit your DOCUMENTDB_URI. Keep it in environment variables or secure config systems.
