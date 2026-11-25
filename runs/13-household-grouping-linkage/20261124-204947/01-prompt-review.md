# 1. Prompt review: 13-household-grouping-linkage

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core goal: a Node.js (Mongoose) service that links customers into households by matching address/phone/surname, persists household docs with member refs, and exposes aggregation endpoints for household CLV and product holdings. Most operational defaults (which Node.js runtime to target, driver versions, exact route names, seed data shape, indexing choices, test infra, README and repo conventions) are not specified and will be chosen by the builder or covered by available skills, so the build can start but will rely on sensible assumptions.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 7: Workflow type, Driver and version, Data model, Queries and indexes, App surface, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 3: Sample data, Run and test instructions, Definition of done |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — the prompt does not require producing a complete .env.example; only the run-environment notes DOCUMENTDB_URI. (No installed skill guarantees a full .env.example will be created.)
- The vector index dimensions match the embedding model's output — the starter prompt does not use embeddings or vector search, so vector-index requirements are not addressed by prompt or skills.
- Vector index parameters chosen for sample data size and README guidance for scaling — not covered by the prompt (no vector use).
- A seed script that loads sample data and creates the index, and can be run twice without duplicating data — the prompt does not request a seed script and no skill ensures this will be added.
- /search returns a clear error for an empty query and when the embedding call fails — the prompt does not include a /search endpoint or any embedding/LLM usage, so this requirement is likely not met.
- Search results include the similarity score — not applicable to the prompt's stated functionality and thus at risk.
- Dependencies are pinned in requirements.txt — this requirement appears Python-centric; prompt is Node.js and does not ensure pinned dependencies or a lockfile will be present (e.g., package-lock.json).
- Unit tests run without a live cluster — prompt asks to verify against a live cluster (skill_md) and does not require tests that run offline; no installed skill guarantees offline unit tests will be included.
- Infrastructure for the cluster is provided as code using the Azure DocumentDB resource type — prompt/run-environment expects using an existing cluster and does not ask for IaC; the documentdb-azure-deployment skill exists but the prompt does not request provisioning code.
- README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt does not explicitly require or describe README contents; unless builder includes it, this may be omitted.
- The sample uses the name 'Azure DocumentDB' throughout — the prompt says DocumentDB but does not enforce naming conventions; builder may use inconsistent product names unless instructed.

## Questions for the prompt author

