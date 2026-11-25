# 1. Prompt review: 15-cohort-analysis-backend

**Verdict: sufficient_with_assumptions**

The prompt clearly states the core goal: a Python FastAPI service that runs a DocumentDB aggregation (using $bucket and $facet) to compute 30/60/90-day cohort retention and materialises weekly snapshots. Many implementation details (Python version, driver version, exact collection/field names, endpoints, seed data, indexes, README and test conventions) are left to the builder and will be filled by installed skills (driver best-practices, aggregation/querying, indexing, local-deployment) or by sensible defaults.

## Where each answer will come from

| Source | Rubric items |
|---|---|
| In the prompt | 2: Goal and scenario, Target service and tier |
| Covered by a skill | 1: Authentication and secrets |
| Ambiguous: builder will guess | 5: Language and runtime, Driver and version, Data model, Queries and indexes, App surface |
| Missing: builder will guess | 7: Workflow type, Sample data, Provisioning and deployment, Run and test instructions, Definition of done, Constraints and non-goals, Repository conventions |
| Not applicable | 1: AI components |

## Reference requirements at risk

- .env.example lists every setting with placeholder values — not mentioned by the prompt and not enforced by any installed skill; builder must add it (risk: may be omitted).
- The vector index dimensions match the embedding model's output — not relevant to the prompt's functionality and not specified (risk: if vector features are later added, dimensions may be inconsistent).
- The vector index parameters are chosen for the sample's data size, and README says how to change them — not covered; vector indexing isn't part of the prompt.
- Seed script loads sample data and can be run twice without duplicating data — prompt does not request this explicitly (local-deployment skill gives guidance but doesn't guarantee an idempotent script will be produced).
- /search returns clear error for an empty query and when the embedding call fails — /search is not part of the cohort prompt; therefore this requirement is not addressed.
- Search results include the similarity score — irrelevant to cohort endpoints; not covered.
- Dependencies are pinned in requirements.txt — prompt doesn't state this explicitly; builder may or may not pin versions.
- Unit tests run without a live cluster — not specified; installed skills advise local testing with containers/mocks, but no explicit test harness is requested.
- Infrastructure for the cluster is provided as code (Azure DocumentDB resource type) — prompt and run-environment indicate using an existing cluster; no IaC is requested and documentdb-azure-deployment skill is available but not invoked.
- README covers what the sample shows, prerequisites, setup, run, and clean-up — prompt doesn't require a README but gallery samples normally need one; this may be omitted if the builder doesn't add it.
- The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name — prompt doesn't mandate naming conventions; builder may accidentally use other product names unless instructed.

## Questions for the prompt author

- Which Python runtime should the sample target (e.g., 3.10, 3.11)?
- Which Python MongoDB driver do you prefer (pymongo synchronous or motor async)? This will affect how FastAPI endpoints are written.
- Do you want specific collection names and a formal document schema (e.g., `customers` and `events` with exact field names), or should the builder invent a sensible schema?
- Should the weekly refresh be implemented as a scheduled background job (APScheduler) inside the service, or as a separate cron/CI job and an admin endpoint to trigger refresh manually?
- Do you want a seed script included and, if so, how large should the sample dataset be (e.g., ~1k customers over 12 months)?

## Contradictions and missing references

- Prompt says “Using the DocumentDB skill” but there is no single installed skill named exactly “DocumentDB skill”; instead many documentdb-* skills are available (documentdb-driver, documentdb-natural-language-querying, etc.). The prompt's reference to a single skill name is ambiguous.

## Rubric

| Item | Status | Blocking | In the prompt | Skill | Assumed if unanswered | Note |
|---|---|---|---|---|---|---|
| Goal and scenario | specified | no | “build a Python FastAPI service that exposes cohort analysis endpoints backed by DocumentDB aggregation.” | - | - | Prompt directly describes business problem: cohort analysis with retention and breakdowns; caching weekly snapshots. |
| Workflow type | missing | no | - | - | Single-agent sample app (one service process) running locally / on the developer machine; no multi-agent orchestration or agent framework used. | Prompt does not state whether this is to be implemented as a single agent run or integrated with agent frameworks; builder will assume a single process FastAPI app. |
| Language and runtime | ambiguous | no | “Python FastAPI” | - | Use Python 3.11 (or latest stable 3.x available on the developer machine) and FastAPI ~0.95+, run with Uvicorn. Use a virtualenv as described in skill.md. | Prompt specifies language and framework but not exact Python version or FastAPI/uvicorn versions. |
| Driver and version | ambiguous | no | - | documentdb-driver | Use PyMongo (pymongo) 4.x (compatible with MongoDB 7.0 wire protocol). Implement MongoClient as a singleton per process as recommended by documentdb-driver. | Prompt doesn't pick a Python MongoDB driver or version; documentdb-driver gives best-practice patterns but not a pinned driver version. |
| Target service and tier | specified | no | Skill/run environment: a vector-capable Azure DocumentDB cluster (compute tier M30, MongoDB 7.0 wire protocol) reachable; use DB sample_customer_360_15 | - | - | The provided run-environment (skill.md) states the exact cluster and database to use; builder should target that live cluster rather than provisioning a new one. |
| Authentication and secrets | covered_by_skill | no | skill.md: connection string is in the environment variable DOCUMENTDB_URI; read at run time; never write it into files or logs. | skill.md (run environment) | - | Credentials come from env; the prompt did not say how secrets are surfaced, but skill.md requires DOCUMENTDB_URI. |
| Data model | ambiguous | no | Prompt mentions grouping customers by acquisition month and breaking down by channel and product (implies customers and event/purchase records). | documentdb-data-modeling | Create collections: `customers` (customer_id, acquired_at, channel, metadata) and `events` or `purchases` (customer_id, product_id, event_date, event_type, amount). Use denormalized fields for fast aggregation (embed product/channel where useful). Add `schemaVersion` field. | Prompt implies required fields but does not specify exact collection names or document schema; the data-modeling skill gives guidance but not a concrete schema. |
| Sample data | missing | no | - | documentdb-local-deployment | Provide an idempotent seed script that generates synthetic data (e.g., 6–18 months of acquisition, purchases across channels/products). Script can be re-run safely (use upsert by a stable key or delete+insert). | Prompt does not say where sample data comes from or its size; local-deployment skill explains seed-script patterns but does not supply exact dataset. |
| Queries and indexes | ambiguous | no | “Use $bucket to group customers by acquisition month, compute retention rates at 30/60/90 days, and break down by channel and product using $facet.” | documentdb-natural-language-querying, documentdb-indexing, documentdb-query-optimization | Aggregation pipeline will include $bucket on acquisition month and $facet for channel/product. Create supporting indexes on acquired_at (date), customer_id, channel, product_id and possibly compound indexes to support aggregation stages. Verify with explain() and tune if COLLSCAN occurs. | Prompt specifies pipeline operators but not index choices; indexing skill gives guidance to choose indexes matching aggregation patterns. |
| AI components | not_applicable | no | - | - | - | No embedding or LLM components requested by the prompt. |
| App surface | ambiguous | no | “exposes cohort analysis endpoints” and “Cohort endpoints serve their results from the cached snapshot documents.” | - | Expose HTTP endpoints such as GET /cohorts (list snapshots), GET /cohorts/{cohort_month} (snapshot details), optional query params to filter by channel/product. Add an admin endpoint or background job to trigger refresh (or use APScheduler to run weekly). Return JSON with cohorts, retention rates and breakdowns. | Prompt specifies endpoints conceptually but not route names, input parameters, or precise response shape. |
| Provisioning and deployment | missing | no | Prompt doesn't ask to provision a cluster; skill.md states one exists and warns not to create another unless policy allows. | documentdb-azure-deployment | Do not provision a new Azure DocumentDB cluster; use the existing cluster referenced in skill.md. Provide local run/runbook instructions, not IaC provisioning for the cluster. | There is an Azure deployment skill available, but the run environment indicates the sample should not create a new cluster. |
| Run and test instructions | missing | no | - | documentdb-local-deployment | Include README steps: create .env from .env.example, pip install -r requirements.txt, run seed script, run `uvicorn app.main:app --reload`, run tests via pytest (with mocks for DB). A successful run returns example cohort JSON and shows the snapshot document created in the snapshots collection. | Prompt does not include exact commands or test strategy; builder will add standard run/test instructions. |
| Definition of done | missing | no | - | - | Accept if: endpoints return cached cohort snapshots matching seeded data, aggregation pipeline runs successfully and snapshots are updated weekly (or on-demand), seed script is idempotent, and code follows driver best-practices (singleton client). | Prompt lacks concrete acceptance criteria; builder will invent reasonable checks. |
| Constraints and non-goals | missing | no | - | - | Keep costs minimal: do not provision new cluster; keep dataset small for demos; do not implement production HA or cross-region DR. Focus the sample on cohort aggregation and snapshotting, not on full product analytics UI. | No cost or scope limits are provided; builder will keep the sample light-weight. |
| Repository conventions | missing | no | - | documentdb-local-deployment | Use common layout: README.md, app/ (FastAPI code), scripts/seed.py, tests/, .env.example, requirements.txt (pinned). Do not commit actual secrets; follow .env.example placeholders. | Prompt does not give layout or naming rules; local-deployment skill suggests env-driven config and seed conventions. |
