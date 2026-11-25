# Documentation and tooling gaps: 11-care-gap-identification-pipeline

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Vector index creation parameters

- **What was missing:** No authoritative, in-repo example of provider-specific createIndex syntax, required embedding dimension, algorithm and metric for DiskANN/HNSW/IVF on the provided cluster.
- **Where the agent looked:** Local repository (README.md, src/db.py, skill.md, readiness notes). Documentation search was not available during this run (documentation_search_available=false).
- **Effect on this build:** The builder intentionally avoided creating any vector index and left vector-index creation out of the seed script; as a result, any embedding-based search examples are not runnable and there is no demonstration of how to set dims or algorithm to match an embedding model.
- **Suggested fix (mcp_tool_or_description):** Ship a short 'Vector index creation' page in the agent-kit that: (1) states the supported index types (DiskANN/HNSW/IVF) for the target SKU, (2) provides a verified createIndex example including parameter names (algorithm, dims, metric) and an idempotent script snippet, and (3) documents how to set EMBEDDING_DIM to match an embedding model. Include a small verification script that queries server index metadata after creation.

## [high] Aggregation-based screening logic

- **What was missing:** Guidance or example that shows how to translate time/diagnosis/age screening rules into a single server-side aggregation pipeline producing 'missing' flags.
- **Where the agent looked:** Local src/db.py and src/pipeline.py. No external docs were reachable during this run.
- **Effect on this build:** The builder implemented rule evaluation in Python rather than inside an aggregation pipeline; this makes the sample simpler but misses the prompt's request to push screening detection to the DB and demonstrates less of the DB's aggregation capability.
- **Suggested fix (sample_or_quickstart):** Provide a small example aggregation pipeline in the repo that demonstrates $lookup/$sort/$group and computed fields to flag missing screenings (example: compute last_visit per patient, compute age from dob in aggregation, then $match where last_visit older than computed interval or last_visit is null). Include an idempotent script that can optionally swap to DB-side detection.

## [high] Embedding model specification for vector search

- **What was missing:** No explicit embedders/model name and the embedding output dimension in README/.env.example.
- **Where the agent looked:** app/.env.example and app/README.md. No external docs were reachable.
- **Effect on this build:** Without model/dimension specified the sample cannot create a correctly-dimensioned vector index or demonstrate embedding-based retrieval.
- **Suggested fix (learn_doc):** Add EMBEDDING_MODEL and EMBEDDING_DIM variables to .env.example and README, describe recommended embedder(s) and their output dimensions, and show how to pass EMBEDDING_DIM into the vector-index creation script.

## [medium] Vector index tuning guidance

- **What was missing:** No README guidance describing how to choose vector-index parameters for larger datasets (e.g., recall vs latency trade-offs and how to change the seed script).
- **Where the agent looked:** Local README.md and src code. No external docs available from this run.
- **Effect on this build:** Without tuning advice, users may create inappropriate indexes for production or be uncertain how to scale parameters.
- **Suggested fix (learn_doc):** Add a 'Vector index sizing' subsection in README: describe sample data size assumptions, give example params for small/medium/large datasets, and show how to edit seed script parameters or environment variables to tune them.

## [medium] Connection-options guidance (TLS, timeouts, pool settings)

- **What was missing:** No guidance in the repo on configuring connection pool sizes, timeouts, TLS options, or whether AAD token auth is supported for the cluster.
- **Where the agent looked:** src/db.py and README.md; the run environment skill.md mentions cluster but gives no explicit driver option guidance. Documentation search not available.
- **Effect on this build:** The sample uses a default MongoClient which is acceptable for demos but lacks recommended production connection settings; users may not know to set pool sizes or timeouts for long-running agent processes.
- **Suggested fix (learn_doc):** Add a 'Connection configuration' section to README that explains safe defaults (connectTimeoutMS, socketTimeoutMS, maxPoolSize), whether TLS verification must be enabled and how to supply CA certs, and explicitly state that the sample reads DOCUMENTDB_URI verbatim and will not attempt AAD unless documented.

## [medium] Discoverability: documented environment variables for LLM

- **What was missing:** The run-time LLM env var names are present, but the prompt review highlighted a risk that the model credential env name would be unspecified. In this repo, OPENAI_API_KEY/OPENAI_MODEL are included but discoverability across agent tools is unknown because external docs were not searchable.
- **Where the agent looked:** .env.example and README.md locally; no external doc search available.
- **Effect on this build:** Resolved within this repo (env names included). If an agent expects different env names, discovery could fail outside this repo.
- **Suggested fix (discoverability):** Add a brief 'Configuration' table in README listing every environment variable required with a one-line description and example placeholder; ensure agent-kit docs reference the same variable names.

## [low] Infra-as-code example

- **What was missing:** No example IaC (Bicep/Terraform) showing the resource type for the managed MongoDB-compatible cluster.
- **Where the agent looked:** Repo root and README. Documentation search unavailable in this run.
- **Effect on this build:** Users who expect an IaC example cannot refer to a validated snippet; the run policy forbade provisioning in this build so none was created.
- **Suggested fix (sample_or_quickstart):** Add a small 'infra/' folder with a comment-rich Bicep or Terraform snippet showing the resource type to create a compatible cluster (or explicitly state 'sample does not provision resources; use DOCUMENTDB_URI from an existing cluster').

