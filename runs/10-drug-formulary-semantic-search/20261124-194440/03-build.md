# 3. Build report: 10-drug-formulary-semantic-search

**Status: partial**

Created a small Python FastAPI sample that demonstrates storing formulary entries with embeddings and a vector-search endpoint. Project files, a seed script that computes embeddings and upserts documents, a quick query demo, and a README were added. Dependency installation succeeded. I could not run the end-to-end data-plane verification because an embedding provider API key (OPENAI_API_KEY) was not present in the environment, so seeding, index creation, and live queries against the DocumentDB cluster were not executed. I did verify the target database exists (sample_healthcare_10) and recorded that pytest is not installed in this environment so integration tests were skipped.

## How to run

1) Create and activate a virtual environment. 2) Install dependencies: pip install -r requirements.txt
3) Export required environment variables:
   - DOCUMENTDB_URI (MongoDB connection string for the Azure DocumentDB cluster)
   - OPENAI_API_KEY (or other embedding provider key if you adapt code)
   Optionally: DATABASE_NAME, COLLECTION_NAME, EMBED_MODEL, EMBED_DIMENSIONS
4) Seed the database (idempotent upsert of sample entries with embeddings):
   python scripts/seed_data.py
5) (Optional) Create the vector index. The sample expects a vector index on the document field 'embedding' with dimensions matching your model (default 1536). See README for guidance and the DocumentDB docs. You can create the index via the DocumentDB MCP server, az CLI, or the Azure portal. Example createIndex (mongo shell style):
   db.formulary.createIndex({ embedding: 'cosmosSearch' }, { name: 'formulary_embedding_hnsw', cosmosSearchOptions: { kind: 'vector-hnsw', dimensions: 1536, similarity: 'COS', maxDegree: 32, lBuild: 50 } })
6) Try a one-shot demo (does the same as the /formulary-search path but runs directly):
   python scripts/query_demo.py --query "patient with hypertension needing ACE inhibitor guidance"
7) Run the web service locally:
   uvicorn main:app --reload
   Then POST JSON {"query":"..."} to http://127.0.0.1:8000/formulary-search

Notes:
- Do not commit secrets; use environment variables or a secure secret store.
- For production use, follow DocumentDB security best practices (private endpoints, RBAC, CMK) — out of scope for this sample.

## Verified by running

- pip install -r requirements.txt: completed (packages installed successfully)
- documentdb_list_databases sample_healthcare_10: returned database with no collections

## Not verified

- scripts/seed_data.py: not run because OPENAI_API_KEY was not set in the environment (embedding provider missing). The seed script exits early and requires the embedding key to compute and insert vectors.
- Vector index creation: not created/verified because the seed script was not executed and the collection was therefore empty. The sample includes guidance and an example createIndex call; create the index with matching dimensions after seeding.
- scripts/query_demo.py: not executed (depends on seed_data having run and OPENAI_API_KEY present).
- main.py /formulary-search endpoint: not exercised end-to-end (requires seeded data + OPENAI_API_KEY).
- pytest integration test: not run; pytest not installed in the environment (the run attempt reported pytest was not found on PATH).

## Open issues

- OPENAI_API_KEY (or alternative embedding provider key) was not present — prevents seeding embeddings and end-to-end verification.
- Index creation against the collection was not performed because the collection had no documents (seed not executed). The index must be created with the 'dimensions' exactly matching the embedding model; use the example in README or run the DocumentDB MCP server create-index command.
- I attempted to log a decision choosing vector-hnsw via the audit tool, but a tool parsing error occurred on one attempt; core decisions are recorded earlier in the audit trail (language/framework, embedding model selection).

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `db.py`
- `main.py`
- `scripts/seed_data.py`
- `scripts/query_demo.py`
- `tests/test_seed.py`

