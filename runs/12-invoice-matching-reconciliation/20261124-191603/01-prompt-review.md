# 1. Prompt review: 12-invoice-matching-reconciliation

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided skill_md gives enough to start a Node.js LangChain + Mongoose sample that reads unmatched invoices, calls an LLM extractor, scores candidate POs and writes results back, and uses in-session agent memory. Several important implementation details (LLM provider/model, exact schema/field names, index shapes, API surface, tests, seed-script and README conventions) are left unspecified and will be decided by the implementer or filled by the installed skills.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Language and runtime, Target service and tier, Authentication and secrets |
| Covered by a skill | 3: Queries and indexes, Provisioning and deployment, Repository conventions |
| Ambiguous: builder will guess | 4: Driver and version, Data model, App surface, Definition of done |
| Missing: builder will guess | 4: Sample data, AI components, Run and test instructions, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Instantiate a LangChain agent named exactly "LangChain agent" — prompt asks for LangChain agent but does not require that exact name; implementer may choose a different identifier.
- Include explicit Mongoose models/schemas for invoices and purchase orders and use those models for reads and writes — prompt requires Mongoose but does not explicitly demand named, complete schemas; implementer will likely create them but it's not enforced.
- Query invoices by an exact field like status == "unmatched" — prompt says read unmatched invoices but doesn't specify the exact field name/value to use; implementer will choose conventions.
- LLM extraction must produce invoiceNumber, vendorName, totalAmount, invoiceDate, lineItems, referencedPoNumber — prompt requires structured extraction but does not enumerate these exact required fields.
- Search POs by amount within a configurable tolerance — prompt requires search by amount but does not require a configurable tolerance parameter.
- Implement fuzzy vendor/string similarity algorithm — prompt requires scoring but does not mandate fuzzy string similarity or a particular algorithm.
- Provide match score breakdown fields (vendorScore, amountDelta, combinedScore) — prompt asks to score candidates but not to include the exact breakdown fields named by the reference.
- Write back exact reconciliation fields (matchedPoId, matchScore, matchDetails including vendorScore and amountDelta, matchedAt, and setting status to "matched") — prompt says write results back but does not mandate these exact fields/field names.
- LLM provider/model and embedding dimensions come from env vars — prompt does not specify LLM provider or env var names for credentials.
- Vector index dimensions must match embedding model output — no embedding model or vector-dimension value specified; risk of mismatch if embeddings are used.
- Vector index parameters and README guidance for scaling — not specified in prompt or skill_md; implementer must choose and document them.
- Idempotent seed script that loads sample data and creates the index and can be run twice without duplicating data — prompt/skill_md imply seeding may happen but no explicit idempotent seed script is required.
- /search returning clear errors for empty query and when embedding call fails — prompt does not define a /search API or error behaviors, so this is likely to be omitted.
- Search results include similarity score — the prompt requests scoring but does not require exposing similarity scores in search responses.
- Dependencies pinned in a requirements.txt (or equivalent lock file) — prompt does not require pinned dependencies; Node samples normally use package.json and package-lock.json but reference expectation may not be met.
- Unit tests that run without a live cluster — not specified; tests may require a live cluster unless the implementer creates mocks.
- Infrastructure-as-code for the cluster (Azure DocumentDB resource type) — prompt assumes an existing cluster and does not request IaC; the sample may omit IaC.
- README covering what the sample shows, prerequisites, setup, run, and clean-up — prompt/skill_md do not provide a full README requirement; implementer must add it but it is at risk of being shallow or omitted.

## Questions for the prompt author

- Which LLM provider and model do you want used for structured-extraction and for embeddings (if any)? (e.g., OpenAI gpt-4o / text-embedding-3-small, Anthropic Claude etc.)
- Should the agent be instantiated with the literal name "LangChain agent" (exact string) as the reference requirement expects?
- How should manual corrections be exposed: HTTP API endpoints (recommended) or a CLI/interactive UI? Provide desired endpoint names if HTTP.
- Should agent memory be strictly session-scoped and ephemeral (never persisted between runs), or allow optional persistence if the implementer adds it?
- Do you require an idempotent seed script and unit tests that run without a live cluster (e.g., using in-memory mocks), or is a live-cluster verification enough?

## Contradictions and missing references

