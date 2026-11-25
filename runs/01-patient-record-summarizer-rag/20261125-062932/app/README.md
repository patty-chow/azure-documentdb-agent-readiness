Patient Record Summarizer (RAG) - Azure DocumentDB Sample

Overview

This sample demonstrates a retrieval-augmented generation (RAG) workflow that stores chunked patient records and their embeddings in an Azure DocumentDB (MongoDB-wire) cluster and provides a simple FastAPI endpoint to retrieve the most relevant chunks for a clinical question and return a grounded clinical summary with references.

Important notes
- This repo is a demonstration only. Do NOT use real PHI. Data in data/ is synthetic.
- The sample expects a reachable Azure DocumentDB cluster and an OpenAI API key for embeddings/LLM.
- Do not hard-code secrets. Set DOCUMENTDB_URI and OPENAI_API_KEY in your environment (see .env.example).

What this sample shows
- Chunking of patient documents and storage of chunks in a DocumentDB collection (patient_chunks).
- Storing embeddings with each chunk in the DB and performing application-side cosine similarity re-ranking.
- A FastAPI POST /search endpoint: accepts {patientId, question, top_k?} and returns {answer, sources, debug}.
- A seed script (seed.py) to insert synthetic sample data into the database (idempotent).

Prerequisites
- Python 3.10+ (the build environment used Python 3.13)
- An Azure DocumentDB (MongoDB-compatible) cluster reachable from your machine. Its connection string should be available in the environment variable DOCUMENTDB_URI.
- An OpenAI API key in OPENAI_API_KEY for embeddings and summarization (optional for running seed; seed will generate random vectors if OPENAI_API_KEY is not present).

Quickstart
1. Create and activate a virtual environment, then install:
   python -m pip install -r requirements.txt

2. Set environment variables (example shown for bash):
   export DOCUMENTDB_URI="<your_documentdb_connection_string>"
   export OPENAI_API_KEY="<your_openai_key>"  # optional for seed; required for real embeddings/chats

3. Seed the sample data (writes to database sample_healthcare_01, collection patient_chunks):
   python seed.py

4. Run the API locally:
   uvicorn app.main:app --reload

5. Example POST to /search (http://127.0.0.1:8000/search):
   {"patientId": "patient_1", "question": "Summarize recent cardiology history and meds.", "top_k": 5}

Design decisions and notes
- Language/runtime: Python 3.x chosen for LlamaIndex and pymongo integration.
- Driver: pymongo used for data-plane access. Embeddings stored as arrays on each document.
- Retrieval: application-side re-rank (cosine similarity) is used to avoid relying on provider-specific vector index creation syntax. The repository includes notes about how to add a native index if your cluster supports it.
- Embeddings/LLM: OpenAI is used by default (text-embedding-3-small, 1536 dims) — configure via OPENAI_API_KEY.
- LlamaIndex: used for prompt/context construction and to illustrate integration points. The retrieval step uses embeddings stored in DocumentDB and Python re-ranking.

Testing
- Unit tests are included that mock out the database and OpenAI calls. Run with:
   pytest -q

Cleaning up
- To remove sample data from your cluster, connect with your preferred mongo client and drop the sample database sample_healthcare_01 or the collection patient_chunks.

License
MIT (see LICENSE)
