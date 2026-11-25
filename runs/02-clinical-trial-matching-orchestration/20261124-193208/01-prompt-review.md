# 1. Prompt review: 02-clinical-trial-matching-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the high-level goal (Python LangChain orchestration that vector-searches trials, runs eligibility and consent agents, and stores matches). Many implementation details (index dims, embedding model, exact schema, API surface, runtime versions, tests, README, .env contents) are not specified and will be chosen by the builder or filled in from the installed DocumentDB skills. Nothing is blocking; the build can start but several important choices will be assumed by the implementer.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Workflow type, Target service and tier, Provisioning and deployment |
| Covered by a skill | 3: Driver and version, Authentication and secrets, Queries and indexes |
| Ambiguous: builder will guess | 4: Language and runtime, Data model, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- In code, create a cosmosSearch vector index that specifies embedding dimensionality — prompt asks for vector search but does not name the embedding model or dimensionality; unless the author specifies the model the builder must choose one and could get the dimension wrong.
- Seed script writes embedding vectors into each trial document — the prompt requires vector search over stored embeddings but does not state how embeddings are produced (model/provider), so seed script behavior is at risk.
- .env.example lists every setting with placeholder values — prompt/skill_md note use of environment variables but don't enumerate all required settings (model keys, DB URI, service-specific flags).
- Dependencies pinned in requirements.txt — prompt doesn't instruct pinning; builders may not pin versions unless asked.
- Unit tests run without a live cluster — prompt doesn't require tests or mocking strategy; often omitted unless explicitly requested.
- Infrastructure-as-code for the cluster using the Azure DocumentDB resource type — run environment says a cluster already exists and the prompt doesn't request providing IaC; reference requires IaC but the starter prompt does not.
- Vector index parameters chosen for sample size and README guidance on changing them for larger datasets — index param tuning and explanatory docs are not specified by the prompt.
- Search results include the similarity score — prompt asks for ranked candidates but doesn't require returning the numeric similarity score; may be omitted unless enforced.
- The vector index dimensions match the embedding model's output — tied to embedding model choice which is unspecified and therefore at risk of mismatch.
- README coverage (what sample shows, prerequisites, setup, run, clean-up) — prompt implies verification but does not mandate a complete README; could be incomplete.

## Questions for the prompt author

- Which embedding model and provider should the sample use (and therefore what is the embedding dimensionality)? This determines the vector index dimensions and seed embeddings.
- Do you want an HTTP API endpoint (e.g., POST /match) for the orchestration or a CLI/demo script? The choice changes the app surface and example usage.
- Should the sample create the cosmosSearch vector index programmatically in code (seed script) or assume the index exists and only show the query? The reference requirements prefer creating the index in code.
- Should the sample include unit tests that run without a live cluster (mocks) and a requirements.txt with pinned versions? If so, which critical versions (Python, pymongo, LangChain) do you want pinned?

## Contradictions and missing references

