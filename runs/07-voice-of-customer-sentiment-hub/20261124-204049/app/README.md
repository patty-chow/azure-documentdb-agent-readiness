Voice of Customer — Sentiment Hub sample

What this sample shows
- Ingest customer feedback from multiple channels (email, chat, survey)
- Use a prompt-engineered LLM to extract sentiment (label + score), key topics, and a verbatim quote
- Produce embeddings and persist enriched documents in Azure DocumentDB (MongoDB wire protocol)
- Create a vector search index (createSearchIndexes) and text/field indexes when possible
- Run aggregation pipelines to surface net sentiment by channel, topic, and time period

Prerequisites
- Python 3.11+ and pip
- An Azure DocumentDB cluster reachable from this machine. Set DOCUMENTDB_URI in your environment.
- (Optional) OpenAI API key in OPENAI_API_KEY to use real LLM/embeddings. If missing the sample runs with a deterministic local fallback.

Quickstart
1. python -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. Copy .env.example to .env and fill DOCUMENTDB_URI and optionally OPENAI_API_KEY
4. Run the seed script to create sample data and (attempt to) create search indexes:
   python -m src.scripts.seed
5. Run the aggregation demo:
   python -m src.scripts.aggregations

Design decisions (short)
- Language/runtime: Python 3.11 (Beanie + Motor). See BUILD_REPORT for detailed recorded decisions.
- ODM/driver: Beanie with Motor for simplicity and direct Beanie compatibility.
- Embeddings/LLM: Default to OpenAI models (EMBEDDING_MODEL, LLM_MODEL env vars). The code falls back to simple heuristics if API keys are not available so the sample is verifiable without cloud credentials.
- Indexes: The sample attempts to create search indexes using the createSearchIndexes DB command (vector-hnsw) per DocumentDB guidance. If the live cluster rejects the command, the sample continues with stored embeddings and aggregation examples.

Files
- src/app/db.py - database connection and Beanie init
- src/app/models.py - Beanie document models
- src/app/processor.py - LLM / embeddings wrapper + ingestion logic with fallback
- src/scripts/seed.py - seed sample data and create indexes
- src/scripts/aggregations.py - run aggregation pipelines and print results
- .env.example - placeholder environment variables
- requirements.txt - pinned dependencies

Security
- Do not commit real secrets. Read DOCUMENTDB_URI and OPENAI_API_KEY from environment at runtime.

License
MIT
