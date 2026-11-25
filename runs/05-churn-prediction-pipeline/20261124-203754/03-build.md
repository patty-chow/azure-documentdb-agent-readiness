# 3. Build report: 05-churn-prediction-pipeline

**Status: partial**

I built a small Python sample that seeds synthetic customer and transaction data, computes RFM features by aggregation, and creates a DocumentDB vector index for RFM embeddings. The repo contains a CLI agent that will perform a vector KNN search (via $search/knn) and optionally call an LLM to generate a churn narrative. I verified the database writes, aggregation, and index creation against the live DocumentDB cluster. End-to-end embedding computation and LLM narrative generation could not be executed because embedding/LLM credentials were not present in the environment; those steps are implemented but skipped when credentials are missing.

## How to run

1) Create/activate a Python virtualenv (recommended).
2) Install dependencies: pip install -r requirements.txt
3) Copy .env.example -> .env and set DOCUMENTDB_URI to your cluster connection string. Optionally set OPENAI_API_KEY and OPENAI_EMBEDDING_MODEL / OPENAI_LLM_MODEL if you want to compute embeddings and generate LLM narratives.
4) Seed sample data: python scripts/seed.py
5) Compute RFM (aggregation & upsert): python scripts/compute_rfm.py
6) Create vector index (dimensions must match your embedding model): python scripts/create_vector_index.py --dimensions 1536 --index-kind vector-hnsw
7) (Optional) Compute embeddings for each customer and store in customers.rfm_embedding (not provided automatically without OPENAI credentials). See README for guidance.
8) Run the agent CLI for a customer: python run_agent.py --customer-id <CUSTOMER_ID> (the agent will report RFM and attempt vector search; if OPENAI_API_KEY is set it will also try to call the LLM).

## Verified by running

- pip install -r requirements.txt: success (packages installed)
- python scripts/seed.py: success (Inserted 200 customers and ~2132 transactions into database sample_customer_360_05)
- python scripts/compute_rfm.py: success (Aggregated RFM for 200 customers and upserted rfm fields into customers collection)
- python scripts/create_vector_index.py --dimensions 1536 --index-kind vector-hnsw: success (createIndexes returned ok)
- documentdb_list_indexes (MCP tool) for database sample_customer_360_05, collection customers: returned two indexes including 'idx_rfm_embedding_vector' with cosmosSearchOptions {'kind': 'vector-hnsw', 'dimensions': 1536, 'similarity': 'COS'}
- documentdb_find_documents (MCP tool) for collection customers (limit=5): returned documents showing rfm fields and rfm_embedding as an empty list (seeded/updated as expected)
- python run_agent.py --customer-id <sample_id>: success (printed customer RFM and correctly reported 'No embedding present for customer. Compute embeddings first.')

## Not verified

- Computing embeddings with OpenAI text-embedding-3-small and storing them in customers.rfm_embedding: not run because OPENAI_API_KEY was not present in the environment.
- End-to-end vector similarity retrieval using stored embeddings (kNN results based on real embeddings): not verified because there are no embeddings stored.
- LLM churn-risk narrative generation using OpenAI (gpt-4o-mini or configured model): not executed because OPENAI_API_KEY was not present.

## Open issues

- Embedding/LLM credentials missing: The environment lacked OPENAI_API_KEY (or equivalent). The README and .env.example note required variables. Without these keys the sample cannot compute embeddings or invoke the LLM for narratives; the rest of the pipeline (RFM, index creation) works without them.
- run_agent.py currently expects rfm_embedding to be populated (number[]). The sample includes an index and search pipeline, but you must compute and store embeddings (e.g., via OpenAI) before the agent returns meaningful vector neighbors.
- I inserted a convenience create_vector_index.py that runs createIndexes via db.command with 'cosmosSearchOptions'. This worked in this environment to add the vector index; depending on account privileges this command might fail for other users. The README calls this out.
- mongosh is not installed on PATH in this environment (readiness report). I verified programmatically using pymongo and the documentdb MCP tools; interactive mongosh debugging is recommended to developers for manual troubleshooting but was not used here.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `LICENSE`
- `src/__init__.py`
- `src/db.py`
- `scripts/seed.py`
- `scripts/compute_rfm.py`
- `scripts/create_vector_index.py`
- `run_agent.py`

