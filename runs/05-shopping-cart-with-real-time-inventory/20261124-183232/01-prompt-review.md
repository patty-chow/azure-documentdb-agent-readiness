# 1. Prompt review: 05-shopping-cart-with-real-time-inventory

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided skill.md give a clear, implementable request: a Node.js (Mongoose) cart service that uses DocumentDB multi-document transactions, optimistic locking via a version field, and clear out-of-stock errors. Several important implementation details (Mongoose/driver versions, exact API endpoints and error format, test harness and seed-script conventions, and index choices) are unspecified and will be decided by the builder’s defaults or require author clarification.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 8: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets, Data model, Provisioning and deployment, Repository conventions |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 2: Driver and version, App surface |
| Missing: builder will guess | 5: Sample data, Queries and indexes, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- Include an automated integration test or concurrency simulation that issues parallel add-to-cart requests and asserts no overselling — the prompt asks to handle optimistic locking but does not require or describe such an integration test; absent explicit instruction, builder may omit or implement only manual checks.
- Seed script loads sample data and creates the index and can be run twice without duplicating data — prompt/skill.md ask to verify against the live cluster but do not prescribe an idempotent seed script.
- One database client is created and reused across requests — the prompt does not mention client lifecycle; although a driver best-practices skill exists, without explicit instruction the builder may instantiate per-request.
- Queries and index shapes (including any vector/full-text indexes and parameters) — prompt gives no index definitions; indexing choices needed for performance and demonstration are likely to be chosen ad-hoc or omitted.
- Dependencies pinned in a requirements file — the prompt doesn't require pinned dependency files (and the reference's mention of requirements.txt is Python-centric), so reproducible pinning may be missing.
- Unit tests run without a live cluster — prompt does not require offline unit tests or mock strategy; builder may only provide tests that require a live DocumentDB instance.
- Infrastructure-as-code for the cluster — prompt/skill.md state a cluster already exists and do not instruct to provide Bicep/Terraform for it; reference requires infra code which is likely to be absent.
- README covers prerequisites, setup, run, and clean-up — the prompt doesn't mandate README content; the builder may include a minimal README but the full required sections are at risk.
- Sample uses the name 'Azure DocumentDB' throughout and no former or neighbouring product name — neither the prompt nor skill.md explicitly instruct naming conventions for documentation, so inconsistent naming is possible.

## Questions for the prompt author

- What API endpoints and request/response shapes do you want? (e.g., POST /cart/:userId/add with { productId, quantity } and what error format/code for out-of-stock and conflict?)
- What retry policy should the sample use for optimistic-lock conflicts (how many retries, backoff strategy) or should it return a conflict after a single failure?
- Do you require the integration concurrency simulation (parallel add-to-cart) and an automated test that runs against the live cluster, or would a local/unit-level concurrency test be acceptable?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js cart service using Mongoose that stores cart and inventory documents in DocumentDB. Use multi-document transactions to atomically decrement stock and add items to the cart. Handle optimistic locking with a version field and surface clear errors when stock is exhausted." | - | - | Business problem, user and behavior (atomic add-to-cart with inventory protection) are explicitly stated. |
| Workflow type | specified | no | "build a Node.js cart service" (single service implementation implied) | - | Builder will implement a single-agent application (one Node.js service) providing an API for cart operations (no multi-agent/orchestration framework). | Prompt implies a single application (no multi-agent coordination). |
| Language and runtime | specified | no | "Node.js" and "Mongoose" | - | Use Node.js runtime available on the run environment; skill.md specifies Node.js 24 is available, so builder will target Node.js 24. | Language is explicit; Node.js version is provided by skill.md (Node.js 24). |
| Driver and version | ambiguous | no | "Mongoose" | - | Builder will pick a recent, Node-24-compatible Mongoose major (likely Mongoose 7.x). MongoDB driver compatibility will follow whatever Mongoose depends on. | Prompt names Mongoose but does not fix a version. A concrete version should be decided (or left to latest stable) for reproducibility. |
| Target service and tier | specified | no | "DocumentDB" | - | Use the live DocumentDB cluster described in skill.md (M30, MongoDB 7.0 wire protocol) and the database sample_retail_05. | The run-environment (cluster tier and database name) is given in skill.md. |
| Authentication and secrets | specified | no | - | - | Connection string will be read at runtime from DOCUMENTDB_URI (per skill.md). Do not commit secrets; provide .env.example with placeholders. | skill.md explicitly instructs to read DOCUMENTDB_URI from env and not to write it to files. |
| Data model | specified | no | "stores cart and inventory documents" and "version field" and "cart and inventory documents" | - | Inventory schema will include numeric stock and numeric version; Cart schema will have userId and items array with productId and quantity, stored in sample_retail_05. | Prompt explicitly requires Inventory stock + version and Cart with userId and items. |
| Sample data | missing | no | - | - | Builder will create a small hand-authored seed dataset (a few products and one cart) for demo purposes unless instructed otherwise. | Prompt and skill.md require verifying against live cluster but do not specify a seed script, data source, size, or licensing. |
| Queries and indexes | missing | no | - | - | Builder will create minimal indexes needed for the demonstrated queries (e.g., index on productId in inventory and userId in cart) but specifics (compound/vector/TTL) are not provided and will be chosen ad-hoc. | No index definitions or explicit query patterns are provided; vector/index specifics in skill.md are irrelevant to this transactional cart sample unless a vector search is added. |
| AI components | not_applicable | no | - | - | - | No AI/embedding/chat components are part of the prompt. |
| App surface | ambiguous | no | "build a Node.js cart service using Mongoose" | - | Builder will expose an HTTP JSON API (likely Express) with endpoints such as POST /cart/:userId/add or POST /cart/add that accept productId and quantity. CLI or UI is not specified. | Prompt does not specify routes, input payloads, or response shape; most builders will implement a small REST API. |
| Provisioning and deployment | specified | no | - | - | Do not provision a new cluster; use the existing DocumentDB cluster described in skill.md. If deployment code is included, it should not create a cluster unless run-policy allows Azure writes. | skill.md explicitly states a cluster is already provisioned and to avoid provisioning another unless allowed. |
| Run and test instructions | missing | no | - | - | Builder will add README with basic npm install / npm run seed / npm test commands, but exact test commands and expectations are unspecified. | Prompt asks to use transactions and handle conflicts but doesn't require test scripts or describe how to run them; reference requires integration concurrency test which is not specified here. |
| Definition of done | missing | no | - | - | Builder will treat successful demo runs that show atomicity, correct optimistic-lock retries, and no oversell as done; exact acceptance criteria (tests pass, README present) are not defined in the prompt. | No explicit acceptance checklist is provided. |
| Constraints and non-goals | missing | no | - | - | Builder will avoid production-hardening (e.g., full HA, CMK) unless explicitly asked; cost and region constraints are not specified. | Prompt does not state cost limits, scale targets, or things to exclude. |
| Repository conventions | specified | no | - | - | Follow the run-environment guidance: use sample_retail_05 DB, read DOCUMENTDB_URI from env, provide a .env.example with placeholders, and do not commit secrets. | skill.md defines several repo/run conventions (env var, DB name, don't commit secrets). |
