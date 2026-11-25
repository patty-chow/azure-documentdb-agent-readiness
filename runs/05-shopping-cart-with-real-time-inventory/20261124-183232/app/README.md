DocumentDB Shopping Cart Sample

This sample demonstrates an Express + Mongoose cart service that uses Azure DocumentDB (MongoDB-compatible) to store inventory and cart documents and performs multi-document transactions to atomically decrement stock and add items to the cart. It demonstrates optimistic concurrency handling (versioning) and a clear OutOfStock error.

Prerequisites

- Node.js 24+ and npm
- A reachable Azure DocumentDB cluster (DocumentDB vCore MongoDB-compatible). The connection string must be available in DOCUMENTDB_URI env var.
- Database used: sample_retail_05 (the app connects to this DB)

Quick start

1. Copy .env.example to .env and set DOCUMENTDB_URI.
2. Install deps: npm install
3. Seed sample data: npm run seed
4. Run demo script: npm run demo
5. Start the HTTP server: npm start

API

POST /cart/:userId/add
Body: { "productId": "<objectId>", "quantity": <number> }
Responses:
- 200: { cart }
- 400: bad request
- 409: OutOfStock
- 500: server error

What this sample shows

- Mongoose models for Inventory and Cart with optimisticConcurrency enabled
- A transaction that decrements Inventory.stock (conditionally) and updates the Cart in the same transaction
- A retry/backoff loop for transient/optimistic errors; clear domain error when stock is exhausted

Security

Do not check secrets into source control. Provide the connection string via DOCUMENTDB_URI or use Microsoft Entra/OIDC patterns (documented by Azure) in production.

Cleanup

Delete the sample documents from the sample_retail_05 database using the Azure portal, mongosh, or the documentdb MCP server.
