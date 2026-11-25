Visual similarity search sample using Azure DocumentDB (Mongo-compatible)

This sample shows how to:
- Encode images with CLIP (512-d embeddings)
- Store embeddings as BSON binary subtype 0x09
- Create a vector-ivf index on the embedding field
- Expose a /visual-search HTTP endpoint that returns the top-8 visually similar products

Prerequisites
- Python 3.10+ and pip
- A reachable Azure DocumentDB cluster; set DOCUMENTDB_URI in environment

Quickstart
1. Create virtualenv and install dependencies:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Copy .env.example to .env and set DOCUMENTDB_URI.

3. Seed the sample data (this will download images and upload embeddings):
   python scripts/seed.py

4. Run the API:
   uvicorn app.main:app --reload --port 8000

5. Call the visual search endpoint (example using curl):
   curl -F "file=@query.jpg" http://localhost:8000/visual-search

Cleanup
- Delete the database `sample_retail_11` from your cluster if desired.

Design Notes
- Embeddings are stored as float32 little-endian bytes wrapped in bson.Binary subtype 0x09.
- The app reads DOCUMENTDB_URI at runtime and never logs secrets.

Limitations
- This sample uses the connection string auth; AAD/OIDC driver auth is not shown.
