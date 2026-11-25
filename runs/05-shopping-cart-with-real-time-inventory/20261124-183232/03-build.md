# 3. Build report: 05-shopping-cart-with-real-time-inventory

**Status: completed**

Built a small Node.js + Mongoose sample cart service that demonstrates multi-document transactions against an Azure DocumentDB (MongoDB-compatible) cluster. The service atomically decrements inventory and updates a user's cart inside a transaction, uses optimistic concurrency (Mongoose versionKey) and a retry/backoff loop for transient/optimistic conflicts, and surfaces a clear OutOfStock error when attempts exceed stock. Seed and demo scripts run against the live cluster (DOCUMENTDB_URI). Indexes were created for SKU and userId and verified via the documentdb MCP server.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string.
2) Install dependencies: npm install
3) Seed the sample data: npm run seed
4) Run the demo script (shows OutOfStock and a successful add): npm run demo
5) Start the HTTP server (optional): npm start

API: POST /cart/:userId/add with JSON body { "productId": "<objectId>", "quantity": <number> }.
Responses: 200 OK (cart), 400 bad request, 409 OutOfStock, 500 server error.

## Verified by running

- npm install: exit code 0 (dependencies installed)
- npm run seed: exit code 0, output 'Seed complete' (inventories and carts created/upserted)
- npm run demo: exit code 0, showed 'Attempt add over stock result: { success: false, error: \"OutOfStock\" }' and then successful add and stock decrement
- documentdb_list_databases (documentdb MCP): database sample_retail_05 present with collections inventories (3 docs) and carts (1 doc)
- documentdb_find_documents on sample_retail_05.inventories: returned 3 inventory documents (sample SKUs and stocks)
- documentdb_find_documents on sample_retail_05.carts: returned 1 cart for user 'alice' with the added item
- documentdb_list_indexes on inventories and carts: sku_1 (unique) and userId_1 indexes verified

## Not verified

None.

## Open issues

None.

## Files

- `package.json`
- `README.md`
- `.env.example`
- `src/db.js`
- `src/index.js`
- `src/service.js`
- `src/seed.js`
- `src/demo.js`
- `src/models/inventory.js`
- `src/models/cart.js`
- `src/models/index.js`

