Azure DocumentDB Fraud Detection Sample (LangChain + Vector Search)

This sample demonstrates using Azure DocumentDB (MongoDB-compatible) as a vector store for a simple fraud-detection similarity check. It:

- Encodes transaction text/features to embeddings (sentence-transformers/all-MiniLM-L6-v2, 384 dims)
- Stores known fraud pattern vectors in a collection (`sample_fintech_01.fraud_patterns`)
- Runs a vector search using the `$search` aggregation stage and the `cosmosSearch` operator
- Produces a numeric fraud risk score and a human-readable explanation of matching patterns

Files in this sample:
- README.md - this file
- .env.example - environment variables you must set
- requirements.txt - Python dependencies
- docdb_client.py - MongoClient singleton helper
- embeddings.py - local sentence-transformers embedding helper
- seed.py - idempotent seed script to insert sample fraud patterns (computes embeddings)
- run_agent.py - demo script: encodes a sample transaction, performs vector search, prints a risk score and explanation

Prerequisites
- Python 3.10+ available on PATH
- An Azure DocumentDB cluster reachable from this machine. Put its MongoDB connection string into DOCUMENTDB_URI (see .env.example).

Important: Do NOT commit secrets. The sample reads DOCUMENTDB_URI from environment variables at runtime.

Quickstart
1. Create and activate a virtualenv (recommended):
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows

2. Install dependencies:
   pip install -r requirements.txt

3. Copy .env.example to .env and fill DOCUMENTDB_URI

4. Seed the database with sample fraud patterns (computes embeddings locally):
   python seed.py

5. Run the demo agent on a sample transaction:
   python run_agent.py "suspicious transaction: high amount, new payee, rapid sequence"

Repository notes
- The seed script is idempotent and uses upsert semantics by pattern_name.
- The sample uses a local embedding model (all-MiniLM-L6-v2) to avoid requiring cloud API keys; you can optionally set OPENAI_API_KEY to enable LLM-based explanations in run_agent.py.

Security
- The sample reads the DocumentDB connection string from DOCUMENTDB_URI and does not write secrets to files.

Cleaning up
- Remove sample documents from the `sample_fintech_01` database using your preferred MongoDB tool or the Azure portal if desired.

References
- Azure DocumentDB vector search docs: https://learn.microsoft.com/azure/documentdb/vector-search
