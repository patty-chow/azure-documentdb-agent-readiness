# 1. Prompt review: 20-open-banking-api-cache-layer

**Verdict: sufficient_with_assumptions**

The starter prompt is clear about the primary goal (a Node.js Mongoose caching layer with stale-while-revalidate and a TTL index) and the run-environment skill_md fills in the important runtime details (Node 24, DOCUMENTDB_URI, database name sample_fintech_20, live cluster). Several implementation details (Mongoose version, exact schema/collection name, middleware vs wrapper, TTL field semantics, README/seed/infrastructure artifacts) are left to the builder's defaults. These are not blocking but will be assumed by the implementer.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 6: Workflow type, Driver and version, Data model, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example listing every setting with placeholder values — skill_md mandates using DOCUMENTDB_URI but the starter prompt doesn't require a .env.example; likely to be omitted unless the builder adds it.
- A seed script that loads sample data and creates the index, and can be run twice without duplicating data — the prompt doesn't request a seed script; implementer may or may not include one.
- Dependencies pinned (the reference expects a requirements.txt style pinning) — the prompt names Node/Mongoose but does not require pinned dependency versions in package.json; the builder will need to decide pinning format.
- Unit tests that run without a live cluster — the prompt doesn't ask for tests or mocking strategy; this is likely to be omitted or minimal unless requested.
- Infrastructure for the cluster provided as code — prompt and skill_md indicate use of an existing cluster and explicitly discourage provisioning; infra-as-code will probably not be included.
- A README that covers what the sample shows, prerequisites, setup, run, and clean-up — the prompt does not require a README; implementer may add one, but it's not guaranteed by the prompt.

## Questions for the prompt author

- Do you want an Express middleware (server-side) or a client wrapper function (to wrap fetch/axios) as the canonical sample, or should the sample include both?
- Which TTL semantics do you prefer: store an expiresAt Date and create a TTL index with expireAfterSeconds: 0, or store cachedAt and use expireAfterSeconds equal to the TTL duration? What default TTL (seconds/minutes) should the sample use?
- Which Mongoose version should be targeted (if any)? I will default to Mongoose ^7 for Node 24 unless you specify otherwise.
- Should the repo include a small seed script and automated unit tests that run without a live cluster (e.g., using an in-memory Mongo mock), or is a manual demo against the provided live cluster sufficient?
- Do you require infrastructure-as-code for the DocumentDB cluster (Bicep/Terraform), or must the sample avoid provisioning and use the provided cluster only?

## Contradictions and missing references

