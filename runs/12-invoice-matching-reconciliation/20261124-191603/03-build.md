# 3. Build report: 12-invoice-matching-reconciliation

**Status: completed**

Created a small Node.js (Node 24) sample app that demonstrates invoice → PO reconciliation against an Azure DocumentDB (MongoDB-compatible) cluster using Mongoose. The repo includes models (Invoice, PurchaseOrder), an idempotent seed script, a one-shot reconciliation CLI, and a minimal Express API to run reconciliation and submit manual corrections. The app reads the DocumentDB connection string from DOCUMENTDB_URI; LLM and embeddings use OPENAI_API_KEY if provided, with a deterministic fallback when not available. I seeded the sample data and ran a reconciliation run (one-shot). I used the DocumentDB MCP server to verify the database, collections and indexes that the sample created or used.

## How to run

1. Install dependencies: npm install
2. Copy .env.example to .env and set DOCUMENTDB_URI to your cluster connection string (and OPENAI_API_KEY if you want LLM/embeddings enabled).
3. Seed the sample data: npm run seed
4a. Run a one-shot reconciliation (CLI): npm run reconcile
4b. Or start the Express API server: npm start
   - POST /reconcile/run to trigger reconciliation
   - POST /reconcile/manual-correction with JSON { invoiceId, matchedPoId } to apply a manual correction (stored in in-process session memory)
   - GET /reconcile/status to inspect last run and session corrections
Notes: The app reads DOCUMENTDB_URI and (optionally) OPENAI_API_KEY from environment. Never commit secrets; use .env or environment variables.

## Verified by running

- npm install: exit code 0 (dependencies installed)
- npm run seed: exit code 0 (seed inserted sample PurchaseOrder and Invoice documents into sample_fintech_12)
- npm run reconcile: exit code 0 (one-shot reconciliation executed; results logged; no matches found with the default fallback extraction in this run)
- documentdb_list_databases (MCP): found database 'sample_fintech_12' with collections 'purchaseorders' and 'invoices' and counts
- documentdb_list_indexes (MCP) for 'invoices': listed _id, invoiceNumber, vendorName indexes (count=3)
- documentdb_list_indexes (MCP) for 'purchaseorders': listed _id, poNumber, vendorName indexes (count=3)
- documentdb_find_documents (MCP) for 'invoices': returned 4 seeded invoice docs (status 'unmatched' at time of check)

## Not verified

- LLM-based structured extraction and embeddings: not executed against a real LLM because OPENAI_API_KEY was not present in the environment during verification; code falls back to deterministic extraction. To verify LLM extraction and embedding-based scoring, set OPENAI_API_KEY and run npm run reconcile; monitor logs and DB updates.
- Vector-index creation on the cluster: this sample code does not create specialized vector indexes in DocumentDB. If you want to use production vector indexes (HNSW/IVF/DiskANN) and tune parameters, create them manually or extend the seed script and use the documentdb-azure-deployment or MCP tools to create the recommended index shape. (Run policy disallowed provisioning Azure resources.)

## Open issues

None.

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/models/purchaseOrder.js`
- `src/models/invoice.js`
- `src/seed.js`
- `src/llm.js`
- `src/reconciler.js`
- `src/reconcile-cli.js`
- `src/server.js`

