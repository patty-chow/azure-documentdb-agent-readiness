# 3. Build report: 17-rare-disease-literature-search

**Status: completed**

Built a small Python sample that demonstrates a LlamaIndex-based ingest pipeline for PubMed abstracts, chunking, embedding, storing vectors in an Azure DocumentDB collection, creating a native vector (DiskANN) index, and exposing a simple FastAPI query app. I created helper scripts, a seed/ingest module, an index-creation utility, and a minimal test. I verified dependency installation, ran unit tests, inserted a small set of dummy documents, and created the cosmosSearch vector-diskann index against the provided cluster. Some OpenAI-dependent flows were not executed during automated verification to avoid requiring secret API keys; instructions to run the full pipeline are in README.md.

## How to run

1) Copy .env.example to .env and fill DOCUMENTDB_URI and OPENAI_API_KEY (if running the full pipeline). 2) Create venv and install: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt. 3) To seed real PubMed abstracts (requires OPENAI_API_KEY): python src/ingest.py --count 50 (or use scripts/seed.py wrapper). 4) To create the vector index (if not already created): python -m src.create_index --dims 1536. 5) To run the server: uvicorn src.app:app --reload --port 8000. 6) Query: POST http://localhost:8000/query with JSON {"query":"your question","k":5}. See README.md for more details and notes about rate limits and safety.

## Verified by running

- pip install -r requirements.txt: succeeded (packages installed).
- pytest tests/test_chunking.py: 1 passed.
- Inserted 3 dummy documents into sample_healthcare_17.pubmed_chunks using PyMongo: succeeded.
- Created cosmosSearch vector-diskann index on sample_healthcare_17.pubmed_chunks with dimensions=1536 via PyMongo createIndexes runCommand: succeeded (index visible from client).

## Not verified

- Full OpenAI-backed ingestion (embed_texts using OpenAI Embeddings) was not executed during automated verification to avoid requiring an OPENAI_API_KEY in the build run. Reason: I intentionally used dummy zero vectors for DB verification. To verify: set OPENAI_API_KEY and run python src/ingest.py --count 20.
- End-to-end RAG answer generation using the LLM (openai.ChatCompletion in src.app) was not tested in the run because it depends on an active OPENAI_API_KEY. To verify: set OPENAI_API_KEY, start server, and POST to /query.
- DocumentDB MCP server listing of inserted documents/indexes: the documentdb MCP server reported the created index, but fetching documents via the MCP 'documentdb_find_documents' call from the agent returned an empty list in this run. The PyMongo client operations (insert + create index) succeeded locally; if MCP listing is required as authoritative, further investigation is needed (possible connection-profile mismatch).

## Open issues

- The DocumentDB MCP 'documentdb_create_index' call failed initially (tool returned 'Function failed') and I fell back to direct PyMongo runCommand to create the index. The runCommand call succeeded and the index now exists. If you prefer MCP-based index creation, re-run MCP tool and capture full error logs for root cause.
- I selected OpenAI embedding model 'text-embedding-3-small' and dimensionality 1536 by convention; the exact model/dim choice is a user decision and must be consistent between embeddings and index dimensions. This choice was recorded as a model_default decision and should be reviewed if you use a different embedding provider or model.
- The sample inserts dummy zero vectors for verification. Replace or seed real embeddings by running the ingest script with a valid OPENAI_API_KEY as documented in README.

## Files

- `requirements.txt`
- `README.md`
- `.env.example`
- `src/__init__.py`
- `src/db.py`
- `src/ingest.py`
- `src/app.py`
- `src/create_index.py`
- `scripts/seed.py`
- `tests/test_chunking.py`

