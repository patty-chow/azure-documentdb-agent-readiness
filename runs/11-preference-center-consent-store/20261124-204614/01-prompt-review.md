# 1. Prompt review: 11-preference-center-consent-store

**Verdict: sufficient_with_assumptions**

The starter prompt is specific enough to begin implementing a FastAPI + Beanie consent store (endpoints, consentVersion, append-only history, TTL). Several low-level decisions (Python version, exact field names, index parameters, endpoint paths, testing/seed scripts, dependency pinning, README contents) are left to the builder and will be filled by skills guidance or sensible defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 1: Goal and scenario |
| Covered by a skill | 4: Target service and tier, Authentication and secrets, Queries and indexes, Provisioning and deployment |
| Ambiguous: builder will guess | 5: Workflow type, Language and runtime, Driver and version, Data model, App surface |
| Missing: builder will guess | 5: Sample data, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: AI components |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — prompt does not mention, skill.md requires env var but does not mandate .env.example; builder must add one.
- The vector index dimensions match the embedding model's output — sample does not use AI/vector features; this item is at risk unless intentionally omitted.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them — not applicable unless vector search added; at risk.
- One database client is created and reused across requests — prompt doesn't specify, but documentdb-driver skill recommends a singleton client. Builder must implement this.
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt didn't request a seed script; at risk.
- /search returns a clear error for an empty query and when the embedding call fails — sample doesn't include search; at risk if search is expected by gallery standards.
- Search results include the similarity score — not applicable unless search is implemented; at risk.
- Dependencies are pinned in `requirements.txt` — prompt doesn't say to pin; at risk unless the builder adds pinned requirements.
- Unit tests run without a live cluster — prompt doesn't ask for tests; at risk unless the builder adds mocking tests.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt and skill.md say use existing cluster; infra-as-code is not provided and is at risk for gallery completeness.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't mention README details; builder must add this for gallery quality.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — prompt uses 'DocumentDB' but does not require naming guidance; builder must ensure consistent naming in README and code comments.

## Questions for the prompt author

- Which Python runtime should be targeted (3.10, 3.11)? This affects package compatibility and CI.
- Do you want specific package versions pinned in requirements.txt, or should the builder choose the latest compatible releases tested locally?
- What name and exact routes should be used for the endpoints (e.g., POST /consents/record, POST /consents/withdraw, GET /consents/{customerId}) and what should the request/response payloads contain?
- What TTL semantics and default retention period should be applied? (expireAt semantics with expireAfterSeconds=0 on a retention datetime field, or a fixed duration like 365 days?)
- Should the sample include a seed script and unit tests that run without a live cluster (e.g., using mongomock) and a README with run/cleanup instructions?

## Contradictions and missing references

