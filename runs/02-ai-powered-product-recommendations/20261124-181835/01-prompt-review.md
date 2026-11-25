# 1. Prompt review: 02-ai-powered-product-recommendations

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear, actionable goal (Node.js + LlamaIndex agent, DiskANN, 20k ingest script, UI, config-file handling, and commented code). Several implementation details are left to the builder (driver version, embedding model, index tuning, session-store choice, README/test details), but installed DocumentDB skills and the provided run-environment notes cover much of the missing infrastructure and best-practice guidance. No blocking unknowns — the build can start but will require the builder to pick defaults for a handful of technical choices.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Authentication and secrets, Sample data, App surface |
| Covered by a skill | 2: Language and runtime, Target service and tier |
| Ambiguous: builder will guess | 4: Driver and version, Data model, Queries and indexes, Definition of done |
| Missing: builder will guess | 4: AI components, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 1: Provisioning and deployment |

## Reference requirements at risk

- Use the Azure DocumentDB skill to read co-purchase order history from Azure DocumentDB (the prompt instructs 'Using the Azure DocumentDB skill' but no single installed skill matches that exact name; the builder may not produce an adapter explicitly called that).
- The vector index dimensions match the embedding model's output (embedding model not specified in prompt; builder must choose — risk that chosen model and index dimensions are inconsistent).
- The vector index parameters are chosen for the catalog size, and the README says how to change them for a larger one (index tuning parameters are not provided and README instructions are not requested explicitly).
- A seed script loads sample products and creates the index, and can be run twice without duplicating data (prompt requires a 20k ingest script but does not require idempotency or seeding of product metadata and index creation semantics).
- /search returns a clear error for an empty query and when the embedding call fails (error-handling behavior for search/embedding failures is not specified).
- Search results include the similarity score (prompt requires top 5 items with reasoning but does not require exposing numeric similarity scores).
- Dependencies are pinned in a lock or requirements file (prompt doesn't mention pinning; Node projects may rely on package-lock.json but requirement asked for pinned dependencies explicitly).
- Unit tests run without a live cluster (prompt doesn't mention tests or test strategy to run offline/mocked).
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type (the run environment provides an existing cluster; the prompt doesn't request IaC).
- The README covers what the sample shows, prerequisites, setup, run, and clean-up (prompt asks for the app but didn't explicitly ask for a README with full instructions).

## Questions for the prompt author

- Which embedding model and provider should the sample use (e.g., OpenAI text-embedding-3-small 1536-dim, a local HuggingFace model, or something else)? This determines index dimensionality and config.
- Which LLM/provider should be used for the LlamaIndex 'reasoning' output (and should model creds be expected in env vars like OPENAI_API_KEY)?
- Which MongoDB Node.js driver and minimum version should the sample target (e.g., 'mongodb' npm package ^5.0)?
- How should per-session agent memory be persisted for personalization: in-memory per server process, browser session storage, or a server-side session store (Redis / DB)?
- Do you require an explicit .env.example and README with exact run/test commands, or should the builder create a minimal README and .env.example with placeholders?

## Contradictions and missing references

- The prompt says "Using the Azure DocumentDB skill" but there is no installed skill named exactly "Azure DocumentDB skill". There are many documentdb-* skills available (e.g., documentdb-driver, documentdb-vector-search) and a run-environment skill_md, but the exact skill name referenced in the prompt is not present.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Node.js LlamaIndex agent that reads co-purchase order history from Azure DocumentDB, generates product embeddings, stores them in a DiskANN index, and uses agent memory to personalise recommendations per session." | - | - | The business problem (product recommendations from co-purchase history) and what to demonstrate are explicit. |
| Workflow type | specified | no | "Node.js LlamaIndex agent" | - | - | Single-agent using the LlamaIndex agent framework is explicit. |
| Language and runtime | covered_by_skill | no | - | skill.md (run environment) | Use Node.js 24 (the run-environment notes say Node.js 24 is available). | Prompt states Node.js; run-environment skill_md supplies Node.js 24. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use the official mongodb npm driver (package 'mongodb') pinned to a recent stable major compatible with Node 24 (e.g. ^5.0), and follow the documentdb-driver guidance to instantiate a singleton MongoClient. | Prompt doesn't name which MongoDB Node driver or version to use; the documentdb-driver skill provides best-practice patterns but not a concrete version choice. |
| Target service and tier | covered_by_skill | no | - | skill.md (run environment) | Use the provided live, vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) and the database named 'sample_retail_02'. | Run-environment notes explicitly describe the available cluster and DB to use. |
| Authentication and secrets | specified | no | "Use a config file for the Azure DocumentDB connection string and display a clear error if the connection string is missing or invalid." | skill.md (run environment) | Read connection string from environment variable DOCUMENTDB_URI at runtime; include a .env.example with a placeholder; never write the real secret to repo or logs. | Prompt requires config-file usage and clear error; run-environment adds the DOCUMENTDB_URI convention and .env.example guidance. |
| Data model | ambiguous | no | "reads co-purchase order history from Azure DocumentDB" | documentdb-data-modeling | Create an 'orders' collection in database 'sample_retail_02' with docs like { orderId, userId, products: [productId], timestamp } and a 'products' collection for metadata; use no sharding for the sample. | The prompt says to read co-purchase history but does not define collection names or document schema. The data-modeling skill gives patterns but not exact shapes — the builder will pick a simple 'orders' document shape. |
| Sample data | specified | no | "include a script to ingest 20,000 product purchase transactions" | - | The ingest script will synthesize 20,000 sample order documents (no external dataset), inserting them into the 'orders' collection. The data will be synthetic and licensed as generated by the project. | Prompt requires a 20k ingest script but doesn't require external dataset or licensing details; builders typically generate synthetic data. |
| Queries and indexes | ambiguous | no | "stores them in a DiskANN index" | documentdb-vector-search, documentdb-indexing | Create a DiskANN vector index with dimensionality matching the chosen embedding model (e.g., 1536), using sensible defaults for DiskANN build/search params (leave lBuild/lSearch default or documented values recommended by documentdb-vector-search). Also create simple single-field indexes for lookup queries (e.g., productId). | DiskANN is required, but concrete index parameters (dimension, L* tuning) are not provided; vector-search and indexing skills provide guidance the builder will follow. |
| AI components | missing | no | "generates product embeddings" and "LlamaIndex agent" | - | Use a hosted embedding provider such as OpenAI (text-embedding-3-small, 1536 dims) with credentials from OPENAI_API_KEY; use LlamaIndex Node bindings to call embeddings and an LLM (e.g., OpenAI gpt-4o-family or gpt-4o-mini) for reasoning. Document the chosen models in README. | Prompt names LlamaIndex and asks for embeddings but does not pick an embedding model or specify where model credentials come from; no installed skill covers LLM/embedding provider selection. |
| App surface | specified | no | "The agent should accept a product ID and return the top 5 recommended items with reasoning." "artistic UI to look like an online retailer's website." | - | Provide a simple web UI (React or plain HTML/JS served by Express) with an input for product ID and a results panel showing five recommendations plus textual reasoning; also expose a /recommend API endpoint accepting productId and returning JSON. | Prompt requires both an artistic retailer-style UI and an input/return contract; UI framework is left to the implementer. |
| Provisioning and deployment | not_applicable | no | "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned" (skill_md). | skill.md (run environment) | - | Prompt/run-environment explicitly uses an existing cluster; provisioning new infrastructure is not required for the sample. |
| Run and test instructions | missing | no | - | - | Builder will add README commands: npm install, npm run seed (to ingest 20k), npm start, and instructions to set DOCUMENTDB_URI and OPENAI_API_KEY; basic manual verification steps will be included but no exhaustive automated tests. | Starter prompt asks for the app but does not specify exact run/test commands or test coverage expectations. |
| Definition of done | ambiguous | no | "accept a product ID and return the top 5 recommended items with reasoning"; "ingest 20,000 product purchase transactions"; "artistic UI"; "config file"; "detailed comments before each method" | - | Treat the prompt's bullet items as acceptance criteria: app runs locally, seed inserts 20k, vector index built and persisted, /recommend returns five items with reasoning, and the UI demonstrates recommended items. | The prompt lists deliverables that can serve as done criteria but does not define pass/fail conditions or verification details. |
| Constraints and non-goals | missing | no | - | - | No cloud provisioning will be done; keep cost low (no high-throughput tiers), data will be synthetic, and the sample is educational (not production-ready security/hardening). | No cost, licensing, or compliance constraints are specified. |
| Repository conventions | missing | no | "Use a config file for the Azure DocumentDB connection string" | skill.md (run environment) | Use a standard Node repo layout (package.json, src/, public/, README.md), include .env.example, package-lock.json or pinned versions in package.json, and add npm scripts for seed/start/test. Follow minimal telemetry/attribution (none required). | Prompt asks for a config file; broader repo conventions are not specified. |
