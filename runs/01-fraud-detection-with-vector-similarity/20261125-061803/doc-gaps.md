# Documentation and tooling gaps: 01-fraud-detection-with-vector-similarity

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Exact vector index creation syntax

- **What was missing:** A verified, copy-pasteable create_index example for Azure DocumentDB's vector indexes (the exact option names such as vectorOptions/indexOptions, algorithm names, and where to supply dims and distance).
- **Where the agent looked:** No documentation server available during this run (documentation_search_available=false); I inspected local files (seed_data.py, README.md) which contain best-effort placeholders but not authoritative syntax.
- **Effect on this build:** The seed script used a plausible create_index and caught failures; without exact syntax the sample cannot demonstrate a tested server-side vector index creation, and end users will need to verify and update the index code for their cluster.
- **Suggested fix (learn_doc):** A short page in the agent-kit or README titled 'Creating a vector index on Azure DocumentDB (MongoDB-compatible)'. Include: (1) the tested createIndex call (code snippet) that works against the managed cluster, (2) example values for algorithm (ivf/hnsw/diskann), dims (match embedding model), and distance (cosine), (3) example error messages and how to fall back to client-side, (4) a minimal shell and Python/pymongo example. Mark as high priority.

## [high] Vector-search aggregation/operator names

- **What was missing:** The exact aggregation stage/operator ($search/$vectorSearch/knnBeta or provider-specific name) and the meta-score key names used to project similarity scores from server-side vector search.
- **Where the agent looked:** No external docs available; local code contains placeholders (src/agent.py uses an addFields + $meta placeholder).
- **Effect on this build:** The implementation falls back to client-side similarity because the operator names and syntax were not verified. Without the operator names the sample cannot demonstrate server-side KNN search semantics or return official server-side similarity scores.
- **Suggested fix (learn_doc):** A short example in the README or an agent-kit page titled 'Running vector KNN queries' that shows the working aggregation pipeline for the managed cluster, including how to pass the query vector, how to request the top-k, how to project the provider's search score (e.g., $meta: 'searchScore'), and how to interpret returned fields. Include language and Python/pymongo examples, plus fallback recipes.

## [high] Embedding provider & embedding dimensions

- **What was missing:** Authoritative guidance on which embedding provider(s) the sample should support, the env var names for provider credentials, and how to determine/check the model output dimensionality so indices and stored vectors match the chosen model.
- **Where the agent looked:** Local repo (.env.example, agent.py, seed_data.py) and readiness notes; no external docs reachable in this run.
- **Effect on this build:** The demo uses mock 128-d embeddings; when switching to a real provider (e.g., OpenAI) real embeddings may have a different dimension (e.g., 1536), which would require re-seeding and index recreation. This mismatch was flagged in the readiness report and partially implemented (seed remains deterministic).
- **Suggested fix (agent_kit_rule):** Add an agent-kit rule and README section 'Embedding provider selection' that: (1) lists supported providers (OpenAI, etc.), (2) declares the env var names (e.g., OPENAI_API_KEY), (3) shows how to query or assert the embedding dimension and set EMBED_DIM via env var or model metadata, (4) instructs to re-seed stored vectors when switching providers, and (5) includes a short Python snippet to validate stored vectors' length against the model output at startup.

## [medium] Index tuning parameters for sample size

- **What was missing:** Practical guidance and example parameter values (nlist, probes, efConstruction, M, etc.) appropriate for small demo datasets vs. production-scale collections.
- **Where the agent looked:** Local README and seed script do not contain concrete parameter suggestions; no external docs reachable.
- **Effect on this build:** No tuning or parameter guidance was provided; seed_data does not set or expose these parameters, so an operator would not know how to adapt index options for larger datasets.
- **Suggested fix (learn_doc):** A 'Vector index tuning' page showing recommended defaults for demo (<10k vectors), medium (10k–1M), and large (>1M) datasets; provide sample create_index parameter sets for IVF and HNSW, guidance on measuring recall/throughput, and commands to rebuild indexes. Include examples and recommended monitoring metrics.

## [medium] LangChain tool / example for provider-side vector search

- **What was missing:** An example LangChain Tool wrapper that executes the provider's vector-search aggregation and returns scored results (including provider search score).
- **Where the agent looked:** No external docs available; local code implements a client-side fallback instead.
- **Effect on this build:** The sample does not ship a LangChain Tool for server-side vector search; users have to implement it themselves and may implement incorrect aggregation stages.
- **Suggested fix (sample_or_quickstart):** Add a small module 'docdb_vector_tool.py' that defines a LangChain Tool (or simple function) that executes the tested aggregation pipeline for vector search and returns structured matches. Include usage examples in README and a test that mocks the driver to validate the tool.

## [medium] Client library version and pinning guidance

- **What was missing:** A short authoritative note stating which client library and exact versions are supported/tested (e.g., pymongo X.Y.Z) and an explanation of pinning policy for the sample.
- **Where the agent looked:** The repo's requirements.txt contains ranged constraints but no exact tested versions. No external docs were reachable.
- **Effect on this build:** The sample currently uses range constraints; reproducibility may suffer and unexpected incompatibilities could arise for consumers of the sample.
- **Suggested fix (discoverability):** Add a README subsection 'Tested dependency set' listing the exact versions used to verify the sample and consider shipping a pip freeze or constraints.txt. Also add a note advising how to update/pin safely.

## [medium] Infrastructure as code (IaC) examples

- **What was missing:** Sample IaC templates (Bicep/ARM/Terraform) that declare the managed DocumentDB resource type expected by the sample.
- **Where the agent looked:** No IaC files in the repo; no external docs reachable to confirm resource type.
- **Effect on this build:** No IaC shipped; consumers who want to provision a test cluster lack an example to follow. The readiness report flagged accelerator tooling that would normally help but was not available.
- **Suggested fix (mcp_tool_or_description):** Add an infra/ directory with minimal Bicep and Terraform examples that create a low-cost, test DocumentDB cluster with notes on region/tier, plus a README link explaining this is optional and when to use it.

## [low] Decisions recorded as model_default

- **What was missing:** For decisions made from model defaults (e.g., choosing driver type and version constraints), an explicit source or link to authoritative guidance was not recorded.
- **Where the agent looked:** Decisions D003 and D008 in decisions.jsonl have reason_source 'model_default'. No local docs or references were provided to justify the choices.
- **Effect on this build:** Model-default choices are acceptable for prototypes but may surprise maintainers; lacking a documented rationale makes future maintenance harder.
- **Suggested fix (discoverability):** Add a short 'Why we chose this driver/version' note in README (or as comments in requirements.txt) that cites a stable upstream compatibility matrix or a pinned tested version to explain the choice.

