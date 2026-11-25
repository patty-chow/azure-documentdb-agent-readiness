# 5. Best-practice audit: 13-algorithmic-trade-journal

**Verdict: pass_with_findings** (8 followed, 4 violated, 2 not assessable, 1 not applicable)

The sample implements the requested Python/FastAPI trade-journal: immutable per-event documents (signals, executions, outcomes) with strategy_id and timestamp, server-side aggregation for counts/avg/win-rate, a deterministic client-side max-drawdown computation, an LLM-ready formatter, idempotent seeding, pinned dependencies, a singleton MongoClient and a compound index. Tests and seeding were exercised against the reachable cluster. Main findings: (1) max-drawdown is computed client-side rather than purely server-side (developer chose this intentionally because no canonical server-side pipeline was found), (2) client retry/backoff behavior is not implemented, (3) unit tests require a live cluster rather than running offline via mocks, and (4) the repo does not include IaC for provisioning the cluster or explicit clean-up steps in the README. Several public guidance gaps were confirmed (notably a missing canonical server-side max-drawdown pipeline example) and are listed under doc_gaps with recommended fixes.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Decision to approve the build with readiness 'ready_with_gaps' is consistent with the build artifacts and the operator-supplied reason. events.jsonl contains operator/approval activity; no contradictions found. |
| D002 | I chose Python with FastAPI targeting modern CPython (3.11/3.10) | prompt | sound | Choosing Python with FastAPI is consistent with the code produced (app/main.py uses FastAPI). The decision cites the prompt and matches the implemented surface. |
| D003 | I chose to read the cluster connection string from the environment variable DOCUMENTDB_URI at runtime | skill | sound | Reading DOCUMENTDB_URI from the environment is implemented (app/app/db.py:5-7). The reason cites skill/readiness and is supported by the run environment. |
| D004 | I chose not to provision any Azure resources and use the existing, reachable cluster | prompt | sound | Decision not to provision Azure resources matches the run policy in the run environment and the builder's approach (no IaC executed). events.jsonl and the run.md indicate provisioning was disallowed. |
| D005 | I chose to compute max drawdown client-side in Python after retrieving the ordered P&L time series from the server | readiness_report | sound | Decision to compute max drawdown client-side is justified by the readiness findings (missing canonical server-side example). The code implements this approach (app/app/aggregations.py:56-73). |
| D006 | I chose to use a singleton MongoClient (module-level) reused across the FastAPI app | skill | sound | Decision to use a singleton MongoClient is aligned with the documentdb-driver guidance and implemented in app/app/db.py:12-17. events.jsonl shows the documentdb-driver skill was loaded during design/build. |
| D007 | I chose to create a compound index {strategy_id: 1, timestamp: -1} on the journal collection | readiness_report | sound | Decision to create a compound index {strategy_id:1, timestamp:-1} is implemented in app/app/db.py:28-29 and the index creation was validated against the live cluster in the builder's verification steps. |

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
| On the checklist, no public source found | 3 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 1 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 2 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 3 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 6 | Public and discoverable. |

#### On the checklist, no public source found

| Topic | Searched | Description |
|---|---|---|
| Driver version pinning | Searched for 'Azure DocumentDB pymongo supported versions', 'DocumentDB driver compatibility pymongo', 'which pymongo version should I pin for Azure DocumentDB'. Found compatibility pages confirming drivers work but no authoritative pinned-version matrix. | The driver version is pinned and is one the service supports.<br>**What would help:** A one-paragraph compatibility table in the quickstart showing supported driver major versions and a recommended pinned version per language. |
| Tests offline | Searched for 'unit tests DocumentDB without live cluster', 'mongomock pymongo example' (found general mocking resources but no DocumentDB-specific test patterns documented in the skills discovered). | Write tests that run without a live cluster (use mocks/fakes) or document the test requirements clearly.<br>**What would help:** A short sample in documentdb-local-deployment showing how to write mongomock-based unit tests for apps that use pymongo. |
| README clean-up instructions | - | Clean-up steps are provided. |

