# Documentation and tooling gaps: 11-market-news-sentiment-orchestration

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Vector index creation & parameters

- **What was missing:** Concrete, tested instructions and a sample createIndex script for creating vector indexes (HNSW/IVF/DiskANN) with the exact option names and parameter defaults (dims, M, efConstruction, distance) for the DocumentDB cluster.
- **Where the agent looked:** No external documentation search available in this run; repository files inspected (scripts/seed.js, src/run.js) show no vector index creation code.
- **Effect on this build:** The sample stores embeddings but did not create a cluster vector index. As a result, vector search was not verified; users must create an index manually and choose matching dimensions/parameters before running similarity queries.
- **Suggested fix (learn_doc):** Title: 'Creating vector indexes on Azure DocumentDB (MongoDB-compatible)'. Outline: description of supported vector index types (HNSW, IVF, DiskANN), exact createIndex command examples for Node.js driver (showing option names supported by the cluster), recommended defaults for small sample datasets, how to set dims from EMBEDDING_DIM env var, and troubleshooting steps for common errors.

## [high] Driver connection options and TLS guidance

- **What was missing:** An authoritative example of recommended MongoClient connection options for this managed DocumentDB offering (TLS/ssl settings, recommended pool sizing and retry options) and a canonical connection-string example for builders to reference.
- **Where the agent looked:** Run environment notes and repository files. No external docs reachable from this run.
- **Effect on this build:** The code uses MongoClient(uri) with default options; without confirmed TLS/option guidance builders may omit important settings or hardcode wrong parameters, risking failed connections or insecure defaults.
- **Suggested fix (learn_doc):** Title: 'Recommended MongoClient options for Azure DocumentDB (MongoDB-compatible)'. Outline: canonical connection string example, TLS enforcement examples, recommended pool (maxPoolSize) values for sample vs production, example Node.js code snippet showing options and explanation.

## [high] Embedding model dimensionality & validation

- **What was missing:** Explicit recommendation to set and validate embedding dimensionality (EMBEDDING_DIM) and code examples that reject or log mismatched-dimension embeddings before insert.
- **Where the agent looked:** Code inspection (src/ai.js, src/run.js) showed embedding calls exist but no dimensionality checks; external doc search unavailable.
- **Effect on this build:** If a user configures a different embedding model than the assumed dims, inserts could produce mismatched-dimension vectors and make vector indexes unusable.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: require EMBEDDING_DIM env var for any sample that stores embeddings; sample code snippet to assert embedding.length === parseInt(process.env.EMBEDDING_DIM) and to log/skip or convert if mismatch. README addition describing how to change EMBEDDING_DIM when selecting different models.

## [high] Search API and similarity scoring

- **What was missing:** A documented /search endpoint example that validates inputs, returns clear errors for empty queries or embedding failures, and includes similarity scores in results.
- **Where the agent looked:** Repository files (src/server.js, src/run.js) do not implement /search; external search unavailable.
- **Effect on this build:** The sample lacks a public-facing search demonstration and does not show how to return similarity scores; this reduces the gallery's ability to demonstrate vector search or LLM retrieval functionality.
- **Suggested fix (sample_or_quickstart):** A short sample 'search' endpoint (server route) that: validates the query, calls embedText(), handles embed failures, runs a vector/hybrid search (with filtering step if needed), and returns hits with similarity scores and metadata.

## [medium] .env.example completeness

- **What was missing:** .env.example does not list runtime PORT and a few optional keys (e.g., EMBEDDING_DIM, OPENAI_API_BASE) that the code or deployment might expect.
- **Where the agent looked:** app/.env.example and app/src/server.js, app/src/ai.js inspected; no external search possible.
- **Effect on this build:** Users can run the demo, but common runtime variables like PORT are not suggested in .env.example which can confuse newcomers and make the demo less discoverable.
- **Suggested fix (agent_kit_rule):** Add entries to .env.example: PORT="3000", EMBEDDING_DIM="1536" (or a placeholder), OPENAI_API_BASE="" (if supporting Azure), and a short comment describing each variable's role.

## [medium] 429 / Retry guidance

- **What was missing:** Explicit guidance and a code sample for honoring Retry-After headers, and implementing exponential backoff with jitter for transient DB and external-service errors.
- **Where the agent looked:** Repository inspection; no external docs reachable.
- **Effect on this build:** No application-level retry/backoff was implemented; under higher load or throttling conditions this could cause failed ingest or missed alerts.
- **Suggested fix (learn_doc):** Title: 'Handling transient errors and throttling on Azure DocumentDB'. Outline: how to detect 429s, read Retry-After headers, implement exponential backoff with jitter in Node.js, and sample wrapper for MongoDB operations using a retry policy.

## [medium] Infrastructure-as-code example

- **What was missing:** A small IaC template (Bicep/ARM or Terraform) that creates the DocumentDB resource type used by the sample, parameterized for tier/region and with low-cost defaults.
- **Where the agent looked:** No IaC files in repo; external docs not available in this run.
- **Effect on this build:** Without IaC, reviewers or users must create the cluster manually; sample cannot be fully end-to-end reproducible from the repo alone.
- **Suggested fix (mcp_tool_or_description):** Provide a minimal Bicep snippet and equivalent Terraform example that create the cluster resource (parameterized name, region, tier) and references any necessary settings for MongoDB wire compatibility; include notes about run_policy and cost.

## [low] README clean-up instructions

- **What was missing:** Explicit clean-up steps (how to drop sample_fintech_11 or remove created collections).
- **Where the agent looked:** app/README.md inspected; external docs not reachable.
- **Effect on this build:** Users are not told how to remove the objects the sample creates; may leave test data in user clusters.
- **Suggested fix (learn_doc):** Add a 'Clean-up' section with commands to remove the sample DB (example using mongo shell or a short Node.js script that drops sample_fintech_11) and an admonition to not run on production clusters.

## [low] Decision reason_source clarity

- **What was missing:** Several logged decisions record reason_source as 'model_default' even though the run-environment or readiness notes provided authoritative guidance (for example DOCUMENTDB_URI).
- **Where the agent looked:** decisions.jsonl and the run-environment/skill_md (readiness report) in repository.
- **Effect on this build:** Mislabelled reason sources can hide whether a decision was guided by operator/dataset/run-environment docs; this reduces traceability.
- **Suggested fix (agent_kit_rule):** Agent-kit rule: when logging decisions, set reason_source to the most specific source available (prompt, skill_md/readiness_report, operator) rather than 'model_default'; show a short checklist for mapping evidence to reason_source.

