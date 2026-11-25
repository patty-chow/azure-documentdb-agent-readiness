Churn Prediction Pipeline Sample (DocumentDB + LangChain)

What this sample shows

- How to connect to an existing Azure DocumentDB (MongoDB-compatible) cluster using PyMongo.
- How to seed a small synthetic dataset of customers and transactions.
- How to compute RFM (Recency, Frequency, Monetary) feature vectors via a MongoDB aggregation pipeline and upsert them into a `customers` collection.
- How to create a DocumentDB vector index for RFM embeddings (dimensions configurable) and how to retrieve nearest churned customer profiles.
- A simple LangChain-based agent CLI that, given a customer_id, retrieves nearest churned neighbors and (optionally) uses an LLM to generate a churn-risk narrative and recommended retention action.

Important notes

- This sample uses an already-provisioned Azure DocumentDB cluster. Do NOT provision or modify cloud resources as part of the sample.
- Read the DocumentDB connection string from the environment variable DOCUMENTDB_URI. Never commit secrets into the repo.
- Embedding/LLM credentials are NOT included. Provide OPENAI_API_KEY in your environment if you want end-to-end embedding and narrative generation.

Prerequisites

- Python 3.10+ (python on PATH)
- pip available
- An Azure DocumentDB cluster reachable from this machine. Its connection URI must be set in DOCUMENTDB_URI in your environment or in a .env file.
- (Optional) OpenAI API key for embeddings and LLM (set OPENAI_API_KEY). Configure OPENAI_EMBEDDING_MODEL (default: text-embedding-3-small) and OPENAI_LLM_MODEL (default: gpt-4o-mini) in .env or environment.

Setup

1. Create and activate a virtual environment (optional but recommended):

   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate    # Windows

2. Install dependencies:

   pip install -r requirements.txt

3. Copy .env.example to .env and fill in DOCUMENTDB_URI and optionally OPENAI_API_KEY.

   cp .env.example .env

Seeding the sample dataset

- The seed script creates two collections in the database `sample_customer_360_05`: `customers` and `transactions`.
- Run:

   python scripts/seed.py

Compute RFM and upsert customers

- Run the aggregation that computes RFM per customer and upserts results into `customers`:

   python scripts/compute_rfm.py

Create a vector index (optional)

- If you plan to run vector similarity searches you should create a vector index that matches your embedding dimensionality.
- Default embedding model in this sample is text-embedding-3-small (1536 dims). To create the index:

   python scripts/create_vector_index.py --dimensions 1536 --index-kind vector-hnsw

Note: creating vector indexes is a data-plane operation against the DocumentDB cluster and requires that your account has the necessary privileges.

Run the agent (CLI)

- Once RFM embeddings are present for a customer (and optionally you have computed embeddings), run:

   python run_agent.py --customer-id <CUSTOMER_ID>

- If embeddings are missing the agent will still show RFM scores and neighbors may be empty.

Cleaning up

- This sample writes documents into the database `sample_customer_360_05`. To remove the collections, use a MongoDB client or the provided cleanup snippet in this README.

Limitations and verification

- The sample assumes OPENAI_API_KEY may not be present in the environment. If it is absent, embedding and LLM steps are skipped; the pipeline still computes RFM and stores empty embeddings.
- The repository intentionally does not create or tear down cloud infrastructure.

License

MIT
