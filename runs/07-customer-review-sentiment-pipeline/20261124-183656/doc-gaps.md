# Documentation and tooling gaps: 07-customer-review-sentiment-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Beanie async-driver compatibility

- **What was missing:** A short authoritative mapping between Beanie releases and which async Mongo client to use (Motor vs PyMongo AsyncMongoClient), including example init code for both paths and recommended pinned versions.
- **Where the agent looked:** Loaded documentdb-driver and documentdb-connection skills, quickstart search results (events.jsonl lines ~12, ~26), web searches for Beanie + AsyncMongoClient but no single authoritative mapping was found in the installed skills.
- **Effect on this build:** Builder chose Motor (decision D004) while the connection skill and Beanie quickstart point to PyMongo's AsyncMongoClient; incompatibility risk remains and blocked a confident implementation choice.
- **Suggested fix (learn_doc):** A one-page 'Beanie compatibility' doc showing: (a) Beanie 1 historically used Motor with sample code, (b) Beanie 2 supports PyMongo AsyncMongoClient with code snippet (from beanie quickstart), (c) pinned package versions to use in requirements.txt for each approach, and (d) a recommended default for Azure DocumentDB samples (with rationale). Include copyable snippets for both driver initializations and a note on which Beanie release to pin.

## [high] Concurrency limits for OpenAI + batching guidance

- **What was missing:** No public DocumentDB guidance showing an example concurrency control pattern (asyncio.Semaphore) for calling OpenAI and separate DB write batching guidance tailored to DocumentDB client patterns.
- **Where the agent looked:** Searches for 'Azure DocumentDB OpenAI concurrency semaphore' and pipeline concurrency patterns returned no useful Microsoft Learn guidance (see discovered_practices.searches_with_no_useful_result).
- **Effect on this build:** The builder had to rely on prior knowledge. Without an example, agents may implement naive parallelism that triggers OpenAI or DB rate limits or causes high small-write load on the cluster.
- **Suggested fix (agent_kit_rule):** An agent-kit rule and a short sample snippet that enforces: use asyncio.Semaphore for OpenAI calls (configurable concurrency limit), and batch DB writes (e.g., bulkWrite with configurable batch size). Include recommended default limits for sample-size workloads.

## [medium] OpenAI model & env var guidance

- **What was missing:** No agent-kit guidance on which OpenAI model(s) to use for sentiment classification and theme extraction, nor the canonical env var names for model and API key in DocumentDB samples.
- **Where the agent looked:** Searches across installed skills and quickstarts; none provided OpenAI model guidance (events.jsonl shows load_skill calls but no OpenAI guidance).
- **Effect on this build:** Builder used a model-default (gpt-3.5-turbo) and OPENAI_API_KEY (decision D005). Lack of guidance risks inconsistent examples or using an unsuitable model for advanced samples (e.g., embeddings or higher-quality classification).
- **Suggested fix (learn_doc):** Add a short 'OpenAI in samples' page describing recommended defaults: classification → gpt-3.5-turbo (cost-effective) or gpt-4o for higher quality, embeddings → text-embedding-3-small (dimensions: 1536 or the chosen model's dims), and the env vars to use (OPENAI_API_KEY, OPENAI_MODEL_CLASSIFIER, OPENAI_EMBEDDING_MODEL). Include small code snippets and a note to document embedding dims if embeddings are used.

## [medium] Beanie field type and index guidance for DocumentDB

- **What was missing:** No public guidance in the DocumentDB skillset about explicit Pydantic/Beanie field types for embeddings and numeric scores, or about doing index creation at model/migration time for Beanie models.
- **Where the agent looked:** Searches for 'Beanie index create_index beanie Azure DocumentDB' and loaded documentdb-indexing/documentdb-driver; no explicit sample-level guidance found.
- **Effect on this build:** The agent could not confirm whether to declare embeddings as List[float] and how to create indexes in a Beanie migration; this complicates safe, reproducible sample code.
- **Suggested fix (sample_or_quickstart):** A short Beanie quickstart sample showing: Pydantic fields for embedding (List[float]), sentiment_score (float), tags (List[str]), index annotations or an example migration script that calls create_index/create_indexes, and a note to pin field types explicitly to avoid implicit BSON typing differences.

## [medium] Tests without live cluster (local gateway example)

- **What was missing:** A small example/test harness demonstrating unit tests that run without a live cluster, using the DocumentDB Gateway Docker image or mocking the driver.
- **Where the agent looked:** documentdb-local-deployment skill (gateway image info found) but no sample tests illustrating how to run CI tests offline.
- **Effect on this build:** No tests were added and the builder did not produce a test harness; agents lack a standard pattern to author tests that don’t require a live cluster.
- **Suggested fix (sample_or_quickstart):** Add a test quickstart showing pytest + pytest-asyncio tests that either (a) run against the DocumentDB Gateway Docker image (instructions to start the gateway on port 10260 with SKIP_INIT_DATA), or (b) use mocked OpenAI and a motor/pymongo testing client. Include example CI commands.

