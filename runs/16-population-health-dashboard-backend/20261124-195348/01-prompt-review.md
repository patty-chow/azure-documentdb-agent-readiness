# 1. Prompt review: 16-population-health-dashboard-backend

**Verdict: sufficient_with_assumptions**

The starter prompt plus the provided run-environment (skill_md) and installed DocumentDB skills are enough to start building a FastAPI backend that exposes $facet-based aggregations and materialises cached summaries. Several important implementation details are left to the builder (Python version, driver version, collection schema, seed data, exact routes, indexes, tests, README, and vector/search-related choices), so the build will proceed but rely on reasonable defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 4: Goal and scenario, Target service and tier, Authentication and secrets, Provisioning and deployment |
| Covered by a skill | 2: Driver and version, Repository conventions |
| Ambiguous: builder will guess | 3: Language and runtime, Queries and indexes, App surface |
| Missing: builder will guess | 7: Workflow type, Data model, Sample data, AI components, Run and test instructions, Definition of done, Constraints and non-goals |
| Not applicable | 0: - |

## Reference requirements at risk

- Each $facet sub-pipeline must compute per-category metric with age band derived using $bucket — prompt requires age bands but does not specify $bucket; builder may implement buckets differently.
- A `.env.example` lists every setting with placeholder values — skill_md instructs to use `.env.example` but does not list every setting the final sample needs (e.g., refresh schedule, summary collection name).
- The vector index dimensions match the embedding model's output — prompt does not use embeddings; vector-index/dimension alignment is not specified and will likely be omitted.
- Vector index parameters chosen for the sample's data size, and README guidance to change them — indexes and README tuning are not requested and may be missing.
- Seed script loads sample data and creates the index, and can be run twice without duplicating data — prompt asks to verify against live cluster but does not require an idempotent seed script; absent unless the builder adds it.
- /search returns clear error for an empty query and when the embedding call fails; search results include similarity score — the starter prompt does not ask for a `/search` endpoint or embeddings, so these search-related requirements are at risk of being omitted.
- Dependencies are pinned in `requirements.txt` — not specified; builder may or may not pin exact versions.
- Unit tests run without a live cluster — tests are not specified; without explicit instruction the builder may write tests that hit the live cluster.
- Infrastructure-as-code for the cluster — the run environment provides an existing cluster and the prompt forbids provisioning, so no IaC will be provided unless the builder separately adds it.
- README that documents what the sample shows, prerequisites, setup, run, and clean-up — the prompt does not require a full README; likely to be incomplete unless the builder authors one.

## Questions for the prompt author

- Which Python minor version should the sample target (e.g., 3.10 or 3.11)?
- Preferred scale for the seed data (e.g., 1k, 10k, 100k patients)? this affects index and pipeline design and README guidance.
- How often should the scheduled refresh run (e.g., every hour, daily)? and should the scheduler be in-process (APScheduler) or an external cron/job triggerable via an endpoint?

## Contradictions and missing references

