# 5. Best-practice audit: 02-transaction-categorization-agent

**Verdict: pass_with_findings** (5 followed, 2 violated, 1 not assessable)

Documentation search tools were available for this run. The sample implements the core functionality requested (LangChain-backed categorization, writes back to Azure DocumentDB, and a server-side aggregation endpoint). Key reference requirements are met (singleton client, idempotent seed, aggregation pipeline, prompt + fixed taxonomy, env-var driven credentials, .env.example, README). Shortcomings: the implementation did not expose DocumentDB operations as LangChain Tools (the agent calls the LLM directly and the app calls the DB), dependencies are not strictly pinned in package.json (carets used though a package-lock exists), there are no tests that run without a live cluster, no infrastructure-as-code for the cluster is provided, and several gallery-quality items (unit tests, pinned deps, infra) are missing. See requirement_results, practice checks and documentation gaps below for details and minimal fixes.

## Review of the builder's decisions

| Decision | What was decided | Reason came from | Assessment | Comment |
|---|---|---|---|---|
| D001 | I approved the build with readiness 'ready_with_gaps' | operator | sound | Decision D001 ('approved the build with readiness "ready_with_gaps"') is an operator decision. The builder_report and README describe remaining gaps; marking it sound. |
| D002 | I chose Node.js (v24) with Express and LangChain JS for the agent. | prompt | sound | D002 chose Node.js v24 with Express and LangChain JS. This matches the prompt and the implementation (app/src/index.js uses Express; langchain is a dependency in package.json). Events.jsonl shows documentdb-driver skill loads during build. |
| D003 | I chose the official mongodb Node.js driver at mongodb@5.x. | prompt | sound | D003 selected the official mongodb driver at 5.x. package.json lists 'mongodb': '^5.9.0', which matches the decision. events.jsonl shows the documentdb-driver skill being loaded during build, supporting the choice. |
| D004 | I chose OpenAI (environment variable OPENAI_API_KEY) as the LLM provider for LangChain. | model_default | questionable | D004 chose OpenAI and OPENAI_API_KEY as the provider/env var (reason_source: model_default). A .env.example includes OPENAI_API_KEY so the implementation aligns with the decision, but the choice was made by model default rather than an explicit prompt or documented policy. If the team expects Azure OpenAI as default, this decision should be made explicit in guidance or the sample should support multiple providers. |
| D005 | I chose a compound index on { date: 1, category: 1 } for the transactions collection. | prompt | sound | D005 chose a compound index { date: 1, category: 1 }. The seed script (app/scripts/seed.js) creates that index. events.jsonl shows documentdb-indexing skill was loaded. Decision aligns with code and indexing guidance. |

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
| On the checklist, found only when searched for by name | 0 | Public but hard to find. A discoverability gap. |
| Found publicly, not on the checklist | 0 | Add it to the checklist, or check that the public guidance is what the team intends. |
| Known to the model, no public source, not on the checklist | 2 | Agents will act on it from memory. Decide whether it holds for this service, then document it either way. |
| On the checklist and found by open discovery | 6 | Public and discoverable. |

#### Known to the model, no public source, not on the checklist

| Topic | Description | What would help |
|---|---|---|
| Prompt taxonomy validation | Include a fixed taxonomy in the prompt and validate that the model's output strictly matches one of the taxonomy values before writing to the DB. | A short example in the documentdb-natural-language-querying skill or sample README showing output-validation patterns (exact-match and fallback) would let an agent confirm this as a recommended practice. |
| Protect PII before LLM | Protect PII before sending text to an external LLM: redact or hash personally-identifying fields (account numbers, full names) in the prompt or obtain explicit consent and document the data sent to the model. | A small doc in the agent kit stating which fields to redact for fintech samples and a code example of canonical redaction patterns. |

#### On the checklist and found by open discovery

| Topic | Description | Sources |
|---|---|---|
| Connection client reuse | Create a single MongoClient and reuse it as a process-wide singleton; initialize/connect once and do not create a client per request. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Partial index for uncategorized | Use partial indexes (partialFilterExpression) to index only the subset of documents your query filters on to reduce index size and write cost (e.g., index only documents where category does not exist). | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Compound index for aggregation | Create a compound index on { date: 1, category: 1 } to accelerate monthly-spend aggregations grouped by month and category. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Server-side aggregation pipelines | Use server-side aggregation pipelines for rollups (e.g., $group with $dateToString or $dateTrunc to bucket by month) so the grouping runs in the database. | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Idempotent seed scripts | Seed scripts should be idempotent (use upsert or conditional writes) and not run automatically in production; keep them versioned. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Idempotent categorization updates | Make categorization updates idempotent by using conditional updates (e.g. filter { _id:..., category: { $exists: false } } and $set the category), avoiding blind re-writes so multiple runs won't overwrite audited labels. | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

