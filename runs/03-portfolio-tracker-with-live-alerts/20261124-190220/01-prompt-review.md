# 1. Prompt review: 03-portfolio-tracker-with-live-alerts

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided run environment (skill_md) and installed DocumentDB skills are enough to start building the Node.js/Mongoose portfolio service. Several implementation details (exact schema fields, driver versions, change-stream options, webhook payload/recording, seed data and run/test instructions, and repository README/fixtures) are not specified and will be chosen by the builder as reasonable defaults unless the author states otherwise.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 6: Driver and version, Data model, Queries and indexes, App surface, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 4: Workflow type, Sample data, Run and test instructions, Definition of done |
| Not applicable | 1: AI components |

## Reference requirements at risk

- Exact Mongoose model fields for positions and alert rules (starter prompt mentions collections but not the required fields). Reason: prompt does not enumerate schema fields; no installed skill provides the exact field list.
- Change stream option 'fullDocument: "updateLookup"' and explicit change-stream configuration. Reason: prompt asks to open a change stream but does not state fullDocument option; installed skills provide connection guidance but not this specific option.
- Price-change detection detail (only trigger evaluation on currentPrice change vs any update). Reason: prompt says detect price updates but not the exact update-event filtering logic.
- Alert rule metric types and evaluation semantics (must support both 'price' and 'pnl' with pnl computed as (currentPrice - avgCost) * shares). Reason: prompt says evaluate rules but does not enumerate metric types or formula; no skill supplies this exact rule set.
- Webhook payload schema and storing webhook delivery status. Reason: prompt says 'fire a webhook' but does not detail payload contents or whether to persist HTTP status; no installed skill prescribes the payload.
- HTTP endpoint contract (GET /portfolio/:userId/summary returning total P&L and sector allocations). Reason: prompt asks for the aggregation but does not explicitly require an HTTP endpoint and route; reference requires it.
- Idempotent seed script that can be run twice without duplicating data. Reason: prompt does not request seed scripts; local-deployment skill provides best practices but no concrete seed artifact.
- Pinned dependency versions (e.g., package.json lock or explicit pinned versions). Reason: prompt does not ask to pin dependencies.
- Unit tests that run without a live cluster. Reason: prompt does not require tests and no skill provides automated unit-test scaffolding for offline tests.
- Infrastructure-as-code for provisioning the DocumentDB cluster (Bicep/Terraform). Reason: prompt assumes an existing cluster and does not request IaC; reference may expect provisioning code but prompt forbids creating another cluster.
- README covering what the sample shows, prerequisites, setup, run, and clean-up. Reason: prompt does not mention README; builder will likely add one but it's not specified.

## Questions for the prompt author

