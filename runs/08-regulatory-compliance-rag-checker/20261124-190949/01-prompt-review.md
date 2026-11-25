# 1. Prompt review: 08-regulatory-compliance-rag-checker

**Verdict: sufficient_with_assumptions**

The prompt clearly defines the core goal (Python + LlamaIndex RAG agent over two DocumentDB collections) and the run environment supplies important runtime details (existing cluster, DATABASE name, DOCUMENTDB_URI). Many DocumentDB-specific concerns (vector/index guidance, connection best-practices, data-model guidance) are covered by installed skills. Missing/ambiguous items (Python version, exact driver/version, embedding/LLM provider and dims, app surface, sample-data/seed script, README/test/packaging conventions) will be decided by the builder's defaults unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Provisioning and deployment |
| Covered by a skill | 3: Authentication and secrets, Data model, Queries and indexes |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, AI components, App surface, Definition of done |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials from environment (embedding/LLM) — prompt/skill_md specify DOCUMENTDB_URI but do not specify model API keys or the env variable names for embeddings/LLM.
- .env.example lists every setting with placeholders — not present in prompt or skills; builder must create it.
- Vector index dimensions match the embedding model's output — embedding model not specified, so index dimensions may be mis-sized unless author declares the model.
- Vector index parameters chosen for the sample's data size and README explains how to change them — skills give guidance but the sample prompt doesn't commit to parameters or documentation.
- Seed script that loads sample data and is idempotent — prompt does not provide a seed dataset or explicit idempotency instructions; skill hints exist but no explicit seed.
- /search (or analyze) endpoint error handling for empty query and embedding-call failure — prompt does not require or define API surface or error behaviors.
- Search results include similarity score — prompt requests 'most relevant' clauses but does not explicitly require returning similarity scores; at risk unless implemented by builder.
- Dependencies pinned in requirements.txt — not specified; builder may or may not pin versions.
- Unit tests run without a live cluster — prompt/skills do not require mock-based tests and tests are not specified; at risk.
- Infrastructure-as-code to provision the cluster — prompt assumes an existing cluster; the gallery requirement to include infra code would be unmet unless the builder adds it.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a README; builder must add one to satisfy gallery expectations.

## Questions for the prompt author

