# 1. Prompt review: 19-insider-threat-detection-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (Python pipeline to aggregate logs, embed with OpenAI, store vectors in a vector-ivf index, nightly anomaly comparisons) and the run environment (live, vector-capable DocumentDB cluster) via the provided skill_md. Several implementation details are left to the builder (Python version, OpenAI model & env var names, embedding dimensionality, index tuning, exact schemas, seed data and tests). Installed skills cover best practices for vector indexes, driver usage (singleton client), and related DB concerns, so the build can start but will require the builder's sensible defaults for missing specifics.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Authentication and secrets, Data model, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The vector index dimensions must match the embedding model's output — the prompt does not specify the embedding model or dimensions, so the builder must assume a model/dimension (at risk).
- .env.example listing every setting with placeholder values — not requested by the prompt or covered by skills (at risk).
- Index parameter choices and README guidance for scaling the index to larger datasets — prompt asks for vector-ivf but does not require documentation or tuning guidance (at risk).
- A seed script that loads sample data and creates the index idempotently — the prompt assumes logs exist; no seed script is specified (at risk).
- "/search" returns a clear error for an empty query and when the embedding call fails — the prompt doesn't request an API endpoint nor error behaviors (at risk).
- Search results include the similarity score — prompt does not require explicit inclusion of similarity in returned results (at risk).
- Dependencies pinned in requirements.txt — prompt does not say to pin versions (at risk).
- Unit tests that run without a live cluster (mocking DB/OpenAI) — not requested by the prompt (at risk).
- Infrastructure-as-code for the cluster (Azure resource) — skill_md says a cluster is provided and the prompt instructs to use it; the reference asks for IaC which the prompt omits (at risk).
- README covering what the sample shows, prerequisites, setup, run, and clean-up — the prompt does not demand a README (at risk).
- Use the explicit product name 'Azure DocumentDB' throughout the sample — prompt doesn't mandate naming in docs, so the builder might vary terminology (at risk).

## Questions for the prompt author