- Prompt: "Using the DocumentDB skill" — there is no installed skill named exactly "DocumentDB"; there are multiple documentdb-* skills installed. The prompt's reference to a single 'DocumentDB skill' is ambiguous.
- skill_md claims the cluster is "vector-capable" and mentions vector indexes, while the starter prompt does not use vector search; this is not a contradiction but an unused capability.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js Mongoose caching layer ... checks DocumentDB for a cached response document with a TTL index ... Implement a stale-while-revalidate pattern" | - | - | Business problem and demo behavior (cache + stale-while-revalidate for open banking API calls) are explicit. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" | - | Builder will implement as a single-process Node.js library/middleware (no multi-agent orchestration)—i.e., a sample Express middleware or wrapper function used in a demo app. | The prompt references a 'DocumentDB skill' but doesn't specify agent framework or whether the build should run as an agent workflow. No installed skill named exactly 'DocumentDB' — multiple documentdb-* skills are present. |
| Language and runtime | specified | no | "Node.js Mongoose" and skill_md: "Node.js 24 with npm and npx is available." | - | - | Node.js 24 (from skill_md) is the expected runtime. |
| Driver and version | ambiguous | no | "Mongoose caching layer" (no version given) | documentdb-driver | Use Mongoose ^7 (latest 7.x compatible with Node 24) and the matching mongodb driver bundled with that Mongoose version; pin to a semver range in package.json (e.g., "mongoose": "^7.5.0"). | Prompt names Mongoose but gives no version. documentdb-driver skill covers best practices for client reuse but does not fix an exact Mongoose version. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, ...). Use the database named `sample_fintech_20`. The connection string is in env var DOCUMENTDB_URI." | - | - | Cluster and database to use are specified in skill_md; the build must use the live cluster and sample_fintech_20 database. |
| Authentication and secrets | specified | no | skill_md: "connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder." | - | - | How to obtain connection string and secrecy requirements are stated in skill_md. |
| Data model | ambiguous | no | "checks DocumentDB for a cached response document with a TTL index" | documentdb-data-modeling | Builder will create a collection named `api_cache` in database `sample_fintech_20` with a Mongoose schema like { key: String (unique), response: Mixed, statusCode: Number, headers: Mixed, cachedAt: Date, expiresAt: Date }. Use `key` derived from request URL+query+body. TTL will be implemented on the expiresAt field. | Prompt requires cache documents and TTL but doesn't specify collection name, exact fields, or whether to store headers/status; data-modeling skill can guide choices but not the exact schema. |
| Sample data | missing | no | - | - | No large sample dataset will be provided. Builder will include a small seed/demo script that inserts one or two cached responses for demonstration, or rely on live upstream API calls for runtime demo. | Starter prompt does not request sample data or a seed script; this will likely be added by the implementer but is not specified. |
| Queries and indexes | ambiguous | no | "checks DocumentDB for a cached response document with a TTL index" | documentdb-indexing | Implement a TTL index in code on an `expiresAt` Date field using Mongoose schema.index({ expiresAt: 1 }, { expireAfterSeconds: 0 }) so documents expire at the expiresAt time. Query pattern will be findOne({ key }). Update uses upsert. | The prompt requires a TTL index but doesn't fix whether expireAfterSeconds or an expiresAt-date-with-0 is used; documentdb-indexing skill can advise but the exact choice is left to implementer defaults. |
| AI components | not_applicable | no | - | - | - | No embeddings or LLMs are needed for this caching sample. |
| App surface | ambiguous | no | "intercepts open banking API calls" and "Provide a function or middleware" (from reference requirements) implied by the prompt | - | Implement as an Express-compatible middleware plus an exported wrapper function that can be used around an HTTP client (fetch/axios). Provide a small demo Express route invoking the middleware/wrapper to show behavior. | Prompt asks for interception but doesn't mandate framework or example endpoints — sample will need a demonstrator (likely Express) chosen by the implementer. |
| Provisioning and deployment | missing | no | skill_md: "Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | documentdb-azure-deployment | No infrastructure-as-code for cluster provisioning will be included. If infra is needed, the builder may include optional Bicep/Terraform scripts but by default will not provision resources. | Starter prompt expects use of an existing cluster; the gallery's infra-as-code requirement is not satisfied by the prompt. |
| Run and test instructions | missing | no | skill_md describes runtime environment but the prompt does not request README or explicit commands | - | Builder will add a README with install (npm install), env var setup (.env.example), seed/run commands (npm run seed, npm start), and a simple test/demo manual steps. Automated unit tests may be minimal or omitted unless requested. | skill_md gives environment constraints but not the explicit run/test commands required for a gallery sample. |
| Definition of done | missing | no | - | - | Builder will treat a working demo (middleware + demo route + TTL index created + verified background refresh on stale) plus a short README as the acceptance criteria. | No explicit acceptance criteria provided in prompt. |
| Constraints and non-goals | missing | no | skill_md: "Never write its value into any file, log, README or test fixture" (constraint about secrets) | documentdb-security | No additional cost/scale constraints are given; builder will adhere to not provisioning new clusters and to keep sample usage small. | General cost or compliance constraints are not specified; only a few security constraints are present in skill_md. |
| Repository conventions | ambiguous | no | skill_md: "Use the database named `sample_fintech_20`... Read connection string from DOCUMENTDB_URI... use a config file or `.env.example` with a placeholder." | documentdb-mcp-setup | Builder will use a conventional Node layout (package.json, src/, test/, README.md), include a .env.example showing DOCUMENTDB_URI and any other env vars, and name the project README to use 'Azure DocumentDB' per gallery conventions. | Some conventions are provided (db name, env var rules) but others (folder layout, tests structure) are left to the implementer. |
