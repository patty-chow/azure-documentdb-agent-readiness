# 1. Prompt review: 06-omnichannel-interaction-history

**Verdict: sufficient_with_assumptions**

The prompt clearly defines the core goal: a Node.js (Mongoose) service that stores omnichannel interaction documents in one DocumentDB collection, with two compound indexes and two endpoints (paginated history and channel-breakdown aggregation). The run environment (Node 24, a reachable Azure DocumentDB M30 cluster, and the required DB name and env var) is provided in the supplied skill_md, and several DocumentDB-focused skills are installed to fill implementation gaps. Several implementation details (Mongoose / driver versions, exact route signatures and pagination strategy, seed-data size and tests/CI, README/provisioning-as-code) are left to the builder's defaults and should be assumed before coding starts.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Data model, Queries and indexes |
| Covered by a skill | 2: Provisioning and deployment, Repository conventions |
| Ambiguous: builder will guess | 2: Driver and version, App surface |
| Missing: builder will guess | 5: Workflow type, Sample data, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- The vector index dimensions match the embedding model's output — the prompt doesn't use embeddings or vector indexes and no skill forces adding vector indexes, so this will likely be omitted.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — not applicable unless vector search is added; at risk of being omitted.
- /search returns a clear error for an empty query and when the embedding call fails — there is no /search or embedding in the prompt, so this error handling requirement will likely be missing.
- Search results include the similarity score — not relevant to this sample and likely omitted.
- Dependencies are pinned in requirements.txt — Node samples use package.json; the reference's requirement (requirements.txt) is Python-specific and therefore at risk / misaligned.
- Unit tests run without a live cluster — the prompt doesn't require tests or mocking; many builders will not include offline-capable unit tests unless asked explicitly.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the run environment already provides a cluster; the prompt does not request creating infra-as-code, so this requirement is at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't request README details; builders often include one but completeness is not guaranteed.

## Questions for the prompt author

- Which pagination style do you want for the history endpoint: offset-based (limit/skip) or cursor-based (timestamp + _id)? This will change the API and implementation.
- Do you want explicit route names and query parameter conventions (e.g. GET /interactions/history?customerId=...&limit=...&cursor=...) or should the implementer choose reasonable defaults?
- Should the repo include an idempotent seed script and small synthetic dataset, or will the environment already contain data to exercise the endpoints?
- Do you require pinned dependency versions (package-lock.json / pinned semver) and unit tests that run offline (mocked Mongo) for CI?

## Contradictions and missing references

- The prompt says "Using the DocumentDB skill" (singular) but no single skill named exactly "DocumentDB" is installed; instead multiple documentdb-* skills are available. This is not blocking but ambiguous about which skill the builder should invoke.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose service that stores customer interaction documents from all channels... Create compound indexes on (customerId, timestamp) and (channel, timestamp)... Expose paginated history and channel-breakdown aggregation endpoints." | - | - | Business problem, dataset and demonstrated DB features are explicit. |
| Workflow type | missing | no | - | - | Treat as a normal single-process web service (no multi-agent orchestration). The sample is a standalone REST API implemented and run locally/locally against the live cluster. | Prompt references using the DocumentDB skill for the builder, but does not require any agent runtime for the sample itself. |
| Language and runtime | specified | no | "Node.js Mongoose service" and skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js chosen; Node 24 is provided by the run environment in skill_md. |
| Driver and version | ambiguous | no | "Mongoose" (no version specified) | documentdb-driver | Use current stable Mongoose v7.x (compatible with MongoDB 7.0 wire protocol) and the driver versions Mongoose brings; ensure compatibility with MongoDB 7.0. | Prompt names Mongoose but leaves version choice to the builder; documentdb-driver skill will guide best practices but not pick exact package version. |
| Target service and tier | specified | no | - | - | Run against the already-provisioned, reachable Azure DocumentDB cluster described in skill_md (compute tier M30, MongoDB 7.0 wire protocol). Use the provided DATABASE name sample_customer_360_06. | The supplied skill_md run environment states the target cluster and DB to use. |
| Authentication and secrets | specified | no | - | - | Read the connection string from the environment variable DOCUMENTDB_URI at runtime and never commit the secret to the repo; provide a .env.example with a placeholder. | This is prescribed in the run environment (skill_md). |
| Data model | specified | no | "single DocumentDB collection with channel, customerId, and timestamp fields"; "one Mongoose schema and model" | documentdb-data-modeling | Schema will include channel (string/enumeration), customerId (string or ObjectId), timestamp (Date/ISO), plus a free-form payload field for channel-specific content. | Prompt explicitly requires the single collection and fields; data-modeling skill can guide embedding/size constraints. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small seed file (JSON) with a few dozen interaction documents across web, mobile, email, call_center and a seed script (npm run seed) to idempotently insert or upsert data for manual testing. | Prompt doesn't say where sample data comes from or its size; builder will supply a small synthetic seed dataset. |
| Queries and indexes | specified | no | "Create compound indexes on (customerId, timestamp) and (channel, timestamp)" and endpoints for paginated history and channel-breakdown aggregation | documentdb-indexing | Declare schema.index({ customerId: 1, timestamp: -1 }) and schema.index({ channel: 1, timestamp: -1 }) and ensure indexes are created at startup (autoIndex or explicit syncIndexes/createIndexes). | Prompt requires index declarations in application code and query patterns are clear. |
| AI components | not_applicable | no | - | - | No embedding or LLM components are required for this sample. | Sample focuses on storage and aggregation, not RAG/vector/semantic search. |
| App surface | ambiguous | no | "Expose paginated history and channel-breakdown aggregation endpoints" (no routes/methods/pagination model specified) | - | Implement a simple REST API (Express) with routes such as GET /interactions/history?customerId=<>&limit=<>&cursor=<>, and GET /interactions/channel-breakdown[?customerId=<>]. Use cursor (timestamp + _id) or offset-based pagination with limit & skip; prefer cursor (timestamp) for correctness. | Route names, HTTP methods, pagination strategy and query parameter names are left to the implementer. |
| Provisioning and deployment | covered_by_skill | no | - | documentdb-azure-deployment | Do not provision a new cluster; the run environment's cluster should be used. If provisioning is required, use the documentdb-azure-deployment skill (Bicep/az CLI) and avoid creating resources by default. | Prompt assumes an existing cluster; the deployment skill exists if infra-as-code is later requested. |
| Run and test instructions | missing | no | - | - | Provide standard README run steps: npm install, cp .env.example .env (set DOCUMENTDB_URI), npm run seed, npm start; tests run via npm test (if provided). | Prompt does not include commands or expected outputs. |
| Definition of done | missing | no | - | - | Accept when the service starts, indexes are created on the specified DB, sample data is loaded, and the two endpoints return expected results (paginated customer history, and channel counts). | No explicit acceptance criteria were provided in the starter prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep sample small and inexpensive: do not provision new cloud resources; avoid production security features beyond TLS / env-based secrets in the README; note that production HA/CMK are out of scope. | No cost, resource or compliance constraints were specified. |
| Repository conventions | covered_by_skill | no | - | documentdb-local-deployment | Include a .env.example (placeholder for DOCUMENTDB_URI), package.json with scripts (start, seed, test), README, and avoid committing secrets. Single Mongo client singleton pattern per documentdb-driver guidance. | The run environment (skill_md) instructs not to write the real connection string and to use .env.example; installed skills recommend single-client reuse and seed patterns. |
