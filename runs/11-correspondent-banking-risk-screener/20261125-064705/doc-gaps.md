# Documentation and tooling gaps: 11-correspondent-banking-risk-screener

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Server-side vector index creation

- **What was missing:** A verified, copy-paste createIndex example for the managed Azure DocumentDB cluster (exact createIndex parameters, option names and an example for HNSW/IVF/DiskANN).
- **Where the agent looked:** Repository files and run environment; no external documentation server was reachable in this run (documentation_search_available: false).
- **Effect on this build:** The builder avoided creating server-side vector indexes and implemented client-side similarity as a fallback. This prevents the sample from demonstrating server-side $search/cosmosSearch vector queries and leaves index tuning to users.
- **Suggested fix (mcp_tool_or_description):** Agent kit / documentation page titled 'Create a vector index on Azure DocumentDB (MongoDB 7 style)'. Outline: short intro, exact createIndex code snippets for HNSW, IVF and DiskANN with parameters (dimensions variable), example Python pymongo call to create index, verification commands to list indexes, and a tested script that can be run against the managed cluster. Provide an opt-in env var example (ENABLE_VECTOR_INDEX=true) and a note about costs and recommended parameters for small/medium/large datasets.

## [high] Embedding model & dimensions authoritative statement

- **What was missing:** A single canonical place documenting the chosen embedding model and its vector dimension (so index dimension and synthetic fallbacks must match it).
- **Where the agent looked:** app/src/embeddings.py and other repository files; no external docs reachable.
- **Effect on this build:** Builder selected text-embedding-3-small and used 1536 dims, but without an authoritative doc consumers might alter embedding model without updating index code.
- **Suggested fix (discoverability):** README 'Configuration' section itemizing MODEL_NAME and EMBEDDING_DIM (e.g., MODEL_NAME=text-embedding-3-small, EMBEDDING_DIM=1536) and advising where to change these constants for other models. Recommend making EMBEDDING_DIM available as a single source of truth in code.

## [high] Exact client & createIndex code snippet

- **What was missing:** A minimal copy-paste snippet showing how to connect with pymongo and create the recommended vector index (exact call using the managed service's accepted options).
- **Where the agent looked:** Repository and local run outputs; no external docs reachable.
- **Effect on this build:** Without the snippet the builder avoided creating indexes and used client-side similarity, reducing production realism of the sample.
- **Suggested fix (mcp_tool_or_description):** A short code sample file 'examples/create_vector_index.py' that sets EMBEDDING_DIM from src/embeddings.py and issues the create_index call with tested options for the product's vector index API, plus verification steps to confirm index creation.

## [medium] Index parameter guidance in README

- **What was missing:** Concrete guidance in the README on which vector index parameters to choose for different dataset sizes and how to adapt parameters.
- **Where the agent looked:** README.md and other repository files. No external docs accessible in this run.
- **Effect on this build:** Left users without guidance on how to tune index parameters for production workloads; the sample deliberately avoids creating such indexes without guidance.
- **Suggested fix (learn_doc):** Add a 'Vector index tuning' subsection to the README explaining typical parameter defaults for small (<=10k), medium (10k-1M) and large (>1M) datasets, with example HNSW/IVF parameter sets and tradeoffs (latency vs memory vs recall).

## [medium] .env.example completeness

- **What was missing:** Optional environment variables used by the code (LLM_MODEL, ENABLE_VECTOR_INDEX/ENABLE_SERVER_SEARCH) were not listed in .env.example.
- **Where the agent looked:** .env.example and src/*.py in repository.
- **Effect on this build:** Users may not realize optional flags exist to enable server-side index creation or change the LLM model name.
- **Suggested fix (agent_kit_rule):** Update .env.example to list LLM_MODEL, OPENAI_API_BASE (already present), and optional toggles like ENABLE_VECTOR_INDEX and ENABLE_SERVER_SEARCH with placeholders and comments explaining their use.

## [medium] Infrastructure as code example for cluster

- **What was missing:** No IaC (Bicep/Terraform) example for creating an Azure DocumentDB cluster or minimal sample to show resource type and required params.
- **Where the agent looked:** Repository root and docs; no external docs reachable.
- **Effect on this build:** Operators who want to reproduce the cluster with correct resource type and settings have no packaged example; the run policy supplied a live cluster so the sample avoided provisioning, but the gallery expects an IaC example.
- **Suggested fix (learn_doc):** Provide a minimal Terraform and Bicep example that declares the DocumentDB resource the product supports (example resource provider and names), with defaults that keep cost low and optional parameters for tier and region. Add a short paragraph in README pointing to the IaC file.

