# 1. Prompt review: 08-insurance-pre-auth-multi-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the goal (Node.js + LangChain multi-agent orchestrator reading and writing Azure DocumentDB) so a builder can start. Many implementation details are unspecified (LLM provider/models, exact DB schema, API surface, seed data, indexing, infra code, tests, and README) and will be chosen by the builder or filled in from the provided run-environment notes and installed DocumentDB skills.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 4: Language and runtime, Driver and version, Target service and tier, Authentication and secrets |
| Ambiguous: builder will guess | 3: Data model, Queries and indexes, App surface |
| Missing: builder will guess | 7: Sample data, AI components, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Model credentials come from environment variables: prompt/skills only specify DOCUMENTDB_URI; model credential handling (provider and env variable names) is not specified.
- A .env.example lists every setting with placeholder values: run environment suggests using .env.example for the DocumentDB URI but does not list all required settings (LLM keys, model names, etc.).
- Vector index dimensions match the embedding model's output: embedding model and dimensions are not specified anywhere, so the vector-index dimensions cannot be guaranteed.
- Vector index parameters chosen for the sample's data size and README explains how to change them: index parameters and README guidance are not provided by the prompt or installed skills.
- A seed script loads sample data and creates the index idempotently: the prompt does not request a seed script; installed skills mention sample-data management but do not supply a ready seed script for this sample.
- /search returns a clear error for an empty query and when the embedding call fails: prompt doesn't define a search API or error behavior.
- Search results include the similarity score: search behavior is unspecified.
- Dependencies are pinned in requirements.txt (or equivalent for Node): the prompt doesn't state how dependency versions are pinned or where; gallery checklist expects pinned deps.
- Unit tests run without a live cluster: tests and mocking strategy are not described.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type: prompt assumes an existing cluster and does not request IaC.
- README covers what the sample shows, prerequisites, setup, run, and clean-up: prompt does not request README contents; this must be added by the builder.

## Questions for the prompt author

