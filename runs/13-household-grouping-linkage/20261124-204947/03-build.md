# 3. Build report: 13-household-grouping-linkage

**Status: completed**

Built a small Node.js + Express + Mongoose sample that: seeds synthetic customer documents into the sample_customer_360_13 database, computes household groupings by shared address/phone/surname, persists household documents referencing customer _id values, and exposes REST endpoints to return household-level CLV and aggregated product holdings. Seed, linking and verification were executed against the live DocumentDB cluster pointed to by DOCUMENTDB_URI in the environment. I used the documentdb MCP tools to inspect databases, sample documents, list indexes and run an explain plan for a representative query.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI (do NOT commit secrets). Optionally set DATABASE_NAME (defaults to sample_customer_360_13).
2) Install deps: npm install
3) Seed sample data: npm run seed
4) Create household group documents: npm run link
5) Verify counts and a sample household: npm run test
6) Start the API server: npm start (server listens on PORT env or 3000). Endpoints:
   - GET /households/:id/clv
   - GET /households/:id/products

## Verified by running

- Loaded documentdb-driver, documentdb-connection, documentdb-data-modeling, documentdb-indexing and documentdb-local-deployment skills before implementing connection, data-model and index choices (load_skill calls executed).
- npm install: 0 exit code (dependencies installed successfully after switching to @faker-js/faker).
- npm run seed: inserted 20 customer documents (script printed 'Inserted 20 customers.').
- npm run link: created household documents (script printed 'Created 21 new households.').
- npm run test: ran verification script which printed counts and a sample household. Output included customers: 40 and households: 41 (counts reflect live DB contents including earlier runs).
- documentdb_list_databases (documentdb MCP): sample_customer_360_13 found.
- documentdb_find_documents (documentdb MCP) on customers: sampled documents returned (showed both structured and flat address shapes).
- documentdb_find_documents (documentdb MCP) on households: sampled household documents returned (including a multi-member household produced by grouping).
- documentdb_list_indexes (documentdb MCP) for customers: confirmed indexes present including compound index normalizedAddress_1_phone_1_surname_1, clv_1, products.productId_1 and _id index.
- documentdb_explain_operation (documentdb MCP) for a find on normalizedAddress: explain returned execution stats (winningPlan was COLLSCAN for the sample query; indexCosts show an index that could be used but execution scanned documents).

## Not verified

- Entra ID (MONGODB-OIDC) authentication flow was not configured or tested; I chose SCRAM-style connection via the DOCUMENTDB_URI environment variable for this sample. (Decision logged: 'I chose SCRAM-SHA-256 via the DOCUMENTDB_URI env var').
- Provisioning a DocumentDB cluster was not performed (az/ARM/Bicep/Terraform not used). Run policy disallowed creating resources; I left IaC out and documented the sample to read connection from env. (Decision logged: 'No provisioning — use existing cluster').
- Vector-index / full-text-search features were not used in this sample (not required by the task); no vector indexes were created or tested.
- No end-to-end automated tests hitting the live HTTP endpoints were run (verification used the seed/link/verify scripts and the MCP server).
- I did not create an index for nested address fields (address.normalizedAddress) — explain showed a COLLSCAN for a query on normalizedAddress because many existing documents in the database use a nested address.normalizedAddress field shape; schema unification or additional index would be required to ensure index usage across mixed shapes.

## Open issues

- Mixed customer document shapes in the live database: some documents use a top-level normalizedAddress (seed script) while others use address.normalizedAddress (existing data). This caused the explain output to show a COLLSCAN for a normalizedAddress find even though a compound index exists on the top-level normalizedAddress field. Recommendation: pick one schema for normalizedAddress (top-level or nested) and create indexes covering the shape used in queries (e.g., create index on 'address.normalizedAddress' if nested).
- Schema/versioning: the repo follows a simple schema for demonstration. For production, add schemaVersion and migration scripts (documentdb-data-modeling skill guidance).
- Idempotency across multiple seed runs: the seed script tags documents with meta.seedTag but existing non-seed documents were present in the db; the sample is idempotent for seed-tagged documents but does not isolate or remove other existing data in the same database.
- Authentication options: README documents using environment-based connection string; an alternate path using Entra ID (MONGODB-OIDC) should be documented and tested for teams that need RBAC-based auth.

## Files

- `package.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `src/db.js`
- `src/index.js`
- `src/models/customer.js`
- `src/models/household.js`
- `src/routes/households.js`
- `src/seed/seed.js`
- `src/link/link_households.js`
- `src/verify/run_verification.js`

