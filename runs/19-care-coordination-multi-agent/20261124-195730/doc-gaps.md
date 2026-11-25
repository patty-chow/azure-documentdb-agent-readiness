# Documentation and tooling gaps: 19-care-coordination-multi-agent

Each entry is something an agent needed to know or do while building this sample and could not find. These are for the product team.

## [high] Explicit PyMongo connection examples for mongoClusters

- **What was missing:** A single authoritative, copy-paste Python example for connecting to the DocumentDB managed mongoClusters surface (read DOCUMENTDB_URI, pass tls options and recommended authMechanism examples for SCRAM and MONGODB-OIDC). The quickstarts give general guidance but do not present a single concrete PyMongo snippet that agents can copy.
- **Where the agent looked:** Microsoft Learn Quickstarts and the documentdb-driver skill materials (searches shown in practice-discovery).
- **Effect on this build:** Builder created MongoClient(DOCUMENTDB_URI) without explicit TLS/auth options (app/app/db.py:27). This omission risks connection failures if users rely on the example and the DOCUMENTDB_URI lacks required options.
- **Suggested fix (mcp_tool_or_description):** A short 'Connect with PyMongo' sample page: 1) Read DOCUMENTDB_URI from env; 2) Show three examples: SCRAM URI, MONGODB-OIDC example, and explicit MongoClient(..., tls=True, tlsAllowInvalidCertificates=False). Provide a minimal snippet that checks connectivity (client.admin.command('ping')) and a one-line note about copying the portal connection string.

## [high] Vector-index small-demo defaults

- **What was missing:** A recommended set of starter vector-index parameters for small datasets (<10k vectors) so sample authors can create vector indexes that work well for demos without having to tune parameters.
- **Where the agent looked:** Azure DocumentDB vector-search docs and quickstarts; readiness notes showed no single 'safe defaults' example.
- **Effect on this build:** Builder deferred vector-index creation; sample documents and seed script create only simple indexes. Users lack a clear example of which m/efConstruction/numLists/lBuild/lSearch defaults to use for a demo.
- **Suggested fix (learn_doc):** Add a 'Vector index starter configs' subsection to the vector-search docs: include a small-demo HNSW block (dimensions placeholder, m=16, efConstruction=64), an IVF suggestion (numLists=1/4/16 depending on dataset size) and a DiskANN note. Show exact createIndexes JSON and a tiny Python script that sets dimensions from EMBEDDING_DIM env var.

## [high] LLM/embedding model selection guidance

- **What was missing:** A concise guidance page that maps common embedding models to embedding output dimensions, and recommends which LLM/chat models pair well for synthesis in samples.
- **Where the agent looked:** Run-readiness notes and Azure docs; no single mapping page found that an agent could use to decide EMBEDDING_MODEL and EMBEDDING_DIM.
- **Effect on this build:** Builder picked text-embedding-3-small (1536 dims) by assumption. Without authoritative guidance an agent may pick mismatched dims and create a vector index with wrong 'dimensions'.
- **Suggested fix (discoverability):** A small table in the LangChain/DocumentDB integration docs: columns embedding_model => dimension => suggested index type => example create_index snippet. Include examples for the common models used in sample repos.

## [high] Provenance schema for LLM outputs

- **What was missing:** A recommended document schema (fields and example values) for storing provenance metadata (model, prompt template, embedding model/version, timestamp, provenance_id) alongside generated artifacts like care plans.
- **Where the agent looked:** Vector/LLM orchestration docs; no explicit sample schema for generated-document provenance was found.
- **Effect on this build:** The sample's care_plans documents do not include provenance metadata, which reduces auditability of generated care plans (app/app/db.py:56-63).
- **Suggested fix (learn_doc):** Add a short 'Recording provenance for generated artifacts' page with a sample care_plans schema, sample code to populate the provenance block in make_care_plan_doc, and guidance for when to record full prompts vs templates.

## [medium] Retries and transient-fault guidance for small apps

- **What was missing:** A short, prescriptive example for application-level retries (exponential backoff + jitter) for PyMongo operations in DocumentDB whiteboard samples.
- **Where the agent looked:** Reliability docs and documentdb-connection skill; examples show principles but no small copy-paste retry wrapper for sample authors.
- **Effect on this build:** The sample lacks retry wrappers and thus may surface transient failures during seeding or care-plan insertion in flaky networks.
- **Suggested fix (sample_or_quickstart):** A 1-page quickstart/fix: include a Python retry decorator that wraps operations like insert_one/update_one with exponential backoff and a max-attempts parameter; show how to combine with pymongo's retryableWrites settings.

## [medium] DocumentDB vs older Cosmos naming and connection patterns

- **What was missing:** A short 'Which connection string format to use' note that contrasts older Cosmos 'mongo.cosmos.azure.com' examples (replicaSet=globaldb, port 10255) with the DocumentDB mongoClusters SRV/non-SRV patterns (host suffix .mongocluster.cosmos.azure.com and ports starting at 10260).
- **Where the agent looked:** Quickstart and connection docs; some examples on the web mix the two surfaces causing confusion.
- **Effect on this build:** If an author copies legacy Cosmos connection options they may produce a non-working client; the repo's .env.example uses the mongocluster pattern but authors often find conflicting examples online.
- **Suggested fix (naming_or_disambiguation):** A one-paragraph note on the quickstart and documentdb-driver skill showing the correct host suffixes and port ranges and warning about replicaSet=globaldb being Cosmos-account specific.