- Which embedding model and LLM provider should the sample use (e.g. OpenAI text-embedding-3 + gpt-4o, local Llama, or another)? This determines embedding dims and index config.
- Which exact Python version should the sample target (e.g. 3.10, 3.11)?
- Do you prefer a CLI, a minimal HTTP API (FastAPI/Flask), or both for the agent's surface? Any required route names (e.g. /analyze or /search)?
- Should the sample include an infra-as-code artifact to create an Azure DocumentDB cluster, or must it assume the cluster is pre-provisioned (per skill_md)?
- Do you want pymongo pinned to a specific version/range in requirements.txt (e.g. pymongo>=4.3,<5)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LlamaIndex RAG agent that indexes regulatory documents and internal policy documents as separate collections... retrieve the most relevant regulatory clauses... produce a compliance gap report" | - | - | Goal, user story and expected output (compliance gap report) are explicitly stated. |
| Workflow type | specified | no | "build a Python LlamaIndex RAG agent" (single agent RAG flow implied) | - | - | Prompt implies a single-agent RAG workflow implemented in one program. |
| Language and runtime | ambiguous | no | "Python" | documentdb-local-deployment | Builder will target a recent Python 3.x (commonly 3.10 or 3.11) and a virtualenv (python/pip available as described in skill_md). | Version not specified; skill_md indicates a dev environment with python/pip but not a concrete Python version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the pymongo driver (modern stable series, e.g. pymongo >=4.0 compatible with MongoDB 7.0). Follow documentdb-driver guidance to create a singleton MongoClient. | Prompt doesn't name pymongo or a version; documentdb-driver skill prescribes singleton MongoClient patterns but not an exact package version. |
| Target service and tier | specified | no | "Using the DocumentDB skill" | - | - | Run environment (skill_md) explicitly says an M30 vector-capable Azure DocumentDB cluster (MongoDB 7.0) is reachable and that the sample must use database `sample_fintech_08`. |
| Authentication and secrets | covered_by_skill | no | - | documentdb-mcp-setup | The DocumentDB connection string is read from DOCUMENTDB_URI (per skill_md). Model/LLM credentials are not specified — assume standard env vars (e.g. OPENAI_API_KEY or PROVIDER-specific vars) and that none are checked into repo. | skill_md requires DOCUMENTDB_URI in env; model/embedding credentials are not specified in prompt or skill_md. |
| Data model | covered_by_skill | no | "indexes regulatory documents and internal policy documents as separate collections" | documentdb-data-modeling | Builder will create two collections in `sample_fintech_08`: `regulatory` and `policies`. Document shape will include at least: _id, title/source, clause_id, full_text, metadata, and optional schemaVersion. Large text may be stored in the document; embedding vectors stored in a vector field or in LlamaIndex-managed storage. | Prompt requires separate collections; documentdb-data-modeling skill gives guidance on shape/embedding/denormalization but exact fields must be chosen by builder. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will include a small synthetic sample dataset (a few regulatory clauses and a few internal policies) and a seed script that upserts documents to avoid duplication. | Prompt does not say source, size, license, or provide sample datasets. |
| Queries and indexes | covered_by_skill | no | "indexes ... as separate collections" and "vector index with LlamaIndex" (implied) | documentdb-vector-search, documentdb-indexing | Builder will create a vector (`cosmosSearch`) index on the regulatory collection matching the embedding dimensions returned by chosen embedding model; scaffold a top-K configurable vector query via `$search`/`cosmosSearch` and return metadata + similarity scores. | Vector/index tuning guidance is available in the installed skills; the prompt doesn't specify index subtype/parameters or exact vector field name. |
| AI components | ambiguous | no | "LlamaIndex RAG agent" | - | Builder will use a common embeddings provider (e.g. OpenAI text-embedding-3 or another embedding model) and a LLM compatible with LlamaIndex; embedding dims (and dimensions) will be set to the chosen provider (e.g. 1536 for some OpenAI embeddings) and recorded in config/env. Model/API keys come from env vars (e.g. OPENAI_API_KEY). | LlamaIndex is specified, but which embedding model / LLM provider and dims are not — this materially affects index dimensions and configuration. |
| App surface | ambiguous | no | "When given a policy excerpt, the agent retrieves... and produces a compliance gap report" | - | Builder will implement a simple CLI and a minimal HTTP endpoint (e.g. FastAPI or Flask) such as POST /analyze that accepts a policy excerpt and returns the report; include example CLI invocation. | Prompt describes the end-to-end operation but not whether a CLI, API, or UI is required. |
| Provisioning and deployment | specified | no | "Using the DocumentDB skill" and skill_md run environment | documentdb-azure-deployment | Do not provision a new cluster; use the existing cluster described in skill_md. If infra code is supplied it must not be used to create another live cluster during the build run. | skill_md explicitly states a reachable cluster exists and build should use it rather than provisioning a new one. |
| Run and test instructions | missing | no | - | - | Builder will add README with commands: pip install -r requirements.txt, export env vars, python seed.py, python app.py, and pytest for unit tests (with guidance for mocking the DB for offline tests). | Prompt/skill_md lack explicit run commands or test instructions. |
| Definition of done | ambiguous | no | "retrieves the most relevant regulatory clauses, compares them, and produces a compliance gap report" | - | Definition of done used by builder: ingestion works (documents in both collections), LlamaIndex vector index built and searchable, end-to-end analyze flow returns a report including a verdict (compliant/partial/non-compliant), listed gaps mapped to regulatory clauses with citations (document ids/metadata), and suggested remediation steps. | Prompt gives high-level acceptance criteria but not precise checks (top-K configurable, explicit fields returned, test expectations). |
| Constraints and non-goals | missing | no | - | - | Builder will keep sample data small to limit costs, avoid provisioning extra cloud resources, and document that this is a demo not production-ready (no CMK, no private endpoints). | No cost/threshold or non-goal guidance provided. |
| Repository conventions | missing | no | - | - | Repository will include: README.md, requirements.txt (pinned), .env.example, src/ or app/ layout, scripts/seed.py, tests/ with unit tests, and a LICENSE. Use the name "Azure DocumentDB" in docs. | Prompt doesn't specify layout, dependency pinning, or README requirements; skill_md gives some environmental requirements but not repo conventions. |
