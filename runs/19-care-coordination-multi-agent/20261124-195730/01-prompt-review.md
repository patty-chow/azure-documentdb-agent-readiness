# 1. Prompt review: 19-care-coordination-multi-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines a Python + LangChain multi-agent orchestration that reads/writes from an existing Azure DocumentDB cluster and synthesises a care plan. Many implementation details (Python version, exact drivers and versions, LLM/embedding selection, collection schemas, indexing, seed data, app surface, tests and README conventions) are left to the builder and will be filled by skills or reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 4: Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 7: Sample data, Queries and indexes, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — skill_md mentions env var usage but does not provide or require a .env.example; the starter prompt doesn't ensure it will be added.
- The vector index dimensions match the embedding model's output — no embedding model is chosen in the prompt, so matching index dims are unspecified.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — indexes and their parameters are not specified in the prompt.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the prompt doesn't request a seed script or idempotency.
- /search returns a clear error for an empty query and when the embedding call fails — error handling for search/embedding is not mentioned.
- Search results include the similarity score — retrieval output format is not specified.
- Dependencies are pinned in `requirements.txt` — the prompt does not say to pin dependencies; it's a common builder decision but at risk.
- Unit tests run without a live cluster — no explicit testing strategy is provided; builders may or may not provide mocked tests.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the run-environment forbids provisioning another cluster; no IaC is requested, so this requirement is at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt does not explicitly require a complete README (although the run-environment implies verification steps).

## Questions for the prompt author

- Which LLM provider and specific models/embedding model should the sample use (e.g., OpenAI; embed: text-embedding-3-small -> 1536 dims; chat: gpt-4o-mini)? This determines vector-dimension and index parameters.
- Do you want an HTTP API (FastAPI) surface in addition to a CLI, or only a CLI demo (the prompt is silent on the app surface)?
- Which Python runtime should be targeted (3.10, 3.11, or other)? This affects dependency compatibility and CI matrix.

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python LangChain multi-agent system ... GP agent that reads the patient's primary care record from DocumentDB, a specialist agent that retrieves referral notes, and a pharmacy agent that checks current medications. An orchestrator coordinates all three and synthesises a unified care plan document written back to DocumentDB." | - | - | Business problem, users (GP/specialist/pharmacy/orchestrator) and demo (synthesise a care plan) are explicit. |
| Workflow type | specified | no | "LangChain multi-agent system" and mention of an orchestrator plus three agents (GP, specialist, pharmacy). | - | - | Multi-agent orchestration with LangChain is explicit. |
| Language and runtime | ambiguous | no | "Python LangChain" | - | Builder will target a modern Python 3.x runtime (likely 3.10 or 3.11). I.e., assume Python 3.10+ for dependencies and type hints. | Prompt specifies Python but not the exact interpreter version; the run environment doc implies Python is available but does not fix a version. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the Python MongoDB driver (PyMongo) and a recent stable release compatible with MongoDB 7.0 (e.g., pymongo >= 4.3). Follow the documentdb-driver guidance to use a singleton MongoClient. | The documentdb-driver skill covers best practices (singleton client) but does not specify an exact package version; the prompt does not name a driver either. |
| Target service and tier | specified | no | "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) ... connection string is in environment variable DOCUMENTDB_URI" (from skill_md / run environment). | - | - | Cluster details (M30, MongoDB 7.0) and DB to use (sample_healthcare_19) are explicitly provided in the run-environment text. |
| Authentication and secrets | specified | no | "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" (from skill_md). | - | - | Where to get the connection string and how to handle secrets is stated. |
| Data model | ambiguous | no | "Use the database named `sample_healthcare_19`" (from skill_md). | documentdb-data-modeling | Builder will create collections: patients (primary care records keyed by patient_id), referrals (referral notes with patient_id), medications (current meds with patient_id), and care_plans (synthesised documents). Document shapes will be simple JSON objects with patient_id, timestamps, clinician/note fields; no sharding will be required for the small sample. | Database name is given, but collection names and precise document schemas are not; the documentdb-data-modeling skill can guide shapes and embedding vs referencing decisions. |
| Sample data | missing | no | - | - | Provide a small synthetic dataset (a few patients with primary-care notes, one or two referrals and medication lists). Implement a seed script that upserts documents so it can be run multiple times without duplicating data. | No source, size, or licensing of sample data is supplied; the builder must create synthetic sample data and a seed script. |
| Queries and indexes | missing | no | - | documentdb-indexing | Create single-field indexes on patient_id for the patients/referrals/medications collections. If using vector retrieval for parts of the pipeline, create a vector index with dimensions matching the chosen embedding model (see AI components assumption). Provide a short README note on how to change index params for larger data sets. | Prompt asks for read operations but does not list query patterns or index definitions; documentdb-indexing skill can be used to pick sensible index shapes. |
| AI components | missing | no | "LangChain" and agent roles are stated, but no LLM or embedding model/provider is specified. | documentdb-vector-search | Use an OpenAI-compatible provider (env var OPENAI_API_KEY). Use a commonly used embedding model (e.g., text-embedding-3-small producing 1536-d vectors) and a chat/completion model for synthesis (e.g., gpt-4o-mini or gpt-4o where available). Put provider credentials in environment variables and document them in .env.example. | LangChain usage is explicit but exact model/provider and embedding dims are not; vector-search skill can guide index choices but not pick a model for you. |
| App surface | ambiguous | no | "An orchestrator coordinates all three and synthesises a unified care plan document written back to DocumentDB." | - | Provide a simple CLI entrypoint (e.g., python run_orchestrator.py --patient-id <id>) and also a minimal FastAPI HTTP endpoint (/orchestrate) that accepts a patient_id and returns the care-plan summary. The sample should demonstrate both the CLI and a single API route for manual testing. | Prompt does not require a specific UI or API; builder will decide. Include example commands in README. |
| Provisioning and deployment | specified | no | "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." (from skill_md). | - | - | The run-environment explicitly indicates the cluster already exists and should be used; the sample should not create new cluster resources. |
| Run and test instructions | missing | no | - | - | Include a README with exact commands: pip install -r requirements.txt, copy .env.example -> .env and fill DOCUMENTDB_URI and model keys, python seed_data.py, python run_orchestrator.py --patient-id <id>, and how to call the FastAPI endpoint. Provide unit tests that mock the database so they run without a live cluster. | No explicit run/test commands provided in prompt or skill_md. |
| Definition of done | missing | no | - | - | Consider done when: (1) the orchestrator calls each worker agent, (2) the orchestrator synthesises a unified care plan via an LLM call, and (3) the care plan is inserted into the care_plans collection in sample_healthcare_19. Include demonstration script showing the inserted care_plan and sample output in the README. | No explicit acceptance criteria in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Treat data as synthetic (no PHI). Avoid provisioning additional Azure resources. Keep compute and API usage modest to limit costs. Note these constraints in README and ensure secrets are not committed. | Privacy and cost constraints are not stated; documentdb-security can provide security guidance but the prompt does not state formal non-goals. |
| Repository conventions | missing | no | "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" (from skill_md) — partial guidance, but other repo conventions are not specified. | - | Repository will include: README.md, requirements.txt (pinned), .env.example, seed_data.py, app/ (code), tests/ with mocks, and a LICENSE. Use the name 'Azure DocumentDB' consistently in docs. | A .env.example is suggested but requirements pinning, test conventions, and README sections are not specified in the prompt. |
