# 5. Best-practice audit: 15-cohort-analysis-backend

**Verdict: pass_with_findings** (9 followed, 7 violated, 1 not applicable)

The sample implements the requested FastAPI cohort-backend, runs the aggregation with $bucket and produces materialised snapshots that the API serves. The run verified seeding, index creation and a successful one-shot snapshot generation against the provided cluster. Main findings: (1) the pipeline does use $bucket successfully in this environment but public docs warn $bucket is unsupported on some Mongo-API server versions — the product docs should be made more prominent to prevent fragile samples; (2) the implementation materialises snapshots but inserts new snapshot documents rather than replacing/upserting previous snapshots; (3) the pipeline computes breakdowns by channel/product but does not use a $facet stage as the prompt suggested; (4) some operational best-practices (explain()/diagnostics, retry/backoff for snapshot writes, RU/throughput guidance and basic instrumentation) are missing. None of the missing items make the sample unusable for demo, but several are important for production-readiness and for agents generating similar samples.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approval of 'ready_with_gaps' is an operator choice. Events show multiple readiness approvals were logged; the build proceeded with the stated readiness level. |
| D002 | I chose Python 3.11+ with FastAPI (uvicorn) as the language and framework for the sample. | prompt | sound | Choosing Python + FastAPI matches the prompt and the run environment; events show this decision was logged and the code uses FastAPI. |
| D003 | I chose PyMongo (pymongo) 4.x as the MongoDB driver and will use a singleton MongoClient per process. | prompt | sound | Choosing PyMongo and a singleton MongoClient follows driver-skill guidance; the code implements a singleton client (app/app/db.py). Events show the documentdb-driver skill was loaded when making this choice. |
| D004 | I chose to use the connection string from DOCUMENTDB_URI environment variable. | readiness_report | sound | The decision to use DOCUMENTDB_URI from environment matches the provided run environment and is consistent with the code (app/app/db.py) and .env.example. Events show the run environment note and the log_decision recorded the choice. |
| D005 | I chose separate collections: 'customers' and 'events' (purchases) with denormalized key fields (channel and product_id) on the events and a schemaVersion field. | prompt | sound | Choosing separate collections customers/events and denormalized fields is consistent with the code and seed script. The code and seed both implement that design (scripts/seed.py lines 24-56). |
| D006 | I chose to seed ~1000 customers over 12 months (configurable via script), defaulting to 500 for faster runs in CI. | readiness_report | sound | Seeding ~1k customers was a reasonable builder choice for demo. The seed script shows NUM_CUSTOMERS configurable; the actual run used 800 customers as reported in the builder report. Events show the seed script ran and inserted sample data. |
| D007 | I chose to materialize cohort snapshots in a 'cohort_snapshots' collection and refresh with a weekly APScheduler job (and expose an admin endpoint to trigger refresh on demand). | prompt | sound | Materialising snapshots in cohort_snapshots and scheduling weekly with APScheduler is implemented (app/app/main.py scheduler lines 9-18). Decision is supported by the code and recorded in events. |
| D008 | I chose to create indexes: customers.acquired_at (single-field), events.customer_id + event_date (compound), events.product_id, events.channel; and a TTL index not needed. | prompt | sound | Index choices were logged and implemented (scripts/seed.py lines 77-85 create indexes). Events confirm index creation via MCP queries during verification. |
| D009 | I approved the build with readiness 'ready_with_gaps' | operator | sound | A later readiness approval with the same text was recorded; consistent with D001. Events show repeated readiness logs. |
| D010 | I chose Python 3.11 with FastAPI and Uvicorn, using PyMongo (pymongo 4.x) as the MongoDB driver. | prompt | sound | Re-affirmation of framework/driver choice (Python/FastAPI/PyMongo) — the code and runtime confirm this selection. |
| D011 | I chose PyMongo (synchronous) 4.x for the driver and will implement a singleton MongoClient per process. | prompt | sound | Decision to use synchronous PyMongo and singleton client is implemented in code and consistent with loaded skills. |
| D012 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Another readiness approval; recorded in the run and consistent with build progress. |
| D013 | I chose Python with FastAPI and Uvicorn. | prompt | sound | Choosing Python + FastAPI again — consistent and supported by the code base. |
| D014 | I chose PyMongo (pymongo) 4.x. | prompt | sound | Pinning to PyMongo 4.x is consistent with the compatibility docs and with the pinned requirements file present in the repo. |
| D015 | I chose to use the existing cluster specified by DOCUMENTDB_URI and NOT provision any Azure resources. | readiness_report | sound | Decision not to provision a new cluster is consistent with the run environment and the run policy; code uses the existing cluster via DOCUMENTDB_URI. |
| D016 | I chose to pin versions in requirements.txt (fastapi 0.95.2, pymongo 4.5.0, uvicorn 0.23.2, apscheduler 3.10.1). | model_default | questionable | Pinning specific dependency versions was logged with reason_source 'model_default'. The project does pin versions; this is reasonable but model_default means the choice wasn't explicitly grounded in an external compatibility doc at the time of the decision. There are public docs covering supported wire-protocols and driver compatibility (Quickstart/compatibility pages), so this is a discoverability gap more than an unsupported decision — consider citing the compatibility page when pinning. |
| D017 | I chose to run the snapshot generation via a python -c one-liner that appends '.' to sys.path at runtime. | tool_unavailable | sound | Decision to run snapshot via python -c with sys.path.append('.') was driven by the runner refusing a PYTHONPATH= prefix; events show the 'PYTHONPATH=.' invocation was refused and that the author used an alternate approach. The 'tool_unavailable' / refusal is present in events and supports the logged reason. |

