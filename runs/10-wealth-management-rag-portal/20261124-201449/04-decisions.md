# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 7 |
| model_default | 6 |
| operator | 3 |
| readiness_report | 1 |
| skill | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:04:50+00:00

## D002 (build): I chose Python with FastAPI

- **Instead of:** Node.js/TypeScript with express; Python with Flask; Python with FastAPI
- **Because:** Python is requested by the prompt (Python LlamaIndex). FastAPI is a modern minimal framework suited to small APIs and async retrieval flows.
- **Reason came from:** `prompt`
- **Evidence:** Assumption: 'Builder will target a recent stable Python ... provide a minimal API and CLI' and common Python/ASGI choices.
- **When:** 2026-11-25T10:05:19+00:00

## D003 (build): I chose Python 3.11

- **Instead of:** Python 3.13 (system); Python 3.11; Python 3.10
- **Because:** Many libraries used (llama_index, deps) are most commonly tested on 3.11; choosing 3.11 maximizes compatibility while remaining recent.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will target a recent stable Python (likely 3.10 or 3.11). I would assume Python 3.11 for tooling and LlamaIndex compatibility.'
- **When:** 2026-11-25T10:05:23+00:00

## D004 (build): I chose pymongo (MongoDB driver) pinned to 'pymongo>=4.3,<5'

- **Instead of:** Use pymongo 3.x; Use pymongo 4.x
- **Because:** PyMongo 4.x supports MongoDB 7.0 wire protocol and is recommended by the documentdb-driver skill for Azure DocumentDB.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use the official PyMongo driver (pymongo) with a recent 4.x release compatible with MongoDB wire protocol 7.0 (e.g., pymongo>=4.3,<5).'
- **When:** 2026-11-25T10:05:32+00:00

## D005 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:08:57+00:00

## D006 (build): I chose Python 3.11 as the target runtime for the sample app (code written to be compatible with 3.10+).

- **Instead of:** Node.js (JavaScript); Python 3.11; Python 3.13
- **Because:** LlamaIndex and related libraries are well-supported on Python 3.11; it balances modern features and compatibility.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Builder will target a recent stable Python (likely 3.10 or 3.11). I would assume Python 3.11 for tooling and LlamaIndex compatibility.'
- **When:** 2026-11-25T10:09:28+00:00

## D007 (build): I chose the official PyMongo driver (pymongo>=4.3,<5) and will use a singleton MongoClient pattern per documentdb-driver guidance.

- **Instead of:** pymongo<4.3; pymongo>=4.3,<5; motor (async)
- **Because:** PyMongo 4.x supports MongoDB 7.0 protocol and is the standard synchronous driver; singleton prevents connection pool exhaustion.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review: 'Use the official PyMongo driver (pymongo) with a recent 4.x release compatible with MongoDB wire protocol 7.0 (e.g., pymongo>=4.3,<5). Use MongoClient singleton pattern per documentdb-driver guidance.'
- **When:** 2026-11-25T10:09:30+00:00

## D008 (build): I chose to read the connection string from the environment variable DOCUMENTDB_URI (SCRAM-style) at runtime and not store secrets in files.

- **Instead of:** Use SCRAM credentials via connection string in env (DOCUMENTDB_URI); Use Microsoft Entra ID (OIDC) authentication; Use hard-coded credentials
- **Because:** DOCUMENTDB_URI is provided on the developer machine per skill_md; it's safest and matches guidance. Do not commit secrets to repo.
- **Reason came from:** `readiness_report`
- **Evidence:** readiness_report instruction: 'Read the exact connection string from the portal / DOCUMENTDB_URI and use pymongo.MongoClient with the URI; prefer SRV-style URIs with `tls=true` and `authMechanism=SCRAM-SHA-256`'
- **When:** 2026-11-25T10:09:34+00:00

## D009 (build): I chose to use the existing cluster referenced by DOCUMENTDB_URI and not provision any Azure resources from this sample.

- **Instead of:** Provision a new cluster via Bicep/az (not allowed); Use existing cluster via DOCUMENTDB_URI and MCP server tools
- **Because:** Run policy forbids provisioning; sample must target live cluster already set up on the machine.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T10:09:37+00:00

## D010 (build): I chose to store embeddings as a numeric array field on documents in the `research_documents` collection and create a cosmosSearch vector index over that field.

