# 1. Prompt review: 03-core-banking-transaction-ledger

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (a Node.js + Mongoose immutable transaction ledger with multi-document transactions and idempotency via transactionRef). The run-environment fragment (skill_md) supplies critical runtime and cluster details (Node 24, DOCUMENTDB_URI, DB name), so the build can start; several implementation details (API surface, driver/mongoose version, seed/test infra, README and provisioning-as-code) are left to the builder and will be chosen by reasonable defaults unless the author specifies them.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 7: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Data model, Provisioning and deployment, Repository conventions |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 2: Driver and version, Queries and indexes |
| Missing: builder will guess | 6: Workflow type, Sample data, App surface, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. (Partially covered: skill_md specifies DOCUMENTDB_URI, but prompt doesn't require an explicit .env.example—builder may or may not create one.)
- .env.example lists every setting with placeholder values. (Missing: prompt/skill_md advise using .env.example but do not demand listing every setting; builder may omit some settings.)
- The vector index dimensions match the embedding model's output. (Missing: no embeddings/vector search in starter prompt; skill_md cluster mentions vector-capable, but nothing specifies embedding model or dims.)
- The vector index parameters are chosen for the sample's data size, and the README says how to change them. (Missing: not relevant unless AI components are added.)
- One database client is created and reused across requests. (At risk: this is best practice and documented in documentdb-driver, but the starter prompt doesn't require it; builder might still do it, but it's not enforced.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. (Missing: prompt asks verification but does not require an idempotent seed script.)
- /search returns a clear error for an empty query and when the embedding call fails. (Missing: there is no search/embedding component in the prompt.)
- Search results include the similarity score. (Missing: no search component requested.)
- Dependencies are pinned in `requirements.txt`. (Not applicable exactly for Node; the equivalent package-lock.json may be created, but the prompt doesn't require pinned dependencies.)
- Unit tests run without a live cluster. (Missing: prompt does not require tests or a DB-mocking strategy.)
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. (Missing: run-environment forbids provisioning; infra-as-code is not requested.)
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. (At risk: prompt doesn't require README contents; builder will likely add one but exact coverage is not specified.)
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. (At risk: prompt says 'DocumentDB' but doesn't require wording conventions; builder may use 'Azure DocumentDB' but could unintentionally use other names.)

## Questions for the prompt author

- Should the sample expose an HTTP REST API (recommended) or only a CLI/library surface? The chosen surface will change routes and example usage in the README.
- Which Mongoose version should be targeted (or should the builder pick latest compatible with Node.js 24)?
- Do you want an idempotent seed script and a minimal test suite that mocks the DB, or is manual verification against the live cluster sufficient?
- Should the sample include provisioning-as-code (Bicep/Terraform) for the cluster, or must it strictly avoid any cloud resource creation (use only the provided cluster)?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no installed skill named exactly 'DocumentDB'. Several documentdb-* skills are installed (e.g., documentdb-driver, documentdb-connection) that collectively cover DocumentDB topics; the wording could mislead a builder expecting a single skill named 'DocumentDB'.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose core banking ledger that stores every debit and credit as an immutable document... Use multi-document transactions... Enforce idempotency with a transactionRef field and unique index" | - | - | Prompt clearly states business problem and what sample demonstrates. |
| Workflow type | missing | no | - | - | Builder will implement a single-agent, no-orchestration sample (a standalone Node.js app with local CLI and/or HTTP endpoints). | Prompt doesn't say whether to produce CLI/API/web UI or any agent orchestration. |
| Language and runtime | specified | no | "Node.js 24 with npm and npx is available." (skill_md run environment) | - | - | Node.js 24 is provided by the run-environment fragment. |
| Driver and version | ambiguous | no | "Mongoose" (prompt) — no version specified | - | Builder will pick a recent Mongoose compatible with Node 24 (e.g., Mongoose 7.x) and the MongoDB 7.0 wire protocol. The project will pin versions in package.json (exact semver or package-lock). | Prompt names Mongoose but not which release; driver best-practices exist in installed skills but no explicit version. |
| Target service and tier | specified | no | "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable" (skill_md run environment) | - | - | Run environment supplies the exact cluster to use and forbids provisioning another cluster. |
| Authentication and secrets | specified | no | "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" (skill_md) | - | - | Secrets location and handling are specified in the run-environment notes. |
| Data model | specified | no | "accounts and transactions are defined as Mongoose schemas and models"; immutable transaction documents; account balance snapshot | - | Sharding/ shard key is not requested; builder will assume single logical collection (no explicit shard key) unless cluster or scale requirements demand otherwise. | The prompt and reference require schemas for transactions and accounts and immutability for transactions; shard key is not specified. |
| Sample data | missing | no | - | - | Provide a small idempotent seed script that creates a few example accounts and initial balances (e.g., 3 accounts, a handful of transactions). The seed script will detect existing data and upsert or skip to be safe to run twice. | The prompt asks to 'verify against the live cluster' in skill_md, but doesn't define sample data content, size, or seeding mechanism. |
| Queries and indexes | ambiguous | no | "Enforce idempotency with a transactionRef field and unique index" (prompt) | - | At minimum create a unique index on transactions.transactionRef. Also create an index on transactions.accountId and transactions.createdAt (e.g., { accountId:1, createdAt:-1 }) to support recent-activity queries. No additional vector or full-text indexes are required for this ledger sample. | Unique index is required and stated; additional helpful indexes are not specified and will be chosen by the builder. |
| AI components | not_applicable | no | - | - | - | No embeddings/LLM or vector search requested by the starter prompt. |
| App surface | missing | no | - | - | Builder will expose a small REST API: POST /transactions to post a transaction (body: accountId, amount, type/credit\|debit, transactionRef, optional metadata), GET /accounts/:id to read balance and recent transactions; and a CLI script (npm run seed) to load sample data. | Prompt does not specify whether the sample should be a CLI, API, or web UI or the exact routes/inputs/outputs. |
| Provisioning and deployment | specified | no | "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." (skill_md run environment) | - | - | Run environment mandates using the existing cluster rather than creating resources. The documentdb-azure-deployment skill exists if infra-as-code were requested, but the starter prompt & run notes direct against provisioning. |
| Run and test instructions | missing | no | - | - | Builder will add README steps: npm install, copy .env.example -> .env and set DOCUMENTDB_URI, npm run seed, npm start, run integration demo steps; tests: npm test running unit tests that mock the DB or use an in-memory/mock layer. | The prompt asks to verify against live cluster in run-environment, but explicit run/test commands and success criteria are not included. |
| Definition of done | missing | no | - | - | Acceptance: sample app can post transactions atomically (insert transaction + update account balance in a transaction), duplicate transactionRef attempts are rejected and do not change balance, transactions are not modified after posting. A small demo script exercises these cases against the provided cluster. | Prompt defines the core behavior but not an explicit checklist; builder will infer acceptance criteria from the required behaviors. |
| Constraints and non-goals | missing | no | - | - | Assume this is a sample/demo: no production HA, no multi-region failover, no CMK, and reasonable cost limits; focus on correctness of transactions and idempotency rather than full production security hardening. | No cost or compliance constraints are stated. |
| Repository conventions | specified | no | "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder" (skill_md). Use database named `sample_banking_03`. | - | Follow standard Node project layout (package.json, src/, test/, README.md); pin dependencies in package-lock.json. | Run-environment guidance specifies environment-variable use and DB name; other repo layout conventions are left to the builder. |
