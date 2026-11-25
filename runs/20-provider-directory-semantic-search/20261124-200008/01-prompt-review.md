# 1. Prompt review: 20-provider-directory-semantic-search

**Verdict: sufficient_with_assumptions**

The prompt clearly states the main goal: a Python LlamaIndex service that stores provider profiles with embedded vectors in Azure DocumentDB and exposes /find-provider to run vector search. Many implementation details (index parameters, embedding model/provider, env var names for model creds, tests, README, seed script idempotency) are not specified and will be chosen by the builder or filled by installed skills (notably vector-search and driver best-practices).

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Target service and tier, Data model, App surface |
| Covered by a skill | 2: Driver and version, Queries and indexes |
| Ambiguous: builder will guess | 5: Workflow type, Language and runtime, Authentication and secrets, AI components, Provisioning and deployment |
| Missing: builder will guess | 5: Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The vector index dimensions match the embedding model's output — embedding model not specified in prompt, so builder may pick one and must ensure index dimensions match.
- The connection string and model credentials come from environment variables; model credentials env var is not specified in the prompt or skill_md (only DOCUMENTDB_URI is specified).
- .env.example lists every setting with placeholder values — prompt does not request or specify .env.example contents.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — prompt does not require parameter choices or README guidance.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the prompt asks to store data but does not require an idempotent seed script.
- /search returns a clear error for an empty query and when the embedding call fails — error-handling behavior is not specified.
- Search results include the similarity score — prompt specifies ranked results but not whether to surface numeric scores.
- Dependencies are pinned in requirements.txt — prompt does not instruct to pin versions.
- Unit tests run without a live cluster — tests are not specified and mocking of the cluster is not requested.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt does not ask to include IaC; skill exists but run env says use live cluster.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt does not mandate a README with these sections.

## Questions for the prompt author

