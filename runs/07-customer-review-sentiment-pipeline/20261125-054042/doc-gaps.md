# Documentation and tooling gaps: 07-customer-review-sentiment-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Driver/version compatibility guidance

- **What was missing:** A short authoritative sentence in the quickstart showing the tested combinations of Beanie/Motor/PyMongo (exact pins) that are known to work with Azure DocumentDB, and a statement that Beanie 2 prefers PyMongo's AsyncMongoClient over Motor in some quickstarts.
- **Where the agent looked:** Searched the installed documentdb Beanie quickstart and the Microsoft Learn 'Quickstart: Connect Beanie to Azure DocumentDB' (learn_microsoft_docs_search results). The quickstart references tested versions in text but the agent discovery did not surface a concise short matrix for this sample's pinned set.
- **Effect on this build:** The builder encountered ImportError and multiple pins had to be iterated (beanie/pymongo/motor), leading to extra build iterations and a pinned pymongo==4.6.0 in requirements. This caused additional decision churn (D014 -> D019 -> D020).
- **Suggested fix (learn_doc):** A short 'Tested client matrix' snippet in the Beanie quickstart and agent-kit that lists 'beanie==1.13.0, motor==3.1.2, pymongo==4.6.0' (or the current tested matrix), with notes on how to reproduce import errors and where to pin. Also add a one-line mention that some older Beanie quickstarts used Motor vs AsyncMongoClient and when to prefer one.

## [high] Single-client pattern guidance (discoverability)

- **What was missing:** Although the connection skill documents singleton client patterns, an explicit code snippet showing a small module-level AsyncMongoClient singleton and a get_motor_client() helper was not in a discoverable top-level sample page for Python/Beanie.
- **Where the agent looked:** documentdb-connection skill and Beanie quickstart; the skill contains guidance but a short copy-paste snippet for Python/Beanie was not prominent.
- **Effect on this build:** The builder implemented init_db that constructs a client per call (src/sample_retail_07/db.py), causing potential resource leaks and a missing get_motor_client() helper referenced by create_indexes.py and other helpers.
- **Suggested fix (discoverability):** Add a 10-line snippet to the Beanie quickstart showing module-level client reuse: _CLIENT: Optional[AsyncMongoClient]=None; def get_motor_client(): global _CLIENT; if not _CLIENT: _CLIENT = AsyncMongoClient(uri, serverSelectionTimeoutMS=20000, maxPoolSize=50); return _CLIENT. Show how to call init_beanie(client[DATABASE]) once at startup.

## [high] Retry guidance for writes & LLM calls

- **What was missing:** A succinct example demonstrating exponential backoff retries for transient errors (HTTP 429/5xx and DB transient network errors) and guidance that Azure DocumentDB does not provide driver-level retryable writes.
- **Where the agent looked:** documentdb-connection skill and azure-deployment skill; the connection skill recommends retries but there's no compact example combined with async OpenAI calls.
- **Effect on this build:** No retry/backoff was implemented in the enrichment pipeline. This makes the sample brittle in the face of transient network errors or rate limits and contradicts the expectation that production-ready samples handle retries.
- **Suggested fix (learn_doc):** A cookbook page: 'Retries and idempotency for DocumentDB + LLMs' showing (1) how to wrap OpenAI HTTP calls with exponential backoff (tenacity or custom), (2) how to apply idempotent upsert semantics for retryable writes, and (3) example values for backoff/limits.

## [high] Index vs aggregation example mismatch (docs + sample)

- **What was missing:** A short example in the indexing quickstart that shows indexing for grouping by a label field and a numeric score field with the exact index shapes to use (compound index examples that match common aggregation keys).
- **Where the agent looked:** documentdb-indexing skill and Beanie quickstart; the skill has index-shape cookbook but the sample's aggregation used sentiment_label while the index used sentiment_score causing a mismatch.
- **Effect on this build:** The sample ended up with an index that does not accelerate the provided aggregation pipeline causing the sample to perform suboptimally and confusing readers.
- **Suggested fix (learn_doc):** Add a 'Group-by example' subsection to index-shape cookbook showing 'When you group on sentiment_label, add index (product_id, sentiment_label)' and include a short Beanie/IndexModel snippet.

## [medium] .env.example completeness and canonical env var names

- **What was missing:** .env.example omitted some env vars the code expects (MODEL, DATABASE_NAME/CONCURRENCY naming mismatch across src vs top-level scripts). The run environment documentation expects DOCUMENTDB_URI as the canonical env var name.
- **Where the agent looked:** Repo files (app/.env.example, src scripts), the Beanie quickstart, and readiness notes about DOCUMENTDB_URI naming.
- **Effect on this build:** The missing placeholders caused minor confusion (two run_pipeline implementations expect different env var names) and required cross-checking code to run scripts. It also risks user error when following README without updating .env.example.
- **Suggested fix (agent_kit_rule):** Standardize and publish canonical env var names for samples (DOCUMENTDB_URI, OPENAI_API_KEY, MODEL, OPENAI_CONCURRENCY, DATABASE_NAME) and require .env.example include them. Agent-kit rule: 'All Python samples must include MODEL and DATABASE_NAME placeholders in .env.example and use DOCUMENTDB_URI as canonical DB URI name.'

## [medium] Prior-knowledge-only practices left undocumented

- **What was missing:** Several practices the model carried from general MongoDB memory but for which no Azure-DocumentDB public page exists (e.g., recommended concurrency defaults for LLM calls, structured-tags vs. text search tradeoffs, testing-with-mock patterns).
- **Where the agent looked:** Agent skill discovery and web searches (see 'searches_with_no_useful_result' list).
- **Effect on this build:** Agent relied on prior knowledge to choose defaults (concurrency=5, mock fallback) that are sensible but not verifiably recommended by public docs. This increases the chance different builders will pick incompatible defaults.
- **Suggested fix (learn_doc):** Small guidance pages: 'LLM concurrency considerations for DocumentDB samples' and 'Testing LLM-backed pipelines in CI', each with recommended defaults and short examples.

## [medium] Missing get_motor_client helper in module examples

- **What was missing:** Some sample helper scripts (create_indexes.py, aggregations.py) rely on get_motor_client but the sample db module originally lacked a single exported get_motor_client. This mismatch suggests the agent-kit should publish a recommended db helper template.
- **Where the agent looked:** Repo scripts (src/sample_retail_07/scripts/create_indexes.py), src/db.py edits in events.
- **Effect on this build:** create_indexes.py and aggregations.py reference get_motor_client which was not implemented in some code iterations, causing those scripts to be broken until the helper was added or client usage standardized.
- **Suggested fix (discoverability):** Add a short 'db utility' snippet to the Beanie quickstart and agent-kit showing get_motor_client + init_beanie usage and note the return types.

