# 1. Prompt review: 07-lab-results-aggregator

**Verdict: sufficient_with_assumptions**

The starter prompt clearly defines the core goal (an async Python Beanie service that stores time-series lab results, runs aggregation pipelines to compute moving averages and flag out-of-range values, and opens a change stream to emit alerts). Several operational details (Python version, driver version, API surface, seed data, index choices, README and test scaffolding, and provisioning-as-code) are not specified and will be chosen by the builder or filled by installed skills (documentdb-driver, documentdb-indexing, documentdb-local-deployment, documentdb-connection).

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Workflow type, Target service and tier, Authentication and secrets, Data model |
| Covered by a skill | 1: Driver and version |
| Ambiguous: builder will guess | 4: Language and runtime, Queries and indexes, App surface, Repository conventions |
| Missing: builder will guess | 5: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values (skill_md mentions DOCUMENTDB_URI but the prompt doesn't require a .env.example).
- The vector index dimensions match the embedding model's output (the prompt doesn't use embeddings and no guidance is provided by a skill for this sample).
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one (not applicable per prompt; at risk because gallery expects this).
- A seed script loads sample data and creates the index, and can be run twice without duplicating data (prompt doesn't request a seed script; documentdb-local-deployment gives patterns but no script).
- /search returns a clear error for an empty query and when the embedding call fails (search API not requested by the prompt).
- Search results include the similarity score (no search component requested).
- Dependencies are pinned in requirements.txt (prompt doesn't mention dependency pinning).
- Unit tests run without a live cluster (prompt requires verifying against a live cluster; no guidance to include offline unit tests or mocks).
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type (prompt uses an existing cluster and does not request infra-as-code).
- The README covers what the sample shows, prerequisites, setup, run, and clean-up (prompt doesn't require a README but gallery samples typically need one).
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name (not enforced by prompt; author must ensure naming in docs).

## Questions for the prompt author

- Which Python minor version should the sample target (3.10, 3.11, ...)? this affects dependency pins and test config.
- What alert delivery mechanism do you want for critical values? (console log only, webhook, email/SMS via provider, or a sample WebSocket/HTTP push endpoint).
- Where should reference ranges and critical thresholds come from? (hard-coded mapping in code, a separate collection in the DB, or an external service/file).
- Should the sample include an idempotent seed script that can be run multiple times to populate demo data, or is hand-seeding/demo data acceptable?
- Do you want a small HTTP API (e.g., FastAPI) to demonstrate inserts and queries, or should the sample be only a background worker/CLI that consumes change streams?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build an async Python service using Beanie ODM that stores lab results as time-series documents... Build aggregation pipelines that compute moving averages and flag results outside reference ranges. Open a change stream to trigger real-time alerts when critical values are written." | - | - | The business problem and demo scenario are stated explicitly. |
| Workflow type | specified | no | "build an async Python service" | - | Interpret as a single long-running async service (no agent orchestration). | Prompt implies a standard single-service application rather than multi-agent orchestration. |
| Language and runtime | ambiguous | no | "async Python" | - | Builder will target a recent stable Python 3.x runtime (assume Python 3.11 unless environment indicates 3.10). The sample's virtual environment described in skill_md implies the repo can rely on local 'python' and 'pip'. | Exact Python minor version not provided; tests, packaging and runtime constraints depend on the chosen version. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use Beanie (ODM) backed by PyMongo async driver. Follow documentdb-driver guidance: create a process-wide singleton AsyncMongoClient (PyMongo's AsyncMongoClient as recommended). Driver minor versions will be chosen to match Beanie compatibility (e.g., PyMongo 4.9+/Beanie version that supports it). | documentdb-driver provides the singleton client pattern and best-practice guidance; exact version pins must still be decided by the builder. |
| Target service and tier | specified | no | - | skill.md run environment | Use the existing vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) reachable via DOCUMENTDB_URI and the database named 'sample_healthcare_07' as stated in the run environment. | The skill_md run environment explicitly states the cluster and database to use; the sample must not provision another cluster. |
| Authentication and secrets | specified | no | - | skill.md run environment | Read connection string from DOCUMENTDB_URI environment variable; do not commit secrets. Use SCRAM-SHA-256/TLS as required by Azure DocumentDB per connection guidance in the skills. | skill_md instructs environment variable usage and prohibits writing secrets to files or logs. |
| Data model | specified | no | "stores lab results as time-series documents in DocumentDB with patientId, testCode, value, and timestamp fields." | - | Each lab result is a separate Beanie Document with fields: patientId (string/UUID), testCode (string), value (numeric), timestamp (ISO datetime). No shard key specified — builder will use a single collection 'lab_results' in database 'sample_healthcare_07'. | Prompt defines the document shape clearly; partitioning/sharding is not requested. |
| Sample data | missing | no | - | documentdb-local-deployment (partial guidance) | Builder will add a small seed script (e.g., a Python script or FastAPI startup task) with a handful (~100) of synthetic patient test records for demo. If not specified, the builder may rely on ad hoc generated data in code. | The starter prompt does not ask for a seed script or sample-data provenance; documentdb-local-deployment skill gives best-practice patterns but does not provide the required seed script or idempotency guarantees. |
| Queries and indexes | ambiguous | no | "Build aggregation pipelines that compute moving averages..." and "flag results outside reference ranges." | documentdb-indexing | Builder will implement aggregation pipelines using $setWindowFields partitioned by patientId and testCode and likely create a compound index on {patientId:1, testCode:1, timestamp:1} to support ordered window aggregation. No vector or full-text indexes are required by the prompt. | Prompt specifies the aggregation patterns but does not state the indexes to create; documentdb-indexing skill guides index shape selection and will be used to pick the compound index recommended above. |
| AI components | not_applicable | no | - | - | No embedding, chat, or other AI components are required for this lab-results aggregator sample. | Reference file mentions vector indexes in general, but the prompt does not request any AI/model usage. |
| App surface | ambiguous | no | "build an async Python service" and "Open a change stream to trigger real-time alerts" | - | Builder will expose a small async HTTP API (likely FastAPI) with endpoints to insert lab results (POST /results), query aggregates (GET /patients/{id}/tests/{code}/moving-average), and run a background change-stream consumer that emits alerts (via console logs and optionally a webhook endpoint). The change-stream consumer will run as an asyncio background task in the same process. | Prompt does not pick a framework or endpoints explicitly; FastAPI + async background tasks is the common choice for an async Python service. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment (if author asked to provision) | No provisioning will be performed: the sample uses the existing cluster given in the run environment. The repo will not include Bicep/Terraform by default unless requested. | The starter prompt explicitly says to 'use the DocumentDB skill' but the run environment already provides a cluster; it does not request infra-as-code. If infra-as-code is required by gallery conventions, it is not specified here. |
| Run and test instructions | missing | no | - | documentdb-local-deployment (partial guidance) | Builder will add basic run instructions in README: create virtualenv, pip install -r requirements.txt, set DOCUMENTDB_URI in env or .env, run seed script, then start the service. No standardized test scripts or CI configuration are specified. | Prompt does not include the explicit commands nor test expectations; skill_md suggests verification against live cluster but not the exact commands to include in README. |
| Definition of done | missing | no | - | - | Builder will treat the sample as done when: service runs, documents can be inserted, moving-average aggregation returns expected output, out-of-range flags are present in pipeline results, and change-stream handler emits alerts on critical writes. | No explicit acceptance criteria are defined; the builder will create practical checks described in the README or tests. |
| Constraints and non-goals | missing | no | - | - | Assume demo-scale only (small sample dataset), no production HA/DR, no customer-managed keys, and TLS required as per Azure constraints in skills. | Cost limits, compliance, and non-goals are not called out and will need to be documented if required by the gallery. |
| Repository conventions | ambiguous | no | - | documentdb-local-deployment (partial guidance) and skill.md run environment | Builder will follow common sample layout: src/, tests/, scripts/seed_data.py, requirements.txt, .env.example, README.md. The run environment requires the DB name 'sample_healthcare_07' be used. | Some conventions are implied by skill_md (database name, env var usage) but full repo conventions (pinned deps, README sections, telemetry) are not specified. |
