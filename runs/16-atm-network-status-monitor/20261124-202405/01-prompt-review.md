# 1. Prompt review: 16-atm-network-status-monitor

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core goal (Node.js Mongoose app that writes heartbeats, consumes a change stream, updates a live summary doc, and triggers thresholded alerts). The run environment (Node 24, live Azure DocumentDB cluster, DOCUMENTDB_URI env var) is provided in the skill_md, so a build can start. Several implementation details are left to the builder (HTTP API shape, exact Mongoose/driver versions, document schemas, indexes, seed data and tests); these will be filled by installed skills or sensible defaults during the build.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Repository conventions |
| Ambiguous: builder will guess | 5: Workflow type, Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — skill_md suggests using .env.example but the starter prompt does not require enumerating all settings; the builder must create this file.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the prompt does not specify sample-data loading or idempotency, so this is likely to be added by assumption rather than specified.
- Dependencies are pinned in requirements.txt — the prompt does not require pinned dependency versions, and Node samples need package-lock.json / pinned versions; the builder must decide how to pin dependencies.
- Unit tests run without a live cluster — the prompt does not mention tests or mocking strategy; creating tests that run offline (using mongodb-memory-server or mocks) is not covered and is at risk.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type — run environment already provides a cluster and the prompt does not ask to include IaC, so an IaC template may be omitted.

## Questions for the prompt author

- How should heartbeats be received: expose an HTTP POST endpoint (e.g., POST /heartbeat), accept messages from a message broker, or simulate ingestion in the seed script? This changes app surface and examples.
- When an alert is triggered, do you want a persistent alert document written to the database (recommended for the sample), a log entry, or an external notification (email/SMS/Webhook)?
- What default availability threshold should be used if the environment variable is absent (e.g., 0.95 = 95%)?
- How large should the sample dataset be (number of ATMs) to include in the seed script for demonstrations?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" (singular). There is no single installed skill named exactly "DocumentDB"; functionality is split across multiple documentdb-* skills. Builder will need to pick which skills to consult.
- Reference checklist mentions "dependencies are pinned in requirements.txt" (Python centric), but this sample is Node.js where dependencies are recorded in package.json / package-lock.json — mismatch in wording but not fatal.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose ATM monitor that receives status heartbeat documents from ATMs and writes them to DocumentDB. Open a change stream to detect status changes (online, offline, low cash), maintain a live network summary document, and trigger alerts when availability drops below a configurable threshold." | - | - | The functional objective and what to demonstrate are explicit and actionable. |
| Workflow type | ambiguous | no | "build a Node.js Mongoose ATM monitor... receives status heartbeat documents... Open a change stream..." (no agent framework mentioned) | - | Implement as a single-process Node.js service (no multi-agent/orchestration framework). Change-stream listener + HTTP API run in the same process. | Prompt does not specify an agent framework; the obvious default is a single Node service. |
| Language and runtime | specified | no | Prompt: "Node.js Mongoose". skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js 24 is stated in the provided run environment (skill_md). |
| Driver and version | ambiguous | no | Prompt: "Mongoose" (no version specified). | documentdb-driver | Use a modern Mongoose release compatible with Node 24 (e.g., Mongoose 7.x) and the mongodb driver version that Mongoose installs; follow documentdb-driver advice for singleton client/connection reuse. | Mongoose is specified but no version range was given. documentdb-driver covers connection best-practices but does not pick a Mongoose version. |
| Target service and tier | specified | no | Prompt: "DocumentDB". skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable... connection string in DOCUMENTDB_URI." | - | - | The run environment specifies the live cluster characteristics to use. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or .env.example with a placeholder, as the prompt asks." | - | - | Where the connection string lives is explicit in the run environment. |
| Data model | ambiguous | no | Prompt: "heartbeat documents... live network summary document... trigger alerts..." (no schema given). | documentdb-data-modeling | Define heartbeat documents with fields like { atmId: String, timestamp: Date, status: 'online'\|'offline'\|'low_cash', cashLevel: Number, meta: {...} }. Summary is a single document keyed e.g. { _id: 'network_summary', counts: { online: N, offline: M, low_cash: K }, availability: 0.95, lastUpdated: Date }. Alerts written to an alerts collection with timestamp and reason. | Prompt names the logical documents but not concrete fields or types; the data-modeling skill will guide choices but the builder must pick a schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Create a seed script that inserts a modest set of sample ATMs (e.g., 20–100) and a few initial heartbeat documents; implement idempotent upsert behavior so the script can be re-run without duplication. | Starter prompt does not specify a seed dataset or loading mechanism; a seed script will need to be added by the builder. |
| Queries and indexes | ambiguous | no | Prompt implies change-stream and summary updates but does not name indexes. | documentdb-indexing | Create indexes that support expected patterns: e.g., heartbeat collection - index on { atmId: 1, timestamp: -1 } for latest-per-ATM lookups; index on status if queries filter by status; possibly a TTL index for very old heartbeat retention. The summary is a single doc (no index required). | Index design is not specified; use documentdb-indexing guidance to choose sensible defaults. |
| AI components | not_applicable | no | - | - | - | No embeddings or LLMs are required by the prompt. |
| App surface | ambiguous | no | Prompt: "receives status heartbeat documents from ATMs" (transport not specified), plus change-stream consumer and summary document. | - | Implement an Express HTTP API with POST /heartbeat to accept heartbeat JSON, and GET /summary to return the current network summary; the same process runs a change-stream cursor that updates the summary and writes alert documents. | The prompt requires ingestion but does not state whether by HTTP, message queue, or other transport — HTTP is the usual sample default. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | Do not provision infrastructure in the sample run; use the existing cluster referenced by DOCUMENTDB_URI. | An IaC skill exists but run environment forbids provisioning for this run. |
| Run and test instructions | missing | no | - | - | Provide README commands: npm install, copy .env.example -> .env (set DOCUMENTDB_URI and THRESHOLD), npm run seed, npm start (or node index.js), and npm test. Use an in-memory MongoDB (mongodb-memory-server) or mocks so unit tests run without a live cluster. | Prompt doesn't include concrete run/test commands; builder will need to add them. |
| Definition of done | missing | no | - | - | Accept when: POST /heartbeat stores heartbeat docs; change-stream listener updates the network summary doc correctly on status changes; availability metric computed and stored; an alert document is written when availability < configured threshold; seed script runs idempotently; README documents steps. | No explicit acceptance criteria in the prompt; use the functional behaviors as the testable definition. |
| Constraints and non-goals | missing | no | - | documentdb-security | Treat this as a developer-focused sample: do not implement production-grade multi-region HA, CMK, or enterprise integration. Do not provision new clusters during the sample run; follow security guidance to avoid leaking credentials. | No cost/scale constraints or non-goals were given; sensible limits should be documented in the README. |
| Repository conventions | covered_by_skill | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | documentdb-local-deployment | Follow standard Node repo layout: package.json, src/, test/, scripts (seed/start/test), .env.example with placeholders, README.md. | The run environment explicitly instructs use of .env.example and not storing secrets in repo; local-deployment skill covers dev environment conventions. |
