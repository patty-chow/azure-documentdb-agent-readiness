Medical Imaging Metadata Store (Azure DocumentDB + OpenAI embeddings)

This sample shows how to store medical imaging metadata (modality, body_part, findings) in Azure DocumentDB and add semantic search via OpenAI embeddings and DocumentDB vector indexes.

Files:
- app/main.py - FastAPI service exposing /search
- app/db.py - MongoDB client helper
- seed.py - Seed dataset (creates documents with embeddings)
- requirements.txt - Python dependencies
- .env.example - Example environment variables

Prerequisites
- Python 3.10+
- A reachable Azure DocumentDB cluster. Set DOCUMENTDB_URI env var to the MongoDB connection string.
- (Optional) OPENAI_API_KEY if you want real embeddings; otherwise the seed will generate synthetic embeddings for demo.

Quickstart
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. Copy .env.example to .env and set DOCUMENTDB_URI (and OPENAI_API_KEY to compute real embeddings)
4. python seed.py
   - This inserts ~50 sample documents into the database named sample_healthcare_04 and collection medical_images.
   - If OPENAI_API_KEY is set, embeddings are computed with the model specified in OPENAI_MODEL; otherwise random embeddings are used.
5. Start the API: uvicorn app.main:app --reload
6. Example search:
   curl "http://127.0.0.1:8000/search?q=pulmonary%20nodule&k=5"

Notes and limitations
- For the native DocumentDB vector index to work, embeddings are stored as a number[] in the "embedding" field and a vector index must be created (the seed script does not create the index; the sample's verification step shows index creation via the DocumentDB MCP tool).
- This is a demo only. Do not use as-is for protected health information (PHI) or production workloads without proper compliance, encryption, and access controls.
