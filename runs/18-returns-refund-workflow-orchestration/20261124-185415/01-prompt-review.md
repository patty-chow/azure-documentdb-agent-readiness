# 1. Prompt review: 18-returns-refund-workflow-orchestration

**Verdict: sufficient_with_assumptions**

The starter prompt is actionable: it names Node.js + LangChain orchestration, three agents, fetching an order from Azure DocumentDB, and writing the final return document via Mongoose. Several important implementation details (LLM model choice, exact request/response API surface, precise document schema and agent output shapes, tests, and runtime dependency versions) are not specified and will be chosen by the builder or supplied skills. No single missing detail blocks a sensible start.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Workflow type |
| Covered by a skill | 3: Language and runtime, Target service and tier, Authentication and secrets |
| Ambiguous: builder will guess | 4: Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: Provisioning and deployment |

## Reference requirements at risk

- Policy agent must return structured result with eligibility (boolean) and eligibilityReason (string) — prompt does not require exact structured output; builder will decide.
- Refund agent must return numeric refundAmount (and optional breakdown) and be skipped when ineligible — prompt doesn't specify structure or skipping behavior in detail.
- Comms agent must generate structured customer notification including customer identifier, eligibility status, refundAmount (if any), eligibilityReason, messageBody and notificationChannel — prompt does not specify output schema.
- Persisted final return document must include orderId, status ('approved','rejected','error'), refundAmount (number, zero if rejected), timestamps, and raw agent outputs — prompt only says 'final return document' and Mongoose, not exact fields.
- The flow must return the final persisted return document as the API response — prompt asks to accept a return request and write back, but does not explicitly require returning the persisted document as the API response.
- Error handling: if order not found or any agent throws, code must write a return document with status 'error' and an error field, and API responds with that document — prompt does not specify error persistence or API error document behavior.
- Provide runnable tests or a demo script that exercises both an approved return path and a rejected return path and verifies final documents — prompt does not request tests or a demo script.
- Sample data: seed script, idempotent seed, and small dataset for both approved/rejected paths — prompt does not provide sample data or a seeding mechanism.
- Repository conventions: .env.example, README, pinned dependency versions, folder layout — prompt does not enumerate repo conventions or env placeholders.
- Unit tests that run without a live cluster — prompt does not specify whether tests should mock DocumentDB or use the live cluster; run environment indicates a live cluster is available but gallery requirement expects unit tests that can run offline.

## Questions for the prompt author

