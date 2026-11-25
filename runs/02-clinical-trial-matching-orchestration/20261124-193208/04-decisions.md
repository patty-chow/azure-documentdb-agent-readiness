# Decision log

| Reason came from | Decisions |
|---|---|
| readiness_report | 3 |
| model_default | 3 |
| operator | 1 |
| prompt | 1 |
| tool_result | 1 |

`model_default` means the agent had no prompt, skill, doc or tool result to go on. Each one is a candidate prompt or documentation gap.

## D001 (readiness): I approved the build with readiness 'ready_with_gaps'

- **Instead of:** Stop and fix gaps first
- **Because:** Approved with --yes
- **Reason came from:** `operator`
- **When:** 2026-11-25T07:50:29+00:00

## D002 (build): I chose Python (runtime available on PATH: Python 3.13) and a virtualenv-based Python project layout.

- **Instead of:** Use Node.js/TypeScript; Use Python 3.11; Use Python 3.13
- **Because:** Python is requested by the sample prompt (LangChain orchestration in Python). Use the actual runtime found on the machine to avoid mismatch.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report: 'Python 3.13.13 is on PATH per inventory.'
- **When:** 2026-11-25T07:51:10+00:00

## D003 (build): I chose OpenAI text-embedding-3-small with 1536 dimensions for embeddings and environment variable OPENAI_API_KEY to provide the key.

- **Instead of:** OpenAI text-embedding-3-small (1536 dims); OpenAI text-embedding-ada-002 (1536?); Hugging Face model (various dims)
- **Because:** OpenAI embeddings are widely used by LangChain examples and are simple to wire in; 1536 dims is a common choice and supported by 'text-embedding-3-small'.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'The sample must choose an embedding model/provider... This determines the vector dimension (e.g., 1536) that must be used when creating the vector index.'
- **When:** 2026-11-25T07:51:15+00:00

## D004 (build): I chose OpenAI chat model 'gpt-3.5-turbo' (via OPENAI_API_KEY) for the eligibility and consent agents.

- **Instead of:** OpenAI gpt-4o or gpt-4; OpenAI gpt-3.5-turbo; Anthropic Claude
- **Because:** gpt-3.5-turbo is broadly available, lower-cost for samples, and supported by LangChain; it is adequate for small summarization and rationale tasks in a sample app.
- **Reason came from:** `model_default`
- **Evidence:** Assumptions: 'Builder will pick a hosted embedding model/provider and a chat/completion model (e.g., OpenAI chat model).','Readiness report notes missing choice.'
- **When:** 2026-11-25T07:51:17+00:00

## D005 (build): I chose to read the DocumentDB connection string from the environment variable DOCUMENTDB_URI at runtime (no secrets in repo).

- **Instead of:** Read DB credentials from a file; Embed DB credentials in code; Read DB connection URI from environment variable DOCUMENTDB_URI
- **Because:** Security best practice and the run environment already provides DOCUMENTDB_URI; the prompt forbids writing secrets to files.
- **Reason came from:** `prompt`
- **Evidence:** Skill_md: 'Its connection string is in the environment variable DOCUMENTDB_URI. Read it from the environment at run time.'
- **When:** 2026-11-25T07:51:20+00:00

## D006 (build): I chose not to provision any Azure resources and to use the existing cluster pointed to by DOCUMENTDB_URI.

- **Instead of:** Provision a new Azure DocumentDB cluster (Bicep/Terraform); Use the existing, reachable cluster described in the run environment
- **Because:** Provisioning is disallowed by run policy and an existing cluster is available for the sample to use; avoid creating paid resources.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report and run environment: 'a cluster is already provisioned and reachable' and run policy: 'Azure resource changes allowed: False.'
- **When:** 2026-11-25T07:51:24+00:00

## D007 (build): I chose to create scalar indexes for query prefiltering (criteria.conditions, criteria.min_age, criteria.max_age) via pymongo, and to attempt creating a vector index of kind 'vector-hnsw' with dimensions 1536 via the documentdb MCP server; if the MCP create-index call fails, the sample will fall back to client-side ranking using stored embeddings.

- **Instead of:** Create only scalar indexes (conditions, age); Also create a vector index with kind vector-hnsw using dimensions matching embedding model
- **Because:** Scalar indexes speed prefilters; vector index creation requires the exact MCP call format so we'll try it programmatically and gracefully handle failure for verification in this environment.
- **Reason came from:** `readiness_report`
- **Evidence:** Readiness report guidance: 'Create vector indexes using the service's createIndexes runCommand with cosmosSearchOptions ... set dimensions to match chosen embedding model.'
- **When:** 2026-11-25T07:51:27+00:00

## D008 (build): I chose to allow the seed script to run without OPENAI_API_KEY by generating random normalized vectors of dimension 1536 when the key is not present.

- **Instead of:** Require OPENAI_API_KEY for seed to generate embeddings; Allow seed to run without an embedding key by generating random vectors of the chosen dimension
- **Because:** This enables the sample to be seeded and verified in environments where an embedding API key is not available while preserving the ability to produce real embeddings when the key is provided.
- **Reason came from:** `model_default`
- **Evidence:** Readiness report: 'Information gap: embedding model and dimensionality ... builder must decide' and run environment may not have OPENAI_API_KEY set.
- **When:** 2026-11-25T07:51:29+00:00

## D009 (build): I attempted to create a service-side vector index via the documentdb MCP server but the create-index call failed; I will record this failure and continue using client-side ranking of stored embeddings as a fallback.

- **Instead of:** Proceed assuming vector index created; Stop and abort; Record failure and fall back to client-side ranking
- **Because:** Service-side vector index creation via the MCP helper failed in this environment; sample remains functional using client-side ranking and scalar indexes created by the seed script.
- **Reason came from:** `tool_result`
- **Evidence:** documentdb_create_index call returned 'Error: Function failed.'
- **When:** 2026-11-25T07:53:14+00:00
