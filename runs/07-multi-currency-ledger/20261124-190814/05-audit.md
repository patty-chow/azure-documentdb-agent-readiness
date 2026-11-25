# 5. Best-practice audit: 07-multi-currency-ledger

**Verdict: fail** (4 followed, 6 not assessable, 1 not applicable)

No application files were produced in the workspace: the builder produced a design (03-build.json) and logged a few decisions, loaded many DocumentDB skills, but did not create the Node.js project, models, server, scripts or README. The reference requirements that the starter prompt explicitly requested are mostly present as design intent but not implemented (partly_met). Several gallery expectations were not produced (many prompt_silent). The installed DocumentDB skills provide authoritative public guidance for many checklist practices (connection-from-env, singleton client, TLS, idempotency unique-index, aggregation best-practices, TTL, ESR indexing, explain()), but a set of important developer-facing recipes are still only prior knowledge (Decimal128/currency math, explicit Mongoose-with-session recipe, exchange-rate indexing pattern, canonical seed dataset and idempotent seed script). Because the sample cannot be run or verified (no code created, no seed executed), the build fails to produce a runnable gallery sample. The product team should publish the few missing public recipes and a driver-compatibility table to prevent agents from making risky assumptions.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Decision D001 (approve build as 'ready_with_gaps') is an operator choice and is supported by the events/decisions log. It is a valid decision given the readiness report caveats. |
| D002 | I chose Node.js with Express and Mongoose (MongoDB driver via Mongoose) for the sample app. | prompt | sound | Decision D002 (choose Node.js + Express + Mongoose) directly follows the prompt and is recorded in decisions.jsonl and events.jsonl; evidence matches the prompt. |
| D003 | I chose mongoose 7.x (latest 7.x) to match Node 24 and provide schema/index convenience. | readiness_report | questionable | Decision D003 (choose Mongoose 7.x) cites the readiness_report as the reason. The readiness findings flagged a missing driver-compatibility mapping; choosing Mongoose 7.x is reasonable but should be validated against the cluster's actual server wire-version before locking. Marked 'questionable' because compatibility was assumed rather than verified and no dependency files were created to lock the version. |

Documentation gaps: 8 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 9 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Decimal128 for money | Store monetary amounts using Decimal128 or integer minor-units; do not use JavaScript Number for currency values. | A short authoritative sentence in the DocumentDB data-modeling docs: 'For monetary values use Decimal128 or integer minor-units; avoid JavaScript Number due to floating-point inaccuracy.' |
| Mongoose sessions pattern | When using Mongoose with sessions, pass { session } to all queries/updates and use session.withTransaction or explicit startTransaction/commitTransaction. | A short example page showing Mongoose session usage with DocumentDB, including session.withTransaction and passing { session } to model calls. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection from env | Read the cluster connection URI from an environment variable (e.g., process.env.DOCUMENTDB_URI) and do not commit credentials to source control; use a secrets store for production. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Singleton client reuse | Create a single shared MongoClient (singleton) for the process and tune connection-pool options (maxPoolSize, ...). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Require TLS | Require TLS on all client connections to Azure DocumentDB; do not disable TLS verification in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Retries & transaction retry | Implement retries for transient network and rate errors with exponential backoff and explicit retry loop for transactions. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Idempotency unique index | Protect against duplicate postings by creating a unique (or partial unique) index on transactions.idempotencyKey and using upsert/$setOnInsert or catching duplicate-key errors. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Idempotency TTL | If you only need idempotency for a bounded window, make idempotency records compact and expire them with a TTL index. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Aggregation pipeline hygiene | Write compact aggregation pipelines: $match early, project only needed fields, use allowDiskUse for large groups, and verify with explain("executionStats"). | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Compound index for ledger queries | Design compound indexes using ESR and create compound index for ledger queries (e.g., accountId + timestamp). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Explain usage | Use explain("executionStats") to confirm queries use intended indexes and watch docsExamined/keysExamined. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |

