# 1. Prompt review: 15-prescription-refill-agent

**Verdict: sufficient_with_assumptions**

The prompt clearly states the scenario (a LangChain conversational refill agent) and the core behaviors (lookup active prescriptions, check refill eligibility, create refill request, and use agent memory). However it leaves many engineering choices unspecified (runtime details, LLM/embedding provider, API surface, schemas, indexes) and — critically — requests Beanie ODM together with Node.js, which is a cross-language mismatch the builder will have to resolve (most likely by substituting a Node.js ODM such as Mongoose or by switching to Python). The build can start but will require explicit assumptions about ODM, LLM/embedding choices, interface, and schema/index shapes.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Provisioning and deployment |
| Covered by a skill | 1: Authentication and secrets |
| Ambiguous: builder will guess | 6: Driver and version, Data model, Queries and indexes, App surface, Definition of done, Constraints and non-goals |
| Missing: builder will guess | 4: Sample data, AI components, Run and test instructions, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- A single Node.js LangChain agent built with Beanie ODM — at risk because Beanie is Python-only; the prompt asks for both Node.js and Beanie, which are incompatible.
- Tools implemented specifically 'through Beanie ODM' for lookups and writes — at risk for the same reason (language/ODM mismatch).
- The connection string and model credentials come from environment variables; none appear in the repository — LLM/model creds are not mentioned by the prompt and must be assumed.
- .env.example lists every setting with placeholder values — not mentioned in the prompt or covered explicitly by the installed skills.
- Vector index dimensions match the embedding model's output — prompt does not specify embedding model so matching dims is at risk.
- Vector index parameters chosen for the sample's data size and README explaining how to change them — not specified.
- Seed script loads sample data and creates the index, and can be run twice without duplicating data — seed guidance exists in local-deployment skill but prompt does not require an idempotent seed; implementation may omit idempotency.
- /search returns a clear error for an empty query and when the embedding call fails — prompt does not mention a /search endpoint or error handling details.
- Search results include the similarity score — not specified in prompt; if fuzzy lookup is added this may be omitted.
- Dependencies are pinned in requirements.txt — prompt is Node.js (package.json); explicit dependency pinning and lockfile conventions are not specified.
- Unit tests run without a live cluster — the prompt requires verify against live cluster; tests that run offline (mocks) are not mandated.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type — prompt explicitly says an existing cluster is available and instructs not to provision, so infra-as-code may be omitted.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — not requested explicitly and may be incomplete.
- The sample uses the name 'Azure DocumentDB' throughout — not guaranteed by the prompt; builder might use other names unless instructed.

## Questions for the prompt author

- Do you require Beanie specifically, or is a Node.js-native ODM acceptable? (Beanie is Python-only.)
- Which interface do you want for the agent: HTTP API (Express), CLI, or a web UI?
- Which LLM and embedding provider/models should the sample use (e.g., OpenAI Chat/Embeddings, or a local LLM)?
- Should the sample run against the live cluster only (as skill_md implies), or should a local Docker Gateway option also be included?
- Do you require seed data, and if so, any constraints on sample data shape/size or PHI/synthetic data policy?

## Contradictions and missing references

