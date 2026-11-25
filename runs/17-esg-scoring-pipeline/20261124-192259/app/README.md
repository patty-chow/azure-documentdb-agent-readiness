Azure DocumentDB ESG Scoring Pipeline Sample

This sample demonstrates a Python LangChain-style agent that reads company ESG documents from an Azure DocumentDB cluster (MongoDB-compatible), asks an LLM to score Environmental, Social, and Governance pillars (1-10) with rationales, stores the rationales' embeddings for semantic search, and runs an aggregation pipeline to rank companies.

Important constraints
- This sample assumes an existing Azure DocumentDB cluster is reachable. Do NOT hard-code credentials. The connection URI must be provided in the environment variable DOCUMENTDB_URI.
- LLM/embedding keys (optional) use OPENAI_API_KEY. If no key is provided, the sample falls back to a deterministic local scorer/embedding for offline demo and tests.

What this repo contains
- sample/: Python package with seed, process, and aggregate scripts
- .env.example: example env variables to copy
- requirements.txt: pinned dependencies
- tests/: simple unit tests using mocks

Quickstart
1. Create a Python virtualenv and activate it.
2. pip install -r requirements.txt
3. Copy .env.example -> .env and fill DOCUMENTDB_URI and optionally OPENAI_API_KEY
4. Seed data: python -m sample.seed
5. Process documents (score & embed): python -m sample.process
6. Aggregate ranking: python -m sample.aggregate
7. Run tests: pytest -q

Notes
- The sample uses collection `esg_companies` in database `sample_fintech_17` and will not touch other databases.
- The demo creates regular MongoDB indexes automatically (name, schemaVersion). A vector index is required to run server-side $search vector queries; the build verification creates a small HNSW index via the MCP server. The sample's process script stores embedding arrays into `rationale_embedding`.
- This is a demonstration. For production, follow Azure DocumentDB security, authentication, and network best practices.
