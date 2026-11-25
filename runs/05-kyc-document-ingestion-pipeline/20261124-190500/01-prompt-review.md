# 1. Prompt review: 05-kyc-document-ingestion-pipeline

**Verdict: sufficient_with_assumptions**

The starter prompt clearly states the core app behavior: an async Python pipeline using Beanie, calling OpenAI for structured extraction, Pydantic validation, and upsert into Azure DocumentDB with incomplete records flagged. Several implementation details (Python and driver versions, HTTP framework, OpenAI model, secrets handling, collection/index shapes, seed data, test strategy, README) are left unspecified and will be chosen by the builder or guided by installed skills. No blocking unknowns; the build can start with reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 3: Goal and scenario, Target service and tier, Data model |
| Covered by a skill | 2: Authentication and secrets, Provisioning and deployment |
| Ambiguous: builder will guess | 6: Workflow type, Language and runtime, Driver and version, AI components, App surface, Definition of done |
| Missing: builder will guess | 5: Sample data, Queries and indexes, Run and test instructions, Constraints and non-goals, Repository conventions |
| Not applicable | 0: - |

## Reference requirements at risk

- The connection string and model credentials come from environment variables; none appear in the repository. (Prompt omitted exact env var names; skill_md mentions DOCUMENTDB_URI but other env names are unspecified.)
- A .env.example lists every setting with placeholder values. (Prompt didn't request this explicitly.)
- The vector index dimensions match the embedding model's output. (Prompt doesn't define embeddings or a vector search feature; vector-index specifics are missing.)
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. (Not requested in prompt.)
- One database client is created and reused across requests. (Prompt implies async pipeline but does not specify singleton/client-reuse; skills recommend it but code may omit.)
- A seed script loads sample data and creates the index, and can be run twice without duplicating data. (Prompt did not ask for a seed script.)
- /search returns a clear error for an empty query and when the embedding call fails. (Search endpoint not requested by prompt.)
- Search results include the similarity score. (Search not requested.)
- Dependencies are pinned in requirements.txt. (Prompt doesn't state dependency pinning.)
- Unit tests run without a live cluster. (Prompt does not require tests or mocking.)
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. (Prompt uses an existing cluster per skill_md; infra-as-code is optional and not requested.)
- The README covers what the sample shows, prerequisites, setup, run, and clean-up. (Prompt didn't request README details explicitly, though a sample should include them.)
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. (Prompt says DocumentDB but does not mandate naming conventions in docs; implementer may accidentally use other names.)

## Questions for the prompt author

- Do you want an HTTP API (e.g., FastAPI) with an /upload endpoint, or a CLI/library function as the upload handler?
- Which Python runtime version should be targeted (3.10, 3.11)?
- Which async Mongo driver should we use with Beanie (Motor/AsyncIOMotorClient) or follow documentdb-connection's recommendation to use PyMongo's AsyncMongoClient and a compatible ODM?
- Which OpenAI model should be used for entity extraction, and are calls to the live OpenAI API allowed in CI/build runs?
- Where should secrets live (env vars, Azure Key Vault)? Confirm env var names (DOCUMENTDB_URI, OPENAI_API_KEY, etc.).
- Should the sample include seed data, unit tests that run without a live cluster (mocks), and infra-as-code for the cluster, or stick to code-only and use the provided live cluster?

## Contradictions and missing references

- Prompt says 'Using the DocumentDB skill' but there is no single installed skill named exactly 'DocumentDB'. Multiple specialized DocumentDB skills are installed (connection, deployment, indexing, etc.) — the builder will need to pick the relevant ones.
- Prompt requests Beanie ODM (which commonly uses Motor) but documentdb-connection skill strongly recommends PyMongo's AsyncMongoClient over Motor for new async Python code. The builder must reconcile Beanie examples (Motor) with documentdb-connection's recommendation; this is a real tension that affects client code and dependencies.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build an async Python pipeline using Beanie ODM that accepts uploaded KYC documents, sends them to OpenAI for structured entity extraction (name, DOB, address, ID numbers), validates the output against a Pydantic schema, and upserts the customer record into DocumentDB. Flag incomplete records for manual review. | - | - | Business problem, actors, and what the sample demonstrates are explicit. |
| Workflow type | ambiguous | no | Using the DocumentDB skill, build an async Python pipeline ... | - | Builder will assume a no-agent application sample (normal async web/service pipeline) implemented as a single-agent/no-agent code sample (no agent framework). | Prompt references a 'DocumentDB skill' but does not request an agent orchestration framework; most builders will produce a plain app. |
| Language and runtime | ambiguous | no | async Python pipeline using Beanie ODM | - | Use modern Python 3.11 (or 3.10) runtime for async features; project will include a requirements.txt and instructions for creating a venv with pip. | Python is specified, but the exact interpreter version is not. |
| Driver and version | ambiguous | no | using Beanie ODM | documentdb-connection, documentdb-driver | Builder will use Beanie (latest stable) with an async Mongo driver compatible with Beanie. Common choice: Motor/AsyncIOMotorClient paired with Beanie; however documentdb-connection recommends PyMongo's AsyncMongoClient for new async Python code. If not resolved, the builder will pick Beanie + Motor (most Beanie examples) and comment on the alternative. | Driver choice/version should be clarified because documentdb-connection recommends AsyncMongoClient rather than Motor; this is a practical tension the builder must reconcile and should be documented in the sample. |
| Target service and tier | specified | no | - | documentdb-local-deployment | Skill.md (run environment) states that a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN/HNSW/IVF) is reachable and DOCUMENTDB_URI is provided in env. Builder will use database sample_fintech_05. | This comes from provided skill_md run environment rather than the short prompt text. |
| Authentication and secrets | covered_by_skill | no | - | documentdb-security | Secrets (connection string, OpenAI key) will be read from environment variables; README/.env.example will document env names. | documentdb-security + azure-deployment skills provide guidance for secure handling and TLS, and documentdb-azure-deployment explains not to commit passwords. Starter prompt does not name env vars explicitly, but skills cover best practice. |
| Data model | specified | no | request the exact fields name, date of birth, address, and ID numbers ... Map and validate the OpenAI-extracted fields against the Pydantic schema; if validation succeeds, transform the validated model into a Beanie document for persistence. | documentdb-data-modeling | Builder will create a 'Customer' Beanie model in a 'customers' collection with fields: name: str, dob: date or ISO string, address: dict (or submodel), id_numbers: list[str]; use government ID (first/primary) or provided customer_id as unique key for upsert. | High-level document shape is specified, but details like collection name, schemaVersion, shard key, and document size handling are left to the implementer and can be guided by data-modeling skill. |
| Sample data | missing | no | - | - | Builder will include a small seed script with a handful (3–10) of example KYC documents (fake/test data) and a script to load them. The seed will be idempotent (upsert by unique key). | Prompt does not ask for sample data or a seed script; reference requirements expect a seed script, so this is at risk. |
| Queries and indexes | missing | no | upserts the customer record into DocumentDB | documentdb-indexing, documentdb-vector-search | Builder will at minimum create a unique index on the stable key (government_id or customer_id). No vector or full-text index required unless the sample adds search; if embedding/search is added later, use vector index with dimensions matched to chosen embedding model and DiskANN for M30. | Prompt doesn't require search; indexing specifics (compound, TTL, vector) are not given and would be decided by the implementer. |
| AI components | ambiguous | no | sends them to OpenAI for structured entity extraction (name, DOB, address, ID numbers) | - | Builder will call OpenAI asynchronously via official OpenAI Python async client (or aiohttp) and will pick a text model appropriate for extraction (e.g., gpt-4o-mini or gpt-4.1 if available). OPENAI_API_KEY will be read from env var. The sample will include a prompt template requesting JSON with exact fields and a small parser that validates JSON and falls back to error handling. | The prompt names OpenAI but leaves model, call method, schema for response, and async client choice to the builder. |
| App surface | ambiguous | no | accepts uploaded KYC documents | - | Builder will implement a minimal async HTTP API (FastAPI + Uvicorn) with a POST /upload endpoint accepting file bytes and returning JSON status for each processed document (upserted / updated / flagged_for_manual_review). | Prompt asks for a pipeline that accepts uploads but does not mandate HTTP vs CLI; FastAPI is a common default for async Python samples. |
| Provisioning and deployment | covered_by_skill | no | - | documentdb-azure-deployment | Skill.md run environment says a cluster already exists. If the sample chooses to include infra code, documentdb-azure-deployment provides templates (Bicep, CLI, Terraform). | The starter prompt does not request creating a cluster; the deployment skill exists if the builder wants to include infra-as-code. |
| Run and test instructions | missing | no | - | - | Builder will add README with commands: pip install -r requirements.txt, copy .env.example to .env with DOCUMENTDB_URI and OPENAI_API_KEY placeholders, run uvicorn to start the API, and a seed/load script. Tests will be minimal and may require a live cluster unless mocks are included. | The prompt doesn't specify which commands or tests to include; these are normally added by the builder. |
| Definition of done | ambiguous | no | Flag incomplete records for manual review. Return or log a clear status for each processed document indicating whether it was upserted, updated, or flagged for manual review. | - | Builder will treat successful upsert/update or flagged_for_manual_review log entries as acceptance criteria, and include example run output in README demonstrating each outcome. | High-level acceptance exists (status per document), but precise tests and coverage are not defined. |
| Constraints and non-goals | missing | no | - | - | Builder will assume no production-grade security beyond reading secrets from env, that the sample should not provision new cloud resources, and costs should be kept low (small sample data). | Prompt doesn't state cost or compliance constraints. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Builder will follow common conventions: src/ or app/ layout, README.md with sections (overview, prerequisites, setup, run, cleanup), .env.example, requirements.txt, and a scripts/ folder for seed/teardown. | No explicit repo layout instructions are in the prompt; skills provide patterns but not a strict convention requirement. |
