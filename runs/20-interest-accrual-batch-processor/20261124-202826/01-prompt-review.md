# 1. Prompt review: 20-interest-accrual-batch-processor

**Verdict: sufficient_with_assumptions**

The starter prompt is executable: it clearly defines a Node.js Mongoose daily batch processor that streams interest-bearing accounts and writes accrual journal documents with unordered bulk writes. Several implementation details (exact Node / Mongoose versions, model shapes, batch size, scheduling time, seed data, README / infra artefacts) are left to the builder's defaults or to follow-up. Installed skills provide useful guidance for driver best practices, indexing, data-model patterns, and connection tuning, so the build can start but will rely on assumptions for missing specifics.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 4: Driver and version, Data model, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — not required by the starter prompt and not enforced by installed skills; builder may omit or incompletely declare env vars.
- Vector index dimensions match the embedding model's output — not relevant to this sample (no embeddings are mentioned) and not covered by the prompt or skills for this use-case.
- Vector index parameters chosen for the sample's data size and README instructions to change them — not covered; builder will likely omit vector index tuning.
- Seed script loads sample data and creates the index, idempotent — the prompt doesn't mention providing a seed script; this is likely to be missed unless the builder adds one by assumption.
- /search returns a clear error for an empty query and when the embedding call fails — the sample has no /search route; this requirement is at risk.
- Search results include the similarity score — not applicable unless search/embeddings are added; at risk of being omitted.
- Dependencies are pinned in requirements.txt — a Python-style requirement; Node projects use package.json/package-lock.json, so this requirement is at risk or inapplicable as stated.
- Unit tests run without a live cluster — starter prompt doesn't require tests; absent further instruction, tests that mock the DB may not be provided.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt uses an existing cluster; infra-as-code is not requested and is likely to be missing.
- README covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt doesn't ask for a README explicitly; this may be omitted or incomplete.

## Questions for the prompt author

- What exact daily schedule/time and timezone should the job use by default (e.g., midnight UTC: "0 0 * * *")?
- Which Mongoose / mongodb driver versions should be targeted (or is using the latest Mongoose 7.x compatible with Node 24 acceptable)?
- What batch size should the cursor pagination group into for bulkWrite operations (e.g., 500, 1000)?
- Should journal insertions be idempotent across repeated runs (i.e., add a runId or dedupe key), or is simple insert-only sufficient? Should the journal document include run metadata (runId, host, timestamp)?
- Do you want infrastructure-as-code (Bicep/Terraform/az CLI) included to provision the DocumentDB cluster, or should the sample explicitly avoid provisioning and rely on the provided cluster?

## Contradictions and missing references

