# 3. Build report: 14-hyper-personalized-content-engine

**Status: partial**

Created a small Node.js sample app that seeds a sample_customer_360_14 database, inserts sample profiles/segments/interactions/content_pieces (with deterministic mock embeddings), exposes an Express /search HTTP endpoint that returns a personalised rationale + ranked content by application-side cosine similarity, and demonstrates (attempts) vector-index creation for DocumentDB. Seeding, data insertion and an in-process sample run succeeded. Creating a cosmosSearch vector index via the driver failed and attempts to create it via the documentdb MCP tool also failed in this run, so server-side vector kNN retrieval ($search) was not exercised — the app uses local similarity for retrieval instead. The sample is configurable (DOCUMENTDB_URI, EMBEDDING_PROVIDER, EMBEDDING_DIM, CHAT_PROVIDER) and includes instructions in README.md.

## How to run

1) Copy .env.example to .env and set DOCUMENTDB_URI with your cluster connection string. Ensure DATABASE_NAME is sample_customer_360_14 or adjust. 2) npm install 3) npm run seed 4) npm start 5) Call the API: GET /search?customerId=cust_1 (default port 3000) Or run an in-process example: npm run run-sample (runs src/run_sample.js).

## Verified by running

- npm install: exit code 0 (dependencies resolved using package.json).
- npm run seed: exit code 0. Output included: 'Seed complete'. The seed script created collections (profiles, segments, interactions, content_pieces) and upserted sample documents (counts printed). It attempted to create a cosmosSearch vector index using the driver but the driver reported that cosmosSearch options were not accepted for index creation.
- node src/run_sample.js: exit code 0. Ran the sample agent in-process; produced a textual rationale and a ranked list of content items (scores shown). This proves retrieval+ranking+rationale path works with the seeded data and mock embeddings.
- documentdb_list_databases (MCP tool) for 'sample_customer_360_14': returned database and collections with counts (segments: 2, profiles: 1, interactions: 1, content_pieces: 14). This verifies documents were inserted into the live cluster.
- documentdb_list_indexes (MCP tool) on content_pieces: returned only the default _id index (no cosmosSearch index present).

## Not verified

- Creation of a cosmosSearch vector index on content_pieces.embedding: attempted via the mongodb driver (createIndex with cosmosSearchOptions) and the documentdb MCP documentdb_create_index tool, both attempts did not result in a visible cosmosSearch index in the collection. Reason: driver reported 'Index type CosmosSearch requested, but the cosmosSearch options were not provided' when called from the seed script; subsequent documentdb_create_index tool call returned a generic failure. This prevented verification of server-side kNN queries using $search.
- A real LlamaIndex Node library integration: the sample implements a lightweight, modular retrieval+generation agent (mock embeddings & rationale). No third-party LlamaIndex Node package was installed or tested because there was no definitive package/version pinned in the prompt or installed skills. The repo is structured so a LlamaIndex-based agent can be swapped in later.

## Open issues

- cosmosSearch index creation: the driver-based createIndex attempt logged a cluster-side error and the documentdb_create_index MCP call returned a failure. Investigate cluster permissions / driver vs server API compatibility or use the portal/management plane to create the vector index. Until the vector index exists, server-side $search kNN queries can't be verified in this sample run.
- Server-side vector retrieval ($search knn) not implemented / tested: the app currently uses application-side cosine similarity over stored embeddings. For realistic scale and performance, replace the local ranking with a server-side $search/knn stage once the cosmosSearch index can be created & verified.
- LlamaIndex integration: if the user specifically needs a LlamaIndex Node agent, add and pin the desired LlamaIndex package and implement the agent using that library; currently the sample uses a simple modular agent to keep the sample easy to run without external API keys.
- The seed script created 14 content_pieces in the target collection — there were pre-existing documents in that collection in the live cluster. If you expect a pristine dataset, remove or inspect pre-existing docs before seeding (seed is idempotent but does not delete extra documents).

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/seed.js`
- `src/agent.js`
- `src/server.js`
- `src/run_sample.js`

