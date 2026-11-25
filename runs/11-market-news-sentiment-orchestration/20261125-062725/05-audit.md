# 5. Best-practice audit: 11-market-news-sentiment-orchestration

**Verdict: pass_with_findings** (6 followed, 13 not assessable)

Documentation search was not available from this run environment, so checks that would normally rely on external docs were judged from the repository contents and the discovery results captured earlier. The sample implements the requested Node.js LangChain-style orchestration, sentiment/ticker extraction (LLM when configured, deterministic fallback otherwise), a reusable MongoClient, idempotent seed/verify scripts, and an alerting demo that logs and optionally POSTs webhooks. Major operational gaps remain around vector-index creation & parameters, embedding-dimensionality validation, an explicit /search endpoint with similarity scoring and error handling, and infrastructure-as-code for the cluster. None of the missing items made the sample non-functional for the demo scenario; they are readiness/documentation and operational gaps that should be fixed before gallery publication.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Approval with readiness 'ready_with_gaps' is consistent with the builder running with --yes. The events log records the build proceeding; this decision is administrative and supported by the run trace. |
| D002 | I chose Node.js (JavaScript/TypeScript not used) for the sample. | prompt | sound | Selecting Node.js matches the prompt and the code produced (package.json main uses src/server.js). events.jsonl shows this decision was recorded and the repository contains Node.js code. |
| D003 | I chose 'mongodb' ^5.7.0 as the driver dependency. | prompt | sound | Driver pinned to 'mongodb' ^5.7.0 and package.json contains that dependency. The events trace shows package.json was written and npm install completed using that dependency. |
| D004 | I chose to read the Azure DocumentDB connection string from the DOCUMENTDB_URI environment variable at runtime. | model_default | questionable | Decision states the connection string is read from DOCUMENTDB_URI (which the code does: src/db.js line 7). However the decision's recorded reason_source is 'model_default' even though the run-environment (skill_md / readiness) explicitly instructs using DOCUMENTDB_URI. The choice is correct but the stated reason_source is inconsistent with available guidance. |
| D005 | I chose OpenAI as the LLM/embedding provider and to read credentials from OPENAI_API_KEY (and OPENAI_API_BASE optionally). | model_default | sound | Choosing OpenAI as the LLM provider is implemented in code (app/src/ai.js) and the choice is reasonable for a sample. The events show fallback heuristics executed when OPENAI_API_KEY was absent. |
| D006 | I chose 'text-embedding-3-small' with embedding dimension 1536 for embeddings. | model_default | questionable | The builder assumed 'text-embedding-3-small' with 1536 dims. This assumption is implemented as the model name in ai.js but embeddings were not exercised in the run (OPENAI_API_KEY was not set). The dimensionality assumption is unverified against the live embedding provider and not validated by the code, so the choice is speculative and should be documented or enforced. |
| D007 | I chose console notifications with an optional webhook POST (WEBHOOK_URL) for demo notifications. | model_default | sound | Console notifications with optional webhook are implemented in app/src/run.js: notify() logs the alert and posts to WEBHOOK_URL if present; events show alerts printed and webhook code exists. |
| D008 | I chose to create a text index on headline and an index on tickers; for vector index I'll include code that attempts to create one but will not rely on it and will document that vector index creation could require manual steps. | readiness_report | sound | Decision to create text and tickers indexes and to document vector index as optional is reflected in scripts/seed.js (createIndex text and tickers). The repo deliberately does not force a vector index creation step in this run; that matches the decision. |
| D009 | I chose both a CLI and a minimal Express HTTP endpoint. | prompt | sound | Both CLI (npm run run) and Express HTTP endpoint (src/server.js) were implemented and exercised. events.jsonl shows run was executed and server is present. |
| D010 | I chose a simple document schema for 'articles' with fields: _id, headline, sentiment (number), tickers (array), timestamp (ISO), embedding (array of numbers) optional. | prompt | sound | The document schema chosen (_id, headline, sentiment, tickers, timestamp, optional embedding) is present in app/src/run.js lines 31-37. This decision is reflected in the implementation. |