- Prompt asks to use 'the DocumentDB skill'. There is no single installed skill named exactly 'DocumentDB skill' — there are multiple documentdb-* skills installed. Builder will map the request to the relevant installed documentdb-* skills (documentdb-driver, documentdb-indexing, documentdb-data-modeling, and run-environment in skill.md).

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | build a Python FastAPI service using Beanie ODM that stores customer consent records and channel preferences ... expose endpoints to record consent, withdraw consent, and retrieve the current preference state | - | - | Business goal, user-facing scenario, and what the sample demonstrates are stated in the prompt. |
| Workflow type | ambiguous | no | Using the DocumentDB skill | - | Implement as a normal single-agent sample app (no orchestration framework) — a single repository with code that runs locally against an existing DocumentDB cluster. | Prompt references a generic 'DocumentDB skill' but does not state agent/workflow model. Builder will treat this as a single-agent code sample. |
| Language and runtime | ambiguous | no | Python FastAPI service | skill.md (run environment) | Target Python 3.11 (current stable dev runtime) with FastAPI (ASGI) and uvicorn for dev server. | Prompt specifies Python and FastAPI but not the Python version; skill.md indicates a python virtualenv exists but does not declare version. |
| Driver and version | ambiguous | no | using Beanie ODM | documentdb-driver | Use a recent Beanie release compatible with Python 3.11 (e.g., Beanie >=1.0 stable line), Motor (async MongoDB driver) and PyMongo versions matching Beanie's requirements. Pin versions in requirements.txt to the tested releases. | Prompt names Beanie but does not give exact package versions; documentdb-driver skill provides best-practice guidance (singleton client) but not specific package versions. |
| Target service and tier | covered_by_skill | no | Using the DocumentDB skill | skill.md (run environment) | Use the existing, reachable vector-capable Azure DocumentDB cluster described in the shared run environment (compute tier M30, MongoDB 7.0 wire protocol) and use database `sample_customer_360_11`. | The shared run-environment (skill.md) instructs to use the provided cluster and database; do not provision another cluster. |
| Authentication and secrets | covered_by_skill | no | - | skill.md (run environment) | Read the connection string from the DOCUMENTDB_URI environment variable at runtime and do not commit credentials to the repository. Provide a .env.example with placeholder values. | skill.md explicitly requires DOCUMENTDB_URI be used and not committed. |
| Data model | ambiguous | no | stores customer consent records and channel preferences ... Use a consentVersion field and append-only consent history sub-array for audit | documentdb-data-modeling | Create a Beanie Document named Consent (collection `consents`) with fields: customerId (str, indexed), consentVersion (int), channels (dict mapping channel name to bool/metadata), history (list of objects {timestamp: datetime, action: 'grant'\|'withdraw', channels: dict, version: int, actor: str, reason: str?}), retention_expires_at (datetime) for TTL. Use customerId as the logical unique key; no sharding for sample (single-shard). | Prompt defines high-level shape (version + append-only history) but not exact field names or collection name; documentdb-data-modeling gives guidance on embedding and document size but not exact schema. |
| Sample data | missing | no | - | documentdb-local-deployment (guidance only) | Provide a seed script that upserts a small set (3–5) of example customer consent documents. The seed script is idempotent (upsert by customerId) so it can be run multiple times without duplication. | Starter prompt doesn't mention sample data or seeds; local-deployment skill talks about sample-data management but does not provide the specific seed script. |
| Queries and indexes | covered_by_skill | no | Add TTL indexes for data retention enforcement | documentdb-indexing | Create a TTL index on the date field named `retention_expires_at` and set expireAfterSeconds = 0 (expire at the stored date). Also create a single-field index on `customerId` (unique or partial) for fast lookups. Keep index count low. | Prompt requests TTL indexes; documentdb-indexing covers TTL semantics and index guidance but does not fix expireAfterSeconds. Builder will pick a sensible default (expireAt semantics with 0). |
| AI components | not_applicable | no | - | - | - | No embedding or chat models are requested. |
| App surface | ambiguous | no | expose endpoints to record consent, withdraw consent, and retrieve the current preference state | - | Expose HTTP endpoints: POST /consents/record, POST /consents/withdraw (JSON body: {customerId, channels, actor?, reason?}), GET /consents/{customerId} returning current preference state and latest consentVersion. Use FastAPI with pydantic models for request/response validation. | The prompt specifies the operations but not exact route names, request/response shapes, or status codes. |
| Provisioning and deployment | covered_by_skill | no | - | skill.md (run environment) | Do not provision a new cluster; use the existing cluster reachable via DOCUMENTDB_URI. Provide local run instructions (uvicorn) and optionally a Dockerfile for the app only (but not for a local DocumentDB gateway). | skill.md explicitly forbids creating another cluster for the sample run and says verify against the live cluster. |
| Run and test instructions | missing | no | - | - | Add README run steps: pip install -r requirements.txt, copy .env.example to .env and fill DOCUMENTDB_URI, run `python -m app.main` or `uvicorn app.main:app --reload`. Provide a seed script command and a simple smoke test. Provide unit tests that mock the DB (pytest + mongomock or use dependency inversion). | Prompt did not request README or test commands; these must be added by the builder. |
| Definition of done | missing | no | - | - | Acceptance criteria: endpoints implemented and documented, Beanie models persist to `sample_customer_360_11` `consents` collection, history append updates verified, TTL index created and retention field set on writes, seed script works idempotently, README contains setup/run/cleanup. | Prompt lacks an explicit 'done' checklist; use the reference-requirements-derived criteria. |
| Constraints and non-goals | missing | no | - | skill.md (run environment) | Do not provision Azure infra; avoid committing secrets; sample is for demo and not production-grade security (but follow TLS and env var best practices). Keep cost low by using existing cluster. | Prompt does not state constraints such as cost or non-goals; skill.md provides the 'do not provision' constraint. |
| Repository conventions | missing | no | - | - | Follow a standard layout: app/ (FastAPI code), models/ or app/models.py (Beanie documents), scripts/seed.py, tests/, requirements.txt, README.md, .env.example. Pin dependencies in requirements.txt. | Prompt doesn't require a particular repo layout or README structure; builder will apply conventions. |
