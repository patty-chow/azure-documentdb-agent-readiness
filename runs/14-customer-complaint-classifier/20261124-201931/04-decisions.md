# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 6 |
| operator | 2 |
| model_default | 2 |
| skill | 2 |
| tool_result | 2 |
| readiness_report | 2 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:23:23+00:00

## D002 (build): I chose to use Beanie ODM with Motor (motor>=3.x) and PyMongo pinned alongside it, because the prompt explicitly requires Beanie; despite documentdb-connection recommending PyMongo's AsyncMongoClient, Beanie depends on Motor.

- **Instead of:** Use PyMongo AsyncMongoClient (per documentdb-connection guidance); Use Motor with Beanie (per prompt requiring Beanie ODM)
- **Because:** The prompt's requirement to use Beanie ODM takes priority for this sample; I will follow driver best-practices (singleton client) while using Motor to satisfy Beanie compatibility.
- **Reason came from:** `model_default`
- **Evidence:** Prompt: 'build a Python LangChain agent using Beanie ODM' and documentdb-connection skill: 'use PyMongo AsyncMongoClient (not Motor)'.
- **When:** 2026-11-25T10:24:04+00:00

## D003 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); Another embedding model (e.g., 1536-dim from other provider)
- **Because:** OpenAI's text-embedding-3-small is a commonly available, cost-effective embedding for semantic search and matches vector-search skill examples; 1536 dims is needed to create the vector index correctly.
- **Reason came from:** `prompt`
- **Evidence:** Assumption in prompt review: 'assume 1536 dims for OpenAI text-embedding-3-small'.
- **When:** 2026-11-25T10:24:08+00:00

## D004 (build): I chose 'gpt-4o-mini' as the classification LLM for the LangChain agent.

- **Instead of:** gpt-4o-mini; gpt-4o or gpt-4
- **Because:** gpt-4o-mini offers a good balance of capability and cost for classification tasks and is compatible with LangChain's OpenAI wrapper in sample code.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use OpenAI as provider: gpt-4o-mini (or gpt-4o if available)'.
- **When:** 2026-11-25T10:24:11+00:00

## D005 (build): I chose to read the cluster connection string from environment variable DOCUMENTDB_URI and use that for SCRAM-style auth (no Entra/OIDC flow in sample).

- **Instead of:** Authenticate with Microsoft Entra OIDC; Authenticate with SCRAM username/password via DOCUMENTDB_URI
- **Because:** Using DOCUMENTDB_URI is simplest for a sample app and avoids complex OIDC setup; it matches the run environment description and avoids storing secrets in files.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI.'
- **When:** 2026-11-25T10:24:19+00:00

## D006 (build): I chose to create a vector-diskann index on 'embedding' with dimensions=1536, similarity='COS', maxDegree=32, lBuild=50.

- **Instead of:** Create vector index using vector-diskann; Create vector index using vector-hnsw or vector-ivf
- **Because:** DiskANN is the recommended choice for production-scale and matches the M30 tier cluster described; dimensions must match the chosen embedding model (1536) and COS is appropriate for cosine-similarity normalized embeddings.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill 'vector-create-diskann-index.md' showing DiskANN example and parameter guidance.
- **When:** 2026-11-25T10:24:21+00:00

## D007 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:27:55+00:00

## D008 (build): I chose Python with FastAPI and Beanie ODM.

- **Instead of:** JavaScript/Node.js; Python (FastAPI + Beanie)
- **Because:** The prompt explicitly requests Python and Beanie; FastAPI provides a small web API surface as assumed in the prompt review.
- **Reason came from:** `prompt`
- **Evidence:** Sample prompt: 'build a Python LangChain agent using Beanie ODM'
- **When:** 2026-11-25T10:28:26+00:00

## D009 (build): I chose concrete pinned versions: beanie==1.19.1, motor==3.1.1, pymongo==4.4.0.

- **Instead of:** beanie>=0.18 / motor 2.x / pymongo 4.x; beanie 1.x / motor 3.x / pymongo 4.x
- **Because:** Pinning concrete, recent stable releases avoids unexpected breaking changes while matching the assumed compatibility matrix.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Beanie 1.x with Motor 3.x and PyMongo 4.x'
- **When:** 2026-11-25T10:28:28+00:00

