# 1. Prompt review: 11-correspondent-banking-risk-screener

**Verdict: sufficient_with_assumptions**

The starter prompt + provided skill.md give a clear goal (Python LangChain agent doing vector embedding/search in Azure DocumentDB) and an available, vector-capable cluster. Several implementation details (Python version, exact driver/version, embedding model & dims, app surface, seed data, tests, README/infra artefacts) are left to the builder and will be filled by skill guidance or reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 6: Language and runtime, Driver and version, Data model, AI components, App surface, Constraints and non-goals |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Provide a `.env.example` that lists every setting with placeholders — not present in the prompt or skill.md; likely to be added by the builder but not specified.
- Vector index dimensions match embedding model output — embedding model is unspecified, so dimensions are at risk.
- Vector index parameters chosen for sample size and README guidance to change them — index tuning is not specified in the prompt; skills can guide but README instructions are not specified.
- Seed script loads sample data and is idempotent (can be run twice without duplicating data) — prompt doesn't mention seed script; skill.md mentions verifying against live cluster but no seed script included.
- /search returns clear errors for empty query and when embedding call fails — error handling behaviour is not specified.
- Search results include the similarity score — prompt asks for matched entries and a risk score but does not explicitly require including the raw similarity score in the returned results.
- Dependencies are pinned in `requirements.txt` — prompt doesn't require pinned versions.
- Unit tests run without a live cluster — no tests or test strategy are specified.
- Infrastructure as code for the cluster is provided — skill.md indicates a cluster already exists; the starter prompt does not ask for infra, but the gallery reference requires it.
- README covers sample, prerequisites, setup, run, and clean-up — the prompt doesn't require a README; the builder must add one but it's not specified.

## Questions for the prompt author

- Which embedding model and provider should be used (and therefore what are the embedding dimensions)? This determines the vector index `dimensions` value.
- What app surface do you want: a small HTTP API (e.g., FastAPI with /review), a CLI demo, or both?
- Do you require infrastructure-as-code (Bicep/Terraform) for provisioning the cluster as part of the repo, or should the sample assume the pre-provisioned cluster described in skill.md?
- Which exact Python runtime and pinned dependency policy should the sample target (e.g., Python 3.10 or 3.11 and pinned versions in requirements.txt)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain agent that embeds correspondent bank entity profiles, stores the vectors in DocumentDB, and searches against embedded sanctions list and adverse media entries" | - | - | Business problem, user and what sample demonstrates are explicit. |
| Workflow type | specified | no | "Python LangChain agent" | - | - | Single-agent LangChain workflow is implied. |
| Language and runtime | ambiguous | no | "Python LangChain agent" | - | Builder will use a modern Python 3.x (likely 3.10 or 3.11) and create a virtualenv; tests and requirements will target that runtime. | Prompt and skill.md say 'python' but do not pin a version. |
| Driver and version | ambiguous | no | store the vectors in DocumentDB (MongoDB-compatible Python driver implied) | documentdb-driver | Use the pymongo Python driver (pymongo 4.x, e.g. >=4.3,<5.0) and follow singleton MongoClient pattern per documentdb-driver guidance. | documentdb-driver skill covers best-practices (singleton MongoClient) but doesn't mandate an exact package version. |
| Target service and tier | specified | no | - | documentdb-local-deployment | Use the provided live Azure DocumentDB cluster described in skill.md: database `sample_banking_11`, vector-capable cluster M30, MongoDB 7.0 protocol with DiskANN/HNSW/IVF available. | skill.md explicitly documents the environment and cluster constraints. |
| Authentication and secrets | specified | no | - | - | Connection string read at runtime from DOCUMENTDB_URI env var; other credentials (embedding/LLM keys) will be read from environment variables. | skill.md requires DOCUMENTDB_URI and forbids writing it to repo files. |
| Data model | ambiguous | no | "embed correspondent bank entity profiles... store sanctions list and adverse media entries as documents" | documentdb-data-modeling | Builder will create collections like `correspondents`, `sanctions`, and `adverse_media`. Documents will include fields: `_id`, metadata fields (name, country, ids), an `embedding` field (float array), `schemaVersion`, and timestamps. Embeddings stored inline on the document. | High-level shapes are implied but exact names, fields and shard key are not specified; data-modeling skill guides choices. |
| Sample data | missing | no | - | - | Builder will include a small synthetic seed dataset (JSON) for correspondents, sanctions, and adverse media in a `seed/` folder and a seed script to load it. | Prompt and skill.md do not supply or point to sample data or its license; seed loading is not specified. |
| Queries and indexes | covered_by_skill | no | "searches against embedded sanctions list and adverse media entries" | documentdb-vector-search | Create a `cosmosSearch` vector index on the embedding field (choose vector-diskann or vector-hnsw per dataset size). Use $search with `cosmosSearch` knn query; include similarity scores in results. | documentdb-vector-search and documentdb-indexing provide the detailed guidance to create and tune vector indexes and to run $search queries. |
| AI components | ambiguous | no | "LangChain agent" and "embeds... profiles" | - | Use a LangChain-compatible embedding provider (commonly OpenAI embeddings via OPENAI_API_KEY). Adopt a specific embedding model (e.g., OpenAI text-embedding-3-small) and set index `dimensions` to the model output (assume 1536 dims unless another model is chosen). Use a chat/completion model via LangChain for the 'plain-language risk narrative' (e.g., GPT-4o-mini or similar) with its API key read from env. | The prompt does not name embedding model, dimensions, or provider; these materially affect index creation. |
| App surface | ambiguous | no | "agent... returns a risk score, matched entries, and a plain-language risk narrative" | - | Builder will implement a small API (FastAPI) with an endpoint such as POST /review or /search that accepts a correspondent id or profile and returns score, matched entries and narrative. A CLI driver for local demo may also be provided. | Starter prompt doesn’t state whether to build CLI, web API, or UI; reference requirements expect a /search route. |
| Provisioning and deployment | specified | no | - | - | Do not provision a cluster in the sample—use the pre-provisioned cluster described in skill.md; do not create new cloud resources unless explicitly allowed. | skill.md explicitly states an existing cluster is available and cluster writes should be avoided unless policy allows. |
| Run and test instructions | missing | no | - | - | Builder will add README steps: create .env from .env.example, pip install -r requirements.txt, run seed script, start FastAPI with uvicorn, then call /review endpoint to see results. | No explicit commands, expected outputs or test descriptions are provided in the prompt or skill.md. |
| Definition of done | missing | no | - | - | Acceptance = sample runs against the provided cluster, seed script loads data and index is created, /review returns risk score + matched entries + narrative, and README explains how to run. | No explicit acceptance criteria in prompt. |
| Constraints and non-goals | ambiguous | no | - | documentdb-security | Follow minimal security constraints: read connection string from env (DOCUMENTDB_URI), avoid logging secrets, and keep sample data small to limit costs. Do not attempt production hardening (e.g., CMK) in sample. | skill.md gives some constraints (don't write secrets), but cost or licensing constraints aren't stated. |
| Repository conventions | missing | no | - | - | Use common sample layout: README.md, requirements.txt, src/, seed/, .env.example, tests/, and follow wording 'Azure DocumentDB' in docs. | No explicit repo layout or naming conventions are given. |
