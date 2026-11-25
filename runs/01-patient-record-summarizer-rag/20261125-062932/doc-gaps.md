# Documentation and tooling gaps: 01-patient-record-summarizer-rag

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Authoritative index-creation snippet (vector index)

- **What was missing:** A validated, idempotent code snippet to create a provider-native vector index (HNSW/IVF/DiskANN) with the exact option names and parameter names for the managed Azure DocumentDB cluster.
- **Where the agent looked:** No external documentation search server was available in this run; discovered from local repo files only.
- **Effect on this build:** The builder avoided implementing DB-side vector index creation and implemented an application-side re-rank fallback instead. This reduces performance/scale realism and leaves index parameters unspecified for users who want to enable DB-side ANN.
- **Suggested fix (mcp_tool_or_description):** Ship a small 'Create vector index' page in the agent-kit that includes: (a) an exact pymongo/mongo shell createIndex snippet for each supported indexType (hnsw, ivf, diskann) using a placeholder EMBEDDING_DIM variable; (b) example parameter values for small, medium and large workloads; (c) a one-line command to verify an index via collection.index_information().

## [high] $search/knn aggregation availability and example

- **What was missing:** Authoritative guidance whether the service exposes an aggregation stage like $search/knnBeta and an exact example aggregation pipeline to use for hybrid vector+text search.
- **Where the agent looked:** No external documentation search server was available in this run; the builder relied on local readiness notes and implemented fallback re-rank.
- **Effect on this build:** Uncertainty led the builder to avoid $search in code, using a slower but portable application-side re-rank instead. If native $search is available, the sample misses an opportunity to demonstrate native ANN performance and syntax.
- **Suggested fix (learn_doc):** A page titled 'Hybrid search and $search/knn examples' with a verified aggregation pipeline example (copy-paste-ready) for the supported cluster and a short feature-detection snippet that the sample can run at startup and conditionally enable native retrieval.

## [high] Driver recommended connection settings

- **What was missing:** A short authoritative list of recommended MongoClient options (timeouts, maxPoolSize, retryWrites, serverSelectionTimeoutMS) for the managed DocumentDB clusters.
- **Where the agent looked:** No external docs reachable in this run; practice came from prior knowledge and local code shows defaults.
- **Effect on this build:** The code uses default MongoClient settings; a sample built without recommended timeout/pooling defaults risks poor behavior in real deployments (slow client creation, connection churn).
- **Suggested fix (discoverability):** Document 'Driver connection best-practices' in the agent-kit and sample README: show MongoClient(uri, maxPoolSize=50, serverSelectionTimeoutMS=5000, retryWrites=True) and explain why and when to change them.

## [high] Retry/429 and bulk ingestion guidance

- **What was missing:** Concrete examples showing exponential backoff/retry patterns, handling 429/TooManyRequests, and recommended bulk ingestion approach (bulk_write, rate-limiting) for seeds.
- **Where the agent looked:** No external docs reachable; guidance inferred from prior knowledge.
- **Effect on this build:** Seed uses per-document replace_one/insert_one with no backoff; this may trigger throttling on real clusters during large ingestions.
- **Suggested fix (learn_doc):** Add a short 'Seeding at scale' page that contains: a bulk_write example, a rate-limiter pattern, and a snippet showing exponential backoff honoring Retry-After for 429 responses.

## [high] Authentication choices and AAD guidance

- **What was missing:** Authoritative listing of the authentication methods supported by the managed MongoDB cluster (SCRAM, X.509, Microsoft Entra ID) and example connection snippets for each.
- **Where the agent looked:** No external docs reachable; the repo only documents that DOCUMENTDB_URI is expected and that AAD was not validated.
- **Effect on this build:** README notes 'authentication variants not validated', leaving users uncertain whether and how to use Microsoft Entra ID for client authentication.
- **Suggested fix (discoverability):** Add an 'Authentication' section to the agent-kit and sample README that states supported auth methods, example connection URIs for SCRAM and for any supported AAD flows, and pointers to official docs.

## [medium] .env.example completeness

- **What was missing:** .env.example lists DOCUMENTDB_URI and OPENAI_API_KEY but omits optional/used variables such as OPENAI_CHAT_MODEL and a note about EMBEDDING_DIM alignment.
- **Where the agent looked:** Repository files (.env.example, README) only; no external docs available.
- **Effect on this build:** Users may miss optional configuration keys and embedding-dimension mismatches when trying to create DB-side indexes or change models.
- **Suggested fix (learn_doc):** Expand .env.example to include OPENAI_CHAT_MODEL, EMBEDDING_DIM as a comment, and an example for providers that require TLS flags; add a short section in README explaining each env var.

## [medium] Provider IaC snippet

- **What was missing:** An example Bicep/ARM/Terraform snippet that provisions the managed MongoDB cluster with the correct provider namespace and resource type, including a minimal, low-cost default.
- **Where the agent looked:** No external docs reachable; the repository contains no infra-as-code.
- **Effect on this build:** The sample cannot show users how to create the right resource type; including incorrect IaC risks guiding users to the wrong resource.
- **Suggested fix (mcp_tool_or_description):** Provide one validated Bicep snippet and one Terraform azapi snippet that create Microsoft.DocumentDB/mongodbClusters with safe defaults, plus a note on required az CLI extension if any.

