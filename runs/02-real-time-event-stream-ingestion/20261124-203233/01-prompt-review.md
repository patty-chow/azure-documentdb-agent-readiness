# 1. Prompt review: 02-real-time-event-stream-ingestion

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core goals: a Node.js ingestion service that batches and unordered-bulk-writes customer events, uses a composite unique index (customerId, eventId) for dedupe, and opens a change stream to trigger downstream profile updates. Many implementation details are unspecified (API surface, driver version, batch size, seed/test/README/infra), but installed skills (driver/connection/indexing/local-deployment) cover the most important technical defaults so a builder can start. Several repository & QA items from the reference requirements are at risk and will be decided by the implementer unless the author clarifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Queries and indexes |
| Covered by a skill | 1: Repository conventions |
| Ambiguous: builder will guess | 3: Driver and version, Data model, App surface |
| Missing: builder will guess | 6: Workflow type, Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — prompt/skills do not explicitly require the sample to include a complete .env.example; the builder may add one but it's not mandated.
- The vector index dimensions match the embedding model's output — the starter prompt does not mention vectors/embeddings; this item from the reference is likely not implemented.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — not addressed by the prompt/skills; at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt doesn't require a seed script; although local-deployment skill suggests patterns, the builder may or may not implement an idempotent seed.
- /search returns a clear error for an empty query and when the embedding call fails — search endpoints are not requested by the prompt; at risk.
- Search results include the similarity score — no search or embedding features are requested; at risk.
- Dependencies are pinned in `requirements.txt` — this is a Node.js sample (package.json), but the reference expects pinned deps; the prompt doesn't require pinning or a lockfile explicitly, so this requirement is at risk.
- Unit tests run without a live cluster — the prompt doesn't require offline-capable unit tests or mocks; builder may not implement mocked tests by default.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt specifically assumes an existing cluster and does not request infra code; this requirement is at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a full README; builder may add one, but it's not specified.

## Questions for the prompt author

- Which transport should the ingestion service use? (HTTP REST endpoint like POST /events is the assumed default; or do you want a consumer for a message broker / Kafka?)
- Preferred behavior when a duplicate (customerId,eventId) is received: ignore the duplicate, update the existing event, or upsert? This affects bulkWrite operation choices and error handling.
- Batching policy: what default batch size and max latency should the sample use (e.g., batch size 500 / flush every 1s)?
- How should the change-stream 'downstream profile update job' be represented in the sample: a logged message, an in-process handler that updates a 'profiles' collection, or enqueuing to an external queue (and if external, which one)?
- Do you require infra-as-code (Bicep/Terraform) for the cluster in the repo, or should the sample explicitly avoid provisioning and rely on the provided cluster?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | “build a Node.js event ingestion service that receives customer behavioural events (page views, clicks, purchases) and bulk-writes them to DocumentDB using unordered bulk operations for throughput. Use a composite unique index on (customerId, eventId) for deduplication. Open a change stream to trigger downstream profile update jobs.” | - | - | Business problem and what the sample demonstrates are explicit. |
| Workflow type | missing | no | - | - | Implement as a standalone code sample (no multi-agent orchestration). The coding agent will produce a single-agent build script / standalone Node.js service. | Prompt doesn't state whether this is an agent-driven workflow or should integrate with a particular orchestrator; this does not prevent implementation but affects packaging and tests. |
| Language and runtime | specified | no | skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js is specified in the prompt and skill_md supplies Node 24 as the run environment. |
| Driver and version | ambiguous | no | - | - | Use the official npm 'mongodb' driver (current stable compatible with MongoDB 7.0 and Node.js 24). The implementer will pick a recent major release (e.g., mongodb >=5.x / compatible with Node 24) and record it in package.json. | Installed 'documentdb-driver' skill gives driver best-practices (singleton client, pooling) but does not mandate a driver package name + version; the builder will choose a sensible current mongodb driver. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... DOCUMENTDB_URI environment variable." | - | - | Run environment indicates an existing live Azure DocumentDB cluster (M30, MongoDB 7.0). Builder should NOT provision another cluster. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or .env.example with a placeholder, as the prompt asks." | - | - | Secrets come from env; skill_md explicitly enforces this. |
| Data model | ambiguous | no | Prompt: "customer behavioural events (page views, clicks, purchases)" and index requirement "(customerId, eventId)". skill_md: use database 'sample_customer_360_02'. | documentdb-data-modeling | Create a database 'sample_customer_360_02' and an 'events' collection. Each event document will include at least: { customerId: string, eventId: string, eventType: string, timestamp: ISODate, payload: object }. Use the composite unique index on (customerId, eventId) to dedupe inserts. | Prompt requires dedupe index but does not define collection name or full document shape; data-modeling skill provides guidance (16 MB limit, embed vs reference) but not the exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Include a simple idempotent seed script (e.g., node scripts/seed.js) that inserts a small set of events (hundreds at most) into the events collection using upserts or honoring the unique index so repeated runs don't duplicate data. | Prompt doesn't request example data or a seed script; local-deployment skill suggests patterns but does not supply actual sample data. |
| Queries and indexes | specified | no | Prompt: "Use a composite unique index on (customerId, eventId) for deduplication." Also: "bulk-writes ... unordered bulk operations". | documentdb-indexing | - | Index shape is explicit. Documentdb-indexing skill gives index-type guidance and best practices. |
| AI components | not_applicable | no | - | - | - | No embedding / LLM components are requested. |
| App surface | ambiguous | no | Prompt: "event ingestion service that receives customer behavioural events..." (no transport specified). | - | Implement as an HTTP REST service (Express) exposing POST /events (accepts single event or array). Provide a small CLI script to run the seed and a /health or /metrics endpoint. Make batch size and flush interval configurable through env variables. | The wording 'receives' implies an API but does not mandate HTTP vs message bus; HTTP is the most likely default for a sample app. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not provision new cloud infrastructure. Use the existing cluster pointed to by DOCUMENTDB_URI. Optionally include a commented example Bicep/az CLI snippet in README, but do not run provisioning in the sample. | Prompt and skill_md explicitly say a cluster is already reachable; the sample should not create infrastructure by default. |
| Run and test instructions | missing | no | skill_md provides environment details but no command list. | - | README will include common commands: npm install, cp .env.example .env (fill DOCUMENTDB_URI), npm run seed, npm start, and npm test. Tests will be limited unless the author asks for offline mocks. | Exact commands and expected outcomes are not specified; builder will add typical instructions. |
| Definition of done | missing | no | - | - | Acceptance: service starts, accepts events, writes them in unordered bulk to the events collection, composite index exists, duplicates are not inserted due to unique index, and change stream events trigger a demonstrable downstream job (e.g., logged or enqueued). | Prompt gives intent but no explicit acceptance criteria. |
| Constraints and non-goals | missing | no | - | - | Treat this as a sample / demo (not production): no provisioning of live clusters, minimal observability, no PII-sensitive data, and keep data volume small to avoid costs. | No cost limits or explicit non-goals are provided; builder will adopt conservative defaults. |
| Repository conventions | covered_by_skill | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder... Use the database named `sample_customer_360_02`." | documentdb-local-deployment | Follow usual sample conventions: package.json, src/, scripts/, .env.example, README.md, scripts/seed.js, tests/ with mocks. Do not check real credentials into repo. | Local-deployment and skill_md already instruct env-driven configuration and placeholder .env usage. |
