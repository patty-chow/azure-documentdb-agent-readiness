# 1. Prompt review: 07-mortgage-application-multi-agent

**Verdict: sufficient_with_assumptions**

The starter prompt plus the run-environment notes give a clear goal (Node.js LangChain multi-agent mortgage pipeline) and enough infra constraints (existing M30 cluster, DOCUMENTDB_URI env var, DB name). Core orchestration and DocumentDB usage are specified, and installed skills cover driver/connection best practices. Several important implementation details are left to the builder (driver version, data model, exact AI models, API surface, seed data and idempotent seeding, index shapes and vector dims, README/test/infrastructure artifacts) and will be filled by sensible defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets, Constraints and non-goals |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 1: Driver and version |
| Missing: builder will guess | 9: Data model, Sample data, Queries and indexes, AI components, App surface, Provisioning and deployment, Run and test instructions, Definition of done, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials from environment: skill.md specifies DOCUMENTDB_URI but not LLM provider credentials; the starter prompt doesn't require model creds to be in env, so that's at risk.
- .env.example lists every setting with placeholders: skill.md instructs using .env.example but does not list all required env vars (LLM creds, model names, other toggles).
- Vector index dimensions must match the embedding model's output: no embedding model was selected in prompt or run notes, so vector dims are unspecified.
- Vector index parameters chosen for data size and README guidance: prompt/skills do not pick concrete index parameters or sample-size tunings.
- Seed script that loads sample data and creates the index idempotently: run notes say to load sample data, but no seed script or idempotency plan is provided.
- /search behavior for empty query and embedding failures: prompt doesn't specify API surface or error-handling behaviors for search endpoints.
- Search results include similarity score: not specified in prompt or skills; likely omitted unless implemented explicitly.
- Dependencies pinned in a requirements file: for Node this means package-lock.json or pinned package.json; starter prompt doesn't require pinning.
- Unit tests runnable without a live cluster: tests must mock DB/LLM to avoid live cluster dependency; prompt doesn't mandate this.
- Infrastructure-as-code for the cluster using the Azure DocumentDB resource type: prompt assumes an existing cluster and does not request IaC; although a skill exists to produce it, the sample may omit infra code.
- README coverage (what the sample shows, prerequisites, setup, run, clean-up): README is not required by the starter prompt, though skill.md asks to record what was executed; actual README content is at risk.

## Questions for the prompt author