- Which Node.js and Mongoose versions should I target (Node.js 24 is available; should I pin to Mongoose 7.x)?
- What exact HTTP routes and request/response shapes do you expect for the household CLV and product-holdings endpoints (or is conventional REST like GET /households/:id/clv acceptable)?
- Should the sample include an idempotent seed script and README with run/test steps? If so, any required minimum sample-data size or real-world schema for CLV calculation (e.g., sum of member.clv field vs. recomputing from transactions)?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" but no installed skill is named exactly "DocumentDB skill"; multiple documentdb-* skills exist (e.g., documentdb-driver, documentdb-connection). The builder will interpret this generically and use the relevant installed documentdb skills.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "identifies household members by matching on shared address, phone, and surname fields... Create household group documents with member references, and expose aggregation endpoints that compute household-level CLV and product holdings across all members." | - | - | The business problem, user-level goal and what the sample demonstrates are explicitly stated. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" and "build a Node.js Mongoose service" | - | Builder will treat this as a single-agent code generation task producing a standalone Node.js service with REST endpoints (no multi-agent orchestration required). | Prompt does not state agent framework or orchestration model. Most builders will implement a simple single-agent/no-agent runtime. |
| Language and runtime | specified | no | "Node.js Mongoose service" | - | Use Node.js (the provided run environment indicates Node.js 24 is available). | Prompt + provided run-environment (skill_md) implies Node.js; use Node.js 24 runtime available on the build machine. |
| Driver and version | ambiguous | no | "Mongoose" | documentdb-driver | Builder will pick a modern Mongoose version compatible with Node.js 24 (e.g., Mongoose 7.x) and the MongoDB Node driver matching Mongoose's peer dependency (mongodb 5.x). | Prompt specifies Mongoose but not versions. documentdb-driver skill gives usage patterns (singleton client), but not exact version pins. |
| Target service and tier | specified | no | "DocumentDB" (and run environment provided separately). | - | Use the existing cluster described in the run environment: database sample_customer_360_13 on an M30, MongoDB 7.0 wire-protocol cluster reachable via DOCUMENTDB_URI. | The sample's skill_md/run-environment explicitly states a reachable, vector-capable Azure DocumentDB cluster (M30, MongoDB 7.0) and the database name to use. |
| Authentication and secrets | specified | no | - | - | Connection string is read at runtime from DOCUMENTDB_URI environment variable (per the provided run environment). Do not write the secret into files or logs; use .env.example placeholders. | The provided run-environment (skill_md) instructs using DOCUMENTDB_URI and not embedding secrets in the repo. |
| Data model | ambiguous | no | "Mongoose models for customer documents and household group documents" and "member references" | documentdb-data-modeling | Create a database sample_customer_360_13 with collections customers and households. Customer documents include name/surname, phone, address (structured or string), CLV and products array; Household documents contain an array of ObjectId refs to customers (Mongoose ref). Collections will remain unsharded for the sample (or shard on _id if needed). | Prompt requires models but does not specify full field shapes or shard key. documentdb-data-modeling skill can guide embedding vs referencing and document-size considerations. |
| Sample data | missing | no | - | - | Builder will add a small idempotent seed script (e.g., ~20 customers, a few households, sample purchases/products) embedded in the repo for demo purposes. Data will be synthetic and generated under a permissive in-repo script. | Prompt does not say where sample data comes from, size, or licensing, nor does any installed skill provide a concrete dataset. |
| Queries and indexes | ambiguous | no | "aggregation endpoints that compute household-level CLV and product holdings" and "matching on shared address, phone, and surname fields" | documentdb-indexing | Create aggregation pipelines that group on normalized address/phone/surname. Add a compound index on { normalizedAddress:1, phone:1, surname:1 } (or separate indexes) to support grouping and matching; include indexes for fields used in aggregations (CLV numeric field, products array). No vector/text index is required for this sample. | The prompt specifies the query patterns but not which indexes to create or their parameters. The documentdb-indexing skill can guide index selection; builder will pick a sensible compound index to support the matching. |
| AI components | not_applicable | no | - | - | - | The prompt does not request embeddings, LLMs, or other AI components. |
| App surface | ambiguous | no | "expose aggregation endpoints that compute household-level CLV and product holdings" | - | Builder will implement a small REST API (Express) with endpoints such as GET /households/:id/clv and GET /households/:id/products (accepting household id or query parameters) returning JSON: { householdId, clvTotal } and { householdId, products: [{ productId, count }] }. Input validation and error responses will be included. | Prompt requires endpoints but does not define exact routes, HTTP verbs, or request/response shapes; builder will choose conventional REST routes. |
| Provisioning and deployment | specified | no | "Using the DocumentDB skill" and run-environment guidance | documentdb-azure-deployment | Do not provision a new cluster; use the already-provisioned cluster reachable via DOCUMENTDB_URI. If deployment code is added, it will be optional and gated behind a clear warning. | The provided run environment instructs that a cluster is already provisioned and available; the sample should use it rather than provisioning another cluster unless explicitly allowed. |
| Run and test instructions | missing | no | - | - | Builder will add npm scripts (npm run seed, npm start, npm test) and README commands to run the sample. Unit/integration tests will be minimal; live verification steps will be documented per skill_md instructions. | Prompt does not include explicit run/test commands or success criteria; these will be added by the builder. |
| Definition of done | missing | no | - | - | Builder will treat 'done' as: models implemented, endpoints available and tested against seeded data, household docs created, and README describes steps to run and verify. | No explicit acceptance criteria are provided in the prompt. |
| Constraints and non-goals | ambiguous | no | - | documentdb-security | Respect the run-environment instruction not to provision new clusters and keep secrets out of the repo. No production HA/DR or CMK work is required for this sample. | The prompt does not enumerate cost or security constraints; installed security-related skills can guide best practices if the builder wishes to include them. |
| Repository conventions | ambiguous | no | - | - | Repository will follow common Node conventions: package.json with pinned or caret-pinned deps, a .env.example with placeholders (per run-environment guidance), src/ or lib/ layout, README.md with setup/run/cleanup, and seed/ scripts directories. | Prompt doesn't prescribe a repo layout or README details; the run environment suggests using .env.example and not committing secrets. |