## D010 (build): I chose OpenAI provider with 'text-embedding-3-small' (1536 dims) for embeddings and 'gpt-4o-mini' for classification calls made by LangChain.

- **Instead of:** Use OpenAI (text-embedding-3-small + gpt-4o-mini); Use Azure OpenAI with a different model; Use local LLM
- **Because:** OpenAI models are widely available and fit the sample's needs; text-embedding-3-small is 1536-dimensional which matches vector index choice; using environment-provided OPENAI_API_KEY keeps secrets out of files.
- **Reason came from:** `model_default`
- **Evidence:** Assumption in prompt review suggested OpenAI and 'text-embedding-3-small' and gpt-4o-mini as reasonable defaults.
- **When:** 2026-11-25T10:28:35+00:00

## D011 (build): I chose to read the cluster connection string from DOCUMENTDB_URI environment variable and use SCRAM (user/password) as the auth method in the sample.

- **Instead of:** Authenticate with Azure Entra (OIDC); SCRAM user/password via connection string from env
- **Because:** The run environment already provides DOCUMENTDB_URI and prompt advised reading it from env; implementing Entra/OIDC would add complexity and extra secrets management not needed for the sample.
- **Reason came from:** `prompt`
- **Evidence:** 'Its connection string is in the environment variable DOCUMENTDB_URI.' — skill_md
- **When:** 2026-11-25T10:28:46+00:00

## D012 (build): I chose HNSW vector index for the sample (vector-hnsw) with dimensions=1536 and similarity=COS.

- **Instead of:** Create DiskANN vector index; Create HNSW vector index; Create IVF vector index
- **Because:** For a small seeded dataset (<=500), HNSW is simple to create and good for demo; DiskANN is production-focused. Dimensions must match embedding model (1536).
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill guidance: 'HNSW is suitable up to ~50k vectors' and the dataset is small.
- **When:** 2026-11-25T10:28:50+00:00

## D013 (build): I chose to modify tests to insert project root into sys.path at test top to avoid shell environment prefixes (the command runner refused 'PYTHONPATH=').

- **Instead of:** Run pytest with PYTHONPATH set (shell prefix); Modify tests to add sys.path so imports work without env prefix
- **Because:** The run environment disallows environment-prefixed commands; changing tests is a small, safe change to make tests import the local src package during CI like runs.
- **Reason came from:** `tool_result`
- **Evidence:** Command runner refused 'PYTHONPATH=.' execution.
- **When:** 2026-11-25T10:30:05+00:00

## D014 (build): I chose to use the documentdb MCP server (connection_profile 'default') to create indexes and insert seed documents into the live cluster.

- **Instead of:** Use local gateway Docker image for index creation and seeding; Use the documentdb MCP server to create indexes and insert sample docs
- **Because:** MCP server provides programmatic, read-only and index-creation tools against the live cluster and is the recommended verification path in this environment. Local gateway is not running per readiness report.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: 'the documentdb MCP server's connection profile `default` is connected to that same cluster. Use its tools to inspect collections, indexes and query plans and to verify what the app created.'
- **When:** 2026-11-25T10:30:31+00:00

## D015 (build): I chose to use documentdb_insert_documents via the documentdb MCP server to load synthetic seed documents for verification.

- **Instead of:** Use seed script locally (requires DOCUMENTDB_URI); Use documentdb MCP server insert_documents tool
- **Because:** Using MCP is direct, does not require local network configuration, and runs against the live cluster that the sample is meant to demonstrate.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report: MCP server provides documentdb_insert_documents tool.
- **When:** 2026-11-25T10:30:40+00:00

## D016 (build): I chose to stop attempting MCP write operations after failures and proceed by adding index-creation JSON and a seed script in the repo; note the MCP tool failure in the report.

- **Instead of:** Retry documentdb_insert_documents and createIndex via MCP; Stop and treat MCP write operations as unavailable and proceed with repo-only artifacts and README guidance
- **Because:** The MCP server tool failed to perform writes; per instructions stop after second failed attempt and proceed with alternate route to avoid wasting cycles.
- **Reason came from:** `tool_result`
- **Evidence:** Calls to documentdb_insert_documents and documentdb_create_index returned 'Error: Function failed.'
- **When:** 2026-11-25T10:30:54+00:00
