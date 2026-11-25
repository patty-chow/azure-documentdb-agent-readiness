# 3. Build report: 15-financial-advisor-chatbot-rag

**Status: partial**

Built a small Node.js sample RAG agent and seed/demo scripts that store financial knowledge articles (with deterministic local embeddings) into the Azure DocumentDB database sample_fintech_15. The sample uses a singleton MongoClient, an in-process retrieval + simple memory-based conversational agent, and a mocked portfolio tool. I installed dependencies successfully. I could inspect the live cluster via the provided DocumentDB MCP server (confirmed sample_fintech_15 exists and contains seeded documents), but running the demo app (which opens a direct MongoDB driver connection to DOCUMENTDB_URI) timed out in this execution environment. Attempts to create a DocumentDB diskann vector index via the MCP create-index tool failed (the tool returned an error), so no vector index was created by this build run. The repo includes seed, demo, and agent code plus a README and .env.example. See verification & not-verified sections for details.

## How to run

1) Install dependencies: npm install
2) Create a .env file or export environment variables referenced in .env.example. Required: DOCUMENTDB_URI set to your cluster connection string. Optional: OPENAI_API_KEY and USE_OPENAI_EMBEDDINGS=true to use OpenAI for embeddings (sample uses deterministic local embeddings if not provided).
3) Seed the knowledge collection (idempotent): npm run seed
4) Run the demo conversation (one-shot): npm run demo
Notes: The sample by default uses deterministic local embeddings so it runs without external ML provider keys. For production, create a DocumentDB vector index on the 'embedding' field with dimensions matching your embedding model (the sample assumes 1536 dims) and similarity COS. Example index spec (DocumentDB shell): db.knowledge.createIndex({embedding: 'cosmosSearch'}, { name: 'knowledge_embedding_diskann', cosmosSearchOptions: { kind: 'vector-diskann', dimensions: 1536, similarity: 'COS', maxDegree: 32, lBuild: 50 } })

## Verified by running

- npm install: succeeded (100 packages added).
- Environment check: DOCUMENTDB_URI was present in environment (printed).
- DocumentDB MCP: documentdb_list_databases returned databases including 'sample_fintech_15' (exists).
- DocumentDB MCP: documentdb_sample_documents on sample_fintech_15.knowledge returned sample documents (several documents with embeddings and metadata present).
- DocumentDB MCP: documentdb_list_indexes on sample_fintech_15.knowledge returned only the default _id index (no vector index present).

## Not verified

- Running the Node.js demo (npm run demo / node src/run_demo.js) to connect via the MongoDB driver to DOCUMENTDB_URI timed out in this execution environment (Tool runner TIMEOUT after 600s). The demo attempts a real driver connection; it did not complete here.
- Creating a DocumentDB vector index: attempted to call the MCP server documentdb_create_index to create a vector-diskann index on sample_fintech_15.knowledge but the tool returned 'Function failed.' and the index was not created. Without the vector index, the sample falls back to in-process nearest-neighbor ranking over seeded documents.
- Any behavior that depends on actual OpenAI embeddings (OPENAI_API_KEY) was not run or validated. The sample can be configured to call OpenAI but defaults to deterministic local embeddings for reproducible demo runs without secrets.

## Open issues

- The Node.js app (driver-based connection to DOCUMENTDB_URI) could not complete in this run due to a runtime timeout when attempting network connection from the runner; this may be an environment/network restriction. Locally, with DOCUMENTDB_URI reachable, the demo should run as written.
- Vector index creation via the MCP server failed here; if you want a DB-native vector search, create a cosmosSearch / vector-diskann index on the 'embedding' field with dimensions=1536 and similarity='COS' using the cluster's shell or the appropriate management tool. The seed script already stores embeddings and metadata.
- If you want end-to-end production-like semantic embeddings, set OPENAI_API_KEY and USE_OPENAI_EMBEDDINGS=true and re-run the seed step (or add your own embedding step).

## Files

- `package.json`
- `.env.example`
- `README.md`
- `src/db.js`
- `src/seed.js`
- `src/agent.js`
- `src/run_demo.js`

