# 5. Best-practice audit: 01-unified-customer-profile-store

**Verdict: pass_with_findings** (10 followed, 4 not assessable, 3 violated)

Documentation search was not available to the auditor (documentation_search_available: false), so all "not found" statements below mean "not searchable from this machine" rather than a definitive absence on the web. The sample implements the requested Node.js + Mongoose service and most gallery hygiene: it reads DOCUMENTDB_URI from the environment, reuses a single Mongoose connection scoped to the sample database, provides an HTTP POST /events endpoint, an idempotent seed that creates indexes non-destructively, and a README describing setup/run. The main functional correctness issue is the upsert implementation: it sets the entire source subdocument (sources.<source>) to the incoming attributes object rather than merging only the dotted paths present in the event; this can clobber unrelated fields previously present under the same source. Other findings: dependencies are not strictly pinned in package.json (caret ranges are used though package-lock.json exists), there are no unit tests that run without a live cluster, and no infrastructure-as-code is included. Decisions recorded in decisions.jsonl are mostly sound; one (D007) is questionable because it claims the upsert avoids overwriting unrelated fields while the code will overwrite the whole source subdocument.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approval with readiness 'ready_with_gaps' is an operator decision. The repo contains trade-offs and missing items consistent with 'ready with gaps'. |
| D002 | I chose Node.js with Express and Mongoose (Mongoose 7.x) for the sample service. | prompt | sound | Decision to use Node.js + Express + Mongoose is consistent with the prompt and implementation (app/package.json and code). |
| D003 | I chose to read DOCUMENTDB_URI from the environment at runtime. | skill | sound | Decision to read DOCUMENTDB_URI from environment is reflected in app/src/db.js lines 4-8. Events show earlier logging attempts failed due to a validation constraint but the final decision D003 is recorded and matches the code. |
| D004 | I chose not to provision Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI. | model_default | sound | Decision not to provision Azure resources is consistent with run policy; README explicitly states the sample does not provision resources (app/README.md line 41). The events log shows the policy reason_source was model_default. |
| D005 | I chose to create a unique index on customerId in the sample's seed/initialization code and schema. | readiness_report | sound | Decision to create a unique index on customerId is implemented in the schema and seed script (app/src/models/customer.js line 18 and scripts/seed.js lines 13-16). |
| D006 | I chose a canonical profile document with nested sub-documents per source system (fields: sources.crm, sources.ecommerce, sources.support). | prompt | sound | Decision to model nested sub-documents per source is implemented (app/src/models/customer.js lines 8-11). |
| D007 | I chose to implement idempotent upserts using updateOne with $set on the nested 'sources.<source>' path and upsert:true. | readiness_report | questionable | The decision states upserts will use $set on nested 'sources.<source>' to avoid overwriting unrelated fields. The code (app/src/lib/upsert.js lines 12-16) does $set on the whole sources.<source> object, which overwrites existing fields under that same source. The decision's stated intent (avoid overwriting unrelated fields inside the same source subdocument) is not achieved by the implementation—either the decision or the implementation is inconsistent with the intended merging behavior. |
| D008 | I chose Mongoose 7.x (package.json pins ^7.6.1). | prompt | sound | Decision to use Mongoose 7.x is reflected in package.json dependencies (mongoose ^7.6.1). |
| D009 | I chose to detect an existing conflicting index and skip creating the unique index to avoid destructive changes to the customer's cluster. | tool_result | sound | Decision to detect existing conflicting index and skip recreation is supported by the seed script's error handling (scripts/seed.js lines 13-22) and by the events log showing an initial index conflict followed by a fixed seed run. |

Documentation gaps: 7 (see `doc-gaps.md`).

## Appendix

### Sources that were reachable in this run

> **No documentation search server answered.** In this report, "not found" means "not searchable from this machine", not "not public". Fix the server in `mcp.json` and re-run the audit.

