# 1. Prompt review: 10-multi-tenant-storefront-saas

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal: a Node.js Mongoose multi-tenant sample that stores Products, Orders and Inventory in shared Azure DocumentDB collections with tenantId-based isolation and the two compound indexes. The run-time constraints and environment (database name, DOCUMENTDB_URI env var, Node 24 availability, and requirement to verify against the live cluster) are provided in the supplied skill_md. Several implementation choices (exact Mongoose/driver versions, API surface, test strategy, seed script behavior, README contents, and some non-goal constraints) are left to the builder and will be filled by skill guidance or reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 7: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Data model, Queries and indexes, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 3: Driver and version, App surface, Repository conventions |
| Missing: builder will guess | 5: Workflow type, Sample data, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- Seed script idempotency and data-loading details — prompt/skills do not specify a seed dataset, its size or idempotent behavior; builder must invent this.
- Automated test that attempts a query without tenantId and asserts the repository rejects it — prompt asks for tenant isolation but does not require a test; no installed skill mandates creating this test.
- Unit tests run without a live cluster — test strategy (mocking or in-memory) is not specified by prompt or skills.
- Dependencies pinned in a requirements file — the reference mentions pinned dependencies (requirements.txt) but the prompt is a Node.js project and neither prompt nor skills require explicit pinning policy (package-lock.json will exist though).
- Infrastructure-as-code for the cluster — run environment says cluster is pre-provisioned and prompt does not request IaC; reference wants IaC but prompt/skills do not provide it.
- README coverage (prereqs, setup, run, clean-up) — prompt doesn't require a README; the run environment says to record what was executed, but a full README is not specified and may be omitted or incomplete.
- Vector index dimension & parameter selection and related search behaviors — the prompt does not use vector search, while the reference expects vector index choices if used; this is not addressed by prompt or skills for this sample.

## Questions for the prompt author

- Should the sample expose a REST API (Express) for demonstration, or is a CLI + repository library sufficient? This will change the app surface and example usage in the README.
- Do you want the sample to pin Mongoose (and mongodb driver) to specific versions, or is 'latest stable compatible with Node 24 / MongoDB 7.0' acceptable?
- Should the project include unit tests that run entirely offline (mocking Mongoose) in addition to the live-cluster verification tests required by the run environment?

## Contradictions and missing references

- Prompt requests "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill"; many documentdb-* skills are installed (documentdb-driver, documentdb-indexing, etc.). Builder will pick appropriate documentdb-* skills.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose app that stores all merchant products, orders, and inventory in shared DocumentDB collections... enforce tenant isolation at the repository layer" | - | - | Business problem and demonstration are explicit: multi-tenant SaaS data isolation in Azure DocumentDB. |
| Workflow type | missing | no | - | - | Treat as a single-agent coding task / local developer sample (no multi-agent orchestration). The builder will produce a simple repo with scripts and maybe an express API. | Prompt does not mention an agent framework or orchestration; this doesn't block building the sample. |
| Language and runtime | specified | no | "Node.js" (skill_md: "Node.js 24 with npm and npx is available") | - | - | Node.js 24 is stated in the provided run environment. |
| Driver and version | ambiguous | no | "Mongoose" | documentdb-driver | Use a modern stable Mongoose (e.g., Mongoose 7.x) compatible with Node 24 and MongoDB 7.0; rely on Mongoose-maintained mongodb driver dependency. | Prompt requires Mongoose but doesn't pin a version; documentdb-driver skill covers driver best practices, not exact package version. |
| Target service and tier | specified | no | Uses Azure DocumentDB; skill_md: "vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...)" | - | - | Run environment explicitly supplies the cluster type/tier and database name to use. |
| Authentication and secrets | specified | no | Prompt silent; skill_md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or .env.example with a placeholder" | - | - | How to obtain and store the connection string is specified by the run environment guidance. |
| Data model | specified | no | "stores all merchant products, orders, and inventory in shared DocumentDB collections. Use a tenantId field on every document, include sku on Product and Inventory, and createdAt timestamps" (prompt + skill_md provides DB name sample_retail_10) | documentdb-data-modeling | - | Prompt and run environment give the main schema constraints; finer-grain fields are left to implementation. |
| Sample data | missing | no | - | - | Builder will add a small seed script with a few tenants, products, inventory rows and orders for demonstration; seed script will be idempotent (upsert by unique key). | Prompt doesn't say what sample data to use or its size/licence or how to load it. |
| Queries and indexes | specified | no | "create compound indexes on (tenantId, sku) and (tenantId, createdAt)" and "enforce tenant isolation at the repository layer" | documentdb-indexing | - | Index shapes are explicitly requested; documentdb-indexing skill can advise on index choice and creation best practices. |
| AI components | not_applicable | no | - | - | - | No AI/embedding/chat components requested. |
| App surface | ambiguous | no | Prompt requests a Node.js Mongoose app and repository layer but does not specify API vs CLI vs UI. | - | Builder will provide a minimal Express REST API exposing repository operations (CRUD endpoints) plus npm scripts and a seed script. Business logic will depend only on repository APIs, not direct model usage. | Which endpoints/CLI commands to expose is left to the implementer; this affects examples and tests but not core repo code. |
| Provisioning and deployment | specified | no | Prompt silent; skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | The run environment forbids creating a new cluster; builder will create collections/indexes on the provided cluster only. |
| Run and test instructions | missing | no | - | - | Include README and npm scripts (npm run start, npm run seed, npm test). Tests: at least one integration test that runs against the live cluster (per skill_md) and unit tests that can run offline/mocked. | Prompt/skills don't provide explicit command list or test harness to run; builder will add conventional scripts. |
| Definition of done | missing | no | - | - | Accept if: schemas defined with tenantId required, compound indexes created and verified at runtime, repository prevents cross-tenant queries and throws when tenantId omitted, seed script loads sample data, and at least one test demonstrates enforcement of tenant isolation. | Prompt lacks formal acceptance criteria; builder will follow the reference requirements and run-environment directives as the checklist. |
| Constraints and non-goals | missing | no | - | documentdb-security | Do not provision new Azure resources; keep credentials in env vars and .env.example; avoid cross-database changes. No production HA or CMK setups are required for this sample. | The run environment gives one constraint (pre-provisioned cluster) but other cost/scope constraints are not specified. |
| Repository conventions | ambiguous | no | Prompt requires repository layer and discourages direct model usage; skill_md: "use a config file or .env.example with a placeholder" and database name sample_retail_10 | - | Use conventional Node layout: src/, src/models, src/repos, src/routes, tests/, README.md, .env.example, package.json with scripts. Expose repository-only API for business logic. | Small repo conventions are implied but not fully enumerated. |