### How the app measures up

#### Violations

| Practice | Category | Evidence | Fix | Source |
|---|---|---|---|---|
| Use partial indexes (partialFilterExpression) to index only the subset of documents your query filters on to reduce index size and write cost (e.g., index only documents where category does not exist). | indexing | app/scripts/seed.js line 9 creates index { date: 1, category: 1 } but no partial index on category:{ $exists:false } is created. | Create a partial index for categorization scans, e.g. coll.createIndex({ date:1, category:1 }, { partialFilterExpression: { category: { $exists: false } } }) in the seed script. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Make categorization updates idempotent by using conditional updates (e.g. filter { _id:..., category: { $exists: false } } and $set the category), avoiding blind re-writes so multiple runs won't overwrite audited labels. | data-consistency | app/src/index.js lines 30-33 and app/scripts/run_categorization.js lines 11-14 call updateOne({ _id: doc._id }, { $set: { category } }) without a conditional filter to ensure category doesn't already exist. The code fetches only uncategorized docs in the query, but the update itself is blind and would overwrite if concurrency or race conditions occur. | Use a conditional update filter to make updates atomic and idempotent, e.g. coll.updateOne({ _id: doc._id, category: { $exists: false } }, { $set: { category } }). | [documentdb-connection](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/connection/SKILL.md) |

#### Could not be assessed

| Practice | Category | What was searched and missing | Source |
|---|---|---|---|
| Protect PII before sending text to an external LLM: redact or hash personally-identifying fields (account numbers, full names) in the prompt or obtain explicit consent and document the data sent to the model. | privacy-llm-security | searches for 'DocumentDB redact PII before LLM' returned no concrete Azure-specific guidance in the installed skills. | prior_knowledge (no public address recorded) |

#### Followed