- Which LLM provider and model names should the sample use for the chat agents and embeddings (OpenAI, Azure OpenAI, other)?
- Do you want infrastructure-as-code for the Azure DocumentDB cluster included in the repo (Bicep/Terraform) or should the sample assume the pre-provisioned cluster described in the run environment?
- Should the sample expose a REST endpoint for demoing the orchestrator, or is a CLI/script-based demo sufficient?
- Do you want the sample to demonstrate vector/embedding-based retrieval of clinical criteria, or simple keyword/text matching from DocumentDB?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill"; instead multiple documentdb-* skills are installed. The builder will need to pick which documentdb-* skills to consult.
- Reference requirements mention `requirements.txt` (Python style) while the sample is requested in Node.js; this is a mismatch between the gallery's checklist and the requested runtime.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js LangChain multi-agent system where an orchestrator reads a pre-auth request from DocumentDB, passes it to a medical-review agent that checks clinical necessity against stored criteria, then to an insurer-comms agent that drafts the submission letter. Store the final submission document and status back in DocumentDB. | - | - | - |
| Workflow type | specified | no | multi-agent system ... an orchestrator ... medical-review agent ... insurer-comms agent; LangChain | - | - | Prompt explicitly requests LangChain multi-agent orchestration. |
| Language and runtime | covered_by_skill | no | Node.js | run environment (skill_md) | - | Run environment block (provided with the prompt) states Node.js 24 is available on the developer machine; use that. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Builder will use the official MongoDB Node.js driver (mongodb) pinned to a current v5.x release compatible with MongoDB 7.0 (e.g., "mongodb >=5.0 <6.0"). | Installed documentdb-driver skill provides guidance (singleton MongoClient, connection reuse). |
| Target service and tier | covered_by_skill | no | DocumentDB | run environment (skill_md) | - | Run environment explicitly says a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF) is reachable and DOCUMENTDB_URI env var points at it. |
| Authentication and secrets | covered_by_skill | no | - | run environment (skill_md) | - | Run environment instructs reading the connection string from DOCUMENTDB_URI env var and not writing it into files; also suggests .env.example placeholder approach. |
| Data model | ambiguous | no | pre-auth request, clinical-necessity criteria, final submission document and status stored in DocumentDB | documentdb-data-modeling | Builder will create three collections: `preauth_requests` (fields: _id, patientId, clinician, requestedProcedureCodes, clinicalNotes, submittedAt, status), `clinical_criteria` (fields: _id, procedureCode, criteriaText, severityTags, lastUpdated), and `submissions` (fields: _id, preauthId, submissionDocument, outcome, submittedAt). No explicit shard key; small sample stays single-shard. | The prompt names the entities but does not define document shapes, relationships, or shards; documentdb-data-modeling skill can guide choices. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a seed script that inserts a small, non-PHI sample dataset: e.g., 3 pre-auth requests and ~5 clinical_criteria documents. Seed script idempotent (upsert by natural key) so it can be run multiple times without duplication. | Starter prompt does not describe sample data source, size, or licensing. documentdb-local-deployment mentions sample-data management but not a named dataset. |
| Queries and indexes | ambiguous | no | medical-review agent reads clinical-necessity criteria stored in DocumentDB and checks the pre-auth request | documentdb-indexing | Create indexes appropriate for the sample: single-field indexes on `_id` and `patientId`, an index on `status` for quick lookups, and a text index on clinical_criteria.criteriaText for keyword lookup. If embeddings are used for criteria retrieval, create a vector index sized to the chosen embedding dimension (see AI components assumption). | Prompt does not state exact query patterns or index shapes; documentdb-indexing can guide index choices but the builder will pick specifics. |
| AI components | missing | no | LangChain multi-agent system (medical-review agent, insurer-comms agent) | - | Builder will pick an LLM provider and models via environment variables. A plausible default: OpenAI-compatible models with env OPENAI_API_KEY; use a chat model (e.g., "gpt-4o-mini" or another available chat model) for agents and a small embedding model (e.g., "text-embedding-3-small") with embedding dimension assumed to be 1536. All model names and credentials are read from env and not checked into repo. | Prompt specifies LangChain but does not name provider, model names, embedding usage, or embedding dims; these are critical choices left to the implementer. |
| App surface | ambiguous | no | orchestrator reads a pre-auth request from DocumentDB and coordinates agents | - | Implement an orchestrator runnable as both a CLI script (e.g., `node src/run-orchestrator.js --id <preauthId>`) and a minimal Express demo API endpoint (e.g., POST /preauth/:id/process) that triggers the workflow for demonstration. Output logs to stdout and persist submission back to DB. | Prompt doesn't require a web UI or CLI explicitly; builder will choose an interface for demonstration. |
| Provisioning and deployment | missing | no | Using the DocumentDB skill, build ... on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable. | documentdb-azure-deployment | Do not include infrastructure provisioning in the sample; rely on the existing cluster described in the run environment. If the builder adds IaC, they will provide a Bicep template via the documentdb-azure-deployment skill, but the prompt does not request it. | The prompt explicitly says a cluster already exists; sample gallery requirements often expect IaC, but the starter prompt does not. |
| Run and test instructions | missing | no | - | - | Include a README with step-by-step commands: `npm install`, create `.env` from `.env.example`, `npm run seed` to load sample data, `npm start` to run the orchestrator or start demo server, and `npm test` for unit tests (tests should be runnable without a live cluster via mocks). | The prompt doesn't specify run commands or test expectations. |
| Definition of done | missing | no | - | - | Define acceptance as: orchestrator successfully reads a pre-auth request from the sample database, medical-review agent returns a clinical-necessity assessment using stored criteria, insurer-comms agent creates a submission document, and the final document and updated status are written back to the `submissions`/`preauth_requests` collection. Provide logs and a demo invocation that show end-to-end completion. | No explicit acceptance criteria are in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Document PHI handling and compliance are out of scope for the sample; include a clear README note that the sample is for demonstration only and should not be used with real PHI. Limit cloud provisioning to avoid extra cost; do not provision new clusters by default. | Security best-practices skill exists but the prompt does not state constraints or non-goals explicitly. |
| Repository conventions | missing | no | - | - | Use a conventional Node layout: src/, test/, scripts for seed and start, package.json with pinned dependencies (or package-lock.json), .env.example, README.md with sections (Overview, Prereqs, Setup, Run, Clean-up). | Starter prompt doesn't prescribe repository layout or naming conventions. |