### How the app measures up

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Implement retries for transient network and rate errors with exponential backoff and explicit retry loop for transactions. | retries & fault tolerance | - | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Write compact aggregation pipelines: $match early, project only needed fields, use allowDiskUse for large groups, and verify with explain("executionStats"). | queries & aggregation | - | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |
| Design compound indexes using ESR and create compound index for ledger queries (e.g., accountId + timestamp). | indexing | - | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use explain("executionStats") to confirm queries use intended indexes and watch docsExamined/keysExamined. | monitoring & provisioning | - | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Store monetary amounts using Decimal128 or integer minor-units; do not use JavaScript Number for currency values. | data modeling | Searched: 'Azure DocumentDB Decimal128 currency', 'Cosmos DB MongoDB Decimal128 money' (no authoritative public guidance found). | prior_knowledge (no public address recorded) |
| When using Mongoose with sessions, pass { session } to all queries/updates and use session.withTransaction or explicit startTransaction/commitTransaction. | Mongoose usage | Searched: 'Mongoose sessions Azure DocumentDB withTransaction', 'Cosmos DB Mongoose session example' with no definitive DocumentDB-hosted Mongoose recipe found. | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Read the cluster connection URI from an environment variable (e.g., process.env.DOCUMENTDB_URI) and do not commit credentials to source control; use a secrets store for production. | secrets & configuration | 03-build.json lines 3-5 (design explicitly states reading DOCUMENTDB_URI from environment and not committing it). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Create a single shared MongoClient (singleton) for the process and tune connection-pool options (maxPoolSize, ...). | connection handling | 03-build.json line 3 (design: 'singleton Mongoose connection'). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Require TLS on all client connections to Azure DocumentDB; do not disable TLS verification in production. | security | Events: read_skill_resource documentdb-security/security-tls-required.md (events.jsonl) and 03-build.json note to not commit connection strings; design ensures TLS in the recommended URI (skill_md). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Protect against duplicate postings by creating a unique (or partial unique) index on transactions.idempotencyKey and using upsert/$setOnInsert or catching duplicate-key errors. | idempotency & indexing | 03-build.json line 3 explicitly states 'DB-level unique index on transactions.idempotencyKey' in the design and open_issues calls out verifying index creation at seed time. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| If you only need idempotency for a bounded window, make idempotency records compact and expire them with a TTL index. | idempotency & retention | Builder design did not state a bounded idempotency-window or TTL usage; no code present. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |

### Reference requirements

