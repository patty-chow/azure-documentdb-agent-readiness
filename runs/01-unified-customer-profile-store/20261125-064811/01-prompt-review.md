# 1. Prompt review: 01-unified-customer-profile-store

**Verdict: sufficient_with_assumptions**

The prompt clearly states the goal (Node.js/Mongoose service to upsert multi-source customer events into a canonical DocumentDB document keyed by customerId) and the key implementation constraints (nested sub-documents per source and merging via $set). The provided skill.md fills important environment details (live DocumentDB cluster, DOCUMENTDB_URI env var, DB name, Node.js 24). Several practical details are left to the builder (HTTP vs handler, Mongoose/driver versions, indexes, seed data, tests, README), so the build can start but will rely on reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Data model |
| Covered by a skill | 5: Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment, Constraints and non-goals |
| Ambiguous: builder will guess | 6: Workflow type, Driver and version, App surface, Run and test instructions, Definition of done, Repository conventions |
| Missing: builder will guess | 2: Sample data, Queries and indexes |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values (skill.md suggests a .env.example but does not enumerate all settings like PORT or NODE_ENV).
- The vector index dimensions match the embedding model's output (not applicable/unspecified; no embedding model is used or mentioned).
- The vector index parameters are chosen for the sample's data size and the README explains how to change them (not specified; sample likely won't include vector indexing decisions).
- One database client is created and reused across requests (skill.md does not mandate or supply code; builder must implement it).
- A seed script loads sample data and creates the index and can be run twice without duplicating data (prompt doesn't require a seed script; skill.md asks verification but no idempotent seed is provided).
- /search returns a clear error for an empty query and when the embedding call fails (search/embedding not part of this sample; requirement not covered).
- Search results include the similarity score (not applicable; no search/embedding component is defined).
- Dependencies are pinned in requirements.txt (Python-specific; for Node, package.json should pin versions—this is not specified).
- Unit tests run without a live cluster (no guidance provided on test strategy or mocking the DB).
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type (skill.md explicitly says a cluster already exists and forbids provisioning; infra-as-code is not provided).
- The README covers what the sample shows, prerequisites, setup, run, and clean-up (README content is not specified; builder will likely add one but details are not enforced).

## Questions for the prompt author

- Should the sample expose an HTTP endpoint (e.g. POST /events) or an exported handler function (e.g. for serverless)? This choice will change dependencies and example usage.
- Do you want a specific Mongoose (or MongoDB driver) version pinned, or should the builder use the latest compatible release with Node.js 24?
- Should the sample include a seed script and sample data, and if so, how many example events are desired (a few hand-crafted events are typical)?
- Is a unique index on customerId required (recommended) and should the sample create it during initialization/seed?

## Contradictions and missing references

- Prompt asks to use the 'DocumentDB skill' but no agent skills are installed. There is a provided skill.md with environment details, but it is not an installed agent skill as referenced by the prompt.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose service that receives customer events from multiple source systems (CRM, e-commerce, support) and upserts them into a canonical customer profile document in DocumentDB." | - | - | Business problem and what to demonstrate are explicit. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" | - | Implement as a simple no-agent sample: a standalone Node.js service (no multi-agent/orchestration framework). | Prompt references a 'DocumentDB skill' but does not specify an agent workflow or framework. |
| Language and runtime | covered_by_skill | no | "Node.js Mongoose service" | skill.md | Use Node.js 24 (available per skill.md) as the runtime. | Prompt names Node.js; skill.md documents Node.js 24 availability. |
| Driver and version | ambiguous | no | "Mongoose" | - | Use a recent stable Mongoose compatible with Node 24 (e.g. latest 7.x release) and let Mongoose manage the underlying MongoDB driver. | Prompt specifies Mongoose but not a version; no installed skill pins versions. |
| Target service and tier | covered_by_skill | no | "DocumentDB" | skill.md | Use the live, reachable Azure DocumentDB cluster described in skill.md (compute tier M30, MongoDB 7.0 wire protocol). | skill.md provides the cluster and database name to use. |
| Authentication and secrets | covered_by_skill | no | - | skill.md | Read connection string at runtime from DOCUMENTDB_URI environment variable; avoid writing it into files or logs; provide .env.example with placeholder. | skill.md explicitly instructs how to obtain and treat the connection string. |
| Data model | specified | no | "Use a stable customerId for identity resolution and model nested sub-documents for each source system's attributes" | - | Create Mongoose schema with top-level customerId and nested sub-documents crm, ecommerce, support. | Prompt specifies canonical profile, stable customerId, and source sub-documents and merging via $set. |
| Sample data | missing | no | - | skill.md | Provide a minimal seed JSON containing a handful (2–5) of example events (CRM, ecommerce, support) and a seed script that upserts them. | Neither prompt nor skill.md provides example data, sizes, or explicit seed script; builder will likely create small hand-crafted sample events. |
| Queries and indexes | missing | no | "identity resolution matches ... customerId" (implied query pattern) | skill.md | Create a (unique) index on customerId and use findOneAndUpdate/updateOne with filter { customerId } and upsert:true; no vector/full-text indexes needed for this sample. | Prompt states filter by customerId but does not request an index to support it; skill.md documents DB but not indexes to create. |
| AI components | not_applicable | no | - | - | - | The sample has no embedding or chat model requirements. |
| App surface | ambiguous | no | "an HTTP endpoint or an exported handler function" (example) | - | Implement an HTTP API (Express) with POST /events that accepts JSON events { source, customerId, attributes } and responds with the upsert result. | Prompt suggests either an HTTP endpoint or exported handler; absent explicit choice, an HTTP endpoint is the most likely default. |
| Provisioning and deployment | covered_by_skill | no | - | skill.md | Do not provision a new cluster; use the existing cluster per skill.md. No infra provisioning is required for the sample. | skill.md explicitly forbids provisioning another cluster and directs use of the provided one. |
| Run and test instructions | ambiguous | no | - | skill.md | Provide npm scripts (start, seed, test). Example commands: npm install, npm run seed, npm start, and simple curl commands to exercise the endpoint. | skill.md requests verification steps (create collections/indexes, load sample data, run queries) but does not provide exact commands; builder will add README and npm scripts. |
| Definition of done | ambiguous | no | - | skill.md | Consider done when the service upserts events by customerId, nested sub-documents are merged using $set, sample data is loaded, and verification queries show expected results against the specified database. | Prompt implies the acceptance criteria but does not enumerate a checklist; skill.md's verification guidance partly fills the gap. |
| Constraints and non-goals | covered_by_skill | no | "...upserts ... merging with $set to avoid overwriting unrelated fields." | skill.md | Do not write secrets to files/logs; do not provision clusters; prefer minimal, local sample infra. | skill.md provides operational constraints (use provided cluster, do not write URI into artifacts). Cost limits and other non-goals are not detailed. |
| Repository conventions | ambiguous | no | - | skill.md | Include typical Node repo layout (package.json, src/, README.md, .env.example) and a .env.example listing at least DOCUMENTDB_URI and PORT. | skill.md hints at .env.example and avoiding secrets, but conventions (README sections, tests location) are not specified. |
