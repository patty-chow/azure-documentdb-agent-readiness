# 1. Prompt review: 06-symptom-triage-chatbot-rag

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the goal (a Python LangChain RAG triage chatbot), the retrieval target (DocumentDB vector index), and the key safety constraint (always recommend professional consultation / never diagnose). The provided run-environment notes and installed DocumentDB skills cover most infra / vector-indexing and driver best-practices, but important choices are left to the builder (Python version, embedding & chat models, exact schema, app surface, seed data and test strategy). These will be filled by skills where possible and otherwise by the builder's defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Queries and indexes, Repository conventions |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, App surface, Constraints and non-goals |
| Missing: builder will guess | 4: Sample data, AI components, Run and test instructions, Definition of done |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables: model credentials not mentioned in prompt or skill_md (DOCUMENTDB_URI is present) — at risk because the embedding/chat provider credentials and their env var names are unspecified.
- .env.example lists every setting with placeholder values — at risk because prompt asks to 'use' but doesn't enumerate required env vars; builder must decide which vars to include.
- The vector index dimensions match the embedding model's output — at risk because embedding model/dimensions aren't specified in the prompt; builder must choose a model and ensure dimensions match.
- Vector index parameters chosen for sample's data size, and README says how to change them — at risk because index subtype/parameters are not chosen in the prompt; vector-search skill gives guidance but the sample must document tuning.
- Seed script loads sample data and can be run twice without duplicating data — at risk because prompt doesn't require or describe an idempotent seed script; local-deployment skill suggests best practice but doesn't supply the seed content.
- /search returns a clear error for an empty query and when the embedding call fails — at risk because error handling is not specified in the prompt.
- Search results include the similarity score — at risk because prompt only asks to retrieve most relevant sections; including the score must be implemented explicitly.
- Dependencies are pinned in requirements.txt — at risk because versions are not provided/required in the prompt; builder will need to pick and pin versions.
- Unit tests run without a live cluster — at risk because the prompt does not mandate test strategies (mocks/fakes) and the run environment assumes a live cluster is available for verification.
- Infrastructure for the cluster is provided as code using Azure DocumentDB resource type — at risk/likely omitted because skill_md forbids provisioning another cluster for this run and the prompt doesn't ask for infra-as-code.

## Questions for the prompt author

