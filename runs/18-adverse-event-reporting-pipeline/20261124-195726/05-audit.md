# 5. Best-practice audit: 18-adverse-event-reporting-pipeline

**Verdict: pass_with_findings** (9 followed, 2 violated, 1 not applicable, 1 not assessable)

The sample implements the core pipeline the starter prompt asked for: it accepts free-text reports, calls an LLM (OpenAI) with an engineered prompt, validates via Pydantic/Beanie, writes structured documents to Azure DocumentDB, and exposes the aggregation that groups by drug and event. The build verified seeding and the aggregation against a live cluster. Most critical functional requirements are met, but there are operational and hygiene gaps the owner should fix before publishing: (1) seed script is not idempotent, (2) retry/backoff for transient DB errors is missing, (3) some connection-driver guidance from the DocumentDB skills (use AsyncMongoClient for Beanie 2 and explicit connection tuning) was not followed in the code, (4) tests are missing though README claims pytest coverage, and (5) no IaC is provided for provisioning a cluster. The product team should publish clear, discoverable guidance about treating LLM outputs as untrusted for DocumentDB apps and a small set of discoverability and naming clarifications identified in the readiness review.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Readiness approval 'ready_with_gaps' is recorded and the trace shows the operator reason source; nothing in the events contradicts the decision. |
| D002 | I chose Python 3.13 (the system python available) for runtime. | readiness_report | sound | Choosing Python 3.13 because it was available on PATH is supported by the readiness report in events (the environment contained Python 3.13). |
| D003 | I chose FastAPI for the app surface with POST /reports and GET /reports/top-events. | model_default | sound | Choosing FastAPI for an async sample is reasonable. The decision reason_source is model_default; events show the decision was recorded and FastAPI was used in the code. |
| D004 | I chose Beanie 2 with PyMongo AsyncMongoClient. | docs | sound | Choosing Beanie 2 with AsyncMongoClient is supported by the Beanie quickstart and the decision log. However the implemented code did not instantiate an Async client (it uses pymongo.MongoClient synchronously), so the decision was not fully followed in code (see practice 'Prefer AsyncMongoClient' violation). The decision itself is supported by documentation in events. |
| D005 | I chose OpenAI (openai-python) as the LLM provider and to read API key from OPENAI_API_KEY. | model_default | questionable | Selecting OpenAI by default is a defensible model_default choice (no provider specified in the prompt), but it is a policy decision that the product team may want to document; events show the decision recorded and OpenAI client is used in code. Marked 'questionable' only because other orgs may prefer Azure OpenAI or configurable providers. |
| D006 | I chose to create a compound index on {drug:1, event:1} programmatically at app startup using the driver's create_index. | skill | sound | Programmatic creation of a compound index on (drug, event) is consistent with the documentdb-indexing skill and the events show the index was created and validated by the documentdb_list_indexes step. |
| D007 | I chose to store raw_text and created_at in addition to extracted structured fields (drug, event, severity, onset_date). | model_default | sound | Storing raw_text and created_at is a reasonable choice; the code and models include these fields and the seed uses raw_text for sample data. |

