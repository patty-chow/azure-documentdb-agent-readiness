# 1. Prompt review: 15-supplier-po-management

**Verdict: sufficient_with_assumptions**

The prompt clearly states the core deliverable: a Python FastAPI service using Beanie with Pydantic validation, full CRUD for suppliers and purchase orders, and an aggregation endpoint. The installed DocumentDB skills cover connection, driver, modeling and indexing guidance so a builder can start coding. Several important implementation details (Python/driver versions, exact schema fields, routing conventions, seed data, tests, README, and whether to provide IaC) are not specified and will be decided by the builder's defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 5: Goal and scenario, Language and runtime, Target service and tier, Authentication and secrets, App surface |
| Covered by a skill | 0: - |
| Ambiguous: builder will guess | 4: Workflow type, Driver and version, Data model, Queries and indexes |
| Missing: builder will guess | 6: Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: AI components |

## Reference requirements at risk

- A `.env.example` lists every setting with placeholder values — not requested by the starter prompt and not enforced by the skills; likely omitted unless builder adds it.
- The vector index dimensions match the embedding model's output — vector/search features are not in the prompt; at risk.
- The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one — at risk (no search/vector requested).
- A seed script loads sample data and creates the index, and can be run twice without duplicating data — the starter prompt doesn't request a seed script; at risk.
- /search returns a clear error for an empty query and when the embedding call fails — no /search endpoint requested; at risk.
- Search results include the similarity score — search not requested; at risk.
- Dependencies are pinned in `requirements.txt` — prompt doesn't require pinned deps; at risk unless builder includes them.
- Unit tests run without a live cluster — tests not requested; at risk.
- Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type — prompt does not require provisioning code; at risk unless builder chooses to add IaC.
- The README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't ask for README; likely omitted unless builder provides it.
- The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name — not enforced by the prompt; builder might use inconsistent naming (risk).

## Questions for the prompt author

- Which Python minor version and runtime should the sample target (e.g., 3.10, 3.11)? This affects dependency selection and CI/testing.
- Which exact fields and types do you require on Supplier and PurchaseOrder (field names, types, which are required)? E.g., Supplier: name (str), contact_email (str); PurchaseOrder: supplier_id (ObjectId), total_value (decimal/float), status (enum).
- Do you prefer PUT (replace) or PATCH (partial update) for update endpoints, or should the sample implement both?
- Should the repository include an idempotent seed script and requirements.txt with pinned versions, plus a README and tests, or only the API code?
- Should the sample create any database indexes (and if so, which ones) as part of startup/seed, or leave index creation to the operator? If create them, should the aggregation index include compound keys (status + supplier_id)?
- Do you want the sample to include unit tests that run without a live cluster (e.g., using motor/Beanie mocks or a test double), or are live-integration tests against the provided cluster acceptable?

## Contradictions and missing references

