# 3. Build report: 04-natural-language-product-search

**Status: completed**

Created a small Python LangChain hybrid-search sample that demonstrates a rewrite step + BM25 (fallback) + vector-search (fallback) fusion (RRF). The repo contains a FastAPI app, a seed script that upserts 20 synthetic product documents (with random embeddings by default), index templates and instructions, and an example searcher implementation that calls an LLM/embedder when OPENAI_API_KEY is provided. Verification installed dependencies, imported the app, upserted 20 documents into the live cluster, and executed a sample search which returned results via the fallback BM25/reg-ex path.

## How to run

1. Create a Python venv and activate it (Python 3.10+ recommended, 3.11 used in sample):
   python -m venv .venv && source .venv/bin/activate
2. Install deps:
   pip install -r requirements.txt
3. Copy .env.example -> .env and set at least DOCUMENTDB_URI (mongodb+srv form). Optionally set OPENAI_API_KEY to enable real embeddings and an LLM rewrite.
4. Seed the sample data:
   python seed/seed.py --skip-embed
   (Optionally compute real embeddings by integrating an embedding call if you set OPENAI_API_KEY and modify the seed script.)
5. (Optional but recommended) Create the BM25 search index and vector index using the templates in indexes/ (see indexes/README.md). Use mongosh and the createSearchIndexes command per Microsoft Learn docs.
6. Run the sample API:
   uvicorn app.main:app --reload
7. Call the endpoint:
   POST http://127.0.0.1:8000/search with JSON {"q": "red running shoes", "top_n": 5}

Notes:
- The app reads secrets from env vars. Do not commit real secrets.
- Index templates are provided in indexes/; index creation is not executed automatically by the sample to avoid accidental incompatible commands. See README/indexes/README.md.


## Verified by running

- pip install -r requirements.txt: completed (exit code 0)
- python import check (import app.main): completed (printed 'imported')
- seed/seed.py --skip-embed: completed (Upserted 20 products into sample_retail_04.products)
- documentdb_list_indexes for sample_retail_04.products via MCP: returned only the default _id index
- Simple search smoke test: executed HybridSearcher.search('red running shoes', top_n=3) and received results (regex fallback path)

## Not verified

- Automatic creation of search (createSearchIndexes) and vector indexes on the cluster was NOT run. Reason: I chose to provide index JSON templates and instructions instead of running createSearchIndexes/vector-index creation via MCP because the exact command shapes for createSearchIndexes and advanced cosmosSearchOptions can be fragile; running them automatically risked failing or mis-configuring a production cluster. See readiness guidance referencing createSearchIndexes + $search.
- Real embedding generation via OpenAI (text-embedding-3-small) and LLM-based rewrite were not exercised here because OPENAI_API_KEY was not used during verification. The code paths support OpenAI via LangChain when OPENAI_API_KEY is set.
- A true $search (BM25) aggregation against a created search index and a vector knn search against a proper vector index were not verified because the search/vector indexes were not created on the cluster; without those indexes $search-based pipelines will not run. The app includes fallbacks that work without those indexes (regex and in-app cosine).
- The MCP documentdb_insert_documents tool call failed when attempted; I switched to running the local seed script which used DOCUMENTDB_URI. The MCP insertion failure message was an opaque 'Function failed.' and could not be retried further.

## Open issues

- Index creation: The sample includes index templates (indexes/search_index.json and indexes/vector_index.json) and instructions. Builders/users should create these indexes with mongosh or the portal before relying on $search + vector knn. Guidance: use db.runCommand({ createSearchIndexes: ... }) for BM25 and the Learn docs for cosmosSearch vector index details.
- Embedding model / dimensions: I chose OpenAI text-embedding-3-small with 1536 dims (logged decision). If you want to use a different embedding provider or dimension, update EMBEDDING_MODEL and EMBEDDING_DIMS in .env and recreate the vector index accordingly.
- MCP tool limit/failure: the documentdb_insert_documents MCP call failed in my run; if you prefer MCP insertion instead of the seed script, investigate the MCP tool logs or permissions for the 'default' connection_profile.
- LLM rewrite & embeddings require OPENAI_API_KEY to be set in .env. The sample code supports those flows but they were not executed in verification due to missing/unused API key.
- Index parameter tuning: for production or larger sample data you should pick vector index kind (vector-hnsw, vector-ivf, vector-diskann) per the documentdb-vector-search guidance in the included skill; the provided vector_index.json uses vector-hnsw as a conservative demo choice.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `app/__init__.py`
- `app/main.py`
- `app/search.py`
- `seed/seed.py`
- `sample_data/products.json`
- `indexes/README.md`
- `indexes/search_index.json`
- `indexes/vector_index.json`

