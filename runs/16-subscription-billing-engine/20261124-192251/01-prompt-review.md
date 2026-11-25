# 1. Prompt review: 16-subscription-billing-engine

**Verdict: sufficient_with_assumptions**

The starter prompt and run-environment notes give a clear goal (Node.js + Mongoose billing engine demonstrating multi-document transactions, idempotency keys, and TTL indexes) and the live-cluster details (DOCUMENTDB_URI and database name). Most implementation choices (API surface, exact schema fields, Mongoose and driver versions, seed scripts, tests, README and deployment artifacts) are not specified and will be chosen by the builder or filled by the installed skills (data-modeling, driver, indexing). No blocking gaps were found — the build can start, but several runner-default assumptions will be taken.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Data model |
| Ambiguous: builder will guess | 5: Workflow type, Driver and version, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — skill_md suggests using .env.example but the prompt doesn't require enumerating all settings; builder may omit some keys.
- Vector index dimensions match embedding model output — the sample does not use embeddings; no guidance leads to constructing vector indexes correctly for an embedding model.
- Vector index parameters chosen for sample size and README notes — not applicable unless vectors are used; at risk because cluster is vector-capable but the prompt doesn't ask to configure these.
- A seed script that loads sample data and creates indexes and can be run twice without duplicating data — prompt asks to create indexes in code but does not require an idempotent seed script; likely to be omitted unless implementer adds it.
- /search returns clear error for empty query and when embedding call fails; search results include similarity score — search endpoints are not requested by the starter prompt; at risk.
- Dependencies are pinned in a requirements file — prompt does not require pinned dependencies; implementer may or may not pin versions in package.json.
- Unit tests run without a live cluster — tests are not specified; unless the builder explicitly adds mocking/test fixtures, tests may require a live cluster.
- Infrastructure for the cluster provided as code — run-environment states an existing cluster is used; sample will probably not include infra-as-code.
- README covers demo, prerequisites, setup, run, and clean-up — the prompt doesn't require a complete README; this is often missed unless the builder is told to include it.

## Questions for the prompt author

- Do you want a minimal HTTP JSON API (recommended) for the sample? If so, confirm endpoints you want (e.g., POST /charge, GET /plans, GET /customers) or say if a CLI-only sample is preferred.
- Which Mongoose version (or range) should be used and pinned in package.json? If none, builder will pick the latest 7.x compatible with Node 24.
- Should the repo include an idempotent seed/migration script and basic unit tests (with DB-mocking) or only a runnable example against the live cluster?
- Is including infrastructure-as-code (Bicep/Terraform) to provision the DocumentDB cluster required, or must the sample never provision resources (use the provided cluster)?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose billing engine that stores subscription plans, customers, and charge events... Use multi-document transactions... Add idempotency key checks... and use TTL indexes to auto-expire trial entitlement documents." | - | - | Prompt clearly states business problem and what the sample demonstrates (transactions, idempotency, TTL). |
| Workflow type | ambiguous | no | No agent/orchestration details; prompt addressed to a coding agent: "Using the DocumentDB skill... build..." | - | Builder will produce a single-process Node.js service (no multi-agent orchestration). The coding agent itself runs locally to produce the repo. | Prompt doesn’t state whether the sample includes background workers, cron jobs, or only HTTP endpoints. |
| Language and runtime | specified | no | "Node.js Mongoose"; skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js is explicit and the run-environment notes specify Node 24. |
| Driver and version | ambiguous | no | "Mongoose" (ODM) is required but no version is given. | documentdb-driver | Builder will use a modern Mongoose 7.x compatible with Node 24 and MongoDB 7 wire protocol (e.g., latest 7.x at time of build). The underlying mongodb driver will be whatever Mongoose pins. | Mongoose is mandated but the exact version/range is not; driver best-practices are available in documentdb-driver. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable... connection string in DOCUMENTDB_URI... Use database named sample_fintech_16." | - | - | The run environment explicitly identifies the live cluster to use and the database name. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file... use a config file or `.env.example` with a placeholder." | documentdb-security | - | Where secrets come from and how to handle them is stated in the run-environment guidance. |
| Data model | covered_by_skill | no | "stores subscription plans, customers, and charge events and entitlement documents" (no field-level schema). | documentdb-data-modeling | Builder will design a small normalized/denormalized schema, e.g. plans {_id, name, price}, customers {_id, name, email, subscription: {planId, status}}, chargeEvents {_id, customerId, amount, currency, idempotencyKey, createdAt}, entitlement {_id, customerId, expiresAt}. No explicit shard key (single-shard DB). | Skill provides modeling guidance; the starter prompt leaves exact document shapes and relationships to the implementer. |
| Sample data | missing | no | - | - | Builder will include a small seed script that inserts a few plans, customers, and entitlements (e.g., 3 plans, 5 customers) and can be run idempotently. | Prompt and skills do not specify source, size, or explicit seed script — only run-environment asks to 'load the sample data' when verifying. |
| Queries and indexes | ambiguous | no | "Add idempotency key checks... unique index in code on the charge events collection... use TTL indexes to auto-expire trial entitlement documents... Create the required indexes... in code." | documentdb-indexing | Builder will create: (1) unique single-field index on chargeEvents.idempotencyKey (unique:true), (2) TTL index on entitlement.expiresAt with expireAfterSeconds: 0, and likely single-field index on chargeEvents.customerId for lookups. Other query patterns and index params left to implementer and indexing skill guidance. | Prompt requires the crucial indexes but does not fully enumerate every index or their detailed options; indexing guidance is available. |
| AI components | not_applicable | no | No embedding or chat/LLM usage requested. | - | - | Although the cluster is vector-capable, the sample does not request any AI/embedding features. |
| App surface | ambiguous | no | "build a Node.js Mongoose billing engine" — no explicit API/CLI/UI surface defined. | - | Builder will expose a minimal HTTP JSON API (e.g., POST /charges or POST /charge to perform the transactional charge operation, GET /plans, GET /customers) and a seed/migration CLI script. The transactional operation will accept {customerId, amount, idempotencyKey, ...} and return the charge event or the existing event if idempotent. | The exact routes, payloads, and responses are left to the implementer; these choices affect tests and README. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | Sample will not include provisioning steps; it will document prerequisites (existing cluster and DOCUMENTDB_URI). | The run environment explicitly states that an existing cluster should be used and not provisioned by the sample. |
| Run and test instructions | missing | no | - | - | Builder will add README instructions with npm install, .env setup, npm run seed, npm start, and example curl requests; tests (if any) will need instructions to run with or without a live cluster. | No concrete commands, expected outputs, or test commands are present in the prompt or skill-md. |
| Definition of done | missing | no | - | - | Builder will treat successful creation of models and indexes, a working POST /charge demonstrating atomicity (either both charge insert and subscription update succeed or neither), idempotency behavior, and TTL expiry of entitlements (observed via the DB) as acceptance criteria. | No explicit acceptance criteria are provided; implementer must define them in README or tests. |
| Constraints and non-goals | missing | no | - | documentdb-security | Builder will avoid provisioning new cloud resources, keep secrets in env vars, and not try to demonstrate cross-region HA or production-level monitoring in this sample. | Cost limits, privacy/PII constraints, or explicit non-goals are not defined. |
| Repository conventions | ambiguous | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder..." | - | Builder will include .env.example, package.json with pinned versions, a seed script, src/ folder with models and routes, and a README covering setup and cleanup. Tests may live in test/ and use mocks for DB where possible. | Some conventions (use .env.example) are stated; fuller repo-level conventions are not spelled out and will be assumed by the implementer. |