- Which embedding model and provider should the sample use (OpenAI text-embedding-3-small, text-embedding-3-large, or another model)? This determines vector dimensions and index settings.
- Do you want the sample to include infrastructure-as-code (Bicep/Terraform) to provision an Azure DocumentDB cluster, or should it rely exclusively on the existing cluster described in the run environment?
- What env var name should be used for the embedding/LLM provider credentials (OPENAI_API_KEY, LLAMA_API_KEY, or something else)?
- Should the HTTP API be POST /find-provider with JSON body or GET /find-provider?q=... ? Any response format preferences (fields to return, include similarity score numeric format)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | Build a Python LlamaIndex service that stores provider profiles ... Expose a /find-provider endpoint ... returns ranked provider matches using vector search. | - | - | Business problem, user and demonstrated DB capability are clearly stated. |
| Workflow type | ambiguous | no | Using the DocumentDB skill | - | Builder will implement this as a single-agent sample: a single Python service (no multi-agent orchestration) that uses installed DocumentDB skills for guidance. | Prompt does not state whether multi-agent/orchestration frameworks should be used. |
| Language and runtime | ambiguous | no | Using the DocumentDB skill, build a Python LlamaIndex service | - | Use modern Python 3.10 or 3.11 (assume 3.11) and a virtualenv; 'python' and 'pip' resolve to that environment per skill_md. | Prompt specifies Python but not the exact interpreter version or packaging/tooling choices. |
| Driver and version | covered_by_skill | no | store ... as DocumentDB documents ... written through the Python driver (e.g. PyMongo). | documentdb-driver | Use the current stable PyMongo for the Python runtime (e.g., pymongo 4.x) and implement a process-wide singleton MongoClient per documentdb-driver guidance. | documentdb-driver skill documents singleton client and best practices; it does not pin a specific PyMongo patch version, so the builder will pick a reasonable recent 4.x version and pin it in requirements.txt. |
| Target service and tier | specified | no | Using the DocumentDB skill ... | - | Run against the existing vector-capable Azure DocumentDB cluster described in skill_md (M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF available), reading connection string from DOCUMENTDB_URI. | skill_md run environment explicitly describes the live cluster the sample must use. |
| Authentication and secrets | ambiguous | no | Using the DocumentDB skill ... | documentdb-mcp-setup | Connection string for DocumentDB comes from env var DOCUMENTDB_URI (per skill_md). Embedding/LLM provider credentials are not specified — builder will assume OpenAI-style API key in OPENAI_API_KEY (or instruct user to set OPENAI_API_KEY) unless the author specifies another provider. | DocumentDB connection env var is provided in skill_md; embedding model credentials are not specified anywhere and must be assumed or requested. |
| Data model | specified | no | stores provider profiles (specialty, languages, accepted insurance, bio) as DocumentDB documents with embedded vectors | documentdb-data-modeling | Use a single collection in database 'sample_healthcare_20' (as required by skill_md) where each document contains fields: name/id, specialty, languages (array), accepted_insurance (array), bio (text), embedding (vector array), plus metadata like model name and dimensions. | Prompt plus skill_md give the database name and fields to store; documentdb-data-modeling skill will guide embedding storage and document size considerations. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small, synthetic sample dataset (e.g., 10–50 provider records) included in the repo as a JSON or CSV seed file. Seed script included that inserts these providers; license will be a permissive sample-data statement in the README. | Prompt doesn't specify data source, size or license; local-deployment skill covers patterns for sample data management but not dataset content. |
| Queries and indexes | covered_by_skill | no | returns ranked provider matches using vector search | documentdb-vector-search | Builder will create a cosmosSearch vector index (likely vector-diskann or vector-hnsw/ivf depending on sample size) on the embedding field and use $search with cosmosSearch to run K-NN similarity queries. Index details (dimensions, similarity metric COS/L2/IP) will be chosen to match the embedding model (assumed later). | documentdb-vector-search skill provides guidance on index type choices and query patterns; it does not set the embedding model dimensions for you. |
| AI components | ambiguous | no | Python LlamaIndex service ... use LlamaIndex to produce the embedding vectors | - | Use LlamaIndex with an OpenAI embedding model (e.g., text-embedding-3-small with 1536 dims) invoked via OPENAI_API_KEY. LlamaIndex calls are made at document ingestion (to store embeddings) and at query time (to embed incoming patient request). | Prompt requires LlamaIndex, but doesn't pick an embedding model/provider or dims; builder must choose and document this. |
| App surface | specified | no | Expose a /find-provider endpoint that accepts a plain-language patient request ... and returns ranked provider matches | - | Implement an HTTP API (e.g., FastAPI with uvicorn) exposing POST /find-provider or GET with query param; accept plain-text user query and return JSON list of providers with similarity scores. | Prompt explicitly defines the endpoint and expected plain-language input. |
| Provisioning and deployment | ambiguous | no | Using the DocumentDB skill | documentdb-azure-deployment | The sample will not attempt to provision a cluster (use the provided live cluster per skill_md). If IaC is required, the documentdb-azure-deployment skill can produce Bicep/CLI, but the prompt and run environment say do not create another cluster. | There is a skill to provision resources, but skill_md instructs to use the existing cluster for this sample. |
| Run and test instructions | missing | no | - | - | Repository will include a README with commands: pip install -r requirements.txt, copy .env.example to .env and set DOCUMENTDB_URI and OPENAI_API_KEY, run a seed script (python seed.py), then run uvicorn app:app --reload; unit tests use pytest with DB access mocked. | Prompt and skill_md do not include explicit run/test command sequences. |
| Definition of done | missing | no | - | - | Accept if: endpoint runs locally, seed script populates sample DB and creates vector index, /find-provider returns ranked providers for sample queries and returns similarity scores, and repo includes README, .env.example, requirements.txt, and basic unit tests. | No explicit acceptance criteria provided in the starter prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep costs low by using existing cluster; do not attempt to manage PHI or implement advanced security beyond TLS and env-driven creds; document non-goals in README (no production HA, no data anonymization). | Prompt doesn't list cost or compliance constraints; security skill is available for best-practices guidance. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Repository will follow typical sample layout: README.md, app/ (FastAPI app), seed.py, requirements.txt (pinned), .env.example, tests/ with pytest, and use the name 'Azure DocumentDB' in docs. | Prompt does not specify repo layout or naming conventions; local-deployment skill suggests env-driven config patterns but not full conventions. |
