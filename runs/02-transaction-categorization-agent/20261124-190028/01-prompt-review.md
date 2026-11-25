# 1. Prompt review: 02-transaction-categorization-agent

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (Node.js + LangChain agent to categorize transactions and expose a monthly-per-category aggregation). The run environment (Node 24, existing cluster sample_fintech_02, DOCUMENTDB_URI) is supplied in the skill_md, so a builder can start. Several implementation details are left unspecified (driver version, exact document shape and collection name, LLM/provider and env vars, taxonomy contents, seed data, exact agent invocation method, run/test/README conventions, indexes), and the builder will make reasonable defaults or rely on the installed documentdb-* skills for patterns and best practices.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 4: Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 6: Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- Define the fixed taxonomy (a concrete list of category strings) in the application code — the starter prompt requests a fixed taxonomy but does not provide the actual list; no installed skill will pick the categories.
- AI model/provider credentials from environment variables — skill_md sets DOCUMENTDB_URI but does not specify model/provider env vars; prompt omits where model credentials come from.
- .env.example that lists every setting with placeholders — skill_md asks never to write connection string and to use .env.example but does not provide the file; the prompt does not require creating it.
- Seed script that loads sample data and creates the index idempotently — prompt asks to read uncategorised transactions but does not provide sample-data source or a seed script; no skill will auto-generate sample dataset for this app.
- Vector index dimensions and vector index parameter choices — the run environment mentions the cluster is vector-capable, but the prompt does not require embeddings or vector indexes; reference expects vector-dimension alignment if vectors used.
- README with prerequisites, setup, run, and cleanup — prompt does not require writing a README or specify its contents.
- Unit tests that run without a live cluster — tests are not mentioned; building tests that mock DocumentDB is not covered by prompt or skills.
- Dependencies pinned in a requirements.txt (or equivalent pinned package.json entries) — prompt doesn't require pinned dependencies; gallery conventions expect this.
- Infrastructure-as-code for the cluster — the run environment already includes a cluster and the prompt forbids provisioning another; the reference asks for infra as code but starter prompt does not provide it.

## Questions for the prompt author