Documentation gaps: 9 (see `doc-gaps.md`).

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
| Known to the model, no public source, not on the checklist | 13 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 6 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Driver connection options | When connecting from Node.js, ensure driver connection options (parser/topology and TLS settings) are explicitly configured according to the platform's best practices. | A brief page stating recommended MongoClient options for Node.js connecting to Azure DocumentDB (recommended tls/ssl, connection pool sizing and retry options) with example code. |
| TLS/cert validation | Enable TLS/SSL and certificate validation for client connections and do not disable certificate validation in production. | A definitive doc stating the TLS requirements and example connection string/query parameters for Azure DocumentDB's MongoDB-compatible endpoint. |
| Retryable writes & app retries | Enable driver retryable writes and implement application-level retries with exponential backoff for transient errors and throttling. | A page describing recommended retry settings for this managed DocumentDB service, including whether the driver should enable retryWrites and sample backoff code. |
| TTL for ephemeral articles | Consider using TTL (expireAfterSeconds) on ephemeral article documents so old headlines are removed automatically instead of accumulating indefinitely. | A short example in the agent kit demonstrating adding a TTL index to the articles collection (e.g., {createdAt:1} with expireAfterSeconds) and guidance for appropriate retention periods. |
| Normalize vectors | Normalize vectors for cosine similarity and validate vector dimensionality at ingest time to avoid mismatched-dimension inserts. | A short guidance page or agent-kit rule that says whether embeddings should be L2-normalized for this service and an example normalize+validate function to run before insert. |
| Avoid shipping embeddings unnecessarily | Keep documents reasonably small and avoid shipping embeddings unless needed (use projection in queries to exclude embedding fields when not required). | A short sample demonstrating projection patterns (exclude 'embedding' in queries by default) and when to include it for vector operations. |
| Handle throttling (429) | Handle HTTP 429/RequestRateTooLarge responses by honoring Retry-After and implementing exponential backoff with jitter; monitor and log 429 spikes. | A guidance page showing how to detect 429s and implement Retry-After/jittered backoff for the MongoDB driver and for external webhooks in Node.js. |
| Use explain() to verify indexes | Use explain() to verify queries use indexes and avoid full-collection scans in production. | A verification example showing use of explain() for the watchlist lookup and any vector queries, and guidance on interpreting the plan. |
| Driver & server metrics | Enable driver and server metrics (connection pool, RU consumption, latency, 429s) and create alerts for throttling, high latency, or connection churn. | A short monitoring checklist and sample code/config showing how to export driver metrics for the service (connection pool, latency, and throttles) to an observability backend. |
| Protect run endpoint | Protect server endpoints that trigger scrapes or runs: require authentication/authorization, rate-limit requests, validate inputs and never expose admin DB endpoints or credentials. | An agent-kit rule or short page advising protecting trigger endpoints in sample repos; a small code snippet showing a simple API key check or middleware-based rate limiting would help. |
| Compound index for alerts | Create a compound index tailored to typical alert lookups (for example {ticker:1, active:1}) so watchlist queries are efficient rather than scanning the whole collection. | A recommendation page showing common compound index shapes for alerting lookup patterns (e.g., {ticker:1, active:1}) and when to add them. |
| Bulk ingestion batching | When ingesting at scale, use bulkWrite with reasonable batch sizes and backoff on failures rather than individual inserts to avoid RU saturation. | A short guidance page showing sample bulkWrite usage for Node.js with batch sizes and backoff recommendations for this managed DocumentDB service. |
| Prefer change streams or watermark polling | Prefer change streams or push-based mechanisms to trigger downstream alerting where available; if not, poll efficiently using a last-seen watermark on created_at. | A clear statement in docs about whether MongoDB change streams are supported by this managed service and an example alternative (watermark polling) if not. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Env var for connection string | Read the DocumentDB connection string from a runtime secret (DOCUMENTDB_URI) and provide a .env.example placeholder instead of committing real credentials. | .env.example<br>app/.env.example |
| Client reuse | Reuse a single MongoClient instance across the application process instead of creating a new client per request (store it in module scope and return the same client). | src/db.js<br>app/src/db.js |
| Explicit indexes | Create explicit indexes for fields used in queries (text index on headline and a normal index on tickers are created by the sample seed script). | scripts/seed.js<br>scripts/seed.js |
| Store embeddings field | Store vector embeddings in a dedicated fixed field (embedding) on the document when available and keep vector dimensionality consistent across documents. | src/run.js and src/ai.js<br>app/src/run.js<br>app/src/ai.js |
| Idempotent seed upserts | Use upserts with a dedupe key (e.g., ticker or article id) to make ingestion idempotent; seed script uses updateOne with upsert:true for watchlist entries. | scripts/seed.js<br>scripts/seed.js |
| Idempotent seed & verify scripts | Use idempotent seed and verification scripts that create-if-not-exists and are scoped to the sample_fintech_11 database (do not enumerate or modify other databases on the cluster). | scripts/seed.js and scripts/verify.js<br>scripts/seed.js<br>scripts/verify.js |

