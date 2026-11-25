# 1. Prompt review: 13-chronic-disease-risk-predictor

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the high-level goal (Python LlamaIndex agent that embeds a new patient, retrieves similar high-risk profiles from an Azure DocumentDB vector index, reasons and generates a personalised narrative). Many DocumentDB concerns (existing cluster, DB name, vector-index guidance, connection best-practices) are covered by the supplied run-environment notes and installed skills. Missing specifics (Python version, exact embedding/chat model and dims, driver version, collection/schema, app surface, seed/idempotency, tests and README details) will be chosen by the builder as reasonable defaults; these assumptions should be confirmed to avoid divergence.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Create, in code, a cosmosSearch vector index with dimensions matching the embedding model's output — the prompt asks for a vector index, but the embedding model/dimensions are not specified, so the builder must assume a model and dims.
- Embed the new patient's clinical features with the same embedding model used for stored profiles — embedding model/provider not specified; at risk.
- Wire the Azure DocumentDB vector store into the LlamaIndex agent as its agent memory — LlamaIndex integration details (how to plug DocumentDB as retriever/memory) are not specified and no LlamaIndex skill is installed; builder must implement integration from scratch.
- The vector index parameters are chosen for the sample's data size and README explains how to change them — prompt and skills provide guidance but do not supply explicit parameter choices or README instructions; at risk.
- A seed script loads sample data and creates the index and can be run twice without duplicating data — sample-data creation is not specified; idempotency must be implemented by the builder.
- Search results include the similarity score — the prompt requests retrieval but not the response shape; builder may or may not include scores unless told.
- .env.example lists every setting with placeholder values — credential/env requirements are partly specified (DOCUMENTDB_URI) but not exhaustively (LLM keys, model names, etc.); at risk.
- Dependencies are pinned in requirements.txt — prompt doesn't mention pinning; at risk unless builder chooses to pin.
- Unit tests run without a live cluster — prompt doesn't mandate tests or mocking strategy; at risk.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type — run environment provides a pre-provisioned cluster and prompt doesn't request infra-as-code; this requirement is likely not met unless the builder opts to add it.
- Search returns a clear error for an empty query and when the embedding call fails — error-handling behavior is not specified; at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't mention README content explicitly; at risk unless the builder produces it.
- The sample uses the name "Azure DocumentDB" throughout — prompt says 'DocumentDB skill' and run-environment references 'Azure DocumentDB', but explicit README/text consistency is not enforced; at risk unless the builder ensures naming.

## Questions for the prompt author