- Prompt says "Using the DocumentDB skill" — there is no single installed skill named exactly "DocumentDB skill". Multiple documentdb-* skills are installed; the builder will need to pick which skill(s) to consult. (Not fatal, but ambiguous.)

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python FastAPI service using Beanie ODM that models suppliers and purchase orders ... and add an aggregation endpoint that summarises open PO value by supplier." | - | - | Business problem, user and demonstration objective are clear. |
| Workflow type | ambiguous | no | - | - | Builder will treat this as a single-agent coding task (no multi-agent orchestration) and use the installed documentdb-* skills as references. | The prompt does not specify agent framework or workflow; assume single coding agent. |
| Language and runtime | specified | no | "Python FastAPI" | documentdb-local-deployment (run-environment guidance in skill_md) | Use a modern Python 3.x (assume 3.11) virtualenv as implied by skill_md that says `python` and `pip` resolve to a virtual environment. | FastAPI + Python requested explicitly; skill_md gives runtime constraints (dev machine with python/pip). Exact Python minor version not specified. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use async stack: Motor + Beanie (Beanie requires Motor). Use recent stable Motor/pymongo versions compatible with the chosen Beanie release (builder will pick current Beanie release and matching motor/pymongo). | Prompt asks for Beanie (implies Motor). The installed documentdb-driver skill gives usage patterns (singleton client) but does not pin exact versions. |
| Target service and tier | specified | no | - | - | Use the live Azure DocumentDB cluster described in skill_md (vector-capable M30, MongoDB 7.0 protocol), and use database `sample_retail_15` as requested by skill_md. | The run environment (skill_md) supplies the cluster and db name — builder must use that cluster. |
| Authentication and secrets | specified | no | - | - | Read connection string from DOCUMENTDB_URI environment variable at runtime; do not write secrets to repo or logs; provide a `.env.example` with placeholders (skill_md instructs to read env at run time). | skill_md explicitly instructs where the connection string lives and how to treat it. |
| Data model | ambiguous | no | "models suppliers and purchase orders as DocumentDB documents with Pydantic schema validation" | documentdb-data-modeling | Builder will create a Supplier Document with required fields: name (str), contact (str or object with email/phone), created_at; PurchaseOrder Document with required supplier_id (ObjectId/str reference), total_value (float / Decimal), status (str, e.g., 'open'/'closed'), created_at. Relationship implemented using supplier_id (referential check on create). | Prompt requires Pydantic validation and a supplier reference but does not enumerate field names/types or whether to embed items — documentdb-data-modeling can be used for guidance. |
| Sample data | missing | no | - | documentdb-local-deployment (mentions sample-data practices) | Builder will add a small idempotent seed script (e.g., few suppliers and POs) but the prompt does not require it; absent explicit instruction, the builder may or may not include seed data. | The reference requirements expect a seed script; the starter prompt didn't ask for one. |
| Queries and indexes | ambiguous | no | "add an aggregation endpoint that summarises open PO value by supplier" | documentdb-indexing, documentdb-query-optimizer, documentdb-natural-language-querying (aggregation help) | Builder will create relevant indexes for aggregation (e.g., index on status and supplier_id) to support the open-PO aggregation, but exact index types and parameters are not specified. The builder may rely on the indexing skill to choose sensible indexes. | Prompt requires aggregation pipeline but does not specify indexes; installed indexing skills provide guidance. |
| AI components | not_applicable | no | - | - | No embedding or chat model is required for this sample. | Although the cluster is vector-capable, the prompt does not request any AI/vector features. |
| App surface | specified | no | "Python FastAPI service using Beanie ODM ... Implement full CRUD endpoints ... and add an aggregation endpoint" | - | Builder will expose REST endpoints for suppliers and purchase-orders and an aggregation GET endpoint. Route naming and whether to use PUT vs PATCH is left to the implementer (common REST paths like /suppliers and /purchase-orders will be used). | Prompt explicitly asks for full CRUD and an aggregation endpoint; exact routes/HTTP semantics are not fully enumerated but are implied. |
| Provisioning and deployment | missing | no | - | documentdb-azure-deployment (available if infra is requested) | Do not create new cloud resources; use the existing cluster described in skill_md. The prompt does not request IaC or deployment artifacts. | Reference requirements ask for IaC, but the starter prompt does not — the builder will likely not create provisioning code unless asked. |
| Run and test instructions | missing | no | - | - | Builder will include minimal run instructions (pip install -r requirements.txt, uvicorn main:app --reload) but the prompt does not require a README or test commands. | Reference requires README and test instructions; not specified in prompt. |
| Definition of done | missing | no | - | - | Builder will treat implemented endpoints, Pydantic validation, and an aggregation endpoint that runs against the specified DB as acceptance criteria. | Prompt doesn't state explicit acceptance criteria or tests. |
| Constraints and non-goals | missing | no | - | documentdb-security (for guidance if security constraints arise) | No explicit cost or compliance constraints; builder will avoid provisioning resources and will not include production DR/HA topology by default. | No cost limits, telemetry rules, or non-goals are supplied. |
| Repository conventions | missing | no | - | documentdb-local-deployment (offers env conventions) and documentdb-driver (singleton client guidance) | Builder will follow common Python sample layout (app/ or src/, main.py, requirements.txt, .env.example, README.md), but specifics (tests/, layout) are not enforced. | Prompt doesn't specify folder layout, naming, or README conventions. |