- Which Mongoose and mongodb driver versions should be used (or should the builder pick the latest stable versions compatible with MongoDB 7.0)?
- How should webhook deliveries be handled on failure? (e.g., single attempt with logging, retry policy with backoff, or push into a durable 'webhook deliveries' collection to retry later?)
- Do you require a seed script and README as part of the delivered sample (the reference gallery typically expects them)? If so, any required minimal dataset size or example users to include?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB skill' — the environment contains several documentdb-* skills (documentdb-driver, documentdb-connection, etc.). The builder will interpret this as 'use the available DocumentDB-related skills/guidance'.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose portfolio service that stores positions and alert rules in DocumentDB. Open a change stream on the positions collection to detect price updates, evaluate each alert rule document, and fire a webhook when a threshold is breached. Include an aggregation that computes portfolio P&L and sector allocation." | - | - | Prompt clearly defines the app purpose, the collections involved, reactive change-stream behavior, and the aggregation requirement. |
| Workflow type | missing | no | - | - | Assume a single, long-running Node.js service (no agent framework) that runs change streams and exposes HTTP endpoints. | Prompt does not say whether to build via an agent, CI orchestration, or simply produce a standalone sample app. |
| Language and runtime | specified | no | "Node.js Mongoose" (starter prompt) and skill_md: Node.js 24 is available on the run environment. | - | - | Runtime constraint in skill_md: Node.js 24 with npm/npx available. |
| Driver and version | ambiguous | no | "Mongoose" (starter prompt) but no version specified. | documentdb-driver | Builder will pick a recent stable Mongoose that is compatible with MongoDB 7.0 (e.g., Mongoose 7.x with the mongodb driver 5.x). Code will use current Mongoose API and a singleton MongoClient pattern. | Installed documentdb-driver skill covers connection pattern (singleton) but does not mandate package versions. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... use database named `sample_fintech_03`. Connection string in env var DOCUMENTDB_URI." | - | - | The run environment explicitly provides the cluster details and connection URI variable; builder must use that cluster and DB name. |
| Authentication and secrets | specified | no | skill_md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder." | - | - | Secrets handling is explicitly constrained in skill_md. |
| Data model | ambiguous | no | "stores positions and alert rules in DocumentDB" (prompt) — no schema fields listed. | documentdb-data-modeling | Builder will create two Mongoose models, Position and AlertRule, with fields sufficient for alert evaluation: Position { userId, symbol, shares:Number, avgCost:Number, currentPrice:Number, sector:String, updatedAt:Date, schemaVersion } and AlertRule { userId, scope:('symbol'\|'global'), symbol?, metric:('price'\|'pnl'), comparison:('>'\|'<'), threshold:Number, webhookUrl:String, active:Boolean, createdAt }. | The documentdb-data-modeling skill gives modeling patterns but does not specify exact field names/required fields; the reference requirements list the preferred fields (and the builder will most likely adopt them). |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will include a small idempotent seed script (e.g., seed.js) that inserts a few example positions and alert rules and can be safely re-run (upsert or dedupe by a unique key). Typical seed size: handful of users, ~10 positions, a few alert rules. | Prompt does not mention sample data or a seed script. documentdb-local-deployment gives best practices but no concrete seed data. |
| Queries and indexes | ambiguous | no | "Include an aggregation that computes portfolio P&L and sector allocation" and "Open a change stream on the positions collection" (prompt). | documentdb-indexing | Builder will implement the aggregation using Mongoose.aggregate() to compute total P&L and per-sector market values and percentages. Reasonable indexes: single-field indexes on userId and on symbol; possibly a compound index on { userId:1, symbol:1 } and an index on sector for efficient grouping. Change streams do not require special indexes but code will use fullDocument updateLookup to get the latest document. | Index guidance exists in the documentdb-indexing skill, but the prompt does not demand any specific indexes or index parameters. |
| AI components | not_applicable | no | - | - | - | No embeddings or other AI components are requested by the starter prompt. |
| App surface | ambiguous | no | "build a Node.js Mongoose portfolio service" and "Include an aggregation that computes portfolio P&L and sector allocation." | - | Builder will expose a small HTTP API (Express) with at least GET /portfolio/:userId/summary returning { totalPnl, sectors:[{ sector, marketValue, percentage }] }. The service will also run the background change-stream listener to evaluate alerts. | Prompt asks for a service but does not enumerate endpoints; the reference expects GET /portfolio/:userId/summary. |
| Provisioning and deployment | specified | no | skill_md: existing cluster reachable; "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | Use the provided live cluster (DOCUMENTDB_URI) and do not create new Azure resources for the sample run. |
| Run and test instructions | missing | no | - | - | Builder will add README with commands: npm install; npm run seed (or node scripts/seed.js); npm start; and example curl to call GET /portfolio/:userId/summary. Tests: unit tests (jest) for aggregation logic; integration runnable if DOCUMENTDB_URI set. | skill_md provides runtime constraints but no run/test commands; these must be created by the builder. |
| Definition of done | missing | no | - | - | Builder will treat 'done' as: app connects to sample_fintech_03 using DOCUMENTDB_URI; Mongoose models are defined; change stream watches positions with fullDocument, detects price changes, queries alert rules, and sends POST webhooks; aggregation endpoint returns correct total P&L and sector allocations for a sample user; a seed script loads sample data; logs/README show what was executed. | No explicit acceptance criteria in prompt; the above will be used as practical completion criteria. |
| Constraints and non-goals | ambiguous | no | skill_md: "Never write its value into any file, log, README or test fixture... Do not provision another cluster unless allowed." | documentdb-security | Builder will avoid storing secrets in code, will not attempt provisioning, will not fully productionize security (e.g., no CMK, no Private Endpoint) but will note them in README as non-goals for the sample. | Security constraints about secrets and cluster provisioning are stated; cost/production constraints are not fully specified. |
| Repository conventions | ambiguous | no | skill_md: recommends `.env.example` placeholders and not storing the real connection string. | documentdb-local-deployment | Builder will follow common sample repo layout: README.md, package.json, src/ (app code), scripts/seed.js, .env.example, tests/, and comment code with references to Azure DocumentDB. README will include setup/run/cleanup. | Prompt/skill_md instruct .env.example usage but does not mandate full repository layout; builder will adopt a conventional layout. |
