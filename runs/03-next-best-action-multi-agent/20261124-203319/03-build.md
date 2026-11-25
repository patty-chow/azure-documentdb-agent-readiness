# 3. Build report: 03-next-best-action-multi-agent

**Status: completed**

Built a Python LangChain-style Next-Best-Action (NBA) multi-agent sample that connects to an existing Azure DocumentDB (Mongo-compatible) cluster, seeds synthetic customer data, runs three deterministic agents (propensity, channel, timing), orchestrates their outputs into an NBA recommendation, and writes the recommendation to sample_customer_360_03.nba_recommendations. Dependencies were installed, the seed script ran successfully, the demo orchestrator produced and wrote NBA documents, and unit tests passed. Vector-index creation (cosmosSearch vector-diskann) via the documentdb MCP create-index tool failed and therefore was not created programmatically; instructions for creating that vector index are included in the repository README/.env.example and documented below.

## How to run

1) Create & activate a Python virtualenv (python 3.10+). 2) Install deps: pip install -r requirements.txt. 3) Set required env vars: DOCUMENTDB_URI (required), optionally OPENAI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIMS, LLM_MODEL. A .env.example is provided. 4) Seed the DB: python seed.py (idempotent). 5) Run demo CLI to create an NBA for cust_001: python main.py --demo. 6) Or start the HTTP demo: uvicorn main:app --reload and GET /nba?customer_id=<id>. 7) Run tests: pytest.

## Verified by running

- pip install -r requirements.txt: completed (dependencies present / installed).
- python seed.py: completed (seed script printed 'Seeding complete').
- python main.py --demo: completed (demo produced and wrote NBA recommendation; sample output printed and contained an _id).
- pytest -q: completed (1 passed).
- documentdb_list_databases(db_name=sample_customer_360_03): returned collections and counts: interactions (count 496), preferences (count 20), nba_recommendations (count 2).
- documentdb_list_indexes(db_name=sample_customer_360_03, collection=interactions): returned indexes: _id_, customer_id_1, customer_id_1_timestamp_-1.
- documentdb_list_indexes(db_name=sample_customer_360_03, collection=preferences): returned indexes: _id_, customer_id_1 (unique).
- documentdb_list_indexes(db_name=sample_customer_360_03, collection=nba_recommendations): returned indexes: _id_.
- documentdb_find_documents(db_name=sample_customer_360_03, collection=nba_recommendations): returned 2 NBA documents (sample entries inserted by the demo).

## Not verified

- Programmatic creation of a cosmosSearch vector-diskann index via the documentdb_create_index MCP tool: attempted but the MCP call failed with 'Error: Function failed.' (tool failure). As a result the vector index on interactions.embedding was NOT created. See 'Open Issues' for next steps.
- Any LLM/embedding runtime behavior that requires an OPENAI_API_KEY (text embeddings + LangChain LLM calls) was not executed in this verification run because the sample is implemented to run deterministically without API keys by default. If you set OPENAI_API_KEY, embeddings/LLM behavior should be tested by the user.

## Open issues

- Vector index creation (cosmosSearch vector-diskann) via the MCP server failed. Manual or alternative programmatic creation is required. Suggested index creation command (mongo shell / pymongo) to run against the cluster (replace dims if you change embedding model):

db.interactions.createIndex(
  { embedding: 'cosmosSearch' },
  {
    name: 'interactions_embedding_diskann',
    cosmosSearchOptions: {
      kind: 'vector-diskann',
      dimensions: 1536,
      similarity: 'COS',
      maxDegree: 32,
      lBuild: 50
    }
  }
);

If that fails, use the Azure DocumentDB portal/CLI instructions in the documentdb-vector-search skill to create a cosmosSearch index. This must be done before vector queries will work correctly.
- Embedding and LLM behavior is optional in this sample and disabled by default. To enable semantic/vector features you must set OPENAI_API_KEY (or another embeddings provider) and ensure EMBEDDING_MODEL and EMBEDDING_DIMS in the environment match the model you choose. Changing embedding model dimensions requires rebuilding the vector index with matching dimensions.
- The MCP vector-index creation call failed with an opaque 'Function failed.' error. If you need automated vector-index creation in CI, retrying with additional diagnostic info from the MCP server or using the cluster's admin tooling/mongosh may be required.
- This sample uses deterministic heuristics for agents by default to ensure it runs in environments without LLM or embedding API keys. If you intend to use LLM-powered agents (LangChain), update src/agents.py to call LangChain and the LLM of your choice and add network/mocking strategies for tests as appropriate.

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `seed.py`
- `main.py`
- `src/db.py`
- `src/agents.py`
- `src/orchestrator.py`
- `tests/test_orchestrator.py`

