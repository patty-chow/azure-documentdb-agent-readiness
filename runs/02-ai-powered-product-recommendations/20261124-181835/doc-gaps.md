# Documentation and tooling gaps: 02-ai-powered-product-recommendations

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] LlamaIndex Node integration guidance

- **What was missing:** No public, discoverable guidance or agent-kit skill shows how to integrate LlamaIndex Node bindings with Azure DocumentDB's vector store (DiskANN) or provides a copy-paste adapter template.
- **Where the agent looked:** Agent kit skills, Microsoft Learn vector-search docs, and run-time readiness notes (events.jsonl searches for LlamaIndex/Node bindings).
- **Effect on this build:** The builder chose not to use LlamaIndex and implemented an equivalent lightweight agent pipeline. This means the published sample does not demonstrate LlamaIndex usage the starter prompt requested.
- **Suggested fix (agent_kit_rule):** Add a skill 'llamaindex-node' to the agent kit with: (1) a minimal example that constructs a LlamaIndex index over DocumentDB's DiskANN-backed collection; (2) an adapter module that shows how to translate LlamaIndex semantics into cosmosSearch queries (createIndexes + $search) and how to persist metadata; (3) a note on required npm package names/versions and an example package.json.

## [high] Embedding-model → index-dimension guidance

- **What was missing:** Explicit examples mapping popular embedding models to index 'dimensions' and a recommended env var name convention for embedding model/dim pairs.
- **Where the agent looked:** documentdb-vector-search skill, Microsoft Learn vector docs, readiness notes.
- **Effect on this build:** Builder assumed text-embedding-3-small → 1536 dims; the run succeeded. Without explicit guidance, other authors may pick mismatched dims and silently corrupt nearest-neighbour behavior.
- **Suggested fix (discoverability):** A brief table in the vector-search quickstart: 'Model name → default dims' (e.g., OpenAI text-embedding-3-small:1536, text-embedding-3-large:3072, etc.), and a note: 'Store embeddingModel and embeddingDims with each document; validate dims on ingest.'

## [high] Retry-and-throttle helpers

- **What was missing:** A ready-to-use retry helper that honours Retry-After and applies exponential backoff/jitter for DocumentDB SDK calls and external embedding/LLM calls.
- **Where the agent looked:** Throttling docs and documentdb-query-optimizer and connection skills; no packaged helper shipped in the agent kit for Node.js sample authors.
- **Effect on this build:** Seed script uses batched insertMany but does not implement retries for 429s, increasing the risk of failed or partial ingestion under throttling.
- **Suggested fix (mcp_tool_or_description):** Ship a small Node.js helper (retryWithBackoff) as part of the agent-kit or sample template showing how to inspect HTTP 429/Retry-After and how to backoff and retry DB and HTTP calls.

## [high] Idempotent seeding and unique-index guidance

- **What was missing:** A recommended pattern and a code snippet that: create unique indexes on productId, use bulkWrite upserts for idempotent seeds, and document how to re-run the seed safely.
- **Where the agent looked:** documentdb-indexing skill and agent-kit samples; guidance present in pieces but not a one-shot snippet in the kit.
- **Effect on this build:** The seed works but is not idempotent; repeated runs may create duplicates if unique indexes are not present or upsert not used.
- **Suggested fix (sample_or_quickstart):** Add an 'idempotent seed' section to the seed example showing createIndex({productId:1},{unique:true}) and using bulkWrite with upsert:true to avoid duplicates.

## [medium] Index tuning defaults & copy-paste createIndexes

- **What was missing:** A small copy-paste 'createIndexes' runCommand example with recommended DiskANN parameters for a sample-size catalog (10k) and a short explanation of recommended lBuild/lSearch values and their effect.
- **Where the agent looked:** documentdb-vector-search skill and Microsoft Learn vector-search docs; the guidance exists but a ready-to-copy snippet for sample authors was not included in the local sample kit docs.
- **Effect on this build:** The sample created a DiskANN index with defaults; runtime behaved, but authors and readers may not know which params to change for larger datasets.
- **Suggested fix (learn_doc):** A short page named 'Sample: create DiskANN index for product catalog' containing the createIndexes runCommand JSON for DiskANN and suggested defaults for NUM_PRODUCTS=10k (e.g., lBuild=40, maxDegree=64) and recommended query-time lSearch values for k=10. Include a note on expected build time and memory.

## [medium] Session TTL index example

- **What was missing:** A concrete example (code snippet) that creates a TTL index on the sessions collection (e.g., db.sessions.createIndex({ createdAt:1 }, { expireAfterSeconds: 3600 })).
- **Where the agent looked:** documentdb-indexing skill and sample repo; skill documents TTL semantics but sample lacked the createIndex snippet.
- **Effect on this build:** Sessions are persisted but there is no automatic expiry defined; long-term run could accumulate session documents.
- **Suggested fix (sample_or_quickstart):** Add a short 'create session TTL index' snippet in seed.js (or README) that shows createIndex with expireAfterSeconds and explains the Date field requirement.

## [medium] Guidance for using deterministic synthetic embeddings in tests

- **What was missing:** Public guidance that explicitly recommends deterministic synthetic embeddings for CI and local dev when external embedding APIs are unavailable.
- **Where the agent looked:** Searches for 'deterministic synthetic embeddings' returned no authoritative guidance (discovered_practices shows this as prior_knowledge_only).
- **Effect on this build:** The builder implemented deterministic synthetic embeddings (good), but this is a prior-knowledge pattern that is not documented for Azure DocumentDB authors; agents may not automatically adopt the pattern.
- **Suggested fix (learn_doc):** A short dev/testing guidance page: 'Testing vector apps without external APIs' that covers deterministic embeddings, seeding, and env flags to avoid external calls.

