# Documentation and tooling gaps: 02-clinical-trial-matching-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Embedding model choice & dimension

- **What was missing:** A gallery-level recommendation that samples should pick and document a specific embedding provider/model and the exact dimensionality to use when creating service-side vector indexes.
- **Where the agent looked:** Microsoft Learn (vector search docs), agent readiness findings, and installed skills.
- **Effect on this build:** The builder picked text-embedding-3-small/1536 by model_default. The vector-index create attempt used dimensions=1536, but the create-index call failed so no verification. Without an explicit documented sample choice, builders may pick mismatched dims and produce silent failures.
- **Suggested fix (learn_doc):** A short 'Embedding model & dimensions' page in the gallery that: (1) lists recommended embedding models for samples (OpenAI text-embedding-3-small 1536, etc.), (2) explicitly states the 'dimensions' value to use in createIndexes, (3) shows the seed code snippet that reads EMBEDDING_MODEL and EMBEDDING_DIM and verifies their consistency before creating an index.

## [high] Service-side vector index create example (runCommand JSON)

- **What was missing:** An explicit, copy-paste createIndexes runCommand JSON snippet for each vector kind (vector-hnsw / vector-ivf / vector-diskann) keyed to EMBEDDING_DIM and common tuning parameters.
- **Where the agent looked:** Integrated vector store docs and documentdb-vector-search skill; agent found examples but builders still attempted community createIndex shapes and needed clearer copyable templates.
- **Effect on this build:** The builder attempted to call the MCP helper; it failed due to management tools disabled. A developer copying an incorrect createIndex API shape would be confused and see failures.
- **Suggested fix (discoverability):** Add a 'createIndexes (cosmosSearchOptions)' snippet for each algorithm in the documentdb-vector-search skill and the seed README, including dimensions placeholder, similarity, and example tuning parameters. Show the exact MCP helper payload and the alternative runCommand JSON for pymongo/driver authors.

## [high] Connection options and retry semantics

- **What was missing:** A concise sample-oriented checklist that agents and builders can apply to MongoClient creation: recommended pool sizing, TLS and authMechanism checks, and whether to include retryWrites=false in the connection string for this service.
- **Where the agent looked:** documentdb-connection skill and Microsoft Learn; guidance exists but not consolidated as a quick rule for samples.
- **Effect on this build:** The sample uses MongoClient(DOCUMENTDB_URI) without explicit options; missing recommended options may lead to suboptimal connection behavior or surprising retry semantics in production.
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule named 'mongodb-connection-sample' that enforces: use a singleton client, include recommended options (e.g., maxPoolSize, minPoolSize or documentdb-specific flags), and assert retryWrites=false or document why not. Provide an example MongoClient initialization snippet.

## [high] IaC example for Microsoft.DocumentDB/mongoClusters

- **What was missing:** A short Bicep or Terraform example that provisions a minimal, low-cost DocumentDB mongoClusters resource to use during CI or dev.
- **Where the agent looked:** Quickstart Bicep/Terraform docs; no repo example included in the sample.
- **Effect on this build:** The sample relies on an externally-provisioned cluster; builders or consumers who want a repeatable demo need to write their own IaC and may pick the wrong resource type (mongoClusters vs databaseAccounts).
- **Suggested fix (mcp_tool_or_description):** Add an 'iac' folder with a Bicep file that creates Microsoft.DocumentDB/mongoClusters with tier/region params and a small default config, plus a README note about run-policy and cost.

## [medium] Client-side ANN fallback guidance

- **What was missing:** Authoritative guidance that states the supported or recommended client-side ANN libraries and patterns when server-side vector search is not available for DocumentDB (the public docs focus on server-side indexes and do not prescribe a client-side library).
- **Where the agent looked:** Microsoft Learn vector search docs and general searches for FAISS/hnswlib in the DocumentDB context (no authoritative result).
- **Effect on this build:** The sample falls back to a deterministic/random vector ranking approach which is functional but not realistic. Builders may implement inefficient linear scans or copy patterns from other services.
- **Suggested fix (learn_doc):** A short guidance page: 'If server-side vector indexing is unavailable, consider FAISS or hnswlib for in-memory ANN; include example code for building an index from stored number[] embeddings and doing batched queries.'

## [medium] Index tuning guidance in README

- **What was missing:** A short README subsection showing how to adjust vector-index parameters for larger datasets and how to re-create indexes safely.
- **Where the agent looked:** Sample README and vector docs; sample README mentions the vector attempt but not tuning guidance.
- **Effect on this build:** Builders have no in-repo guidance on when to move from client-side ranking to DiskANN and how to tune parameters.
- **Suggested fix (discoverability):** An 'Index tuning' appendix in README that shows recommended small-dataset defaults used in the sample and links to the authoritative vector tuning docs, plus commands to re-create the index with adjusted parameters.

## [medium] Prior-knowledge-only practices (eligibility schema)

- **What was missing:** A public, DocumentDB-specific example that shows an opinionated, structured eligibility criteria schema for trial documents so agents don't rely solely on model priors.
- **Where the agent looked:** Searches for 'eligibility criteria structured' returned no authoritative DocumentDB guidance.
- **Effect on this build:** Agents may rely on prior knowledge or inconsistent schemas across samples. The sample does use a structured criteria object, but a canonical schema would help interoperability and agent verification.
- **Suggested fix (learn_doc):** A short gallery doc 'Trial document schema' with required/optional fields, types, example documents, and an example $jsonSchema validator to enforce it.

## [low] Decisions that used model_default

- **What was missing:** Two builder decisions (embedding model and LLM model) were chosen from model_default; a public statement describing recommended defaults for samples would remove ambiguity.
- **Where the agent looked:** Readiness findings and decision log (decisions.jsonl).
- **Effect on this build:** The choices are reasonable but not authoritative; explicit defaults for gallery samples would reduce inconsistency across builds.
- **Suggested fix (naming_or_disambiguation):** A short 'Gallery defaults' page listing recommended embedding model and LLM choices for samples, and the environment variables they set (EMBEDDING_MODEL, EMBEDDING_DIM, LLM_MODEL).

