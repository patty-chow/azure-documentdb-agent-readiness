Customer Complaint Classifier sample

This sample demonstrates a Python FastAPI + Beanie app that reads unclassified complaint documents from an Azure DocumentDB (Mongo-compatible) cluster, classifies them with an LLM, stores embeddings, and exposes search and hotspots aggregation endpoints.

Prerequisites
- Python 3.10+ (virtualenv recommended)
- An Azure DocumentDB cluster reachable; set DOCUMENTDB_URI in .env (see .env.example)
- OPENAI_API_KEY set in .env for embeddings and classification (or set mocks for tests)

Quickstart
1. pip install -r requirements.txt
2. cp .env.example .env and fill values
3. (optional) Run the seed script to populate sample data:
   python -m src.seed.seed --uri "$DOCUMENTDB_URI" --db sample_banking_14
4. Start the API:
   uvicorn src.app.main:app --reload

What the sample shows
- Beanie Document model for complaints
- LangChain/OpenAI-based classification pipeline (LLM + embeddings)
- Vector index creation guidance (cosmosSearch) in scripts
- Aggregation pipeline returning hotspots by product_category

Tests
- pytest (tests mock network/AI calls so they run offline)

Security
- Do not commit secrets. Read connection string and API keys from environment.

License: MIT