- "Using the DocumentDB skill" — the prompt names a generic 'DocumentDB skill' but no single installed skill has that exact name. Several documentdb-* skills are installed and will be used instead.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "reads unmatched invoices from DocumentDB, extracts structured fields using an LLM tool, searches DocumentDB for candidate PO matches by amount and vendor, scores each candidate, and writes the reconciliation result back." | - | - | Business problem and sample's objective are clear. |
| Workflow type | specified | no | "build a Node.js LangChain agent" | - | - | Single-agent orchestration using LangChain is requested. |
| Language and runtime | specified | no | skill_md: "Node.js 24 with npm and npx is available." | - | Use Node.js v24 (as stated in skill_md). | Prompt does not set a version, but skill_md does. |
| Driver and version | ambiguous | no | "using Mongoose" | documentdb-driver | Use a recent Mongoose major compatible with Node 24 (e.g., Mongoose 7.x) and its bundled mongodb driver; lock versions in package.json. | Mongoose is required, but the exact package versions are not specified. documentdb-driver provides best-practice patterns but not a required version. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... DOCUMENTDB_URI env var." | - | - | Run environment gives the exact live cluster and database to use. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time. Never write its value into any file... use a config file or .env.example with a placeholder." | - | - | Connection string location and handling are specified in skill_md; LLM credentials are not specified (see AI components). |
| Data model | ambiguous | no | "using Mongoose" and "reads unmatched invoices" and "searches DocumentDB for candidate PO matches" | documentdb-data-modeling | Implement Mongoose schemas for Invoice and PurchaseOrder. Invoice fields: status, invoiceNumber, vendorName, totalAmount, invoiceDate, lineItems[], referencedPoNumber, matchedPoId, matchScore, matchDetails, matchedAt. PO fields: vendorName, poNumber, totalAmount, lineItems[]. | Prompt requires Mongoose but does not enumerate the exact schemas or field names; documentdb-data-modeling can advise on shapes. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide a small synthetic seed dataset (tens of invoices and POs) via an idempotent seed script included in repo. | No source, size, license or explicit seed script is specified in the starter prompt or skill_md (although skill_md asks to create collections and load sample data during verification). |
| Queries and indexes | covered_by_skill | no | "searches DocumentDB for candidate PO matches by amount and vendor" | documentdb-indexing | Create single-field indexes on vendorName and totalAmount and a compound index if necessary. If embeddings are used for fuzzy vendor matching, create an appropriate vector index with dimensions matching the embedding model. | Index specifics (shapes/params) are not in the prompt; documentdb-indexing will guide choices. |
| AI components | missing | no | "extracts structured fields using an LLM tool" and "LangChain agent" | - | Default to an OpenAI-compatible model via LangChain (e.g., OpenAI chat/completion model for extraction and text-embedding-3-small for embeddings). Require OPENAI_API_KEY in env. The exact model and embedding dims must be chosen and documented by the implementer. | Prompt references an LLM extraction tool but does not name provider, models, or embedding dimensions. |
| App surface | ambiguous | no | "Use agent memory to learn from manual corrections within a session." and "reads unmatched invoices... writes the reconciliation result back." | - | Implement a minimal Express HTTP API with endpoints: POST /reconcile/run to trigger reconciliation, POST /reconcile/manual-correction to submit corrections to agent memory, and GET /reconcile/status or similar for inspection. Also provide a CLI entrypoint (npm run reconcile) for one-shot runs. | Prompt implies there will be a callable path for manual corrections but does not define web vs CLI surface or route names. |
| Provisioning and deployment | covered_by_skill | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable." | documentdb-azure-deployment | Do not provision new clusters in the sample run; use the provided cluster. Provide optional IaC via documentdb-azure-deployment skill only if the author requests it. | The environment forbids creating new clusters during the run; a deployment skill exists if needed for repo completeness. |
| Run and test instructions | missing | no | skill_md includes verification steps but no explicit commands. | - | Include standard commands in README: npm install, cp .env.example .env (fill in vars), npm run seed, npm start, npm run test. Tests may be limited if live cluster required. | No explicit run/test commands or expected outputs are specified in the starter prompt. |
| Definition of done | ambiguous | no | "reads unmatched invoices... writes the reconciliation result back... Use agent memory to learn from manual corrections within a session." | - | Define done as: the sample can be started locally (with env vars set), seed script loads data, reconciliation run updates invoices with matchedPoId and matchDetails, manual corrections applied via the API are stored in in-memory session and influence subsequent matches in same session, and a short demo script shows before/after state. | No explicit acceptance criteria present; implementer will supply them in README/test output. |
| Constraints and non-goals | missing | no | - | - | Treat this as a developer-focused sample—no production HA, no CMK, no cross-region replication; avoid provisioning new paid resources during verification. | No cost or compliance constraints are specified. |
| Repository conventions | covered_by_skill | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or .env.example with a placeholder..." | documentdb-local-deployment | Follow common sample conventions: top-level README, src/, tests/, scripts/seed.js, .env.example, package.json with pinned deps, and no secrets in repo. | Some conventions are implied by skill_md and local-deployment guidance; full repo layout not fully specified. |