#### On the checklist, found only when searched for by name

| Topic | Searched for | Sources |
|---|---|---|
| IaC resource type | Infrastructure is defined as code using the service's own resource type (Microsoft.DocumentDB/mongoClusters).<br>**Searches:** Searched for 'Microsoft.DocumentDB/mongoClusters Bicep example' and 'Azure DocumentDB bicep template'. Found the mongoClusters template documentation at learn.microsoft.com. | [Microsoft.DocumentDB mongoClusters 2024-07-01 (deployment-language-terraform)](https://learn.microsoft.com/azure/templates/microsoft.documentdb/mongoclusters) |

#### Found publicly, not on the checklist

| Topic | Description | Sources |
|---|---|---|
| Pinned dependencies (audit trail) | Pin dependency versions used in the sample. | check (no public address recorded) |
| Tests against live DB (audit trail) | Test strategy: integration tests run against provided cluster vs offline tests. | check (no public address recorded) |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Server-side aggregation best practices | Compute aggregates like win rate, average and total P&L using server-side aggregation pipelines ($match → $group → $project) and retrieve ordered series for cumulative/drawdown calculations; for very large aggregations consider allowDiskUse for server-side sorts or spilling. | A short page in the aggregation guidance stating when to set allowDiskUse and how to detect memory pressure from explain() would help. |
| Drawdown windowing | For server-side cumulative metrics and drawdown, prefer $setWindowFields if the cluster supports it; if not available compute cumulative series client-side after retrieving an ordered series from the DB. | A canonical server-side pipeline example that computes max drawdown using $setWindowFields/$reduce would let an agent implement this server-side reliably. |
| Schema validation | Enforce collection-level validation (JSON Schema) to require and type-check fields such as strategy_id, event_type, timestamp and pnl to prevent invalid events from being stored. | A short 'collection validation' example page in the local-deployment or indexing skill showing json-schema examples for event journals. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Client reuse | Create and reuse a single MongoClient per process (singleton) rather than creating a new client per request; initialize it once and reuse across handlers. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Connection settings | Connection settings (timeouts, retry options, TLS) follow the service's recommendation for the chosen driver. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md)<br>[documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md)<br>[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Secrets from env | Keep the cluster connection string/credentials out of source control by reading the connection URI from environment variables (e.g. DOCUMENTDB_URI) or a secret store and providing only a placeholder in .env.example. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Compound index | Create a compound index following ESR (Equality → Sort → Range), for example a compound index on { strategy_id: 1, timestamp: -1 } to serve time-range and sorted queries per strategy. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Retries/backoff | Implement exponential backoff with jitter for client-side retries (initial delay ~100–200ms, exponential factor ~2, max attempts 3–5) and treat some server error codes specially as retryable or non-retryable. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Seed idempotence | Design seed scripts and tests to be idempotent: guard with existence checks or deterministic IDs so repeated runs do not create duplicate documents. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Connection settings (timeouts, retry options, TLS) follow the service's recommendation for the chosen driver. | connection | app/app/db.py:15-16 sets serverSelectionTimeoutMS=5000 but the client is not configured with retryWrites/retryReads, socketTimeoutMS, or explicit TLS flags. No application retry/backoff wrapper is present. | Create the MongoClient with explicit recommended options and add application-level retry/backoff where appropriate. Example smallest change: MongoClient(DOCUMENTDB_URI, serverSelectionTimeoutMS=5000, socketTimeoutMS=300000, retryWrites=True). Add an app-level retry wrapper with exponential backoff for transient errors. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md)<br>[documentdb-security](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/security/SKILL.md)<br>[documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Implement exponential backoff with jitter for client-side retries (initial delay ~100–200ms, exponential factor ~2, max attempts 3–5) and treat some server error codes specially as retryable or non-retryable. | retries | app/app/db.py:15-16 sets only serverSelectionTimeoutMS=5000. No application-level retries or backoff are implemented and insert paths (app/app/journal.py:27-33) directly call insert_one. | Add an application retry wrapper around insert operations (e.g., 3 attempts with exponential backoff + jitter) or use a helper library; at minimum set retryWrites=True on the client and add a retry loop for transient network errors. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |
| Write tests that run without a live cluster (use mocks/fakes) or document the test requirements clearly. | testing | app/tests/test_aggregations.py:7-23 creates real documents via get_db() and coll.insert_one / delete_many; the test requires a live cluster. | Add tests that patch app.db.get_db to return a mongomock.MongoClient() or use unittest.mock to stub the DB for unit tests. Keep one integration test suite that runs only when a DOCUMENTDB_URI is provided. | checklist only (no public address recorded) |
| Clean-up steps are provided. | provisioning | app/README.md (no 'Clean-up' section present). | Add a 'Clean-up' section with commands such as 'mongo <URI> --eval "db.getSiblingDB(\"sample_fintech_13\").dropDatabase()"' or steps to delete the cluster via az cli/templates. Warn about shared clusters. | checklist only (no public address recorded) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| For server-side cumulative metrics and drawdown, prefer $setWindowFields if the cluster supports it; if not available compute cumulative series client-side after retrieving an ordered series from the DB. | aggregation | Searched for 'Azure DocumentDB $setWindowFields support' and 'DocumentDB server-side max drawdown example' with no complete tested example returned. | prior_knowledge (no public address recorded) |
| Enforce collection-level validation (JSON Schema) to require and type-check fields such as strategy_id, event_type, timestamp and pnl to prevent invalid events from being stored. | data_modeling | Searched for 'Azure DocumentDB schema validation json schema' with no single official example showing schema validators for event journaling. | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create and reuse a single MongoClient per process (singleton) rather than creating a new client per request; initialize it once and reuse across handlers. | connection | app/app/db.py:12-17 (module-level _client and get_client() creating a MongoClient instance once) | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Keep the cluster connection string/credentials out of source control by reading the connection URI from environment variables (e.g. DOCUMENTDB_URI) or a secret store and providing only a placeholder in .env.example. | authentication and secrets | app/app/db.py:5-7 (reads DOCUMENTDB_URI from environment and errors if missing); app/.env.example:1-2 contains a placeholder; README warns about not committing secrets (app/README.md:25-26). | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| The driver version is pinned and is one the service supports. | connection | app/requirements.txt:3 pins pymongo==4.4.0. The sample pins dependencies but public guidance that names specific pinned driver versions for Azure DocumentDB was not found during discovery. | checklist only (no public address recorded) |
| Create a compound index following ESR (Equality → Sort → Range), for example a compound index on { strategy_id: 1, timestamp: -1 } to serve time-range and sorted queries per strategy. | indexing | app/app/db.py:25-29 (ensure_indexes creates idx_strategy_time with [ ('strategy_id',1), ('timestamp',-1) ]); decisions.jsonl D007 records that choice. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Compute aggregates like win rate, average and total P&L using server-side aggregation pipelines ($match → $group → $project) and retrieve ordered series for cumulative/drawdown calculations; for very large aggregations consider allowDiskUse for server-side sorts or spilling. | aggregation | app/app/aggregations.py:39-51 implements $match/$group/$project on outcome documents for trade_count, total_pnl, avg_pnl; coll.aggregate used (line 53). | prior_knowledge (no public address recorded) |
| Design seed scripts and tests to be idempotent: guard with existence checks or deterministic IDs so repeated runs do not create duplicate documents. | testing | app/scripts/seed_data.py:26-30 (checks existing outcome count and exits if >=10) and app/scripts/seed_data.py:19-21 (ensure_indexes called). | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Pin dependency versions used in the sample. | audit trail | app/requirements.txt:1-6 shows pinned versions. No matching decision entry in decisions.jsonl records the chosen pinned versions. | check (no public address recorded) |
| Test strategy: integration tests run against provided cluster vs offline tests. | audit trail | app/tests/test_aggregations.py:7-23 interacts with the real DB; there is no decision recorded in decisions.jsonl explaining whether offline tests were considered or why live-cluster tests were chosen. | check (no public address recorded) |

#### Not applicable

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Infrastructure is defined as code using the service's own resource type (Microsoft.DocumentDB/mongoClusters). | provisioning | No IaC files in the repository. The documentation page for Microsoft.DocumentDB/mongoClusters exists (learn.microsoft.com template). | [Microsoft.DocumentDB mongoClusters 2024-07-01 (deployment-language-terraform)](https://learn.microsoft.com/azure/templates/microsoft.documentdb/mongoclusters) |

### Reference requirements

15 of 24 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | There is no /search endpoint in app/app/main.py; sample does not implement semantic/vector search. | If search is in scope, add a /search endpoint that validates non-empty query payloads and returns clear error codes; wrap embedding calls with try/except and return 4xx/5xx responses describing failures. |
| Search results include the similarity score. | not_met | prompt_silent | No search endpoint or similarity scoring implemented in the sample. | If adding search, include similarity score in results (e.g., return normalized similarity with each hit). |
| Unit tests run without a live cluster. | not_met | prompt_silent | app/tests/test_aggregations.py uses get_db() and runs against the reachable cluster (tests create and delete documents in the real DB at lines 7-23). The builder ran pytest against the live cluster (build report). | Add unit tests that patch get_db or use an in-memory/mocked Mongo client (e.g., mongomock or unittest.mock to patch app.db.get_db) so tests run offline. Provide an additional CI/test task that runs integration tests only when a real DOCUMENTDB_URI is provided. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | Repository contains no Bicep/ARM/Terraform templates for Microsoft.DocumentDB/mongoClusters or analogous IaC files. | Add a minimal IaC template (Bicep or Terraform) that targets Microsoft.DocumentDB/mongoClusters with parameters for tier, region, and storage; include a README note that the template is not executed by the sample and is for operator use. |
| Win rate, average P&L and drawdown are computed by aggregation pipelines run in Azure DocumentDB (e.g. through the driver's aggregate call) that group on the strategy identifier, returning one result per strategy. | partly_met | prompt_silent | app/app/aggregations.py:39-51 (server-side $group computes trade_count, total_pnl, avg_pnl, wins; coll.aggregate used at line 53). Drawdown is computed client-side: app/app/aggregations.py:56-73 (ordered series is fetched then processed in Python). | If you require a purely server-side drawdown, add to the starter prompt: 'Compute max drawdown server-side using an aggregation pipeline (use $setWindowFields if available); if unsupported, compute it client-side and document why.' Alternatively, add a canonical server-side drawdown pipeline to the documentdb-query-optimization or a new aggregation example doc (preferred for re-use). |
| The pipeline computes drawdown per strategy from that strategy's outcomes ordered by timestamp (e.g. the largest peak-to-trough decline of cumulative P&L). | partly_met | prompt_silent | app/app/aggregations.py:16-21 (outcomes_pipeline sorts by timestamp), app/app/aggregations.py:56-73 (client-side cumulative series and max_drawdown calculation). | Either require server-side drawdown in the starter prompt or include a canonical server-side pipeline in a skill/doc so future builders can implement it (add a documented $setWindowFields-based example in documentdb-query-optimization). |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | app/README.md:3-23 covers what the sample shows, prerequisites and quickstart; README does not include explicit clean-up steps (no instructions to drop the DB/collection or delete resources). | Add a 'Clean-up' section to README with commands to drop the sample DB/collection or instructions to delete the cluster if you created one (and a safety warning about deleting shared resources). |
| The vector index dimensions match the embedding model's output. | not_checkable | - | The sample does not store vector embeddings or create vector indexes; vector features are not used by this app. | not applicable for this sample |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector indexes or embeddings are created by this sample. | not applicable for this sample |
| A Python service inserts each trading signal, each execution and each outcome as its own document into Azure DocumentDB using a MongoDB-compatible Python driver (e.g. PyMongo); every document carries a strategy identifier and a timestamp. | met | - | app/app/journal.py:6-24 (Signal/Execution/Outcome models declare strategy_id and timestamp); app/app/journal.py:27-33 (insert_event uses coll.insert_one(payload)) | none |
| Journal documents are immutable: the service has no code path that updates or deletes a stored signal, execution or outcome document. | met | - | app/app/journal.py:27-33 (insert-only API); app/app/main.py:16-29 (endpoints only insert events). Note: tests delete test fixtures (tests/test_aggregations.py:18) but the service itself has no update/delete endpoints. | none |
| The pipeline computes win rate per strategy from the outcome documents (e.g. winning outcomes divided by total outcomes). | met | - | app/app/aggregations.py:42-49 ($group computes wins and trade_count) and app/app/aggregations.py:74 (win_rate computed from those values). | none |
| The pipeline computes average P&L per strategy from a numeric P&L value on the outcome documents. | met | - | app/app/aggregations.py:45-46 ($sum and $avg over 'pnl' in the server-side $group) and projection at line 50. | none |
| A context engineering layer in Python takes the aggregated per-strategy stats and formats them into prompt-ready context for LLM-driven strategy review (e.g. a structured block of win rate, average P&L and drawdown with a short narrative). | met | - | app/app/formatter.py:4-11 (format_strategy_review returns a deterministic LLM-ready summary string). | none |
| The service exposes operations (e.g. functions or endpoints) to record a signal, an execution or an outcome, and to produce the review context for a given strategy. | met | - | app/app/main.py:16-29 (POST endpoints /journal/signal, /journal/execution, /journal/outcome) and app/app/main.py:31-35 (GET /stats/{strategy_id} returning stats and formatted summary). | none |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/app/db.py:5-7 (DOCUMENTDB_URI read from environment, runtime error if missing); app/.env.example contains placeholder (app/.env.example:1-2); README admonishes not to commit secrets (app/README.md:25-26). | none |
| A `.env.example` lists every setting with placeholder values. | met | - | app/.env.example:1-2 (DOCUMENTDB_URI placeholder present). Only DOCUMENTDB_URI is required by the sample; it is listed. | If additional settings are later added (e.g., TLS flags, DB name), add them to .env.example similarly. |
| One database client is created and reused across requests. | met | - | app/app/db.py:12-17 (module-level _client and get_client() returns singleton MongoClient created once). | none |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed_data.py:19-21 (ensure_indexes()), app/scripts/seed_data.py:26-30 (idempotent guard: check existing outcomes count and exit if >=10), and the script inserts signals/executions/outcomes (lines 32-46). | none |
| Dependencies are pinned in `requirements.txt`. | met | - | app/requirements.txt:1-6 (fastapi==0.100.0, uvicorn==0.22.0, pymongo==4.4.0, python-dotenv==1.0.0, pytest==7.4.0, httpx==0.26.0). | none |
| The sample runs with the commands in the README. | met | - | Builder verified pip install -r requirements.txt and python scripts/seed_data.py and pytest -q (see build report verification). README commands match what was run (app/README.md:19-23). | none |
| Tests exist and pass without a live cloud resource, or the README says what they need. | met | - | Tests require a live cluster but the README documents the prerequisite 'set DOCUMENTDB_URI' and the need for a reachable cluster (app/README.md:13-16), satisfying the 'or README says what they need' clause. | If desired, add offline mock tests as noted above. |
| Dependencies are pinned. | met | - | app/requirements.txt shows pinned dependency versions (app/requirements.txt:1-6). | none |
| The sample names the service correctly and does not use a former or neighbouring product name. | met | - | app/README.md:1-3 uses 'Azure DocumentDB (MongoDB-compatible)'; no references to Azure Cosmos DB for MongoDB RU or Amazon DocumentDB appear in the repository. | none |

