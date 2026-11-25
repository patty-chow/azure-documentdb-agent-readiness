# Documentation and tooling gaps: 17-rare-disease-literature-search

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & dimension guidance

- **What was missing:** No product-level guidance telling sample authors which embedding provider/model to choose and what default dimensions to assume for a PubMed-abstract LlamaIndex sample.
- **Where the agent looked:** Installed documentdb-* skills and Microsoft Learn pages (see readiness_findings and skill resources loaded during the run).
- **Effect on this build:** Builder made a model_default decision (text-embedding-3-small / 1536 dims). That is internally consistent, but agents working from memory may choose incompatible dims and create a mismatched index. The sample requires the user to keep the env dims and model aligned.
- **Suggested fix (learn_doc):** A short guidance page 'Embedding model choices for DocumentDB samples' that: (1) lists recommended embedding models for small gallery samples with dims (e.g., OpenAI text-embedding-3-small: 1536), (2) explains that index dimensions must equal model output dims, (3) shows a code snippet to validate embedding length at runtime and fail fast or rebuild index, (4) advises how to change OPENAI_EMBEDDING_DIMS and re-run create_index.py.

## [high] Error-handling for embedding & empty queries

- **What was missing:** The starter prompt and skills did not force the builder to implement explicit input validation and user-facing error messages for empty queries or failed embedding/LLM calls.
- **Where the agent looked:** Repo code and installed skills; no sample-level rule enforced error-handling for the HTTP API.
- **Effect on this build:** The /query endpoint will raise unhandled exceptions for empty input or failed embedding/ChatCompletion calls, yielding unclear server errors to users.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and a small README snippet requiring API endpoints to validate inputs and handle external-API exceptions clearly (HTTP 400 for empty queries, HTTP 502/503 for failed upstream embedding/LLM calls), plus a minimal try/except wrapper example for the openai embedding/ChatCompletion calls.

## [high] Dependency pinning policy for gallery samples

- **What was missing:** No enforced sample-level policy or guidance requiring dependencies to be pinned to exact test-verified versions.
- **Where the agent looked:** Repo and installed skills; README does not advise pinning and requirements.txt uses minimum versions.
- **Effect on this build:** The builder chose flexible minimum version constraints which reduces reproducibility and risks runtime incompatibilities in CI or on users' machines.
- **Suggested fix (agent_kit_rule):** A short agent-kit rule and README checklist item: 'Pin critical dependencies (llama-index, pymongo, openai) to test-verified exact versions in requirements.txt or provide a constraints file; update pins when intentionally upgrading and document test results.' Provide example pinned requirements and a brief procedure for updating pins.

## [medium] Index tuning & README guidance

- **What was missing:** README lacks guidance on how to tune vector-index parameters (lBuild, maxDegree) for larger data sizes and trade-offs.
- **Where the agent looked:** Repository README and installed skills; the vector-search skill documents parameters but the sample README doesn't surface tuning advice.
- **Effect on this build:** The sample uses conservative defaults but does not educate users how to scale the index for larger corpora; users may copy defaults that are suboptimal for production.
- **Suggested fix (discoverability):** Add a subsection to the sample README titled 'Index tuning for larger datasets' linking to documentdb-vector-search SKILL.md and summarizing recommended maxDegree/lBuild ranges for small/medium/large corpora plus an example command showing how to re-create the index with new parameters.

## [medium] Chunk size and token-count recommendation

- **What was missing:** No public DocumentDB guidance in the installed skills prescribes a chunk size tuned to embeddings/tokenization; this practice was prior knowledge only.
- **Where the agent looked:** Searches in installed skills and Microsoft Learn (see discovered_practices notes).
- **Effect on this build:** Builder picked chunk_size=512 and overlap=50 by convention; without explicit guidance maintainers may not choose an optimal chunk size for retrieval quality vs cost.
- **Suggested fix (learn_doc):** A short note in the sample README advising a default token-based chunk size for the sample embedding model (e.g., ~512 tokens), why overlap matters, and a small script/flag to record token counts for each chunk to support tuning experiments.

## [medium] Batch size guidance for bulk writes

- **What was missing:** No public guidance in installed skills about recommended batch sizes for DocumentDB bulk writes for vector ingestion.
- **Where the agent looked:** Installed skills and Microsoft Learn; searches for 'DocumentDB bulk_write batch size' returned no useful DocumentDB-specific guidance.
- **Effect on this build:** Ingest uses bulk_write but leaves batch sizing implicit; users might choose too-large batches for their cluster tier and experience timeouts or resource contention.
- **Suggested fix (discoverability):** A short 'Bulk ingestion' page in the docs or agent-kit describing recommended batch sizes (e.g., 500–2000 for high-throughput clusters, 100–500 for smaller tiers), recommendations to use ordered=False, and an example with PyMongo bulk_write and retry/backoff.

## [medium] Infrastructure IaC for DocumentDB clusters

- **What was missing:** A minimal Bicep/Terraform example to provision an Azure DocumentDB mongoClusters resource as part of the sample.
- **Where the agent looked:** Repository and installed skills; README instructs using an existing cluster but provides no IaC artifact in repo.
- **Effect on this build:** The sample assumes an existing cluster; users who want to reproduce the demo need to consult external quickstarts and may select the wrong resource type (databaseAccounts vs mongoClusters).
- **Suggested fix (sample_or_quickstart):** Add a minimal Bicep and Terraform example in a /infra folder that provisions a low-cost mongoClusters M-series cluster with variables for tier/region and a note: 'Use this only for development; billing applies'. Include an explicit note about using Microsoft.DocumentDB/mongoClusters (not databaseAccounts).

## [medium] Decisions recorded as model_default

- **What was missing:** Several build-time choices (embedding model, LLM model, and dependency pinning policy) were 'model_default' decisions rather than grounded in product docs.
- **Where the agent looked:** decisions.jsonl and readiness notes.
- **Effect on this build:** Model_default decisions led to configuration choices (text-embedding-3-small, gpt-3.5-turbo, flexible requirements) that maintainers should review for correctness, especially for a biomedical sample.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule requiring explicit justification (in README or decisions.jsonl) when choosing a model_default for embedding/LLM/models or dependency pinning; require a short rationale and test notes for medical domain samples.

## [low] MCP management tool opt-in documentation

- **What was missing:** During the run the documentdb_create_index MCP tool failed with 'Management tools are disabled by default. Set ENABLE_MANAGEMENT_TOOLS=true to opt in.' There is no local repo note documenting that MCP management tools may be disabled by default and how to opt in.
- **Where the agent looked:** events.jsonl and the repo README; the run captured the tool error but the README doesn't explain the opt-in flag.
- **Effect on this build:** The builder fell back to PyMongo runCommand to create the index; users expecting MCP-based index creation may see the same error and not understand the opt-in.
- **Suggested fix (discoverability):** Add a short note in README.md under 'Index creation' explaining MCP management tools may be disabled and include the env note: 'If MCP management tools are disabled, set ENABLE_MANAGEMENT_TOOLS=true in the MCP server config or use the included create_index.py which uses the driver as a fallback.'