- Which embedding model and provider should be used (e.g., OpenAI text-embedding-3-small, or another model)? this determines embedding dims and the vector-index dims.
- Do you want a web API (Flask/FastAPI) endpoint (e.g., `/predict` or `/search`) or a CLI demo only? (this changes the app surface)
- What collection name and concrete document schema should I use for stored high-risk profiles (field names for embedding, patient id, features, interventions)?
- Should the sample include a seed script that creates the cosmosSearch index and data, and must it be idempotent?
- Do you require pinned dependency versions in requirements.txt and unit tests that run without a live cluster (e.g., using mongomock)?
- Do you want the demo to return similarity scores alongside retrieved profiles in responses?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | “build a Python LlamaIndex agent with agent memory that stores high-risk patient profile embeddings in a DocumentDB vector index ... For a new patient, embed their clinical features, retrieve the most similar high-risk profiles, and use the agent to reason ... generate a personalised risk narrative with recommended interventions.” | - | - | - |
| Workflow type | specified | no | “a Python LlamaIndex agent with agent memory” → single-agent, LlamaIndex-based | - | - | - |
| Language and runtime | ambiguous | no | “build a Python LlamaIndex agent” (Python chosen but no version specified) | - | Use Python 3.10 (or 3.11) for the sample; ensure compatibility with latest LlamaIndex and pymongo driver. | skill_md says `python` available but gives no explicit version. |
| Driver and version | ambiguous | no | Prompt implies storing profiles in DocumentDB (e.g., via PyMongo) but does not name a driver/version. | documentdb-driver | Use pymongo as the MongoDB driver, pinned to a recent 4.x release compatible with MongoDB 7.0 (e.g. pymongo>=4.4,<5.0). Create a singleton MongoClient per process as recommended by documentdb-driver. | documentdb-driver skill covers client usage patterns but does not mandate a specific pymongo version. |
| Target service and tier | specified | no | skill_md: a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF) is reachable; connection string in DOCUMENTDB_URI; use database `sample_healthcare_13`. | - | - | Run environment (skill_md) explicitly sets the cluster and database to use. |
| Authentication and secrets | specified | no | skill_md: connection string is in the environment variable `DOCUMENTDB_URI`; do not write it to files/logs. | - | - | Builder should also expect to read LLM/API keys from environment variables. |
| Data model | ambiguous | no | Prompt: “store high-risk patient profiles as documents ... with each profile's embedding vector held in a field on its document.” skill_md: use database `sample_healthcare_13`. | documentdb-data-modeling | Create a single collection named `high_risk_profiles` with documents like { patient_id, features: {...}, embedding: [float], risk_label, recommended_interventions }. Use embedding field name `embedding`. | Prompt gives high-level shape but not concrete collection name, field names or allowed feature set. documentdb-data-modeling can advise embed vs reference concerns but not exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a seed script that generates synthetic high-risk profiles (e.g., 100–500 records) and inserts them into `high_risk_profiles`. Synthetic data only (no PHI). | Starter prompt doesn't specify sample-data source, size, or license; local-deployment skill helps with dev patterns but doesn't supply the dataset. |
| Queries and indexes | covered_by_skill | no | “store ... embeddings in a DocumentDB vector index” and “retrieve the most similar ... by running a $search / cosmosSearch aggregation against the Azure DocumentDB vector index” | documentdb-vector-search | Create a cosmosSearch vector index on `embedding` with similarity COS (or L2/IP per choice) and index dimensions matching the chosen embedding model. Use top-k retrieval via $search aggregation. | documentdb-vector-search provides patterns and parameters; the exact index kind (DiskANN/HNSW/IVF) and parameter values will need a concrete choice from the builder. |
| AI components | missing | no | Prompt requires embeddings and an agent (LlamaIndex) but does not name embedding model, dims, or chat model provider. | - | Use an OpenAI embedding model (e.g., text-embedding-3-small, 1536 dims) and expose API keys via environment variables (e.g., OPENAI_API_KEY). Use LlamaIndex with an OpenAI chat model (configurable via env). Document embedding dims (1536) and set the vector index accordingly. | This is a decisive choice that affects index dims and index creation; the prompt leaves it open. |
| App surface | ambiguous | no | Prompt asks for a LlamaIndex agent but does not specify CLI/API/UI or endpoint names. | - | Provide a small Flask (or FastAPI) HTTP API with a `/predict` (or `/search`) JSON endpoint that accepts patient features and returns the generated risk narrative and retrieved profiles + similarity scores. Also include a simple CLI helper for seeding and local testing. | Reference requirements expect a `/search` behavior; the builder should align naming to README. |
| Provisioning and deployment | specified | no | skill_md: a live DocumentDB cluster is already provisioned and reachable; do not provision another cluster unless allowed. | documentdb-azure-deployment | - | The installed documentdb-azure-deployment skill could be used to provide infra code if the author wanted to include it, but the run environment forbids creating another cluster for this sample. |
| Run and test instructions | missing | no | - | - | Include README with commands: pip install -r requirements.txt, cp .env.example .env (fill in keys), python seed.py, python app.py (or uvicorn). Include pytest-based unit tests that mock the DB (mongomock) so they run without a live cluster. | Prompt does not include run/test instructions. |
| Definition of done | missing | no | - | - | Acceptance: live run demonstrates embedding a new patient, retrieving top-k similar high-risk profiles from DocumentDB vector index, agent reasoning and outputting a personalised narrative with recommended interventions; README documents steps; seed script can be run idempotently. | No explicit acceptance criteria in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Use synthetic data only (no PHI), read secrets from env vars, mention that this is a demo not intended for production or real clinical decision-making, and include a short note about privacy and compliance in README. | Given the healthcare theme, builders should explicitly avoid using real PHI. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Use a standard layout: README.md, src/ (app code), seed.py, requirements.txt (pinned), tests/ (pytest), .env.example with placeholders. Use the name "Azure DocumentDB" consistently in docs. | The prompt doesn't demand layout or pinned deps; local-deployment skill gives some guidance for dev parity. |
