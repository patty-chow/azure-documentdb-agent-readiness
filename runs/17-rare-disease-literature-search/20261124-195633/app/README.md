Rare disease literature search sample using Azure DocumentDB (MongoDB-compatible) and LlamaIndex

This sample shows:
- Ingesting PubMed abstracts via NCBI E-utilities
- Chunking text with LlamaIndex token splitter
- Embedding chunks with OpenAI embeddings
- Storing vectors and metadata in an Azure DocumentDB collection `sample_healthcare_17.pubmed_chunks`
- Creating a native vector index (cosmosSearch / vector-diskann)
- Exposing a FastAPI /query endpoint that performs a vector $search and returns a generated answer with ranked citations (pmid + year)

Prerequisites
- Python 3.10+ available as `python` and `pip`
- A reachable Azure DocumentDB cluster with connection string in env var DOCUMENTDB_URI
- An OpenAI API key in env var OPENAI_API_KEY

Setup
1. Copy .env.example to .env and fill in DOCUMENTDB_URI and OPENAI_API_KEY.
2. python -m venv .venv && source .venv/bin/activate
3. pip install -r requirements.txt

Seeding data (small sample)
- Run: python scripts/seed.py --count 20

Run the server
- uvicorn src.app:app --reload --port 8000
- POST /query with JSON {"query": "What are recent findings about rare genetic diseases?"}

Security
- Do not commit secrets. The sample reads DOCUMENTDB_URI and OPENAI_API_KEY from the environment.

Notes
- The sample creates a collection `pubmed_chunks` in DB `sample_healthcare_17`.
- Index creation uses the DocumentDB MCP server (documentdb_create_index) when available; otherwise it attempts to create the index via a runCommand using PyMongo.

License and data
- Uses PubMed abstracts obtained via NCBI E-utilities (public domain/publicly available abstracts). Respect NCBI's terms of use and rate limits.
