DocumentDB Returns Orchestration Sample

This sample demonstrates a Node.js + LangChain orchestration that:
- Fetches an order from an Azure DocumentDB (MongoDB-compatible) cluster (via Mongoose)
- Passes the order to a policy agent (LLM) to decide eligibility
- Passes the result to a refund-calculation agent (LLM)
- Passes the refund result to a comms agent (LLM) to generate customer notification
- Persists the final return document into the `returns` collection

Prerequisites
- Node 24+ and npm
- An Azure DocumentDB cluster reachable via the connection string in DOCUMENTDB_URI (env var)
- (Optional) An OpenAI API key in OPENAI_API_KEY if you want live LLM calls. If not provided, the sample uses deterministic mock LLM outputs for demos and tests.

Files
- src/: application source (models, orchestration, server)
- scripts/seed.js: seeds two sample orders into the `orders` collection
- scripts/demo.js: runs two demo scenarios (approved and rejected) using the orchestration (mocked if OPENAI_API_KEY not set)
- .env.example: example env file

How to run (local dev)
1. Copy .env.example to .env and set DOCUMENTDB_URI (and optionally OPENAI_API_KEY)
2. npm install
3. npm run seed    # idempotent, inserts two sample orders
4. npm run demo    # runs two scenarios and prints the persisted return documents

Security
- Do not commit secrets. This repo reads DOCUMENTDB_URI and OPENAI_API_KEY from environment variables.

Notes
- This sample is intentionally small and uses a mock LLM if OPENAI_API_KEY is not set to avoid unexpected costs during demos.
- The sample uses database `sample_retail_18` and collections `orders` and `returns`.
