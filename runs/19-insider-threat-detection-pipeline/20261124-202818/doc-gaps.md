# Documentation and tooling gaps: 19-insider-threat-detection-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model & dimensions guidance

- **What was missing:** No authoritative guidance in the sample or product docs listing recommended OpenAI embedding models and the dimensions the sample should use. The builder picked text-embedding-3-small / 1536 dims from model defaults (a model_default decision).
- **Where the agent looked:** Microsoft docs and installed documentdb skills; searches for OpenAI model dims were not applicable because OpenAI docs are external.
- **Effect on this build:** The builder made a reasonable assumption (1536 dims) and set EMBEDDING_DIMS accordingly; had an incorrect dimension been chosen, the vector index creation step would have failed or produced mis-sized vectors.
- **Suggested fix (learn_doc):** Add a short 'Embedding model and index dimensions' page to the gallery guidance and the documentdb-agent-kit that: (1) lists recommended embedding models for samples (text-embedding-3-small, text-embedding-3-large), (2) states each model's output dimension, (3) shows how to set EMBEDDING_DIMS and OPENAI_EMBEDDING_MODEL in .env.example, and (4) warns about mixing models in one collection. Include copy-paste examples for the common choices.

## [high] Persist-without-embedding / backfill pattern

- **What was missing:** No public guidance (Microsoft docs or skill pages) describing the recommended pattern for continuing ingestion when a third-party embedder (OpenAI) is temporarily unavailable and how to mark records for later backfill.
- **Where the agent looked:** documentdb-vector-search skill, vector-search docs, and targeted searches for 'embedder backfill Azure DocumentDB'.
- **Effect on this build:** The sample implements a pragmatic approach (ingest persists empty embedding if embedder fails), but this pattern is a product-level judgement that agents will default to without authoritative guidance. Without guidance agents may either block ingestion or lose the ability to backfill reliably.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and a short guidance doc: 'When embedder unreachable, persist features with embedding:null or embedding:[] and set needs_embedding:true; provide a backfill job example and an index on needs_embedding for efficient backfill queries.'

## [high] IaC example for Azure DocumentDB mongoClusters

- **What was missing:** No IaC (Bicep/Terraform) example that targets Microsoft.DocumentDB/mongoClusters in the repo or in the agent-kit templates for gallery samples.
- **Where the agent looked:** project files and documentdb-azure-deployment skill resources; Microsoft Learn templates for mongoClusters.
- **Effect on this build:** The run environment provided an existing cluster, but a builder reusing this sample would not have an in-repo IaC snippet to provision a cluster. This increases friction for reproducible demos and for automated CI-based demos.
- **Suggested fix (mcp_tool_or_description):** Ship a minimal Bicep/Terraform example that creates a Microsoft.DocumentDB/mongoClusters resource with parameters for tier, storage, and region. Include a short README section showing how to deploy it (az cli or az deployment) and a note about default, low-cost parameters for demo use.

## [medium] Binary float32 embedding storage guidance

- **What was missing:** No public guidance (in Microsoft docs or installed skills) stating whether embeddings should be stored as float32 binary arrays or JSON numbers for optimal storage/precision in Azure DocumentDB.
- **Where the agent looked:** Microsoft Learn vector-search docs, documentdb-vector-search skill resources, and targeted searches for 'float32 embedding storage Azure DocumentDB'.
- **Effect on this build:** The sample persists embeddings as JSON arrays of Python floats. That works for the demo, but production performance/size/precision trade-offs remain unclear to builders and could cause inefficiencies or precision loss at scale.
- **Suggested fix (learn_doc):** A short 'Embedding storage format' guidance page stating the recommended numeric type (float32 vs double), examples of storing embeddings in BSON/float32, driver considerations, and sample code to pack/unpack float32 arrays if beneficial.

## [medium] Index tuning guidance for gallery samples

- **What was missing:** The sample creates a vector-ivf index with algorithmParameters.nlist=1024 but README lacks clear guidance on how to change index parameters for larger datasets (numLists/nlist/efConstruction/efSearch).
- **Where the agent looked:** create_indexes.py, README.md, documentdb-vector-search skill and Microsoft docs (vector-search).
- **Effect on this build:** The sample chose sensible defaults for a small dataset, but a developer reusing the sample for larger data might not know which parameters to change or what defaults to pick, possibly producing a suboptimal index.
- **Suggested fix (discoverability):** Add an 'Index tuning' section to README and include copy-paste templates for vector-ivf, vector-hnsw and vector-diskann with recommended defaults for small/medium/large workloads and an explanation of the parameters to adjust (numLists, efConstruction, m, efSearch).

## [medium] README: index & threshold tuning and clean-up

- **What was missing:** The README lacks explicit instructions on (A) how to tune vector index parameters for larger datasets, (B) how to tune anomaly threshold selection, and (C) explicit clean-up steps to remove created collections/resources.
- **Where the agent looked:** app/README.md and documentdb-agent-kit resources.
- **Effect on this build:** Users re-running the sample may not know how to adapt index parameters or thresholds for their data and may not clean up sample collections.
- **Suggested fix (discoverability):** Update README with (1) index-tuning guidance and where to change parameters, (2) guidance on selecting/tuning ANOMALY_COSINE_THRESHOLD (advise empirical tuning or statistical methods), and (3) explicit clean-up commands (drop collections or run a cleanup script).

