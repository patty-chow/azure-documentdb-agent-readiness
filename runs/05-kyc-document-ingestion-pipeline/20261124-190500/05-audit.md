# 5. Best-practice audit: 05-kyc-document-ingestion-pipeline

**Verdict: pass_with_findings** (7 followed, 2 violated, 1 not assessable)

The sample implements the core async Beanie+FastAPI pipeline, sends uploaded documents to OpenAI, validates with Pydantic, models customers with Beanie, and upserts on a government_id key. Secrets are read from the environment and a .env.example is provided. Key gaps: (1) connection timeout/retry parameters recommended by the documentdb-connection guidance were not applied, (2) index creation via the MCP tooling failed because management/write tools are opt-in in this environment, (3) the seed script is not idempotent in all cases and index-creation/verification was not completed programmatically, and (4) a few gallery checklist items (search endpoints, unit tests, infra-as-code) are missing. The build choices are mostly reasonable and recorded; one builder choice (Beanie vs Beanie2 / Motor vs AsyncMongoClient) was made in code but the decision log attempt failed and is missing a final recorded decision. See requirement-by-requirement results, practice checks, decision reviews and documentation gaps below.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approving the build as 'ready_with_gaps' is a reasonable operator-level decision. The log entry exists (decisions.jsonl) and fits the recorded readiness state. |
| D002 | I chose Python 3.13 as the runtime for the sample. | readiness_report | sound | Choosing Python 3.13 is supported by the readiness report and build logs (pip installs ran). events.jsonl includes the readiness evidence quoted. |
| D003 | I chose to read all secrets (DOCUMENTDB_URI, OPENAI_API_KEY) from environment variables at runtime. | prompt | sound | Reading secrets from environment matches the prompt instruction and the code: db.py and openai_client.py read environment variables. Evidence: prompt and code lines referenced. |
| D004 | I chose gpt-4o-mini as the OpenAI model for structured extraction in this sample. | model_default | questionable | Choosing gpt-4o-mini is a sensible default for an extraction sample. However the decision's reason_source is 'model_default' (decisions.jsonl) rather than a documented product recommendation; per the audit rules this should be documented explicitly in sample README or product guidance so other builders don't pick different models unexpectedly. |
| D005 | I chose to upsert records by government_id (stable unique identifier) and create a unique index on government_id. | model_default | sound | Upserting by government_id and creating a unique index is implemented in code (models.py uses Indexed(..., unique=True) and upsert uses replace_one with upsert=True). The decision matches implementation. |
| D006 | I chose to use the existing DocumentDB cluster and not provision any new Azure resources. | readiness_report | sound | Using the existing cluster and not provisioning new resources follows the run policy and readiness report. The decision is consistent with build actions. |
| D007 | I chose motor==3.5.3 to match available PyPI releases compatible with Beanie in this environment. | tool_result | sound | Selecting motor==3.5.3 because a later motor release was unavailable on PyPI in this environment is supported by the pip install traces in events.jsonl; the change is recorded in requirements.txt. |
| D008 | I chose openai==1.0.0 to match an older stable client API surface compatible with synchronous ChatCompletion.create used in the sample's thread-executor call. | tool_result | sound | Selecting openai==1.0.0 based on available PyPI versions is supported by the pip traces. Implementation uses the older ChatCompletion.create surface invoked in a thread, matching the selected client. |
| D009 | I chose to create and verify the unique index on government_id using the documentdb MCP server (create_index and list_indexes) for reliable programmatic verification. | readiness_report | questionable | Choosing to create/verify the unique index via the documentdb MCP server was reasonable. However the attempt to create the index and insert a seed document failed because management/write MCP tools are disabled by default in this environment (events.jsonl shows ToolExecutionException for documentdb_create_index and documentdb_insert_documents). The plan was sound but the verification step did not succeed; the decision should have included an environment check or fallback plan (e.g., create indexes on app init) and the run should log the failed MCP calls (which it does). |