- Which LLM provider and model should the LangChain agents use in the sample (e.g., OpenAI gpt-4o-mini, gpt-4, or a local/mocked model)? This changes prompt templates, cost and the demo/test approach.
- Should the demo/tests call the real LLMs (requiring a live API key and incurring cost) or should tests mock agent responses so they run reliably without external calls?
- Do you prefer a small HTTP API (Express POST /returns) as the app surface, or something else (CLI script) for the sample's entrypoint and demo automation?
- Please confirm the required fields and exact names for the persisted return document (e.g., field names: orderId, status with allowed values 'approved'/'rejected'/'error', refundAmount (number), timestamps, policyResult/refundResult/commsResult raw outputs).

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no installed skill named exactly 'DocumentDB skill'. There are many documentdb-* skills (documentdb-driver, documentdb-data-modeling, etc.) and a supplied run-environment skill.md; the prompt likely means 'use the available DocumentDB skills / run environment'.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js LangChain orchestration flow that accepts a return request, passes the order document fetched from DocumentDB to a policy agent ... refund-calculation agent ... comms agent ... Write the final return document back to DocumentDB via Mongoose. | - | - | Business problem, target user (developer sample), and what to demonstrate (orchestration across agents + DocumentDB persistence) are clear. |
| Workflow type | specified | no | LangChain orchestration flow ... policy agent ... refund-calculation agent ... comms agent | - | - | Multi-agent orchestration (LangChain) is explicitly required. |
| Language and runtime | covered_by_skill | no | Node.js | run environment (skill.md) | - | The supplied run-environment info (skill.md) states Node.js 24 is available; use that. |
| Driver and version | ambiguous | no | Write the final return document back to DocumentDB via Mongoose. | documentdb-driver | Pick a current Mongoose release compatible with Node 24 and MongoDB 7.0 (e.g., Mongoose 7.x) and use the underlying mongodb driver as the client; follow `documentdb-driver` singleton-client pattern. | Prompt mandates Mongoose but gives no version. `documentdb-driver` skill supplies connection-pattern guidance (singleton MongoClient), but not exact package versions. |
| Target service and tier | covered_by_skill | no | DocumentDB | run environment (skill.md) | - | Run environment states a vector-capable Azure DocumentDB cluster (M30, MongoDB 7.0) is reachable and DOCUMENTDB_URI contains the connection string; build against that cluster. |
| Authentication and secrets | covered_by_skill | no | - | run environment (skill.md) | - | skill.md instructs the connection string is provided in env var DOCUMENTDB_URI and must not be written into files; this covers where secrets live. |
| Data model | ambiguous | no | passes the order document fetched from DocumentDB ... Write the final return document back to DocumentDB via Mongoose. | documentdb-data-modeling | Create database `sample_retail_18` (per run-env). Use collections `orders` (preexisting sample order documents) and `returns`. The return document will include orderId, status, refundAmount, timestamps, policyResult/refundResult/commsResult raw outputs and optionally schemaVersion. Embed related small fields; avoid large embedded arrays to stay under 16 MB. | The prompt requires reading an order and writing a return document but does not specify collection names or full shapes. The `documentdb-data-modeling` skill gives modeling principles but not the exact schema. |
| Sample data | missing | no | - | - | Provide a small seed script that inserts two sample orders into `orders` (one that should pass policy eligibility, one that should fail), so the demo/test can exercise both paths. | The prompt does not describe source, size, or loader for sample data; none of the installed skills supply a ready dataset for this sample. |
| Queries and indexes | ambiguous | no | fetches the order document from DocumentDB | documentdb-indexing | Create a simple unique index on `orderId` in `orders` and an index on `returns.orderId` and `createdAt`. No vector or full-text indexing is required for the returns orchestration sample unless search features are later added. | Prompt does not ask for explicit indexes. `documentdb-indexing` skill can advise, but exact indexes and parameters are unspecified. |
| AI components | missing | no | LangChain orchestration flow ... policy agent ... refund-calculation agent ... comms agent | - | Use an OpenAI-compatible chat model via LangChain (model selected by env var, e.g., OPENAI_MODEL=gpt-4o-mini) and place API key in OPENAI_API_KEY. Agent prompts and output schemas will be implemented in code (system+instruction templates) to produce structured JSON outputs. | Prompt requires LangChain agents but does not specify LLM provider, model, or embedding/chat models. This choice materially affects costs and prompt engineering. |
| App surface | ambiguous | no | accepts a return request ... Write the final return document back to DocumentDB via Mongoose. | - | Implement an Express-based HTTP API with POST /returns (body: { orderId, reason, requester }) that triggers the fetch + orchestration and responds with the persisted return document. | Prompt implies an input (return request) and a persistence step but does not say whether sample should be CLI, API, or UI. An API is the most likely choice for a sample. |
| Provisioning and deployment | not_applicable | no | Using the DocumentDB skill ... This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable. | documentdb-azure-deployment | - | Run environment explicitly provides a cluster to use. The prompt does not ask to provision resources; provisioning is intentionally out-of-scope for this sample run. |
| Run and test instructions | missing | no | - | - | Include npm scripts (install, start, seed, demo) and a demo/test script that runs two scenarios (approved and rejected) against the local API and verifies that Mongoose wrote the expected return documents. Tests may run against the live cluster or mock LLM calls (see question). | The prompt doesn't request README or exact commands or tests; the reference requirements expect runnable tests/demo scripts but the prompt is silent. |
| Definition of done | missing | no | - | - | Acceptance: POST /returns returns a persisted return document; policy/refund/comms agent outputs are included in saved document; approved path sets status 'approved' and refundAmount > 0; rejected path sets status 'rejected' and refundAmount = 0; error cases persist status 'error' with an error field. | Prompt does not enumerate exact acceptance criteria; builder will pick pragmatic checks as above. |
| Constraints and non-goals | missing | no | - | documentdb-security | Do not provision new cloud resources; do not store secrets in repository; keep usage of external LLMs limited in demo to avoid unexpected cost. Use TLS and the DOCUMENTDB_URI env var for auth. | No explicit cost, compliance or non-goal constraints given; reasonable assumptions must be applied. |
| Repository conventions | missing | no | - | - | Repo will include: README, src/, tests/, scripts/seed.js, .env.example, package.json with pinned versions (or an explicit minimal semver range), and a sample config loader that reads env vars (DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL). | Starter prompt does not mandate layout or files; typical gallery conventions should be followed. |