- Which OpenAI embedding model should be used (model name)? This determines embedding dimensionality and index dimensions.
- Which Python runtime should be targeted (exact version, e.g., 3.10 or 3.11) and which MongoDB driver/version should be pinned (e.g., pymongo 4.x)?
- Do you want the sample to include infrastructure-as-code (Bicep/Terraform) to provision the cluster, or must it deliberately rely on the existing cluster described in skill_md?
- What concrete alerting/output mechanism do you prefer for flagged employees (write to 'alerts' collection, send email, or print a report)? Also, what threshold rule should the sample use to decide 'significant deviation' (e.g., cosine similarity < 0.7 or distance > X)?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB skill'. Multiple related skills exist (vector-search, driver, connection, etc.) — the prompt likely means 'use the DocumentDB skills available'.
- Starter prompt asks to 'embed them using OpenAI' but no installed skill covers OpenAI API usage or which embedding model/dimensions to use; this is not contradicted by skills but is an unaddressed dependency.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "aggregate employee activity logs ... into behavioural feature vectors, embeds them using OpenAI, stores the vectors in a DocumentDB vector-ivf index, and runs a nightly job ... flagging significant deviations." | - | - | Business problem, user, and what the sample demonstrates are clearly stated. |
| Workflow type | specified | no | "build a Python pipeline ... and runs a nightly job" — a standalone pipeline / scheduled job (no agent framework specified). | - | - | This implies a no-agent app (a scheduled Python process). |
| Language and runtime | ambiguous | no | "Python pipeline" | documentdb-local-deployment | Use Python 3.11 (or latest 3.x commonly available on developer machines). Provide a venv and instructions using python/pip as described in skill_md. | Prompt and skill_md say 'python' is available but no explicit version is given; the builder will pick a recent stable 3.x. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official pymongo driver (pymongo >= 4.3, e.g. 4.5) and implement a process-wide singleton MongoClient per documentdb-driver guidance. | The installed skill covers the singleton pattern but the starter prompt doesn't state which driver/version to pin. |
| Target service and tier | specified | no | - | documentdb-vector-search | - | skill_md (run environment) explicitly states a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0) is reachable and must be used (database sample_banking_19). |
| Authentication and secrets | ambiguous | no | "Using the DocumentDB skill" and "embeds them using OpenAI" | documentdb-mcp-setup | DATABASE: read connection string from DOCUMENTDB_URI env var (as in skill_md). OPENAI: read API key from OPENAI_API_KEY env var and model from OPENAI_EMBEDDING_MODEL env var. No credentials are written to repo; supply .env.example. | DB connection env var is specified in skill_md; OpenAI keys/vars are not specified in the prompt or skills. |
| Data model | ambiguous | no | "aggregates employee activity logs ... into one behavioural feature vector per employee" and "known anomaly profiles are held as documents" | documentdb-data-modeling | Collections: use database 'sample_banking_19' with collections named e.g. 'activity_logs' (raw events), 'employee_vectors' (one doc per employee embedding + metadata), 'anomaly_profiles' (profile embeddings), and 'alerts'. Feature vector doc includes employee_id, window_start/end, numeric feature array, embedding, model name and dimension. | Prompt defines high-level shapes but not exact document fields, collection names, or shard keys; use doc-modeling skill for best practices. |
| Sample data | missing | no | - | - | Provide an idempotent seed script that creates synthetic employee activity logs for a small number (e.g. 50–200) of employees and inserts them into 'activity_logs'. The script must be safe to re-run without duplicate documents (use upserts or check by unique keys). | Starter prompt assumes logs exist in the cluster; it does not provide sample-data source, size, or a seed script. |
| Queries and indexes | covered_by_skill | no | "stores the vectors in a DocumentDB vector-ivf index" | documentdb-vector-search | Builder will create a cosmosSearch index of kind 'vector-ivf' on the embedding field. Embedding dimensionality must match the OpenAI model (assume 1536 unless model chosen differs). Similarity will be COS by default (or as chosen in env). Index parameters (nlist, lBuild/lSearch or maxDegree) will use sample-sized defaults per vector-search guidance and be documented. | The prompt requests vector-ivf; vector-search skill covers index creation and tuning but the prompt doesn't specify dimensions or exact index params. |
| AI components | missing | no | "embeds them using OpenAI" | - | Use OpenAI embeddings API via the official openai Python SDK (or HTTP client); default to an embedding model such as text-embedding-3-small with 1536 dims (or a modern embedding model documented in README). Calls are made from the pipeline code when creating/updating vectors. OPENAI_API_KEY read from env. | Prompt names OpenAI but does not pick a model, API package, or error-handling approach; no installed skill covers OpenAI API specifics. |
| App surface | ambiguous | no | "build a Python pipeline ... and runs a nightly job" | - | Implement as a CLI-driven Python project with commands: 'seed' (load sample data), 'ingest' (aggregate and embed recent activity), 'run-nightly' (process all employees), and 'search' (ad-hoc run). Nightly scheduling is demonstrated via a cron example (e.g. 2:00 AM) or a simple scheduler loop; no full web UI is required for the sample. | Prompt requests a nightly job but does not ask for a web API; gallery samples often provide CLI/README-run scripts. |
| Provisioning and deployment | specified | no | - | documentdb-azure-deployment | Use the existing, reachable vector-capable cluster described in skill_md; do not provision a new cluster during the sample run. | skill_md explicitly says a cluster already exists and should be used; az is signed in but the sample should not create another cluster. |
| Run and test instructions | missing | no | - | - | Provide README commands: setup venv, pip install -r requirements.txt, export env vars from .env, run 'python -m sample.seed' to seed, 'python -m sample.ingest' to run one ingestion, 'python -m sample.run_nightly' to simulate nightly run. Include unit tests that mock DB and OpenAI and a tests/README entry. | Prompt and skill_md describe environment but don't include concrete run/test commands or a test plan. |
| Definition of done | missing | no | - | - | Minimum acceptance: seed script inserts sample logs; code runs to aggregate per-employee feature vectors; embeddings are produced via OpenAI and persisted; vector-ivf index is created; nightly job computes centroid comparisons and performs a cosmosSearch against anomaly profiles; alerts are written for flagged employees; README documents the steps and results. | Prompt describes the goal but does not give a testable acceptance checklist. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep sample data synthetic to avoid PII, keep dataset small to limit vector index sizing/cost, do not attempt production-scale HA or DR configuration. Document cost and non-goals in README. | Prompt does not define cost limits, privacy requirements, or non-goals; security skill can advise but doesn't specify sample constraints. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Follow standard layout: src/, tests/, docs/README.md, requirements.txt with pinned versions, .env.example with placeholders, and LICENSE. Use 'Azure DocumentDB' in docs and sample text. | Starter prompt doesn't prescribe layout or documentation requirements. |