- Which LLM/provider and model should the sample use (OpenAI, Azure OpenAI, or a different provider)? What environment variable(s) hold the model API key and endpoint?
- What is the fixed taxonomy (explicit list of category strings) you want included in-code, or should the builder invent a reasonable finance taxonomy (e.g., Food, Travel, Utilities, Entertainment, Income, Other)?
- What is the collection name and exact field names for merchant, amount and date? (If unspecified, should the builder use 'transactions' with fields {merchant, amount, date, category}?)
- How should the LangChain agent be invoked in the sample: via an HTTP endpoint, a CLI command, or a background/cron-like process started by the app?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' (singular). No single skill named exactly 'DocumentDB' is installed — instead there are many documentdb-* skills (documentdb-driver, documentdb-connection, documentdb-indexing, etc.). The builder will interpret this as 'use the available DocumentDB skills'.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js LangChain agent that reads uncategorised transactions from DocumentDB ... assigns a category from a fixed taxonomy, writes the category back ... and exposes an aggregation endpoint showing monthly spend breakdown by category." | - | - | The business problem, user action, and what the sample demonstrates are clear. |
| Workflow type | specified | no | "LangChain agent" (implies single-agent workflow using LangChain). | - | - | Single LangChain agent is explicitly requested. |
| Language and runtime | specified | no | skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js runtime version is provided in the run-environment skill_md. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official mongodb Node.js driver (npm package 'mongodb'), current stable release compatible with MongoDB 7.0 (e.g., mongodb@5.x), and follow documentdb-driver guidance to instantiate a singleton MongoClient reused across the app. | The documentdb-driver skill gives patterns (singleton client) but does not pick an exact driver package/version; the builder must choose a specific npm package/version. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol...) is reachable... use database named sample_fintech_02." | - | - | Run environment explicitly gives the cluster tier and database to use. |
| Authentication and secrets | specified | no | skill_md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or .env.example with a placeholder." | - | - | Secrets location for the DocumentDB connection is stated. LLM/model credentials are not specified (see AI components). |
| Data model | ambiguous | no | "reads uncategorised transactions from DocumentDB" and writes category back to the document; skill_md: "use the database named sample_fintech_02" | documentdb-data-modeling | Assume a collection named 'transactions' in database 'sample_fintech_02' with documents shaped roughly as: { _id, transactionId, merchant (string), amount (number), date (ISODate), category (string\|null\|missing), metadata... }. Treat documents with category null/empty/missing as uncategorised. | Prompt and skill_md do not fix collection name or field names; documentdb-data-modeling can guide structure but won't pick exact names. |
| Sample data | missing | no | - | - | Builder will add an idempotent seed script (e.g., seed.js) that upserts a small set (dozens) of sample transactions across multiple months containing merchant, amount, and date fields so aggregation can be demonstrated. | No sample-data source, size, license, or loader is specified. |
| Queries and indexes | ambiguous | no | "exposes an aggregation endpoint showing monthly spend breakdown by category" (implies use of MongoDB aggregation pipeline). | documentdb-indexing | Implement aggregation with a pipeline that projects year-month from the ISO date (e.g., {$dateToString: {format: "%Y-%m", date: "$date"}}), groups by that and category, and sums amount. Create an index on { date: 1, category: 1 } (or separate single-field indexes) to help aggregation; use documentdb-indexing guidance for index choice. | Index shapes and full list of query patterns are not provided; documentdb-indexing skill can guide decisions but won't strictly mandate parameters. |
| AI components | missing | no | "uses prompt engineering to instruct the LLM to assign a category from a fixed taxonomy" and "LangChain agent" | - | Use LangChain's Node.js integration with an OpenAI-compatible chat model (e.g., gpt-3.5-turbo or another available model). Model API key provided via environment variable (e.g., OPENAI_API_KEY). The app will craft a prompt containing merchant and amount (and optionally date), the in-code taxonomy, few-shot examples, and explicit instruction to return a single category label. The code will validate / map any LLM output to one of the taxonomy values. | Neither provider nor exact model, nor env var names, are specified; these will materially affect integration code. |
| App surface | ambiguous | no | "exposes an aggregation endpoint showing monthly spend breakdown by category." | - | Provide an HTTP server (Express) with at least: GET /monthly-spend that returns JSON per-month/per-category totals. Also provide either POST /run-categorization or a CLI command (npm run categorize) to invoke the LangChain agent to process uncategorized transactions; the builder will choose one and document it. | Prompt does not state how the agent is triggered (HTTP endpoint, scheduler, or manual CLI); that choice will be made by the implementer. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Use the database named sample_fintech_02... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | - | The run environment explicitly directs use of the existing cluster; deployment/provisioning of cloud infra is not required for the sample run. |
| Run and test instructions | missing | no | - | - | Builder will include README/run instructions: npm install, copy .env.example to .env, set DOCUMENTDB_URI and model API key, run seed script, start server (npm start), call GET /monthly-spend and run POST /run-categorization or CLI to trigger categorization. Tests (if any) will be described but are not present by default. | No explicit run/test commands are provided. |
| Definition of done | missing | no | - | - | Acceptance criteria: (1) agent updates documents' category field only for documents that were uncategorized, (2) aggregation endpoint returns JSON grouping by year-month and category with correct sums matching the seeded data, and (3) connection string and model creds are read from env vars and not committed. | Prompt doesn't give explicit, testable acceptance criteria. |
| Constraints and non-goals | missing | no | - | - | Default constraints: do not provision new clusters or commit secrets; sample should be small and cost-conscious, not production-grade (no CMK or complex HA changes). | No cost/scale/compliance limits or non-goals were specified. |
| Repository conventions | missing | no | - | - | Follow standard Node.js repo layout: package.json, src/, routes/, scripts/seed.js, .env.example, README.md. Use 'Azure DocumentDB' naming in docs per gallery policy. Pin versions in package.json where reasonable. | Prompt does not provide a required structure or README conventions. |
