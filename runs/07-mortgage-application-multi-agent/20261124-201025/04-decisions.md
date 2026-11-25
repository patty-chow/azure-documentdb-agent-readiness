# Decision log

| Reason came from | Decisions |
|---|---|
| model_default | 5 |
| prompt | 3 |
| operator | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T09:47:10+00:00

## D002 (build): I chose Node.js (v24) with Express for the sample app and LangChain-style agents in Node.

- **Instead of:** Python/Flask; Node.js/Express
- **Because:** The prompt requested a Node.js LangChain multi-agent sample and the environment has Node.js 24 installed.
- **Reason came from:** `prompt`
- **Evidence:** <assumptions_from_prompt_review> 'Builder will use Node.js 24 with npm and npx is available.'
- **When:** 2026-11-25T09:47:29+00:00

## D003 (build): I chose the official MongoDB Node.js driver 'mongodb' at version '^5.0.0'.

- **Instead of:** mongodb driver v4.x; mongodb driver v5.x
- **Because:** Driver v5.x is compatible with Node.js 24 and aligns with documentdb-driver skill guidance (singleton MongoClient).
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Builder will use the official MongoDB Node.js driver (npm package "mongodb") and pick a recent v5.x release compatible with Node.js 24 (e.g., "mongodb": "^5.0.0")'.
- **When:** 2026-11-25T09:47:31+00:00

## D004 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime.

- **Instead of:** Use managed Entra ID / RBAC (OIDC); Use connection string in env var DOCUMENTDB_URI
- **Because:** Prompt and run environment explicitly instruct using DOCUMENTDB_URI and forbids writing secrets into files.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T09:47:34+00:00

## D005 (build): I chose to use the existing pre-provisioned cluster and not to provision any Azure resources.

- **Instead of:** Provision a new cluster via IaC; Use existing pre-provisioned cluster
- **Because:** The environment already provides a reachable cluster and policy forbids provisioning Azure resources in this run.
- **Reason came from:** `prompt`
- **Evidence:** skill_md: 'A vector-capable Azure DocumentDB cluster ... is reachable ... DOCUMENTDB_URI' and run_policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T09:47:37+00:00

## D006 (build): I chose not to create a shard key; collections will be single-shard for this sample.

- **Instead of:** Shard collections and choose a shard key; No sharding for sample (single-shard)
- **Because:** Simpler for a small demo dataset and aligns with the review assumptions.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'No shard key will be created for the sample (single-shard usage).'
- **When:** 2026-11-25T09:47:42+00:00

## D007 (build): I chose OpenAI for the embedding and chat models, with embedding model 'text-embedding-3-small' (1536 dims) and a chat model placeholder 'gpt-4o-mini' for agents.

- **Instead of:** Use OpenAI (text-embedding-3-small); Use Anthropic or other provider
- **Because:** OpenAI is commonly used with LangChain; explicit model and dims allow creating indexes and placeholder environment variables. The sample will fallback to deterministic mocks if credentials are not provided.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'Builder will use a hosted LLM provider compatible with LangChain (commonly OpenAI) with chat model... and an embedding model (e.g., text-embedding-3-small with 1536 dimensions).'
- **When:** 2026-11-25T09:47:45+00:00

## D008 (build): I chose Jest for unit testing and simple mocking of DB/LLM.

- **Instead of:** Jest; Mocha
- **Because:** Jest is a common choice for Node.js projects and supports easy mocking for unit tests; aligns with repository conventions assumed in the prompt review.
- **Reason came from:** `model_default`
- **Evidence:** assumptions_from_prompt_review: 'test/ for tests (Jest)'.
- **When:** 2026-11-25T09:59:51+00:00

## D009 (build): I chose NOT to create a vector index programmatically in the seed script and instead documented the manual step in README.

- **Instead of:** Create vector index programmatically in seed; Document vector-index creation as manual step
- **Because:** Vector index creation requires explicit algorithm choice and may depend on cluster capabilities and embedding dimensions; leaving it manual avoids making unsupported calls on the target cluster. The sample still demonstrates the pipeline without vector search.
- **Reason came from:** `model_default`
- **Evidence:** readiness_report: 'Create vector indexes with the DocumentDB createIndexes / cosmosSearchOptions payload ... dimensions matching your embedding model' and README note: 'Vector-index creation is documented but left as a manual step because it depends on the embedding model and cluster capabilities.'
- **When:** 2026-11-25T09:59:54+00:00
