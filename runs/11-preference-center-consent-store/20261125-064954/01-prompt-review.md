# 1. Prompt review: 11-preference-center-consent-store

**Verdict: sufficient_with_assumptions**

The starter prompt gives a clear goal (Python FastAPI + Beanie consent store with append-only history, TTL index, and three endpoints) and the run-environment constraints supply the target cluster and DB name. Several implementation details are unspecified (Python version, driver versions, exact routes/payloads, seed script, pinned deps, README, tests, index parameters), so a builder can start but will make concrete defaults for those gaps.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 10: Workflow type, Language and runtime, Driver and version, Data model, Queries and indexes, App surface, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Missing: builder will guess | 1: Sample data |
| Not applicable | 1: AI components |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — skill.md instructs using .env.example, so this is likely to be added, but the starter prompt itself did not require it. (skill.md partially covers this)
- The vector index dimensions match the embedding model's output — no embedding model is requested in the prompt, and skill.md does not provide model info; this is at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — not applicable to the prompt's scope and not covered.
- One database client is created and reused across requests — not specified in prompt or skill.md; implementer may or may not follow this best practice.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — seed script is not requested and skill.md doesn't supply sample data; at risk.
- /search returns a clear error for an empty query and when the embedding call fails — search is not part of this prompt; at risk if the gallery expects search behavior.
- Search results include the similarity score — not relevant to this sample as specified; at risk per reference requirements.
- Dependencies are pinned in `requirements.txt` — not specified; implementer may include or omit pinned versions, so this is at risk.
- Unit tests run without a live cluster — no test strategy is specified; at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — skill.md forbids provisioning new cluster; infra code is not requested and is at risk.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't request README; skill.md asks verification but not README content, so this is at risk.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — no naming guidance in the prompt; at risk.

## Questions for the prompt author

- Which Python minor version should the sample target (e.g. 3.10 or 3.11)? This affects dependency compatibility and CI/test setup.
- Do you have preferred route names and exact request/response schemas (e.g. POST /consents vs POST /consent, what fields are required) or should the implementer choose pragmatic defaults?
- Should the sample include an idempotent seed script, pinned requirements.txt, unit tests (mocking the DB), and a README, or is delivering only the running service sufficient?

## Contradictions and missing references

- Prompt asks to use 'the DocumentDB skill' but the installed_skills list is empty; no skill named 'DocumentDB' is available to the builder.
- skill.md mandates using a .env.example and not writing the connection string to files; the prompt does not mention configuration details itself but references a skill that is missing.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python FastAPI service using Beanie ODM that stores customer consent records and channel preferences... append-only consent history sub-array for audit... expose endpoints to record consent, withdraw consent, and retrieve the current preference state." | - | - | Prompt clearly states the business goal and what the sample demonstrates. |
| Workflow type | ambiguous | no | "Using the DocumentDB skill" | - | Builder will implement a normal code sample (no agent orchestration) — a standalone FastAPI service that talks to DocumentDB directly. | Prompt references a 'DocumentDB skill' but does not state an agent framework; no agent skills are installed. See contradictions. |
| Language and runtime | ambiguous | no | "Python FastAPI service" | - | Target a modern supported Python 3.x, e.g. Python 3.11 (builder will use 3.11 or 3.10 as default). | Python language is specified but the exact version is not. |
| Driver and version | ambiguous | no | "using Beanie ODM" | - | Use the current stable Beanie from PyPI and its compatible motor/pymongo versions (install latest Beanie; let pip resolve compatible motor/pymongo). | ODM is specified but specific library versions or pinned deps are not. |
| Target service and tier | specified | no | - | - | - | skill.md provides the cluster details and enforces using the existing cluster and database name 'sample_customer_360_11' (M30, MongoDB 7.0 wire protocol, DiskANN, etc.). |
| Authentication and secrets | specified | no | - | - | - | skill.md requires reading connection string from DOCUMENTDB_URI environment variable and not writing secrets to files; use .env.example placeholders. |
| Data model | ambiguous | no | "Customer consent records and channel preferences are modelled as Beanie ODM Document classes"; "consentVersion field and append-only consent history sub-array" | - | Builder will define a Beanie Document with fields: customer_id (string, indexed), consentVersion (int), current_preferences (dict of channel->bool), history (list of events with timestamp, action, actor, channels), and retention_date (datetime) used for TTL. | Shape is sketched but field names, types and collection name(s) are left to the implementer; no shard key or relationships specified. |
| Sample data | missing | no | - | - | Builder will create a small idempotent seed script inserting a few (3–5) representative consent documents for demonstration/testing. | Prompt does not mention seed data source, size, or license; skill.md only requires verification against live cluster but does not supply sample data. |
| Queries and indexes | ambiguous | no | "Add TTL indexes for data retention enforcement" | - | Builder will create a TTL index on the retention_date field with a sensible default expireAfterSeconds (e.g. 365 days expressed in seconds, configurable via env), and add an index on customer_id for fast lookup. No vector or text indexes are required for this sample. | Only TTL index requirement is explicit; index parameters and any additional indexes are unspecified. |
| AI components | not_applicable | no | - | - | - | No embedding/chat components requested. |
| App surface | ambiguous | no | "expose endpoints to record consent, withdraw consent, and retrieve the current preference state" | - | Builder will implement routes such as POST /consent (record), POST /consent/withdraw (withdraw), and GET /consent/{customer_id} (retrieve), with JSON request/response payloads documenting expected fields. | HTTP methods and high-level intent are stated but exact route names, request/response schemas and error handling are left to the implementer. |
| Provisioning and deployment | specified | no | - | - | - | skill.md explicitly requires using the existing live cluster and disallows provisioning another cluster; Docker is available but a local gateway is not to be used. |
| Run and test instructions | ambiguous | no | - | - | Builder will include basic run instructions (create .env from .env.example, pip install -r requirements.txt, uvicorn main:app --reload) and a small integration test that runs against the live cluster if available. Unit tests that run without a live cluster are not specified but likely omitted unless added by the implementer. | skill.md asks to verify against live cluster but exact commands, test harness and CI are unspecified. |
| Definition of done | ambiguous | no | "...stores customer consent records...append-only consent history...TTL indexes...endpoints to record consent, withdraw consent, and retrieve the current preference state." | - | Accept when: FastAPI service runs, Beanie models exist, endpoints perform described operations against sample_customer_360_11, TTL index created in code, and a small demo/seed shows the features. | No explicit acceptance criteria (tests, performance, coverage) provided; implementer will create pragmatic criteria. |
| Constraints and non-goals | ambiguous | no | - | - | Builder will avoid provisioning new cloud resources, will not commit secrets, and will focus on correctness/demo rather than production hardening or infra-as-code. | skill.md gives some constraints (use existing cluster, do not write secrets), but no cost or compliance constraints are listed. |
| Repository conventions | ambiguous | no | - | - | Use a simple layout (app/, tests/, scripts/seed.py), add requirements.txt, .env.example, README.md describing setup/run, and keep secrets out of the repo per skill.md. | Prompt/skill.md require not committing connection strings and suggest .env.example, but other repo conventions (README sections, naming) are not specified. |