- The prompt uses the phrase "Using the DocumentDB skill" as if a single skill named exactly that exists; installed skills are split into specialized documentdb-* skills (documentdb-connection, documentdb-vector-search, etc.). There is no skill named exactly "DocumentDB" — builder will need to pick among the installed documentdb-* skills.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python LangChain orchestration pipeline that accepts a patient profile, uses vector search against a DocumentDB index of trial criteria to find candidate trials, passes candidates to an eligibility agent..., then hands off to a consent agent... Store match results in DocumentDB. | - | - | Clear business problem, user, and demonstration goal. |
| Workflow type | specified | no | orchestration pipeline... passes candidates to an eligibility agent... hands off to a consent agent | LangChain (implied by prompt). | - | Multi-agent orchestration (LangChain Python) explicitly requested. |
| Language and runtime | ambiguous | no | Python LangChain | documentdb-connection (environment notes) — skill_md states python and pip are available on the developer machine but not specific version. | Builder will target a modern Python 3.x (most likely Python 3.11) and create a virtualenv. LangChain will be pinned to a recent compatible release in requirements.txt. | Prompt specifies Python but not exact Python or LangChain versions; skill_md confirms Python is available but not versioned. |
| Driver and version | covered_by_skill | no | - | documentdb-connection; documentdb-driver | Use PyMongo (pymongo) compatible with MongoDB 7.0; builder will pick a recent PyMongo (e.g., pymongo >=4.9 for AsyncMongoClient if using async, or >=4.4 for sync usage) and follow the singleton MongoClient pattern. | Skills recommend PyMongo best practices (singleton client) and note async API availability (PyMongo 4.9+). |
| Target service and tier | specified | no | skill_md: A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable from this machine. Connection string in DOCUMENTDB_URI. Use database sample_healthcare_02. | - | - | Run environment (skill_md) gives cluster tier and DB name to use. |
| Authentication and secrets | covered_by_skill | no | skill_md: connection string in environment variable DOCUMENTDB_URI; do not write it to files or logs. | documentdb-security (for auth/recommendations) and skill_md | All secrets (DB URI and any model API keys) will come from environment variables; builder will include a .env.example with placeholders. | Secrets location is defined in the run environment; security skill provides best-practice guidance. |
| Data model | ambiguous | no | index of trial criteria, trial documents, patient profile | documentdb-data-modeling | Builder will create a 'trials' collection in database sample_healthcare_02 with documents containing fields like: 'trial_id' or _id, 'title', 'criteria' (structured inclusion/exclusion fields: age ranges, conditions, lab thresholds), 'embedding' (list of floats), and 'metadata'. Patient profile will be JSON with matching fields (age, conditions, labs). | Prompt implies trial criteria/embedding but doesn't define exact schema or collection name; data-modeling skill offers patterns but not a single canonical schema. |
| Sample data | missing | no | - | documentdb-local-deployment (dev data patterns) can help with seeding guidance | Builder will include a small synthetic seed dataset (few-to-dozen trial documents) generated by a seed script included in the repo; no external licensed dataset will be used. | Prompt and skill_md ask to load sample data for verification, but do not specify source, size, license or seed content. |
| Queries and indexes | covered_by_skill | no | use vector search against a DocumentDB index of trial criteria to find candidate trials | documentdb-vector-search; documentdb-indexing; documentdb-full-text-search | Builder will use a 'cosmosSearch' vector $search query via PyMongo against an 'embedding' field, and will programmatically create a vector index (e.g., kind vector-hnsw or vector-ivf) with the dimensionality matching the chosen embedding model. | Skills cover creating and tuning vector indexes and issuing $search queries; prompt does not name embedding field or index parameters, so builder will pick defaults (field 'embedding' and index params suitable for small sample). |
| AI components | missing | no | - | - | Builder will pick a hosted embedding model/provider (commonly OpenAI text-embedding-3-small or similar) and a chat/completion model for the eligibility/consent agents (e.g., OpenAI chat model). Embedding dimensionality will be set to the chosen model's output (e.g., 1536 for many OpenAI embeddings). Model API keys come from environment variables (e.g., OPENAI_API_KEY). | Starter prompt requires agent behavior but does not specify embedding or chat models, nor where to call them; these are important choices the builder must make. |
| App surface | ambiguous | no | orchestration pipeline that accepts a patient profile | - | Builder will expose a small HTTP API (FastAPI) endpoint (e.g., POST /match or /search) that accepts a patient profile JSON and returns match results. A CLI wrapper or example script may also be provided for demonstration. | Prompt doesn't require a UI vs API vs CLI. Reference requirements expect an HTTP endpoint name (/search) and error handling; builder will likely provide an API for demonstration. |
| Provisioning and deployment | specified | no | skill_md: cluster already provisioned and reachable; don't create another cluster. | documentdb-azure-deployment (available if user wanted to provision) | No cloud provisioning will be performed by the sample; the provided cluster will be used. | Run environment explicitly states the cluster exists and must be used; builder should not provision new clusters. |
| Run and test instructions | missing | no | - | - | Builder will include README with commands: pip install -r requirements.txt, cp .env.example .env (fill in API keys/URI), python seed.py, uvicorn main:app --reload, and pytest (unit tests will mock DB). | Prompt and skill_md require verification but do not enumerate exact run/test commands. |
| Definition of done | missing | no | - | - | Definition of done will be: seed script creates collections/indexes and sample data; POST /match returns ranked candidate trials; eligibility agent returns structured pass/fail + rationale; consent agent returns plain-language summary; match stored in DB; unit tests pass and README documents steps. | No explicit acceptance criteria in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security (for security constraints guidance) | Builder will use synthetic patient data (no PHI), instruct users not to use real patient data, and follow TLS/env-var secrets handling. Cost/provisioning limits: do not create new paid Azure resources. | HIPAA/PHI handling not specified; implementer should call out synthetic-data constraint. |
| Repository conventions | ambiguous | no | skill_md: instructs to use config file or .env.example with placeholders | documentdb-local-deployment (env patterns) and documentdb-driver (singleton pattern) | Builder will follow common conventions: top-level README.md, src/ or app/ for source, scripts/seed.py, tests/, requirements.txt, .env.example, and a short build report. | Prompt and skill_md give partial conventions (env handling) but not full repo layout or dependency-pinning expectations. |
