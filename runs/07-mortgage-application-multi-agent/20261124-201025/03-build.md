# 3. Build report: 07-mortgage-application-multi-agent

**Status: completed**

Created a small Node.js (Express) sample that implements a LangChain-style multi-agent mortgage pipeline against an existing Azure DocumentDB cluster. The app reads applications from the `applications` collection, runs an underwriting agent, a compliance agent and a comms agent, and writes the result to a `decisions` collection. The sample reads DOCUMENTDB_URI and LLM credentials from environment variables, includes an idempotent seed script, unit test(s) that mock DB/LLM, and a README with setup/run instructions. I verified installation, unit tests, seeding, a pipeline run for a sample application and inspected the cluster via the documentdb MCP tools.

## How to run

1. Copy .env.example -> .env and fill DOCUMENTDB_URI (and OPENAI_API_KEY if you want real LLM calls).
2. npm install
3. npm run seed          # idempotent: inserts/updates sample applications and creates demo indexes
4. npm start             # starts the Express demo server (POST /seed, POST /run/:applicationId, GET /applications/:id)
   OR run once: node src/run_pipeline.js <applicationId>
5. Use the documentdb MCP server tools or Mongo client to inspect the `sample_banking_07` database and the `applications` and `decisions` collections.

Notes: The agents will use OpenAI (model from OPENAI_MODEL) when OPENAI_API_KEY is set; otherwise deterministic rule-based fallbacks are used so the sample runs without LLM credentials.

## Verified by running

- npm install: completed (node/npm packages installed successfully).
- npm test: 1 passed (test/pipeline.test.js passed; Jest test uses mocked DB/LLM).
- npm run seed: script executed successfully and upserted 3 sample applications into database 'sample_banking_07'.
- documentdb_list_databases (MCP): returned database 'sample_banking_07' with collection 'applications' (count 3).
- documentdb_find_documents (MCP): fetched 3 inserted application documents (app-001, app-002, app-003).
- node src/run_pipeline.js app-001: ran pipeline end-to-end using deterministic agents and wrote a decisions document for applicationId app-001.
- documentdb_find_documents (MCP): fetched the decision document for app-001 from the 'decisions' collection.

## Not verified

- LLM-driven agent outputs against a real LLM provider were NOT executed because OPENAI_API_KEY was not provided in the environment. The code paths fallback to deterministic logic and are unit-tested with mocks. (Reason: no LLM credentials available in the environment).
- Automated creation of a vector index was not executed; vector-index creation was left as a manual/documented step in README because the exact index algorithm/parameters depend on embedding model choice and cluster capabilities and the sample should not assume or change cluster-level vector configuration without explicit consent.
- Hybrid search or DocumentDB 'cosmosSearch' vector operations were not demonstrated against a real embedding vector store because we did not create vector indexes nor compute/store embeddings (requires embedding model credentials and chosen index configuration).

## Open issues

- If you want LLM-powered agent outputs (semantic justifications, more natural letters), set OPENAI_API_KEY and OPENAI_MODEL in .env and re-run the pipeline. The code will attempt OpenAI calls when credentials are present.
- If you want to demonstrate vector search (embedding + vector index), choose an embedding model and dimension, create the vector index using the cluster's supported kind (HNSW/IVF/DiskANN) and store embeddings for documents. The README notes this as a manual step.
- This sample uses simple deterministic underwriting/compliance logic for offline/demo runs. For production or richer examples, replace or augment the rule-based logic with LLM prompts or a proper rules engine and add more robust error handling/observability.

## Files

- `package.json`
- `.env.example`
- `.gitignore`
- `README.md`
- `src/db.js`
- `src/index.js`
- `src/seed.js`
- `src/pipeline.js`
- `src/run_pipeline.js`
- `src/agents/underwriting.js`
- `src/agents/compliance.js`
- `src/agents/comms.js`
- `test/pipeline.test.js`

