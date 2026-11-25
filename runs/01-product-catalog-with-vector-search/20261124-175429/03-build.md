# 3. Build report: 01-product-catalog-with-vector-search

**Status: partial**

Built a small Python Flask sample that demonstrates storing embeddings as BSON binary vectors, creating a vector-ivf index payload, and exposing a /search endpoint that uses a real OpenAI embedding when OPENAI_API_KEY is set or a deterministic mock embedder otherwise. The repository includes scripts to load sample data and to attempt server-side index creation. Syntax checks passed, but full integration (inserting docs, creating the index on a live DocumentDB instance, and end-to-end search using a real embedding provider) was not executed in this environment.

## How to run

1) (Optional, recommended) Start the DocumentDB local gateway for development:
   docker run -p 10260:10260 ghcr.io/documentdb/documentdb/documentdb-local:latest

2) Install Python deps in a virtual environment locally:
   python -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt

3) Copy .env.example to .env and edit if needed (set MONGO_URI to your gateway or cluster, optionally set OPENAI_API_KEY if you want real embeddings).

4) Load the sample data (computes embeddings and inserts records):
   python scripts/load_data.py --file data/sample_products.json

   - This will embed title+description using OPENAI_API_KEY (text-embedding-ada-002) if provided; otherwise it uses a deterministic mock embedder.
   - Embeddings are normalized and stored as BSON Binary (packed float32 little-endian) in the 'embedding' field. embeddingModel and embeddingDims metadata are included.

5) Create the vector index (attempts to call the server-side createSearchIndexes command; if it fails it prints the payload for manual use):
   python scripts/create_vector_index.py

   - The script prints the createSearchIndexes payload for a vector-ivf index with COS similarity and options.nlist=100.
   - If your cluster accepts the command shape, the script will attempt the db.command call; otherwise use the printed payload with mongosh or the portal admin API.

6) Run the Flask app:
   python app.py

7) Example search (curl):
   curl -X POST -H "Content-Type: application/json" -d '{"q":"comfortable running shoes"}' http://localhost:5000/search

Notes:
- The repository intentionally reads secrets from environment variables (MONGO_URI, OPENAI_API_KEY) and includes .env.example as a template. Do not commit real keys.
- If your DocumentDB cluster supports the $search knn / cosmosSearch stage and the vector index has been created, the app attempts the server-side $search pipeline. If that fails the app falls back to an in-memory cosine similarity ranking (fetches embeddings from the collection and computes dot-product ranking in-app).

## Verified by running

- py_compile: app.py, scripts/load_data.py, scripts/create_vector_index.py compiled successfully (syntax check)

## Not verified

- Inserting sample documents into a live DocumentDB cluster (scripts/load_data.py) — not executed because the runner environment prevented installing dependencies and no DocumentDB local gateway / cluster was started in this session.
- Server-side createSearchIndexes invocation against a live DocumentDB cluster (scripts/create_vector_index.py) — not executed against an actual DocumentDB instance; the script prints the payload and will attempt db.command when run in a configured environment.
- End-to-end /search behavior against a managed DocumentDB cluster with a vector-ivf index and real embeddings from OpenAI — not executed because OPENAI_API_KEY was not provided here and no cluster was available to test.
- pip install of requirements in this execution environment — failed due to the environment blocking system pip installs ('externally-managed-environment').

## Open issues

- The runner environment refused pip install (error: 'externally-managed-environment'); as a result I could not install dependencies (numpy, openai, pymongo) and could not run integration tests that require them. Workaround: run steps locally in a venv as described in README.
- No DocumentDB local gateway (Docker) or cloud cluster was started during this run, so the vector index creation and data ingestion cannot be verified programmatically from this session.
- OpenAI API key was not available in the environment. Real embeddings were not requested or tested here; the code falls back to a deterministic mock embedder for offline testing. If you provide OPENAI_API_KEY, the sample will call text-embedding-ada-002 at ingestion and query time.

## Files

- `requirements.txt`
- `app.py`
- `scripts/load_data.py`
- `scripts/create_vector_index.py`
- `data/sample_products.json`
- `README.md`
- `.env.example`
- `tests/test_utils.py`