- Which embedding model and provider should the sample use (e.g., OpenAI text-embedding-3-small)? the embedding model determines vector dimensions and must be chosen before index creation.
- Which chat / LLM model should be used for generation, and must it be a hosted provider (OpenAI) or local model? This affects runtime and credentials.
- Do you want an HTTP API (FastAPI) endpoint (/search or /triage), a CLI demo, or a small web UI as the sample surface?
- Should the repository include infrastructure-as-code for the cluster (Bicep/Terraform), or must the sample avoid provisioning and only use the provided cluster?
- Are there any dataset licensing or PHI constraints for the sample data, and do you prefer synthetic/manual guideline excerpts vs a curated public source?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain RAG chatbot that indexes clinical triage guidelines in a DocumentDB vector index... enforce safety guardrails (always recommend professional consultation, never diagnose)" | - | - | Goal, user problem and safety non-goals are expressed clearly. |
| Workflow type | specified | no | "Python LangChain RAG chatbot" (single RAG chain/agent) | - | - | Single-agent RAG workflow implied. |
| Language and runtime | ambiguous | no | "Python" and LangChain | - | Builder will target a modern Python 3.x runtime (e.g., 3.10 or 3.11). Use virtualenv and 'python' / 'pip' from the run environment. | Prompt doesn't name an explicit Python version; skill_md only says 'python' is available on the developer machine. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the Python MongoDB driver (PyMongo) and a current stable release compatible with chosen Python (e.g., pymongo >=4.x). Follow the documentdb-driver guidance to create a single process-wide MongoClient. | Skills provide best-practice usage (singleton MongoClient) but do not mandate a specific driver version. |
| Target service and tier | specified | no | From skill_md: a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable and DOCUMENTDB_URI is set. | - | - | Run-environment notes supply the exact live cluster details the sample must use. |
| Authentication and secrets | specified | no | From skill_md: connection string is in environment variable DOCUMENTDB_URI; do not write its value to files/logs; use a config file or .env.example with a placeholder. | - | - | Secrets expected to be read from env; skill_md enforces not leaking the URI. |
| Data model | ambiguous | no | "indexes clinical triage guidelines in a DocumentDB vector index" | documentdb-data-modeling | Builder will create a single database 'sample_healthcare_06' (per skill_md) and a collection named 'guidelines' (or similar) where documents have fields: _id, section_id, title, text/content, embedding (array of floats), metadata (source, section, keywords, documented_urgency), model_name and dimensions. | Prompt doesn't specify collection name, exact fields, or whether metadata/urgency tags exist; documentdb-data-modeling can guide shape decisions but doesn't set names. |
| Sample data | missing | no | - | - | Include a small synthetic/hand-curated corpus of triage guideline sections (e.g., 20–100 short sections authored for the sample, permissively licensed or original text). Provide an idempotent seed script (seed.py) that upserts documents and embeddings. | Prompt requests indexing clinical triage guidelines but does not say where the documents come from or their licensing/size. |
| Queries and indexes | covered_by_skill | no | "DocumentDB vector index" and "retrieve the most relevant guideline sections..." | documentdb-vector-search | Use a cosmosSearch vector index (DiskANN/HNSW/IVF chosen per dataset size), similarity 'COS' by default and a $search / cosmosSearch knn query with k=5 unless tuned; store embedding field and dimensions together with each document. | The vector-index creation and $search retrieval are addressed by the vector-search skill; the builder must still choose index subtype and parameters based on data size. |
| AI components | missing | no | - | - | Builder will pick a commonly available embedding provider and LLM (for example OpenAI embeddings such as text-embedding-3-small and an OpenAI chat model via LangChain). The vector dims must be set to the chosen embedding output (e.g., 1536 for common OpenAI embeddings). Credentials will be read from env vars (e.g., OPENAI_API_KEY). | Prompt doesn't name the embedding model, chat model, provider, or dimensions; these choices affect index dimensions and must be decided before index creation. |
| App surface | ambiguous | no | "LangChain RAG chatbot" | - | Provide a minimal HTTP API (FastAPI) exposing a /search (or /triage) POST endpoint that accepts free-text symptom descriptions and returns a structured JSON response (or Pydantic model) including advice and urgency level. Include a CLI script for seeding and a simple demo client. | Starter prompt does not mandate CLI vs API vs UI; many LangChain samples default to a small API. |
| Provisioning and deployment | specified | no | From skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | No new cloud cluster will be provisioned; sample will create collections/indexes on the existing cluster using the provided DOCUMENTDB_URI. | The environment notes explicitly constrain provisioning. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | README will instruct: create virtualenv, pip install -r requirements.txt, create .env from .env.example, run python seed.py, start server with 'uvicorn app:app --reload', and run tests via pytest. The builder will include expected outputs for a successful run. | The prompt and skills don't include explicit run/test commands or test expectations; local-deployment skill offers best-practices for env-driven config. |
| Definition of done | missing | no | - | - | Accept when: seed script runs idempotently, vector index created with correct dimensions, server accepts symptom text and returns structured JSON with retrieved context, triage advice, urgency level, safety language (recommend professional consultation, no diagnosis), and examples in README demonstrating the behavior. | Prompt lists functionality but does not provide explicit acceptance criteria or tests. |
| Constraints and non-goals | ambiguous | no | "always recommend professional consultation, never diagnose" (safety guardrails) | - | Enforce guardrails via prompt-template and answer post-processing; avoid storing or logging PHI; clearly state non-goals (no automated diagnoses, not for emergency use). | Safety guardrails are explicit; other constraints (cost, PHI handling, licences) are not specified. |
| Repository conventions | covered_by_skill | no | skill_md guidance: "use a config file or `.env.example` with a placeholder, as the prompt asks." | documentdb-local-deployment | Include .env.example (placeholders for DOCUMENTDB_URI, OPENAI_API_KEY, etc.), requirements.txt with pinned deps, seed/seed.py, app/ package, README.md, and tests/pytest layout. | Local-deployment skill and skill_md recommend env-driven configuration and seed-script patterns; README and pinned deps still need to be created by the builder. |
