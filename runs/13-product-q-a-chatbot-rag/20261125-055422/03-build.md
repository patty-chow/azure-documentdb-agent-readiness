# 3. Build report: 13-product-q-a-chatbot-rag

**Status: partial**

I created a small Python RAG sample that uses Azure DocumentDB as a vector store backing a LlamaIndex-style workflow. The sample includes seeding, chunking, a CLI REPL, and a small test. I installed dependencies, ran tests (1 passed), seeded the provided sample data into the live DocumentDB cluster (inserted 5 products and 5 chunks), and ran a sample retrieval that falls back to simple text-matching when embeddings/indexes are not present. Vector-index creation and the full embedding+vector-search+LLM RAG path were not fully verified (no embeddings created during verification and an attempt to create a DocumentDB vector index via the MCP helper failed). See not_verified and open_issues for details and remediation steps.

## How to run

1) Create and activate a virtualenv: python -m venv .venv && source .venv/bin/activate (Windows: .venv\Scripts\activate)
2) Install deps: pip install -r requirements.txt
3) Copy .env.example to .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY, LLM_MODEL): cp .env.example .env && edit .env
   - DOCUMENTDB_URI must point to your Azure DocumentDB cluster (mongodb+srv://... with tls=true)
   - EMBEDDING_MODEL default is openai/text-embedding-3-small and EMBEDDING_DIMS=1536
4) Seed the sample data (recommended to start with skip embeddings): python seed.py --skip-embeddings
   - If you have OPENAI_API_KEY and want embeddings computed, omit --skip-embeddings
5) (Optional) Create a vector index in DocumentDB that matches EMBEDDING_DIMS (1536) and preferred engine (vector-diskann / vector-hnsw). See infra/README.md and Microsoft docs for the exact create index command.
6) Run the CLI REPL: python app.py
   - Ask product questions. The app will retrieve top-5 chunks and either call the configured LLM (if OPENAI_API_KEY present) or produce a fallback framed answer.
7) For a one-shot test retrieval (non-interactive): python run_sample_query.py


## Verified by running

- pip install -r requirements.txt: succeeded (installed pymongo, python-dotenv, openai, pytest, and dependencies)
- pytest: 1 passed (tests/test_utils.py)
- seed.py --skip-embeddings: succeeded (Inserted 5 products into sample_retail_13.products; created/updated 5 chunks in sample_retail_13.product_chunks)
- documentdb_find_documents (via MCP): queried sample_retail_13.products and sample_retail_13.product_chunks; returned inserted documents
- run_sample_query.py: executed retrieval fallback; returned top-5 chunks for sample query

## Not verified

- Vector index creation on the cluster (cosmosSearch vector index) — attempted to call the documentdb_create_index helper but it failed; I did NOT create/verify a vector index (evidence: documentdb_list_indexes returned only _id index). Reason: MCP create_index call returned an error; exact cluster-side createIndexes with cosmosSearchOptions was not run successfully by the helper (tool failure).
- Embedding computation and storage: not executed during verification (seed was run with --skip-embeddings). This is because OPENAI_API_KEY was not provided in the environment for the verification run. If you set OPENAI_API_KEY and re-run seed.py (without --skip-embeddings), the script will compute embeddings and store them on chunk documents.
- Server-side $search cosmosSearch vector queries: not verified because no vector index and (during verification) embeddings were not present. The app falls back to text-based retrieval in that case.
- LLM generation (OpenAI ChatCompletion) was not exercised in verification because OPENAI_API_KEY was not set in the verification environment. The code path is present and will call OpenAI if OPENAI_API_KEY is set.

## Open issues

- Vector index creation: the MCP helper call to create a cosmosSearch (vector) index failed. The sample includes guidance in README/infra/README.md about the index parameters to create (dimensions must match EMBEDDING_DIMS). To complete the RAG flow, create a vector index on the product_chunks.embedding field (e.g., kind vector-hnsw or vector-diskann with dimensions=1536) using Azure docs or portal/az CLI. After creating the index and inserting embeddings, the app's vector search path will be usable.
- Embedding & LLM dependencies: The run environment did not provide OPENAI_API_KEY during verification. Re-run: remove --skip-embeddings when calling seed.py with OPENAI_API_KEY set so embeddings are computed and stored, then create the vector index, then run app.py to exercise full embedding -> server-side vector search -> LLM generation flow.
- Optional LlamaIndex integration: I removed 'llama-index' from requirements because the pinned versions in quick tests showed Python version constraints (the environment is Python 3.13). If you want LlamaIndex support, install a compatible LlamaIndex release for your Python version or run this sample on a Python 3.11/3.10 environment (then add llama-index to requirements).
- Index creation automation: I attempted to create the vector index via the documentdb_create_index MCP helper but the call failed (tool error). If you want automated index creation as part of seeding, either (a) run a code path that calls the appropriate createIndexes runCommand with cosmosSearchOptions on a client that supports it, or (b) use the portal/az CLI/documentdb MCP tools with the correct parameters. I did not retry the index creation after the first failure to avoid destructive or repeated control-plane calls.

## Files

- `README.md`
- `requirements.txt`
- `.env.example`
- `data/sample_products.json`
- `db.py`
- `utils.py`
- `seed.py`
- `app.py`
- `infra/README.md`
- `tests/test_utils.py`
- `run_sample_query.py`