Documentation gaps: 5 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

| Source | Reachable | Detail |
|---|---|---|
| `learn` (documentation search) | yes | 3 tools |
| Installed agent skills | 17 | 17 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 2 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 1 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 0 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 14 | Public and discoverable. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| Driver version support | Pin the driver version and use a version the service supports.<br>**Searches:** search: 'Azure DocumentDB pymongo supported versions quickstart' | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python) |
| Feature-support check | Check the Azure Cosmos DB feature-support pages for the server-version you run; aggregation-stage support varies by server version.<br>**Searches:** search: 'Azure DocumentDB aggregation stage $bucket feature support' | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language) |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Bucket stage support | Avoid relying on aggregation stages that may be unsupported by some API-server versions (e.g., $bucket/$bucketAuto) — check compatibility pages. | [Azure Cosmos DB feature support (MongoDB) / aggregation pipeline pages](https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-70#aggregation-pipeline) |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Singleton MongoClient | Create and reuse a single MongoClient process-wide (singleton) and avoid creating a new client per request; configure pool parameters only after understanding your workload. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Connection tuning | Tune connection-pool settings to your deployment scenario and set fail-fast timeouts. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| No credentials in repo | Read the DocumentDB connection string from an environment variable (DOCUMENTDB_URI), never hard-code credentials and keep only a .env.example | README.md / .env.example<br>README.md / .env.example |
| Prefer Entra ID for auth | Keep DB credentials in a secret store and prefer Microsoft Entra (managed identity) + RBAC instead of long-lived DB passwords | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| TLS enforcement | Always require TLS for client connections and never disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Retryable writes and app retries | Enable driver retryable reads/writes where supported and implement application-level retries with exponential backoff for transient errors. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Indexes for cohort aggregation | Create indexes that support your cohort aggregation and query patterns — index acquisition timestamp and customer identifier and add compound ESR indexes for common filters/sorts. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Aggregation & explain() | Prefer aggregation pipelines (server-side aggregation) and verify pipeline performance with explain(). | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Project early | Project only required fields early in aggregation pipelines to reduce RU usage. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Materialize snapshots | Materialize heavy cohort snapshots as compact summary documents and refresh them on a schedule; perform snapshot writes with batched operations to reduce RU and roundtrips. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Embed frequently-read attributes | Embed frequently-read attributes (channel, product) in event documents to avoid expensive $lookup joins. | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Instrument snapshots | Instrument the service with application-level metrics (snapshot duration, RU consumed per snapshot) and alert on RU throttling. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Compound indexes for facets | For aggregation facets (channel/product breakdown), design compound indexes matching equality and group keys (ESR rule). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Prefer incremental snapshots | Prefer incremental/change-feed-driven snapshot updates rather than full recomputes for large datasets. | [Improve efficiency of reads by using a cache / materialize via Stream Analytics and change feed](https://learn.microsoft.com/azure/cosmos-db/how-to-cache#caching-patterns) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Keep DB credentials in a secret store and prefer Microsoft Entra (managed identity) + RBAC instead of long-lived DB passwords | authentication_and_secrets | The app reads DOCUMENTDB_URI and uses it for SCRAM auth (app/app/db.py lines 7-11). No OIDC/Microsoft Entra ID flow is implemented. | Document why SCRAM is used in README and add guidance / optional example for MONGODB-OIDC/DefaultAzureCredential (or provide a separate sample that enables Microsoft Entra ID authentication). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Enable driver retryable reads/writes where supported and implement application-level retries with exponential backoff for transient errors. | retries | The MongoClient is constructed with retryWrites=True in some app/db.py variants in the repo (events show that), but snapshot writes (snapshots.insert_one) are not wrapped with explicit application-level retries or backoff (app/app/cohort.py lines 174-175). | Wrap snapshot persistence in a retry loop with exponential backoff (or use a helper that retries transient errors), and consider capturing and retrying RequestRateTooLarge/429 responses. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Prefer aggregation pipelines (server-side aggregation) and verify pipeline performance with explain(). | queries | The app uses aggregation pipelines (good) but the sample does not call explain("executionStats") or capture executionStats to validate index usage and RU-cost (app/app/cohort.py runs customers.aggregate(...) but no explain call). | Add an explain("executionStats") step in scripts/refresh_snapshots.py or a helper that records the aggregation's executionStats to logs or a diagnostics collection so readers can confirm index usage and RU consumption. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Project only required fields early in aggregation pipelines to reduce RU usage. | queries | The pipeline does a $lookup that pulls full events arrays then filters in-memory; it does not project minimal fields in the $lookup pipeline (app/app/cohort.py lines 66-74 and $lookup). | Use $lookup with a pipeline that $project only the event_date and product/channel fields required, or project fields before expensive stages to limit returned data. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Instrument the service with application-level metrics (snapshot duration, RU consumed per snapshot) and alert on RU throttling. | monitoring | No instrumentation or logging of snapshot duration or RU consumption is implemented; generate_cohort_snapshot simply runs the pipeline and inserts snapshot (app/app/cohort.py lines 145-175). | Log snapshot start/end times and capture explain() RU metrics or return executionStats; add a basic metric emit (duration, doc counts, and failure counts) to the snapshot script. | [documentdb-monitoring](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/monitoring/SKILL.md) |
| Prefer incremental/change-feed-driven snapshot updates rather than full recomputes for large datasets. | caching | The app runs a full recompute weekly (BackgroundScheduler or on-demand), it does not implement incremental or change-feed updates (app/app/main.py lines 9-18 and app/scripts/generate_snapshot.py). | Document and optionally provide an alternate script that uses the cluster's change feed or change streams to incrementally update snapshots, or show how to run per-cohort partial recomputes. | [Improve efficiency of reads by using a cache / materialize via Stream Analytics and change feed](https://learn.microsoft.com/azure/cosmos-db/how-to-cache#caching-patterns) |
| Check the Azure Cosmos DB feature-support pages for the server-version you run; aggregation-stage support varies by server version. | queries | The sample did not add a README note or runtime compatibility check to ensure the server version supports all aggregation stages used (no explain() or server-version check documented). | Add a short 'compatibility check' step in README (and an optional script) that queries the server for its MongoDB wire version or runs a small feature-check pipeline and exits with a clear error if unsupported stages (like $bucket) are missing. | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create and reuse a single MongoClient process-wide (singleton) and avoid creating a new client per request; configure pool parameters only after understanding your workload. | connection | app/app/db.py: uses module-level _client and get_client() to return a singleton MongoClient (lines 13-28). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Tune connection-pool settings to your deployment scenario and set fail-fast timeouts. | connection | app/app/db.py: sets serverSelectionTimeoutMS and (in a prior write) retryWrites=True; conservative defaults used when constructing MongoClient (lines 19-25 in some app/db.py copies). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Pin the driver version and use a version the service supports. | connection | app/requirements.txt pins pymongo==4.5.0 (app/requirements.txt line 3). Microsoft docs state DocumentDB supports modern MongoDB wire protocol versions so recent PyMongo 4.x is appropriate. | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python) |
| Read the DocumentDB connection string from an environment variable (DOCUMENTDB_URI), never hard-code credentials and keep only a .env.example | authentication_and_secrets | app/app/db.py: DOCUMENTDB_URI read from env (lines 7-11). app/.env.example contains placeholder (app/.env.example lines 1-3). No secrets are checked in. | README.md / .env.example<br>README.md / .env.example |
| Always require TLS for client connections and never disable certificate validation in production. | security | app/.env.example suggests mongodb+srv connection string including tls=true and README warns not to commit secrets (app/.env.example & README.md). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Create indexes that support your cohort aggregation and query patterns — index acquisition timestamp and customer identifier and add compound ESR indexes for common filters/sorts. | indexing | app/scripts/seed.py creates indexes on customers.customer_id (unique), customers.acquired_at, customers.channel, customers.primary_product_id and events.customer_id, events.event_date, events.product_id (seed.py lines 77-85). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Materialize heavy cohort snapshots as compact summary documents and refresh them on a schedule; perform snapshot writes with batched operations to reduce RU and roundtrips. | caching | App materializes a compact snapshot document and writes it to cohort_snapshots (app/app/cohort.py lines 168-175). The weekly scheduler is configured (app/app/main.py lines 9-18). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Embed frequently-read attributes (channel, product) in event documents to avoid expensive $lookup joins. | data_modeling | Seeded documents include channel and primary_product_id fields in customer and product/product_id and channel in events (app/scripts/seed.py lines 44-52 and event docs lines 66-72). | [documentdb-data-modeling](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/data-modeling/SKILL.md) |
| Avoid relying on aggregation stages that may be unsupported by some API-server versions (e.g., $bucket/$bucketAuto) — check compatibility pages. | queries | The app uses $bucket (app/app/cohort.py lines 98-113) and the one-shot snapshot generation completed successfully in this run (builder_report: 'Generated snapshot: ...'). However Azure docs explicitly warn some aggregation stages may be unsupported on some API-server versions. | [Azure Cosmos DB feature support (MongoDB) / aggregation pipeline pages](https://learn.microsoft.com/azure/cosmos-db/mongodb/feature-support-70#aggregation-pipeline) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| For aggregation facets (channel/product breakdown), design compound indexes matching equality and group keys (ESR rule). | indexing | The app creates single-field indexes that are useful for lookups, but does not create compound ESR indexes specifically tuned for the current facet computation (seed.py lines 77-85). The sample's small dataset is served by single-field indexes; for large data, add compound indexes. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |

### Reference requirements

14 of 21 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC files (Bicep/Terraform/ARM) for Microsoft.DocumentDB/mongoClusters are present in the repository (no templates in repo root). | Add a small Bicep or Terraform example that creates a Microsoft.DocumentDB/mongoClusters resource (or an ARM template snippet) and documents default low-cost parameters. |
| The pipeline uses a `$facet` stage to break the cohorts down by channel and by product. | partly_met | builder_error | app/app/cohort.py: channel and product breakdowns are produced by $push/$arrayToObject mapping after the $bucket stage (lines 109-140, 116-141), but there is no `$facet` stage in the pipeline. | Replace or augment the post-bucket transformation with an explicit $facet stage that computes channel and product facets (small change in the pipeline definition: add a $facet with two sub-pipelines that $unwind/$group or $sortByCount on channels and products). |
| A weekly refresh re-runs the pipeline and replaces the materialised snapshot documents. | partly_met | builder_error | app/app/main.py: BackgroundScheduler schedules weekly_job that calls generate_cohort_snapshot(db) (lines 9-18). | Change snapshot persistence to upsert/replace (e.g., use update_one(filter={'snapshot_month': ...}, {'$set': snapshot}, upsert=True) instead of insert_one) so a weekly run replaces the previous snapshot rather than inserting a fresh document. |
| The vector index dimensions match the embedding model's output. | not_checkable | - | No vector index or embedding model is used by this sample; vectors are out of scope. | n/a |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector search or vector index in the repository. | n/a |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | prompt_silent | This sample exposes cohort endpoints only; no /search endpoint exists. | If search is later added, add explicit input validation and error handling that returns HTTP 400 for empty queries and 502/503 for embedding failures. |
| Search results include the similarity score. | not_checkable | prompt_silent | No search endpoint or vector retrieval implemented in this sample. | n/a |
| A Python FastAPI service exposes HTTP endpoints that return cohort analysis results. | met | - | app/app/main.py: lines 24-36 define GET /cohorts and GET /cohorts/{snapshot_month}; lines 39-43 define POST /admin/refresh. | n/a |
| The cohort computation is an aggregation pipeline that Azure DocumentDB executes, sent through a MongoDB driver (e.g. PyMongo). | met | - | app/app/cohort.py: pipeline defined and executed with customers.aggregate(...); app/scripts/generate_snapshot.py runs generate_cohort_snapshot (app/app/cohort.py: lines 64-146, 145-176). | n/a |
| The pipeline uses a `$bucket` stage to group customers by acquisition month. | met | - | app/app/cohort.py: $bucket stage present (lines 98-113) with groupBy: "$acquired_at" and boundaries constructed earlier. | n/a |
| The pipeline computes retention rates at 30, 60 and 90 days for each cohort. | met | - | app/app/cohort.py: retained30/retained60/retained90 computed in $addFields (lines 76-97) and summed in $bucket output (lines 105-108). | n/a |
| Cohort snapshots are cached as materialised documents stored in Azure DocumentDB (e.g. a snapshots collection), produced by running the pipeline. | met | - | app/app/cohort.py: snapshot document constructed and snapshots.insert_one(snapshot) (lines 168-175). scripts/generate_snapshot.py (lines 8-11) runs the function and prints the result. | n/a |
| The cohort endpoints serve their results from the cached snapshot documents. | met | - | app/app/main.py -> api_list_snapshots and api_get_snapshot call list_snapshots/get_snapshot which read from cohort_snapshots (lines 24-36). | n/a |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/app/db.py: reads DOCUMENTDB_URI and DB_NAME from environment (lines 5-11). app/.env.example contains placeholders (app/.env.example lines 1-3). | n/a |
| A `.env.example` lists every setting with placeholder values. | met | - | app/.env.example lists DOCUMENTDB_URI and DB_NAME (app/.env.example lines 1-3). | n/a |
| One database client is created and reused across requests. | met | - | app/app/db.py: uses a module-level _client and get_client(), returning a singleton MongoClient (lines 13-28). | n/a |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed.py: drops and re-inserts collections (lines 35-38) and creates indexes (lines 77-85). The script is idempotent for demo use (deletes previous sample data then inserts fresh data). | n/a |
| Dependencies are pinned in `requirements.txt`. | met | - | app/requirements.txt pins exact versions (fastapi==0.95.2, uvicorn==0.23.2, pymongo==4.5.0, etc.) (app/requirements.txt lines 1-7). | n/a |
| Unit tests run without a live cluster. | met | - | app/tests/test_cohort.py uses mongomock and inserts a small in-memory DB for tests; tests do not require a live cluster (app/tests/test_cohort.py shows mongomock usage). | n/a |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md includes 'What this sample shows', prerequisites, quick start, API endpoints and cleaning up instructions (README.md lines 1-31, 37-43). | n/a |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | app/README.md, .env.example and other files refer to 'Azure DocumentDB' (README.md lines 1 and 14; .env.example comments). | n/a |

