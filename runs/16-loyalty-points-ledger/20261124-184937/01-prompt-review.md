# 1. Prompt review: 16-loyalty-points-ledger

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the app goal (Node.js + Mongoose loyalty ledger), the two collections (events immutable, balances), multi-document transactions, and the /balance and /history endpoints with an aggregation to compute tier from lifetime points. The provided run-time notes (skill_md) fill several environment and runtime details (Node.js 24, DOCUMENTDB_URI, database name). Missing details (HTTP framework, exact Mongoose/driver versions, seed data, explicit indexes, test strategy, README/packaging) will be decided by the builder using sensible defaults (Express, Mongoose 7.x, create indexes on accountId + timestamp, a small idempotent seed script, npm start, etc.). No blocking unknowns prevent starting the build.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Data model, Repository conventions |
| Ambiguous: builder will guess | 4: Workflow type, Driver and version, Queries and indexes, App surface |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- The vector index dimensions match the embedding model's output — the prompt and skills do not request or use vector indexes for this sample, so this reference requirement is unlikely to be satisfied.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — not applicable/unspecified for this sample and therefore at risk.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the prompt does not require a seed script; although skill_md suggests loading sample data during verification, no explicit idempotent seed script is requested.
- /search returns a clear error for an empty query and when the embedding call fails — the starter prompt does not implement search or embeddings; this will not be produced.
- Search results include the similarity score — not applicable to this sample and not requested by the prompt, so at risk.
- Dependencies are pinned in requirements.txt — the prompt uses Node.js; the generic requirement calls out requirements.txt (Python) rather than package.json or package-lock.json. There is no instruction to pin Node dependencies in an equivalent file, so this requirement may not be met.
- Unit tests run without a live cluster — the prompt does not request tests or a mocking strategy; unless the builder adds mocked/unit tests intentionally, this requirement is at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the prompt explicitly uses an existing cluster and does not request provisioning code; this is at risk unless the builder adds it.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt does not request creating a README; without one this requirement will be unmet.

## Questions for the prompt author

- Which HTTP framework should the sample use (Express, Fastify, Koa)? This determines the scaffolding and middleware choices.
- Do you want explicit versions for Node/Mongoose/driver pinned in package.json? (I will assume Node 24 and Mongoose 7.x / MongoDB driver compatible with MongoDB 7.0 unless you specify.)
- Should the sample include an idempotent seed script and a README with run/verification steps? If so, any preference for sample dataset size?

## Contradictions and missing references