- The prompt says "Using the DocumentDB skill" but there is no single installed skill named exactly "DocumentDB skill"; many specialized documentdb-* skills are installed instead. The builder will need to choose which skill(s) to consult.
- Reference requirement item "Dependencies are pinned in requirements.txt" appears aimed at Python projects; the starter prompt requests a Node.js sample, so a requirements.txt artifact is not applicable.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose batch processor ... queries all active interest-bearing account documents ... computes accrued interest ... writes each accrual as an immutable journal document using unordered bulk writes" | - | - | The business problem, user scenario, and what the sample demonstrates are explicit. |
| Workflow type | specified | no | "batch processor that runs on a daily schedule" — a single scheduled process | - | - | This is a standalone scheduled app (no multi-agent orchestration required). |
| Language and runtime | specified | no | skill_md run environment: "Node.js 24 with npm and npx is available." | - | - | Node.js runtime (version 24) is provided in the run environment. |
| Driver and version | ambiguous | no | "Mongoose" (the ODM is specified) but no version | documentdb-driver | Use Mongoose 7.x (the current major compatible with Node 24) and the accompanying MongoDB driver 5.x; pin with caret ranges in package.json but include package-lock.json. | The documentdb-driver skill gives best-practice patterns (singleton client, reuse) but does not specify exact package versions. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol ...) is reachable ... connection string in env var DOCUMENTDB_URI" | - | - | The run environment explicitly identifies the live cluster and tier to use; the sample must use that cluster and database. |
| Authentication and secrets | specified | no | skill_md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or .env.example with a placeholder" | - | - | Secrets location and handling (env var, do not commit) are stated in the run environment. |
| Data model | ambiguous | no | "account and journal documents defined as Mongoose models" (document types required) but shapes/fields not specified | documentdb-data-modeling | Builder will define minimal models such as: Account {_id, balance: Number, interestRate: Number, status: 'active'\|'closed', interestBearing: Boolean, updatedAt, schemaVersion}, Journal {_id, accountId: ObjectId, runDate: ISODate, amount: Number, createdAt: ISODate, immutable: true}. The journal is an insert-only reference to the account._id. | The prompt requires models but leaves exact fields / schemaVersion / immutability conventions to implementer; data-modeling skill provides guidance but not concrete shapes. |
| Sample data | missing | no | - | documentdb-local-deployment | Include a seed script that creates a modest dataset (e.g., ~100 accounts with a mix of active/inactive and interest-bearing flags) and idempotently upserts by a unique account number so it can be re-run without duplication. | The starter prompt doesn't supply or require a seed dataset; none of the installed skills supply a concrete sample dataset for this banking example (documentdb-local-deployment helps manage local sample-data but not the specific seed content). |
| Queries and indexes | covered_by_skill | no | "queries all active interest-bearing account documents ... in cursor-paginated batches" | documentdb-indexing | Create an index to support the query, e.g., a partial/compound index on { status: 1, interestBearing: 1 } or a partial index with filter { status: 'active', interestBearing: true } to avoid COLLSCAN. Also create an index on journal.accountId for efficient lookups/aggregation if needed. | The prompt specifies the query pattern; documentdb-indexing gives index-selection guidance but the exact index definition (partial vs compound) must be chosen by the builder. |
| AI components | not_applicable | no | - | - | - | No embeddings or AI components are required by the prompt. |
| App surface | ambiguous | no | "runs on a daily schedule" — a scheduled batch processor | - | Implement as a Node.js process with a small CLI and scheduler: an npm script (e.g., "start": "node ./dist/worker.js") and a built-in schedule via node-cron or a run-once CLI flag. Default cron schedule: "0 0 * * *" (midnight UTC) and provide a --once flag for manual runs. | The prompt specifies 'daily' but not the exact cron expression, timezone, or whether a hosted scheduler (Azure Functions / WebJob / CronJob) is desired. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment | Do not create new cloud resources; use the existing cluster available in the run environment. If infra-as-code is required later, the documentdb-azure-deployment skill can be used to provide Bicep/az CLI artifacts. | The starter prompt does not ask the builder to provision infrastructure. The skill exists but the prompt's run environment says an existing cluster should be used. |
| Run and test instructions | missing | no | - | - | Include a README with commands: npm install, copy .env.example to .env and set DOCUMENTDB_URI, npm run seed, npm run start (or node --once). Provide a test command (npm test) where unit tests mock the DB so they run without a live cluster. | No explicit run/test commands are given in the prompt; the builder must author standard instructions. |
| Definition of done | missing | no | - | - | Accept when: (1) scheduled job can be run manually with --once; (2) it iterates all active interest-bearing accounts using a cursor and batch size, (3) computes interest correctly for sample inputs, (4) writes a per-account insert-only journal entry for the run using Model.bulkWrite with ordered: false for each batch, and (5) the run has been verified against the live cluster per the run environment. | No explicit acceptance criteria provided; the builder will need to define concrete checks. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep costs low by not provisioning new clusters, follow TLS and env-var secret handling, and do not attempt production DR/CMK/HA configuration in the sample. | No cost/usage constraints or non-goals are given; the builder will pick sensible defaults. |
| Repository conventions | ambiguous | no | skill_md: "Use the database named `sample_banking_20` ... connection string in env var DOCUMENTDB_URI. Never write its value ... use a config file or `.env.example` with a placeholder" | - | Follow a conventional Node layout: src/, scripts/, tests/, package.json, package-lock.json, .env.example with placeholders for DOCUMENTDB_URI and other settings (BATCH_SIZE, RUN_ONCE flag), README.md explaining purpose and run steps. | Some conventions (DB name, DOCUMENTDB_URI) are given; others (folder layout, exact env var names beyond DOCUMENTDB_URI) are not fully specified. |