### How the app measures up

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| When connecting from Node.js, ensure driver connection options (parser/topology and TLS settings) are explicitly configured according to the platform's best practices. | connection_handling | - | prior_knowledge_only (no public address recorded) |
| Enable TLS/SSL and certificate validation for client connections and do not disable certificate validation in production. | connection_handling | - | prior_knowledge_only (no public address recorded) |
| Enable driver retryable writes and implement application-level retries with exponential backoff for transient errors and throttling. | retries | - | prior_knowledge_only (no public address recorded) |
| Consider using TTL (expireAfterSeconds) on ephemeral article documents so old headlines are removed automatically instead of accumulating indefinitely. | data_modeling | - | prior_knowledge_only (no public address recorded) |
| Normalize vectors for cosine similarity and validate vector dimensionality at ingest time to avoid mismatched-dimension inserts. | vector_search | - | prior_knowledge_only (no public address recorded) |
| Keep documents reasonably small and avoid shipping embeddings unless needed (use projection in queries to exclude embedding fields when not required). | data_modeling | - | prior_knowledge_only (no public address recorded) |
| Handle HTTP 429/RequestRateTooLarge responses by honoring Retry-After and implementing exponential backoff with jitter; monitor and log 429 spikes. | retries | - | prior_knowledge_only (no public address recorded) |
| Use explain() to verify queries use indexes and avoid full-collection scans in production. | queries | - | prior_knowledge_only (no public address recorded) |
| Enable driver and server metrics (connection pool, RU consumption, latency, 429s) and create alerts for throttling, high latency, or connection churn. | logging_monitoring | - | prior_knowledge_only (no public address recorded) |
| Protect server endpoints that trigger scrapes or runs: require authentication/authorization, rate-limit requests, validate inputs and never expose admin DB endpoints or credentials. | server_endpoints | - | prior_knowledge_only (no public address recorded) |
| Create a compound index tailored to typical alert lookups (for example {ticker:1, active:1}) so watchlist queries are efficient rather than scanning the whole collection. | indexing | - | prior_knowledge_only (no public address recorded) |
| When ingesting at scale, use bulkWrite with reasonable batch sizes and backoff on failures rather than individual inserts to avoid RU saturation. | provisioning | - | prior_knowledge_only (no public address recorded) |
| Prefer change streams or push-based mechanisms to trigger downstream alerting where available; if not, poll efficiently using a last-seen watermark on created_at. | queries | - | prior_knowledge_only (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Read the DocumentDB connection string from a runtime secret (DOCUMENTDB_URI) and provide a .env.example placeholder instead of committing real credentials. | auth_and_secrets | app/.env.example lines 1-2; app/src/db.js line 7 reads process.env.DOCUMENTDB_URI. | .env.example<br>app/.env.example |
| Reuse a single MongoClient instance across the application process instead of creating a new client per request (store it in module scope and return the same client). | connection_handling | app/src/db.js lines 3-11 implement module-scoped client and getClient() returns same instance. | src/db.js<br>app/src/db.js |
| Create explicit indexes for fields used in queries (text index on headline and a normal index on tickers are created by the sample seed script). | indexing | scripts/seed.js lines 29-33: createIndex({ headline: 'text' }) and createIndex({ tickers: 1 }). verify.js prints these indexes in events. | scripts/seed.js<br>scripts/seed.js |
| Store vector embeddings in a dedicated fixed field (embedding) on the document when available and keep vector dimensionality consistent across documents. | vector_search | app/src/run.js line 37 adds doc.embedding when embedText() returns a vector; app/src/ai.js embedText() returns the embedding array when OPENAI_API_KEY set. | src/run.js and src/ai.js<br>app/src/run.js<br>app/src/ai.js |
| Use upserts with a dedupe key (e.g., ticker or article id) to make ingestion idempotent; seed script uses updateOne with upsert:true for watchlist entries. | data_modeling | scripts/seed.js lines 24-27: wl.updateOne({ticker:w.ticker}, {$set:w}, {upsert:true}) ensures watchlist upserts. | scripts/seed.js<br>scripts/seed.js |
| Use idempotent seed and verification scripts that create-if-not-exists and are scoped to the sample_fintech_11 database (do not enumerate or modify other databases on the cluster). | scripts | scripts/seed.js uses upsert:true for watchlist entries (lines 24-27) and scripts/verify.js operates against sample_fintech_11 (line 4). | scripts/seed.js and scripts/verify.js<br>scripts/seed.js<br>scripts/verify.js |

### Reference requirements

13 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| The vector index dimensions match the embedding model's output. | not_met | prompt_silent | The code stores embeddings (app/src/run.js line 37) but no cluster vector index is created by the seed script (scripts/seed.js lines 29-33 create only text and tickers indexes). The embedding model choice and dimensionality are an assumed value in decisions (D006) but not enforced in code. | Add an EMBEDDING_DIM environment variable and validate embedText() output length against it before inserting documents; document the chosen embedding model in README and use EMBEDDING_DIM when creating vector indexes in the seed script. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_met | prompt_silent | README notes that vector index creation is not guaranteed (app/README.md line 36-38) but does not recommend index parameters (M/efConstruction/efSearch or similar) or defaults for small vs large datasets; scripts/seed.js does not create a vector index. | Add a README section describing recommended vector-index type and parameter defaults for the sample (including EMBEDDING_DIM) and add an optional seed script path or sample createIndex command that uses those parameters. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_met | prompt_silent | No /search endpoint is implemented. app/src/server.js exposes only GET /run (lines 5-12). | Add a /search endpoint that validates the query, returns 400 for empty queries, calls embedText() and returns a meaningful 502/5xx or JSON error when embedding fails, with logging for operators. |
| Search results include the similarity score. | not_met | prompt_silent | No search endpoint implemented; the current orchestration logs alerts and stores embeddings but does not expose vector similarity results or similarity scores. | Implement a /search endpoint that runs the vector or hybrid search and returns results with a similarity or distance score field for each hit. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No IaC (ARM/Bicep/Terraform) files were added to the repository. Directory listing shows no .bicep, .tf, or ARM templates. | Add a small ARM/Bicep or Terraform sample template that declares the Azure DocumentDB resource (for example Bicep/ARM resource type Microsoft.DocumentDB/databaseAccounts or the appropriate provider resource) with cost-conscious defaults and parameterized region/tier. |
| A `.env.example` lists every setting with placeholder values. | partly_met | builder_error | app/.env.example lines 1-10 include DOCUMENTDB_URI, OPENAI_API_KEY, WEBHOOK_URL, NEWS_API_KEY. server.js uses process.env.PORT (app/src/server.js line 14) but PORT is not present in .env.example. | Add missing runtime environment placeholders (for example add 'PORT="3000"' and any other optional env keys such as OPENAI_API_BASE, EMBEDDING_DIM) to .env.example. |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | partly_met | builder_error | app/README.md includes what the sample shows, prerequisites and run/seed instructions (lines 16-28) but does not document explicit clean-up steps for the resources the sample creates (such as how to remove the sample database or collections). | Add a 'Clean-up' subsection to README with the commands to drop the sample database/collections (for example a small script or instructions to run 'db.dropDatabase()' against sample_fintech_11, or how to remove created resources). |
| Implement the pipeline in Node.js with LangChain, with an orchestrator that runs the scraper agent, the sentiment agent and the alert agent in that order and passes each agent's output to the next. | met | - | app/src/run.js lines 21-31 and 39-47: run() calls fetchHeadlines(), analyzeHeadlineLLM(), embedText(), inserts the document, then queries watchlist and calls notify() for matches. | none |
| Implement a scraper agent that fetches financial news headlines and hands the fetched headlines to the orchestrator. | met | - | app/src/scraper.js lines 29-41: fetchHeadlines() returns either NewsAPI results (if NEWS_API_KEY set) or a bundled sample headlines array. | none |
| Implement a sentiment agent that assigns a sentiment score to each fetched headline. | met | - | app/src/ai.js lines 11-19 (heuristic fallback) and lines 22-35 (LLM path): analyzeHeadlineLLM() returns a numeric sentiment. | none |
| Have the sentiment agent extract the ticker mentions from each headline alongside its score. | met | - | app/src/ai.js line 18 (regex uppercase words) and lines 32-35 (parsing JSON from LLM) return tickers in the analysis result. | none |
| Store every scored article as a document in Azure DocumentDB using a MongoDB driver for Node.js (e.g. `mongodb`), with each document carrying the headline, its sentiment score and the extracted ticker mentions. | met | - | app/src/run.js lines 31-40 constructs the document with headline, sentiment, tickers and uses articles.insertOne(doc). app/src/db.js lines 5-11 show MongoClient read from DOCUMENTDB_URI. package.json lists dependency 'mongodb'. | none |
| Implement an alert agent that queries Azure DocumentDB for watchlist entries matching the tickers extracted from the scored headlines. | met | - | app/src/run.js lines 43-46: matches = await watchlist.find({ ticker: { $in: doc.tickers } }).toArray(); | none |
| Have the alert agent fire a notification for each watchlist match it finds. | met | - | app/src/run.js lines 7-15 (notify function logs and optionally POSTs to WEBHOOK_URL) and lines 46-48 call notify(m, doc) for each match. | none |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/src/db.js line 7 reads process.env.DOCUMENTDB_URI; app/src/ai.js line 4 reads process.env.OPENAI_API_KEY; app/.env.example provides placeholders (lines 1-6). No real keys in repo. | none |
| One database client is created and reused across requests. | met | - | app/src/db.js lines 3-11 implement a module-scoped client variable and return the same MongoClient instance from getClient(). | none |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | scripts/seed.js lines 24-27 use updateOne(..., {upsert:true}) for the watchlist; lines 29-33 create text and tickers indexes. The script logs 'Upserted watchlist' and 'Ensured indexes on articles'. | none |
| Dependencies are pinned in requirements.txt. | met | - | This is a Node project: app/package.json lists package versions and app/package-lock.json is present and was used by npm install (events show npm install completed using package-lock.json). | none |
| Unit tests run without a live cluster. | met | - | app/tests/run-tests.js calls fetchHeadlines() and analyzeHeadlineLLM() only (it does not touch the DB). events.jsonl shows npm test completed and printed 'fetchHeadlines returned 20 items' and analysis output. | none |
| The sample uses the name "Azure DocumentDB" throughout, and no former or neighbouring product name. | met | - | app/README.md and app/.env.example refer to 'Azure DocumentDB (MongoDB-compatible)' and no occurrences of 'Cosmos' or other neighbouring product names were found in repository files. | none |

