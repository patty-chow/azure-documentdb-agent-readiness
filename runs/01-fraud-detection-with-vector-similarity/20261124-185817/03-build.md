# 3. Build report: 01-fraud-detection-with-vector-similarity

**Status: partial**

I built a small Python sample app that demonstrates using Azure DocumentDB as a vector store for fraud-detection similarity matching. The repository files (README, .env.example, requirements.txt, docdb client, embedding helpers, an idempotent seed script, and a demo agent script) were created. I logged the key design decisions (language, driver, embedding model, index type, auth approach, LangChain explanation strategy) as required. I attempted programmatic verification against the provided DocumentDB MCP server: I successfully listed databases but attempts to create the vector index and insert sample documents via the MCP tools failed (function errors). Because the live-cluster data-plane steps (index creation, document inserts, search query) could not be completed in this session, the sample is code-complete and ready to run on a machine where DOCUMENTDB_URI is configured; the README explains how to run and verify locally. See files_created and verification_done / not_verified for details.

## How to run

1) Create and activate a Python 3.10+ virtualenv:
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows

2) Install dependencies:
   pip install -r requirements.txt

3) Copy .env.example to .env and set DOCUMENTDB_URI to your cluster's connection string. Optionally set OPENAI_API_KEY to enable LLM-backed explanations.

4) Seed the database with sample fraud patterns (computes embeddings locally and upserts by pattern_name):
   python seed.py

   - The seed script writes to database `sample_fintech_01`, collection `fraud_patterns`.
   - It uses the sentence-transformers model all-MiniLM-L6-v2 (384 dims). Ensure your environment can install and run that model (this may pull in torch). If you prefer not to install the local model, you may modify seed.py to provide precomputed vectors.

5) Run the demo agent on a transaction text to compute a fraud risk score and explanation:
   python run_agent.py "suspicious transaction: high amount, new payee, rapid sequence"

6) Cleanup: remove inserted docs via your preferred MongoDB/DocumentDB admin tool, or drop the sample database `sample_fintech_01` if appropriate.

Notes:
- The sample expects DOCUMENTDB_URI to be set to the cluster's connection string. Do NOT commit secrets into repository files.
- The repository uses a local sentence-transformers model by default to avoid requiring cloud API keys. If you want to use OpenAI/other embeddings instead, replace embeddings.py accordingly and update requirements.


## Verified by running

- Created repository files: README.md, .env.example, requirements.txt, docdb_client.py, embeddings.py, seed.py, run_agent.py (file creation succeeded).
- Logged design decisions via audit-log calls (language, driver, embedding model, index type, auth approach, LangChain explanation strategy).
- documentdb_list_databases: call returned existing databases (example returned 'sample_retail_20'), proving the MCP server is reachable from this environment.

## Not verified

- Index creation: attempted to create a vector-ivf index (kind=vector-ivf, dimensions=384, numLists=1) on sample_fintech_01.fraud_patterns via the MCP tool but the call failed with a function error. Reason: MCP tool returned an error when calling documentdb_create_index in this session. (I attempted the createIndexes call via the MCP tool; see log entries.)
- Data insertion: attempted to insert sample documents into sample_fintech_01.fraud_patterns via the MCP tool but the call failed with a function error. Because the insertion calls failed, the collection and its documents were not confirmed present via the MCP server.
- Vector search verification: could not run an end-to-end $search (cosmosSearch) aggregation against the live collection because index creation and/or data insertion via MCP failed; therefore I did not observe search results or similarity scores from the live cluster in this session.
- Local runtime verification (pip install and running seed.py / run_agent.py): not executed here because DOCUMENTDB_URI is not guaranteed to be set in this run environment and because I used the MCP path for verification attempts. To fully verify locally, follow the README: set DOCUMENTDB_URI, pip install -r requirements.txt, then run seed.py and run_agent.py.

## Open issues

- MCP tool errors when attempting to create indexes and insert documents. The MCP server is reachable for listing databases (documentdb_list_databases succeeded) but the create_index/insert_documents calls returned function errors in this session. Possible causes: missing connection_profile selection, temporary MCP tool backend error, or privileges. The user should re-run the verification steps locally with DOCUMENTDB_URI set (seed.py) or retry the MCP calls in an environment where the MCP tools are fully connected.
- Installing sentence-transformers will pull a large dependency (torch); the user may need time or platform-specific wheels. If the environment cannot install torch, seed.py can be adapted to use precomputed vectors or an alternate lightweight embedding provider.
- The sample's run_agent.py provides a deterministic, template-based explanation by default. If the user wants richer LLM-generated explanations, they can set OPENAI_API_KEY and update run_agent.py to call an LLM (the code includes a note).
- Index tuning and production hardening: the sample uses vector-ivf with numLists=1 for simplicity. For production workloads choose an index type and tuned parameters appropriate to dataset size (references in the README and the DocumentDB vector-search docs).

## Files

- `README.md`
- `.env.example`
- `requirements.txt`
- `docdb_client.py`
- `embeddings.py`
- `seed.py`
- `run_agent.py`

