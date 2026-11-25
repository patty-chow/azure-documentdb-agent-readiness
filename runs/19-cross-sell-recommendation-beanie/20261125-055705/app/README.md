# Cross-sell Recommendation (Beanie + Azure DocumentDB)

This sample shows how to build an async Python service using Beanie ODM that:
- Aggregates co-purchase pairs from order history stored in Azure DocumentDB
- Generates embeddings using OpenAI and stores vectors in DocumentDB
- Exposes a /cross-sell endpoint that accepts a basket of product IDs and returns top-5 recommendations ranked by an "affinity" score (combines vector similarity and co-purchase frequency)

Prerequisites
- Python 3.10+ (venv recommended)
- A vector-capable Azure DocumentDB cluster reachable via `DOCUMENTDB_URI` env var
- An OpenAI API key in `OPENAI_API_KEY`

Quickstart
1. Copy `.env.example` to `.env` and fill values, or export env vars.
2. Create and activate a virtualenv, install deps:
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
3. Seed sample data (writes to the `sample_retail_19` database):
   python seed.py
4. Start the service:
   uvicorn app.main:app --reload
5. Request cross-sell:
   curl -X POST localhost:8000/cross-sell -H "Content-Type: application/json" -d '{"basket":["prod_1","prod_2"]}'

Notes and design decisions
- Secrets are read from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY). See `.env.example`.
- Embeddings: uses OpenAI model `text-embedding-3-small` (1536 dims) by default. Change EMBEDDING_MODEL in env to use another model.
- Data model: collections `products`, `orders`, `product_pairs` in database `sample_retail_19`.
  - products: {_id, name, embedding, embedding_model, dimensions}
  - orders: {_id, items: [product_id], ts}
  - product_pairs: {_id, product_ids: [a,b], count, embedding, embedding_model, dimensions, updated_at}
- Indexing: For production, create a vector index (e.g., vector-diskann) on product_pairs.embedding using DocumentDB's `createSearchIndexes` / `cosmosSearch`. This sample does not modify cluster indexes automatically; see skills/docs and the provided `index_example.json`.

Testing
- Unit tests mock DB and OpenAI (pytest). Run:
  pytest -q

Limitations
- This sample focuses on demonstrating the end-to-end flow. Production considerations (Private Endpoints, CMK, RBAC, rate limits) are out of scope and noted in docs.

References
- DocumentDB vector search guidance: see documentdb-vector-search skill
