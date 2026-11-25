Visual similarity search sample for Azure DocumentDB (MongoDB-wire-compatible)

This sample encodes product images with CLIP, stores 512-d float32 embeddings as BSON Binary subtype 0x09, attempts to create a vector-ivf index, and exposes a /visual-search endpoint.

Prerequisites
- Python 3.10+ (venv recommended)
- A vector-capable Azure DocumentDB cluster reachable; set DOCUMENTDB_URI in .env or environment

Setup
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. cp .env.example .env and set DOCUMENTDB_URI
4. python seed.py  # creates sample_data and seeds the sample_retail_11.products collection
5. uvicorn app.main:app --reload

Usage
POST /visual-search (multipart/form-data; field 'image')
Returns up to 8 visually similar products with scores.

Notes on index creation and vector search
- The sample attempts to create a vector-ivf index on products.embedding with dimensions=512 and nlist=100. Exact index option names vary across providers; the seed script captures and logs server errors if the createIndex call is rejected.
- If the cluster does not support vector search via server-side query syntax, the API falls back to fetching embeddings and computing similarity locally (suitable for small datasets and demonstration).

Files
- app/: FastAPI app and helpers
- seed.py: generates placeholder images and seeds the DB
- sample_data/: generated images

Security
- Do NOT commit secrets. DOCUMENTDB_URI must only be read from environment or .env at runtime.

What I verified
- Unit tests for embedding pack/unpack ran (see build report in repository root).

What I could not verify
- Whether the attempted vector index creation options are accepted by your DocumentDB cluster; check logs when running seed.py. Exact server option names were not available in the local builder environment.
