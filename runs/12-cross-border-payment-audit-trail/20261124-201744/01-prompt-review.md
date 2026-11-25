# 1. Prompt review: 12-cross-border-payment-audit-trail

**Verdict: sufficient_with_assumptions**

The starter prompt + provided run-time context give a clear goal (Node.js + Mongoose audit trail) and the live cluster details (DB name, tier, connection env var). Many implementation details (exact driver versions, API route names, seed data shape/size, tests, README / .env.example, IaC) are unspecified and will be decided by the builder's defaults or skills (index guidance, connection best-practices). Build can start, but several non-blocking assumptions will be made.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 7: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, Data model, App surface, Provisioning and deployment |
| Covered by a skill | 1: Queries and indexes |
| Ambiguous: builder will guess | 3: Workflow type, Driver and version, Repository conventions |
| Missing: builder will guess | 4: Sample data, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not specified in the starter prompt; skill.md suggests env usage but does not guarantee a complete .env.example will be created.
- The vector index dimensions match the embedding model's output — not applicable/mentioned in the prompt; nothing in skills forces inclusion; at risk because the reference requires it but the sample probably won't implement vector features.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — not covered; applies only if vector search is added.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — starter prompt didn't mandate a seed script; builder will likely add one but it's not specified.
- /search returns a clear error for an empty query and when the embedding call fails — the sample does not request a search endpoint, so this will probably be omitted.
- Search results include the similarity score — not applicable unless search is implemented; not specified.
- Dependencies are pinned in `requirements.txt` — mismatch with Node.js; the reference expects pinned dependencies but lists a Python idiom; for Node.js the analogous requirement (package-lock.json or pinned semver in package.json) is not specified.
- Unit tests run without a live cluster — starter prompt does not require tests and provides no mocking strategy; without explicit instruction, the builder must decide how to mock the DB so tests run offline.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — the run environment states a cluster already exists and discourages provisioning; the prompt did not ask for IaC, so this reference requirement is likely to be unmet.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — README is not specified in the prompt (skill.md gives some run-time constraints), so a full README could be omitted or incomplete unless the builder adds it.

## Questions for the prompt author

- Do you want a specific HTTP route pattern and verbs? (e.g., POST /payments/:ref/stage to append a stage, GET /payments/:ref/timeline to retrieve timeline).
- Which Mongoose and mongoose-compatible MongoDB driver versions should be pinned (or should I use the latest stable compatible with Node 24)?
- Should the sample include an idempotent seed script and how large should the sample dataset be (tiny: 5 payments, small: 100 payments, etc.)?
- Do you require infrastructure-as-code for the cluster (Bicep/Terraform) to be included in the repo, or must the sample only use the pre-provisioned cluster described in skill.md?
- How strict should application-layer immutability be enforced? Prefer Mongoose schema 'immutable' fields, pre('updateOne')/pre('replaceOne') hooks that throw, or both?

## Contradictions and missing references

