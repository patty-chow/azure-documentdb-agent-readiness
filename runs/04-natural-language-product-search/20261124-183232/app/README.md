# 04-natural-language-product-search

This sample shows a Python LangChain-based hybrid search agent that queries Azure DocumentDB (MongoDB wire protocol) using both BM25 full-text ($search) and vector search, then fuses results (RRF) and returns the best matches.

What it includes
- FastAPI app (POST /search) demonstrating a rewrite step then hybrid search.
- A small synthetic product dataset and a seed script.
- .env.example showing required environment variables.
- Index JSON templates (search index + vector index) and instructions (README) to create them.

Prereqs
- Python 3.10+ (3.11 recommended)
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI in .env pointing to it.
- (Optional) OPENAI_API_KEY for embeddings and rewrite via LangChain/OpenAI. If not provided the sample falls back to a simple rewrite and requires precomputed embeddings in the DB.

Setup
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.example .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY to enable embeddings)
4. Option A (recommended): run `python seed/seed.py --use-openai` to compute real embeddings and insert sample docs.
   Option B: run `python seed/seed.py --skip-embed` to insert docs with random embeddings (for demo only).
5. Create the search and vector indexes in your cluster using the templates in `indexes/` (instructions in indexes/README.md). The sample works best with a createSearchIndexes BM25 index on `title`/`description` and a vector index on `embedding`.

Run
- Start the app: uvicorn app.main:app --reload
- POST /search with JSON {"q": "red running shoes", "top_n": 5}

Notes and non-goals
- This is an educational sample. It is not production-ready (no auth, no CMK, no private endpoints).
- The repository never writes secrets; read them from environment variables.

Files created by this sample
- app/main.py - FastAPI application and hybrid search glue
- app/search.py - Core search and LangChain rewrite/embedding helper
- seed/seed.py - Seed script to insert synthetic product docs
- sample_data/products.json - Synthetic product docs
- indexes/ - Templates and instructions for creating search/vector indexes