- Which LLM provider and exact model names should the LangChain agents use (chat model and embedding model)? This affects embedding dimensions and env vars required.
- Do you want infrastructure-as-code for the Azure DocumentDB cluster included (Bicep/Terraform), or must the sample assume the existing cluster only (as skill.md suggests)?
- Which concrete collection names and document schema do you want used for applications and decisions, or should the builder invent a small example schema?
- Should the sample expose an HTTP API (Express) for triggering the pipeline, or should it be a CLI/script that runs locally against an applicationId?
- Do you require pinned dependency versions in package.json/package-lock, and any specific test framework to be used (Jest, Mocha)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js LangChain multi-agent mortgage pipeline where an orchestrator reads the application document from DocumentDB, passes it to an underwriting agent ... compliance agent ... comms agent ... Write the outcome back to DocumentDB." | - | - | - |
| Workflow type | specified | no | "LangChain multi-agent ... an orchestrator ... underwriting agent ... compliance agent ... comms agent" | - | - | - |
| Language and runtime | specified | no | skill.md: "Node.js 24 with npm and npx is available." | - | - | Run environment explicitly provides Node.js 24. |
| Driver and version | ambiguous | no | - | documentdb-driver | Builder will use the official MongoDB Node.js driver (npm package "mongodb") and pick a recent v5.x release compatible with Node.js 24 (e.g., "mongodb": "^5.0.0"), and will follow the documentdb-driver guidance to use a module-level singleton MongoClient. | The documentdb-driver skill covers best practice (singleton client) but neither prompt nor skills pick a concrete driver version. |
| Target service and tier | specified | no | skill.md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ..." | - | - | Run environment fixes the cluster and tier to M30, MongoDB 7.0. |
| Authentication and secrets | specified | no | skill.md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | - | Connection string source and handling are specified; model/LLM credentials are not named and will need to be provided via env vars by the builder. |
| Data model | missing | no | - | documentdb-data-modeling | Builder will create collections such as `applications` (one doc per mortgage application with fields: applicantId, name, income, liabilities, requested_amount, property_value, credit_score, employment history, documents[]) and `decisions` (linked by applicationId, storing underwriting assessment, compliance result, decision letter, timestamps). No shard key will be created for the sample (single-shard usage). | Prompt and run notes name the DB (sample_banking_07) but do not specify collections / field shapes; documentdb-data-modeling can guide choices but does not supply a concrete schema. |
| Sample data | missing | no | skill.md requests verification: "create the collections and indexes, load the sample data..." but does not provide sample data source. | documentdb-local-deployment | Builder will include an idempotent seed script that inserts a small set of synthetic sample applications (e.g., 4–6 documents covering approved/declined/edge cases) and will be runnable twice without duplicating (upsert by applicationId). | No dataset, licence, or size is specified. Local dev skill offers sample-data patterns but not the concrete payload. |
| Queries and indexes | missing | no | - | documentdb-indexing, documentdb-vector-search | Builder will create indexes appropriate for sample queries: a compound/index on applicationId, text or field indexes on applicant name and credit_score, and a small vector index for embeddings whose dimension matches the chosen embedding model (see AI components assumption). Index parameters will be tuned for a tiny dataset (default small-memory / low-lBuild settings) and noted in the README. | Prompt asks to 'create the collections and indexes' in skill.md, but does not specify exact index shapes or vector dims; indexing skills exist to guide choices. |
| AI components | missing | no | "LangChain" and "agents" are named, but no provider or model names/dimensions are specified. | - | Builder will use a hosted LLM provider compatible with LangChain (commonly OpenAI) with chat model for agents (e.g., gpt-4o-mini or similar conversational model) and an embedding model for vector search (e.g., text-embedding-3-small with 1536 dimensions). API credentials for the chosen provider will be read from env vars (e.g., OPENAI_API_KEY). | Choosing concrete models, dimensions, and calling points is left to the implementer and affects vector index shape. |
| App surface | missing | no | Prompt describes pipeline flow but not how the app is exercised (CLI, API, UI). | - | Builder will expose a minimal Express-based HTTP API with endpoints such as POST /seed (seed data), POST /run/:applicationId (run pipeline for an application), and GET /applications/:id to view stored results; this gives a simple way to demo the orchestrator without a UI. | The choice between CLI/API/UI is unspecified and will be selected by the builder. |
| Provisioning and deployment | missing | no | skill.md: instructs to use the existing cluster and not to provision unless policy allows; starter prompt does not request infra-as-code. | documentdb-azure-deployment | Builder will not include infrastructure provisioning for the cluster (sample uses the pre-provisioned M30 cluster); if IaC is required later, the documentdb-azure-deployment skill can produce a Bicep/Terraform template. | Reference requirements expect infra as code, but the starter prompt explicitly assumes an existing cluster in skill.md. |
| Run and test instructions | missing | no | skill.md gives execution context and verification goals but no explicit run/test commands. | - | Builder will include README steps: npm install, copy .env.example -> .env and fill DOCUMENTDB_URI and LLM creds, npm run seed, npm start, then curl POST /run/:applicationId. Unit tests will be runnable with `npm test` and will mock the DB/LLM (so tests run without live cluster). | Explicit commands and test harness are absent and must be authored. |
| Definition of done | missing | no | - | - | Builder's acceptance criteria: a developer can follow README to seed data, run the pipeline for a sample application, observe underwriting and compliance outputs and a drafted decision letter, and see the outcome written to the `decisions` document in `sample_banking_07`. | No formal acceptance checklist is declared in the prompt. |
| Constraints and non-goals | specified | no | skill.md: "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." and "Never write its value [DOCUMENTDB_URI] into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder." | - | - | Key constraints about not provisioning and secret handling are provided. Cost limits and other non-goals are not detailed. |
| Repository conventions | missing | no | skill.md asks for `.env.example` placeholders and gives DB name but includes no full repo layout or dependency-pinning conventions. | - | Builder will follow typical Node.js sample conventions: package.json at repo root, src/ for source, test/ for tests (Jest), README.md with sections (what, prerequisites, setup, run, cleanup), .env.example listing env vars, and package-lock.json committed to pin dependencies. | No explicit repository structure, naming, or telemetry guidance is provided. |
