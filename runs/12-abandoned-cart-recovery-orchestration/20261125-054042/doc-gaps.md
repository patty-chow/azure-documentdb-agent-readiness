# Documentation and tooling gaps: 12-abandoned-cart-recovery-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Abandoned-cart partial/compound index example

- **What was missing:** A concise, copy-paste snippet in the public docs showing the recommended compound index for abandoned-cart queries (e.g., { status: 1, lastUpdated: 1 }) and an example of using a partialFilterExpression for status='abandoned'.
- **Where the agent looked:** Installed documentdb-indexing skill resources and Microsoft Learn quickstarts (skill resources returned index-compound-esr.md but no small, concrete abandoned-cart snippet).
- **Effect on this build:** The builder created only a lastUpdated index (single-field) and did not add the recommended compound or partial index; this likely increased RU and left the pipeline to scan more documents than necessary. The sample still ran but did not follow the indexing best practice.
- **Suggested fix (sample_or_quickstart):** Short sample page titled 'Indexing for time-window queries (abandoned-cart example)'. Outline: intent, query shape, ESR rule reminder, 2 copy-paste createIndex examples (1) compound: db.carts.createIndex({ status: 1, lastUpdated: 1 }) and (2) partial: db.carts.createIndex({ lastUpdated: 1 }, { partialFilterExpression: { status: 'abandoned' } }), plus a note about awaiting index creation and verifying with explain('executionStats').

## [high] DocumentDB driver retryWrites guidance (agent rule)

- **What was missing:** An agent-kit rule or short enforcement guidance that tells sample authors and automation to set retryWrites=false (or to rely on the portal-provided connection string) for vCore DocumentDB clusters.
- **Where the agent looked:** documentdb-connection skill and public quickstarts (quickstart text mentions connection strings but no automated agent rule enforced this).
- **Effect on this build:** The sample's db.js left retryWrites: true, which contradicts the service-recommended setting. This is a subtle but important behavioral difference that can cause incorrect retry behaviour in DocumentDB.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: when generating db client config for Azure DocumentDB, set retryWrites=false (or ensure connection string contains retryWrites=false) and tls=true. Provide the exact code snippet for Node.js MongoClient options and a short rationale explaining the service recommendation.

## [high] Explain() and pre-run verification snippet

- **What was missing:** A short verification script/template that runs explain('executionStats') for the sample's main query and records RU/doc to help authors test before scaling.
- **Where the agent looked:** documentdb-query-optimizer skill resources; skills explain the need but a one-line copy-paste verify script was not present in the sample's repo.
- **Effect on this build:** No explain() verification was performed by the sample, so index efficacy wasn't formally recorded; developer relied on manual index inspection instead.
- **Suggested fix (sample_or_quickstart):** Add a small script verify_index.js that runs the abandoned-cart query with explain('executionStats') and prints key metrics (totalDocsExamined, totalKeysExamined, executionTimeMillis) and a README section explaining how to interpret numbers.

## [medium] .env.example completeness & discoverability

- **What was missing:** The shipped .env.example did not include every env variable the code references (e.g. TWILIO_FROM_NUMBER and optional DB_NAME). There is no single small doc that lists 'env vars this sample checks'.
- **Where the agent looked:** Repository .env.example and README; no separate env-vars list or table.
- **Effect on this build:** Users might run the sample and miss provider-specific placeholders (e.g. TWILIO_FROM_NUMBER), or they may not know optional overrides such as DB_NAME, leading to confusion when wiring real providers.
- **Suggested fix (discoverability):** .env-vars page in sample README or a one-line table in README listing every environment variable the sample reads (DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, SENDGRID_API_KEY, DB_NAME). Mark which are required vs optional and give placeholder examples.

## [medium] Append-only / audit logging pattern for recovery logs

- **What was missing:** Public guidance specific to DocumentDB about append-only 'recovery_logs' vs updating carts in-place (trade-offs: auditability, cost, partitioning implications). The earlier open search did not return a DocumentDB-specific 'append-only notification logs' recommended pattern.
- **Where the agent looked:** Searches recorded during discovery: 'Azure DocumentDB append-only notification logs best practice' and related terms (no useful public DocumentDB-specific guidance found).
- **Effect on this build:** The builder implemented a simple recovery_logs insertion (insertOne) — acceptable for sample purposes — but an explicit recommendation would have guided design choices (append-only vs cart update, index shape for logs, partitioning guidance).
- **Suggested fix (learn_doc):** A short 'Notification & audit logging patterns' page describing when to use append-only logs (and how to partition them), example schema for recovery_logs, example indexes (cartId + sentAt), retention strategies (TTL vs archival), and notes on idempotent write patterns for avoiding double-sends.

