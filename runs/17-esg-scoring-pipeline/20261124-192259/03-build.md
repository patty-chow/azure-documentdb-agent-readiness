# 3. Build report: 17-esg-scoring-pipeline

**Status: completed**

A small Python sample app was built that seeds synthetic ESG company documents into an Azure DocumentDB (MongoDB-compatible) database, runs a processing step that (via prompt-engineering / LangChain when API keys exist, or via a deterministic fallback) scores E/S/G (1-10) with rationales, stores normalized embeddings for the rationales in each document, and runs an aggregation pipeline to rank companies by composite score. The repo includes a README, .env.example, a small Python package (sample/) with seed/process/aggregate modules, unit tests, and an idempotent seed script. I verified dependency installation, seeding, processing, aggregation, and unit tests. Creation of a server-side vector index via the documentdb create-index MCP tool failed twice and is recorded in not_verified.

## How to run

1) Create and activate a Python virtualenv. 2) pip install -r requirements.txt. 3) Copy .env.example to .env and fill DOCUMENTDB_URI (SRV-style connection string for your Azure DocumentDB cluster). Optionally set OPENAI_API_KEY (and leave OPENAI_EMBEDDING_MODEL/OPENAI_LLM_MODEL defaults) to use real LLM/embedding calls; otherwise the sample uses deterministic offline fallbacks. 4) Seed the sample data: python -m sample.seed 5) Process documents (score & embed): python -m sample.process 6) Aggregate and print top companies: python -m sample.aggregate 7) Run tests: python -m pytest -q

## Verified by running

- pip install -r requirements.txt: succeeded
- python -m sample.seed: ran and upserted 8 sample documents and created standard indexes (name unique, schemaVersion)
- python -m sample.process: ran and wrote E/S/G scores, rationale strings, and rationale_embedding arrays back to the 8 documents (bulk update succeeded)
- documentdb_list_indexes (MCP): returned 3 indexes (_id, idx_name_unique, idx_schemaVersion)
- documentdb_find_documents (MCP): returned sample documents including stored score_E/score_S/score_G, rationale strings and rationale_embedding arrays (sample returned 8 docs)
- pytest: 4 passed (tests/test_utils.py 2 tests, tests/test_seed_process.py 2 tests)

## Not verified

- documentdb_create_index (vector index creation) via MCP server: attempted twice and failed with 'Function failed.'; vector index was not created programmatically by the build. Reason: the documentdb_create_index tool returned an error on both attempts. Create the vector index manually or retry with appropriate permissions/parameters. Index JSON I attempted: keys: {"rationale_embedding":"cosmosSearch"}, options.name: "idx_rationale_embedding_hnsw", cosmosSearchOptions: {kind: "vector-hnsw", dimensions: 1536, similarity: "COS", maxDegree: 32, lBuild: 50}
- Server-side $search vector queries using a created vector index: not verified because the vector index creation failed above

## Open issues

- Vector index creation via the documentdb_create_index MCP tool failed twice (tool returned 'Function failed.'). The sample stores embeddings (rationale_embedding) and includes a recommended vector-index JSON and instructions, but the index was not installed in the cluster by the automation step. To run server-side vector $search queries, create a cosmosSearch vector-hnsw (or diskann) index on 'rationale_embedding' with dimensions matching your embedding model (1536) and similarity 'COS'.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `sample/__init__.py`
- `sample/config.py`
- `sample/db.py`
- `sample/utils.py`
- `sample/seed.py`
- `sample/process.py`
- `sample/aggregate.py`
- `tests/test_utils.py`
- `tests/test_seed_process.py`