Documentation gaps: 7 (see `doc-gaps.md`).

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
| On the checklist, found only when searched for by name | 1 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 8 | Public and discoverable. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| Driver version pinning | Driver version is pinned and is one the service supports.<br>**Searches:** learn.microsoft.com quickstart Beanie tested driver versions | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie#prerequisites) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Beanie init patterns | When public guidance is absent for framework-specific initialization (e.g., Beanie-specific init rules), follow framework docs and treat service-level guidance as application policy. | A short authoritative note in product docs about recommended async client patterns for Beanie (Motor vs AsyncMongoClient) would remove ambiguity. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | When using drivers, prefer a single shared MongoClient instance per process (connection-pool singleton) instead of creating a client per request. | [Driver Manager Connection Pooling](https://learn.microsoft.com/odbc/reference/develop-app/driver-manager-connection-pooling?view=sql-server-ver17)<br>[documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| TLS & timeouts | Require TLS for all client connections to Azure DocumentDB (connection strings include tls=true) and use certificate validation in production; configure sensible driver timeouts so code fails fast. | [Secure your Azure DocumentDB cluster](https://learn.microsoft.com/azure/documentdb/security#transport-security)<br>[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Secrets in repo | Read the Azure DocumentDB connection string from a runtime secret store (environment variable or secret manager) and do not commit the connection string to source control. | [Migrate from Amazon DocumentDB to Azure DocumentDB (with MongoDB compatibility)](https://learn.microsoft.com/azure/documentdb/migrate-amazon-documentdb#update-your-application) |
| Unique upsert index | Create a unique index for the stable upsert key used by the pipeline (for example government_id) to prevent duplicates and make upserts deterministic. | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#index-types) |
| Avoid large binaries | Avoid storing large binary files or multi-megabyte payloads in DocumentDB documents; keep only metadata and structured fields in the database and store raw files in blob storage or other object storage. | [Azure DocumentDB at a glance](https://learn.microsoft.com/azure/documentdb/at-a-glance#security-and-governance) |
| Retries & backoff | Handle transient faults with bounded retries that use exponential backoff (and jitter) and only retry operations that are safe to replay. | [Recommendations for handling transient faults](https://learn.microsoft.com/azure/well-architected/design-guides/handle-transient-faults#implementing-retries) |
| Use MCP for verification | Use the service-provided tooling (MCP server) to inspect live collections, index definitions and query plans as part of verification and troubleshooting. | [Migrate MongoDB to Azure DocumentDB online by using Azure DocumentDB migration extension](https://learn.microsoft.com/azure/documentdb/how-to-migrate-vs-code-extension#perform-the-migration) |
| LLM output validation & raw preservation | When using OpenAI or other LLMs in a pipeline, validate outputs server-side and persist only validated structured fields while preserving raw responses in a non-indexed raw field for auditing. | [Full-text search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#how-azure-documentdb-full-text-search-works) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Require TLS for all client connections to Azure DocumentDB (connection strings include tls=true) and use certificate validation in production; configure sensible driver timeouts so code fails fast. | connection | app/.env.example includes tls=true (app/.env.example line 2) and db.py comments note TLS is required (app/src/app/db.py line 17) but no driver timeout parameters (serverSelectionTimeoutMS/socketTimeoutMS) are set on AsyncIOMotorClient (app/src/app/db.py line 19). | Set sensible timeouts when creating the client, e.g. AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000, socketTimeoutMS=60000) or parse and append serverSelectionTimeoutMS to the URI. | [Secure your Azure DocumentDB cluster](https://learn.microsoft.com/azure/documentdb/security#transport-security)<br>[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Handle transient faults with bounded retries that use exponential backoff (and jitter) and only retry operations that are safe to replay. | retries | No retry/backoff logic around the OpenAI call or DB operations. openai_client.extract_entities will raise and be translated to HTTP 500 (openai_client.py lines 24-39 and main.py lines 25-28). DB upsert operations are executed without explicit retry/backoff (models.py upsert uses replace_one directly). | Wrap non-idempotent operations in retries with exponential backoff and jitter where safe, or rely on driver retry settings for idempotent operations; for OpenAI calls use bounded retries and circuit-breakers for transient network errors. | [Recommendations for handling transient faults](https://learn.microsoft.com/azure/well-architected/design-guides/handle-transient-faults#implementing-retries) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use the service-provided tooling (MCP server) to inspect live collections, index definitions and query plans as part of verification and troubleshooting. | operations | - | [Migrate MongoDB to Azure DocumentDB online by using Azure DocumentDB migration extension](https://learn.microsoft.com/azure/documentdb/how-to-migrate-vs-code-extension#perform-the-migration) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| When using drivers, prefer a single shared MongoClient instance per process (connection-pool singleton) instead of creating a client per request. | driver_usage | app/src/app/db.py lines 6, 14-21: module-level _client is assigned AsyncIOMotorClient(uri) in init_db() and reused. | [Driver Manager Connection Pooling](https://learn.microsoft.com/odbc/reference/develop-app/driver-manager-connection-pooling?view=sql-server-ver17)<br>[documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Driver version is pinned and is one the service supports. | connection | app/requirements.txt pins beanie==1.16.4 and motor==3.5.3 (app/requirements.txt). Quickstarts list tested combinations (Beanie 2 + PyMongo AsyncMongoClient) but the sample pins Motor+Beanie 1; the code runs with the pinned packages. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie#prerequisites) |
| Read the Azure DocumentDB connection string from a runtime secret store (environment variable or secret manager) and do not commit the connection string to source control. | auth_and_secrets | app/src/app/db.py reads DOCUMENTDB_URI from environment (lines 8-12) and .env.example uses placeholders (app/.env.example lines 1-4); no real secrets are in the repo. | [Migrate from Amazon DocumentDB to Azure DocumentDB (with MongoDB compatibility)](https://learn.microsoft.com/azure/documentdb/migrate-amazon-documentdb#update-your-application) |
| Create a unique index for the stable upsert key used by the pipeline (for example government_id) to prevent duplicates and make upserts deterministic. | indexing | app/src/app/models.py declares government_id: Optional[Indexed(str, unique=True)] (line 17). The upsert method uses replace_one with upsert=True (lines 33-39). | [MongoDB Query Language (MQL) compatibility in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/compatibility-query-language#index-types) |
| Avoid storing large binary files or multi-megabyte payloads in DocumentDB documents; keep only metadata and structured fields in the database and store raw files in blob storage or other object storage. | data_modeling | The app accepts file uploads but decodes text and stores structured fields and raw extraction; it does not persist the uploaded binary file into the DB (main.py lines 16-23, 31-37). README warns that only text uploads are supported and suggests adding OCR and storing raw files in blob storage (app/README.md lines 31-35). | [Azure DocumentDB at a glance](https://learn.microsoft.com/azure/documentdb/at-a-glance#security-and-governance) |
| When public guidance is absent for framework-specific initialization (e.g., Beanie-specific init rules), follow framework docs and treat service-level guidance as application policy. | app_orm | The app uses init_beanie(database=_client.get_default_database(), document_models=[Customer]) in db.py line 21; this matches common Beanie init usage, but there is known public guidance recommending Beanie 2 + AsyncMongoClient in some quickstarts. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python#code-examples) |
| When using OpenAI or other LLMs in a pipeline, validate outputs server-side and persist only validated structured fields while preserving raw responses in a non-indexed raw field for auditing. | data_validation | openai_client.extract_entities parses JSON and returns a 'raw' fallback when parsing fails (openai_client.py lines 41-50). Extraction is validated by Pydantic ExtractionSchema(**extracted) before storage (main.py line 29) and the Customer model stores extracted.raw (models.py lines 6-11, 18). | [Full-text search in Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/full-text-search-overview#how-azure-documentdb-full-text-search-works) |

### Reference requirements

11 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | There is no /search endpoint in app/src/app/main.py. | Add a /search endpoint that validates input, returns 400 for empty queries, wraps embedding/LLM calls with try/except, and returns clear error messages when embedding fails. |
| Search results include the similarity score. | not_met | prompt_silent | No search implementation present. | If you add semantic search, include similarity scores in the HTTP response and document the score semantics in README. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No test files present in the repository; pytest is listed in requirements but no unit tests or mocking harness provided. | Add unit tests with mocked OpenAI and mocked database clients (e.g., using pytest + pytest-asyncio + respx/httpx mocking or monkeypatching Beanie/Motor) so tests run offline. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No Bicep/Terraform/ARM templates or infra-as-code files found in the repository. | Add a minimal Bicep/ARM/Terraform snippet (Microsoft.DocumentDB/mongoClusters) or a link to the documentdb-azure-deployment skill example, if you want to provide infra as code. |
| A .env.example lists every setting with placeholder values. | partly_met | builder_error | .env.example lists DOCUMENTDB_URI, OPENAI_API_KEY and OPENAI_MODEL (app/.env.example lines 1-4). README instructs to copy .env.example (app/README.md lines 21-25). | Add any runtime variables the app relies on (for example DATABASE_NAME or MONGODB_DATABASE / DB_NAME if you want explicit database selection) to .env.example and document their use in README; e.g., add DB_NAME=sample_fintech_05. |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | partly_met | builder_error | scripts/seed.py exists and uploads three sample documents to the /upload endpoint (scripts/seed.py lines 8-12, 14-22). The app declares a unique index via Beanie's model (models.py line 17) but MCP index creation failed in this run (events.jsonl documentdb_create_index exception). The seed script uses POST to /upload (which upserts on government_id only when provided), but two of the three seed samples have no government_id so repeated runs would produce duplicates. | Make the seed script idempotent by providing government_id for all seed samples or change the seed to call an upsert endpoint directly with deterministic keys; also add a script to create/verify indexes idempotently (createIndex with if-not-exists pattern or use Beanie init to create indexes on startup and document how to run it). |
| The vector index dimensions match the embedding model's output. | not_checkable | could_not_determine | This sample does not compute or store embeddings and has no vector-index creation code. | If you add embeddings, document the embedding model and set vector index dims to the model's output size in the index-creation script or README. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | could_not_determine | No vector index or embedding code present. | Only applicable if embeddings are added; provide index-creation helper with parameters and README guidance. |
| The pipeline accepts uploaded KYC documents as its input (e.g. a file upload or document bytes handed to an ingestion entry point). | met | - | app/src/app/main.py lines 16-23 (FastAPI /upload handler reading UploadFile and file.read()). | - |
| The pipeline is written in async Python, with the OpenAI calls and the Beanie ODM database operations awaited. | met | - | app/src/app/openai_client.py defines async extract_entities and app/src/app/main.py awaits extract_entities (line 26) and awaits cust.upsert() (line 40). | - |
| Each uploaded document is sent to OpenAI with a request for structured entity extraction covering name, DOB, address and ID numbers. | met | - | app/src/app/openai_client.py PROMPT_TEMPLATE (lines 12-22) requests name, dob, address, government_id and main.py calls extract_entities (line 26). | - |
| A Pydantic schema declares the extracted entities (name, DOB, address, ID numbers), and the OpenAI output is validated against that schema before it is stored. | met | - | app/src/app/schemas.py defines ExtractionSchema and main.py constructs ExtractionSchema(**extracted) on line 29 before mapping to Customer. | - |
| The customer record is modelled as a Beanie ODM Document, and a validated record is upserted into Azure DocumentDB through Beanie (updated when a matching customer already exists, inserted otherwise; matched on e.g. an ID number). | met | - | app/src/app/models.py defines class Customer(Document) with an upsert() method that calls replace_one({'government_id': self.government_id}, self, upsert=True) (lines 13-21, 33-39). main.py constructs Customer and calls await cust.upsert() (main.py lines 31-41). | - |
| A record whose extraction fails schema validation or lacks required entities is stored as incomplete and flagged for manual review (e.g. a review flag on the stored document). | met | - | app/src/app/models.py: Customer.status defaults to 'manual_review' (line 19) set_complete_if_valid toggles status to 'complete' only if all fields present (lines 26-31). For missing government_id, upsert inserts (lines 33-38) leaving status 'manual_review'. | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/app/db.py reads DOCUMENTDB_URI from environment (lines 8-12). app/src/app/openai_client.py reads OPENAI_API_KEY and OPENAI_MODEL from environment (lines 7-10). app/.env.example contains placeholders (app/.env.example lines 2-4). No real secrets are committed. | - |
| One database client is created and reused across requests. | met | - | app/src/app/db.py defines a module-level _client and init_db() sets _client = AsyncIOMotorClient(uri) (lines 6, 14-21); startup event calls init_db() (app/src/app/main.py lines 12-15). | - |
| Dependencies are pinned in requirements.txt. | met | - | app/requirements.txt pins fastapi==0.95.2, uvicorn[standard]==0.22.0, beanie==1.16.4, motor==3.5.3, pydantic==1.10.12, openai==1.0.0, pytest==7.4.2, httpx==0.24.1 (app/requirements.txt). | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md contains Overview, Prerequisites, Setup, Run instructions and Cleanup (app/README.md lines 3-39, 41-45). | - |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | README and code name the target service 'Azure DocumentDB' (app/README.md lines 5, 10). | - |

