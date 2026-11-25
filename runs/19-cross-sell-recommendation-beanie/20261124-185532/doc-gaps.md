# Documentation and tooling gaps: 19-cross-sell-recommendation-beanie

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Canonical unordered pair key & schema

- **What was missing:** No public, discoverable guidance that prescribes a canonical unordered-pair key name or canonicalization strategy (e.g., sorted tuple -> 'pair_key' or hashed composite) for co-purchase pair documents.
- **Where the agent looked:** Searched installed skills and Microsoft Learn; practice discovery searches returned no authoritative example named 'canonical_pair_key' (see searches_with_no_useful_result entries).
- **Effect on this build:** The builder must invent the canonicalization (naming, ordering) strategy. Different authors may pick inconsistent field names (product_a_id/product_b_id vs canonical pair_key) which complicates idempotent upserts and unique indexing.
- **Suggested fix (naming_or_disambiguation):** Add a short 'Canonical pair keys' page to the Azure DocumentDB samples docs describing a recommended schema (fields: pair_key: '<minId>_<maxId>' or hashed canonical key, product_ids array, co_purchase_count:int, embedding:float[], embedding_model:string, embedding_dims:int, created_at). Example createIndex command for the unique key and sample upsert pattern using $inc + upsert.

## [high] Affinity scoring formula for cross-sell

- **What was missing:** No public guidance on an affinity formula combining co_purchase_count and vector similarity for cross-sell ranking. The sample prompt required an 'affinity score' but did not define how to combine components.
- **Where the agent looked:** Searches of Azure docs and installed vector-search skills; no canonical scoring formula found for combining frequency and similarity.
- **Effect on this build:** Builder must invent a heuristic; different heuristics lead to inconsistent or non-reproducible ranking. This is a common source of surprises in gallery samples.
- **Suggested fix (learn_doc):** A short guidance page 'Ranking for RAG & cross-sell' recommending a normalized weighted-sum: affinity = w_sim * (normalized_cosine) + w_count * (normalized_log_co_purchase_count). Include recommended defaults for demo datasets and instructions for tuning weights and unit tests to validate behavior.

## [high] Idempotent seed / upsert pattern

- **What was missing:** No small reference snippet in public docs showing an idempotent seed script pattern for building co-purchase counters (aggregation + atomic upsert) that can be re-run safely.
- **Where the agent looked:** Installed skills (query-optimization, indexing) and Microsoft Learn, no seed-pattern snippet located.
- **Effect on this build:** Without an idempotent seed example, implementers may insert duplicate Orders or create non-idempotent updates; the sample's 'run twice' promise is at risk.
- **Suggested fix (sample_or_quickstart):** Add a tiny sample script demonstrating: (1) insertOrdersIfMissing (idempotent upsert by order_id), (2) aggregation pipeline to compute unordered pairs, and (3) atomic upsert using updateOne({pair_key}, {$inc:{co_purchase_count:n}}, upsert:true). Include a 'dry-run' flag and transaction-safe pattern where available.

## [high] Comprehensive .env.example & env var names

- **What was missing:** No public naming convention for the OPENAI model env var, embedding model name, or SAMPLE database name; the prompt referenced DOCUMENTDB_URI but did not enumerate all env variables.
- **Where the agent looked:** Quickstart docs include MONGODB_URI examples, but nothing that enumerates OPENAI_EMBEDDING_MODEL and model-dimension mapping in this sample context.
- **Effect on this build:** Agents and builders will pick different env var names and defaults; index-dimension mismatches may silently break vector search.
- **Suggested fix (discoverability):** Add a template .env.example in the samples repo showing DOCUMENTDB_URI, DATABASE_NAME, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, EMBEDDING_DIMS (auto-filled from model), INDEX_KIND, INDEX_PARAMS, and explain which are required and which optional.

## [high] Beanie & async client guidance (Motor vs AsyncMongoClient)

- **What was missing:** The quickstart docs recommend PyMongo's AsyncMongoClient for Beanie 2.x; this contradicts older memory recommending Motor. A prominent, discoverable note is needed.
- **Where the agent looked:** documentdb-connection and Beanie quickstarts in installed skills; the contradiction was found in discovery.
- **Effect on this build:** The builder picked Motor (D004) despite guidance; an agent defaulting to Motor will implement suboptimal or incompatible client code.
- **Suggested fix (discoverability):** Make the Beanie quickstart's recommendation more prominent: 'If you are using Beanie 2.x, use PyMongo AsyncMongoClient; do not use Motor for new code.' Add a short migration note and code example.

## [medium] Index-dimension mapping for common embedding models

- **What was missing:** No small authoritative table mapping common OpenAI embedding models (text-embedding-3-small, text-embedding-3-large, etc.) to index 'dimensions' used in cosmosSearch createIndexes examples.
- **Where the agent looked:** Vector-search skill docs explain 'dimensions must match' but no compact table mapping model name -> dims was found.
- **Effect on this build:** Builder assumed 1536 for text-embedding-3-small; without a reference table mistakes cause index/dimension mismatch.
- **Suggested fix (learn_doc):** A one-page mapping table in Vector Search docs listing popular embedding providers and model names with their output vector dims and recommended similarity metric.

## [medium] Return similarity and component scores in search responses

- **What was missing:** No sample guidance that the API should return both the database search score and the co_purchase_count (or formula components) so callers can explain recommendations.
- **Where the agent looked:** Search of existing quickstarts and vector-search docs.
- **Effect on this build:** Without guidance, samples may return only IDs and an opaque rank, reducing developer utility and testability.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule recommending that gallery cross-sell samples return: candidate_id, affinity_score, vector_similarity, co_purchase_count, and explanation text. Include sample JSON schema.

## [medium] Unit-test patterns for vector + DB samples

- **What was missing:** A short pattern showing how to run unit tests for vector-search samples offline (mocking OpenAI and DocumentDB calls) was not found as a compact recipe.
- **Where the agent looked:** Installed skills and Microsoft Learn.
- **Effect on this build:** Without a test pattern, implementers may write tests that require a live cluster making CI and contributor experience difficult.
- **Suggested fix (sample_or_quickstart):** Add a 'Testing' section to the sample quickstart showing how to mock the embedding API and Mongo driver (pytest + respx/httpx for embeddings, pytest-mock for pymongo Async client), with example test that asserts ranking logic.