None.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | "build a Python FastAPI service that exposes aggregation-backed endpoints for a population health dashboard" | - | - | Prompt clearly states business goal and what to demonstrate (faceted aggregations, caching summaries). |
| Workflow type | missing | no | - | - | Builder will use a single-agent, no-orchestration approach (one process running FastAPI with background scheduler). | Prompt says 'Using the DocumentDB skill' but does not specify an agent framework or orchestration; not needed to start the sample. |
| Language and runtime | ambiguous | no | "Python FastAPI"; skill_md: "python and pip resolve to a virtual environment" | - | Use a recent stable Python 3.x — e.g., Python 3.10 or 3.11 for the sample and CI. | Prompt specifies Python/FastAPI but not an exact Python minor version. |
| Driver and version | covered_by_skill | no | - | documentdb-driver | Use PyMongo (pymongo) compatible with MongoDB 7.0, e.g. pymongo >=4.4.0; implement MongoClient as a singleton per documentdb-driver guidance. | The documentdb-driver skill covers driver best-practices (singleton client, reuse). It does not prescribe an exact pip version; builder will pick a recent compatible pymongo. |
| Target service and tier | specified | no | skill_md: "A vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol, DiskANN, HNSW and IVF vector indexes) is reachable... use database named `sample_healthcare_16`" | - | - | Run-environment (skill_md) explicitly defines the live cluster and database to use. |
| Authentication and secrets | specified | no | skill_md: "Its connection string is in the environment variable `DOCUMENTDB_URI`. Read it from the environment at run time. Never write its value into any file ... use a config file or `.env.example` with a placeholder" | - | - | Location of connection string and .env guidance are given in the run environment note. |
| Data model | missing | no | "break down patient cohorts by diagnosis, age band, gender, and region"; "materialised summary documents" | documentdb-data-modeling | Create a `patients` collection with documents like { patient_id, dob (or age), gender, region, diagnoses: [codes], lastEncounterDate, metadata }. Create a `summaries` collection to store materialised aggregation documents keyed by summary name and timestamp. | Prompt requires faceted breakdowns but does not define collection names, field names, or exact document shapes; documentdb-data-modeling can guide choices but the schema itself is unspecified. |
| Sample data | missing | no | - | - | Provide an idempotent seed script that generates synthetic patient data (e.g., a few thousand records) and upserts into `sample_healthcare_16.patients`. The seed script will be safe to run multiple times (use unique keys/upsert). | Prompt and installed skills do not supply an actual dataset or its licence/source. |
| Queries and indexes | ambiguous | no | "Implement faceted queries ... using $facet"; skill_md & reference mention vector indexes exist but prompt doesn't require vector/search. | documentdb-indexing | Aggregation pipelines will use $facet with sub-pipelines per dimension; to support performance, create single-field indexes on diagnosis (or diagnoses array as multikey), gender, region, and an index on dob or age field to support bucketing. No vector or text indexes will be required unless search is later added. | Query pattern (use $facet) is specified, but exact index shapes and parameters are not; documentdb-indexing skill should be consulted to pick indexes. |
| AI components | missing | no | - | documentdb-vector-search | No embedding or chat model is required for this sample; vector search is not implemented. The cluster's vector capabilities will be unused unless search/semantic features are later added. | Prompt does not ask for embedding or other AI pieces; if added, their models/dimensions would need explicit spec. |
| App surface | ambiguous | no | "build a Python FastAPI service that exposes aggregation-backed endpoints" | - | Provide endpoints such as: GET /facets (returns live computed facets), GET /summaries/{name} (returns cached summary), POST /summaries/refresh (trigger refresh), and background scheduled refresh. Inputs: query parameters to filter cohort (date range, diagnosis filter); outputs: JSON with buckets and counts. | Prompt specifies FastAPI and aggregation-backed endpoints but does not enumerate exact routes or request/response shapes. |
| Provisioning and deployment | specified | no | skill_md: "This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable... Do not provision another cluster unless the run policy says Azure writes are allowed; the cluster above is the one to use." | - | - | The run environment explicitly instructs to use the existing cluster and not to provision new infrastructure. |
| Run and test instructions | missing | no | - | - | Provide README commands: pip install -r requirements.txt, cp .env.example .env (fill DOCUMENTDB_URI), run seed script, run uvicorn main:app --reload, and pytest for tests. Unit tests will be written to run without a live cluster using mocks. | Prompt and skills do not provide explicit run/test command list. |
| Definition of done | missing | no | - | - | Accept when: FastAPI endpoints exist and return JSON of facet buckets; expensive aggregations are written to `summaries` collection; scheduled refresh updates summary documents; seed script populates sample data; code uses singleton MongoClient; README explains setup and run steps. | No explicit acceptance criteria provided in the prompt. |
| Constraints and non-goals | missing | no | - | documentdb-security | Keep cloud cost low by using existing cluster; do not attempt to provision production-grade HA or cross-region DR; do not include PHI beyond synthetic sample data. | Prompt does not state cost/scale limits or privacy constraints; build should assume synthetic data only. |
| Repository conventions | covered_by_skill | no | skill_md: "Never write its value into any file, log, README or test fixture; use a config file or `.env.example` with a placeholder, as the prompt asks." | - | Follow standard layout: src/ or app/, tests/, scripts/seed_data.py, requirements.txt pinned, .env.example with placeholders, README.md with setup/run/cleanup, and use the name 'Azure DocumentDB' in docs. | Run-environment guidance covers at least the .env.example / secrets convention. Use that plus typical gallery conventions. |
