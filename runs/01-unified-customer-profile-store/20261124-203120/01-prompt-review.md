# 1. Prompt review: 01-unified-customer-profile-store

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided run-environment (skill_md) and installed DocumentDB skills are enough for a builder to start and complete a useful Node.js/Mongoose sample. Several implementation details are unspecified and will be chosen by the builder (e.g., HTTP endpoint vs exported handler, Mongoose version, collection name, seed-data shape and index choices). Nothing is blocking.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 6: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Provisioning and deployment, Constraints and non-goals |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 4: Workflow type, Data model, App surface, Repository conventions |
| Missing: builder will guess | 5: Driver and version, Sample data, Queries and indexes, Run and test instructions, Definition of done |
| Not applicable | 1: AI components |

## Reference requirements at risk

- The vector index dimensions match the embedding model's output — prompt does not request embeddings or vector indexes; no skill provides explicit sample values, so builder will likely skip vector-index tuning.
- Vector index parameters are chosen for the sample's data size and README says how to change them — not specified and not implied by prompt.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt implies loading data for verification in skill_md but does not require or describe an idempotent seed script.
- /search returns a clear error for an empty query and when the embedding call fails — the starter prompt does not include a search API or embedding calls.
- Search results include the similarity score — not applicable unless search/embedding functionality is added; prompt does not request this.
- Dependencies are pinned in requirements.txt — this is a Python-style requirement and not matched to a Node.js sample; prompt does not specify dependency pinning policy (package-lock.json or pnpm-lock.json will typically be used).
- Unit tests run without a live cluster — prompt/skill_md expect verification against a live cluster but do not require tests that run offline; nothing specifies mocking strategy.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — skill_md explicitly says a cluster already exists and forbids provisioning for this run, and the starter prompt does not ask for infra-as-code.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — README requirements are not stated in the starter prompt; builder will probably add a README but its required contents are not mandated.

## Questions for the prompt author

- Do you prefer an HTTP endpoint (e.g., Express POST /events) or an exported handler function (serverless) as the sample's entry point? This changes initialization pattern and connection reuse guidance.
- Which Mongoose version should be used (or should I use the latest stable compatible with Node.js 24)?
- What collection name do you prefer for the canonical profiles (e.g., 'customer_profiles' or 'customers')? Should customerId be enforced unique at the DB level?
- Do you want a seed script and sample data included (and if so, approximate size: a few dozen records vs hundreds)?
- Should the sample include unit tests that mock MongoDB, or end-to-end tests against the live cluster, or both?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js Mongoose service that receives customer events from multiple source systems (CRM, e-commerce, support) and upserts them into a canonical customer profile document in DocumentDB | - | - | Business problem and what the sample demonstrates are clearly stated in the starter prompt. |
| Workflow type | ambiguous | no | Using the DocumentDB skill, build a Node.js Mongoose service ... | - | Builder will produce a single long-running Node.js service (no multi-agent orchestration). Deliverable will be a self-contained service (Express app) rather than orchestrating multiple agents. | Prompt doesn't state agent framework or whether an exported handler (serverless) is preferred. |
| Language and runtime | specified | no | Node.js Mongoose service | - | - | The run-environment (skill_md) clarifies Node.js 24 with npm/npx is available. |
| Driver and version | missing | no | Mongoose service | documentdb-driver | Use Mongoose latest stable 7.x (compatible with Node.js 24) and the bundled MongoDB Node driver via Mongoose. DocumentDB driver-specific tuning follows documentdb-driver/documentdb-connection guidance. | Prompt does not pin a Mongoose version; documentdb-driver covers MongoClient patterns but not Mongoose package/version selection. |
| Target service and tier | specified | no | - | - | - | skill_md supplies the live cluster details: vector-capable cluster, compute tier M30, MongoDB 7.0 wire protocol, connection string in env var DOCUMENTDB_URI, and use DB sample_customer_360_01. |
| Authentication and secrets | specified | no | Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks. | - | - | Run-environment clearly mandates env var usage and not committing secrets. |
| Data model | ambiguous | no | canonical customer profile document ... stable customerId ... nested sub-documents for each source system's attributes (crm, e-commerce, support) | documentdb-data-modeling | Create a Mongoose model 'CustomerProfile' in collection 'customer_profiles' (or 'customers') with top-level fields: customerId (string, unique), crm (subdoc), ecommerce (subdoc), support (subdoc). No explicit shard key for the sample (single-shard / small dataset). | Prompt specifies document shape but not collection name or sharding strategy; documentdb-data-modeling can guide shard-key decisions if needed. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small synthetic seed dataset (dozens of events / ~50 profiles) generated by a seed script that upserts events for multiple sources. Seed data will be synthetic, not licensed, and suitable for demo purposes. | Prompt does not describe sample-data source, size, or license. skill_md expects the builder to create and load sample data for verification but doesn't specify details. |
| Queries and indexes | missing | no | merge with $set to avoid overwriting unrelated fields | documentdb-indexing | At minimum create a unique index on customerId (e.g., { customerId: 1, unique: true }). No other indexes unless query patterns are added; builder will document how to add more indexes. For small demo data, minimal indexing is sufficient. | Prompt requires $set merge behavior but does not specify indexes or index parameters; documentdb-indexing can be used to choose indexes if query patterns are added. |
| AI components | not_applicable | no | - | - | Sample does not include vector/embedding or semantic search components. Although the cluster is vector-capable, the starter prompt does not ask for any AI or embedding usage. | Reference requirements mention vector-index concerns but the prompt does not require AI features. |
| App surface | ambiguous | no | The service exposes an entry point that receives a customer event ... (e.g. an HTTP endpoint or an exported handler function). | - | Implement an Express HTTP POST /events endpoint that accepts JSON: { source: 'crm'\|'ecommerce'\|'support', customerId: '...', attributes: {...} } and returns success/failure JSON. Document the handler shape in README. | Prompt suggests either HTTP endpoint or exported handler; choice is left to builder. |
| Provisioning and deployment | specified | no | Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use. | documentdb-azure-deployment | - | Run-environment explicitly states a live cluster exists and forbids creating a new one for the sample run; builder should not provision infra during the sample build. |
| Run and test instructions | missing | no | - | - | README will contain commands: npm install, npm run seed (to load demo data), npm start (to start service), and npm test. Tests will be unit tests using Jest and will mock MongoDB (so they run without a live cluster). | Prompt and skill_md expect verification against the live cluster but do not provide explicit run/test commands; builder will create them. |
| Definition of done | missing | no | - | - | Acceptance criteria: service compiles and runs, POST events upsert into sample_customer_360_01.customer_profiles by customerId, seed script can load sample events idempotently, README documents setup and run steps. | No explicit acceptance checklist provided in the prompt. |
| Constraints and non-goals | specified | no | Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder ... Do not provision another cluster unless the run policy says Azure writes are allowed | documentdb-security | - | Run-environment gives constraints about secrets and provisioning; documentdb-security skill can be used for further hardening if desired. |
| Repository conventions | ambiguous | no | use a config file or `.env.example` with a placeholder, as the prompt asks. | - | Use conventional Node layout: package.json, src/ (app code), models/ (Mongoose schemas), scripts/seed.js, tests/, README.md, .env.example with placeholders. Dependencies listed in package.json and a lockfile (package-lock.json) will be committed; do not commit real secrets. | Prompt/skill_md specify .env.example but not other repository patterns; builder will follow usual Node sample conventions. |
