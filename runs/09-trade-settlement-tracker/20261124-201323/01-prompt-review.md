# 1. Prompt review: 09-trade-settlement-tracker

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided run-environment skill.md give a clear goal (Node.js Mongoose settlement tracker) and the live-cluster details needed to start. Several implementation details (Mongoose/driver versions, exact schema shape, endpoints, seed-data size/format, test/run commands, and infra-as-code) are not specified and will be filled by the builder's defaults or by consulting the installed documentdb-* skills.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 1: Constraints and non-goals |
| Ambiguous: builder will guess | 6: Workflow type, Driver and version, Data model, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 3: Sample data, Run and test instructions, Definition of done |
| Not applicable | 1: AI components |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. Reason: skill.md requires DOCUMENTDB_URI, but the prompt does not instruct creation of .env.example explicitly — skill.md suggests it; builder must remember to include .env.example. (Partly covered but must be implemented.)
- .env.example lists every setting with placeholder values. Reason: not specified in prompt; skill.md hints at .env.example but does not enumerate all settings required by the sample.
- The vector index dimensions match the embedding model's output. Reason: Not applicable to this sample (no embeddings requested) and not covered by prompt or skills for this sample.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. Reason: no vector/indexing parameters are specified; not relevant unless builder adds vector search.
- One database client is created and reused across requests. Reason: documentdb-driver skill covers singleton best practice but the prompt doesn't require this; builder must implement it.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. Reason: prompt does not request a seed script; skill.md requires verification against live cluster but does not provide the sample data/seed script — this is likely to be omitted unless the builder adds it.
- /search returns a clear error for an empty query and when the embedding call fails. Reason: Not relevant to this prompt (no search/embedding endpoint requested).
- Search results include the similarity score. Reason: Not relevant to this prompt.
- Dependencies are pinned in requirements.txt. Reason: The reference mentions requirements.txt (Python). For Node.js this would translate to pinned versions in package.json; prompt/skill.md do not require pinned dependency versions.
- Unit tests run without a live cluster. Reason: Tests and mocking strategy are not specified; builder must add test harness/mocks to meet this requirement if desired.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. Reason: skill.md says a cluster already exists and that the sample should not provision a new cluster; the prompt does not request provisioning code.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. Reason: README content is not specified in the prompt; builder must author it.

## Questions for the prompt author