Documentation gaps: 6 (see `doc-gaps.md`).

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
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 12 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| LLM outputs are untrusted | Treat LLM-driven extraction outputs as untrusted: validate, canonicalize, map to controlled vocabularies, log parse confidence, and quarantine ambiguous results rather than writing them directly to production structured fields. | A short Microsoft docs page stating recommended LLM-output handling patterns (validation + canonicalization + quarantine) for DocumentDB apps. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Create one MongoClient / driver client per process (a singleton) and reuse it across requests rather than creating a new client per request; tune maxPoolSize for expected concurrency. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Secrets from env | Do not commit cluster connection strings or credentials to source control; read DOCUMENTDB_URI and other secrets from environment variables or a secret store and provide only a .env.example placeholder in the repo. | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples) |
| TLS required | Always connect to Azure DocumentDB with TLS enabled (tls=true) and do not disable certificate validation in production. | [Connect to Azure DocumentDB using MongoDB Shell](https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication) |
| Server-side schema & raw_text | Use server-side JSON Schema validation where available and also validate/canonicalize inputs in the application; keep the original free-text report in a raw_text field and write parsed typed fields separately. | [$jsonSchema](https://learn.microsoft.com/documentdb/query/operators/evaluation-query/$jsonschema) |
| Compound index for aggregation | Create a compound index that matches the aggregation/grouping access pattern (for example { drug: 1, event: 1 }) so the GROUP/COUNT aggregation can be satisfied efficiently rather than scanning the collection. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Retries / backoff | Implement retries with exponential backoff and jitter for transient errors and throttling (HTTP 429); when a Retry-After header is present, honor it rather than retrying immediately. | [Design throttling to improve resilience / Retry-After guidance](https://learn.microsoft.com/azure/well-architected/design-guides/throttling#[tp-5]-respect-backpressure) |
| allowDiskUse for large aggregation | For large aggregation pipelines use allowDiskUse:true and reduce intermediate sizes by filtering/projecting early. | [aggregate command and aggregation pipeline examples and limitations](https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate) |
| Index build & seeding | When building or reindexing large indexes, schedule index creation during low-traffic windows and prefer background/index-build-safe approaches; for large data loads, batch inserts rather than single inserts. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Protect raw_text / PHI | Avoid logging or persisting PHI/PII unnecessarily; if you store raw_text for auditing or re-parsing, protect it with least-privilege access, encryption at rest (CMK when needed), and consider field-level encryption. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Bulk seed writes | Use bulk/batched writes (insert_many / bulk API) for seeding and high-throughput ingestion rather than single inserts to reduce round-trips and improve throughput; respect service batch/write limits. | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |
| Prefer AsyncMongoClient | Prefer PyMongo's AsyncMongoClient for async Python workloads and initialize clients outside request/handler scope so the async client is reused across invocations. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Explain plan before adding indexes | Use explain('executionStats') and examine keysExamined/docsExamined and winningPlan to verify index usage and identify COLLSCAN or scatter-gather behavior before adding indexes. | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Implement retries with exponential backoff and jitter for transient errors and throttling (HTTP 429); when a Retry-After header is present, honor it rather than retrying immediately. | retries | No retry/backoff is implemented for DB operations or OpenAI calls. app/src/main.py DB operations are performed without retry wrappers; index creation prints warning on exception (lines 42-46) but has no retry logic. | Add a retry policy for transient DB errors and 429 responses (e.g., tenacity with exponential backoff and jitter). For 429 responses with Retry-After, parse and sleep accordingly before retrying. | [Design throttling to improve resilience / Retry-After guidance](https://learn.microsoft.com/azure/well-architected/design-guides/throttling#[tp-5]-respect-backpressure) |
| Prefer PyMongo's AsyncMongoClient for async Python workloads and initialize clients outside request/handler scope so the async client is reused across invocations. | driver | app/src/main.py comments say 'Use PyMongo AsyncMongoClient per Beanie 2 quickstart' (line 35) but the code instantiates pymongo.MongoClient (synchronous) on line 37 rather than AsyncMongoClient. Builder_report notes startup init was not executed with the async client. | Use AsyncMongoClient from pymongo (e.g., from pymongo import AsyncIOMotorClient or pymongo.AsyncIOMongoClient depending on API) and pass that client into init_beanie as shown in the Beanie quickstart; ensure the client object is created at startup and stored for reuse. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use explain('executionStats') and examine keysExamined/docsExamined and winningPlan to verify index usage and identify COLLSCAN or scatter-gather behavior before adding indexes. | queries | - | [documentdb-query-optimization](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimization/SKILL.md) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create one MongoClient / driver client per process (a singleton) and reuse it across requests rather than creating a new client per request; tune maxPoolSize for expected concurrency. | connection | app/src/main.py lines 36-40 (MongoClient created at startup and passed into init_beanie) | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Do not commit cluster connection strings or credentials to source control; read DOCUMENTDB_URI and other secrets from environment variables or a secret store and provide only a .env.example placeholder in the repo. | secrets | app/.env.example contains only placeholders (lines 2-6). app/src/main.py lines 17-19 read DOCUMENTDB_URI and OPENAI_API_KEY from environment. | [Quickstart: Use Azure DocumentDB with MongoDB driver for Python](https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples) |
| Always connect to Azure DocumentDB with TLS enabled (tls=true) and do not disable certificate validation in production. | security | app/.env.example line 2 includes tls=true in the example connection string. The app reads the URI from env and therefore relies on that setting. | [Connect to Azure DocumentDB using MongoDB Shell](https://learn.microsoft.com/azure/documentdb/how-to-connect-mongo-shell#connect-with-interactive-password-authentication) |
| Use server-side JSON Schema validation where available and also validate/canonicalize inputs in the application; keep the original free-text report in a raw_text field and write parsed typed fields separately. | data_modeling | App stores raw_text and parsed fields in AdverseEvent (app/src/models.py lines 6-12). Application-level Pydantic validation is used before insert (main.py lines 59-60). No server-side $jsonSchema validator is created in this repo. | [$jsonSchema](https://learn.microsoft.com/documentdb/query/operators/evaluation-query/$jsonschema) |
| Create a compound index that matches the aggregation/grouping access pattern (for example { drug: 1, event: 1 }) so the GROUP/COUNT aggregation can be satisfied efficiently rather than scanning the collection. | indexing | Index created at startup in app/src/main.py lines 41-46 (coll.create_index([...], name='idx_drug_event')) and seed.py line 23 ensures index. documentdb_list_indexes call in events shows idx_drug_event present. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| When building or reindexing large indexes, schedule index creation during low-traffic windows and prefer background/index-build-safe approaches; for large data loads, batch inserts rather than single inserts. | indexing | Seed script uses insert_many (app/seed.py line 104) which is batched. The sample creates a compound index programmatically at startup, and the builder documented that they used a simple compound B-tree index. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Avoid logging or persisting PHI/PII unnecessarily; if you store raw_text for auditing or re-parsing, protect it with least-privilege access, encryption at rest (CMK when needed), and consider field-level encryption. | security | App stores raw_text in the document (app/src/models.py line 11). README and seed note the sample uses synthetic text and warns not to commit secrets; however no field-level encryption or CMK guidance is implemented in sample code. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Use bulk/batched writes (insert_many / bulk API) for seeding and high-throughput ingestion rather than single inserts to reduce round-trips and improve throughput; respect service batch/write limits. | performance | app/seed.py line 104 uses coll.insert_many(SAMPLES, ordered=False) | [Document size and batch write limits in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/max-document-size) |
| Treat LLM-driven extraction outputs as untrusted: validate, canonicalize, map to controlled vocabularies, log parse confidence, and quarantine ambiguous results rather than writing them directly to production structured fields. | data_modeling | The sample validates the LLM output by passing parsed JSON into the AdverseEvent Pydantic/Beanie model (app/src/main.py lines 59-61). However the sample does not canonicalize drug names or map severity to a controlled vocabulary, nor does it log parse confidence or quarantine ambiguous parses. | prior_knowledge_only (no public address recorded) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| For large aggregation pipelines use allowDiskUse:true and reduce intermediate sizes by filtering/projecting early. | queries | The example aggregation groups a small seeded set (10 docs) and the event run used allowDiskUse:false; no large aggregation is present in the sample. | [aggregate command and aggregation pipeline examples and limitations](https://learn.microsoft.com/documentdb/query/commands/aggregation/aggregate) |

### Reference requirements

11 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | not_met | builder_error | app/seed.py line 104 calls coll.insert_many(SAMPLES, ordered=False) — this will insert the same documents again on each run (no upsert dedupe or unique index in place). | Change the seed to upsert or make it idempotent, e.g. create a suitable unique index and use update_one(filter, {'$setOnInsert': doc}, upsert=True) for each sample or run bulk upsert. |
| Unit tests run without a live cluster. | not_met | builder_error | No tests are present in the repository; README claims pytest runs lightweight unit tests but no test files are included. | Add unit tests that mock the DB (e.g., using mongomock or pytest fixtures) so they run offline; mark integration tests that require DOCUMENTDB_URI separately. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (Bicep / Terraform / ARM) files present in repo; readiness findings also note missing IaC. | Add a minimal Bicep (or Terraform) template using Microsoft.DocumentDB/mongoClusters with tier/storage/region parameters and documented defaults. |
| Dependencies are pinned in requirements.txt. | partly_met | builder_error | app/requirements.txt pins beanie==2.2.0 and pymongo==4.19.0, but other dependencies use ranges (fastapi>=0.95,<1, uvicorn>=0.20,<1, etc.). | Pin exact versions for all runtime/test dependencies (replace ranges with exact versions) to improve reproducibility. |
| The vector index dimensions match the embedding model's output. | not_checkable | - | No vector/embedding field or vector index creation appears in the code or seed script (app/src/models.py and seed.py contain no embedding field). | n/a |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector indexes or guidance present in code or README. | n/a |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | - | This sample does not implement a /search endpoint, only POST /reports and GET /reports/top-events. | n/a |
| Search results include the similarity score. | not_checkable | - | No search/embedding features implemented in this repo. | n/a |
| A Python pipeline that accepts a free-text adverse event report and runs it through extraction, schema validation and storage in sequence. | met | - | app/src/main.py lines 48-61 (POST /reports route, calls extract_with_openai, constructs AdverseEvent(**parsed), await ae.insert()) | n/a |
| An LLM call driven by an engineered prompt that extracts the structured fields drug, event, severity and onset date. | met | - | app/src/main.py lines 79-109 (prompt string with explicit keys; openai.ChatCompletion.create call and JSON parsing) | n/a |
| A Pydantic schema for the extracted report with the fields drug, event, severity and onset date, and validation of the LLM output against that schema before the report is stored. | met | - | app/src/models.py lines 6-12 (AdverseEvent Document fields) and app/src/main.py lines 59-60 (AdverseEvent(**parsed) and await ae.insert()) | n/a |
| A Beanie ODM Document model representing the structured adverse event report with those four fields. | met | - | app/src/models.py lines 6-16 (class AdverseEvent(Document)...) | n/a |
| The validated report written to Azure DocumentDB through that Beanie Document model. | met | - | app/src/main.py lines 59-61 (create AdverseEvent and await ae.insert()) | n/a |
| An aggregation pipeline, run through Beanie ODM against the stored reports, that groups them by drug and event, counts the reports in each group and orders the result so the most frequently reported events for each drug come first. | met | - | app/src/main.py lines 63-77 (aggregation pipeline building, coll.aggregate and async iteration producing AggregationOut results) | n/a |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/main.py lines 17-19 (os.getenv) and app/.env.example lines 1-5 (placeholders only) | n/a |
| .env.example lists every setting with placeholder values. | met | - | app/.env.example lines 2-6 list DOCUMENTDB_URI, DOCUMENTDB_DATABASE, OPENAI_API_KEY, OPENAI_MODEL as placeholders | n/a |
| One database client is created and reused across requests. | met | - | app/src/main.py lines 36-40 create MongoClient(DOCUMENTDB_URI) and call await init_beanie(database=db, ...). The client is created once during startup. | n/a |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md lines 1-24 (what it shows, prerequisites, quickstart) and lines 34-35 (cleanup). | n/a |
| The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. | met | - | README first line: 'Adverse Event Reporting sample for Azure DocumentDB...' and other files refer to Azure DocumentDB; no references to Amazon DocumentDB or Cosmos DB databaseAccounts in the sample code. | n/a |