- **Instead of:** Store embeddings externally in a separate vector DB; Store embeddings as a numeric array field inside research_documents in DocumentDB
- **Because:** Azure DocumentDB supports vector indexes against a field stored on documents; storing embeddings inline simplifies retrieval and maintains atomicity.
- **Reason came from:** `prompt`
- **Evidence:** assumptions_from_prompt_review data model and documentdb-vector-search guidance: 'Embeddings stored as a numeric array field on the research_documents documents.' and 'Create vector indexes using the documented `createIndexes` / `cosmosSearch` API'
- **When:** 2026-11-25T10:09:39+00:00

## D011 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T10:13:46+00:00

## D012 (build): I chose to target Python 3.11 for compatibility but will run with the system Python available at runtime (3.13) if necessary.

- **Instead of:** Use Python 3.13 (system); Target Python 3.11
- **Because:** LlamaIndex and related ecosystem are commonly validated on Python 3.11; using 3.11 as target ensures better compatibility while allowing the provided system Python to execute the sample.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Builder will target a recent stable Python (likely 3.10 or 3.11). I would assume Python 3.11 for tooling and LlamaIndex compatibility.'
- **When:** 2026-11-25T10:14:17+00:00

## D013 (build): I chose pymongo>=4.3,<5 as the MongoDB driver dependency.

- **Instead of:** pymongo<4.3; pymongo>=4.3,<5
- **Because:** MongoDB wire protocol 7.0 requires modern pymongo 4.x; pinning <5 avoids potential incompatible major upgrades.
- **Reason came from:** `model_default`
- **Evidence:** Assumption from prompt review: 'Use the official PyMongo driver (pymongo) with a recent 4.x release compatible with MongoDB wire protocol 7.0 (e.g., pymongo>=4.3,<5). Use MongoClient singleton pattern per documentdb-driver guidance.'
- **When:** 2026-11-25T10:14:19+00:00

## D014 (build): I chose to use the cluster connection string read from the DOCUMENTDB_URI environment variable (SCRAM-style) for authentication at runtime.

- **Instead of:** Use SCRAM credentials directly from connection string in env; Use Microsoft Entra ID OIDC
- **Because:** Run environment already provides DOCUMENTDB_URI and the sample should not handle provisioning or Entra flows; storing secrets in env follows the run guidance.
- **Reason came from:** `prompt`
- **Evidence:** Skill.md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T10:14:23+00:00

## D015 (build): I chose not to provision any Azure resources and to use the existing cluster referenced by DOCUMENTDB_URI.

- **Instead of:** Provision a new cluster using Azure tooling; Do not provision — use existing cluster
- **Because:** Run policy forbids creating Azure resources and an existing cluster is available for the sample.
- **Reason came from:** `prompt`
- **Evidence:** Skill.md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Readiness report: 'Do not provision another cluster (skill.md forbids provisioning); use the existing cluster.'
- **When:** 2026-11-25T10:14:25+00:00

## D016 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions as the default embedding model for the sample, with a fallback to synthetic random normalized vectors when OPENAI_API_KEY is not provided.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); Use another embedding model or local embeddings
- **Because:** Using a well-known public model avoids vendor lock for examples; providing a fallback keeps the sample runnable without an API key while ensuring vector dimensions match the index.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Embedding model and output dimensionality' is unspecified; common default is OpenAI text-embedding-3-small (1536).
- **When:** 2026-11-25T10:14:29+00:00

## D017 (build): I chose OpenAI gpt-4o-mini as the default chat/completion model for the RAG agent in examples and prompts, configurable via environment variables.

- **Instead of:** OpenAI gpt-4o-mini; OpenAI gpt-4; Local Llama model
- **Because:** gpt-4o-mini is a cost-effective, capable chat model suitable for examples; making it configurable keeps the sample flexible for other providers.
- **Reason came from:** `model_default`
- **Evidence:** No model specified in prompt; readiness report indicated LLM provider unspecified.
- **When:** 2026-11-25T10:14:32+00:00

## D018 (build): I chose vector-hnsw for the sample's vector index because the seed dataset is small (~30 documents) and HNSW is appropriate up to ~50k vectors.

- **Instead of:** vector-diskann; vector-hnsw
- **Because:** HNSW is simpler and suitable for small datasets; will set dimensions=1536, similarity='COS', maxDegree=32, lBuild=50 per guidance.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search guidance: 'Use vector-hnsw up to ~50k vectors' and vector-create-diskann.md which explains index selection.
- **When:** 2026-11-25T10:14:48+00:00
