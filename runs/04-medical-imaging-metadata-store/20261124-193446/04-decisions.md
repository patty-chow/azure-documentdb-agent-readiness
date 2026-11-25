# Decision log

| Reason came from | Decisions |
|---|---|
| prompt | 4 |
| skill | 4 |
| operator | 1 |
| readiness_report | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'blocked'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **Evidence:** Embedding storage format conflict: The sample strictly requires storing embeddings as BSON Binary vectors, but Azure DocumentDB's native vector indexes require vectors to be a number[] (JSON array of numbers). The app, seed script and index creation must be revised: either (A) change the requirement to store embeddings as number[] so cosmosSearch vector indexes can be created and used, or (B) accept that native vector indexing cannot be used and perform application-layer kNN (not recommended). Author action: confirm which storage format to use and whether native vector index use is mandatory.; OpenAI model unspecified: The sample needs the exact embedding model and its dimensionality so the vector index can be created with the correct 'dimensions' value. Author action: specify OPENAI_MODEL (and desired embedding precision) before index creation.; The prompt required storing embeddings as BSON Binary; if the author insists on that format but still wants vector-ivf index demonstration, the sample cannot be implemented as written and must be changed. Author action: change prompt or accept an alternate approach (store as number[]).
- **When:** 2026-11-25T08:09:16+00:00

## D002 (build): I chose Python 3.10 as the language/runtime for the sample.

- **Instead of:** Node.js/TypeScript; Python 3.10; Go
- **Because:** Python is requested in the sample prompt and is the preferred choice for rapid prototyping and for using OpenAI SDK and PyMongo; 3.10 is a stable target.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use Python 3.10 or 3.11 (builder will target a current 3.x LTS; assume 3.10 for packaging/CI).
- **When:** 2026-11-25T08:09:45+00:00

## D003 (build): I chose pymongo>=4.4,<5 for the MongoDB driver.

- **Instead of:** pymongo 3.x; pymongo>=4.4,<5; motor (async)
- **Because:** PyMongo is the recommended synchronous driver and is widely used; choose 4.x for modern API compatibility.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use PyMongo (pymongo) as the MongoDB driver; pin a recent 4.x release (e.g., pymongo>=4.4,<5) in requirements.txt, and follow the documentdb-driver skill guidance for client reuse.'
- **When:** 2026-11-25T08:09:48+00:00

## D004 (build): I chose to read secrets and connection strings from environment variables (DOCUMENTDB_URI, OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_DIM).

- **Instead of:** Read secrets from files; Read from environment variables; Use Azure Key Vault
- **Because:** Environment variables are standard for samples, avoid checked-in secrets, and align with the prompt guidance.
- **Reason came from:** `prompt`
- **Evidence:** Assumption from prompt review: 'Use environment variables: DOCUMENTDB_URI for DB connection and OPENAI_API_KEY ... Do not write secrets into repo; include a .env.example with placeholders.'
- **When:** 2026-11-25T08:09:52+00:00

## D005 (build): I chose to store embeddings as a number[] (JSON array of numbers) in the 'embedding' field.

- **Instead of:** Store embeddings as BSON Binary; Store embeddings as number[] (array of numbers)
- **Because:** Azure DocumentDB native vector indexes require vectors to be a number[]; storing as binary would prevent using native vector-ivf index as the sample requires.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Do not store embeddings as BSON Binary if you want to use the DocumentDB native vector indexes; store embeddings as a number[] field (embedding: [0.12, -0.04, ...]) and create the vector index with cosmosSearchOptions.'
- **When:** 2026-11-25T08:09:55+00:00

## D006 (build): I chose OpenAI model text-embedding-3-small and EMBEDDING_DIM=1536.

- **Instead of:** text-embedding-3-large; text-embedding-3-small; text-embedding-3-mini
- **Because:** text-embedding-3-small balances cost and quality for a sample; vector-create-diskann-index.md shows 1536 as the matching dimension for that model.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search skill resource vector-create-diskann-index.md uses 1536 as the dimensions matching text-embedding-3-small and recommends matching dimensions exactly.
- **When:** 2026-11-25T08:09:59+00:00

## D007 (build): I chose to create a vector-ivf index (kind: 'vector-ivf').

- **Instead of:** vector-diskann; vector-hnsw; vector-ivf
- **Because:** The prompt specifically asked for a vector-ivf index; the corpus seeded by this sample will be small (~50 documents) making IVF appropriate for demo and faster to build.
- **Reason came from:** `prompt`
- **Evidence:** Prompt requested 'create a vector-ivf index'. The documentdb-vector-search skill indicates vector-ivf is appropriate for small demo corpora (under ~10k vectors).
- **When:** 2026-11-25T08:10:02+00:00

## D008 (build): I chose to use the existing pre-provisioned cluster and not provision any Azure resources.

- **Instead of:** Provision new cluster via az/ARM; Use existing pre-provisioned cluster
- **Because:** Run policy disallows creating Azure resources; the environment already has a reachable cluster as described.
- **Reason came from:** `skill`
- **Evidence:** Skill_md: 'This sample is being built on a developer machine where an Azure DocumentDB cluster is already provisioned and reachable.' Also run_policy forbids provisioning.
- **When:** 2026-11-25T08:10:12+00:00

## D009 (build): I chose similarity 'COS' (cosine) for the index and query-time comparisons.

- **Instead of:** similarity COS (cosine); similarity L2; similarity IP
- **Because:** We normalize embeddings at insert time (seed and embed_text normalize) so cosine similarity is appropriate.
- **Reason came from:** `skill`
- **Evidence:** documentdb-vector-search guidance: 'Use COS for normalized text embeddings' and the seed normalizes embeddings.
- **When:** 2026-11-25T08:11:08+00:00

## D010 (build): I chose lBuild=50 for the index build parameter.

- **Instead of:** lBuild 50; lBuild 10; lBuild 200
- **Because:** 50 is a balanced default for demo quality and build time.
- **Reason came from:** `skill`
- **Evidence:** vector-create-diskann-index.md recommended default lBuild=50 for good quality.
- **When:** 2026-11-25T08:11:11+00:00

## D011 (build): I chose to use pymongo.create_index from a local script (create_index.py) after the MCP documentdb_create_index call failed.

- **Instead of:** Use documentdb_create_index MCP tool; Use pymongo.create_index from the sample script
- **Because:** create_index via pymongo succeeded and returned the index name; using pymongo is consistent with standard MongoDB drivers and allowed by the environment for verification.
- **Reason came from:** `tool_result`
- **Evidence:** Attempt to call documentdb_create_index via MCP returned an error: 'Error: Function failed.' (tool_result).
- **When:** 2026-11-25T08:12:21+00:00