- Do you want the sample to include an idempotent seed script and example dataset in the repo, and if so, roughly how many synthetic trades should be seeded (e.g., 100, 1k, 10k)?
- Should the sample include infra-as-code (Bicep/Terraform) to provision the cluster, or should it rely only on the already-provisioned cluster (the run-environment says a cluster exists and provisioning should be avoided)?
- Which Mongoose/mongo driver versions should be pinned (if any), or is it acceptable to target latest stable Mongoose compatible with Node 24?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB skill'. Multiple documentdb-* skills exist (documentdb-driver, documentdb-connection, documentdb-data-modeling, etc.). The builder will map the request to those installed documentdb-* skills.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js Mongoose settlement tracker that models each trade as a state machine document in DocumentDB | - | - | Prompt clearly states business problem: trade settlement lifecycle as state-machine documents, logging transitions and detecting failures. |
| Workflow type | ambiguous | no | - | - | Assume this is a normal single-process server sample (no agent framework) — a Node/Express service running on the developer machine that connects to the live cluster. | Prompt does not say 'no-agent' explicitly; the sample is a standard app rather than an agentic orchestration. |
| Language and runtime | specified | no | Node.js Mongoose | - | Use Node.js 24 (documented in skill.md run environment). | skill.md explicitly states Node.js 24 is available; use that runtime. |
| Driver and version | ambiguous | no | Mongoose | documentdb-driver | Use a recent Mongoose 7.x release compatible with Node.js 24 and the MongoDB 7.0 wire protocol; rely on Mongoose's bundled compatible mongodb driver (latest stable). | Prompt names Mongoose but gives no version. documentdb-driver skill covers best practices but not an exact version to pin. |
| Target service and tier | specified | no | - | - | Use the existing vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) and the database sample_banking_09, as described in the run environment. | skill.md provides the cluster tier and database name to use. |
| Authentication and secrets | specified | no | - | - | Read connection string from environment variable DOCUMENTDB_URI; do not commit credentials to repo and provide a .env.example placeholder. | skill.md explicitly instructs that DOCUMENTDB_URI contains the connection string and that it must not be written into files. |
| Data model | ambiguous | no | models each trade as a state machine document | documentdb-data-modeling | Create a 'trades' collection in sample_banking_09. Each trade document includes tradeId, assetClass, counterparty, currentState, stateHistory (array of transition records), metadata (timestamps), and a lightweight version field. No sharding by default (single-shard). | Prompt requires state-machine documents but doesn't define exact fields, relationships, or shard key. documentdb-data-modeling can guide structure but not the concrete schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small idempotent seed script that upserts ~100-500 synthetic trades (various asset classes and counterparties). The seed script is safe to run twice and creates required indexes. | Prompt doesn't say where sample data comes from or how much to load. documentdb-local-deployment discusses sample-data tooling for local, but the run environment expects verifying against the live cluster and doesn't provide a concrete sample dataset. |
| Queries and indexes | ambiguous | no | Expose an aggregation endpoint showing settlement rates by asset class and counterparty | documentdb-indexing | Create single-field indexes on assetClass, counterparty, and currentState; consider a compound index {assetClass:1, counterparty:1, currentState:1} for the aggregation, plus indexes for any filter fields. No vector or text indexes required for this sample. | Prompt requires an aggregation but doesn't specify which indexes to create or their exact shapes; use documentdb-indexing guidance to pick sensible indexes. |
| AI components | not_applicable | no | - | - | - | No embeddings or LLMs are requested in the prompt. |
| App surface | ambiguous | no | Expose an aggregation endpoint showing settlement rates by asset class and counterparty | - | Implement an Express-based HTTP API with endpoints: POST /trades/:id/advance (to advance state), GET /settlement-rates (aggregation by assetClass and counterparty), and an administrative /seed endpoint or script. Default port 3000. | Prompt specifies only the aggregation endpoint; it does not list other endpoints or inputs/outputs. Builder will add sensible endpoints for advancing state and seeding. |
| Provisioning and deployment | specified | no | - | - | Do not provision another cluster; use the existing reachable cluster in DOCUMENTDB_URI. No infra-as-code will be created unless explicitly requested. | skill.md states a cluster already exists and advises not to create another cluster for the sample run. |
| Run and test instructions | missing | no | - | - | Include straightforward commands: npm install; cp .env.example .env and fill DOCUMENTDB_URI; npm run seed; npm start; optional tests via npm test (with instructions for mocking or using the live cluster). | Prompt doesn't provide commands or test/run expectations. skill.md gives environment constraints but not explicit run steps. |
| Definition of done | missing | no | - | - | Define done as: trades stored as single documents, state transitions performed in a transaction with transition logs written in same transaction, change stream detects failed settlements and runs exception handler, aggregation endpoint returns settlement rates grouped by asset class and counterparty. | Prompt describes features but doesn't give explicit acceptance criteria or example responses. |
| Constraints and non-goals | covered_by_skill | no | - | documentdb-security | Follow run-environment constraints from skill.md: do not write connection strings to repo, use sample_banking_09 only, and avoid provisioning a new cluster. | skill.md and installed security-related skills give guidance on secrets and network practices. Explicit cost-limits/SLAs were not requested. |
| Repository conventions | ambiguous | no | - | - | Use a standard Node sample layout (src/, scripts/, test/, README.md). Provide .env.example with placeholders, package.json with pinned versions, and a README with prerequisites, setup, run, and cleanup instructions. | skill.md mentions .env.example and that the build report should record what was executed; it does not fully specify repo layout or README sections. |