- Reference requirements mention 'Dependencies are pinned in requirements.txt' (a Python convention) while the starter prompt and skill.md target a Node.js/Mongoose sample—this is a mismatch.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Node.js Mongoose audit trail service that writes an immutable document to DocumentDB at every stage of a cross-border payment lifecycle (initiated, routed, FX converted, settled) | - | - | Clear business problem and what the sample demonstrates (immutable audit trail per lifecycle stage). |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" (meta instruction) and a standard app request to build a service | - | Builder will produce a normal no-agent sample (Express API) rather than an agent-based sample; the 'DocumentDB skill' phrase is treated as guidance to use installed documentdb* skills for best-practice, not to include an agent framework. | Prompt addressed to a coding agent but does not require or name an agent framework; two competent builders could differ. |
| Language and runtime | specified | no | Node.js Mongoose | - | Use Node.js runtime available in run environment: Node.js 24 (from skill.md). | skill.md run-environment supplies exact Node version (Node.js 24). |
| Driver and version | ambiguous | no | Mongoose ODM (no version specified) | documentdb-driver | Builder will pick a recent Mongoose release compatible with Node 24 (e.g. mongoose ^7.x) and rely on mongoose's bundled mongodb driver; versions will be pinned in package.json/package-lock.json. | The documentdb-driver skill covers best practices (singleton MongoClient) but does not prescribe exact Mongoose version. |
| Target service and tier | specified | no | writes ... to DocumentDB | - | Use the pre-provisioned, reachable Azure DocumentDB cluster described in skill.md: compute tier M30, MongoDB 7.0 wire protocol, and the database named 'sample_banking_12'. | Run-environment (skill.md) contains the live-cluster and database name. |
| Authentication and secrets | specified | no | - | - | Connection string is read from environment variable DOCUMENTDB_URI at runtime (per skill.md); secrets must not be written to files or checked in. | skill.md explicitly instructs this; builder will create .env.example with placeholders (if following guidance), but the prompt did not explicitly require .env.example. |
| Data model | specified | no | Mongoose model for the audit documents; record a document per lifecycle stage | documentdb-data-modeling | Audit document schema includes: paymentReference (string), stage (enum: initiated, routed, fx_converted, settled), recordedAt (timestamp) used for ordering, plus an immutable unique _id. No shard key will be chosen (single-shard collection assumed unless scaling is requested). | The prompt requires audit documents per stage and an ordering field; documentdb-data-modeling skill can advise if embedding/refs needed. |
| Sample data | missing | no | - | documentdb-local-deployment | Builder will include a small idempotent seed script (e.g., a few payments each with 3–4 stage documents) that can be safely re-run without duplicating data (use upsert or dedupe by unique doc id). | Starter prompt does not specify sample data source, size, license, or exact load method. skill.md mentions verifying by loading sample data but doesn't define it. |
| Queries and indexes | covered_by_skill | no | Expose an aggregation endpoint that reconstructs the full timeline for a given payment reference | documentdb-indexing | Builder will implement an aggregation pipeline like [{ $match: { paymentReference } }, { $sort: { recordedAt: 1 } }] and create a supporting index (compound index on { paymentReference: 1, recordedAt: 1 }) to avoid collection scans. | The documentdb-indexing skill provides index-shape guidance; prompt specifies aggregation but not indexes, so builder will add the common compound index. |
| AI components | not_applicable | no | - | - | - | No embedding or LLM components are requested. |
| App surface | specified | no | Expose an aggregation endpoint that reconstructs the full timeline for a given payment reference | - | Builder will expose a REST endpoint (likely Express) such as GET /payments/:reference/timeline which accepts a payment reference and returns the ordered stage documents as JSON. The service will also provide endpoints to insert stage audit docs (e.g., POST /payments/:reference/stage). | Prompt names an aggregation endpoint; route names, HTTP verbs and auxiliary endpoints are left to the builder. |
| Provisioning and deployment | specified | no | - | - | Do not provision a new cluster; use the existing live cluster in skill.md. The documentdb-azure-deployment skill exists if IaC is later requested, but the prompt explicitly assumes a reachable cluster. | skill.md run-environment explicitly says a cluster is already provisioned and reachable. |
| Run and test instructions | missing | no | - | - | Builder will add npm scripts (start, seed, test) and a README describing setup (npm install, copy .env.example -> .env, set DOCUMENTDB_URI, npm run seed, npm start). Unit tests will probably mock the DB to run without a live cluster. | No explicit run/test commands were provided in the starter prompt; run-environment gives some verification guidance but not explicit commands. |
| Definition of done | missing | no | - | - | Builder will define done as: (1) able to insert stage audit docs (one per stage), (2) attempt to update/replace an audit doc is rejected by application-layer guards, and (3) aggregation endpoint returns chronologically ordered stage documents for a given payment reference. | Prompt implicitly defines goals but no explicit acceptance criteria checklist was given. |
| Constraints and non-goals | missing | no | - | - | Keep sample small to avoid costs; do not provision infrastructure; do not implement full production security beyond TLS and env-driven secrets; do not include vector search or embedding features. | No explicit cost or compliance constraints were specified. |
| Repository conventions | ambiguous | no | - | - | Builder will use a typical Node repo layout (package.json, src/, tests/, README.md, .env.example), follow the run-environment guidance about not writing the connection string into files and provide a .env.example with placeholders. | Prompt did not mandate README sections, license, dependency pinning conventions, or tests layout; skill.md suggests some conventions but not a full repo policy. |
