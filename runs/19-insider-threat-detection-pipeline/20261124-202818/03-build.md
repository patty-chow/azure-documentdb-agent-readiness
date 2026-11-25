# 3. Build report: 19-insider-threat-detection-pipeline

**Status: partial**

Built a small Python sample pipeline that seeds synthetic employee activity logs into an existing Azure DocumentDB cluster, aggregates per-employee behavioural features, attempts to embed them via OpenAI, stores feature documents in a collection and creates a DocumentDB vector-ivf index. Verified unit tests, seeding, index creation, ingestion run (embedding attempts), and nightly-run logic. Embeddings did not complete during verification because OPENAI_API_KEY was not set in the environment; the code handles that gracefully and still persists feature documents (with empty embedding).

## How to run

1) Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate

2) Install dependencies:
   pip install -r requirements.txt

3) Provide secrets (either export env vars or copy .env.example to .env and edit):
   - DOCUMENTDB_URI  (mongodb+srv connection string for the existing DocumentDB cluster)
   - OPENAI_API_KEY  (optional for full embedding behavior)
   - OPENAI_EMBEDDING_MODEL (optional, default text-embedding-3-small)
   - ANOMALY_COSINE_THRESHOLD (optional, default 0.7)
   - DATABASE_NAME (optional, default sample_banking_19)

4) Seed synthetic data (idempotent):
   python -c "import sys; sys.path.insert(0,'src'); import seed as s; s.seed()"

5) Create the vector index (uses the MongoDB runCommand createIndexes with cosmosSearchOptions):
   python -c "import sys; sys.path.insert(0,'src'); from sample.create_indexes import create_vector_index; create_vector_index()"

6) Run a single ingestion (aggregates recent 7-day features, requests embeddings and upserts employee_vectors):
   python -c "import sys; sys.path.insert(0,'src'); from sample.ingest import ingest_once; ingest_once()"

   If OPENAI_API_KEY is unset, embeddings will fail and empty embeddings will be stored; provide OPENAI_API_KEY to get real embeddings.

7) Simulate the nightly anomaly detection run:
   python -c "import sys; sys.path.insert(0,'src'); from sample.run_nightly import run_nightly_once; run_nightly_once()"

8) Run tests:
   pytest -q

Notes on scheduling: the sample demonstrates a CLI-run nightly job (run_nightly). For production scheduling, run this module via a cron job or Azure scheduler / Function; README includes a cron example.

## Verified by running

- pip install -r requirements.txt: success
- pytest: 3 passed, 1 warning
- Seed script (python seed.seed): inserted 5324 activity_logs (60 employees * ~days distribution)
- Created vector index on sample_banking_19.employee_vectors using createIndexes (cosmosSearch vector-ivf): command returned ok
- Ingest run: aggregated recent activity and upserted 60 employee_vectors; OpenAI embedding attempts were attempted but failed due to missing OPENAI_API_KEY (embedding code caught the error and persisted empty embeddings)
- Nightly-run simulation: executed run_nightly logic (no alerts created in this run)
- Verified indexes via documentdb MCP server: employee_vectors has _id_ and embedding_vector_ivf (kind: vector-ivf, dimensions:1536, similarity:COS)

## Not verified

- Production OpenAI embedding calls: Could not complete during verification because OPENAI_API_KEY was not present in the environment. The code path for calling OpenAI embeddings exists and was executed but raised 'OPENAI_API_KEY not set', so embeddings were not produced. To verify: set OPENAI_API_KEY and re-run 'ingest'.
- Vector KNN search using DocumentDB $search (cosmosSearch) was not demonstrated via server-side $search aggregation during verification. The sample includes a local KNN helper (knn_local) and shows how to create a vector index; a $search-based KNN example and its explain() would require additional demo queries or mongosh usage.
- End-to-end detection sensitivity: threshold selection (ANOMALY_COSINE_THRESHOLD=0.7) is illustrative and was not validated against labeled anomalies. Tuning would require labeled data and further experiments.

## Open issues

- OpenAI API key was not set in the verification environment, so embeddings were not generated. Re-run ingestion with OPENAI_API_KEY set to create real embeddings.
- The sample demonstrates index creation via the MongoDB runCommand approach; if your cluster or access method prefers the documentdb MCP server for index creation, adapt the create_indexes.py or use the MCP 'create index' call documented in the skills.
- Anomaly detection threshold (cosine < 0.7) is a sample choice. For production, choose a threshold empirically using labeled data or use a statistical detection method (z-scores, Mahalanobis) and consider per-employee baselines or minimum history requirements.
- The project uses a textified numeric feature vector for embeddings (stringified features). For higher-fidelity semantic embeddings consider embedding richer textual descriptions of behaviour or using mixed lexical+vector signals.
- Scheduling is left as a cron example / CLI; users should choose robust scheduling (Azure Functions, Container Instances, or orchestration) in production.

## Files

- `requirements.txt`
- `.env.example`
- `README.md`
- `pytest.ini`
- `src/sample/__init__.py`
- `src/sample/config.py`
- `src/sample/db.py`
- `src/sample/utils.py`
- `src/sample/embedder.py`
- `src/sample/ingest.py`
- `src/sample/create_indexes.py`
- `src/sample/run_nightly.py`
- `src/sample/search.py`
- `src/seed.py`
- `tests/test_utils.py`
- `tests/test_ingest.py`

