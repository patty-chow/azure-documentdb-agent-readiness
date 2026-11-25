# 5. Best-practice audit: 09-clinical-notes-de-identification

**Verdict: pass_with_findings** (6 followed, 3 violated, 1 not assessable, 1 not applicable)

The sample implements the core de-identification pipeline the starter prompt requested: Beanie models (RawNote, DeidNote), a seed script, an idempotent dry-run de-id, an OpenAI-backed run mode (code present but not executed), index-creation script, pinned dependencies, and README/instructions. Verification ran the seed and dry-run paths and created DeidNote documents. Shortcomings are mostly engineering and documentation gaps the starter prompt did not ask for (vector/index guidance, explicit Entra ID guidance, retries/backoff, IaC), plus one deliberate driver choice (Beanie 1.x + Motor) that conflicts with Microsoft Learn guidance recommending Beanie 2 + AsyncMongoClient. None of the missing items made the sample unusable for the core scenario, but several are important for production safety or discoverability and should be fixed before publishing.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approving the build as 'ready_with_gaps' matches the readiness findings and is a reasonable human operator decision recorded in D001; events.jsonl contains log_decision for this. |
| D002 | I chose Python 3.13 for the sample's runtime. | readiness_report | sound | Choosing Python 3.13 is supported by the readiness report and the run environment; events.jsonl logs the decision and the environment evidence. |
| D003 | I chose Beanie 1.x with Motor (AsyncIOMotorClient). | model_default | questionable | The decision chose Beanie 1.x + Motor (reason_source=model_default). Microsoft Learn quickstart recommends Beanie 2 + PyMongo AsyncMongoClient for Azure DocumentDB. Choosing 1.x/Motor is defensible but contrasts official guidance; note discoverability gap and recommend aligning with the quickstart. |
| D004 | I chose to verify using the documentdb MCP server and the pipeline dry-run behavior to avoid calling OpenAI in CI. | readiness_report | sound | Using the MCP server and dry-run to avoid external OpenAI calls was reasonable based on the readiness report. Events show MCP write tools were disabled (tool execution failed), but the decision itself was justified by the environment guidance. |
| D005 | I chose to use the documentdb MCP server to insert seed documents for verification. | readiness_report | questionable | The builder attempted to use the MCP server to insert seed documents (reasonable given the readiness note), but the MCP write tool was disabled during execution (events.jsonl shows ToolExecutionException). The choice was defensible but did not succeed in practice. |
| D006 | I chose to retry documentdb_insert_documents once. | tool_result | sound | Retrying documentdb_insert_documents once is a reasonable operational response to transient failures; events show two attempts and both failed with a policy-related error, but the retry decision is sensible. |
| D007 | I chose to run seed.py to insert the synthetic notes using the sample code (Beanie + Motor). | tool_result | sound | Falling back to running seed.py (the project's own seed script) was the correct fallback; events.jsonl shows seed.py subsequently inserted the 5 synthetic notes. |
| D008 | I chose to handle missing default DB by selecting 'sample_healthcare_09' explicitly in init_db. | tool_result | sound | Handling a missing default DB by explicitly selecting 'sample_healthcare_09' is practical and the code was updated accordingly; events show the code overwrite and later successful seed execution. |
| D009 | I chose to use a dict filter {'metadata.seed': True} in RawNote.find to check for seeded docs. | tool_result | sound | Using a dict filter {'metadata.seed': True} to check seeded docs was a pragmatic fix; events reflect the change and successful seeding. |
| D010 | I chose to create indexes via the documentdb MCP server for verification. | readiness_report | questionable | Creating indexes via the MCP server was reasonable but the documentdb_create_index tool failed due to management-tools being disabled in this environment (events.jsonl shows ToolExecutionException). The plan to use MCP was sensible but did not succeed here. |
| D011 | I chose to retry documentdb_create_index once. | tool_result | sound | Retrying documentdb_create_index once was a reasonable attempt; events show the retry also failed, so the subsequent fallback to a local script was appropriate. |
| D012 | I chose to create indexes using Motor in a Python script (create_indexes.py). | tool_result | sound | Creating indexes using a Motor script (create_indexes.py) was a successful fallback and events.jsonl show that create_indexes.py succeeded and the indexes were observed via documentdb_list_indexes. |
| D013 | I chose to change the tests to avoid instantiating Beanie Document objects and instead test model structure and Settings statically. | model_default | sound | Changing tests to avoid instantiating Beanie documents removes the external DB dependency for unit tests, making them deterministic. Events show the tests were updated and then passed. Note: this reduces integration coverage but is acceptable for CI-level unit tests. |

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
| On the checklist, found only when searched for by name | 1 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 1 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 9 | Public and discoverable. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| Driver version choice | Use the service-recommended driver/ODM versions (Beanie 2 + AsyncMongoClient recommended for Beanie quickstart).<br>**Searches:** Searched Microsoft Learn for 'Beanie quickstart Azure DocumentDB' and found guidance recommending Beanie 2 + AsyncMongoClient. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| External LLM PHI guidance | Before sending clinical text to an external LLM, verify compliance and minimize PHI exposure. | A short official guidance page stating whether sending PHI to external LLMs is acceptable, required mitigations (BAA, encryption, minimal context), or recommended alternatives (local regex, on-prem LLM). |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Create a single shared MongoClient/Async client at process startup and reuse it across requests. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| TLS enforcement | Always require TLS for client connections and do not disable certificate validation in production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Connection tuning & retries | Tune driver connection-pool and timeout settings and implement retry/backoff for transient errors. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Authentication method | Prefer Microsoft Entra ID and RBAC for authentication or state clearly why SCRAM/native auth is used. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Index on sourceId | Create explicit indexes on fields your application queries frequently (sourceId, created_at). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Idempotent pipeline | Ensure exactly one DeidNote per RawNote (unique index on sourceId or upsert pattern). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Avoid logging PHI | Do not log PHI or connection strings; redact or hash identifiers in application logs and use synthetic data for CI and local testing. | README.md<br>README.md |
| Seed script idempotency | Seed scripts should be idempotent and safe to run twice. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Local development gateway | For local development, use the DocumentDB Gateway Docker image (port 10260) rather than the stock mongo image for parity. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Tune driver connection-pool and timeout settings and implement retry/backoff for transient errors. | connection | app/src/db.py:11 creates client but does not set maxPoolSize/serverSelectionTimeoutMS; app contains no retry/backoff logic around DB operations or OpenAI calls. | Add explicit pool/timeouts in client initialization (e.g., maxPoolSize=50, serverSelectionTimeoutMS=5000 for server deployment) and wrap transient DB/HTTP calls with exponential backoff + jitter. Put reusable retry logic into src/db.py or a connection helper. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Use the service-recommended driver/ODM versions (Beanie 2 + AsyncMongoClient recommended for Beanie quickstart). | connection | app/requirements.txt pins beanie==1.26.0 and motor==3.1.1 (Beanie 1.x + Motor); Microsoft Learn quickstart recommends Beanie 2 + PyMongo AsyncMongoClient. | Update requirements.txt and code to follow Beanie 2 + AsyncMongoClient (change motor usage to AsyncMongoClient) or explicitly document the compatibility and why Beanie 1.x was chosen. Prefer aligning with the official quickstart for publishable samples. | [Quickstart: Connect Beanie to Azure DocumentDB](https://learn.microsoft.com/azure/documentdb/quickstart-python-beanie) |
| Prefer Microsoft Entra ID and RBAC for authentication or state clearly why SCRAM/native auth is used. | secrets | app/src/db.py:8-11 reads DOCUMENTDB_URI connection string from env; README.md:12-16 instructs setting DOCUMENTDB_URI. There is no code or README explanation about using Microsoft Entra ID (MONGODB-OIDC) or reason for not using it. | Either: (a) implement Microsoft Entra ID support (show how to fetch an OIDC token and pass it to the driver) or (b) add a short README section explaining why the sample uses a connection string (e.g., simplest for samples) and recommend Entra ID for production. | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Before sending clinical text to an external LLM, verify compliance and minimize PHI exposure. | security | Searched for 'Azure DocumentDB OpenAI PHI guidance' and found no authoritative product statement. | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create a single shared MongoClient/Async client at process startup and reuse it across requests. | connection | app/src/db.py:11 (AsyncIOMotorClient created) and app/deid_pipeline.py:35-37 (init_db called once and reused). | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Always require TLS for client connections and do not disable certificate validation in production. | security | app/src/db.py:11 (AsyncIOMotorClient(uri, tls=True) ensures TLS). | [documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md) |
| Create explicit indexes on fields your application queries frequently (sourceId, created_at). | indexing | app/create_indexes.py:16-18 creates idx_sourceId and idx_created_at; events.jsonl documents created indexes and documentdb_list_indexes confirms idx_sourceId and idx_created_at. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Ensure exactly one DeidNote per RawNote (unique index on sourceId or upsert pattern). | application_pattern | app/deid_pipeline.py:61-66 checks existing DeidNote by sourceId and skips inserting if present; app/create_indexes.py creates idx_sourceId to support efficient lookup. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Do not log PHI or connection strings; redact or hash identifiers in application logs and use synthetic data for CI and local testing. | security | README.md:33-34 states all provided notes are synthetic and 'Never commit real PHI' and the code does not print raw note contents; no connection strings committed to repo. | README.md<br>README.md |
| Seed scripts should be idempotent and safe to run twice. | testing | app/seed.py:34-46 checks for metadata.seed True before inserting; events.jsonl shows seed.py printed 'Inserted 5 synthetic notes.' and earlier prevented duplicate runs. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| For local development, use the DocumentDB Gateway Docker image (port 10260) rather than the stock mongo image for parity. | local_development | The sample targets a live cluster (DOCUMENTDB_URI) and does not include a local docker-compose dev environment or instructions to run the DocumentDB gateway; README suggests connecting to a reachable cluster. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

### Reference requirements

15 of 21 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The vector index dimensions match the embedding model's output. | not_met | prompt_silent | No embedding generation or vector-index creation is present in the repository (no embedding call in deid_pipeline.py and create_indexes.py creates only sourceId and created_at indexes). | If the sample will include embeddings/vector search, update the sample's README and create_indexes script to choose index dimensions that equal the embedding length (e.g., dimensions=1536 for the chosen embedding model). Prefer adding a rule to the documentdb-vector-search skill requiring index dimension = embedding length for any sample that uses embeddings. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_met | prompt_silent | No vector index creation or embedding parameters are present; README contains no vector-index guidance. | Add index-creation examples and a short 'vector index sizing' section to README showing parameters for small vs larger datasets (or add to documentdb-vector-search skill guidance). |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC files (Bicep/ARM/Terraform) targeting Microsoft.DocumentDB/mongoClusters are present in the repository. | Add a minimal Bicep/Terraform example that creates a Microsoft.DocumentDB/mongoClusters resource (or an AzAPI wrapper) with conservative defaults. Prefer shipping this as a sample template file in the repo. |
| Enforce schema and model validation at the application or DB layer (Beanie/Pydantic or MongoDB validation) and include a schemaVersion field to support migrations. | partly_met | skill_guidance_not_followed | app/src/models.py defines Pydantic/Beanie models with typed fields (text, metadata, created_at) but there is no schemaVersion field and no DB-level schema validation. | Add a schemaVersion field to both RawNote and DeidNote models and optionally add a small collection validation document or document the migration plan in README. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | prompt_silent | The sample provides no HTTP /search endpoint or web server to exercise; no code references /search. | Add a minimal search API (e.g., FastAPI) that validates empty queries and returns structured errors, and document error behavior in README. |
| Search results include the similarity score. | not_checkable | prompt_silent | No search endpoint or similarity calculation present in the codebase to inspect. | If adding search, return similarity score with each result and document the format. |
| The pipeline is written in Python and reads the raw clinical notes from Azure DocumentDB through a Beanie ODM Document model that represents a raw note. | met | - | app/src/models.py:6-13 (RawNote definition); app/src/db.py:19 (init_beanie with database); app/deid_pipeline.py:35-38 (RawNote.find_all()). | none |
| Each note returned by the read is sent to OpenAI, one note at a time, and the text OpenAI returns is taken as that note's de-identified version. | met | - | app/deid_pipeline.py:44-58 (per-note openai.ChatCompletion.create call and use of resp['choices'][0]['message']['content']). | none |
| The request to OpenAI carries a prompt engineered for de-identification: it instructs the model to identify PHI entities in the note and replace each with a placeholder (e.g. [NAME], [DATE]). | met | - | app/deid_pipeline.py:47-50 (prompt text: 'You are a de-identification assistant. Replace all PHI (names, dates, locations, IDs) with placeholders...'). | none |
| The prompt names the PHI categories to detect, covering at least names, dates, locations and IDs. | met | - | app/deid_pipeline.py:47-49 (prompt lists names, dates, locations, IDs and placeholders). | none |
| The de-identified text is written back to Azure DocumentDB as a new, separate document through a Beanie ODM Document model, leaving the raw note document as it was. | met | - | app/src/models.py:14-22 (DeidNote model); app/deid_pipeline.py:60-66 (create DeidNote instance and insert if no existing). | none |
| Each de-identified document carries a sourceId field holding the id of the raw note it was produced from. | met | - | app/src/models.py:16 (DeidNote.sourceId Indexed()); app/deid_pipeline.py:60 (sourceId=str(n.id)). | none |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/.env.example:2-4 (DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL placeholders); app/src/db.py:8-11 (reads DOCUMENTDB_URI from env and errors if missing). | none |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example:1-4 contains DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL placeholders. | none |
| One database client is created and reused across requests. | met | - | app/src/db.py:11 (AsyncIOMotorClient created once in init_db) and app/deid_pipeline.py:35-37 (init_db called once and client reused for the batch). | none |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/seed.py:34-46 (seed records with metadata.seed marker; script checks for existing seeded docs before inserting); app/create_indexes.py:16-18 creates indexes. Events show seed.py inserted 5 notes and create_indexes.py created indexes. | none |
| Dependencies are pinned in requirements.txt. | met | - | app/requirements.txt:1-6 (pinning beanie==1.26.0, motor==3.1.1, pymongo==4.6.0, openai==0.27.10, python-dotenv==1.0.0, pytest==7.4.0). | none |
| Unit tests run without a live cluster. | met | - | app/tests/test_models.py (static checks that don't require DB init); events.jsonl shows pytest passed (2 passed) after adjusting tests (events lines ~66). | none |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md contains Overview, What it demonstrates, Prerequisites, Quickstart, Security, Cleaning up (lines 1-37). | none |
| The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. | met | - | app/README.md:1 and other files reference 'Azure DocumentDB' (README overview and quickstart). | none |
| Make the de-identification pipeline idempotent by ensuring exactly one DeidNote per RawNote. | met | - | app/deid_pipeline.py:61-66 (check for existing DeidNote with same sourceId and skip insert if present); app/create_indexes.py creates idx_sourceId which supports lookups. | none |

