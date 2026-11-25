# DocumentDB + LlamaIndex RAG Ticket Assistant (sample)

This sample demonstrates a Retrieval-Augmented Generation (RAG) workflow that stores embeddings in an Azure DocumentDB (MongoDB-compatible) vector index and uses those results to generate suggested ticket resolutions. It is a compact learning sample — do not use as-is in production.

What the sample shows
- Seed a DocumentDB database (`sample_customer_360_10`) with synthetic knowledge-base articles and past ticket resolutions.
- Create a vector index (HNSW) on the `embedding` field of the `kb_documents` collection.
- Query the vector index with a ticket embedding to retrieve the top-5 similar documents.
- Use the retrieved documents as context to generate a concise suggested resolution.

Prerequisites
- Python 3.13 on PATH (the run environment provides Python 3.13).
- A reachable Azure DocumentDB cluster connection string set in the environment variable `DOCUMENTDB_URI` (do not commit secrets).
- (Optional) OPENAI_API_KEY if you want real embeddings and LLM responses. If not set, the sample uses deterministic pseudo-embeddings and returns a template suggestion.

Files
- seed.py - idempotent script to populate the `kb_documents` collection and create vector/indexes.
- app.py - minimal Flask app exposing POST /suggest to get a suggested resolution for a ticket.
- tools/submit_ticket.py - CLI helper to POST a ticket to /suggest (for local testing).
- .env.example - example environment variables to copy to `.env`.
- requirements.txt - pinned dependencies.

Quickstart
1. Copy the example env file and edit:
   cp .env.example .env
   # fill DOCUMENTDB_URI and optionally OPENAI_API_KEY

2. Create virtualenv and install dependencies
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

3. Seed the database (creates indexes and inserts sample docs)
   python seed.py

4. Run a quick retrieval verification (non-server)
   python -m src.verify_retrieval

5. Run the Flask app
   python app.py

6. POST a ticket (example):
   curl -X POST http://127.0.0.1:5000/suggest -H 'Content-Type: application/json' \
     -d '{"ticket_text": "Users cannot login with SSO after password rotation"}'

Notes and cleanup
- The sample writes to the `sample_customer_360_10` database only.
- To remove sample documents, connect to the database and drop the `kb_documents` collection.

Security
- The app reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables at runtime — do not commit secrets into source control.

License: MIT