0 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| A .env.example lists every setting with placeholder values. | not_met | prompt_silent | Workspace contains no .env.example; 03-build.json open_issues line 14 lists .env.example as still to be created. | Add a .env.example file listing required variables (DOCUMENTDB_URI, NODE_ENV, PORT, SEED_SKIP, etc.) with placeholders. Suggested prompt addition: 'Create .env.example listing DOCUMENTDB_URI and other settings.' |
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | This ledger sample does not define /search; no code exists. | If a search endpoint is added, implement explicit validation returning 400 for empty queries and error-handling for embedding failures. |
| Search results include the similarity score. | not_met | prompt_silent | No search functionality present or implemented. | If adding search, include score fields returned from $search or cosmosSearch and document them in the API responses. |
| Dependencies are pinned in requirements.txt (or equivalent for Node). | not_met | prompt_silent | No package.json or package-lock.json in workspace; builder_report planned dependencies but did not create files (03-build.json open_issues). | Create package.json with explicit version pins (or include package-lock.json). Example: add "mongoose": "^7.0.0" and lock with npm ci / package-lock.json. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No test files exist in the workspace; builder_report did not create tests (03-build.json open_issues). | Add unit tests that mock Mongoose (e.g., use in-memory Mongo or sinon/stub) and document test command in README. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | 03-build.json open_issues line 14 explicitly notes IaC was not created; run policy also indicated cluster already exists. | Add a Bicep/ARM or Terraform example using Microsoft.DocumentDB/mongoClusters (or az documentdb CLI) in an infra/ directory, but mark as optional since the run environment provided the cluster. |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | not_met | prompt_silent | No README.md in workspace; 03-build.json open_issues calls out README.md as missing. | Add README.md with sample summary, prerequisites (DOCUMENTDB_URI), install, seed, run, and cleanup instructions. |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | not_met | prompt_silent | No README or docs to inspect; prompt and builder design use the term 'DocumentDB' but no published text to verify exact naming conventions. | When authoring README and docs, consistently use the term 'Azure DocumentDB' and include a short 'naming' sentence to distinguish it from Cosmos DB (RU) and Amazon DocumentDB. |
| A Node.js application that uses Mongoose as the ODM against Azure DocumentDB, with Mongoose models for ledger transactions and for exchange-rate documents, each kept in its own collection. | partly_met | builder_error | 03-build.json lines 1-5 (design asserts an Express + Mongoose app with models for transactions and exchange_rates). | Create the project files (package.json, src/, models/transaction.js, models/exchangeRate.js) and add a README. Add code that imports mongoose and defines the two models. |
| The transaction model has a currency field and a reference to an exchange-rate document, and each posted transaction is stored with the reference to the rate document it was recorded against. | partly_met | builder_error | 03-build.json line 3 (design declares models with exchange_rate reference and currency field). | Add Mongoose schemas implementing { amount: Decimal128\|Number, currency: String, exchangeRate: { type: ObjectId, ref: 'ExchangeRate' }, idempotencyKey: String, createdAt: Date } and export the models. |
| Every transaction posting carries an idempotency key, and posting the same key a second time does not create another ledger entry. | partly_met | builder_error | 03-build.json lines 3-4 (design lists DB-level unique index on transactions.idempotencyKey and idempotent seed/upsert idea). | Implement and create a unique (partial) index on transactions.idempotencyKey and add handler code that either uses findOneAndUpdate with $setOnInsert or catches duplicate-key errors and returns the existing document. |
| Posting a transaction performs its writes inside an Azure DocumentDB multi-document transaction using a Mongoose session (session.withTransaction or explicit start/commit/abort), and the model operations for the posting are passed that session. | partly_met | builder_error | 03-build.json line 3 (design: 'transactionally-protected transaction posting with idempotency behavior'). | Add code that starts a Mongoose session and uses session.withTransaction or startTransaction/commitTransaction and passes { session } to all Mongoose operations involved in the post. |
| An HTTP endpoint for posting transactions (e.g. POST /transactions) that accepts the transaction to record and persists it through the Mongoose models. | partly_met | builder_error | 03-build.json 'how_to_run' section (describes POST /transactions) and builder report summary. | Add Express route POST /transactions that validates payload (accountId, amount, currency, exchangeRateId, idempotencyKey), starts a session, and persists within the transaction. |
| An HTTP endpoint for querying balances that takes the requested base currency as a request parameter (e.g. base=USD) and returns the ledger balances expressed in that currency. | partly_met | builder_error | 03-build.json 'how_to_run' section (describes GET /balances?baseCurrency=USD) and design summary. | Add Express route GET /balances that accepts baseCurrency, runs the aggregation pipeline and returns results. |
| Balance conversion is a Mongoose aggregation pipeline executed by Azure DocumentDB: pipeline joins transactions to exchange-rate docs ($lookup), converts each amount into the base currency and sums the converted amounts, and the endpoint returns the pipeline's output. | partly_met | builder_error | 03-build.json line 3 (design asserts aggregation-based conversion and grouping). | Implement the aggregation pipeline in code (e.g., Transaction.aggregate([...]) with $lookup, $addFields or $project using Decimal128 arithmetic where appropriate, $group to sum per account, and return the aggregation result from the endpoint. |
| The connection string and model credentials come from environment variables; none appear in the repository. | partly_met | builder_error | 03-build.json lines 3-5 (design states: read DOCUMENTDB_URI from env at runtime; do not commit secrets). | Implement config/ env-loading code (e.g., dotenv) and ensure no secrets are checked in. Add .env.example (see next requirement). |
| One database client is created and reused across requests. | partly_met | builder_error | 03-build.json line 3 (design: 'singleton Mongoose connection'). | Implement a single connection module that connects once (mongoose.connect) and exports the connection; have server code import and reuse it. |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | builder_error | 03-build.json lines 3 and 5 (design includes idempotent seed script and instructions to run node scripts/seed.js). | Add scripts/seed.js implementing idempotent upserts for exchange rates and sample transactions and ensure index creation uses createIndex or upsert semantics. |
| The vector index dimensions match the embedding model's output. | not_checkable | could_not_determine | The ledger sample does not use embeddings or vector indexes; no files present to inspect. | If vectors are added, record the embedding model dims in README and set vector index dims accordingly when creating the index. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | could_not_determine | Not applicable to this ledger sample; no vector indexes were created. | Omit vector guidance for this sample or add a README section if vector features are introduced. |