- "Using the DocumentDB skill" — there is no single installed skill with the exact name "DocumentDB skill". The environment includes multiple documentdb-* skills that cover different aspects (driver, connection, data modeling, indexing, etc.), but the prompt's phrase could be misread as referring to a single skill that isn't installed.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose loyalty ledger that stores every earn and redeem event as an immutable document... Expose a /balance and /history endpoint and include an aggregation that calculates tier status from lifetime points." | - | - | Business problem and what the sample demonstrates are clearly stated. |
| Workflow type | ambiguous | no | - | - | Builder will implement this as a single-agent sample (one service app) with no multi-agent orchestration. | Prompt does not mention agent framework or multi-agent orchestration; this does not block building the sample. |
| Language and runtime | specified | no | "Node.js Mongoose" (starter prompt) and skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js is specified and skill_md supplies the available runtime version (Node 24). |
| Driver and version | ambiguous | no | "Mongoose" (starter prompt) but no version specified. | documentdb-driver | Use a current stable Mongoose compatible with Node 24 (Mongoose 7.x) and the MongoDB Node driver 4.x/5.x stable for MongoDB 7.0 compatibility; pin package.json to explicit versions. | The documentdb-driver skill gives best-practice patterns (singleton client) but does not prescribe explicit driver/Mongoose versions. |
| Target service and tier | specified | no | "DocumentDB" (starter prompt) and skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable... use database named sample_retail_16" | - | - | skill_md provides the exact target cluster and DB name to use for the sample. |
| Authentication and secrets | specified | no | - | - | skill_md requires reading the connection string from DOCUMENTDB_URI in the environment; do not write the secret into files or logs and provide a .env.example placeholder. | The run-time notes explicitly say the connection string is in DOCUMENTDB_URI and must not be written into files; use a .env.example placeholder. |
| Data model | covered_by_skill | no | "stores every earn and redeem event as an immutable document" and implied separate balances collection; Mongoose is required. | documentdb-data-modeling | Schema fields: events {_id, accountId, type: 'earn'\|'redeem', amount: Number, timestamp: Date, metadata?}, mark core event fields immutable in Mongoose schema; balances {_id, accountId, balance, lifetimePoints?} with accountId unique. If sharding is used, use accountId as shard key. | Prompt gives high-level model (events + balances, immutability); documentdb-data-modeling provides guidance for embedding/refs and other modeling choices. Exact field list and shard key are not fully enumerated; builder will choose sensible fields as assumed above. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will include a small idempotent seed script that inserts a few accounts and events (e.g., 3 accounts, 10 events each) and creates required indexes. Seed script will check for existing docs and upsert or skip to allow repeated runs. | Starter prompt does not mention sample data content, size, license, or loading mechanism. documentdb-local-deployment helps with local sample-data patterns but does not supply specific sample data. |
| Queries and indexes | ambiguous | no | Aggregation that calculates tier status from lifetime points; read balance and history endpoints. | documentdb-indexing | Create an index on events {accountId: 1, timestamp: 1} to satisfy chronological history queries, and a unique index on balances {accountId: 1}. The aggregation will sum 'earn' amounts by accountId. No vector/full-text indexes are required for this sample. | Prompt requires an aggregation but does not specify indexes; documentdb-indexing can guide index choices but builder will add the common indexes above. |
| AI components | not_applicable | no | - | - | - | No embedding, LLMs or other AI components are requested for this sample. |
| App surface | ambiguous | no | "Expose a /balance and /history endpoint" | - | Implement a small Express-based HTTP API with GET /balance?accountId=<id> and GET /history?accountId=<id>. Return JSON: /balance => {accountId, balance, lifetimePoints, tier}; /history => [array of event documents ordered oldest-first]. | Prompt names endpoints but does not specify HTTP framework or exact query parameter/URL form; Express + query parameter is the likely default. |
| Provisioning and deployment | specified | no | - | - | Do not provision a new cluster; use the existing cluster referenced in DOCUMENTDB_URI and the database sample_retail_16. | skill_md explicitly says a cluster is already provisioned and that the build should not provision another cluster. |
| Run and test instructions | missing | no | - | - | Include README with npm install, .env example, npm run seed, npm start, and curl examples for the two endpoints; unit tests (if any) will be documented and may require a live cluster unless mocked. | Starter prompt does not request run or test commands or how to verify success. |
| Definition of done | missing | no | - | - | Acceptance criteria: endpoints exist and return correct data; transactions are used when writing events and balances; redeem prevents negative balance; aggregation computes lifetime points and tier and is included in /balance responses; connection uses DOCUMENTDB_URI and database sample_retail_16. | No explicit pass/fail criteria are provided in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep sample lightweight and cost-conscious: do not provision new cloud resources, do not store secrets in repo, keep sample data small, and avoid production security settings beyond TLS and env-based secrets. | Prompt doesn't specify cost or compliance constraints; documentdb-security can advise on production hardening if requested. |
| Repository conventions | covered_by_skill | no | - | documentdb-local-deployment | Follow common sample layout: package.json, src/, models/, routes/, scripts/seed.js, .env.example (no secrets), README.md. Use database name sample_retail_16 as specified in skill_md. | skill_md instructs to read connection string from env and to provide a .env.example placeholder; repository layout otherwise left to builder conventions. |