| Practice | Category | Evidence | Source |
|---|---|---|---|
| Create a single MongoClient and reuse it as a process-wide singleton; initialize/connect once and do not create a client per request. | connection-handling | app/src/db.js lines 9-17 create a single MongoClient and clientPromise used across the app. | [documentdb-driver](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/driver/SKILL.md) |
| Create a compound index on { date: 1, category: 1 } to accelerate monthly-spend aggregations grouped by month and category. | indexing | app/scripts/seed.js lines 8-9 create index { date: 1, category: 1 }. | [documentdb-indexing](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/indexing/SKILL.md) |
| Use server-side aggregation pipelines for rollups (e.g., $group with $dateToString or $dateTrunc to bucket by month) so the grouping runs in the database. | queries-and-aggregation | app/src/index.js lines 12-19 define an aggregation pipeline using $dateToString and $group and executes coll.aggregate(...). | [documentdb-query-optimizer](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/query-optimizer/SKILL.md) |
| Seed scripts should be idempotent (use upsert or conditional writes) and not run automatically in production; keep them versioned. | provisioning-and-seeding | app/scripts/seed.js lines 20-22 use updateOne with upsert:true for each sample row. | [documentdb-local-deployment](https://github.com/Azure/documentdb-agent-kit/blob/main/skills/local-deployment/SKILL.md) |
| Include a fixed taxonomy in the prompt and validate that the model's output strictly matches one of the taxonomy values before writing to the DB. | llm-integration | app/src/agent.js lists TAXONOMY (lines 3-12) and after llm.call applies normalization & exact match rules (lines 33-40) to map the model output to a taxonomy value or fallback to 'Other'. | prior_knowledge (no public address recorded) |

### Reference requirements

12 of 20 met. The builder never saw these; this measures the starter prompt and the skills.

| Requirement | Status | Cause | Evidence | Smallest fix |
|---|---|---|---|---|
| Unit tests run without a live cluster. | not_met | prompt_silent | No test files or test framework found in repository. | Add unit tests using a mock/memory MongoDB (e.g., mongodb-memory-server or mocking the mongodb client) and a simple test runner (Jest), plus CI instructions in README. |
| Infrastructure for the cluster is provided as code, using the Azure DocumentDB resource type. | not_met | prompt_silent | No Terraform/Bicep/ARM templates in the repo; README instructs using an existing cluster. | Add a minimal Bicep or Terraform example that targets Microsoft.DocumentDB/mongoClusters and documents default tier/storage params (marked for sample use only). |
| The agent reaches Azure DocumentDB through LangChain tools (e.g. one tool that fetches uncategorised transactions and one that writes a category back), and the agent decides when to invoke them. | partly_met | builder_error | app/src/agent.js defines the LLM call and prompt; app/src/index.js (POST /run-categorization) queries the DB and calls the agent; there is no LangChain Tool wrapper for DB operations. | Implement DB access as LangChain Tools (e.g. fetch_uncategorized, write_category) and register them in the LangChain agent; or change the prompt requirement to accept direct DB calls. |
| Dependencies are pinned in requirements.txt. | partly_met | prompt_silent | This Node.js sample has app/package-lock.json present (locks versions) but package.json uses caret (^) ranges for dependencies (app/package.json lines 14-19). There is no requirements.txt (Python) – the requirement appears generic. | Use exact versions in package.json or include a note to rely on package-lock.json; alternatively commit a lockfile-based policy in README (recommended minimal change: replace ^ ranges with exact versions or add 'npm ci' guidance). |
| The vector index dimensions match the embedding model's output. | not_checkable | prompt_silent | The sample does not use embeddings or create vector indexes (no embedding code or vector-index creation found). | If you intend to use embeddings, add embedding creation + index creation steps and record the embedding model id/dimensions in .env.example or a config file. |
| The vector index parameters are chosen for the sample's data size, and the README says how to change them for a larger one. | not_checkable | prompt_silent | No vector index is created by the sample. | Only applicable if vectors are used. Provide a short section in README explaining index kinds (ivf/hnsw/diskann) and parameters to tune with data size. |
| /search returns a clear error for an empty query and when the embedding call fails. | not_checkable | prompt_silent | The sample does not implement a /search endpoint. | If you add /search, validate input and return clear errors for empty queries and embedding failures; add tests demonstrating these cases. |
| Search results include the similarity score. | not_checkable | prompt_silent | No search endpoint or embedding scoring is implemented. | If adding search, include similarity/score in the response and add unit tests. |
| A Node.js LangChain agent reads transactions that have not yet been categorised from Azure DocumentDB through a MongoDB-compatible Node.js driver (e.g. the `mongodb` package), selecting documents that carry no category. | met | - | app/src/db.js lines 9-17 (MongoClient created) and app/src/index.js lines 24-33 (coll.find filter for category missing/null/empty). | - |
| The prompt is engineered to instruct the LLM to assign exactly one category from a fixed taxonomy: the taxonomy is defined in the application, listed in the prompt, and the LLM is told to choose only from it. | met | - | app/src/agent.js lines 3-12 (TAXONOMY array) and lines 24-29 (prompt text listing the taxonomy and instructing to choose ONE category). | - |
| The prompt includes each transaction's details (e.g. merchant name and amount) so the LLM reasons over them when choosing the category. | met | - | app/src/agent.js lines 28-29 include Merchant, Amount, Date fields in the prompt. | - |
| The category the LLM assigns is written back to the same transaction document in Azure DocumentDB (e.g. an update that sets a category field on that document). | met | - | app/src/index.js lines 31-33 (updateOne on _id sets category) and app/scripts/run_categorization.js lines 12-14 do the same in CLI mode. | - |
| An HTTP endpoint returns the monthly spend breakdown by category. | met | - | app/src/index.js lines 8-21 implement GET /monthly-spend and return JSON of month + categories. | - |
| That breakdown is computed by an aggregation pipeline run in Azure DocumentDB that groups transactions by month and by category and sums their amounts (e.g. `$group` on a month derived from the transaction date plus the category, with `$sum` of the amount). | met | - | app/src/index.js lines 12-19 define an aggregation pipeline using $dateToString to bucket by month and $group with $sum on amount. | - |
| The connection string and model credentials come from environment variables; none appear in the repository. | met | - | app/.env.example lists DOCUMENTDB_URI and OPENAI_API_KEY; app/src/db.js reads process.env.DOCUMENTDB_URI (lines 5-7); app/src/agent.js reads process.env.OPENAI_API_KEY (lines 14-18). No secrets are committed. | - |
| A .env.example lists every setting with placeholder values. | met | - | app/.env.example lines 2-4 contain placeholders for DOCUMENTDB_URI, OPENAI_API_KEY and PORT. | - |
| One database client is created and reused across requests. | met | - | app/src/db.js lines 9-17 create a single MongoClient and clientPromise; app/src/index.js awaits clientPromise for requests. | - |
| A seed script loads sample data and creates the index, and can be run twice without duplicating data. | met | - | app/scripts/seed.js lines 8-9 createIndex and lines 20-22 use updateOne with upsert: true for idempotent insertion. | - |
| The README covers what the sample shows, prerequisites, setup, run, and clean-up. | met | - | app/README.md contains Overview, What it shows, Prerequisites, Setup, Usage and Cleanup sections (lines 3-33). | - |
| The sample uses the name 'Azure DocumentDB' throughout, and no former or neighbouring product name. | met | - | app/README.md title and text refer to 'Azure DocumentDB'; env var names use DOCUMENTDB_URI; no other product names are used in top-level files. | - |

