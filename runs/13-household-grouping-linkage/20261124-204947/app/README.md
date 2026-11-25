DocumentDB Household Linkage Sample

This sample demonstrates how to identify household members by matching on shared address, phone, and surname fields across customer documents in Azure DocumentDB (MongoDB compatible) and to expose household-level aggregations (CLV and products).

Prerequisites
- Node.js 20+ (Node 24 recommended)
- A reachable Azure DocumentDB cluster; set its connection string in DOCUMENTDB_URI environment variable

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI
2. Install deps: npm install
3. Seed sample customers: npm run seed
4. Link household groups: npm run link
5. Run verification: npm run test
6. Start API: npm start

API Endpoints
- GET /households/:id/clv -> { householdId, clvTotal }
- GET /households/:id/products -> { householdId, products: [{ productId, name, totalQty, count }] }

Design notes
- Data model: customers and households collections. Household documents reference customer _id values.
- Indexes: compound index on { normalizedAddress, phone, surname }, index on clv and products.productId.
- The app reads DOCUMENTDB_URI and DATABASE_NAME from environment. Do not commit secrets.

Verification
The repository includes a verification script (npm run test) that prints counts and a sample household.

Cleanup
You can remove seeded documents by running a small script or manually removing documents from the sample_customer_360_13 database.
