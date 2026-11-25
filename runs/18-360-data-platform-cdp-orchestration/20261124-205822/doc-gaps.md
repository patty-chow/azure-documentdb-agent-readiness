# Documentation and tooling gaps: 18-360-data-platform-cdp-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Dedupe + provenance guidance (missing public doc)

- **What was missing:** No Azure DocumentDB Learn page or official guidance prescribing a recommended schema for storing dedupe/merge provenance (which fields to keep, how to store model/prompt metadata, and when to soft-delete originals).
- **Where the agent looked:** Microsoft Learn docs (search terms: 'Azure DocumentDB merge provenance', 'store merge history', 'dedupe audit'), internal skills and repo search.
- **Effect on this build:** The sample deletes merged documents and does not persist a canonical 'merge_history' audit document; an agent cannot confirm a recommended audit schema for LLM-assisted merges.
- **Suggested fix (learn_doc):** A short 'Deduplication and provenance' Learn page recommending: (1) keep a canonical document per customer; (2) create a 'merge_history' collection storing {workflow_run_id, merged_ids, canonical_id, fields_changed, model_name, prompt_hash, timestamp}; (3) example code for writing the audit doc and for rolling back merges if needed.

## [high] Persisting LLM matching metadata

- **What was missing:** No public guidance that codifies persisting model/prompt/version/scores for LLM-assisted matching for reproducibility and audit.
- **Where the agent looked:** Microsoft Learn docs and the documentdb LangChain guidance.
- **Effect on this build:** The sample does not persist model/prompt metadata so LLM-driven decisions are not auditable by default.
- **Suggested fix (learn_doc):** A short guidance page for 'LLM-assisted workflows on DocumentDB' describing what metadata to persist for each LLM call (model name/version, prompt hash, deterministic fallback seed, similarity scores) and an example schema.

## [high] Management tools opt-in behaviour (MCP indexing calls disabled by default)

- **What was missing:** The run encountered a tool error: 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.' There should be a clearly discoverable note about this opt-in requirement where MCP tool usage is documented.
- **Where the agent looked:** Events trace; searched repo for documentdb_create_index usage and general MCP docs.
- **Effect on this build:** Vector index creation via the MCP tool failed during verification; the build could not verify native vector index creation.
- **Suggested fix (discoverability):** A short note in the MCP/documentdb skill docs and the sample README: 'To run management operations via the MCP tools in automated verification runs, set ENABLE_MANAGEMENT_TOOLS=true. If not set, create indexes via the portal or documentdb CLI.'

## [medium] Canonical identifier canonicalization examples

- **What was missing:** No Azure-lead page prescribing canonicalization and hashed keys for identifiers (email/phone) specifically for dedupe scenarios.
- **Where the agent looked:** Microsoft Learn and documentdb skills for 'normalize email', 'hashed key', 'dedupe'.
- **Effect on this build:** The sample normalizes names but does not canonicalize emails (lowercase/hash) by default; an agent will not know recommended canonicalization steps.
- **Suggested fix (learn_doc):** A short 'Canonical identifiers for dedupe' section on the data-modeling guidance page: examples of email normalization, phone normalization, storing hashed keys for equality lookup, index recommendations and sample code.

## [medium] Vector-index demo defaults and tuning

- **What was missing:** A one-page recommendation for default vector-index parameters suitable for demo-sized datasets (tens to hundreds of vectors) showing safe lBuild/lSearch/numLists defaults and an explanation of algorithm trade-offs.
- **Where the agent looked:** documentdb-vector-search skill and Microsoft Learn vector-search pages.
- **Effect on this build:** The builder had to pick reasonable defaults (HNSW/1536 dims) but no concise demo defaults page exists, making consistent choices across samples harder.
- **Suggested fix (discoverability):** Add a 'Vector index quickstart: demo defaults' subsection on the vector-search page with a short table: 'Dataset size → recommended algorithm → example params (lBuild,lSearch,numLists,maxDegree)'.

## [medium] Driver version guidance in quickstarts

- **What was missing:** No single-sentence recommendation in the quickstart indicating the exact driver versions the service supports or recommends for Python/pymongo (and a statement about compatibility when wire protocol versions change).
- **Where the agent looked:** Quickstart and compatibility pages on Microsoft Learn.
- **Effect on this build:** The builder had to pick pinned driver versions; tests and users would benefit from explicit supported-version guidance.
- **Suggested fix (discoverability):** Add a short 'Supported driver versions' note on the top of the quickstart and vector-search pages with tested pymongo versions and guidance on reading the cluster's supported wire protocol.

