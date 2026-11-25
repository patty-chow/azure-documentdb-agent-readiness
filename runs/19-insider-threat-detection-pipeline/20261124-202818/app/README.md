Insider Threat Detection sample using Azure DocumentDB (vector search)

This sample demonstrates a pipeline that:
- Seeds synthetic employee activity logs into an Azure DocumentDB database (sample_banking_19.activity_logs)
- Aggregates per-employee behavioural feature vectors (recent window)
- Calls OpenAI embeddings to embed the feature representation
- Stores embeddings into a DocumentDB collection (employee_vectors)
- Demonstrates creating a vector-ivf index on the embedding field
- Runs a nightly job that computes similarity between recent embedding and historical centroid and flags anomalies

Prerequisites
- Python 3.11+ (this project used Python 3.13)
- An Azure DocumentDB cluster reachable; set DOCUMENTDB_URI in environment
- OpenAI API key (OPENAI_API_KEY)

Quickstart
1. Create and activate a venv
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
2. Install dependencies
   pip install -r requirements.txt
3. Copy .env.example to .env and fill in values or export env vars
4. Seed sample data
   python -m sample.seed
5. Create vector index (one-time)
   python -m sample.create_indexes
6. Run a single ingestion (aggregate + embed)
   python -m sample.ingest
7. Simulate nightly run
   python -m sample.run_nightly

Notes
- Secrets are read from environment variables; do not commit real secrets.
- Scheduling is demonstrated via a cron example in docs/cron_example.txt; the sample provides a CLI-run 'run-nightly' command instead of an installed scheduler.

Non-goals and Costs
- This sample uses synthetic, non-PII data. It is small-scale and intended for learning only.
- Embeddings will incur OpenAI API costs. Use the embedding model and frequency appropriate for your account.