| Source | Reachable | Detail |
|---|---|---|
| Installed agent skills | 0 | 0 have a public address |

### Public availability of best practices

| Outcome | Count | What it means |
|---|---|---|
| On the checklist, no public source found | 0 | Not public, or not written down. A documentation gap. |
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 7 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 10 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Connection options | Use the driver/Mongoose connection options and the provided connection string so driver-level TLS and SRV handling remain correct; avoid hardcoding conflicting flags in code. | A short, authoritative Mongoose connect snippet (pinned to the tested Mongoose version) showing recommended options for the managed DocumentDB cluster (e.g., which tls/ssl/replicaSet/retryWrites/connectTimeoutMS values to include) would let an agent verify and implement recommended flags. |
| Connection pool sizing | Configure a connection pool sized to the workload rather than opening many short-lived connections per request; set maxPoolSize appropriate to app concurrency. | A short guidance page stating recommended maxPoolSize defaults and examples for low/high concurrency deployments for this managed DocumentDB product. |
| Idempotency and event dedupe | Make updates idempotent by using upsert patterns and timestamps (createdAt/updatedAt); track event deduplication at the application layer if needed. | A short spec describing when to include eventId tracking and example schema additions to the Customer profile would let an agent implement event deduplication. |
| Retry/backoff | Implement retry with exponential backoff and jitter for transient network errors and throttling (429). | A recommended retry policy example for this managed DocumentDB product (which error codes to retry, recommended max attempts and backoff parameters). |
| Avoid unbounded document growth | Avoid unbounded document growth by keeping profile documents small or moving high-cardinality/time-series events into a separate collection. | Guidance page describing document-size limits for this managed DocumentDB product and recommended patterns (when to move events to a separate collection and sample schema). |
| Indexing for query patterns | Create indexes that match your read/query patterns and avoid broad wildcard indexes over large nested subdocuments. | Documentation stating RU implications of additional indexes and examples of partial/sparse indexes for optional source fields would help decide further indexing. |
| DB-level schema validation | Use schema validation on the DB if you need to enforce document shapes; Mongoose validation alone is not DB-level enforcement. | A short example of the collection validator JSON schema and a seed snippet that calls db.createCollection(..., { validator: { $jsonSchema: ... } }). |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection reuse | Create and reuse a single client for the life of the process (do not open per-request connections). | src/db.js<br>src/db.js |
| Secrets in repo | Read the cluster connection string only from an environment variable (DOCUMENTDB_URI) at runtime and do not commit real credentials; provide a .env.example with a placeholder instead. | .env.example / README.md / src/db.js<br>.env.example<br>src/db.js |
| Unique index on customerId | Create a unique index on customerId so identity resolution and upserts can rely on a stable unique key. | src/models/customer.js<br>src/models/customer.js<br>scripts/seed.js |
| Idempotent upserts | Perform single-document idempotent upserts using updateOne with upsert:true and $set/$setOnInsert (set updatedAt and setOnInsert createdAt) to keep writes atomic and safe for concurrent updates. | src/lib/upsert.js / README.md<br>src/lib/upsert.js |
| Per-source nested subdocuments | Model each source system as a nested subdocument (sources.crm, sources.ecommerce, sources.support) so source-specific attributes are stored under each source key. | src/models/customer.js / README.md<br>src/models/customer.js |
| Flexible source schema | Use a flexible SourceSchema (strict: false) for source subdocuments so events with different attribute shapes can be accepted without prior schema changes. | src/models/customer.js<br>src/models/customer.js |
| Idempotent index creation | Create indexes in an idempotent, non-destructive way (call createIndexes and handle IndexKeySpecsConflict rather than dropping existing indexes). | scripts/seed.js<br>scripts/seed.js |
| Input validation | Validate incoming event shape at the API boundary and return HTTP 400 for missing required fields (require source, customerId, attributes). | src/routes/events.js<br>src/routes/events.js |
| Set vs replace for source attributes | Model each source system as a nested subdocument and update that source key with targeted $set of the changed sub-paths so each source’s data is isolated and partial updates do not overwrite unrelated fields. | README.md / src/lib/upsert.js / src/models/customer.js<br>src/lib/upsert.js |
| README completeness | The README states what the sample shows, prerequisites, setup, run and clean-up steps. | README.md |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Model each source system as a nested subdocument and update that source key with targeted $set of the changed sub-paths so each source’s data is isolated and partial updates do not overwrite unrelated fields. | data_model | app/src/lib/upsert.js lines 12-16 set update.$set[setPath] = attributes which replaces the whole sources.<source> object rather than setting only the provided attributes via dotted sub-paths. | Change upsertEvent to generate $set entries per nested attribute (e.g. update.$set[`sources.${source}.${field}`] = value for each field) or recursively merge per-field so existing unrelated fields under the same source are preserved. | README.md / src/lib/upsert.js / src/models/customer.js<br>src/lib/upsert.js |
| Implement retry with exponential backoff and jitter for transient network errors and throttling (429). | retries | No retry/backoff logic is present in DB calls or seed scripts; app/src/lib/upsert.js calls Customer.updateOne() without retries. | Add a small retry wrapper to upsertEvent that retries on transient network errors and 429 responses with exponential backoff and jitter, limited to a small number of attempts. | src/lib/upsert.js (no public address recorded) |
| Use schema validation on the DB if you need to enforce document shapes; Mongoose validation alone is not DB-level enforcement. | data_model/validation | Repository uses Mongoose schemas for application-level validation but contains no DB-level JSON Schema validators or createCollection validators. | If DB-level enforcement is desired, add a createCollection call in seed.js with a JSON Schema validator for required fields (customerId, sources object shape) and document it in README. | src/models/customer.js (no public address recorded) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Use the driver/Mongoose connection options and the provided connection string so driver-level TLS and SRV handling remain correct; avoid hardcoding conflicting flags in code. | connection | - | src/db.js (no public address recorded) |
| Configure a connection pool sized to the workload rather than opening many short-lived connections per request; set maxPoolSize appropriate to app concurrency. | connection | - | src/db.js (no public address recorded) |
| Avoid unbounded document growth by keeping profile documents small or moving high-cardinality/time-series events into a separate collection. | data_model/provisioning | - | sample-data/events.json / src/models/customer.js (no public address recorded) |
| Create indexes that match your read/query patterns and avoid broad wildcard indexes over large nested subdocuments. | indexing/queries | - | src/models/customer.js (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create and reuse a single client for the life of the process (do not open per-request connections). | connection | app/src/db.js lines 10-16 (mainConnection caching and early return) and line 20 (useDb('sample_customer_360_01')). | src/db.js<br>src/db.js |
| Read the cluster connection string only from an environment variable (DOCUMENTDB_URI) at runtime and do not commit real credentials; provide a .env.example with a placeholder instead. | authentication/secrets | app/.env.example lists DOCUMENTDB_URI (line 4); app/src/db.js reads process.env.DOCUMENTDB_URI (line 4) and errors if unset (lines 5-8). | .env.example / README.md / src/db.js<br>.env.example<br>src/db.js |
| Create a unique index on customerId so identity resolution and upserts can rely on a stable unique key. | indexing/data_model | app/src/models/customer.js line 18 declares CustomerSchema.index({ customerId: 1 }, { unique: true }); scripts/seed.js calls Customer.createIndexes() (line 14) and handles conflicts. | src/models/customer.js<br>src/models/customer.js<br>scripts/seed.js |
| Perform single-document idempotent upserts using updateOne with upsert:true and $set/$setOnInsert (set updatedAt and setOnInsert createdAt) to keep writes atomic and safe for concurrent updates. | data_model/transactions | app/src/lib/upsert.js lines 13-22 show $set updatedAt and $setOnInsert createdAt/customerId and line 25 uses updateOne(..., { upsert: true }). | src/lib/upsert.js / README.md<br>src/lib/upsert.js |
| Model each source system as a nested subdocument (sources.crm, sources.ecommerce, sources.support) so source-specific attributes are stored under each source key. | data_model | app/src/models/customer.js lines 8-11 define sources.crm, sources.ecommerce and sources.support as subdocuments (SourceSchema). | src/models/customer.js / README.md<br>src/models/customer.js |
| Use a flexible SourceSchema (strict: false) for source subdocuments so events with different attribute shapes can be accepted without prior schema changes. | data_model/validation | app/src/models/customer.js line 4 defines const SourceSchema = new Schema({}, { strict: false }). | src/models/customer.js<br>src/models/customer.js |
| Create indexes in an idempotent, non-destructive way (call createIndexes and handle IndexKeySpecsConflict rather than dropping existing indexes). | indexing/provisioning | app/scripts/seed.js lines 13-22 call Customer.createIndexes() and catch IndexKeySpecsConflict to skip destructive changes; events.jsonl shows initial attempt produced an index conflict and seed was updated to handle it. | scripts/seed.js<br>scripts/seed.js |
| Validate incoming event shape at the API boundary and return HTTP 400 for missing required fields (require source, customerId, attributes). | input_validation/observability | app/src/routes/events.js lines 6-11 check for !source \|\| !customerId \|\| !attributes and return 400 with an error JSON. | src/routes/events.js<br>src/routes/events.js |
| Make updates idempotent by using upsert patterns and timestamps (createdAt/updatedAt); track event deduplication at the application layer if needed. | retries/idempotency | The sample uses upsert with $setOnInsert createdAt and $set updatedAt (app/src/lib/upsert.js lines 14-21) which provides basic idempotency at the document level; it does not store per-event eventId for dedupe. | src/lib/upsert.js (no public address recorded) |
| The README states what the sample shows, prerequisites, setup, run and clean-up steps. | sample hygiene | app/README.md includes what the sample shows, prerequisites and quickstart (lines 5-27). Clean-up is missing (limitations mention no provisioning). | README.md |

### Reference requirements

10 of 19 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The update merges the event's attributes with the `$set` operator on dotted paths inside the originating source system's sub-document (e.g. `crm.email`), writing only the fields present in the event. | not_met | builder_error | app/src/lib/upsert.js lines 12-16 build setPath = `sources.${source}` and then $set [setPath]: attributes (this replaces the whole source subdocument with the attributes object rather than setting dotted sub-fields). | Update upsertEvent to set individual dotted fields instead of replacing the whole subdocument. Example smallest change: build update.$set entries per attribute key (e.g. for each [k,v] in attributes set update.$set[`sources.${source}.${k}`] = v) and then call updateOne(filter, update, { upsert: true }). |
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | The sample exposes only POST /events and has no /search endpoint; no embedding or search logic is present. | Add a /search endpoint (or a separate sample) and implement explicit checks returning HTTP 400 for empty queries and 502/500 with clear error messages if embedding service calls fail. |
| Search results include the similarity score. | not_met | prompt_silent | No search or embedding implementation exists in this repository. | If search is added, include similarity score in the JSON response and tests that assert its presence. |
| Unit tests run without a live cluster. | not_met | prompt_silent | No test files are present and no test framework is configured in package.json. | Add unit tests that mock Mongoose (or use an in-memory Mongo stub) to test upsert logic and validation. For example, a test for upsertEvent that stubs db.model(...).updateOne and asserts called arguments. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | There are no ARM/Bicep/Terraform files or az CLI provisioning scripts in the repo; README explicitly says the sample does not provision resources (app/README.md line 41). | Add an optional infra/ folder with an example (ARM/Bicep/Terraform) that shows the correct resource type and minimal parameters for creating a DocumentDB account, clearly marked optional. |
| Dependencies are pinned in `requirements.txt`. | partly_met | prompt_silent | This is a Node.js project: app/package.json lists dependencies with caret ranges (dotenv: ^16.3.1, express: ^4.18.2, mongoose: ^7.6.1). A package-lock.json is present in the repo, which locks the dependency graph for reproducible installs, but package.json uses ranged semver, not exact pins. | Either pin exact dependency versions in package.json (remove caret and use exact versions) or add guidance in README to use npm ci and commit package-lock.json (already present). |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | prompt_silent | app/README.md documents what the sample shows, prerequisites and quickstart setup/run (lines 5-27), but it does not include explicit clean-up steps to remove created data/collections. | Add a short "clean-up" section to README with commands to drop the sample collection or instructions to run a cleanup script (or explain how to remove the sample DB/collection safely). |
| The vector index dimensions match the embedding model's output. | not_checkable | - | The sample does not create or use any vector index or embeddings; repo contains no embedding model or vector-index creation. | If vectors are added later, include explicit dims and model mapping in seed/index creation code and README. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | - | No vector indexes exist in the repo; README does not document any vector index parameters. | N/A unless the sample adds vector search; then document algorithm_config, m/efConstruction and dims in README and seed script. |
| The service is written in Node.js and uses the Mongoose ODM, with a Mongoose schema and model for the canonical customer profile document stored in Azure DocumentDB. | met | - | app/src/models/customer.js lines 6-23 define a Mongoose schema (CustomerSchema) and createModel(db) returning db.model('Customer', CustomerSchema). | none |
| The canonical profile schema carries a stable `customerId` field and one nested sub-document per source system (CRM, e-commerce and support). | met | - | app/src/models/customer.js lines 6-12 (customerId field and sources.crm, sources.ecommerce, sources.support). | none |
| The service exposes an entry point that receives a customer event carrying its originating source system, the customer's `customerId` and that system's attributes (e.g. an HTTP endpoint or an exported handler function). | met | - | app/src/routes/events.js lines 6-13 define POST /events expecting { source, customerId, attributes }; app/src/index.js registers the route (lines 9 and 13-18). | none |
| Identity resolution matches an incoming event to its profile on the stable `customerId` alone: the update's filter selects the document by `customerId`. | met | - | app/src/lib/upsert.js lines 11-13: const filter = { customerId }; the update call uses that filter (line 25). | none |
| Each event is applied through a Mongoose upsert (e.g. `findOneAndUpdate` or `updateOne` with `upsert: true`), creating the canonical profile document when none exists for that `customerId` and updating the existing one otherwise. | met | - | app/src/lib/upsert.js lines 23-26 use updateOne(filter, update, { upsert: true }). | none |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/.env.example lists DOCUMENTDB_URI (line 4) and app/src/db.js reads process.env.DOCUMENTDB_URI (line 4) and exits when not set (lines 5-8). No real credentials are committed. | none |
| A `.env.example` lists every setting with placeholder values. | met | - | app/.env.example contains DOCUMENTDB_URI and PORT placeholders (lines 4-5) and sample URI examples (lines 7-9). The code only requires DOCUMENTDB_URI and optionally PORT. | none |
| One database client is created and reused across requests. | met | - | app/src/db.js lines 10-16 cache mainConnection and return the same mongoose connection; routes call dbModule.connect() but it returns the reused connection (line 14-21). | none |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed.js reads sample-data/events.json (lines 24-26) and upserts each event (line 30). It calls Customer.createIndexes() inside a try/catch and handles index conflicts non-destructively (lines 13-22). The run logs show the seed was executed twice and the second run completed (events.jsonl run outputs). | none |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | app/README.md uses 'Azure DocumentDB' (line 3 and elsewhere) and the code/comments refer to DocumentDB. No Cosmos or other vendor names are used in the sample files. | none |