- The prompt requests 'Beanie ODM' together with 'Node.js'. Beanie is a Python ODM (Motor/PyMongo/Beanie) and not usable directly from Node.js; a builder must either switch the implementation language to Python or substitute a Node.js ODM (for example Mongoose).
- The prompt says 'Using the DocumentDB skill' but there is no single skill named exactly 'DocumentDB skill' — instead several documentdb-* skills are installed. The builder will interpret this as 'use the DocumentDB-related skills' rather than a single skill.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | 'build a Node.js LangChain agent ... that look[s] up the patient's active prescriptions ... check refill eligibility ... and create a refill request document' and 'agent memory so the patient can say \"refill my blood pressure medication\" without specifying the drug name each time.' | - | - | Business problem, user and demonstrated DB behavior are explicit. |
| Workflow type | specified | no | 'Node.js LangChain agent' and 'using ... tools' (conversational agent with tools) | - | - | Single-agent LangChain with tool-call orchestration is requested. |
| Language and runtime | specified | no | 'Node.js LangChain agent' | - | Use Node.js 24 (the run-environment snippet supplied alongside the prompt indicates Node.js 24 is available). | Prompt indicates Node.js; precise patch version not given but run-environment (skill_md) specifies Node.js 24. |
| Driver and version | ambiguous | yes | 'Beanie ODM' (the prompt explicitly asks for Beanie) | - | Builder will likely substitute a Node.js-native ODM (e.g., Mongoose) or else switch the implementation language to Python (to use Beanie). Most builders will choose Mongoose for a Node.js sample. | Contradiction: Beanie is a Python ODM. Requesting Beanie in a Node.js sample prevents a straightforward start unless the builder changes language or swaps ODM. |
| Target service and tier | specified | no | skill_md: 'A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable ... DOCUMENTDB_URI env var' | - | - | Run environment explicitly points to the live cluster and database to use. |
| Authentication and secrets | covered_by_skill | no | skill_md: 'connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment ... Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder.' | documentdb-connection | Store DocumentDB URI and LLM/embedding keys in environment variables; do not commit secrets. | documentdb-connection and the run-environment guidance cover TLS, SCRAM-SHA-256 and env-driven config. |
| Data model | ambiguous | no | 'look up the patient's active prescriptions ... create a refill request document' but no schema fields are enumerated | documentdb-data-modeling | Builder will define a minimal schema: prescriptions collection with patientId, drugName, daysSupply, refillCount, lastFilledAt, active (bool), prescriptionId; refillRequests collection with patientId, prescriptionId, requestedAt, status. | Data-modeling skill gives guidance (embed vs reference, schemaVersion) but the prompt does not specify exact document shapes or relationships. |
| Sample data | missing | no | - | - | Create a small synthetic seed dataset (a few patients with 1–5 prescriptions each) loaded by an idempotent seed script. | Prompt/skills do not specify source/size/licence. skill_md suggests seeding and verifying against the live cluster but gives no concrete sample set. |
| Queries and indexes | ambiguous | no | 'look up the patient's active prescriptions' and eligibility checks (days supply remaining, refill count) indicate query patterns but do not list indexes | documentdb-indexing | Create indexes on prescriptions(patientId, active) and prescriptions(prescriptionId) and on refillRequests(patientId, requestedAt). If vector search will be used for fuzzy medication match, create a vector index whose dims match the chosen embedding model. | Indexing guidance is available from the installed skill, but the exact indexes and their parameters are not specified. |
| AI components | missing | no | 'LangChain agent' and 'agent memory' are requested but no LLM/embedding models or providers are named | documentdb-vector-search | Builder will pick a commonly used provider (e.g., OpenAI or local LLM via environment-configured key) for chat and embeddings; embeddings model chosen to match vector-index dims (e.g., text-embedding-3-small → 1536 dims). Agent memory will be LangChain's conversation memory backed by a small collection or in-process store. | The prompt does not name a chat model, embedding model, or where to call them; the vector-search skill can guide index creation once model dims are chosen. |
| App surface | ambiguous | no | 'LangChain agent' (conversational) but no API/CLI/UI specified | - | Implement a minimal HTTP API (Express) with a /chat endpoint that proxies user messages to the LangChain agent; include a simple CLI script for local prompts. | Prompt requires conversational behavior but does not constrain delivery format. |
| Provisioning and deployment | specified | no | skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable ... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use.' | documentdb-azure-deployment | No new cloud resources will be provisioned; use live cluster described in skill_md. | Provisioning skill exists if needed, but run-environment explicitly instructs to use the existing cluster. |
| Run and test instructions | missing | no | - | - | README will include `npm install`, `.env` setup instructions, `npm run seed` to load sample data, and `npm start` to run the API. Tests: unit tests for eligibility logic and mocked DB tests; integration tests optional against live cluster and run separately. | The prompt/skills suggest verification steps but do not give explicit commands or test harnesses. |
| Definition of done | ambiguous | no | 'look up... check eligibility... create refill request... agent memory so follow-ups resolve the drug' describes behavior but no explicit acceptance criteria or testable artifacts are provided | - | Definition of done: agent can accept an initial request naming a medication, create a refill request in the DB when eligible, and respond to a follow-up 'refill my blood pressure medication' resolving to the previous prescription and creating a refill request when eligible. | Functional behavior is described but needs measurable tests. |
| Constraints and non-goals | ambiguous | no | skill_md: 'Never write the connection string into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder' and 'Do not provision another cluster...' | documentdb-security | Keep secrets out of the repo, don't provision new clusters, avoid storing PHI in public repos; make clear the sample is for demo purposes only, not production-ready for PHI. | Security & run-environment constraints exist but general cost or compliance limits are not spelled out in the prompt. |
| Repository conventions | missing | no | - | - | Use a simple Node.js layout: src/, scripts/seed.js, README.md, .env.example, package.json with pinned versions (lockfile), and tests/ with unit tests. Include instructions and attribution to 'Azure DocumentDB'. | Prompt does not prescribe folder layout, README sections, or dependency-pinning conventions. |
