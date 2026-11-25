# 5. Best-practice audit: 07-customer-review-sentiment-pipeline

**Verdict: fail** (7 violated, 6 not assessable, 2 not applicable)

The build did not produce the sample code or artifacts requested by the starter prompt. The builder recorded design decisions and loaded many DocumentDB skills, but no source files, scripts, README, .env.example, requirements, tests or index-creation scripts were written or executed. Because the core pipeline (async Beanie code that calls OpenAI and upserts enriched documents) is missing, the sample does not implement the starter prompt and cannot be verified. The run did surface useful guidance (connection, indexing, security, vector-search) from the installed skills; several public best-practices are discoverable. Key gaps that blocked this build are (a) the builder did not create files due to a tooling/parsing error and (b) a driver compatibility question (Beanie + Motor vs PyMongo Async client) remains unresolved. See requirement_results for per-requirement findings, checks for reconciled practices, decision_reviews for each recorded decision, and doc_gaps with recommended fixes.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | D001 is an operator approval recorded as 'approved with --yes'. Events.jsonl shows the readiness/approval logging and this is an operator action; the trace contains the log. |
| D002 | I chose Python 3.11 as the language/runtime for the sample. | prompt | sound | D002 (choose Python 3.11) is supported by the prompt (async Python + Beanie) and the events.jsonl log_decision records it (Recorded as D002). Evidence supports the decision. |
| D003 | I approved the build with readiness 'ready_with_gaps' | operator | sound | D003 is another operator acceptance recorded in decisions.jsonl; events show the recorded action and no conflicting sources; assessment is sound. |
| D004 | I chose Beanie with Motor (AsyncIOMotorClient) as the async driver for this sample. | model_default | questionable | D004 chose Beanie + Motor (AsyncIOMotorClient). Events.jsonl shows the documentdb-connection and Beanie quickstart guidance recommending PyMongo's AsyncMongoClient for Beanie 2. The decision's reason_source is 'model_default' rather than the skill; the choice is defensible historically but it contradicts the loaded skill's quickstart. The trace shows the skill was loaded before the decision (events lines show load_skill documentdb-connection). |
| D005 | I chose to use the OpenAI model 'gpt-3.5-turbo' and the env var OPENAI_API_KEY for the API key. | model_default | sound | D005 selected gpt-3.5-turbo and OPENAI_API_KEY. No installed DocumentDB skill prescribes an OpenAI model; the choice is a reasonable default and events.jsonl records the log_decision. Because the choice is a model default, add documentation guidance (see doc_gaps) so future builders don't rely on ungrounded defaults. |

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
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 1 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 12 | Public and discoverable. |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Audit trail: index plan | Audit trail — record index-shape decisions | checklist only (no public address recorded) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| OpenAI concurrency limit | Limit concurrency to external APIs (OpenAI) and the database (by batching DB writes) so the pipeline is resilient to rate limits and doesn't overwhelm the DB. | A short sample showing asyncio.Semaphore usage for OpenAI calls and how to batch DB writes would let an agent implement this reliably. |
| Beanie field types & indexes | When using an ODM (Beanie/Pydantic), declare explicit Pydantic field types for embeddings and scores and create indexes at model/migration time rather than relying on implicit typing. | A brief Beanie quickstart page showing Pydantic type annotations for List[float] (embedding) and float (sentiment_score) and create_index examples for Beanie would help agents author correct models. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Env var for URI and secrets | Read the cluster connection URI from an environment variable (e.g., DOCUMENTDB_URI) at runtime and never commit credentials; ship a .env.example or config template with placeholders instead of real secrets. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Async driver selection | For new Python async code on Azure DocumentDB prefer PyMongo's AsyncMongoClient rather than Motor; Motor is deprecated and PyMongo's async API is the supported path. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)<br>Quickstart: Connect Beanie to Azure DocumentDB |
| Least-privilege DB user | Create and use a dedicated least-privilege database user for applications (or prefer Microsoft Entra ID / managed identity + RBAC). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| TLS required | Always use TLS for connections to Azure DocumentDB (tls=true) and do not disable certificate validation in production; prefer SCRAM-SHA-256 for authentication. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Retryable reads/writes | Enable driver-level retryable reads/writes and implement application-level exponential backoff for transient network or rate-limit (429) errors; make upserts idempotent using $setOnInsert where appropriate. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Compound index for aggregation | Design a compound index following the ESR rule (Equality → Sort → Range) to support aggregation summaries (e.g., { product_id: 1, sentiment_label: 1 }). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Multikey tags index | Index array fields (tags) as multikey indexes for tag queries and add a descending index on created_at to accelerate queries for recent documents. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Bulk/batched operations | Use bulk/batched operations for large imports or enrichment pipelines to reduce round trips and manage RU consumption. | [Manage a document in Azure Cosmos DB for MongoDB using JavaScript](https://learn.microsoft.com/azure/cosmos-db/mongodb/how-to-javascript-manage-documents#update-a-document) |
| Aggregation explain() | Implement the aggregation summary with an aggregation pipeline using $group by product_id and sentiment_label and run explain() on the aggregation to verify the query plan and index usage. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Idempotent upserts | Make reprocessing idempotent by using a stable _id and upsert semantics; use $setOnInsert for fields that must remain only on first insert and $set for subsequent updates. | [$setOnInsert](https://learn.microsoft.com/documentdb/query/operators/field-update/$setoninsert#examples) |
| Full-text search via $search | Prefer DocumentDB's built-in full-text search and create search indexes with createSearchIndexes and query via the $search aggregation stage. | [documentdb-full-text-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md) |
| Vector index dimensions | Create vector indexes with matching embedding 'dimensions' and 'similarity' (mismatches cause silently incorrect results), and rebuild indexes if you change the embedding model or similarity metric. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Read the cluster connection URI from an environment variable (e.g., DOCUMENTDB_URI) at runtime and never commit credentials; ship a .env.example or config template with placeholders instead of real secrets. | authentication and secrets | No .env.example or code consuming DOCUMENTDB_URI present in repository; events.jsonl shows documentdb-local-deployment skill was loaded recommending this practice. | Add .env.example and read DOCUMENTDB_URI and OPENAI_API_KEY from environment (pydantic BaseSettings). | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| For new Python async code on Azure DocumentDB prefer PyMongo's AsyncMongoClient rather than Motor; Motor is deprecated and PyMongo's async API is the supported path. | connection handling | The builder recorded the decision to use Beanie + Motor (decision D004 in decisions.jsonl). The documentdb-connection/Quickstart guidance (events.jsonl) recommends PyMongo's AsyncMongoClient for Beanie 2. No code created to reconcile choice. | Either pin Beanie to a Motor-compatible release or switch the sample to use PyMongo AsyncMongoClient per the skill's quickstart. Update requirements.txt accordingly. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md)<br>Quickstart: Connect Beanie to Azure DocumentDB |
| Design a compound index following the ESR rule (Equality → Sort → Range) to support aggregation summaries (e.g., { product_id: 1, sentiment_label: 1 }). | indexing | Builder planned compact indexes (product_id, tags multikey, sentiment_bucket) but did not create them on the cluster; builder_report lists index creation as 'not run' and attempts to log the index decision encountered a logging/parsing error (events.jsonl). | Add idempotent index-creation steps to the seed script or a migration script (createIndex on the collection with the compound order aligned to the aggregation pipeline). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Index array fields (tags) as multikey indexes for tag queries and add a descending index on created_at to accelerate queries for recent documents. | indexing | No index-creation code present; the builder planned a multikey index on tags but did not execute index creation. | Create a multikey index on tags and consider adding created_at: -1 if recent queries are frequent; include these createIndex calls in seed/migration script. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use bulk/batched operations for large imports or enrichment pipelines to reduce round trips and manage RU consumption. | provisioning and performance | No pipeline code present; builder_report planned upserts but did not implement batching. The learn.microsoft.com guidance was discovered in the run. | Implement batched writes (bulkWrite or grouped update_many/upsert calls) and tune batch size for the sample dataset; document rationale. | [Manage a document in Azure Cosmos DB for MongoDB using JavaScript](https://learn.microsoft.com/azure/cosmos-db/mongodb/how-to-javascript-manage-documents#update-a-document) |
| Make reprocessing idempotent by using a stable _id and upsert semantics; use $setOnInsert for fields that must remain only on first insert and $set for subsequent updates. | data integrity | No upsert code present and seed pipeline was not run. Builder_report mentions intention to use upsert but did not implement; $setOnInsert guidance was discovered. | Implement upserts with a stable external review id as _id and use $setOnInsert for first-insert-only fields; include tests validating idempotency. | [$setOnInsert](https://learn.microsoft.com/documentdb/query/operators/field-update/$setoninsert#examples) |
| Audit trail — record index-shape decisions | audit trail | The builder attempted to log the index decision (events.jsonl shows multiple log_decision attempts that failed with argument validation errors). The intended index plan (product_id, tags multikey, sentiment_bucket) appears in builder_report open_issues but the recorded decision for index choice failed validation. | Ensure log_decision calls use an allowed reason_source and succeed; add an agent-kit rule that requires index decisions to be recorded with a permitted reason_source value. | checklist only (no public address recorded) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Create and use a dedicated least-privilege database user for applications (or prefer Microsoft Entra ID / managed identity + RBAC). | authentication and secrets | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Always use TLS for connections to Azure DocumentDB (tls=true) and do not disable certificate validation in production; prefer SCRAM-SHA-256 for authentication. | security | - | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Enable driver-level retryable reads/writes and implement application-level exponential backoff for transient network or rate-limit (429) errors; make upserts idempotent using $setOnInsert where appropriate. | retries | - | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Limit concurrency to external APIs (OpenAI) and the database (by batching DB writes) so the pipeline is resilient to rate limits and doesn't overwhelm the DB. | openai integration | Searched for Azure DocumentDB OpenAI concurrency semaphore and pipeline OpenAI rate limit patterns; found no authoritative public guidance specific to DocumentDB. | prior_knowledge_only (no public address recorded) |
| Implement the aggregation summary with an aggregation pipeline using $group by product_id and sentiment_label and run explain() on the aggregation to verify the query plan and index usage. | queries | - | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| When using an ODM (Beanie/Pydantic), declare explicit Pydantic field types for embeddings and scores and create indexes at model/migration time rather than relying on implicit typing. | beanie_async | Searched for 'Azure DocumentDB sample guidance about Beanie ODM field annotations'; no useful Microsoft Learn page was found. | prior_knowledge_only (no public address recorded) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Prefer DocumentDB's built-in full-text search and create search indexes with createSearchIndexes and query via the $search aggregation stage. | full-text search | The sample focuses on sentiment and tags extraction and the builder explicitly chose not to create a $search index; no $search code exists. | [documentdb-full-text-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/full-text-search/SKILL.md) |
| Create vector indexes with matching embedding 'dimensions' and 'similarity' (mismatches cause silently incorrect results), and rebuild indexes if you change the embedding model or similarity metric. | vector search | Builder decided not to include vector indexes in this sample; no vector creation code present. | [documentdb-vector-search](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/vector-search/SKILL.md) |

### Reference requirements

0 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The pipeline is written in Python with async/await and uses the Beanie ODM to read the raw product review documents from Azure DocumentDB (e.g. a Beanie `Document` model for reviews queried with an awaited `find`). | not_met | builder_error | No application files or Beanie models present in the repository (list_files shows only planning docs; builder_report and events.jsonl record plans but no created files). | Add package sample_retail_07 with run_pipeline.py implementing an async Beanie Document model (e.g., class RawReview(Document): ...) and an awaited find (await RawReview.find(...)). |
| For each review, the pipeline calls OpenAI to classify the review's sentiment and to extract its key themes. | not_met | builder_error | No code calling OpenAI is present in the workspace; decisions and builder_report show the call was planned but not implemented. | Implement the async OpenAI call in the pipeline (await the async client for each review) and add unit tests that mock OpenAI responses. |
| The OpenAI classification call is made asynchronously inside the pipeline (e.g. the async OpenAI client awaited per review). | not_met | builder_error | No runtime code; planned design recorded in decisions but not implemented. | Use OpenAI's async client or an asyncio wrapper and await calls in the pipeline (document in README and add a minimal integration example). |
| Each review document is enriched with a sentiment score field and a tags field derived from the OpenAI result (the tags holding the extracted themes). | not_met | builder_error | No Beanie model or schema files present; builder_report mentions planned fields but did not write files. | Update the Beanie model(s) to include sentiment_score: float and tags: List[str] and set them from OpenAI response before save/upsert. |
| The enriched document is upserted back into Azure DocumentDB through Beanie (e.g. an awaited `save`/`replace`, or an upsert on the underlying collection), so an existing review is updated in place. | not_met | builder_error | No persisted-upsert code or scripts in repository; seed/index creation and upsert runs were not executed per build report. | Implement upsert logic with Beanie (await review.replace()/save() or underlying collection.update_one(..., upsert=True)) and include an idempotency pattern (stable _id or $setOnInsert). |
| A summary aggregation query runs against Azure DocumentDB (via Beanie's aggregate or the underlying collection) and groups the enriched reviews by product and by sentiment (e.g. a `$group` on a compound key returning a count per group). | not_met | builder_error | No aggregation script or runnable code in repository; builder_report planned a summary script but did not create or run it. | Add a summary script (e.g., sample_retail_07/summary.py) that runs an aggregation pipeline grouping by { product_id, sentiment_bucket } and prints counts; include an explain() call for verification. |
| The connection string and model credentials come from environment variables; none appear in the repository. | not_met | skill_guidance_not_followed | No .env.example or configuration files present; no code to read DOCUMENTDB_URI or OPENAI_API_KEY in the repo. | Create .env.example and code that reads DOCUMENTDB_URI and OPENAI_API_KEY (via pydantic BaseSettings or os.environ), and ensure no real secrets are committed. |
| A `.env.example` lists every setting with placeholder values. | not_met | skill_guidance_not_followed | No .env.example file present in the project root (list_files shows none). | Add .env.example listing DOCUMENTDB_URI, OPENAI_API_KEY, and any other settings used, with placeholder values and comments. |
| One database client is created and reused across requests. | not_met | builder_error | No client initialization module or code present. The driver-best-practices skill was loaded but no code was created to follow it. | Add a single client module (e.g., sample_retail_07/db.py) that creates and exports one Async client instance reused across modules (per documentdb-driver guidance). |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | not_met | builder_error | No scripts/seed_sample_data.py or index-creation scripts in repo; build report lists 'not run' for seeding and index creation. | Add scripts/seed_sample_data.py that upserts documents by stable _id and includes idempotent index-creation (create_index with exist checks or idempotent createSearchIndexes calls). |
| Dependencies are pinned in `requirements.txt`. | not_met | prompt_silent | No requirements.txt found in the workspace. | Add requirements.txt with pinned versions (example pins: beanie==2.x, motor/pymongo pinned to the chosen driver version, openai pinned) and document them in README. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No tests present; no test config or mocking harness (and the local Gateway Docker image is available but not used). | Add tests using pytest with mocks for the OpenAI client and a local gateway (or use mongomock/pytest-asyncio) so unit tests run offline; include CI instructions. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep/Terraform/ARM) files were added. The run context supplied an existing cluster and the builder did not author infra as code. | Add a minimal Bicep or Terraform sample template that creates Microsoft.DocumentDB/mongoClusters (or documents az documentdb mongocluster create). |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | not_met | prompt_silent | No README.md is present in the repository. | Add README.md with sections: Overview, Prerequisites (DOCUMENTDB_URI, OPENAI_API_KEY), Setup (virtualenv, pip install -r requirements.txt), Seed, Run pipeline, Run summary, Cleanup, Troubleshooting. |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | not_met | prompt_silent | No files (README or code) present to check naming; builder_report notes awareness of naming confusion but did not produce artifacts. | Ensure README, docs and code use the product name 'Azure DocumentDB' and include a short sentence clarifying how it differs from Cosmos RU-based Mongo API. |
| The vector index dimensions match the embedding model's output. | not_checkable | - | The builder intentionally decided not to create vector indexes (open_issues and decisions note 'no embeddings'); there is no vector index creation code to inspect. | If embeddings are added later, create the vector index with 'dimensions' equal to the embedding model's output and include a note in the README to rebuild indexes if the model changes. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector index creation or README guidance present; builder chose not to include vectors. | If vector search is added, include a short index-choices section in the README with recommended DiskANN/HNSW settings for sample size and guidance for scaling. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | - | No HTTP server or /search endpoint implemented in the repo. The starter prompt did not require an HTTP API. | If adding an HTTP search endpoint, implement input validation that returns 400 for empty queries and meaningful 5xx/4xx messages when embedding/OpenAI calls fail. |
| Search results include the similarity score. | not_checkable | - | No search or embedding code present. | When returning vector search results, include the similarity score in the response payload and add unit tests that verify score presence. |

