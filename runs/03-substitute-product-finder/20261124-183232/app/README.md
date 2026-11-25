Product Substitute Finder - Azure DocumentDB Sample

What this sample shows
- A small FastAPI web app using Beanie ODM and Motor to talk to an Azure DocumentDB (MongoDB-compatible) cluster.
- Ingestion script to generate synthetic product documents and embeddings for each product.
- Vector index on the product embedding field (HNSW) and a /substitute endpoint that returns 5 nearest products.

Prerequisites
- Python 3.11+ (the build machine has Python 3.13)
- An Azure DocumentDB cluster reachable via DOCUMENTDB_URI environment variable.
- (Optional) OpenAI API key in OPENAI_API_KEY to generate real embeddings; otherwise the ingest script will use deterministic random vectors.

Quickstart
1. Copy .env.example to .env and set DOCUMENTDB_URI and OPENAI_API_KEY (optional).
2. python -m pip install -r requirements.txt
3. Create indexes (optional via MCP tool) or run ingest which attempts to create index before inserting.
4. Run ingestion: python scripts/ingest.py --count 10000
   (For verification during development run with smaller count, e.g. --count 100)
5. Run the app: uvicorn app.main:app --reload
6. Open http://localhost:8000 to view the retailer UI and try /substitute via the UI.

Notes
- The app reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables. It errors clearly if DOCUMENTDB_URI is missing or connection fails.
- The sample intentionally keeps code simple and well-commented for learning.

Cleaning up
- To remove products from the sample database use your preferred MongoDB tool to drop the `sample_retail_03` database or the `products` collection.
